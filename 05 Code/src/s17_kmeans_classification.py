"""Step 17 - K-Means (K = 3) on the final 0-100 vulnerability index -> Low / Medium / High.

Primary input: ONLY vulnerability_index_0_100 (data/processed/vulnerability_index_scores.csv, 34 districts).
K-Means cluster numbers are arbitrary, so clusters are re-ordered by centroid:
lowest centroid -> Low, middle -> Medium, highest -> High.

Outputs (data/processed/):
  kmeans_vulnerability_classification.csv  one row per district (sorted by index, highest first, for presentation)
  kmeans_diagnostics.csv                   K = 2, 3, 4: inertia, silhouette, sizes, centroids (K = 3 is primary)
  kmeans_sensitivity.csv                   group changes for the comparison versions of the index
  kmeans_secondary_pc_patterns.csv         SECONDARY/EXPLORATORY: K-Means on PC1-PC3 scores (not vulnerability groups)
No drought validation, maps or dashboard here.

Run:  python src/s17_kmeans_classification.py   (after s16)
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from common import ROOT, load_config, write_csv
from s15_index_methods import SET_A, load_inputs
from s16_vulnerability_index import index_from

OUT = ROOT / "data" / "processed"
K = 3
SEED = 2026
N_INIT = 20
GROUPS = np.array(["Low Vulnerability", "Medium Vulnerability", "High Vulnerability"])


def ordered_kmeans(values, k=K):
    """K-Means on one variable; returns raw cluster labels, centroid-order of each district (0 = lowest), centroids."""
    km = KMeans(n_clusters=k, random_state=SEED, n_init=N_INIT).fit(values.reshape(-1, 1))
    centroids = km.cluster_centers_.ravel()
    order = np.empty(k, dtype=int)
    order[np.argsort(centroids)] = np.arange(k)       # cluster with the smallest centroid gets order 0, and so on
    return km, order[km.labels_], centroids


def to_0_100(v):
    v = np.asarray(v, dtype=float)
    return 100 * (v - v.min()) / (v.max() - v.min())


def main():
    cfg = load_config()
    kc = cfg["decisions"]["kmeans_classification"]
    assert (kc["n_clusters"], kc["random_state"], kc["n_init"]) == (K, SEED, N_INIT), "settings differ from config"
    scores = pd.read_csv(OUT / "vulnerability_index_scores.csv")
    assert len(scores) == 34 and scores.district_id.is_unique
    names = scores.current_district_name.to_numpy()
    vi = scores.vulnerability_index_0_100.to_numpy()

    # --- primary classification ------------------------------------------------------------------------
    km, rank, centroids = ordered_kmeans(vi)
    _, rank_again, _ = ordered_kmeans(vi)
    assert (rank == rank_again).all(), "K-Means result is not deterministic"
    for c in range(K):                               # a K-Means centroid is the mean index of its members
        assert np.isclose(centroids[c], vi[km.labels_ == c].mean())
    sorted_centroids = np.sort(centroids)
    assert (np.diff(sorted_centroids) > 0).all()

    tertile = pd.qcut(vi, 3, labels=False)           # simple comparison: lower / middle / upper third by index value
    table = scores[["district_id", "census_2011_district_code", "current_district_name", "vulnerability_index_0_100"]].copy()
    table["kmeans_cluster"] = km.labels_
    table["vulnerability_group"] = GROUPS[rank]
    table["cluster_centroid"] = centroids[km.labels_]
    table["tertile_group"] = np.array(["Lower third", "Middle third", "Upper third"])[tertile]
    table["kmeans_matches_tertile"] = rank == tertile
    table = table.sort_values("vulnerability_index_0_100", ascending=False)   # presentation order only

    # --- K = 2, 3, 4 diagnostics ----------------------------------------------------------------------
    diag = []
    for k in (2, 3, 4):
        m, r, cen = ordered_kmeans(vi, k)
        diag.append({"k": k, "primary": k == K, "inertia": m.inertia_,
                     "silhouette_score": silhouette_score(vi.reshape(-1, 1), m.labels_),
                     "cluster_sizes_low_to_high": ";".join(str((r == g).sum()) for g in range(k)),
                     "centroids_low_to_high": ";".join(f"{c:.2f}" for c in np.sort(cen)),
                     "boundaries_between_groups": ";".join(f"{b:.2f}" for b in (np.sort(cen)[1:] + np.sort(cen)[:-1]) / 2)})
    diag = pd.DataFrame(diag)

    # --- sensitivity: the comparison versions of the index, each classified the same way ---------------
    cand = pd.read_csv(OUT / "index_candidates" / "candidate_scores_set_A.csv")
    assert (cand.district_id.to_numpy() == scores.district_id.to_numpy()).all()
    versions = {"equal weights": cand.equal_score, "PCA |loading|, all 6 components": cand.B_abs_all6_score,
                "OECD/JRC factor weights": cand.C_oecd_varimax_score, "hazard + social": cand.hazard_social_score}
    for name, scen in (("Pune-excluded rainfall", "pune_excluded"), ("ONI v6 instead of RONI", "oni_v6")):
        data = load_inputs(scen)
        assert (data.district_id.to_numpy() == scores.district_id.to_numpy()).all()
        versions[name] = index_from(data[SET_A].to_numpy(), K)[0]
    sens = []
    for name, v in versions.items():
        v = to_0_100(v)
        _, r, cen = ordered_kmeans(v)
        changed = r != rank
        sens.append({"comparison": name, "n_districts": len(v), "spearman_with_primary": stats.spearmanr(vi, v).statistic,
                     "n_changing_group": int(changed.sum()), "pct_changing_group": 100 * changed.mean(),
                     "changed_districts": "; ".join(f"{names[i]} ({GROUPS[rank[i]].split()[0]} -> {GROUPS[r[i]].split()[0]})"
                                                    for i in np.where(changed)[0]),
                     "group_sizes_low_medium_high": ";".join(str((r == g).sum()) for g in range(K)),
                     "centroids_low_medium_high": ";".join(f"{c:.2f}" for c in np.sort(cen))})
    changed = rank != tertile
    sens.append({"comparison": "tertiles of the primary index (not K-Means)", "n_districts": len(vi),
                 "spearman_with_primary": 1.0, "n_changing_group": int(changed.sum()), "pct_changing_group": 100 * changed.mean(),
                 "changed_districts": "; ".join(f"{names[i]} ({GROUPS[rank[i]].split()[0]} -> tertile {tertile[i] + 1})"
                                                for i in np.where(changed)[0]),
                 "group_sizes_low_medium_high": ";".join(str((tertile == g).sum()) for g in range(K)),
                 "centroids_low_medium_high": ";".join(f"{vi[tertile == g].mean():.2f}" for g in range(K))})
    sens = pd.DataFrame(sens)

    # --- SECONDARY / EXPLORATORY: district patterns from PC1-PC3 scores (not vulnerability groups) -------
    pcs = pd.read_csv(OUT / "pca_primary_scores.csv")
    assert (pcs.district_id.to_numpy() == scores.district_id.to_numpy()).all()
    P = pcs[["PC1", "PC2", "PC3"]].to_numpy()
    pm = KMeans(n_clusters=3, random_state=SEED, n_init=N_INIT).fit(P)
    patterns = pcs[["district_id", "current_district_name", "PC1", "PC2", "PC3"]].copy()
    patterns["pattern"] = np.array(["Pattern A", "Pattern B", "Pattern C"])[pm.labels_]
    patterns["vulnerability_group"] = GROUPS[rank]
    patterns["silhouette_score_all"] = silhouette_score(P, pm.labels_)
    patterns = patterns.sort_values(["pattern", "PC1"])

    write_csv(table, OUT / "kmeans_vulnerability_classification.csv")
    write_csv(diag, OUT / "kmeans_diagnostics.csv")
    write_csv(sens, OUT / "kmeans_sensitivity.csv")
    write_csv(patterns, OUT / "kmeans_secondary_pc_patterns.csv")

    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 200)
    print("centroids (Low, Medium, High):", np.round(sorted_centroids, 2))
    print("sizes (Low, Medium, High):", [int((rank == g).sum()) for g in range(K)])
    print("silhouette K=3:", round(diag.silhouette_score[diag.k == 3].iloc[0], 3))
    for g in GROUPS[::-1]:
        t = table[table.vulnerability_group == g]
        print(f"\n{g} ({len(t)}): " + ", ".join(f"{n} {x:.1f}" for n, x in zip(t.current_district_name, t.vulnerability_index_0_100)))
    print("\n" + diag.round(3).to_string(index=False))
    print("\n" + sens.drop(columns="changed_districts").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
