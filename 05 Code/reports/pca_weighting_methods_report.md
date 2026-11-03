# From PCA to One Vulnerability Score — Methodology Comparison (candidates only)

Script: `src/s15_index_methods.py` (run after `src/s14_rainfall_sensitivity.py`). Outputs: `data/processed/index_candidates/`.
Tests: `tests/test_index_methods.py`.

**Nothing here is final.** No weighting method has been chosen, and `config/project_decisions.yaml` is unchanged.
The "candidate ranks" in `candidate_scores_set_A.csv` exist only to compare methods; they are not the project's
district ranking. No Low/Medium/High classes and no K-Means were produced. 2026 drought data were not used.

---

## 0. Short answers

| Question | Answer (details in the section given) |
|---|---|
| 1. Which PCA-to-index formulations are documented and defensible? | Four families have verified sources: component-score sums with sign ("cardinality") adjustment (SoVI), first-component weights (asset/wealth indices), \|loading\| × eigenvalue indicator weights (applied vulnerability studies), and the OECD/JRC factor-analysis weighting (squared rotated loadings). All are documented. Whether each is *defensible* depends on the data (§2, §3). |
| 2. Which fits THIS project's six direction-aligned indicators best? | **Method B, \|loading\| × explained variance over the retained components.** It is the only PCA method tested that (a) keeps every aligned indicator adding to vulnerability, (b) does not depend on the arbitrary signs of the components, and (c) stays stable under every robustness check. The OECD method (C) is the recognised handbook method and is a strong second candidate, but it gives the El Niño slope a low weight for a technical reason (§3C) and depends more on the number of components. Component-score methods (A) and PC1-only give small holdings (and in some cases rainfed share) a **negative** weight, which contradicts the framework. |
| 3. Component retention? | Kaiser, OECD standard practice and Jolliffe all give **3 components (74.5%)**. Parallel analysis gives only 1, and the bootstrap gives 2. For Method B the choice hardly matters (3 vs 6 components: rank correlation 0.995). Recommended: 3 components by the OECD rule, reporting "all 6" as a sensitivity check and stating the parallel-analysis result openly (§4). |
| 4. Mixed loading signs? | They come from the data: small-holding share is **negatively correlated with all five other aligned indicators**. No PCA method can make it agree with them. Signed methods turn this into a negative weight. Sign-free methods (B, C) keep the direction set by the framework and use PCA only for *how much* each indicator counts (§5). |
| 5. Sensitivity to Pune and leave-one-out? | Method B: the largest LOO weight range is 0.05, and the Pune correction changes weights by ≤ 0.015; rank correlation with the primary is ≥ 0.966 in all 34 LOO runs and 0.995 for Pune. The A methods are unstable: rank correlation falls to 0.79, and to −0.53 for one variant (§6). |
| 6. How different from equal weights? | Very little for sign-safe methods. B's weights are 0.151–0.183 (equal = 0.167); rank correlation with equal weights is 0.993; at most one district moves 5 places. For C the rank correlation is 0.935. The reason is that Set A's indicators are only weakly correlated (KMO = 0.40), so PCA has little shared structure to weight by (§2, §7). |
| 7. Is Set A more robust than Set B? | Neither is clearly better for the sign-safe methods. Set B has a higher KMO (0.59), mainly because its additions overlap with existing indicators (e.g. cropped-land share vs ENSO slope, r = 0.78). It still gives negative weights to small holding, marginal-worker share and ST share in the signed methods, its component count changes when Pune is omitted, and C is less stable in Set B. Set A stays the primary set; Set B stays a sensitivity check (§8). |

---

## 1. Notation

For district *i* and aligned indicator *j* (higher = more vulnerable): z<sub>ij</sub> = standardised value (StandardScaler).
PCA on the 6 × 6 correlation matrix gives:
- eigenvalues λ<sub>k</sub> (they sum to 6)
- explained-variance ratios EVR<sub>k</sub> = λ<sub>k</sub> / 6
- unit eigenvectors v<sub>k</sub> ("weights" in `pca_primary_loadings.csv`)
- loadings L<sub>jk</sub> = v<sub>jk</sub> √λ<sub>k</sub> (the correlation between indicator *j* and component *k*)

Every candidate score is a **weighted sum of the standardised indicators**, S<sub>i</sub> = Σ<sub>j</sub> w<sub>j</sub> z<sub>ij</sub>, including
the component-score methods. Methods can therefore be compared directly through their weights w<sub>j</sub>. All weights are
reported scaled so that Σ|w<sub>j</sub>| = 1. Scaling does not change the ordering of districts.

