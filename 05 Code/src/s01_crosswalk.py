"""Step 1 - master district crosswalk for geographies A (35, Census 2011) and B (36, current).

All joins are by numeric code (Census 2011 district code / LGD code). Names from every
source are carried alongside for audit; no fuzzy name matching is used anywhere.
"""
from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd

from common import (INTERIM, MUMBAI_CODES, PALGHAR_LGD, PALGHAR_SUBDISTRICTS, SRC, THANE,
                    active, load_config, soi_layer, write_csv)


def census_district_names(pca: pd.DataFrame) -> pd.Series:
    d = pca[(pca.Level == "DISTRICT") & (pca.TRU == "Total")]
    return d.set_index(d.District.astype(int)).Name


def build(pca: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    ref = pd.read_csv(SRC["district_reference"], dtype=str)
    ref["census_2011_district_code"] = ref.census_2011_district_code.astype(int)
    ref["current_lgd_district_code"] = ref.current_lgd_district_code.astype(int)

    census_names = census_district_names(pca)
    soi = soi_layer("DISTRICT_BDY")
    soi_names = soi.set_index(soi.DIST_LGD.astype(int)).DISTRICT
    dm = gpd.read_file(SRC["datameet_shp"])
    dm = dm[dm.ST_NM == "Maharashtra"]
    dm_names = dm.set_index(dm.censuscode.astype(int)).DISTRICT
    icr = pd.DataFrame(json.load(open(SRC["icrisat_districts"], encoding="utf-8")))
    icr = icr[(icr.STNAME == "Maharashtra") & (icr.INDC_DTC > 0)]
    icr_names = dict(zip(icr.INDC_DTC.astype(int), icr.DISTNAME))

    exclude_mumbai = active(cfg, "exclude_mumbai_from_index") == "exclude"
    geo_source = active(cfg, "boundary_source")
    rows = []
    for geo in ("A", "B"):
        for _, r in ref.iterrows():
            cen, lgd = r.census_2011_district_code, r.current_lgd_district_code
            is_palghar = lgd == PALGHAR_LGD
            if geo == "A" and is_palghar:
                continue
            district_id = lgd if geo == "B" else cen
            if geo == "A" and cen == THANE:
                boundary_id = f"SOI_DIST_LGD:{THANE}+{PALGHAR_LGD} (dissolved)"
                sub_rule = "all Census 2011 sub-districts of 517, incl. Palghar talukas " + ";".join(PALGHAR_SUBDISTRICTS)
                parent, current_name = "", "Thane (Census 2011 extent: present-day Thane + Palghar)"
            elif geo == "B" and cen == THANE and not is_palghar:
                boundary_id = f"SOI_DIST_LGD:{THANE}"
                sub_rule = "Census 2011 sub-districts of 517 EXCEPT " + ";".join(PALGHAR_SUBDISTRICTS)
                parent, current_name = "Thane (Census 2011)", r.current_district_name
            elif is_palghar:
                boundary_id = f"SOI_DIST_LGD:{PALGHAR_LGD}"
                sub_rule = "Census 2011 sub-districts " + ";".join(PALGHAR_SUBDISTRICTS) + " of district 517"
                parent, current_name = "Thane (Census 2011)", r.current_district_name
            else:
                boundary_id = f"SOI_DIST_LGD:{cen}"
                sub_rule = f"all Census 2011 sub-districts of {cen}"
                parent, current_name = "", r.current_district_name
            rows.append({
                "geography_version": geo,
                "district_id": district_id,
                "census_2011_state_code": 27,
                "census_2011_district_code": cen,
                "census_2011_district_name": census_names.get(cen, ""),
                "current_district_name": current_name,
                "current_district_code": lgd if not (geo == "A" and cen == THANE) else f"{THANE}+{PALGHAR_LGD}",
                "current_district_code_source": "LGD code from Survey of India DIST_LGD field",
                "marathi_name": r.marathi_name if not (geo == "A" and cen == THANE) else "ठाणे (+ पालघर)",
                "district_boundary_id": boundary_id,
                "boundary_source_active": geo_source,
                "datameet_2011_name": dm_names.get(cen, "") if not is_palghar else "",
                "survey_of_india_name": soi_names.get(lgd, ""),
                "icrisat_name": icr_names.get(cen, "") if not is_palghar else "",
                "agcensus_2010_11_report_name": r.agcensus_2010_11_report_name if isinstance(r.agcensus_2010_11_report_name, str) else "",
                "gr_names_as_printed": r.gr_names_as_printed if isinstance(r.gr_names_as_printed, str) else "",
                "former_names": r.former_names if isinstance(r.former_names, str) else "",
                "parent_district": parent,
                "census_subdistrict_rule": sub_rule,
                "in_index_scope_default": not (exclude_mumbai and cen in MUMBAI_CODES),
                "notes": r.notes if isinstance(r.notes, str) else "",
            })
    cw = pd.DataFrame(rows).sort_values(["geography_version", "district_id"]).reset_index(drop=True)
    return cw


def palghar_reconstruction_table(pca: pd.DataFrame) -> pd.DataFrame:
    sub = pca[(pca.Level == "SUB-DISTRICT") & (pca.TRU == "Total") & (pca.District == str(THANE))]
    sub = sub[["Subdistt", "Name", "TOT_P", "No_HH"]].copy()
    sub["assigned_district_geography_B"] = sub.Subdistt.map(lambda s: "Palghar (681)" if s in PALGHAR_SUBDISTRICTS else "Thane (517)")
    sub["assigned_district_geography_A"] = "Thane (517)"
    sub["census_pca_rule"] = "sum TRU=Total/Rural/Urban sub-district rows"
    sub["village_directory_rule"] = "sum villages whose 'Sub District Code' is in the Palghar set"
    sub["agcensus_rule"] = "sum Table 26 tahsil rows (Wasai, Wada, Dahanu, Palghar, Vikramgad, Jawahar, Mokhada, Talasari)"
    sub["rainfall_rule"] = "area-weighted over the Survey of India Palghar polygon (LGD 681)"
    return sub.rename(columns={"Subdistt": "census_2011_subdistrict_code", "Name": "subdistrict_name",
                               "TOT_P": "population_2011", "No_HH": "households_2011"})


def run(pca: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    cw = build(pca, cfg)
    write_csv(cw, INTERIM / "district_crosswalk.csv")
    write_csv(palghar_reconstruction_table(pca), INTERIM / "palghar_reconstruction_rules.csv")
    return cw
