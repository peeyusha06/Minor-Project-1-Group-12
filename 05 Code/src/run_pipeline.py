"""Run the full data-engineering pipeline (no PCA, no clustering, no scoring).

Usage (from the project root):
    python src/run_pipeline.py                 # everything
    python src/run_pipeline.py --reuse-rainfall  # skip re-reading 76 NetCDF files if outputs exist

All alternatives are written under data/interim/variants/; the ACTIVE variant chosen in
config/project_decisions.yaml is copied to the top-level data/interim/ file names.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

import s01_crosswalk, s02_census_pca, s03_village_directory, s04_agcensus, s05_rainfall  # noqa: E402
import s06_enso, s07_climate_features, s08_validation, s09_merge, s10_dictionary_report  # noqa: E402
from common import ENSO_INDICES, GEOGRAPHIES, INTERIM, active, district_ids, geo_dir, load_config, variant_dir  # noqa: E402

GEO_FILES = ["census_district_features.csv", "census_consistency_checks.csv", "village_directory_district_features.csv",
             "village_directory_qa.csv", "agriculture_census_features.csv", "agriculture_census_qa.csv",
             "district_monthly_rainfall.csv", "district_annual_monsoon_rainfall.csv", "rainfall_qa.csv",
             "rainfall_extreme_district_years.csv", "drought_validation.csv"]
VARIANT_FILES = ["climate_vulnerability_features.csv", "maharashtra_district_feature_table.csv"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def rainfall_outputs_current(cfg: dict) -> bool:
    """Stored rainfall tables may be reused only if they match the current study period and deficient rule."""
    sp = cfg["decisions"]["study_period"]
    thr = cfg["decisions"]["deficient_monsoon_threshold"]["departure_pct"]
    for g in GEOGRAPHIES:
        f = geo_dir(g) / "district_annual_monsoon_rainfall.csv"
        if not f.exists():
            return False
        a = pd.read_csv(f)
        if a.year.min() != sp["first_year"] or a.year.max() != sp["last_year"]:
            return False
        if not (a.deficient_monsoon == (a.monsoon_departure_pct <= thr)).all():
            return False
    return True


def main(reuse_rainfall: bool = False) -> None:
    cfg = load_config()
    log("loading Census PCA (Maharashtra rows)")
    pca = s02_census_pca.load_pca()
    cw = s01_crosswalk.run(pca, cfg)
    log(f"crosswalk: {len(cw)} rows")
    villages = s03_village_directory.load_villages()
    log(f"village directory: {len(villages)} villages")

    census, vd, agc, val = {}, {}, {}, {}
    for geo in GEOGRAPHIES:
        census[geo] = s02_census_pca.run(pca, geo)
        vd[geo] = s03_village_directory.run(geo, cfg, villages)
        agc[geo] = s04_agcensus.run(geo)
        val[geo] = s08_validation.run(pca, geo, district_ids(geo))
        log(f"geography {geo}: census {len(census[geo])}, village dir {len(vd[geo])}, agcensus {len(agc[geo])}, validation {len(val[geo])}")

    if reuse_rainfall and rainfall_outputs_current(cfg):
        log("reusing existing rainfall outputs")
        annual = {g: pd.read_csv(geo_dir(g) / "district_annual_monsoon_rainfall.csv") for g in GEOGRAPHIES}
    else:
        log("aggregating IMD gridded rainfall (both geographies)")
        annual = s05_rainfall.run(GEOGRAPHIES, cfg)
    rain_qa = {g: pd.read_csv(geo_dir(g) / "rainfall_qa.csv") for g in GEOGRAPHIES}

    enso = s06_enso.run(cfg)
    log("ENSO classification done")
    for geo in GEOGRAPHIES:
        for index in ENSO_INDICES:
            clim = s07_climate_features.run(annual[geo], enso[index], geo, index)
            s09_merge.run(geo, index, cfg, cw, census[geo], vd[geo], agc[geo], clim, rain_qa[geo])
            log(f"variant geo_{geo}__{index}: master table written")

    geo, index = active(cfg, "district_geography"), active(cfg, "enso_index")
    for f in GEO_FILES:
        shutil.copyfile(geo_dir(geo) / f, INTERIM / f)
    for f in VARIANT_FILES:
        shutil.copyfile(variant_dir(geo, index) / f, INTERIM / f)
    log(f"active variant geo_{geo}__{index} copied to data/interim/")

    s10_dictionary_report.run(cfg)
    log("data dictionary and data quality report written")

    import s11_feature_selection
    s11_feature_selection.main()
    log("feature-selection audit written (no PCA run)")

    import s12_pca_input
    s12_pca_input.main()
    log("primary PCA input table written (not standardised; PCA is run separately by s13_pca_primary.py)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse-rainfall", action="store_true")
    main(ap.parse_args().reuse_rainfall)
