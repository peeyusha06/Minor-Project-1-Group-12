"""Consistency checks for the paper: numbers against the fixed CSV outputs, citations, cross-references and wording.

Run:  python paper/build/check_paper.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from references import REFS  # noqa: E402

md = (ROOT / "paper" / "paper_source.md").read_text()
src = (ROOT / "paper" / "build" / "paper_content.md").read_text()
fails = []


def need(text, why):
    if text not in md:
        fails.append(f"missing '{text}' ({why})")


f3 = lambda x: f"{x:.3f}"   # noqa: E731
f1 = lambda x: f"{x:.1f}"   # noqa: E731

# PCA variance
v = pd.read_csv(PROC / "vulnerability_index_components.csv")
for r in v.itertuples():
    need(f"| {r.component} | {f3(r.eigenvalue)} | {f1(100 * r.explained_variance_ratio)} | {f1(100 * r.cumulative)} |",
         "Table II row")
need(f"{f1(100 * v.cumulative[2])} percent", "cumulative variance of 3 components")
pa = pd.read_csv(PROC / "index_candidates" / "eigenvalues_retention_checks.csv")
for x in pa.parallel_95pct_random:
    need(f3(x), "parallel analysis 95th percentile")

# factorability
fc = pd.read_csv(PROC / "index_candidates" / "factorability_checks.csv").set_index(["feature_set", "item"]).value
need(f"{fc[('set_A', 'KMO overall')]:.2f}", "KMO")
need(f"χ² = {fc[('set_A', 'Bartlett chi-square')]:.1f}", "Bartlett chi-square")
need(f"p = {fc[('set_A', 'Bartlett p-value')]:.3f}", "Bartlett p")

# weights and loadings
w = pd.read_csv(PROC / "vulnerability_index_weights.csv")
for r in w.itertuples():
    row = " | ".join(f3(x).replace("-", "−") for x in (r.loading_PC1, r.loading_PC2, r.loading_PC3, r.raw_weight, r.weight))
    need(row, f"Table III row {r.original_feature}")
need(f3(w.raw_weight.sum()), "sum of raw weights")
need(f"{w.weight.min():.3f} and {w.weight.max():.3f}", "weight range in text")

# index
s = pd.read_csv(PROC / "vulnerability_index_scores.csv")
vi = s.vulnerability_index_0_100
need(f"mean of {f1(vi.mean())}", "index mean")
need(f"median of {f1(vi.median())}", "index median")
need(f"deviation of {f1(vi.std())}", "index sample SD")
need(f"{f1(vi.quantile(.25))} to {f1(vi.quantile(.75))}", "IQR")
need(f"raw score {f3(s.raw_vulnerability_score.max())}", "Beed raw score")
need(f"raw score {f3(s.raw_vulnerability_score.min()).replace('-', '−')}", "Nagpur raw score")
assert s.current_district_name[vi.idxmax()] == "Beed" and s.current_district_name[vi.idxmin()] == "Nagpur"

# K-Means
k = pd.read_csv(PROC / "kmeans_diagnostics.csv").set_index("k")
need(f3(k.silhouette_score[3]), "silhouette K=3")
need(f3(k.silhouette_score[2]), "silhouette K=2")
need(f3(k.silhouette_score[4]), "silhouette K=4")
for c in k.centroids_low_to_high[3].split(";"):
    need(f"{float(c):.1f}", "centroid")
for b in k.boundaries_between_groups[3].split(";"):
    need(f"{float(b):.1f}", "boundary")
g = pd.read_csv(PROC / "kmeans_vulnerability_classification.csv")
for grp, names in g.groupby("vulnerability_group").current_district_name:
    if not grp.startswith("Medium"):
        for n in names:
            need(n, f"{grp} member")
    rng = g[g.vulnerability_group == grp].vulnerability_index_0_100
    need(f"{f1(rng.min())} to {f1(rng.max())}", f"{grp} range")
need(f"{int(g.kmeans_matches_tertile.sum())} of the 34", "tertile agreement")

# validation
vs = pd.read_csv(PROC / "drought_validation_summary.csv")
for r in vs[vs.role.isin(["historical", "HOLDOUT"])].itertuples():
    need(f3(r.spearman_rho), f"rho {r.year}")
    for grp in ("low", "medium", "high"):
        need(f"{getattr(r, 'mean_' + grp):.2f}", f"mean share {grp} {r.year}")
need("| Districts with any declaration | 26 | 15 | 32 |", "districts with declaration")

# sensitivity
sens = pd.read_csv(PROC / "vulnerability_index_sensitivity.csv")
ks = pd.read_csv(PROC / "kmeans_sensitivity.csv").set_index("comparison").n_changing_group
for r in sens.itertuples():
    need(f"{f3(r.spearman_with_primary)} | {r.max_abs_rank_change} | {ks[r.comparison]} |", f"Table V {r.comparison}")

# citations: every key used, every reference cited, numbering sequential in order of first use
keys = []
for grp in re.findall(r"\[(@[^\]]+)\]", src):
    for kk in grp.split(";"):
        kk = kk.strip()[1:]
        if kk not in keys:
            keys.append(kk)
if set(keys) != set(REFS):
    fails.append(f"citation/reference mismatch: {set(keys) ^ set(REFS)}")
first = [int(n) for n in re.findall(r"\[(\d+)\]", md.split("## REFERENCES")[0])]
seen = []
for n in first:
    if n not in seen:
        seen.append(n)
if seen != sorted(seen) or seen != list(range(1, len(REFS) + 1)):
    fails.append("references are not numbered in order of first citation")

# tables and figures cited in order
body = md.split("## REFERENCES")[0]
text_only = "\n".join(l for l in body.split("\n") if not l.startswith(("**TABLE", "*Fig.", "![")))
roman = ["I", "II", "III", "IV", "V", "VI"]
tab_cites = [m for m in re.findall(r"Table (VI|IV|V|III|II|I)\b", text_only)]
order_t = []
for t in tab_cites:
    if t not in order_t:
        order_t.append(t)
if order_t != roman:
    fails.append(f"tables cited out of order: {order_t}")
fig_cites = []
for f in re.findall(r"Fig\. (\d)", text_only):
    if f not in fig_cites:
        fig_cites.append(f)
if fig_cites != [str(i) for i in range(1, 7)]:
    fails.append(f"figures cited out of order: {fig_cites}")

# wording
low = body.lower()
for bad in ("predicts drought", "accuracy", "probability of drought", "causes drought", "proves", "revolutionary",
            "cutting-edge", "game-changing", "oecd/jrc method was used"):
    if bad in low:
        fails.append(f"discouraged wording: {bad}")
for m_ in re.finditer(r"predict(?!ion center)", low):
    ctx = low[max(0, m_.start() - 60):m_.end() + 20]
    if not re.search(r"not|nor|never|no ", ctx):
        fails.append(f"'predict' without negation: ...{ctx}...")
dashes = [l for l in body.split("\n") if "—" in l and not l.startswith("***")]
if dashes:
    fails.append(f"em dashes outside Abstract/Keywords: {len(dashes)} lines")
for acr in ("ENSO", "IMD", "RONI", "PCA", "AHP", "KMO", "ONI", "IPCC", "GR", "OECD", "JRC", "NOAA"):
    first_use = re.search(rf"\b{acr}\b", body.split("## I. INTRODUCTION")[1])
    if first_use and f"({acr})" not in body:
        fails.append(f"acronym {acr} never defined")
if "Maharashtra" not in md.split("\n")[0] and "Artificial Intelligence-Driven Vulnerability Index Mapping for Districts in Maharashtra to El Niño Droughts Using Socioeconomic and Climatic Principal Component Analysis" not in md:
    fails.append("title changed")

print("\n".join(fails) if fails else "ALL CHECKS PASSED")
sys.exit(1 if fails else 0)
