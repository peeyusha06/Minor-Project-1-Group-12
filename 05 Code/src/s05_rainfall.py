"""Step 5 - district rainfall from the official IMD 0.25 deg gridded daily rainfall (NetCDF).

Source: data/raw/rainfall/imd_gridded_0p25_netcdf/ind{YEAR}_rfp25.nc (primary study period from config: 1950-2024), variable RAINFALL (mm/day),
_FillValue -999 (masked on read). Cite: Pai et al. (2014) MAUSAM 65(1):1-18.

Method (config: rainfall_spatial_aggregation):
  1. Each grid point is represented by a 0.25 x 0.25 deg box centred on it.
  2. Weight w[d, c] = area (km2, Albers equal-area) of cell box c inside district polygon d.
  3. Daily district rainfall = sum_c w[d,c] * R[c] / sum_c w[d,c] over cells with valid data that day.
  4. Monthly rainfall = sum of daily district values in the month (NaN if any day has no valid cell).
  5. Monsoon rainfall = June + July + August + September.
  6. Baseline = district mean monsoon rainfall over the configured baseline years.
     Departure % = (monsoon - baseline) / baseline * 100.
  7. SPI = gamma distribution fitted to the district's baseline-period monsoon totals,
     transformed to a standard normal quantile (all years evaluated with the baseline fit).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr
from scipy import stats
from shapely.geometry import box

import geopandas as gpd

from common import SRC, active, district_polygons, geo_dir, load_config, write_csv

LAT_RANGE = (15.0, 23.0)
LON_RANGE = (72.0, 81.75)
HALF = 0.125


def grid_cells(lats: np.ndarray, lons: np.ndarray) -> gpd.GeoDataFrame:
    recs = [(i, j, la, lo, box(lo - HALF, la - HALF, lo + HALF, la + HALF)) for i, la in enumerate(lats) for j, lo in enumerate(lons)]
    return gpd.GeoDataFrame(pd.DataFrame(recs, columns=["iy", "ix", "lat", "lon", "geometry"]), geometry="geometry", crs=4326)


def weights(districts: gpd.GeoDataFrame, cells: gpd.GeoDataFrame, aea: str) -> pd.DataFrame:
    d = districts.to_crs(aea)
    c = cells.to_crs(aea)
    inter = gpd.overlay(c, d, how="intersection", keep_geom_type=True)
    inter["weight_km2"] = inter.area / 1e6
    inter = inter[inter.weight_km2 > 1e-6]
    return inter[["district_id", "iy", "ix", "lat", "lon", "weight_km2"]].reset_index(drop=True)


def weight_matrix(w: pd.DataFrame, ids: list[int], ny: int, nx: int) -> np.ndarray:
    W = np.zeros((len(ids), ny * nx))
    pos = {d: k for k, d in enumerate(ids)}
    for r in w.itertuples():
        W[pos[r.district_id], r.iy * nx + r.ix] += r.weight_km2
    return W


def year_files(first: int, last: int) -> list[tuple[int, str]]:
    return [(y, str(SRC["imd_dir"] / f"ind{y}_rfp25.nc")) for y in range(first, last + 1)]


def compute_monthly(geos: tuple[str, ...], cfg: dict) -> dict:
    aea = cfg["decisions"]["rainfall_spatial_aggregation"]["equal_area_crs"]
    source = active(cfg, "boundary_source")
    sp = cfg["decisions"]["study_period"]
    files = year_files(sp["first_year"], sp["last_year"])

    ds0 = xr.open_dataset(files[0][1])
    sub0 = ds0.RAINFALL.sel(LATITUDE=slice(*LAT_RANGE), LONGITUDE=slice(*LON_RANGE))
    lats, lons = sub0.LATITUDE.values, sub0.LONGITUDE.values
    ds0.close()
    cells = grid_cells(lats, lons)

    setup = {}
    for geo in geos:
        polys = district_polygons(geo, source)
        w = weights(polys, cells, aea)
        ids = sorted(polys.district_id.tolist())
        area = polys.to_crs(aea).set_index("district_id").area / 1e6
        setup[geo] = {"ids": ids, "w": w, "W": weight_matrix(w, ids, len(lats), len(lons)), "area_km2": area}

    monthly = {g: [] for g in geos}
    daily_cov = {g: [] for g in geos}
    grid_qa = []
    for year, path in files:
        ds = xr.open_dataset(path)
        da = ds.RAINFALL.sel(LATITUDE=slice(*LAT_RANGE), LONGITUDE=slice(*LON_RANGE))
        assert np.allclose(da.LATITUDE.values, lats) and np.allclose(da.LONGITUDE.values, lons), f"grid changed in {year}"
        x = da.values.reshape(da.shape[0], -1)  # (days, cells), NaN where -999
        valid = ~np.isnan(x)
        xf = np.where(valid, x, 0.0)
        times = pd.to_datetime(da.TIME.values)
        grid_qa.append({"year": year, "n_days": len(times), "n_cells_valid_any_day": int(valid.any(axis=0).sum()),
                        "n_cells_valid_all_days": int(valid.all(axis=0).sum()), "min_daily_mm": float(np.nanmin(x)),
                        "max_daily_mm": float(np.nanmax(x))})
        for geo in geos:
            W = setup[geo]["W"]
            num = xf @ W.T
            den = valid.astype(float) @ W.T
            with np.errstate(invalid="ignore", divide="ignore"):
                daily = np.where(den > 0, num / den, np.nan)
            cov = den / W.sum(axis=1)  # share of district weight with valid data, per day
            df = pd.DataFrame(daily, index=times, columns=setup[geo]["ids"])
            m = df.groupby(df.index.month).agg(lambda s: s.sum() if s.notna().all() else np.nan)
            m = m.stack(future_stack=True).rename("rainfall_mm").reset_index()
            m.columns = ["month", "district_id", "rainfall_mm"]
            m["year"] = year
            monthly[geo].append(m)
            daily_cov[geo].append(pd.DataFrame({"district_id": setup[geo]["ids"], "year": year,
                                                "min_valid_weight_share": cov.min(axis=0),
                                                "n_days_no_valid_cell": (den == 0).sum(axis=0)}))
        ds.close()
    return {"setup": setup, "monthly": monthly, "coverage": daily_cov, "grid_qa": pd.DataFrame(grid_qa), "cells": cells}


def spi_from_baseline(values: pd.Series, base_mask: pd.Series) -> pd.Series:
    base = values[base_mask].dropna()
    a, loc, scale = stats.gamma.fit(base, floc=0)
    cdf = stats.gamma.cdf(values, a, loc=loc, scale=scale)
    cdf = np.clip(cdf, 1e-6, 1 - 1e-6)
    return pd.Series(stats.norm.ppf(cdf), index=values.index)


def flag_extremes(wide: pd.DataFrame, in_base: pd.Series, ratio: float) -> pd.Series:
    """Flag district-years above ratio x the all-years-included baseline mean (flag only; values untouched)."""
    base_all = wide[in_base].groupby("district_id").monsoon_rainfall_mm.mean()
    return wide.monsoon_rainfall_mm > ratio * wide.district_id.map(base_all)


def annual_monsoon(monthly: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    months = cfg["decisions"]["monsoon_months"]["months"]
    b = cfg["decisions"]["rainfall_baseline"]
    thr = cfg["decisions"]["deficient_monsoon_threshold"]["departure_pct"]
    ext = cfg["decisions"]["rainfall_extreme_values"]
    names = {6: "june_rainfall_mm", 7: "july_rainfall_mm", 8: "august_rainfall_mm", 9: "september_rainfall_mm"}
    wide = monthly[monthly.month.isin(months)].pivot_table(index=["district_id", "year"], columns="month", values="rainfall_mm", dropna=False)
    wide = wide.rename(columns=names).reset_index()
    wide["monsoon_rainfall_mm"] = wide[[names[m] for m in months]].sum(axis=1, min_count=len(months))
    wide["annual_rainfall_mm"] = wide.set_index(["district_id", "year"]).index.map(
        monthly.groupby(["district_id", "year"]).rainfall_mm.sum(min_count=12))
    in_base = wide.year.between(b["first_year"], b["last_year"])
    wide["extreme_value_flag"] = flag_extremes(wide, in_base, ext["flag_ratio"])
    base_all = wide[in_base].groupby("district_id").monsoon_rainfall_mm.mean()
    wide["extreme_low_review_flag"] = wide.monsoon_rainfall_mm < ext["low_flag_ratio"] * wide.district_id.map(base_all)
    base_mask = in_base & ~wide.extreme_value_flag if ext["active"] == "exclude_flagged_from_baseline" else in_base
    base = wide[base_mask].groupby("district_id").monsoon_rainfall_mm.mean()
    wide["baseline_monsoon_excl_flagged_mm"] = wide.district_id.map(wide[in_base & ~wide.extreme_value_flag].groupby("district_id").monsoon_rainfall_mm.mean())
    wide["baseline_monsoon_mm"] = wide.district_id.map(base)
    wide["baseline_period"] = f"{b['first_year']}-{b['last_year']}"
    wide["monsoon_departure_pct"] = (wide.monsoon_rainfall_mm - wide.baseline_monsoon_mm) / wide.baseline_monsoon_mm * 100
    # exact (unrounded) departure is compared with the IMD threshold, e.g. -19.6% is not deficient
    wide["deficient_monsoon"] = wide.monsoon_departure_pct <= thr
    wide["spi_monsoon"] = np.nan
    for d, g in wide.groupby("district_id"):
        wide.loc[g.index, "spi_monsoon"] = spi_from_baseline(g.monsoon_rainfall_mm, base_mask.loc[g.index])
    return wide.sort_values(["district_id", "year"]).reset_index(drop=True)


def qa_table(res: dict, geo: str, annual: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    s = res["setup"][geo]
    w = s["w"]
    cov = pd.concat(res["coverage"][geo])
    q = pd.DataFrame({"district_id": s["ids"]})
    q["district_area_km2"] = q.district_id.map(s["area_km2"])
    q["n_grid_cells_intersecting"] = q.district_id.map(w.groupby("district_id").size())
    q["n_grid_cells_ge_50pct_inside"] = q.district_id.map(w[w.weight_km2 >= 0.5 * w.weight_km2.max()].groupby("district_id").size()).fillna(0).astype(int)
    q["sum_cell_weights_km2"] = q.district_id.map(w.groupby("district_id").weight_km2.sum())
    q["weights_over_area_ratio"] = q.sum_cell_weights_km2 / q.district_area_km2
    q["min_daily_valid_weight_share"] = q.district_id.map(cov.groupby("district_id").min_valid_weight_share.min())
    q["days_with_no_valid_cell"] = q.district_id.map(cov.groupby("district_id").n_days_no_valid_cell.sum())
    a = annual.groupby("district_id")
    q["years_available"] = q.district_id.map(a.monsoon_rainfall_mm.count())
    q["first_year"] = q.district_id.map(a.year.min())
    q["last_year"] = q.district_id.map(a.year.max())
    q["missing_monsoon_years"] = q.district_id.map(a.monsoon_rainfall_mm.apply(lambda x: int(x.isna().sum())))
    q["min_monsoon_mm"] = q.district_id.map(a.monsoon_rainfall_mm.min())
    q["max_monsoon_mm"] = q.district_id.map(a.monsoon_rainfall_mm.max())
    q["baseline_monsoon_mm"] = q.district_id.map(a.baseline_monsoon_mm.first())
    q["low_cell_count_flag"] = q.n_grid_cells_intersecting < 10
    q["partial_valid_coverage_flag"] = q.min_daily_valid_weight_share < 0.9
    q["n_extreme_flagged_years"] = q.district_id.map(a.extreme_value_flag.sum()).astype(int)
    q["baseline_excl_flagged_mm"] = q.district_id.map(a.baseline_monsoon_excl_flagged_mm.first())
    q["baseline_change_if_flagged_excluded_pct"] = (q.baseline_excl_flagged_mm - q.baseline_monsoon_mm) / q.baseline_monsoon_mm * 100
    return q


def run(geos: tuple[str, ...], cfg: dict) -> dict:
    res = compute_monthly(geos, cfg)
    out = {}
    for geo in geos:
        monthly = pd.concat(res["monthly"][geo]).sort_values(["district_id", "year", "month"]).reset_index(drop=True)
        monthly = monthly[["district_id", "year", "month", "rainfall_mm"]]
        annual = annual_monsoon(monthly, cfg)
        qa = qa_table(res, geo, annual, cfg)
        d = geo_dir(geo)
        write_csv(monthly, d / "district_monthly_rainfall.csv", 4)
        write_csv(annual, d / "district_annual_monsoon_rainfall.csv", 4)
        write_csv(qa, d / "rainfall_qa.csv", 4)
        write_csv(res["setup"][geo]["w"], d / "rainfall_grid_weights.csv", 6)
        ext = annual[annual.extreme_value_flag | annual.extreme_low_review_flag][
            ["district_id", "year", "june_rainfall_mm", "july_rainfall_mm", "august_rainfall_mm",
             "september_rainfall_mm", "monsoon_rainfall_mm", "baseline_monsoon_mm", "extreme_value_flag"]].copy()
        ext["ratio_to_baseline"] = ext.monsoon_rainfall_mm / ext.baseline_monsoon_mm
        ext["flag_type"] = ext.extreme_value_flag.map({True: "high (eligible for optional baseline exclusion)", False: "low (review only)"})
        ext = ext.drop(columns="extreme_value_flag")
        write_csv(ext, d / "rainfall_extreme_district_years.csv", 2)
        out[geo] = annual
    write_csv(res["grid_qa"], geo_dir(geos[0]).parent / "rainfall_grid_qa_by_year.csv", 3)
    return out


if __name__ == "__main__":
    run(("A", "B"), load_config())
