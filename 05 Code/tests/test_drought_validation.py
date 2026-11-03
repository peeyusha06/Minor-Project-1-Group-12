from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
INTERIM = ROOT / "data" / "interim"
scores = pd.read_csv(OUT / "vulnerability_index_scores.csv")
groups = pd.read_csv(OUT / "kmeans_vulnerability_classification.csv")
hist = pd.read_csv(OUT / "drought_validation_districts.csv")
hold = pd.read_csv(OUT / "drought_validation_holdout_2026.csv")
summary = pd.read_csv(OUT / "drought_validation_summary.csv")
val = pd.read_csv(INTERIM / "drought_validation.csv").set_index("district_id")
both = pd.concat([hist, hold], ignore_index=True)


def test_joins_keep_the_34_index_districts():
    for y, d in both.groupby("year"):
        assert len(d) == 34 and set(d.district_id) == set(scores.district_id)
    assert not both.duplicated(["year", "district_id"]).any()
    names = scores.set_index("district_id").current_district_name
    assert (both.current_district_name == both.district_id.map(names)).all()


def test_index_and_groups_match_the_fixed_files():
    idx = scores.set_index("district_id").vulnerability_index_0_100
    grp = groups.set_index("district_id").vulnerability_group
    assert np.allclose(both.vulnerability_index_0_100, both.district_id.map(idx))
    assert (both.vulnerability_group == both.district_id.map(grp)).all()


def test_declarations_never_used_upstream():
    tables = [INTERIM / "maharashtra_district_feature_table.csv", INTERIM / "pca_input_primary.csv",
              OUT / "vulnerability_index_scores.csv", OUT / "kmeans_vulnerability_classification.csv"]
    for t in tables:
        cols = " ".join(pd.read_csv(t, nrows=1).columns).lower()
        assert not any(w in cols for w in ("declared", "drought", "circle", "2026")), t.name
    for n in range(11, 18):
        src = next((ROOT / "src").glob(f"s{n}_*.py")).read_text()
        assert "drought_validation" not in src and "declared_" not in src, n


def test_share_uses_census_taluka_denominator_and_official_totals():
    assert (both.drought_unit_type == "taluka").all()
    assert (both.total_talukas_census_2011 == both.district_id.map(val.total_talukas_census_2011)).all()
    assert np.allclose(both.drought_intensity, both.declared_talukas / both.total_talukas_census_2011, atol=1e-6)
    assert (both.declared_talukas <= both.total_talukas_census_2011).all()
    totals = both.groupby("year").declared_talukas.sum().to_dict()
    assert totals == {2018: 151, 2023: 40, 2026: 265}           # Mumbai City / Suburban are never listed in the GRs


def test_revenue_circles_kept_separate():
    assert "addl_revenue_circles_count_context_only" in hist.columns
    assert not any("circle" in m for m in summary.drought_measure)
    assert "addl_revenue_circles_count_context_only" not in hold.columns


def test_correlations_use_the_intended_districts():
    main = summary[summary.drought_measure.str.startswith("declared taluka share")]
    assert set(main.year.astype(str)) == {"2018", "2023", "2026"} and (summary.n_districts == 34).all()
    for _, row in main.iterrows():
        d = both[both.year == int(row.year)]
        rho = stats.spearmanr(d.vulnerability_index_0_100, d.drought_intensity).statistic
        assert np.isclose(rho, row.spearman_rho, atol=1e-6)
    assert summary.loc[summary.year.astype(str) == "2026", "role"].eq("HOLDOUT").all()
