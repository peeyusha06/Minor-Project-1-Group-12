# Paper Audit: Final Implemented Project (before writing the IEEE paper)

Audit date: 4 October 2026. Repository state: commit `ab8dc27` (dashboard), working tree clean apart from untracked PPT files.
Test suite: `python3 -m pytest tests -q` gives **69 passed** (run during this audit).

Every number below was read from the final output files named in brackets, not from memory. Where a report and a CSV
both give a value, both were checked and agree unless listed in section 20.

---

## 1. Final research problem

District drought vulnerability to El Niño cannot be judged from rainfall alone. A district's position depends on how
strongly its monsoon rainfall has historically weakened in El Niño years (exposure), how much of its economy and land
depend on rain-fed agriculture (sensitivity) and its socioeconomic ability to cope (adaptive capacity). The project
asks how these climatic, agricultural and socioeconomic indicators can be combined, with objective statistical weights,
into one relative vulnerability index for Maharashtra's districts, and whether that index is consistent with observed
drought declarations. [`reports/final_vulnerability_index_report.md` §1; `reports/feature_selection_report.md` §1, §9]

## 2. Final research objective

Build an exploratory composite El Niño drought-vulnerability index for the 34 in-scope districts of Maharashtra by
(i) constructing six direction-aligned indicators from official climate, census and agricultural sources,
(ii) deriving indicator weights from PCA (absolute-loading method, 3 components), (iii) scaling the index to 0–100,
(iv) classifying districts into Low / Medium / High groups with K-Means (K = 3) applied to the final index, and
(v) checking the index against Government of Maharashtra drought declarations for 2018, 2023 and a 2026 holdout,
with maps and a read-only Streamlit dashboard. [`config/project_decisions.yaml` → `vulnerability_index`,
`kmeans_classification`, `validation`]

## 3. Final study area

- Maharashtra, current administrative geography ("geography B"): **36 districts**. Palghar (LGD 681) is rebuilt from
  its 8 Census 2011 sub-districts in every source. [config `district_geography`, active B, FIXED]
- **34 districts** in the index. Mumbai City (519) and Mumbai Suburban (518) are excluded because the Village Directory
  has no villages and the Agriculture Census reports no holdings for them. [config `exclude_mumbai_from_index`;
  `vulnerability_index_scores.csv` has 34 rows]
- Title (changed 8 October 2026 to match the Maharashtra scope and avoid acronyms): "Artificial Intelligence-Driven Vulnerability Index Mapping for Districts in Maharashtra to El Niño Droughts Using Socioeconomic and Climatic Principal Component Analysis". The earlier
  title was "AI-Driven Vulnerability Index Mapping for Districts in India to El Niño Droughts Using Socioeconomic and Climatic PCA".

## 4. Final datasets and sources [`data/raw/source_manifest.csv`]

| Dataset | Publisher | Use |
|---|---|---|
| IMD 0.25° × 0.25° gridded daily rainfall (NetCDF), 1950–2024 (Pai et al., 2014) | India Meteorological Department, Pune | Monsoon rainfall per district |
| Relative Oceanic Niño Index (RONI), ERSST.v6 | NOAA Climate Prediction Center | Primary ENSO index (official NOAA index since 1 Feb 2026) |
| Oceanic Niño Index (ONI), ERSST.v6 | NOAA CPC | Sensitivity only |
| Census of India 2011 Primary Census Abstract | Office of the Registrar General & Census Commissioner | Agricultural-worker share, literacy |
| Census of India 2011 District Census Handbook, Village Directory, Maharashtra (release 2700) | ORGI | Rainfed share of net sown area |
| Agriculture Census 2010-11 (Phase I) Maharashtra State Report | Commissionerate of Agriculture, Govt. of Maharashtra (2014) | Small-holding share |
| Administrative Boundary Database OVSF/1M/8, Maharashtra | Survey of India | District polygons (rainfall aggregation, maps) |
| Drought GRs 31-10-2018 (151 talukas), 31-10-2023 (40 talukas), 25-09-2026 (265 talukas, Trigger-1) | Government of Maharashtra | **Validation only** |
| Supplementary GRs: 268 revenue circles (06-11-2018), 1,021 revenue circles (10-11-2023) | Government of Maharashtra | Context only (not an intensity measure) |

Note: the exact download URL of the Census 2011 PCA workbook is recorded as NOT VERIFIED in the manifest (downloaded by
the user; publisher is certain). ICRISAT, DataMeet and geoBoundaries files are cross-checks only and are not used in the index.

