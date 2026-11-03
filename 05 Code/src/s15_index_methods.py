"""Step 15 - candidate ways of turning the PCA into ONE vulnerability score (methodology comparison only).

NOT the final index: no method is chosen here, no final ranking, no Low/Medium/High, no K-Means.

Every candidate score is a weighted sum of the standardised, direction-aligned indicators, score = z @ w,
so each method can be compared through its indicator weights w (normalised so that sum |w| = 1;
a negative weight means that indicator LOWERS the score although it is aligned as "higher = more vulnerable").

Methods (formulas and sources in reports/pca_weighting_methods_report.md):
  equal            w_j = 1/p                                                   (baseline, not PCA)
  pc1_only         w = first eigenvector, sign set so sum(w) > 0             (Filmer & Pritchett 2001 style)
  A_var_sum        w = sum_k EVR_k * c_k * v_k over retained k, c_k = sign(sum_j v_jk)   (SoVI-style cardinality)
  A_var_dominant   same, c_k = sign of the component's largest-|weight| indicator
  B_abs_loading    w_j ~ sum_k EVR_k * |L_jk| over retained k                (Pinzon Florez et al. 2026)
  B_abs_all6       same, all six components
  C_oecd_varimax   varimax-rotated retained loadings, each indicator weighted by its largest squared rotated
                   loading x factor variance share (OECD/JRC Handbook 2008, section 6.1)
  hazard_social    0.5 x z(mean z of rainfall indicators) + 0.5 x z(mean z of social/farm indicators)
Retained components: Kaiser rule (eigenvalue > 1), decided again in every scenario.

Run:  python src/s15_index_methods.py   (after s14_rainfall_sensitivity.py)
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from common import INTERIM, ROOT, VARIANTS, load_config, write_csv
from s11_feature_selection import SET_A, SET_B
from s14_rainfall_sensitivity import PUNE, RAIN_COLS

OUT = ROOT / "data" / "processed" / "index_candidates"
# directions of the four Set B additions, as recorded in the feature-selection audit (all: higher = more vulnerable)
SET_B_EXTRA_SIGNS = {"rain_en_max_deficit_pct": 1, "agri_cropped_land_share_pct": 1,
                     "soc_marginal_worker_share_of_workers_pct": 1, "soc_st_share_pct": 1}
HAZARD = ["enso_rain_slope_pct_per_degC", "rain_en_deficient_frequency", "rain_en_max_deficit_pct"]
METHODS = ["equal", "pc1_only", "A_var_sum", "A_var_dominant", "B_abs_loading", "B_abs_all6", "C_oecd_varimax", "hazard_social"]


def load_inputs(scenario):
    """In-scope districts with every Set B indicator direction-aligned (higher = more vulnerable)."""
    cfg = load_config()
    signs = {**cfg["decisions"]["pca_primary"]["sign_multipliers"], **SET_B_EXTRA_SIGNS}
    if scenario == "oni_v6":
        m = pd.read_csv(VARIANTS / "geo_B__ONI_v6" / "maharashtra_district_feature_table.csv")
    else:
        m = pd.read_csv(INTERIM / "maharashtra_district_feature_table.csv")
    if scenario == "pune_excluded":
        c = pd.read_csv(INTERIM / "sensitivity" / "climate_features_pune_excluded.csv").set_index("district_id")
        pune = m.district_id == PUNE          # only Pune lost flagged years in this scenario
        for f, cf in RAIN_COLS.items():
            m.loc[pune, f] = c.loc[PUNE, cf]
    m = m[m.in_index_scope].sort_values("district_id").reset_index(drop=True)
    out = m[["district_id", "current_district_name"]].copy()
    for f in SET_B:
        out[f] = m[f] * signs[f]
    return out


def varimax(L, iters=500, tol=1e-10):
    """Varimax rotation (Kaiser 1958) with Kaiser row normalisation, as in SPSS / the OECD handbook example."""
    h = np.sqrt((L ** 2).sum(axis=1, keepdims=True))
    A = L / h
    p, k = A.shape
    R = np.eye(k)
    d = 0
    for _ in range(iters):
        B = A @ R
        u, s, vt = np.linalg.svd(A.T @ (B ** 3 - B * (B ** 2).sum(axis=0) / p))
        R = u @ vt
        if s.sum() < d * (1 + tol):
            break
        d = s.sum()
    return A @ R * h


def oecd_weights(L):
    """OECD/JRC handbook: square the (rotated) loadings, give each indicator to the factor where its squared loading
    is largest, weight = squared loading / factor variance x factor variance / total explained variance."""
    sq = L ** 2
    ev = sq.sum(axis=0)                                   # variance explained by each (rotated) factor
    f = sq.argmax(axis=1)
    w = sq[np.arange(len(L)), f] / ev[f] * ev[f] / ev.sum()
    return w / w.sum()                                    # handbook footnote 25: rescale to sum to one


def abs_loading_weights(L, evr):
    w = (np.abs(L) * evr).sum(axis=1)
    return w / w.sum()


def pca_parts(z):
    pca = PCA().fit(z)
    v = pca.components_                                   # rows = unit eigenvectors
    evr = pca.explained_variance_ratio_
    L = v.T * np.sqrt(evr * z.shape[1])                   # indicators x components, correlation loadings
    return v, evr, L


def method_weights(z, cols, k=None):
    """Indicator weights of every method for one standardised table; k = retained components (default Kaiser)."""
    v, evr, L = pca_parts(z)
    eig = evr * z.shape[1]
    if k is None:
        k = int((eig > 1).sum())
    w = {"equal": np.full(len(cols), 1 / len(cols))}
    w["pc1_only"] = v[0] * np.sign(v[0].sum())
    w["A_var_sum"] = sum(evr[i] * np.sign(v[i].sum()) * v[i] for i in range(k))
    w["A_var_dominant"] = sum(evr[i] * np.sign(v[i][np.argmax(np.abs(v[i]))]) * v[i] for i in range(k))
    w["B_abs_loading"] = abs_loading_weights(L[:, :k], evr[:k])
    w["B_abs_all6"] = abs_loading_weights(L, evr)
    w["C_oecd_varimax"] = oecd_weights(varimax(L[:, :k]) if k > 1 else L[:, :1])
    # hazard + social: each sub-index = mean z of its indicators, re-standardised so both halves count equally
    hz = np.array([c in HAZARD for c in cols])
    h, s = z[:, hz].mean(axis=1), z[:, ~hz].mean(axis=1)
    w["hazard_social"] = np.where(hz, 0.5 / (hz.sum() * h.std()), 0.5 / ((~hz).sum() * s.std()))
    return {m: x / np.abs(x).sum() for m, x in w.items()}, k


def ranks(score):
    return pd.Series(score).rank(ascending=False, method="min").astype(int).to_numpy()


def factorability(z, cols, label):
    """KMO sampling adequacy (overall and per indicator) and Bartlett's sphericity test (OECD/JRC Handbook 2008)."""
    n, p = z.shape
    r = np.corrcoef(z, rowvar=False)
    inv = np.linalg.inv(r)
    partial = -inv / np.sqrt(np.outer(np.diag(inv), np.diag(inv)))
    np.fill_diagonal(r, 0)
    np.fill_diagonal(partial, 0)
    r2, p2 = (r ** 2).sum(axis=0), (partial ** 2).sum(axis=0)
    chi2 = -(n - 1 - (2 * p + 5) / 6) * np.log(np.linalg.det(np.corrcoef(z, rowvar=False)))
    df = p * (p - 1) / 2
    rows = [{"feature_set": label, "item": "KMO overall", "value": r2.sum() / (r2.sum() + p2.sum())},
            {"feature_set": label, "item": "Bartlett chi-square", "value": chi2},
            {"feature_set": label, "item": "Bartlett df", "value": df},
            {"feature_set": label, "item": "Bartlett p-value", "value": stats.chi2.sf(chi2, df)},
            {"feature_set": label, "item": "largest |correlation| between indicators", "value": np.abs(r).max()}]
    rows += [{"feature_set": label, "item": f"KMO {c}", "value": r2[j] / (r2[j] + p2[j])} for j, c in enumerate(cols)]
    return rows


