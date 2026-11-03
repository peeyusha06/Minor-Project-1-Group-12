import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from common import INTERIM, ROOT  # noqa: E402
from s13_pca_primary import run_pca  # noqa: E402
from s15_index_methods import (HAZARD, METHODS, SET_A, abs_loading_weights, load_inputs, method_weights,  # noqa: E402
                               oecd_weights, pca_parts, varimax)

CANDIDATES = ROOT / "data" / "processed" / "index_candidates"
base = load_inputs("primary")
z = StandardScaler().fit_transform(base[SET_A])


def test_oecd_weights_reproduce_handbook_table_18():
    # OECD/JRC Handbook (2008) Table 17: rotated TAI factor loadings; Table 18: resulting "PC" weights
    L = np.array([[.07, .97, .06, .06], [.13, .07, -.07, .93], [.79, -.21, .21, .42], [-.64, .56, -.04, .36],
                  [.37, .17, .38, .68], [.82, -.04, .25, .35], [.88, .23, -.09, .09], [.08, .04, .96, .04]])
    table_18 = [0.17, 0.15, 0.11, 0.07, 0.08, 0.12, 0.14, 0.16]
    assert np.abs(oecd_weights(L) - table_18).max() < 0.006


def test_varimax_is_an_orthogonal_rotation():
    _, _, L = pca_parts(z)
    R = varimax(L[:, :3])
    assert np.allclose((R ** 2).sum(axis=1), (L[:, :3] ** 2).sum(axis=1))     # communalities unchanged
    T = np.linalg.lstsq(L[:, :3], R, rcond=None)[0]
    assert np.allclose(T.T @ T, np.eye(3), atol=1e-8)


def test_abs_loading_weights_ignore_arbitrary_component_signs():
    _, evr, L = pca_parts(z)
    flipped = L * np.array([1, -1, 1, -1, 1, -1])
    assert np.allclose(abs_loading_weights(L[:, :3], evr[:3]), abs_loading_weights(flipped[:, :3], evr[:3]))
    w = abs_loading_weights(L, evr)
    assert (w > 0).all() and np.isclose(w.sum(), 1)


def test_candidate_scores_are_weighted_sums_of_z():
    scores = pd.read_csv(CANDIDATES / "candidate_scores_set_A.csv")
    w, k = method_weights(z, SET_A)
    assert k == 3 and set(w) == set(METHODS)
    for m in METHODS:
        assert np.isclose(np.abs(w[m]).sum(), 1)
        assert np.allclose(scores[f"{m}_score"], z @ w[m], atol=1e-5)          # CSV stores 6 decimals
    assert np.allclose(scores.equal_score, z.mean(axis=1), atol=1e-5)
    hz = np.isin(SET_A, HAZARD)
    h, s = z[:, hz].mean(axis=1), z[:, ~hz].mean(axis=1)
    expected = 0.5 * h / h.std() + 0.5 * s / s.std()
    ratio = scores.hazard_social_score / expected
    assert np.allclose(ratio, ratio.iloc[0], atol=1e-4)                         # same score up to a positive scale
    for m in ("B_abs_loading", "B_abs_all6", "C_oecd_varimax", "equal", "hazard_social"):
        assert (w[m] > 0).all()                                               # every aligned indicator adds vulnerability


def test_rainfall_sensitivity_changes_only_rainfall_inputs():
    primary = pd.read_csv(INTERIM / "pca_input_primary.csv")
    rain = ["enso_rain_slope_pct_per_degC", "rain_en_deficient_frequency",
            "pca_enso_rain_slope_vulnerability", "pca_en_deficient_frequency"]
    dropped = pd.read_csv(ROOT / "data" / "processed" / "sensitivity" / "rainfall_sensitivity_dropped_district_years.csv")
    for name in ("pune_excluded", "all_flagged_excluded"):
        sens = pd.read_csv(INTERIM / "sensitivity" / f"pca_input_{name}.csv")
        other = [c for c in primary.columns if c not in rain]
        assert sens[other].equals(primary[other])
        changed = set(primary.district_id[(sens[rain] - primary[rain]).abs().max(axis=1) > 1e-9])
        assert changed <= set(dropped.district_id[dropped.scenario == name])
    assert set(dropped.district_id[dropped.scenario == "pune_excluded"]) == {521}


def test_primary_pca_outputs_still_match_primary_input():
    primary = pd.read_csv(INTERIM / "pca_input_primary.csv")
    cols = [c for c in primary.columns if c.startswith("pca_")]
    _, load, _, _ = run_pca(primary, cols)
    stored = pd.read_csv(ROOT / "data" / "processed" / "pca_primary_loadings.csv")
    assert np.allclose(load.drop(columns="variable"), stored.drop(columns="variable"), atol=1e-6)