## 5. Final study period

- Primary climate period: **1950–2024** (75 monsoons; first year of both NOAA series, last year IMD lists as available).
- Rainfall baseline: **1971–2020** district mean June–September rainfall (IMD's current LPA period), computed from the grid.
- **2025**: sensitivity only, not used in any primary table. **2026**: validation holdout only.
- 18 El Niño monsoon years under RONI: 1951, 1953, 1957, 1963, 1965, 1972, 1976, 1977, 1982, 1987, 1991, 1993, 1994,
  1997, 2002, 2004, 2015, 2023. [`enso_yearly_features.csv`; ONI v6 gives 14]
- Socioeconomic reference: 2011. Landholding reference: 2010-11.

## 6. Final six primary indicators (Set A) [config `pca_primary.features`; `vulnerability_index_weights.csv`]

| # | Feature | Definition | Unit | Dimension | Source |
|---|---|---|---|---|---|
| 1 | `enso_rain_slope_pct_per_degC` | OLS slope of June–September departure (% of 1971–2020 baseline) on the mean of the JJA and JAS RONI values, over 1950–2024 | % per °C | Exposure | IMD, NOAA RONI |
| 2 | `rain_en_deficient_frequency` | Share of the 18 El Niño monsoons with departure ≤ −20% (unrounded) | fraction | Exposure | IMD, NOAA RONI |
| 3 | `soc_agri_worker_share_of_workers_pct` | (Cultivators + agricultural labourers, main + marginal) / total workers × 100 | % | Sensitivity | Census 2011 PCA |
| 4 | `irr_rainfed_share_of_cropped_land_pct` | Unirrigated area / net area sown × 100 | % | Sensitivity | Census 2011 Village Directory |
| 5 | `land_small_holding_share_pct` | Holdings < 2 ha (marginal + small) / all holdings × 100 | % | Sensitivity | Agriculture Census 2010-11, Table 2 (Table 26 for Palghar) |
| 6 | `soc_literacy_rate_7plus_pct` | Literates / (population − population aged 0–6) × 100 | % | Adaptive capacity | Census 2011 PCA |

Largest absolute correlation between any two Set A indicators: 0.45 (agricultural-worker share vs literacy).
[`factorability_checks.csv`]

## 7. Direction of every indicator [config `pca_primary.sign_multipliers`]

| Indicator | Multiplier | Reason |
|---|---|---|
| ENSO rainfall slope | −1 | a more negative slope means a larger El Niño rainfall loss |
| El Niño deficient frequency | +1 | |
| Agricultural-worker share | +1 | |
| Rainfed share | +1 | |
| Small-holding share | +1 | |
| Literacy rate | −1 | higher literacy is treated as greater adaptive capacity |

After alignment, a higher value means greater vulnerability for all six. Directions come from the
exposure–sensitivity–adaptive-capacity framework and are not tested by the project.

## 8. Final preprocessing

- District crosswalk by numeric code (Census 2011 code = Survey of India `DIST_LGD`; Palghar 681); no fuzzy name matching.
  Renamed districts: Aurangabad → Chhatrapati Sambhajinagar, Osmanabad → Dharashiv, Ahmednagar → Ahilyanagar.
- Rainfall: each 0.25° grid cell represented by its box; weight = area of the box inside the district polygon in an
  Albers equal-area projection; daily area-weighted mean; monthly sums; monsoon = June + July + August + September;
  departure % = (monsoon − baseline) / baseline × 100.
- ENSO: NOAA CPC episode rule (index rounded to 0.1 °C, ≥ +0.5 for ≥ 5 consecutive overlapping seasons). Reproduces
  919/919 ONI v6 cells and 915/919 RONI cells of NOAA's published tables (4 mismatches, all in a 1984 La Niña run;
  no El Niño season affected). Project rule: El Niño monsoon year when both JJA and JAS are warm-episode seasons.
- Village Directory: the raw columns "Total Unirrigated Land Area" and "Area Irrigated by Source" are swapped
  (source-wise irrigated areas sum to the "unirrigated" column in 43,661 of 43,665 villages); the code maps them
  explicitly; the raw file is unchanged.
- Agriculture Census: Table 2 used (Table 5 rows for Dhule and Chandrapur contain report errors).
- No imputation; only Mumbai City and Mumbai Suburban lack agricultural data, and they are out of scope.
- No log transformation.
- IMD values kept as published. Ten implausibly high district-years (> 2 × baseline) are flagged, e.g. Pune 2005
  (4.87 ×) and 2009 (2.03 ×); none is an El Niño monsoon year; a Pune-excluded version is a sensitivity check only.
  Whether these values are errors is NOT VERIFIED.

