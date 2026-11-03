# Feature Selection Report (before PCA)

Project: *Artificial Intelligence-Driven Vulnerability Index Mapping for Districts in Maharashtra to El Niño Droughts Using Socioeconomic and Climatic Principal Component Analysis* — Maharashtra, district level.

Data used: primary configuration in `config/project_decisions.yaml` (geography B = 36 current districts, ENSO index = RONI, study period 1950–2024, deficient monsoon = unrounded departure ≤ −20%). Numbers come from `src/s11_feature_selection.py`; tables are in `data/interim/feature_selection_audit.csv`, `feature_correlations.csv`, `recommended_pca_features.csv` and `feature_set_summary.csv`.

**No PCA, scaling, clustering, scoring or ranking has been done.** This report only examines which variables are sensible inputs. **Update after the project decisions (27 Sep 2026): Set A is the primary PCA feature set; Set B and the alternatives are kept for sensitivity analysis only.**

**How to read the vulnerability directions.** Each variable is something the dataset measures directly (for example, the share of holdings below 2 ha). Saying that a higher value means "more vulnerable" is an interpretation taken from the exposure–sensitivity–adaptive-capacity framework. This project does not test those mechanisms. The only relationships the project itself measures are the historical rainfall and ENSO statistics for 1950–2024, and those are associations, not proof of cause. The audit table has a column `evidence_in_this_project` that states this for every variable.

---

## 1. Purpose of feature selection

The data-engineering stage deliberately kept every reasonable variable (30 PCA candidates). The aim now is a smaller set where each variable:

- has a clear meaning and a stated direction under the framework;
- comes from a verified source;
- adds information the others do not.

## 2. Current sample size

| Item | Variables | Districts in scope | Districts per variable |
|---|---|---|---|
| All candidates | 30 | 34 | 1.1 |
| Set A (primary) | 6 | 34 | 5.7 |
| Set B (sensitivity) | 10 | 34 | 3.4 |

The 34 districts are the 36 current districts minus Mumbai City and Mumbai Suburban, which have no village or landholding data.

**Why this matters.** PCA is built from the correlation matrix, and with 34 districts each correlation is itself uncertain. A true correlation of 0 can easily show up anywhere between about −0.34 and +0.34. An observed correlation of 0.5 is compatible with values from about 0.20 to 0.72 (95% range). With 30 variables there are 435 such correlations; with Set A there are 15, and with Set B 45.

Set A is substantially more manageable than the 30-variable candidate set. Even so, PCA with only 34 districts remains sensitive to influential districts (for example Pune, with suspect rainfall values, and Nandurbar, with 69% ST population). It should be treated as exploratory rather than definitive. Set B is less compact again. No universal minimum sample size is assumed here. The number of districts is fixed by geography, so the only practical lever is the number and distinctness of the variables.

## 3. Why not use all 30 variables?

The reduction is **not** because PCA cannot run with 30 variables. Mathematically it can: it would still produce components and loadings.

The reasons are:

1. **Overlapping information.** Many candidates describe the same thing. Three variables summarise the same ENSO–rainfall relationship; four describe landholding size.
2. **Exact complements and derived measures.** Rainfed share is 100 − irrigated share. The El Niño-minus-non-El-Niño variables are calculated from other candidates. Including both adds no new information.
3. **Alternative measurements of one concept.** The agricultural and marginal worker shares each exist with two denominators, and marginal holdings are nested inside small holdings.
4. **A small cross-sectional sample.** With 34 districts, estimates of 435 correlations are noisy, and later components can change a lot if a single district changes.
5. **Interpretation and weighting.** A concept entered three times gets extra weight in the leading components only because of how the table was built. A compact set is easier to interpret and to explain, and redundant information has less influence on the result.

## 4. Current candidate variables

All 30 are listed with source, year, formula, what is measured, dimension, direction, evidence and decision in `feature_selection_audit.csv`.

| Decision | Count |
|---|---|
| Set A core | 6 |
| Set B addition | 4 |
| Alternative (documented swap-in) | 5 |
| Exclude | 15 |

Some candidates were not forced into a dimension:

- work participation rate, non-worker share and well share of irrigation have no clear vulnerability direction;
- SC and ST shares are marked as *indirect* sensitivity indicators.