## 2. First check: is Set A suitable for PCA-based weighting?

The OECD/JRC Handbook (2008, "Step 4" on multivariate analysis) recommends checking factorability before using PCA/FA:
- KMO sampling adequacy of at least 0.6, with 0.8 or more preferred
- Bartlett's test of sphericity

It also notes that PCA/FA weights only correct for overlapping information between correlated indicators, and cannot
be estimated when the indicators are uncorrelated (section 6.1).

| Check (`factorability_checks.csv`) | Set A | Set B |
|---|---|---|
| KMO overall | **0.40** | 0.59 |
| Bartlett chi-square (df), p | 35.5 (15), p = 0.002 | 181.8 (45), p < 0.001 |
| Largest \|correlation\| between indicators | 0.45 | 0.77 |

Set A correlations (aligned directions): the largest is agri-worker share vs literacy (0.45). **Small-holding share is
negatively correlated with every other indicator** (−0.17 to −0.33).

**Meaning:** the indicators are not all independent (Bartlett p = 0.002), but they share little common structure
(KMO 0.40, below the 0.6 guideline). This is partly by design: the feature-selection audit removed redundant
indicators. So PCA-derived weights for Set A are **weakly determined by the data**. This explains most of the results
below.

## 3. Documented methods

### Sources and verification status