## 9. Final PCA methodology [`src/s13_pca_primary.py`, `src/s16_vulnerability_index.py`]

- Input: 34 × 6 matrix of direction-aligned indicators.
- `StandardScaler` (population SD) → z-scores; PCA (scikit-learn) on the standardised matrix, equivalent to PCA of the
  correlation matrix. Eigenvalues = EVR × 6.
- Loading L(j,k) = eigenvector(j,k) × √eigenvalue(k) (correlation of indicator j with component k).
- Leave-one-district-out stability: PC1 median |cosine| 0.999, minimum 0.948 (Pune omitted); PC2 and PC3 can swap
  (Pune, Ratnagiri) but the PC2–PC3 plane is stable (projection ≥ 0.926). [`pca_leave_one_out.csv`, `pca_stability_report.md`]
- Factorability: KMO = **0.40** (0.398508); Bartlett χ² = 35.47, df = 15, p = 0.002. [`factorability_checks.csv`]
- **The index is not a principal component.** PCA is used only to derive weights.

## 10. Component-retention decision

**3 components retained** (74.5% of variance). Kaiser (eigenvalue > 1), the OECD/JRC standard practice (eigenvalue > 1,
each > 10%, cumulative > 60%) and Jolliffe (eigenvalue > 0.7) all give 3. Horn's parallel analysis (95th percentile of
5,000 random 34 × 6 data sets) retains only 1; bootstrap of districts retains 2. Random-data 95th percentiles:
1.874, 1.465, 1.194 for PC1–PC3. [`retention_rules.csv`, `eigenvalues_retention_checks.csv`]

## 11. Exact PCA variance results [`pca_primary_variance.csv` = `vulnerability_index_components.csv`]

| Component | Eigenvalue | EVR | Cumulative |
|---|---|---|---|
| PC1 | 2.056426 | 0.342738 | 0.342738 |
| PC2 | 1.246465 | 0.207744 | 0.550482 |
| PC3 | 1.165158 | 0.194193 | 0.744675 |
| PC4 | 0.663285 | 0.110548 | 0.855222 |
| PC5 | 0.615596 | 0.102599 | 0.957822 |
| PC6 | 0.253070 | 0.042178 | 1.000000 |

Loadings, PC1 / PC2 / PC3 [`vulnerability_index_weights.csv`]:
slope 0.739 / 0.329 / 0.102; deficient frequency 0.192 / 0.880 / 0.303; agricultural workers 0.712 / −0.119 / −0.529;
rainfed 0.290 / −0.562 / 0.690; small holding −0.661 / 0.080 / −0.425; literacy (aligned) 0.667 / −0.166 / −0.356.

## 12. Exact final PCA-derived weights [`vulnerability_index_weights.csv`]

| Indicator | EVR·\|L\| PC1 | PC2 | PC3 | Raw weight | Weight |
|---|---|---|---|---|---|
| ENSO rainfall slope (aligned) | 0.253 | 0.068 | 0.020 | 0.341 | **0.168** |
| El Niño deficient frequency | 0.066 | 0.183 | 0.059 | 0.307 | **0.151** |
| Agricultural-worker share | 0.244 | 0.025 | 0.103 | 0.372 | **0.183** |
| Rainfed share | 0.099 | 0.117 | 0.134 | 0.350 | **0.173** |
| Small-holding share | 0.227 | 0.017 | 0.083 | 0.326 | **0.161** |
| Literacy (aligned) | 0.229 | 0.035 | 0.069 | 0.332 | **0.164** |
| Total | | | | 2.029 | 1.000 |

Method name used in the project: "PCA absolute-loading weights" (candidate "Method B"). It is **not** the OECD/JRC
method; the OECD/JRC factor-analysis weighting (varimax, squared rotated loadings) is a sensitivity comparison only.

## 13. Exact vulnerability-index formula [config `vulnerability_index`]

- z_ij = (x_ij − μ_j) / σ_j
- L_jk = v_jk √λ_k
- raw_weight_j = Σ_{k=1..3} EVR_k |L_jk|; w_j = raw_weight_j / Σ_j raw_weight_j
- V_i = Σ_j w_j z_ij
- VI_i = 100 (V_i − V_min) / (V_max − V_min)