## 5. Exact structural redundancy vs alternative measures

### A. Exact structural redundancy / identities

In each pair, one variable is fully determined by the other(s), so keeping both adds no information. All the identities were checked in the data (tests).

| Relationship | Type |
|---|---|
| rainfed share = 100 − irrigated share | identity |
| non-worker share = 100 − work participation rate | identity |
| agricultural worker share of workers = cultivator share + agricultural labourer share (all ÷ workers) | identity |
| El Niño-minus-non-El-Niño deficit = El Niño mean deficit − non-El-Niño mean deficit | identity |
| El Niño-minus-non-El-Niño deficient frequency = El Niño frequency − non-El-Niño frequency | identity |
| ENSO–rainfall Pearson r, Spearman ρ and slope | statistics of the same two underlying series (not an algebraic identity) |

These involve **14 of the 30 variables**. No shortlist contains two members of any of them.

### B. Alternative denominators and nested measures (not exact duplicates)

| Pair | Relation | Observed r |
|---|---|---|
| agricultural worker share of workers / of population | alternative denominators for the same count | 0.98 |
| marginal worker share of workers / marginal workers per population | alternative denominators for the same count (the prototype used population) | 0.98 |
| small holding share (< 2 ha) / marginal holding share (< 1 ha) | nested measure (marginal ⊂ small) | 0.96 |

These are different quantities, not algebraic duplicates. Each pair measures one underlying concept in two ways, so only one of each is kept in either shortlist. The denominator choice is a config decision.

## 6. Empirical correlation findings

These are computed on the 34 in-scope districts (`feature_correlations.csv`, 435 pairs), and **20 pairs have |r| ≥ 0.8**. The notable pairs that are not identities:

| Pair | r | Comment |
|---|---|---|
| small holding share – average holding size | −0.99 | same Agriculture Census table; near-mirror |
| El Niño mean deficit – El Niño mean SPI | −0.90 | two scales for the same thing |
| ENSO slope – El Niño-minus-non-El-Niño deficit | −0.87 | both describe how much drier El Niño years are |
| rural population share – agricultural worker share | 0.87 | rural districts are agricultural districts |
| ENSO slope – cropped-land share | −0.78 | cropland is concentrated in the dry interior, where the ENSO association is strongest |
| marginal worker share – cropped-land share | −0.74 | forested/tribal districts: little cropland, much seasonal work |

A high correlation was **not** used on its own to drop a variable. For example, the ENSO slope and cropped-land share (r = −0.78) are both in Set B because one is a climate statistic and the other a land-use measure.

## 7. Exposure variables

Exposure here means how strongly the district's monsoon rainfall has historically been associated with El Niño, and how much land a deficit could affect.

| Variable | What is measured | Direction used | Decision |
|---|---|---|---|
| `enso_rain_slope_pct_per_degC` | average % change in monsoon departure per 1 °C of ENSO index, 1950–2024 | more negative = greater exposure | Set A |
| `rain_en_deficient_frequency` | share of El Niño years with a deficient monsoon (IMD ≤ −20%) | higher = greater exposure | Set A |
| `rain_en_max_deficit_pct` | largest El Niño-year deficit | higher = greater exposure | Set B |
| `agri_cropped_land_share_pct` | net area sown ÷ village area | higher = greater exposure (more land a deficit can affect) | Set B |
| `rain_en_mean_deficit_pct` | mean El Niño-year deficit | higher = greater exposure | Alternative |

## 8. Sensitivity variables

Sensitivity here means characteristics that, under the framework, are assumed to make the same rainfall deficit more harmful. The dataset measures the shares; the harm mechanisms are hypotheses and are not tested here.

| Variable | What is measured | How it is used in the framework | Decision |
|---|---|---|---|
| `soc_agri_worker_share_of_workers_pct` | share of workers who are cultivators or agricultural labourers | higher is treated as greater sensitivity, because agricultural employment is assumed to be rainfall-dependent | Set A |
| `irr_rainfed_share_of_cropped_land_pct` | share of net sown area that is unirrigated | higher is treated as greater sensitivity, because rainfed crops are assumed to depend on the monsoon | Set A |
| `land_small_holding_share_pct` | share of holdings below 2 ha | higher is treated as greater sensitivity, because smaller operational holdings are hypothesised to give less capacity to absorb a failed season | Set A |
| `soc_marginal_worker_share_of_workers_pct` | share of workers who worked < 6 months | higher is treated as greater sensitivity (seasonal work assumed less secure) | Set B |
| `soc_st_share_pct` | Scheduled Tribe share of population | if retained, an **indirect** social-vulnerability indicator | Set B |
| agricultural labourer share, rural share, SC share | as named | as above | Alternatives |

