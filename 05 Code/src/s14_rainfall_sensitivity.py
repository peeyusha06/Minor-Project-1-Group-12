"""Step 14 - rainfall sensitivity for the flagged IMD values (Pune first). Primary outputs are NOT changed.

Treatment ("exclude flagged"): the district-years flagged as implausibly high (monsoon > 2 x baseline,
config rainfall_extreme_values) are removed from that district's rainfall calculations. The 1971-2020 baseline,
departures, deficient flags, SPI, El Nino deficient frequency, worst El Nino deficit and ENSO-rainfall slope
are then recomputed without them. The published IMD values themselves are not edited.

Scenarios:
  pune_excluded         only Pune's flagged years (2005, 2009) - the main check
  all_flagged_excluded  every flagged high district-year in Maharashtra (broader check)

Outputs:
  data/interim/sensitivity/climate_features_<scenario>.csv   recomputed rainfall features (all 36 districts)
  data/interim/sensitivity/pca_input_<scenario>.csv          Set A input, same layout as pca_input_primary.csv
  data/processed/sensitivity/<scenario>/pca_*.csv            PCA + leave-one-out, same layout as step 13
  data/processed/sensitivity/rainfall_sensitivity_comparison.csv

Run:  python src/s14_rainfall_sensitivity.py
"""
import numpy as np
import pandas as pd

from common import INTERIM, ROOT, load_config, write_csv
from s05_rainfall import spi_from_baseline
from s07_climate_features import features
from s12_pca_input import PCA_NAMES
from s13_pca_primary import run_pca

PUNE = 521
SCENARIOS = {"pune_excluded": [PUNE], "all_flagged_excluded": None}
OUT = ROOT / "data" / "processed" / "sensitivity"
SENS_IN = INTERIM / "sensitivity"
RAIN_COLS = {"enso_rain_slope_pct_per_degC": "enso_rain_slope_pct_per_degC",   # master name: step 7 name
             "rain_en_deficient_frequency": "en_deficient_frequency",
             "rain_en_max_deficit_pct": "en_max_deficit_pct"}


def rainfall_without_flagged(annual, cfg, districts):
    """Drop flagged high district-years (optionally only for some districts) and recompute baseline-based columns."""
    b = cfg["decisions"]["rainfall_baseline"]
    thr = cfg["decisions"]["deficient_monsoon_threshold"]["departure_pct"]
    drop = annual.extreme_value_flag.copy()
    if districts:
        drop &= annual.district_id.isin(districts)
    a = annual[~drop].copy()
    in_base = a.year.between(b["first_year"], b["last_year"])
    a["baseline_monsoon_mm"] = a.district_id.map(a[in_base].groupby("district_id").monsoon_rainfall_mm.mean())
    a["monsoon_departure_pct"] = (a.monsoon_rainfall_mm - a.baseline_monsoon_mm) / a.baseline_monsoon_mm * 100
    a["deficient_monsoon"] = a.monsoon_departure_pct <= thr
    for d, g in a.groupby("district_id"):
        a.loc[g.index, "spi_monsoon"] = spi_from_baseline(g.monsoon_rainfall_mm, in_base.loc[g.index])
    return a, annual[drop][["district_id", "year"]]


def sensitivity_input(primary_in, clim, signs, changed):
    """Primary Set A input with the rainfall variables replaced for the districts that lost flagged years.
    (Other districts keep their primary values; recomputing them from the 4-decimal CSV differs by ~1e-5 only.)"""
    out = primary_in.copy()
    c = clim.set_index("district_id")
    rows = out.district_id.isin(changed)
    for f in ("enso_rain_slope_pct_per_degC", "rain_en_deficient_frequency"):
        out.loc[rows, f] = out.district_id[rows].map(c[RAIN_COLS[f]])
        out[PCA_NAMES[f]] = out[f] * signs[f]
    return out