def retention_table(z):
    """Eigenvalues with parallel-analysis thresholds and bootstrap intervals, plus the K chosen by each rule."""
    n, p = z.shape
    _, evr, _ = pca_parts(z)
    eig = evr * p
    rng = np.random.default_rng(2026)
    rand = np.array([np.linalg.eigvalsh(np.corrcoef(rng.standard_normal((n, p)), rowvar=False))[::-1] for _ in range(5000)])
    boot = np.array([pca_parts(StandardScaler().fit_transform(z[rng.integers(0, n, n)]))[1] * p for _ in range(2000)])
    ev = pd.DataFrame({"component": [f"PC{k + 1}" for k in range(p)], "eigenvalue": eig, "explained_variance_ratio": evr,
                       "cumulative": np.cumsum(evr), "parallel_mean_random": rand.mean(axis=0),
                       "parallel_95pct_random": np.percentile(rand, 95, axis=0),
                       "bootstrap_2.5pct": np.percentile(boot, 2.5, axis=0), "bootstrap_97.5pct": np.percentile(boot, 97.5, axis=0)})

    def first_fail(ok):
        return int(np.argmin(ok)) if not ok.all() else p

    rules = [
        ("Kaiser: eigenvalue > 1", first_fail(eig > 1), "OECD/JRC Handbook 2008, Box 6"),
        ("OECD standard practice: eigenvalue > 1, each > 10% variance, cumulative > 60%",
         first_fail((eig > 1) & (evr > 0.10)), "OECD/JRC Handbook 2008, section 6.1 (cumulative at this K checked below)"),
        ("Jolliffe: eigenvalue > 0.7", first_fail(eig > 0.7), "OECD/JRC Handbook 2008, Box 6"),
        ("Variance explained >= 80%", int(np.argmax(np.cumsum(evr) >= 0.8)) + 1, "OECD/JRC Handbook 2008, Box 6"),
        ("Variance explained >= 90%", int(np.argmax(np.cumsum(evr) >= 0.9)) + 1, "OECD/JRC Handbook 2008, Box 6"),
        ("Horn parallel analysis: eigenvalue > 95th percentile of random-data eigenvalue",
         first_fail(eig > ev.parallel_95pct_random.to_numpy()), "Horn (1965); 5000 random 34 x 6 normal data sets"),
        ("Horn parallel analysis: eigenvalue > mean random-data eigenvalue",
         first_fail(eig > ev.parallel_mean_random.to_numpy()), "Horn (1965)"),
        ("Bootstrap: lower 2.5% bound of eigenvalue > 1", first_fail(ev["bootstrap_2.5pct"].to_numpy() > 1),
         "bootstrap of districts, 2000 resamples (idea from OECD/JRC Handbook 2008, Jackson 1993)"),
        ("All components", p, "no reduction"),
    ]
    rt = pd.DataFrame(rules, columns=["rule", "components_retained", "source"])
    rt["cumulative_variance_at_K"] = [np.cumsum(evr)[k - 1] if k > 0 else 0 for k in rt.components_retained]
    return ev, rt