| Source | What it documents | Status |
|---|---|---|
| OECD/JRC (2008) *Handbook on Constructing Composite Indicators: Methodology and User Guide* (Nardo, Saisana, Saltelli, Tarantola et al.), [PDF](https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/08/handbook-on-constructing-composite-indicators-methodology-and-user-guide_g1gh9301/9789264043466-en.pdf) | FA/PCA weighting (section 6.1, Tables 16–18, after Nicoletti et al. 2000); retention rules (Box 6, section 6.1); KMO/Bartlett; strengths and weaknesses of PCA (Table 2) | Read. Table 18 weights **reproduced exactly** by our code (test `test_oecd_weights_reproduce_handbook_table_18`) |
| Hazards Vulnerability & Resilience Institute (2016) *The SoVI® Recipe*, University of South Carolina, [PDF](https://sc.edu/study/colleges_schools/artsandsciences/centers_and_institutes/hvri/documents/sovi/sovi_recipe_2016.pdf) | z-scores → PCA with varimax, Kaiser retention → cardinality (+/−) per component → additive sum of components | Read |
| Cutter, Boruff & Shirley (2003) *Social vulnerability to environmental hazards*, Social Science Quarterly 84(2) | Original SoVI (factor analysis, additive model) | Abstract only (full text NOT VERIFIED) |
| Kynclová, P., *Inclusive Growth Index – Methodology*, ch. 6 "Weights", [bookdown](https://bookdown.org/kynclova_petra/IGI_methodology/weights.html) | Components weighted by their share of explained variance; retention "SS loadings > 1 and proportion > 0.1" citing the OECD handbook | Read |
| Pinzón Flórez, Díaz, Echeverry et al. (2026) *Designing a Territorial Composite Vulnerability Index…*, PLOS One 21, [doi:10.1371/journal.pone.0332486](https://doi.org/10.1371/journal.pone.0332486) | w<sub>j</sub> = Σ<sub>k≤K</sub> λ<sub>k</sub>\|L<sub>jk</sub>\|; S<sub>i</sub> = Σ w<sub>j</sub> z<sub>ij</sub>; retention by eigenvalue > 1, scree and Horn's parallel analysis | Read (methods section) |
| Konak, A. (2026) *Data Fusion and Aggregation Methods to Develop Composite Indexes…*, arXiv:2507.09204v2 | Review. Signed form w<sub>i</sub> = Σ<sub>k</sub> a<sub>ki</sub>λ<sub>k</sub> / ΣΣ a<sub>kl</sub>λ<sub>k</sub> over all components, attributed to Salvati & Zitti (2009) and said to be used for drought vulnerability by Kim et al. (2021, Natural Hazards 109) | Read. The original Salvati & Zitti and Kim et al. formulas are **NOT VERIFIED** (paywalled) |
| Filmer & Pritchett (2001) *Estimating wealth effects without expenditure data — or tears*, Demography 38(1) | Asset index: weights = first principal component | Abstract only; method description verified in Tareq et al. (2021) *Heliyon* 7, e06163 |
| Horn (1965), Psychometrika 30 | Parallel analysis for retention | Not re-read in this project; used as described in Pinzón Flórez et al. (2026) |

### A. Component-score composite, weighted by explained variance

- **Formula:** S<sub>i</sub> = Σ<sub>k∈K</sub> (EVR<sub>k</sub> / Σ<sub>K</sub>EVR) · c<sub>k</sub> · PC<sub>ik</sub>, where PC<sub>ik</sub> = Σ<sub>j</sub> v<sub>jk</sub> z<sub>ij</sub>. The implied indicator weight is w<sub>j</sub> ∝ Σ<sub>k</sub> EVR<sub>k</sub> c<sub>k</sub> v<sub>jk</sub>.
  SoVI uses c<sub>k</sub> but gives all components equal weight. The variance-share weighting is the IGI variant.
- **What the weights mean:** each component counts in proportion to how much of the district-to-district variation it
  explains.
- **Signs:** component signs are arbitrary, so each component needs a "cardinality" c<sub>k</sub> = +1 or −1. SoVI sets it
  by interpreting the dominant variables. Two objective rules were tested:
  - sum rule: c<sub>k</sub> = sign(Σ<sub>j</sub> v<sub>jk</sub>)
  - dominant rule: c<sub>k</sub> = sign of the largest-|v| entry

  **They disagree for PC3.** Its weights sum to −0.20, but its largest entry is rainfed share (+0.64).
- **Do all six indicators add to vulnerability? No.** The sum rule gives rainfed share −0.154 and small holding −0.064.
  The dominant rule gives small holding −0.232. With all 6 components, rainfed share is still −0.10.
- **Mixed-sign components:** cardinality flips a *whole* component. When a component contains aligned indicators with
  opposite signs (PC1: small holding −0.66; PC3: rainfed +0.69 vs agri workers −0.53), no choice of c<sub>k</sub> is right
  for all of them.
- **Absolute loadings:** not used; the method depends on signs.
- **Retention:** only the retained components are used (Kaiser, K = 3).
- **34 districts:** the cardinality decision itself flips between LOO runs. Omitting Nagpur gives a rank correlation
  with the primary of −0.53 (dominant rule) and 0.79 (sum rule), and switching to ONI v6 gives 0.78 (sum rule).
- **Verdict:** documented, but **not compatible** with direction-aligned indicators here. Reported only for comparison.

### PC1-only (Filmer & Pritchett style)

- **Formula:** w = v<sub>1</sub>, with the sign set so that Σw > 0.
- **Assumption:** one underlying factor explains most of the shared variation.
- **Here:** PC1 explains only 34%. It gives small holding −0.20 and El Niño deficient frequency only +0.06, which
  becomes −0.06 under ONI v6.
- **Verdict:** not compatible, for the same reason as A.

### B. |loading| × explained variance (indicator-weight approach)

- **Formula:** w<sub>j</sub> = Σ<sub>k∈K</sub> EVR<sub>k</sub>·|L<sub>jk</sub>| / Σ<sub>j</sub>Σ<sub>k∈K</sub> EVR<sub>k</sub>·|L<sub>jk</sub>|, and S<sub>i</sub> = Σ<sub>j</sub> w<sub>j</sub> z<sub>ij</sub>.
  - Using λ<sub>k</sub> instead of EVR<sub>k</sub> (as Pinzón Flórez et al. do) gives identical normalised weights, because EVR = λ/6.
  - Using eigenvector entries |v| instead of loadings gives 0.155–0.185, also close to equal.
- **What the weights mean:** how strongly each indicator is tied to the important (retained, variance-weighted) patterns
  in the data. They do **not** measure theoretical importance or direction. The handbook makes the same general point
  about PCA/FA weights.
- **Signs:** the absolute value makes the weights independent of the arbitrary component signs (tested). Every weight is
  positive, so all six aligned indicators add to vulnerability.
- **Mixed-sign components:** the absolute value counts "moves opposite to the others" (small holding on PC1, −0.66)
  the same as "moves with them". This is acceptable **only because the direction has already been fixed by the
  framework**. PCA then decides only the size of each weight. The report must say this; the method cannot be used to
  claim that the data show small holdings increase vulnerability.
- **Is the absolute value appropriate?** Yes for this purpose. The signed version (Konak's eq. 6 over all components)
  changes whenever a component's arbitrary sign is flipped, so it is not well-defined unless signs are fixed first, and
  fixing them brings back the cardinality problem of A.
- **Retention:** the weights barely change for K = 3 to 6 (e.g. slope 0.168–0.178). They change at K = 1, where they
  equal |PC1 loadings| and deficient frequency falls to 0.06.
- **34 districts:** the most stable PCA-derived weights tested (§6).
- **Caveat:** the weights are close to equal (0.151–0.183). This is a real result (KMO 0.40), not an error.

### C. OECD/JRC Handbook factor-analysis weighting (Nicoletti et al. 2000 approach)

- **Steps** (handbook section 6.1):
  1. Retain *m* components.
  2. Rotate them (varimax, with Kaiser normalisation).
  3. Square the rotated loadings.
  4. Assign each indicator to the factor where its squared loading is largest, and scale within that factor.
  5. Weight each factor by its share of the explained variance.
  6. Rescale the final weights to sum to 1 (handbook footnote 25).

  Algebraically this reduces to w<sub>j</sub> ∝ max<sub>k</sub> L̃<sub>jk</sub>², the largest squared rotated loading.
- **Here (K = 3), rotated factors:**
  - F1: agri workers 0.90, literacy 0.77, slope 0.49
  - F2: deficient frequency 0.93, slope 0.60
  - F3: rainfed 0.92, small holding −0.66
- **Weights:** slope 0.092, deficient frequency 0.224, agri workers 0.206, rainfed 0.216, small holding 0.112,
  literacy 0.151.
- **Signs:** squaring removes signs, so all weights are positive. Small holding's weight comes from a factor on which it
  loads *negatively* (−0.66); squaring hides the sign conflict, as the absolute value does in B.
- **Why the slope gets the lowest weight:** it is linked to both the social factor (0.49) and the hazard factor (0.60),
  so neither squared loading is large. The method rewards an indicator for belonging clearly to one factor, not for
  being important. For the core El Niño indicator this is a conceptual drawback.
- **Retention:** sensitive to it. The slope's weight is 0.175 at K = 2, 0.092 at K = 3 and 0.100 at K = 4. With one
  factor, deficient frequency falls to 0.018.
- **34 districts:** the handbook itself lists sensitivity to small samples, outliers and data revisions as weaknesses
  of PCA/FA weights (Table 2), and assumes the indicators are factorable (KMO ≥ 0.6, not met here).
- **Verdict:** the most authoritative source and fully reproducible, but its assumptions are only partly met. It is a
  strong sensitivity candidate.

## 4. Component retention (`retention_rules.csv`, `eigenvalues_retention_checks.csv`)

| Rule | Components kept | Cumulative variance |
|---|---|---|
| Kaiser (eigenvalue > 1) | 3 | 74.5% |
| OECD standard practice (eigenvalue > 1, each > 10%, cumulative > 60%) | 3 | 74.5% |
| Jolliffe (eigenvalue > 0.7) | 3 | 74.5% |
| ≥ 80% variance | 4 | 85.5% |
| ≥ 90% variance | 5 | 95.8% |
| Horn parallel analysis (95th percentile of random eigenvalues, 5000 random 34 × 6 data sets) | **1** | 34.3% |
| Horn parallel analysis (mean random eigenvalue) | 1 | 34.3% |
| Bootstrap (lower 2.5% bound of the eigenvalue > 1; 2000 resamples of districts) | 2 | 55.0% |
| All components | 6 | 100% |

| Component | Eigenvalue | Random 95th percentile | Bootstrap 95% interval |
|---|---|---|---|
| PC1 | 2.056 | 1.874 | 1.86 – 2.70 |
| PC2 | 1.246 | 1.465 | 1.14 – 1.64 |
| PC3 | 1.165 | 1.194 | 0.81 – 1.24 |

**Reading:** only PC1 is clearly larger than what random data of this size would give. PC2 and PC3 have overlapping
intervals, which is why they swap in the leave-one-out check. This is the small-sample limitation in numbers.

**Recommended rule for the index:** K = 3 by the OECD standard-practice rule, with all 6 components as a sensitivity
check. Reasons:
1. It is the handbook's documented rule, and all three eigenvalue rules agree.
2. For Method B the choice barely matters: K = 3 vs K = 6 weights differ by ≤ 0.012, rank correlation 0.995.
3. K = 1 (parallel analysis) would base the weights on PC1 alone, which is the mixed-sign component, and would give
   El Niño deficient frequency almost no weight.

The parallel-analysis result should be stated openly as a limitation, not hidden.

## 5. Mixed loading signs — what they are and how to handle them

- **Where they come from:** districts with a high small-holding share tend to score *lower* on the other five
  aligned indicators: weaker El Niño rainfall link, lower agri-worker share, less rainfed land and higher literacy.
  So in the data, small-holding share goes the opposite way to the other five (all five correlations negative).
  This is a fact about Maharashtra's geography, not a PCA error.
- **Options:**
  1. **Signed methods (A, PC1-only):** small holding gets a negative weight, meaning "more smallholders = less
     vulnerable". This contradicts the framework's stated direction. **Reject.**
  2. **Sign-free methods (B, C):** the framework fixes the direction and PCA fixes only the size. **Recommended**,
     with the limitation written down.
  3. **Drop or replace small holding:** not justified by these results. Removing an indicator because it disagrees
     would be choosing variables for a convenient answer. The feature-selection audit kept it for a stated reason.
  4. **Separate sub-indices (hazard / social):** keeps hazard and social indicators apart, but small holding is also
     negatively correlated with agri workers (−0.30) and rainfed share (−0.33) *inside* the social group. So this
     does not remove the issue; it only makes it less visible.

## 6. Robustness of the weights (`weight_robustness_summary.csv`, `score_robustness.csv`)

Set A, Kaiser K = 3 (K was 3 in every scenario and every LOO run).

| Method | Largest LOO weight range (indicator) | Largest weight change, Pune correction | Largest weight change, ONI v6 | LOO rank ρ min (median) | Pune ρ | ONI ρ |
|---|---|---|---|---|---|---|
| Equal | 0 | 0 | 0 | 0.990 (0.999) | 0.991 | 0.967 |
| Hazard + social | 0.018 | 0.003 | 0.020 | 0.995 (0.999) | 0.996 | 0.964 |
| **B \|loading\|, K = 3** | **0.053 (deficient freq.)** | **0.013** | **0.038** | **0.966 (0.998)** | **0.995** | **0.961** |
| B \|loading\|, all 6 | 0.048 | 0.011 | 0.018 | 0.981 (0.998) | 0.998 | 0.981 |
| C OECD varimax | 0.077 (slope) | 0.020 | 0.023 | 0.974 (0.997) | 0.990 | 0.944 |
| PC1-only | 0.158 (deficient freq.) | 0.038 | 0.118 (sign flips) | 0.970 (0.998) | 0.997 | 0.982 |
| A, sum rule | 0.283 (rainfed; sign flips) | 0.019 | 0.262 | 0.794 (0.989) | 0.994 | 0.775 |
| A, dominant rule | 0.550 (agri workers; sign flips) | 0.040 | 0.105 | **−0.528** (0.994) | 0.994 | 0.910 |

- ρ = Spearman rank correlation between the scenario's candidate score and the primary candidate score (for LOO, over
  the 33 remaining districts).
- For every sign-safe method the lowest LOO ρ is never below 0.966 (it comes from omitting Pune for B, Nandurbar for C, Thane for equal weights and Nagpur for hazard + social).
- Part of the "Pune" change for all methods, equal weights included, is simply Pune's own inputs changing. Pune itself
  moves up to 7 places.

**Conclusion:** B is the most stable PCA-derived method, apart from B-all6, which is equally stable and nearly
identical. The Pune correction hardly affects any weights; the ONI v6 switch matters a little more (ρ 0.94–0.98 for
the sign-safe methods).

## 7. PCA-based weights vs equal weights (`rank_movement_vs_equal.csv`, `method_rank_correlation.csv`)

| Method | Negative weights | ρ with equal | Median \|rank move\| | Largest move up / down | Districts moving ≥ 5 places |
|---|---|---|---|---|---|
| B \|loading\|, K = 3 | 0 | 0.993 | 0 | 3 / 5 | 1 |
| B \|loading\|, all 6 | 0 | 0.988 | 0 | 3 / 7 | 1 |
| C OECD varimax | 0 | 0.935 | 1 | 9 / 10 | 7 |
| Hazard + social | 0 | 0.998 | 0 | 1 / 2 | 0 |
| PC1-only | 1 | 0.752 | 5 | 18 / 14 | 18 |
| A, sum rule | 2 | 0.727 | 4 | 16 / 11 | 16 |
| A, dominant rule | 1 | 0.675 | 5 | 21 / 14 | 19 |

The sign-safe methods (B, C, hazard + social) agree closely with each other (ρ 0.91–0.995) and with equal weights.
The methods that allow negative weights disagree with everything else. **In plain terms:** for these six indicators,
PCA does not find a reason to weight any indicator much more than the others. The index ordering is therefore robust
to the weighting choice, as long as the framework's directions are respected. That is worth reporting as a strength.
Honesty requires also saying that PCA adds little beyond equal weighting here.

## 8. Set A vs Set B (`candidate_weights_set_B.csv`)

| | Set A (6) | Set B (10) |
|---|---|---|
| KMO | 0.40 | 0.59 |
| Kaiser components | 3 in every run | 4 (3 when Pune is omitted) |
| Negative weights in signed methods | small holding (and rainfed) | small holding, marginal-worker share, ST share (deficient freq. ≈ 0) |
| B weights | 0.151 – 0.183 | 0.077 – 0.113 (equal = 0.100) |
| B: LOO ρ min / ONI ρ | 0.966 / 0.961 | 0.982 / 0.949 |
| C: LOO ρ min / ONI ρ | 0.974 / 0.944 | 0.917 / 0.956 |

Set B's higher KMO comes mostly from its additions overlapping with existing indicators: cropped-land share vs ENSO
slope 0.78, marginal workers vs cropped land 0.75, worst El Niño deficit vs slope 0.72. That is shared information, not
new evidence. Set B does not remove the sign conflict (it adds two more negatively weighted indicators in the signed
methods), and it is not more robust overall. **Set A remains the primary set.** This conclusion does not depend on
which set gives a more convenient district ordering; ordering was not used in the comparison.

## 9. Hazard + social comparison

- **Rule:**
  - Hazard sub-index H = mean z of the two El Niño rainfall indicators (in Set B: the three rainfall indicators).
  - Social/farm sub-index S = mean z of the four other indicators.
  - Each sub-index is re-standardised, then V = 0.5·z(H) + 0.5·z(S), so hazard and social count equally.
- **Implied weights:** 0.177 for each hazard indicator and 0.161 for each social indicator. They are nearly equal
  because the four social indicators partly cancel each other out (the small-holding correlations are negative), so
  their average varies less and is scaled up by the re-standardisation.
- **Results:** ρ with equal weights 0.998, and the most stable method overall (LOO ρ ≥ 0.995).
- **Use:** a transparent, easy-to-explain comparison method. It is not PCA-based.

## 10. Candidate tables produced

`data/processed/index_candidates/`:

| File | Contents |
|---|---|
| `candidate_weights_set_A.csv` | Weights of all 8 methods |
| `candidate_scores_set_A.csv` | Score and candidate rank per district per method (**candidate only**) |
| `candidate_weights_set_B.csv` | Set B weights (primary and Pune-corrected) |
| `weights_by_components_retained.csv` | Methods A, B, C for K = 1–6 |
| `retention_rules.csv`, `eigenvalues_retention_checks.csv`, `factorability_checks.csv` | Retention and factorability checks |
| `weight_robustness_long.csv`, `weight_robustness_summary.csv`, `score_robustness.csv`, `components_retained_by_scenario.csv` | Robustness results |
| `method_rank_correlation.csv`, `rank_movement_vs_equal.csv` | Method comparison |

## 11. Recommendation for the team/guide decision (NOT yet written into the config)

1. **Primary index weighting (proposed):** Method B, |loading| × explained variance over the components retained by the
   OECD standard-practice rule (K = 3), applied to the standardised Set A indicators, S<sub>i</sub> = Σ w<sub>j</sub> z<sub>ij</sub>.
2. **Report alongside it:** equal weights (baseline), the OECD/JRC method (C), hazard + social (V), B with all 6
   components, and the Pune-corrected and ONI v6 versions. The final report should say that the sign-safe methods
   agree (ρ ≥ 0.93).
3. **Do not use** component-score sums (A) or PC1-only as the index. They give aligned indicators negative weights and
   are unstable with 34 districts.
4. **State the limitations:**
   - KMO 0.40, so PCA weights are close to equal.
   - Only PC1 passes parallel analysis.
   - The small-holding direction is set by the framework, not shown by the data.
   - Pune remains influential.
5. **Decisions still to confirm** (to be added to `config/project_decisions.yaml` only after confirmation):
   - `index_weighting_method`
   - `index_component_retention`
   - the score scale for mapping (e.g. min–max 0–100 as in Pinzón Flórez et al. 2026, or z-score)
   - then the Low/Medium/High classification rule (K-Means on the final score vs quantiles), not yet started