**SC and ST shares.** They are not removed for being sensitive topics or for correlation. If retained, they are **indirect social-vulnerability indicators**. The present dataset does not measure household poverty or income; no verified district poverty variable exists in the sources, although the proposal mentions poverty. ST share is in Set B with a warning that it is very skewed (Nandurbar 69%). SC share is an alternative: it has a small spread (3–20%) and no drought-related mechanism is measured here.

## 9. Adaptive-capacity variables

Adaptive capacity here means characteristics used as indicators of the ability to cope with a drought year.

| Variable | What is measured | How it is used | Decision |
|---|---|---|---|
| `soc_literacy_rate_7plus_pct` | literacy rate, age 7+ | used as an adaptive-capacity indicator (higher treated as lower vulnerability) | Set A |
| `irr_irrigated_share_of_cropped_land_pct` | irrigated share of net sown area | higher treated as lower vulnerability (irrigation assumed to buffer deficits) | Alternative (= 100 − rainfed share) |

Literacy is used here as an adaptive-capacity **indicator**. The framework assumes that literacy helps people get information, credit, relief and non-farm work, but this dataset does not show that literacy causes any of those. **This dimension is thin:** the current data have no income, credit, banking or infrastructure variable. This is recorded as a limitation, not filled in.

## 10. Climate variable assessment

| Variable | What it measures | About El Niño drought? | Overlaps with | Stable? (r, RONI vs ONI) | Easy in a viva? | Direction clear? | Decision |
|---|---|---|---|---|---|---|---|
| `enso_rain_pearson_r` | strength of association between ENSO index and monsoon departure | yes (association) | slope, Spearman (same series) | 0.96 | medium | yes | Exclude |
| `enso_rain_spearman_rho` | rank version of the above | yes | Pearson, slope (same series) | 0.93 | low | yes | Exclude |
| `enso_rain_slope_pct_per_degC` | average % change in monsoon rainfall per 1 °C of ENSO index | yes | Pearson, Spearman (same series) | **0.98** | **high** | yes | **Set A** |
| `rain_monsoon_cv_pct` | general year-to-year variability | no (not El Niño specific) | — | does not use ENSO | high | yes | Exclude (skew 3.0 from suspect Pune/Jalna values) |
| `rain_en_mean_deficit_pct` | average deficit in El Niño years | yes | SPI; minus-version (identity) | **0.59** | high | yes | Alternative (unstable; Pune outlier) |
| `rain_en_max_deficit_pct` | worst El Niño-year deficit | yes | — | 0.98 | high | yes | Set B (one year per district) |
| `rain_en_deficient_frequency` | share of El Niño years with a deficient monsoon | yes | minus-version (identity) | 0.87 | **high** | yes | **Set A** (Pune concern) |
| `rain_en_mean_spi` | mean SPI in El Niño years | yes | mean deficit (r = −0.90) | 0.42 | low | yes | Exclude |
| `rain_en_minus_nonen_deficit_pct` | El Niño mean deficit minus non-El-Niño mean deficit | yes | exactly derived from mean deficit | 0.48 | medium | yes | Exclude |
| `rain_en_minus_nonen_deficient_frequency` | El Niño frequency minus non-El-Niño frequency | yes | exactly derived from frequency | 0.71 | medium | yes | Exclude |

**About the correlation/slope variables.** A negative slope means that, over 1950–2024, years with a higher ENSO index tended to have lower monsoon rainfall in that district. That is an association in the data. It does not prove that El Niño caused the deficit in any particular year, and the report should not claim so. The slope was preferred over Pearson r because it keeps the size of the effect (in % of rainfall) and changes least when the ENSO index changes.

**Why two climate variables in Set A.** The slope uses all 75 years (1950–2024) and describes the typical ENSO–rainfall association. The deficient frequency uses only the El Niño years (18 under RONI) and records how often those years actually had deficient monsoons. They are only weakly correlated (r = −0.33), so they carry different information.

