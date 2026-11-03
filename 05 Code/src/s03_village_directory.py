"""Step 3 - agricultural land-use and irrigation features from the Census 2011 Village Directory.

Source: data/raw/census/DH_2011_DCHB_Village_Release_2700.xlsx, sheet 'Village_Data_2700'
(one row per village, 43,665 villages, 33 districts; Mumbai City/Suburban have no villages).

LABEL ANOMALY (documented in config: village_directory_irrigation_labels)
The raw columns 'Total Unirrigated Land Area (in Hectares)' and 'Area Irrigated by Source
(in Hectares)' are swapped. The raw file is not edited. RAW_TO_ANALYTICAL below maps the
raw header text to the analytical meaning explicitly, and the QA table re-tests the evidence
(sum of source-wise irrigated areas == column labelled 'Total Unirrigated') every run.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import PALGHAR_LGD, PALGHAR_SUBDISTRICTS, SRC, THANE, active, geo_dir, write_csv

# position in sheet -> (exact raw header, analytical name)
RAW_COLUMNS = {
    2: ("District Code", "district_code"),
    4: ("Sub District Code", "subdistrict_code"),
    6: ("Village Code", "village_code"),
    23: ("Total Geographical Area (in Hectares)", "total_geographical_area_ha"),
    378: ("Forest Area (in Hectares)", "forest_ha"),
    379: ("Area under Non-Agricultural Uses (in Hectares)", "non_agricultural_use_ha"),
    380: ("Barren & Un-cultivable Land Area (in Hectares)", "barren_unculturable_ha"),
    381: ("Permanent Pastures and Other Grazing Land Area (in Hectares)", "pastures_ha"),
    382: ("Land Under Miscellaneous Tree Crops etc. Area (in Hectares)", "misc_tree_crops_ha"),
    383: ("Culturable Waste Land Area (in Hectares)", "culturable_waste_ha"),
    384: ("Fallows Land other than Current Fallows Area (in Hectares)", "other_fallow_ha"),
    385: ("Current Fallows Area (in Hectares)", "current_fallow_ha"),
    386: ("Net Area Sown (in Hectares)", "net_area_sown_ha"),
    # --- swapped labels: raw header text -> analytical meaning ---
    387: ("Total Unirrigated Land Area (in Hectares)", "irrigated_area_ha"),
    388: ("Area Irrigated by Source (in Hectares)", "unirrigated_area_ha"),
    # --- source-wise irrigated area ---
    389: ("Canals Area (in Hectares)", "canal_irrigated_ha"),
    390: ("Wells/Tube Wells Area (in Hectares)", "well_irrigated_ha"),
    391: ("Tanks/Lakes Area (in Hectares)", "tank_irrigated_ha"),
    392: ("Waterfall Area (in Hectares)", "waterfall_irrigated_ha"),
    393: ("Other Source (specify) Area (in Hectares)", "other_source_irrigated_ha"),
}
AREA_COLS = [v[1] for k, v in RAW_COLUMNS.items() if k >= 23]
SOURCE_COLS = ["canal_irrigated_ha", "well_irrigated_ha", "tank_irrigated_ha", "waterfall_irrigated_ha", "other_source_irrigated_ha"]
LAND_USE_PARTS = ["forest_ha", "non_agricultural_use_ha", "barren_unculturable_ha", "pastures_ha", "misc_tree_crops_ha",
                  "culturable_waste_ha", "other_fallow_ha", "current_fallow_ha", "net_area_sown_ha"]


def load_villages() -> pd.DataFrame:
    raw = pd.read_excel(SRC["village_directory"], sheet_name=0, header=0, usecols=list(RAW_COLUMNS), dtype=str)
    headers = [str(h).strip() for h in raw.columns]
    expected = [RAW_COLUMNS[k][0] for k in sorted(RAW_COLUMNS)]
    assert headers == expected, f"Village Directory headers changed: {set(expected) ^ set(headers)}"
    v = raw.copy()
    v.columns = [RAW_COLUMNS[k][1] for k in sorted(RAW_COLUMNS)]
    for c in AREA_COLS:
        v[c] = pd.to_numeric(v[c], errors="coerce")
    v["district_code"] = v.district_code.astype(int)
    v["subdistrict_code"] = v.subdistrict_code.str.zfill(5)
    v["source_sum_ha"] = v[SOURCE_COLS].sum(axis=1, min_count=1)
    v["irr_plus_unirr_ne_nas"] = (v.irrigated_area_ha + v.unirrigated_area_ha - v.net_area_sown_ha).abs() > 1
    # evidence for the label swap, per village
    v["sources_match_col387"] = (v.source_sum_ha - v.irrigated_area_ha).abs() < 1
    v["sources_match_col388"] = (v.source_sum_ha - v.unirrigated_area_ha).abs() < 1
    # clipped alternative (config: village_directory_negative_values = clip_irrigated_to_nas)
    v["irrigated_clipped_ha"] = np.minimum(v.irrigated_area_ha, v.net_area_sown_ha)
    v["unirrigated_clipped_ha"] = (v.net_area_sown_ha - v.irrigated_clipped_ha).clip(lower=0)
    return v


def assign_district(v: pd.DataFrame, geo: str) -> pd.Series:
    d = v.district_code.copy()
    if geo == "B":
        d[(v.district_code == THANE) & v.subdistrict_code.isin(PALGHAR_SUBDISTRICTS)] = PALGHAR_LGD
    return d


def district_features(v: pd.DataFrame, geo: str, policy: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    v = v.assign(district_id=assign_district(v, geo))
    g = v.groupby("district_id")
    s = g[AREA_COLS + ["irrigated_clipped_ha", "unirrigated_clipped_ha"]].sum(min_count=1)
    s["n_villages"] = g.size()
    s["n_villages_with_net_area_sown"] = g.net_area_sown_ha.apply(lambda x: int((x > 0).sum()))
    irr = s.irrigated_clipped_ha if policy == "clip_irrigated_to_nas" else s.irrigated_area_ha
    unirr = s.unirrigated_clipped_ha if policy == "clip_irrigated_to_nas" else s.unirrigated_area_ha

    f = pd.DataFrame(index=s.index)
    f["n_villages"] = s.n_villages
    f["total_geographical_area_ha"] = s.total_geographical_area_ha
    f["net_area_sown_ha"] = s.net_area_sown_ha
    f["irrigated_area_ha"] = irr
    f["unirrigated_area_ha"] = unirr
    for c in SOURCE_COLS + ["forest_ha", "current_fallow_ha", "other_fallow_ha", "culturable_waste_ha"]:
        f[c] = s[c]
    f["cropped_land_share_pct"] = s.net_area_sown_ha / s.total_geographical_area_ha * 100
    f["irrigated_share_of_cropped_land_pct"] = irr / s.net_area_sown_ha * 100
    f["rainfed_share_of_cropped_land_pct"] = unirr / s.net_area_sown_ha * 100
    f["irrigated_plus_rainfed_share_pct"] = f.irrigated_share_of_cropped_land_pct + f.rainfed_share_of_cropped_land_pct
    src_total = s[SOURCE_COLS].sum(axis=1)
    f["well_share_of_irrigated_pct"] = s.well_irrigated_ha / src_total * 100
    f["canal_share_of_irrigated_pct"] = s.canal_irrigated_ha / src_total * 100
    f["tank_share_of_irrigated_pct"] = s.tank_irrigated_ha / src_total * 100
    f["forest_share_pct"] = s.forest_ha / s.total_geographical_area_ha * 100
    f["fallow_share_pct"] = (s.current_fallow_ha + s.other_fallow_ha) / s.total_geographical_area_ha * 100
    f = f.reset_index()

    q = pd.DataFrame(index=s.index)
    q["n_villages"] = s.n_villages
    q["n_villages_with_net_area_sown"] = s.n_villages_with_net_area_sown
    q["raw_sum_col387_labelled_total_unirrigated_ha"] = s.irrigated_area_ha
    q["raw_sum_col388_labelled_area_irrigated_by_source_ha"] = s.unirrigated_area_ha
    q["raw_sum_source_wise_irrigated_ha"] = src_total
    q["derived_irrigated_ha"] = irr
    q["derived_unirrigated_ha"] = unirr
    q["net_area_sown_ha"] = s.net_area_sown_ha
    q["derived_irrigated_pct"] = f.set_index("district_id").irrigated_share_of_cropped_land_pct
    q["derived_rainfed_pct"] = f.set_index("district_id").rainfed_share_of_cropped_land_pct
    q["irrigated_plus_unirrigated_minus_nas_ha"] = irr + unirr - s.net_area_sown_ha
    q["villages_irr_plus_unirr_ne_nas"] = g.irr_plus_unirr_ne_nas.sum()
    q["villages_sources_match_col387"] = g.sources_match_col387.sum()
    q["villages_sources_match_col388"] = g.sources_match_col388.sum()
    q["villages_matching_neither"] = g.apply(lambda x: int((~x.sources_match_col387 & ~x.sources_match_col388).sum()), include_groups=False)
    for c in ["net_area_sown_ha", "irrigated_area_ha", "unirrigated_area_ha", "total_geographical_area_ha"]:
        q[f"n_missing_{c}"] = g[c].apply(lambda x: int(x.isna().sum()))
        q[f"n_negative_{c}"] = g[c].apply(lambda x: int((x < 0).sum()))
    q["negative_unirrigated_ha_total"] = g.unirrigated_area_ha.apply(lambda x: float(x[x < 0].sum()))
    q["land_use_parts_minus_geo_area_pct"] = (s[LAND_USE_PARTS].sum(axis=1) - s.total_geographical_area_ha) / s.total_geographical_area_ha * 100
    q["irrigated_pct_if_clipped"] = s.irrigated_clipped_ha / s.net_area_sown_ha * 100
    q["irrigated_pct_keep_raw"] = s.irrigated_area_ha / s.net_area_sown_ha * 100
    q["clip_minus_raw_pct_points"] = q.irrigated_pct_if_clipped - q.irrigated_pct_keep_raw
    q["policy_applied"] = policy
    q = q.reset_index()
    return f, q


def icrisat_cross_check(f: pd.DataFrame) -> pd.DataFrame:
    """Compare Village Directory net area sown (2011) with ICRISAT DLD net cropped area (2010-2012)."""
    d = json.load(open(SRC["icrisat_landuse"], encoding="utf-8"))
    cols = [h["header"] for h in d["headers"]]
    icr = pd.DataFrame(d["data"], columns=cols)
    icr = icr[(icr["State Name"] == "Maharashtra") & icr.Year.isin(["2010", "2011", "2012"])]
    icr["code"] = pd.to_numeric(icr["Indian census District Code 2011"], errors="coerce")
    icr["nca"] = pd.to_numeric(icr["NET CROPPED AREA"], errors="coerce")
    icr = icr[(icr.nca >= 0) & (icr.code > 0)]
    m = icr.groupby("code").nca.mean() * 1000  # 1000 ha -> ha
    out = f[["district_id", "net_area_sown_ha"]].copy()
    out["icrisat_net_cropped_area_2010_12_mean_ha"] = out.district_id.map(m)
    out["vd_over_icrisat_ratio"] = out.net_area_sown_ha / out.icrisat_net_cropped_area_2010_12_mean_ha
    return out


def run(geo: str, cfg: dict, villages: pd.DataFrame) -> pd.DataFrame:
    policy = active(cfg, "village_directory_negative_values")
    f, q = district_features(villages, geo, policy)
    write_csv(f, geo_dir(geo) / "village_directory_district_features.csv")
    write_csv(q, geo_dir(geo) / "village_directory_qa.csv")
    if geo == "A":
        write_csv(icrisat_cross_check(f), geo_dir(geo) / "village_directory_vs_icrisat_net_area.csv")
    return f