def compare(name, prim, sens, primary_in, sens_in):
    """Rows of (scenario, section, item, primary, sensitivity) comparing two PCA runs."""
    (pv, pl, ps, ploo), (sv, sl, ss, sloo) = prim, sens
    rows = []

    def add(section, item, a, b, note=""):
        rows.append({"scenario": name, "section": section, "item": item, "primary": a, "sensitivity": b,
                     "difference": b - a if isinstance(a, (int, float, np.floating)) else np.nan, "note": note})

    for k in range(6):
        add("explained_variance_ratio", f"PC{k + 1}", pv.explained_variance_ratio[k], sv.explained_variance_ratio[k])
    wp = pl[[f"PC{k}_weight" for k in range(1, 7)]].to_numpy().T      # rows = components
    ws = sl[[f"PC{k}_weight" for k in range(1, 7)]].to_numpy().T
    for k in range(3):
        cos = ws @ wp[k]
        best = int(np.argmax(np.abs(cos)))
        sign = np.sign(cos[best])
        note = f"matched to sensitivity PC{best + 1}" + (" (sign flipped to match)" if sign < 0 else "")
        add("component_match_abs_cosine", f"PC{k + 1}", 1.0, abs(cos[best]), note)
        for j, v in enumerate(pl.variable):
            add(f"PC{k + 1}_weight", v, wp[k, j], sign * ws[best, j], note)
            add(f"PC{k + 1}_loading", v, pl[f"PC{k + 1}_loading"][j], sign * sl[f"PC{best + 1}_loading"][j], note)
        sp, s2 = ps[f"PC{k + 1}"].to_numpy(), sign * ss[f"PC{best + 1}"].to_numpy()
        add("score_correlation", f"PC{k + 1}", 1.0, np.corrcoef(sp, s2)[0, 1], note)
        pune = (primary_in.district_id == PUNE).to_numpy()
        add("pune_score", f"PC{k + 1}", sp[pune][0], s2[pune][0], note)
        add("max_abs_score_change_other_districts", f"PC{k + 1}", 0.0, np.abs(s2 - sp)[~pune].max(), note)
    for f in ("enso_rain_slope_pct_per_degC", "rain_en_deficient_frequency"):
        p_val = primary_in.loc[primary_in.district_id == PUNE, f].iloc[0]
        s_val = sens_in.loc[sens_in.district_id == PUNE, f].iloc[0]
        add("pune_input", f, p_val, s_val)
    for k in (1, 2, 3):
        add("loo_median_abs_cosine", f"PC{k}", ploo[f"abs_cosine_PC{k}"].median(), sloo[f"abs_cosine_PC{k}"].median())
        add("loo_min_abs_cosine", f"PC{k}", ploo[f"abs_cosine_PC{k}"].min(), sloo[f"abs_cosine_PC{k}"].min(),
            f"primary min when omitting {ploo.omitted_district[ploo[f'abs_cosine_PC{k}'].idxmin()]}; "
            f"sensitivity min when omitting {sloo.omitted_district[sloo[f'abs_cosine_PC{k}'].idxmin()]}")
        add("loo_runs_order_changed", f"PC{k}", int(ploo[f"order_changed_PC{k}"].sum()), int(sloo[f"order_changed_PC{k}"].sum()),
            "sensitivity: " + ";".join(sloo.omitted_district[sloo[f"order_changed_PC{k}"]]))
    for k in (2, 3):
        c = f"PC{k}_in_LOO_PC2_PC3_plane"
        add("loo_min_plane_projection", f"PC{k}", ploo[c].min(), sloo[c].min())
    return rows


def main():
    cfg = load_config()
    signs = cfg["decisions"]["pca_primary"]["sign_multipliers"]
    annual = pd.read_csv(INTERIM / "district_annual_monsoon_rainfall.csv")
    enso = pd.read_csv(INTERIM / "enso_yearly_features.csv")
    primary_in = pd.read_csv(INTERIM / "pca_input_primary.csv")
    base_clim = pd.read_csv(INTERIM / "climate_vulnerability_features.csv").set_index("district_id")
    cols = [c for c in primary_in.columns if c.startswith("pca_")]
    prim = run_pca(primary_in, cols)

    rows, dropped_all = [], []
    for name, districts in SCENARIOS.items():
        a, dropped = rainfall_without_flagged(annual, cfg, districts)
        clim, _ = features(a, enso, "RONI", "B")
        # districts without dropped years must reproduce the primary features exactly
        same = ~clim.district_id.isin(dropped.district_id)
        for c in RAIN_COLS.values():
            assert np.allclose(clim.loc[same, c], clim.loc[same, "district_id"].map(base_clim[c]))
        sens_in = sensitivity_input(primary_in, clim, signs, dropped.district_id)
        sens = run_pca(sens_in, cols)

        write_csv(clim, SENS_IN / f"climate_features_{name}.csv")
        write_csv(sens_in, SENS_IN / f"pca_input_{name}.csv")
        for table, fname in zip(sens, ("variance", "loadings", "scores", "leave_one_out")):
            write_csv(table, OUT / name / f"pca_{fname}.csv")
        rows += compare(name, prim, sens, primary_in, sens_in)
        dropped_all.append(dropped.assign(scenario=name))
        print(f"{name}: dropped {len(dropped)} district-years; "
              f"EVR {np.round(sens[0].explained_variance_ratio.to_numpy()[:3], 3)}")

    write_csv(pd.DataFrame(rows), OUT / "rainfall_sensitivity_comparison.csv")
    write_csv(pd.concat(dropped_all), OUT / "rainfall_sensitivity_dropped_district_years.csv")


if __name__ == "__main__":
    main()
