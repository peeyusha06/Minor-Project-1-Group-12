import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from s17_kmeans_classification import GROUPS, ordered_kmeans  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data" / "processed"
scores = pd.read_csv(OUT / "vulnerability_index_scores.csv")
table = pd.read_csv(OUT / "kmeans_vulnerability_classification.csv")
sens = pd.read_csv(OUT / "kmeans_sensitivity.csv")


def test_every_district_classified_once():
    assert len(table) == 34 and table.district_id.is_unique
    assert set(table.district_id) == set(scores.district_id)
    assert table.vulnerability_group.notna().all()
    m = table.merge(scores[["district_id", "vulnerability_index_0_100"]], on="district_id", suffixes=("", "_index"))
    assert np.allclose(m.vulnerability_index_0_100, m.vulnerability_index_0_100_index)   # index copied unchanged


def test_three_groups_ordered_by_centroid():
    assert table.kmeans_cluster.nunique() == 3
    assert set(table.vulnerability_group) == set(GROUPS)
    cen = table.groupby("vulnerability_group").cluster_centroid.first()[list(GROUPS)].to_numpy()
    assert (np.diff(cen) > 0).all()                                     # Low < Medium < High
    means = table.groupby("vulnerability_group").vulnerability_index_0_100.mean()[list(GROUPS)].to_numpy()
    assert np.allclose(cen, means, atol=1e-4)                           # centroid = mean index of the group
    lo = table.groupby("vulnerability_group").vulnerability_index_0_100.min()[list(GROUPS)].to_numpy()
    hi = table.groupby("vulnerability_group").vulnerability_index_0_100.max()[list(GROUPS)].to_numpy()
    assert (hi[:-1] < lo[1:]).all()                                     # groups do not overlap on the index


def test_ordering_ignores_arbitrary_cluster_numbers():
    values = np.array([1.0, 2, 3, 50, 51, 52, 98, 99, 100])
    _, rank, _ = ordered_kmeans(values)
    assert list(GROUPS[rank]) == ["Low Vulnerability"] * 3 + ["Medium Vulnerability"] * 3 + ["High Vulnerability"] * 3


def test_primary_classification_is_deterministic():
    vi = scores.vulnerability_index_0_100.to_numpy()
    km1, r1, c1 = ordered_kmeans(vi)
    km2, r2, c2 = ordered_kmeans(vi)
    assert (r1 == r2).all() and np.allclose(c1, c2)
    stored = table.set_index("district_id").vulnerability_group
    assert (GROUPS[r1] == stored.loc[scores.district_id].to_numpy()).all()


def test_sensitivity_table_complete():
    expected = {"equal weights", "PCA |loading|, all 6 components", "OECD/JRC factor weights", "hazard + social",
                "Pune-excluded rainfall", "ONI v6 instead of RONI", "tertiles of the primary index (not K-Means)"}
    assert set(sens.comparison) == expected and (sens.n_districts == 34).all()
    assert np.allclose(sens.pct_changing_group, 100 * sens.n_changing_group / 34)
    names = set(table.current_district_name)
    for s in sens.changed_districts.dropna():
        assert {x.split(" (")[0] for x in s.split("; ")} <= names