**Pune.** Pune's deficient frequency (0.72) is 3.6 standard deviations above the mean. Part of this comes from implausibly high IMD values (2005, 2009) that inflate Pune's baseline: excluding those years lowers it to 0.61, still the highest in the state. Pune is also deficient unusually often in non-El-Niño years (0.37, against a state median of 0.16). Decision taken: the primary analysis keeps all published IMD values (config `rainfall_extreme_values` = keep), so Pune remains a known influential district to watch in the PCA.

## 11. Agricultural variable assessment

| Aspect | Variables | Relation | Choice |
|---|---|---|---|
| Agricultural exposure | cropped-land share | — | Set B |
| Irrigation dependence | irrigated share, rainfed share, well share | irrigated + rainfed = 100 (identity) | Rainfed share (Set A); irrigated share = same information (alternative). Well share excluded: its direction is unclear, since wells may buffer one bad season but may fail in multi-year droughts. |
| Landholding fragmentation | small holding share, marginal holding share, small-holding area share, average holding size | marginal ⊂ small (nested); average size ≈ mirror of small share (r = −0.99, empirical) | Small holding share (Set A); the rest excluded |

Irrigated and rainfed share are never both kept, and neither are small and marginal holding share.

## 12. Set A — compact set (PRIMARY PCA feature set)

| # | Variable | Dimension | Direction used | Why |
|---|---|---|---|---|
| 1 | `enso_rain_slope_pct_per_degC` | Exposure | more negative = more vulnerable | most stable ENSO–rainfall statistic; easy unit |
| 2 | `rain_en_deficient_frequency` | Exposure | + | how often El Niño years were deficient (IMD definition) |
| 3 | `soc_agri_worker_share_of_workers_pct` | Sensitivity | + | agricultural employment ("agricultural dependency" in the proposal) |
| 4 | `irr_rainfed_share_of_cropped_land_pct` | Sensitivity | + | irrigation dependence (named in the proposal) |
| 5 | `land_small_holding_share_pct` | Sensitivity | + | share of small operational holdings |
| 6 | `soc_literacy_rate_7plus_pct` | Adaptive capacity | − | adaptive-capacity indicator |

Checks (recomputed by the tests):

- 6 variables for 34 districts;
- no exact identity and no alternative-measure pair inside the set;
- no missing values;
- largest within-set correlation |r| = 0.45 (agricultural worker share vs literacy).

## 13. Set B — broader set (sensitivity only), and documented alternatives

Set B is Set A plus:

| Variable | Dimension | Why | Concern |
|---|---|---|---|
| `rain_en_max_deficit_pct` | Exposure | worst-case El Niño deficit; stable across indices | depends on one year per district |
| `agri_cropped_land_share_pct` | Exposure | land a deficit can affect | r = −0.78 with the ENSO slope |
| `soc_marginal_worker_share_of_workers_pct` | Sensitivity | seasonal, less secure work | skewed (1.6) |
| `soc_st_share_pct` | Sensitivity (indirect) | indirect social-vulnerability indicator | very skewed (2.4; Nandurbar 69%); no income/poverty data |

Checks:

- 10 variables for 34 districts;
- no exact identity and no alternative-measure pair inside the set;
- no missing values;
- largest within-set |r| = 0.77.

**Documented alternatives** (listed in `recommended_pca_features.csv`):

| Alternative | Could replace | Reason to consider |
|---|---|---|
| `rain_en_mean_deficit_pct` | deficient frequency | more familiar "average deficit", but unstable across indices |
| `irr_irrigated_share_of_cropped_land_pct` | rainfed share | same information, framed as adaptive capacity |
| `soc_agri_labourer_share_of_workers_pct` | agricultural worker share | focuses on landless labour |
| `soc_rural_population_share_pct` | agricultural worker share | simpler, but less specific |
| `soc_sc_share_pct` | ST share | social-vulnerability framing |

Decision: Set A is the primary PCA feature set. Set B and the alternatives remain available for sensitivity analysis.

## 14. Methodological decisions (now FIXED)

These were open when this audit was first written. They were decided by the project team on 27 Sep 2026 and are recorded as FIXED in `config/project_decisions.yaml`:

