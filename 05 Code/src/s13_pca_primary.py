"""Step 13 - primary PCA on the six direction-aligned variables + leave-one-district-out stability.

Input : data/interim/pca_input_primary.csv (34 districts, pca_* columns; higher = more vulnerable)
Output: data/processed/pca_primary_variance.csv, pca_primary_loadings.csv, pca_primary_scores.csv,
        data/processed/pca_leave_one_out.csv
No index, ranking or K-Means is produced here.

Run:  python src/s13_pca_primary.py
"""
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from common import INTERIM, ROOT, write_csv

OUT = ROOT / "data" / "processed"
N_CHECK = 3        # components examined in the stability check
MAJOR = 0.4        # |weight| >= 0.4 counts as a major loading (equal weights would be 1/sqrt(6) = 0.41)


def fit_pca(X):
    z = StandardScaler().fit_transform(X)
    pca = PCA().fit(z)
    w = pca.components_.copy()
    # component signs are arbitrary; fix them so the largest-magnitude weight is positive
    for k in range(len(w)):
        if w[k, np.argmax(np.abs(w[k]))] < 0:
            w[k] = -w[k]
    return z, pca, w


def run_pca(df, cols):
    """PCA tables (variance, loadings, scores) and the leave-one-district-out comparison for one input table."""
    X = df[cols].to_numpy()
    p = len(cols)
    z, pca, w = fit_pca(X)

    # eigenvalues of the correlation matrix; they sum to the number of variables (6).
    # (sklearn's explained_variance_ uses n-1 and is larger by n/(n-1); the ratios are identical.)
    eig = pca.explained_variance_ratio_ * p
    names = [f"PC{k + 1}" for k in range(p)]
    variance = pd.DataFrame({"component": names, "eigenvalue": eig,
                             "explained_variance_ratio": pca.explained_variance_ratio_,
                             "cumulative_explained_variance": np.cumsum(pca.explained_variance_ratio_),
                             "eigenvalue_gt_1": eig > 1})

    load = pd.DataFrame({"variable": cols})
    for k, n in enumerate(names):
        load[f"{n}_weight"] = w[k]                        # eigenvector: score = sum(weight x z)
    for k, n in enumerate(names):
        load[f"{n}_loading"] = w[k] * np.sqrt(eig[k])     # correlation between variable and component

    scores = df[["district_id", "census_2011_district_code", "current_district_name"]].copy()
    s = z @ w.T
    for k, n in enumerate(names):
        scores[n] = s[:, k]

    # leave-one-district-out: refit scaler + PCA without district i, compare with the full PCA
    rows = []
    for i in range(len(df)):
        keep = np.arange(len(df)) != i
        _, pca_i, w_i = fit_pca(X[keep])
        r = {"omitted_district_id": df.district_id[i], "omitted_district": df.current_district_name[i]}
        for k in range(p):
            r[f"evr_PC{k + 1}"] = pca_i.explained_variance_ratio_[k]
        for k in range(N_CHECK):
            cos = w_i @ w[k]                              # cosine with every LOO component (unit vectors)
            best = int(np.argmax(np.abs(cos)))
            aligned = w_i[k] * np.sign(cos[k]) if cos[k] != 0 else w_i[k]
            major = np.abs(w[k]) >= MAJOR
            r[f"abs_cosine_PC{k + 1}"] = abs(cos[k])
            r[f"best_match_PC{k + 1}"] = f"PC{best + 1}"
            r[f"order_changed_PC{k + 1}"] = best != k
            r[f"major_sign_changed_PC{k + 1}"] = bool((np.sign(aligned[major]) != np.sign(w[k][major])).any())
            r[f"major_set_changed_PC{k + 1}"] = bool(((np.abs(aligned) >= MAJOR) != major).any())
        # PC2 and PC3 have similar eigenvalues, so they may swap; check whether the plane they span is stable:
        # length of the projection of full PC2 / PC3 onto the plane of LOO PC2 + PC3 (1 = inside the plane)
        for k in (1, 2):
            r[f"PC{k + 1}_in_LOO_PC2_PC3_plane"] = np.sqrt((w_i[1] @ w[k]) ** 2 + (w_i[2] @ w[k]) ** 2)
        rows.append(r)
    loo = pd.DataFrame(rows)
    return variance, load, scores, loo


def main():
    df = pd.read_csv(INTERIM / "pca_input_primary.csv")
    cols = [c for c in df.columns if c.startswith("pca_")]
    variance, load, scores, loo = run_pca(df, cols)

    write_csv(variance, OUT / "pca_primary_variance.csv")
    write_csv(load, OUT / "pca_primary_loadings.csv")
    write_csv(scores, OUT / "pca_primary_scores.csv")
    write_csv(loo, OUT / "pca_leave_one_out.csv")

    pd.set_option("display.width", 200)
    print(variance.round(3).to_string(index=False))
    print(load[["variable"] + [f"PC{k}_weight" for k in range(1, 5)] + [f"PC{k}_loading" for k in range(1, 4)]].round(3).to_string(index=False))
    print(loo[[c for c in loo.columns if c.startswith(("abs_cosine", "order_changed", "major_"))]].describe(include="all").round(3).to_string())


if __name__ == "__main__":
    main()
