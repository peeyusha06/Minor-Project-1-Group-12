import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from common import INTERIM, load_config  # noqa: E402
from s12_pca_input import PCA_NAMES  # noqa: E402

CFG = load_config()
PCA_CFG = CFG["decisions"]["pca_primary"]
master = pd.read_csv(INTERIM / "maharashtra_district_feature_table.csv")
pca_in = pd.read_csv(INTERIM / "pca_input_primary.csv")
annual = pd.read_csv(INTERIM / "district_annual_monsoon_rainfall.csv")


def test_primary_scope_is_34_districts_geography_b_roni():
    assert (master.geography_version == "B").all() and len(master) == 36
    assert master.in_index_scope.sum() == 34 and len(pca_in) == 34
    assert (master.enso_index == "RONI").all() and (pca_in.enso_index == "RONI").all()


def test_primary_study_period_ends_2024():
    assert CFG["decisions"]["study_period"]["last_year"] == 2024
    assert annual.year.min() == 1950 and annual.year.max() == 2024
    assert (master.enso_n_study_years == 75).all()
    years = master.enso_elnino_years.str.split(";").explode().astype(int)
    assert years.max() <= 2024  # 2025 and 2026 never enter the primary features


def test_deficient_threshold_uses_unrounded_departure():
    assert (annual.deficient_monsoon == (annual.monsoon_departure_pct <= -20)).all()
    assert "monsoon_departure_pct_rounded" not in annual.columns
    near = annual[annual.monsoon_departure_pct.between(-20, -19.5, inclusive="neither")]
    assert len(near) > 0 and not near.deficient_monsoon.any()


def test_six_features_with_correct_sign_multipliers():
    expected = {"enso_rain_slope_pct_per_degC": -1, "rain_en_deficient_frequency": 1,
                "soc_agri_worker_share_of_workers_pct": 1, "irr_rainfed_share_of_cropped_land_pct": 1,
                "land_small_holding_share_pct": 1, "soc_literacy_rate_7plus_pct": -1}
    assert PCA_CFG["sign_multipliers"] == expected and len(PCA_CFG["features"]) == 6
    meta = pd.read_csv(INTERIM / "pca_input_metadata.csv").set_index("original_feature")
    assert meta.sign_multiplier.to_dict() == expected


def test_aligned_values_and_originals_untouched():
    m = master[master.in_index_scope].set_index("district_id")
    p = pca_in.set_index("district_id")
    for f, s in PCA_CFG["sign_multipliers"].items():
        assert (p[f] - m.loc[p.index, f]).abs().max() < 1e-9          # original copied unchanged
        assert (p[PCA_NAMES[f]] - s * p[f]).abs().max() < 1e-9          # aligned = sign x original
    assert (m.enso_rain_slope_pct_per_degC < 0).all()                 # master still holds the raw (negative) slope
    assert p[list(PCA_NAMES.values())].notna().all().all()


def test_pca_outputs_consistent():
    out = Path(__file__).resolve().parents[1] / "data" / "processed"
    var = pd.read_csv(out / "pca_primary_variance.csv")
    assert len(var) == 6 and abs(var.explained_variance_ratio.sum() - 1) < 1e-9 and abs(var.eigenvalue.sum() - 6) < 1e-9
    assert len(pd.read_csv(out / "pca_primary_scores.csv")) == 34
    assert len(pd.read_csv(out / "pca_leave_one_out.csv")) == 34