Recomputing V from the stored z-scores and weights reproduces the stored raw score (max difference 1.4 × 10⁻⁶,
rounding of the CSV).

## 14. Exact index results [`vulnerability_index_scores.csv`]

- Raw score V: min −0.938964 (Nagpur), max 0.838467 (Beed), mean 0 by construction.
- Index: min 0.0 (**Nagpur**), max 100.0 (**Beed**), mean 52.8, median 47.5, SD 23.8 (sample SD; population SD 23.4),
  interquartile range 38.2–68.5.
- Ranking (index): Beed 100.0, Jalna 91.8, Latur 90.9, Dharashiv 89.4, Parbhani 84.0, Nanded 81.8, Nandurbar 75.4,
  Ahilyanagar 75.2, Solapur 69.4, Hingoli 65.9, Washim 62.7, Buldhana 61.2, Satara 58.6, Sangli 53.7, Dhule 53.1,
  Akola 51.9, Chhatrapati Sambhajinagar 49.1, Palghar 45.9, Ratnagiri 45.7, Kolhapur 45.2, Jalgaon 43.4, Amravati 42.6,
  Yavatmal 42.2, Sindhudurg 42.0, Gadchiroli 41.1, Pune 37.3, Nashik 36.8, Raigad 36.5, Chandrapur 35.3, Wardha 32.6,
  Bhandara 25.6, Gondia 18.7, Thane 10.9, Nagpur 0.0.
- Natural-unit profile of the extremes: Beed slope −23.5 % per °C, deficient frequency 0.444 (8 of 18), agricultural
  workers 78.0%, rainfed 82.3%, small holdings 81.5%, literacy 77.0%. Nagpur: −10.7 % per °C, 0.278, 33.7%, 73.9%,
  68.5%, 88.4%.

## 15. Exact K-Means methodology and results [`kmeans_*.csv`, `src/s17_kmeans_classification.py`]

- Input: `vulnerability_index_0_100` only (34 values). No scaling. `KMeans(n_clusters=3, random_state=2026, n_init=20)`.
- Raw labels were Medium = 0, High = 1, Low = 2; reordered by centroid (lowest → Low).

| Group | n | Centroid | Range | Upper boundary |
|---|---|---|---|---|
| Low | 4 | 13.81 | 0.0–25.6 | 29.83 |
| Medium | 20 | 45.86 | 32.6–62.7 | 64.12 |
| High | 10 | 82.38 | 65.9–100.0 | — |

- High: Beed, Jalna, Latur, Dharashiv, Parbhani, Nanded, Nandurbar, Ahilyanagar, Solapur, Hingoli.
- Low: Bhandara, Gondia, Thane, Nagpur.
- Silhouette K = 2 / 3 / 4: 0.594 / **0.587** / 0.571; inertia 5946.5 / 2868.9 / 1456.3.
- Tertile comparison: 25 of 34 districts (73.5%) agree; the 9 that differ are all K-Means Medium.
- Exploratory K-Means on PC1–PC3 scores: silhouette 0.28; not used for classification.

## 16. Exact validation methodology and results [`drought_validation_summary.csv`]

- Measure: declared_taluka_share = talukas declared in the main GR / Census 2011 talukas (355 in total).
  2018 and 2023: severe + moderate in the final GR; 2026: Trigger-1 talukas.
- Primary statistic: Spearman ρ between the fixed 0–100 index and the share (n = 34); group means second.
- Declarations were never used in feature selection, weighting, scaling or clustering (test enforced).

| Year | Role | Spearman ρ | p (two-sided) | Pearson r | Districts with any declaration | Mean share Low / Medium / High |
|---|---|---|---|---|---|---|
| 2018 | historical | 0.585 | 0.0003 | 0.541 | 26 | 0.054 / 0.390 / 0.657 |
| 2023 | historical | 0.450 | 0.0075 | 0.440 | 15 | 0.000 / 0.100 / 0.199 |
| 2018 + 2023 (mean share) | pooled | 0.572 | 0.0004 | 0.566 | 27 | 0.027 / 0.245 / 0.428 |
| 2026 | **holdout** (Trigger-1) | 0.545 | 0.0009 | 0.503 | 32 | 0.388 / 0.696 / 0.988 |
| 2018 severe only | secondary | 0.591 | 0.0002 | 0.570 | 21 | |
| 2023 severe only | secondary | 0.428 | 0.0115 | 0.507 | 10 | |

