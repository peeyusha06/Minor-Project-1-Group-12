import itertools
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from common import INTERIM  # noqa: E402
from s11_feature_selection import ALT_MEASURES, EXACT, SET_A, SET_B  # noqa: E402

audit = pd.read_csv(INTERIM / "feature_selection_audit.csv")
rec = pd.read_csv(INTERIM / "recommended_pca_features.csv")
summary = pd.read_csv(INTERIM / "feature_set_summary.csv")
master = pd.read_csv(INTERIM / "maharashtra_district_feature_table.csv")
scope = master[master.in_index_scope]
dic = pd.read_csv(INTERIM / "data_dictionary.csv")
candidates = dic[(dic.role == "pca_candidate") & (dic.table == "maharashtra_district_feature_table.csv")].feature


def test_every_candidate_audited_once():
    assert audit.feature.is_unique and rec.feature.is_unique
    assert set(audit.feature) == set(candidates)


def test_sets_exist_and_are_complete_in_scope():
    assert len(SET_A) == 6 and len(SET_B) == 10 and set(SET_A) <= set(SET_B)
    assert set(rec.feature) <= set(master.columns)
    assert scope[SET_B].notna().all().all()


def test_no_exact_or_alternative_pair_inside_a_set():
    flags = audit.set_index("feature").exact_structural_redundancy
    for a, b, _ in EXACT:
        assert flags[a] == "yes" and flags[b] == "yes"
    for a, b, _ in EXACT + ALT_MEASURES:
        for s in (SET_A, SET_B):
            assert not (a in s and b in s), f"{a} and {b} both in a set"


def test_exact_identities_hold_in_data():
    s = scope
    assert ((s.irr_irrigated_share_of_cropped_land_pct + s.irr_rainfed_share_of_cropped_land_pct - 100).abs() < 0.5).all()
    assert ((s.soc_work_participation_rate_pct + s.soc_non_worker_share_pct - 100).abs() < 1e-4).all()
    parts = s.soc_cultivator_share_of_workers_pct + s.soc_agri_labourer_share_of_workers_pct
    assert ((s.soc_agri_worker_share_of_workers_pct - parts).abs() < 1e-4).all()
    diff = s.rain_en_mean_deficit_pct - s.rain_nonen_mean_deficit_pct
    assert ((s.rain_en_minus_nonen_deficit_pct - diff).abs() < 1e-4).all()
    diff = s.rain_en_deficient_frequency - s.rain_nonen_deficient_frequency
    assert ((s.rain_en_minus_nonen_deficient_frequency - diff).abs() < 1e-4).all()


def test_set_summary_matches_recomputation():
    s = summary.set_index("n_variables")
    for cols in (SET_A, SET_B):
        row = s.loc[len(cols)]
        c = scope[cols].corr().abs()
        assert round(max(c.loc[a, b] for a, b in itertools.combinations(cols, 2)), 2) == row.max_abs_r
        assert row.exact_redundancy_remaining == 0 and row.missing_values_in_scope == 0
    assert rec.in_set_A.sum() == 6 and rec.in_set_B.sum() == 10
    n = len(candidates)
    assert len(pd.read_csv(INTERIM / "feature_correlations.csv")) == n * (n - 1) // 2