1. **Feature set:** Set A (primary); Set B only for sensitivity.
2. **Pune rainfall values:** keep all published IMD values; the baseline excluding flagged years is sensitivity only.
3. **ENSO index:** RONI (primary); ONI v6 only as a cross-check, never mixed.
4. **Geography:** B, 36 current districts (Palghar rebuilt from official 2011 sub-district data); 34 in the PCA scope.
5. **Irrigation framing:** rainfed share.
6. **Denominators:** agricultural and marginal worker shares both divided by total workers.
7. **Skewed variables:** no log transformation. It was considered but not used, because the six variables are interpretable percentages or statistical measures and transforming them would reduce direct interpretability.
8. **Direction alignment before PCA:** the ENSO slope and literacy are multiplied by −1, so that higher = more vulnerable for all six (`data/interim/pca_input_primary.csv`).
9. **Study period:** 1950–2024; 2025 is sensitivity only and 2026 is validation holdout only.
10. **Deficient monsoon:** unrounded departure ≤ −20%. Compared with rounding, this changes 13 district-years whose departure lies between −20% and −19.5% (they are no longer counted as deficient).

## 15. Risks and limitations before PCA

- **Small sample:** 34 districts. Any PCA should be treated as exploratory, and its stability should be checked, for example by leaving one district out at a time or by bootstrap.
- **Influential districts:** Pune (suspect IMD rainfall) and Nandurbar (ST share 69%).
- **Thin adaptive capacity:** only literacy; there are no income, credit or infrastructure variables.
- **Mixed reference years:** climate 1950–2024, socioeconomic data 2011, landholding data 2010-11.
- **Assumed mechanisms:** the vulnerability directions of the socioeconomic and agricultural variables come from the framework and are not demonstrated by this project.
- **Association, not causation:** the ENSO variables describe historical association only.
- **Judgement in selection:** PCA gives data-driven weights *within* the chosen variables, but choosing the variables is a judgement. This report records that judgement.
- **The implementation has moved on from the proposal** in several places (Appendix A).

## 16. Next step

The decisions above are recorded, and the primary PCA and its leave-one-district-out stability check are reported in `reports/pca_primary_report.md` and `reports/pca_stability_report.md`. No index, ranking or K-Means has been produced yet.

---

## Appendix A. Comparison with the original proposal (`ppt 1.pptx`)

| Proposal item | Status now | What changed and why |
|---|---|---|
| Combine district climatic and socioeconomic records for Maharashtra | Done (36 districts; 34 in the PCA scope) | Scope is Maharashtra, as agreed with the guide; the title is unchanged. |
| Climatic data: IMD rainfall, NOAA ONI | IMD **gridded** rainfall 1950–2024; NOAA **RONI** (official since Feb 2026) or ONI v6 | The prototype's 5-district rainfall file could not be traced to a source, whereas the gridded IMD data are official and reproducible. The prototype's El Niño rule was replaced by NOAA's documented episode rule. |
| Socioeconomic data: Census, Economic Survey of Maharashtra; population density, literacy, agricultural dependency | Census 2011 population tables and Village Directory, Agriculture Census 2010-11; literacy and agricultural dependency kept | The Economic Survey of Maharashtra was not used. **Population density was not constructed**; it could be added (Census population ÷ district area) if the guide wants it. **Poverty** has no verified district source; ST/SC shares are only indirect indicators. |
| Irrigation (slide 4: "zero irrigation") | Rainfed/irrigated share from the Village Directory | Included, in line with the proposal. |
| Preprocessing: merging, handling nulls, log transformations | Merging done; nulls not imputed (only Mumbai lacks agricultural data, and it is out of scope) | Log transforms not yet decided (section 14). |
| PCA for objective weighting | Not run yet | Plan unchanged; this report narrows its inputs. |
| K-Means into Low/Medium/High zones | Not run yet | Plan unchanged. The prototype used hierarchical clustering, whereas the proposal says K-Means. |
| Interactive map / Streamlit dashboard | Not started | Plan unchanged; the Survey of India boundaries are ready. |
| Validation | Added: drought declarations 2018/2023/2026 (2026 holdout) | Not in the proposal; added so that the index can be checked against observed droughts. |

Nothing in the proposal has been rewritten; the changes above are implementation decisions recorded in the config and reports.