- Only 2023 is an El Niño monsoon year under the RONI rule (JJA 0.54, JAS 0.79); 2018 is not (0.08, 0.16).
- 2023: the main GR lists only 40 talukas; 1,021 revenue circles were declared separately and cannot be converted to
  shares (no verified per-district total of circles).
- 2026: Trigger-1 stage; 19 of 34 districts at share 1.0 (ceiling effect). Nagpur (index 0.0) had 14 of 14 talukas
  declared; IMD's 26-09-2026 snapshot gives Nagpur −33% for 1 June–26 September 2026.
- Disagreements (percentile-rank gap ≥ 0.5): 2018 Latur, Nanded; 2023 Nanded, Parbhani (higher index, lower
  declaration) and Pune, Nashik (lower index, higher declaration); 2026 Nagpur.

## 17. Exact sensitivity-analysis results [`vulnerability_index_sensitivity.csv`, `kmeans_sensitivity.csv`]

| Comparison | Spearman ρ with primary | Max rank move (district) | Districts moving ≥ 5 places | Districts changing group |
|---|---|---|---|---|
| Equal weights | 0.993 | 5 (Pune) | 1 | 2 |
| OECD/JRC factor weights | 0.934 | 10 (Chhatrapati Sambhajinagar) | 7 | 2 |
| Hazard + social (50/50) | 0.991 | 6 (Pune) | 1 | 1 |
| PCA \|loading\|, all 6 components | 0.995 | 3 (Gadchiroli) | 0 | 1 |
| Pune-excluded rainfall | 0.995 | 3 (Gadchiroli) | 0 | 1 |
| ONI v6 instead of RONI | 0.961 | 6 (Dhule) | 4 | 4 |

No district moves between Low and High in any version. Changing districts are boundary cases (Wardha, Hingoli,
Washim, Buldhana, plus Satara and Solapur under ONI v6). Under ONI v6 Jalna, not Beed, has the highest index.
Pune's index under the Pune-excluded version: 37.3 → 35.3.

## 18. Important limitations

1. 34 districts only; small sample for PCA (parallel analysis retains 1 component; PC2/PC3 swap in leave-one-out).
2. KMO = 0.40: weak common-factor structure, so the weights are exploratory statistical weights and close to equal
   (0.151–0.183 vs 0.167). Not evidence of a latent vulnerability construct.
3. Small-holding share is negatively correlated with the other five aligned indicators; its direction is set by the
   framework, not shown by the data.
4. Socioeconomic data from 2011 and landholdings from 2010-11, combined with 2025-vintage Survey of India boundaries.
5. Adaptive capacity is represented only by literacy (no income, credit or infrastructure variables).
6. Unusual published IMD rainfall values (Pune 2005, 2009 and others) kept as published; NOT VERIFIED as errors.
7. Drought declarations are administrative decisions, not measured crop loss; 2023 is only partly captured at taluka
   level; 2026 is a Trigger-1 holdout with a ceiling effect; only 2023 is an El Niño year.
8. The 0–100 index is relative to the 34 districts; 0 does not mean "not vulnerable".
9. No causal claim and no drought prediction; the ENSO statistics are historical associations.

## 19. Existing figures and tables that can be reused

| File | Content | Use in paper |
|---|---|---|
| `outputs/maps/maharashtra_vulnerability_groups.png` | K-Means groups, SOI boundaries | Fig. (group map) |
| `outputs/maps/maharashtra_vulnerability_index.png` | 0–100 index | Fig. (index map) |
| `outputs/maps/maharashtra_drought_2018.png`, `_2023.png`, `_2026_holdout.png`, `maharashtra_index_vs_2026.png` | declaration shares | not needed in the paper (page limit); the validation scatter is generated instead |

New figures needed (generated only from final CSVs, no re-modelling): methodology flowchart, PCA explained-variance
chart, loading heatmap, index-vs-declared-share scatter.

## 20. Inconsistencies found

None changes any number used in the paper. None was corrected in the repository, because each is a stage-record or
labelling issue rather than an error in the final implementation.

