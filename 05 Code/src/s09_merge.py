"""Step 9 - master district feature table (one row per district), NO standardisation, NO selection.

Validation variables are deliberately NOT merged here; they live only in drought_validation.csv.
"""
from __future__ import annotations

import pandas as pd

from common import MUMBAI_CODES, active, variant_dir, write_csv
from feature_registry import REG

SOC = ["rural_population_share_pct", "literacy_rate_7plus_pct", "work_participation_rate_pct", "non_worker_share_pct",
       "agri_worker_share_of_workers_pct", "agri_worker_share_of_population_pct", "cultivator_share_of_workers_pct",
       "agri_labourer_share_of_workers_pct", "marginal_worker_share_of_workers_pct", "marginal_workers_per_population_pct",
       "sc_share_pct", "st_share_pct"]
CLIM_ENSO = ["n_study_years", "n_elnino_years", "elnino_years", "enso_rain_pearson_r", "enso_rain_pearson_p",
             "enso_rain_spearman_rho", "enso_rain_slope_pct_per_degC"]
CLIM_RAIN = ["baseline_monsoon_mm", "monsoon_cv_pct", "en_mean_deficit_pct", "en_max_deficit_pct", "en_deficient_frequency",
             "en_mean_spi", "nonen_mean_deficit_pct", "nonen_deficient_frequency", "en_minus_nonen_deficit_pct",
             "en_minus_nonen_deficient_frequency"]


def build(geo: str, index: str, cfg: dict, cw: pd.DataFrame, census: pd.DataFrame, vd: pd.DataFrame,
          agc: pd.DataFrame, clim: pd.DataFrame, rain_qa: pd.DataFrame) -> pd.DataFrame:
    g = cw[cw.geography_version == geo][["district_id", "geography_version", "census_2011_district_code", "census_2011_district_name",
                                         "current_district_name", "marathi_name", "district_boundary_id"]].copy()
    exclude = active(cfg, "exclude_mumbai_from_index") == "exclude"
    g["in_index_scope"] = ~(exclude & g.census_2011_district_code.isin(MUMBAI_CODES))
    g["agri_data_available"] = g.district_id.isin(vd.district_id) & g.district_id.isin(agc.district_id)
    g["district_area_km2"] = g.district_id.map(rain_qa.set_index("district_id").district_area_km2)

    c = clim.set_index("district_id")
    m = g.copy()
    m["enso_index"] = index
    for f in CLIM_ENSO:
        m["enso_" + f if not f.startswith("enso_") else f] = m.district_id.map(c[f])
    for f in CLIM_RAIN:
        m["rain_" + f] = m.district_id.map(c[f])
    s = census.set_index("district_id")
    m["soc_total_population"] = m.district_id.map(s.total_population)
    for f in SOC:
        m["soc_" + f] = m.district_id.map(s[f])
    v = vd.set_index("district_id")
    m["agri_n_villages"] = m.district_id.map(v.n_villages)
    m["agri_net_area_sown_ha"] = m.district_id.map(v.net_area_sown_ha)
    m["agri_cropped_land_share_pct"] = m.district_id.map(v.cropped_land_share_pct)
    m["agri_forest_share_pct"] = m.district_id.map(v.forest_share_pct)
    m["agri_fallow_share_pct"] = m.district_id.map(v.fallow_share_pct)
    m["irr_irrigated_share_of_cropped_land_pct"] = m.district_id.map(v.irrigated_share_of_cropped_land_pct)
    m["irr_rainfed_share_of_cropped_land_pct"] = m.district_id.map(v.rainfed_share_of_cropped_land_pct)
    m["irr_well_share_of_irrigated_pct"] = m.district_id.map(v.well_share_of_irrigated_pct)
    m["irr_canal_share_of_irrigated_pct"] = m.district_id.map(v.canal_share_of_irrigated_pct)
    m["irr_tank_share_of_irrigated_pct"] = m.district_id.map(v.tank_share_of_irrigated_pct)
    a = agc.set_index("district_id")
    m["land_n_holdings_total"] = m.district_id.map(a.n_holdings_total)
    m["land_small_holding_share_pct"] = m.district_id.map(a.small_holding_share_pct)
    m["land_marginal_holding_share_pct"] = m.district_id.map(a.marginal_holding_share_pct)
    m["land_small_holding_area_share_pct"] = m.district_id.map(a.small_holding_area_share_pct)
    m["land_avg_holding_size_ha"] = m.district_id.map(a.avg_holding_size_ha)

    registered = [r["feature"] for r in REG if r["table"] == "maharashtra_district_feature_table.csv"]
    missing = [col for col in m.columns if col not in registered]
    assert not missing, f"undocumented master columns: {missing}"
    return m[[f for f in registered if f in m.columns]].sort_values("district_id").reset_index(drop=True)


def run(geo, index, cfg, cw, census, vd, agc, clim, rain_qa) -> pd.DataFrame:
    m = build(geo, index, cfg, cw, census, vd, agc, clim, rain_qa)
    write_csv(m, variant_dir(geo, index) / "maharashtra_district_feature_table.csv")
    return m