def main():
    cols_a = list(SET_A)
    scen = {s: load_inputs(s) for s in ("primary", "pune_excluded", "oni_v6")}
    base = scen["primary"]
    names = base.current_district_name.to_numpy()
    z = StandardScaler().fit_transform(base[cols_a])
    w_prim, k_prim = method_weights(z, cols_a)

    # --- Part 3: retention -------------------------------------------------------------------------------
    ev, rt = retention_table(z)
    fact = pd.DataFrame(factorability(z, cols_a, "set_A") +
                        factorability(StandardScaler().fit_transform(base[SET_B]), list(SET_B), "set_B"))
    by_k = []
    v, evr, L = pca_parts(z)
    for k in range(1, 7):
        wk, _ = method_weights(z, cols_a, k)
        for m in ("A_var_sum", "B_abs_loading", "C_oecd_varimax"):
            by_k += [{"method": m, "components_retained": k, "indicator": c, "weight": wk[m][j]} for j, c in enumerate(cols_a)]
    by_k = pd.DataFrame(by_k)

    # --- Parts 2/6/7: candidate weights and scores (Set A, primary data) ----------------------------------
    weights = pd.DataFrame({"indicator": cols_a, **{m: w_prim[m] for m in METHODS}})
    scores = base[["district_id", "current_district_name"]].copy()
    for m in METHODS:
        scores[f"{m}_score"] = z @ w_prim[m]
    for m in METHODS:
        scores[f"{m}_candidate_rank"] = ranks(scores[f"{m}_score"])
    rank_corr = pd.DataFrame([[stats.spearmanr(scores[f"{a}_score"], scores[f"{b}_score"]).statistic for b in METHODS]
                              for a in METHODS], index=METHODS, columns=METHODS).reset_index(names="method")
    move = []
    for m in METHODS:
        d = scores[f"{m}_candidate_rank"] - scores["equal_candidate_rank"]     # positive = lower priority than equal
        move.append({"method": m, "spearman_with_equal": stats.spearmanr(scores[f"{m}_score"], scores["equal_score"]).statistic,
                     "median_abs_rank_move": d.abs().median(), "max_abs_rank_move": d.abs().max(),
                     "largest_move_to_higher_priority": -d.min(), "largest_move_to_lower_priority": d.max(),
                     "district_with_max_move": names[d.abs().idxmax()], "n_districts_moving_5plus": int((d.abs() >= 5).sum()),
                     "n_negative_weights": int((w_prim[m] < 0).sum())})
    move = pd.DataFrame(move)

    # --- Parts 4/5: robustness of weights and scores, Set A and Set B ----------------------------------------
    long, score_rob = [], []
    all_idx = np.arange(len(base))

    def record(fs, cols, full, scenario, data, idx):
        zz = StandardScaler().fit_transform(data[cols])
        w, k = method_weights(zz, cols)
        for m in METHODS:
            for j, c in enumerate(cols):
                long.append({"feature_set": fs, "scenario": scenario, "method": m, "components_retained": k,
                             "indicator": c, "weight": w[m][j]})
            s, ref = zz @ w[m], full[m][idx]
            move = np.abs(ranks(ref) - ranks(s))
            score_rob.append({"feature_set": fs, "scenario": scenario, "method": m, "components_retained": k,
                              "spearman_with_primary": stats.spearmanr(ref, s).statistic,
                              "max_abs_rank_change": int(move.max()), "district_with_max_change": names[idx][move.argmax()]})

    for fs, cols in (("set_A", cols_a), ("set_B", list(SET_B))):
        zf = StandardScaler().fit_transform(base[cols])
        wf, _ = method_weights(zf, cols)
        full = {m: zf @ wf[m] for m in METHODS}
        record(fs, cols, full, "primary", base, all_idx)
        for sc in ("pune_excluded", "oni_v6"):
            assert (scen[sc].district_id.to_numpy() == base.district_id.to_numpy()).all()
            record(fs, cols, full, sc, scen[sc], all_idx)
        for i in range(len(base)):
            record(fs, cols, full, f"loo_{names[i]}", base[all_idx != i], all_idx[all_idx != i])
    long = pd.DataFrame(long)
    score_rob = pd.DataFrame(score_rob)

    summ = []
    for (fs, m, c), g in long.groupby(["feature_set", "method", "indicator"], sort=False):
        g = g.set_index("scenario").weight
        loo = g[g.index.str.startswith("loo_")]
        row = {"feature_set": fs, "method": m, "indicator": c, "primary": g["primary"], "loo_min": loo.min(),
               "loo_max": loo.max(), "loo_range": loo.max() - loo.min(), "loo_min_when_omitting": loo.idxmin()[4:],
               "loo_max_when_omitting": loo.idxmax()[4:], "pune_excluded": g["pune_excluded"], "oni_v6": g["oni_v6"]}
        if fs == "set_A":                 # the same indicator's weight in Set B, rescaled within the six Set A indicators
            b = long[(long.feature_set == "set_B") & (long.scenario == "primary") & (long.method == m)].set_index("indicator").weight
            row["set_B_share_within_set_A"] = b[c] / np.abs(b[cols_a]).sum()
        summ.append(row)
    summ = pd.DataFrame(summ)
    k_used = long[~long.scenario.str.startswith("loo_")].groupby(["feature_set", "scenario"]).components_retained.first().reset_index()
    k_loo = long[long.scenario.str.startswith("loo_")].groupby("feature_set").components_retained.unique().reset_index()
    set_b = long[(long.feature_set == "set_B") & ~long.scenario.str.startswith("loo_")].pivot_table(
        index=["scenario", "indicator"], columns="method", values="weight", sort=False).reset_index()

    write_csv(fact, OUT / "factorability_checks.csv")
    write_csv(ev, OUT / "eigenvalues_retention_checks.csv")
    write_csv(rt, OUT / "retention_rules.csv")
    write_csv(by_k, OUT / "weights_by_components_retained.csv")
    write_csv(weights, OUT / "candidate_weights_set_A.csv")
    write_csv(scores, OUT / "candidate_scores_set_A.csv")
    write_csv(rank_corr, OUT / "method_rank_correlation.csv")
    write_csv(move, OUT / "rank_movement_vs_equal.csv")
    write_csv(long, OUT / "weight_robustness_long.csv")
    write_csv(summ, OUT / "weight_robustness_summary.csv")
    write_csv(score_rob, OUT / "score_robustness.csv")
    write_csv(set_b, OUT / "candidate_weights_set_B.csv")
    write_csv(k_used, OUT / "components_retained_by_scenario.csv")
    print("components retained in LOO runs:", k_loo.to_dict("records"))

    pd.set_option("display.width", 220)
    print(f"Kaiser K (primary) = {k_prim}")
    print(rt.to_string(index=False))
    print(weights.round(3).to_string(index=False))
    print(move.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