| # | Where | Issue | Authoritative source | Action |
|---|---|---|---|---|
| 1 | `reports/feature_selection_report.md` (header, Appendix A), `reports/data_quality_report.md` §0, `reports/pca_weighting_methods_report.md` (§0 header, §11), `reports/final_vulnerability_index_report.md` §15, `reports/kmeans_classification_report.md` §10, config `pca_primary.kmeans` | Stage-time statements now outdated ("No PCA has been performed", "K-Means not run yet", "not yet validated", "nothing here is final") | Later-stage reports and config sections `vulnerability_index`, `kmeans_classification`, `validation` (all FIXED) | Flagged only. The paper describes the final pipeline. |
| 2 | `reports/data_quality_report.md` §10 rainfall QA table | District 681 is labelled "Thane" (should be Palghar) and old names appear (Bid, Raigarh, Gondiya, Buldana, Aurangabad, Ahmadnagar, Osmanabad) | `data/manual/district_reference.csv`; all joins use codes, so values are correct | Flagged only; display label issue. |
| 3 | `data/interim/data_dictionary.csv` `group` column | Literacy is grouped under "D. Socioeconomic sensitivity" and rainfed share under "F. Irrigation / rainfed exposure", while the final framework treats them as Adaptive capacity and Sensitivity | `pca_input_metadata.csv` / `vulnerability_index_weights.csv` `conceptual_dimension` | Paper uses the conceptual dimensions. |
| 4 | Index SD | Reports give 23.8 (sample SD, ddof = 1); population SD is 23.4 | Recomputed from `vulnerability_index_scores.csv` | Paper reports 23.8 and labels it the sample standard deviation. |
| 5 | Sensitivity table | "All 6 components" and "Pune-excluded rainfall" have identical ρ (0.994805) and the same largest move (3, Gadchiroli) | Verified: different score series with the same Σd² = 34; K-Means sensitivity shows different changed districts (Wardha vs Hingoli) | Not an error. |
| 6 | `config/project_decisions.yaml` `enso_episode_rule` | States that the rule reproduces "all El Niño cells" of the RONI table; overall match is 915/919 | `enso_cpc_table_check.csv` (mismatches only in 1984 La Niña seasons) | Consistent; paper states 919/919 ONI and 915/919 RONI. |
| 7 | Feature sources | Earlier proposal mentioned the Economic Survey of Maharashtra, population density and poverty; none is used in the final index | `feature_selection_report.md` Appendix A | Paper lists only the final sources. |

## 21. Conceptual rules carried into the paper

- PCA derives weights; the index is a weighted sum of z-scores, not PC1.
- K-Means is applied to the final 0–100 index only; it does not construct the index.
- Drought declarations are validation data only; 2026 is a holdout, examined after the index and groups were fixed.
- No claims of prediction, probability or causality. The index is relative to the 34 districts.
- The primary weighting method is the PCA absolute-loading method; OECD/JRC is a sensitivity comparison.

## 22. Descriptive values computed for the paper (from the fixed outputs, no re-modelling)

Computed directly from `vulnerability_index_scores.csv`, `kmeans_vulnerability_classification.csv`,
`vulnerability_index_weights.csv` and `data/interim/maharashtra_district_feature_table.csv`:

| Value | Result |
|---|---|
| Group mean ENSO slope, High / Medium / Low | −19.87 / −10.77 / −7.95 % per °C |
| Group mean literacy, High / Medium / Low | 75.16 / 81.93 / 86.08 % |
| Group mean agricultural-worker share, High / Medium / Low | 74.93 / 63.68 / 46.31 % |
| Largest mean weighted contributions (w × z), High group | ENSO slope 0.197, literacy 0.162, agricultural workers 0.110 |
| Marathwada districts in the High group | 7 of 8 (Chhatrapati Sambhajinagar is Medium, 49.1) |
| Lowest literacy among the 34 districts | Nandurbar, 64.4% |
| Census 2011 rural population share, Nagpur / Thane | 31.7% / 13.8% |
| Rainfed share, Bhandara / Gondia (two lowest) | 45.3% / 46.4% |
| Correlation of aligned slope and deficient frequency | 0.33 |

## 23. Paper-specific decisions (for the team to review)

- **Table and figure numbering follows IEEE first-citation order.** The requested structure puts sensitivity (V-D)
  before validation (V-E) and the index (V-B) before the groups (V-C). The paper therefore numbers the sensitivity table
  as Table V and the validation table as Table VI, and the index map as Fig. 4 and the group map as Fig. 5.
- **Maps were redrawn for the paper** (`paper/make_figures.py`) with the project's own `map_table()`, `draw_groups()`
  and `draw_continuous()` functions, without in-figure titles or footnotes (IEEE captions go below the figure). Data
  and colours are identical to `outputs/maps/`.
- **One literature source was removed** (Hinkel 2011) because its specific argument could not be verified.
- **No analytical file was changed.** MD5 checksums of `data/processed/*.csv` were identical before and after the
  figure and paper builds, and the test suite still passes.
