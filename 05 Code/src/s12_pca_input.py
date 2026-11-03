"""Step 12 - primary PCA input table (direction-aligned, NOT standardised; no PCA here).

Writes:
  data/interim/pca_input_primary.csv    in-scope districts, 6 original variables + 6 direction-aligned copies
  data/interim/pca_input_metadata.csv   one row per PCA input: sign multiplier, dimension, reason, source, formula

Direction alignment: each variable is multiplied by +1 or -1 (config pca_primary.sign_multipliers)
so that a higher value always means greater vulnerability. The master table is not modified.

Run:  python src/s12_pca_input.py
"""
import pandas as pd

from common import INTERIM, active, load_config, write_csv
from s11_feature_selection import ALT_MEASURES, AUDIT, EXACT

PCA_NAMES = {
    "enso_rain_slope_pct_per_degC": "pca_enso_rain_slope_vulnerability",
    "rain_en_deficient_frequency": "pca_en_deficient_frequency",
    "soc_agri_worker_share_of_workers_pct": "pca_agri_worker_share",
    "irr_rainfed_share_of_cropped_land_pct": "pca_rainfed_share",
    "land_small_holding_share_pct": "pca_small_holding_share",
    "soc_literacy_rate_7plus_pct": "pca_literacy_vulnerability",
}


def main():
    cfg = load_config()
    p = cfg["decisions"]["pca_primary"]
    features, signs = p["features"], p["sign_multipliers"]
    master = pd.read_csv(INTERIM / "maharashtra_district_feature_table.csv")
    dic = pd.read_csv(INTERIM / "data_dictionary.csv").set_index("feature")
    last_year = cfg["decisions"]["study_period"]["last_year"]

    # preparation checks: stop here rather than run PCA on a wrong table
    assert active(cfg, "district_geography") == "B" and (master.geography_version == "B").all()
    assert (master.enso_index == "RONI").all(), "primary table must use RONI only"
    assert len(features) == 6 and set(features) == set(PCA_NAMES) == set(signs)
    for a, b, _ in EXACT + ALT_MEASURES:
        assert not (a in features and b in features), f"redundant pair {a} / {b}"
    scope = master[master.in_index_scope].copy()
    assert len(scope) == 34, f"expected 34 in-scope districts, found {len(scope)}"
    assert scope[features].notna().all().all(), "missing PCA inputs"
    assert all(pd.api.types.is_numeric_dtype(scope[f]) for f in features)
    years = scope.enso_elnino_years.str.split(";").explode().astype(int)
    assert years.max() <= last_year, "a year after the study period entered the ENSO features"
    assert (scope.enso_n_study_years == last_year - cfg["decisions"]["study_period"]["first_year"] + 1).all()

    out = scope[["district_id", "census_2011_district_code", "current_district_name", "geography_version", "enso_index"]].copy()
    for f in features:
        out[f] = scope[f]
    for f in features:
        out[PCA_NAMES[f]] = scope[f] * signs[f]
    out["direction_note"] = "pca_* = original x sign multiplier (pca_input_metadata.csv); higher pca_* = greater vulnerability"

    meta = []
    for f in features:
        s = signs[f]
        meta.append({
            "feature": PCA_NAMES[f], "original_feature": f,
            "direction": "higher = more vulnerable" + (" (sign flipped: original higher = less vulnerable)" if s == -1 else ""),
            "sign_multiplier": s, "conceptual_dimension": AUDIT[f][2], "why_selected": AUDIT[f][7],
            "source": dic.loc[f, "source"], "year": dic.loc[f, "year"], "formula": f"{s} x ({dic.loc[f, 'formula']})",
        })
    write_csv(out, INTERIM / "pca_input_primary.csv")
    write_csv(pd.DataFrame(meta), INTERIM / "pca_input_metadata.csv")
    print(f"PCA input: {len(out)} districts x {len(features)} variables; sign flips: {[f for f in features if signs[f] == -1]}")


if __name__ == "__main__":
    main()
