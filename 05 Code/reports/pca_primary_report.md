# Primary PCA Report

Project: *Artificial Intelligence-Driven Vulnerability Index Mapping for Districts in Maharashtra to El Niño Droughts Using Socioeconomic and Climatic Principal Component Analysis* — Maharashtra.

Script: `src/s13_pca_primary.py`. Input: `data/interim/pca_input_primary.csv` and `pca_input_metadata.csv`. Outputs: `data/processed/pca_primary_variance.csv`, `pca_primary_loadings.csv`, `pca_primary_scores.csv`.

**No vulnerability index, ranking, Low/Medium/High labels or K-Means have been produced.** The 2026 drought declarations were not used.

## 1. Data and setup

| Item | Value |
|---|---|
| Geography | B: 36 current districts (Palghar rebuilt from official 2011 sub-district data) |
| Districts in the PCA | 34 (Mumbai City and Mumbai Suburban excluded: no village or landholding data) |
| ENSO index | NOAA RONI (ERSST.v6); El Niño monsoon year = JJA and JAS both inside a NOAA warm episode (project rule) |
| Study period | 1950–2024 (18 El Niño monsoon years); rainfall baseline 1971–2020 |
| Variables | Set A, 6 variables |
| Transformation | none (no log) |

Direction alignment before scaling, so that for every input *higher = more vulnerable* under the project's framework:

| PCA input | Original variable | Multiplier |
|---|---|---|
| `pca_enso_rain_slope_vulnerability` | `enso_rain_slope_pct_per_degC` (% change in monsoon rainfall per 1 °C of RONI) | −1 |
| `pca_en_deficient_frequency` | `rain_en_deficient_frequency` (share of El Niño years with departure ≤ −20%) | +1 |
| `pca_agri_worker_share` | `soc_agri_worker_share_of_workers_pct` | +1 |
| `pca_rainfed_share` | `irr_rainfed_share_of_cropped_land_pct` | +1 |
| `pca_small_holding_share` | `land_small_holding_share_pct` | +1 |
| `pca_literacy_vulnerability` | `soc_literacy_rate_7plus_pct` | −1 |

The direction is an assumption of the vulnerability framework, not something this project has demonstrated (see `reports/feature_selection_report.md`). Flipping a sign does not change the size of any correlation; it only changes its sign, so that the loadings are easier to read.

## 2. Standardisation

Each input is converted to a z-score:

  z = (x − mean of x across the 34 districts) / (standard deviation of x)

using scikit-learn's `StandardScaler` (population standard deviation). After this, every variable has mean 0 and standard deviation 1.

**Why it is needed.** The six inputs are in different units and ranges: the ENSO slope is in % per °C (about −26 to −7 before the sign flip), the deficient frequency is a fraction (0.11 to 0.72), and the shares are percentages. PCA looks for directions of largest variance. Without standardisation, a variable would dominate simply because its numbers are bigger. After standardisation, PCA works on the correlation matrix, so each variable starts with equal importance.

## 3. The PCA equations

Let **Z** be the 34 × 6 matrix of standardised values and **R** = ZᵀZ / 34 the 6 × 6 correlation matrix. PCA solves

  **R v**ₖ = λₖ **v**ₖ,  k = 1 … 6

where each **v**ₖ is a unit-length eigenvector (the component *weights*) and λₖ its eigenvalue. The components are uncorrelated and are ordered so that λ₁ ≥ λ₂ ≥ … ≥ λ₆.

The score of district *i* on component *k* is a weighted sum of its standardised values:

  PCₖ(i) = v₁ₖ z₁(i) + v₂ₖ z₂(i) + … + v₆ₖ z₆(i)

## 4. Eigenvalues and explained variance

| Component | Eigenvalue | Explained variance | Cumulative |
|---|---|---|---|
| PC1 | 2.056 | 34.3% | 34.3% |
| PC2 | 1.246 | 20.8% | 55.0% |
| PC3 | 1.165 | 19.4% | 74.5% |
| PC4 | 0.663 | 11.1% | 85.5% |
| PC5 | 0.616 | 10.3% | 95.8% |
| PC6 | 0.253 | 4.2% | 100.0% |

- **What an eigenvalue represents.** Because the data are standardised, each variable contributes a variance of 1, so the six eigenvalues add up to 6. A component's eigenvalue is how much of that total it captures: PC1 captures as much as about two original variables.
- **Explained variance ratio** = eigenvalue ÷ 6. (scikit-learn's own `explained_variance_` divides by n − 1 and is larger by the factor 34/33; the ratios are the same.)
- **Three components have eigenvalues above 1**, i.e. each captures more than a single original variable. Together they explain 74.5% of the variation.
- **PC2 and PC3 have similar eigenvalues** (1.25 and 1.17). When eigenvalues are this close, small changes in the data can swap the two components. This is examined in `reports/pca_stability_report.md`.

## 5. Weights and loadings

The **weights** are the eigenvector entries used to calculate the scores. The **loadings** are the correlations between each input variable and each component (weight × √eigenvalue). Loadings are easier to interpret: values near ±1 mean the component closely follows that variable.

Weights (eigenvectors):

| variable | PC1 | PC2 | PC3 | PC4 | PC5 | PC6 |
|---|---|---|---|---|---|---|
| pca_enso_rain_slope_vulnerability | 0.515 | 0.295 | 0.094 | 0.481 | −0.466 | −0.436 |
| pca_en_deficient_frequency | 0.134 | 0.788 | 0.280 | −0.004 | 0.271 | 0.458 |
| pca_agri_worker_share | 0.497 | −0.107 | −0.490 | −0.227 | −0.373 | 0.558 |
| pca_rainfed_share | 0.202 | −0.504 | 0.639 | 0.345 | −0.005 | 0.422 |
| pca_small_holding_share | −0.461 | 0.072 | −0.394 | 0.722 | −0.090 | 0.312 |
| pca_literacy_vulnerability | 0.465 | −0.149 | −0.330 | 0.277 | 0.750 | −0.118 |

Loadings (correlation of variable with component):

| variable | PC1 | PC2 | PC3 | PC4 | PC5 | PC6 |
|---|---|---|---|---|---|---|
| pca_enso_rain_slope_vulnerability | **0.74** | 0.33 | 0.10 | 0.39 | −0.37 | −0.22 |
| pca_en_deficient_frequency | 0.19 | **0.88** | 0.30 | −0.00 | 0.21 | 0.23 |
| pca_agri_worker_share | **0.71** | −0.12 | **−0.53** | −0.18 | −0.29 | 0.28 |
| pca_rainfed_share | 0.29 | **−0.56** | **0.69** | 0.28 | −0.00 | 0.21 |
| pca_small_holding_share | **−0.66** | 0.08 | −0.43 | 0.59 | −0.07 | 0.16 |
| pca_literacy_vulnerability | **0.67** | −0.17 | −0.36 | 0.23 | 0.59 | −0.06 |

## 6. Why component signs are arbitrary

If **v** is an eigenvector, so is −**v**, with the same eigenvalue and the same explained variance. Different software, or the same software on slightly different data, can return either sign. A component's sign therefore carries no meaning by itself; only the *pattern* of signs within a component does (which variables move together and which move in opposite directions).

To keep the results reproducible, the script uses a fixed rule: each component is flipped so that its largest-magnitude weight is positive. This rule is only a convention. It does **not** make "high PC1" mean "more vulnerable".

## 7. Scores for all 34 districts

Standardised component scores (mean 0 across the 34 districts). Rows are alphabetical; this is **not** a ranking.

| district_id | district | PC1 | PC2 | PC3 | PC4 | PC5 | PC6 |
|---|---|---|---|---|---|---|---|
| 522 | Ahilyanagar | 0.81 | 1.69 | -0.87 | 0.78 | -0.59 | -0.56 |
| 501 | Akola | -0.14 | 0.51 | 1.16 | -0.41 | -0.95 | 0.71 |
| 503 | Amravati | -0.34 | -0.14 | 0.49 | -0.53 | -1.10 | 0.31 |
| 523 | Beed | 1.57 | 1.34 | -0.23 | 1.26 | -0.36 | 0.34 |
| 506 | Bhandara | -1.91 | 0.73 | -2.64 | -0.52 | -0.50 | -0.18 |
| 500 | Buldhana | 0.51 | -0.50 | 0.22 | -0.30 | -0.84 | 0.70 |
| 509 | Chandrapur | 0.03 | 0.31 | -0.11 | -1.21 | 0.53 | -0.13 |
| 515 | Chhatrapati Sambhajinagar | -0.39 | -1.21 | -0.56 | 0.82 | -0.31 | -0.74 |
| 525 | Dharashiv | 2.42 | 1.21 | 0.78 | 0.34 | -0.58 | -0.18 |
| 498 | Dhule | 0.85 | -1.50 | -0.52 | -0.30 | 0.91 | -0.32 |
| 508 | Gadchiroli | 0.29 | 0.10 | -1.91 | -1.32 | 1.00 | -0.06 |
| 507 | Gondia | -2.27 | 0.33 | -2.64 | -0.48 | -0.69 | -0.32 |
| 512 | Hingoli | 1.16 | -0.91 | -0.22 | -0.14 | -0.35 | 0.16 |
| 499 | Jalgaon | 0.34 | -1.22 | -0.31 | -0.52 | 0.11 | -0.32 |
| 514 | Jalna | 1.65 | -0.04 | -0.53 | 0.94 | 0.65 | 0.21 |
| 530 | Kolhapur | -1.93 | 0.03 | -0.81 | 0.76 | 0.36 | 0.43 |
| 524 | Latur | 1.80 | 0.61 | 0.61 | 0.99 | -0.31 | -0.05 |
| 505 | Nagpur | -1.51 | 0.37 | 1.37 | -1.10 | -0.18 | -1.30 |
| 511 | Nanded | 1.09 | -0.45 | -0.09 | 0.98 | 0.09 | 0.11 |
| 497 | Nandurbar | 2.14 | -0.88 | -0.74 | -0.74 | 2.54 | 0.50 |
| 516 | Nashik | -0.66 | 0.50 | -0.19 | -0.63 | 0.18 | 0.00 |
| 681 | Palghar | -0.84 | -0.83 | 1.04 | 0.69 | 1.38 | -0.14 |
| 513 | Parbhani | 1.81 | -0.40 | -0.08 | 0.78 | 0.21 | -0.28 |
| 521 | Pune | -1.89 | 3.57 | 1.34 | -0.41 | 1.30 | 0.72 |
| 520 | Raigad | -2.02 | -0.48 | 0.85 | 0.78 | 0.59 | 0.19 |
| 528 | Ratnagiri | -0.92 | -2.01 | 0.16 | 0.48 | -0.32 | 0.35 |
| 531 | Sangli | -0.28 | -0.11 | -0.45 | 0.65 | -0.62 | -0.48 |
| 527 | Satara | -1.38 | 1.16 | -1.02 | 0.66 | -0.09 | 0.79 |
| 529 | Sindhudurg | -1.57 | -1.83 | 0.23 | 0.72 | -0.77 | 0.45 |
| 526 | Solapur | 1.80 | 1.80 | 0.34 | 0.07 | 0.04 | -1.11 |
| 517 | Thane | -2.90 | -0.48 | 2.48 | 0.70 | 0.73 | -0.64 |
| 504 | Wardha | 0.45 | -0.13 | 1.53 | -1.67 | -0.63 | 0.17 |
| 502 | Washim | 1.03 | -0.05 | 0.46 | -0.68 | -0.80 | 0.65 |
| 510 | Yavatmal | 1.17 | -1.10 | 0.85 | -1.45 | -0.64 | 0.00 |

## 8. Interpretation of the components

Loadings of about |0.5| or more are treated as "strong" in the descriptions below.

### PC1 (34.3%) — dryland agrarian interior vs coastal / eastern smallholder districts

- **Positive:** ENSO–rainfall slope (0.74), agricultural worker share (0.71) and low literacy (0.67).
- **Negative:** small-holding share (−0.66).
- **Weak:** rainfed share (0.29) and deficient frequency (0.19).
- **High scores:** Dharashiv, Nandurbar, Parbhani, Latur, Solapur, Jalna, Beed.
- **Low scores:** Thane, Gondia, Raigad, Kolhapur, Bhandara, Pune.

High-PC1 districts combine a strong historical association between El Niño and lower monsoon rainfall, a large agricultural workforce and lower literacy. They also have *fewer* small holdings (larger average holdings). Low-PC1 districts are mostly in the Konkan, the western ghats belt and the eastern rice belt. There the ENSO–rainfall association is weak, and small holdings are very common.

**PC1 should not be called "vulnerability".** Under the framework, all six inputs are aligned so that higher = more vulnerable, yet small-holding share loads *opposite* to the other three strong variables. A high PC1 score therefore means "more vulnerable" on ENSO exposure, agricultural dependence and literacy, but "less vulnerable" on landholding size. The negative loading reflects geography: small holdings are concentrated in wetter coastal and eastern districts. It is not evidence that small holdings reduce vulnerability.

### PC2 (20.8%) — frequency of deficient El Niño monsoons

- **Strong:** El Niño deficient frequency (0.88), rainfed share (−0.56), with a smaller contribution from the ENSO slope (0.33).
- **High scores:** Pune (3.57, by far the largest), Solapur, Ahilyanagar, Beed, Dharashiv, Satara.
- **Low scores:** Ratnagiri, Sindhudurg, Dhule, Jalgaon, Chhatrapati Sambhajinagar.

This component mainly measures how often El Niño years were deficient. It picks out the western rain-shadow districts, which are also relatively more irrigated (hence the negative rainfed loading). **Pune dominates this component.** Its high deficient frequency is partly linked to the implausible IMD rainfall values documented in the data quality report. The stability check (section 9) shows that PC2 changes considerably when Pune is left out.

### PC3 (19.4%) — rainfed cropping vs the agricultural, smallholder rice belt

- **Positive:** rainfed share (0.69), with some deficient frequency (0.30).
- **Negative:** agricultural worker share (−0.53), small-holding share (−0.43) and low literacy (−0.36).
- **High scores:** Thane, Wardha, Nagpur, Pune, Akola, Palghar.
- **Low scores:** Bhandara, Gondia, Gadchiroli, Satara.

This component contrasts districts with mostly rainfed cropland but a smaller agricultural workforce against the east-Vidarbha rice districts (Bhandara, Gondia, Gadchiroli), which have a higher irrigated share, many farm workers and many small holdings. Two of its loadings (small holding −0.43, literacy −0.36) are close to the "strong" cut-off, so the exact description is less firm than for PC1.

### PC4–PC6

Eigenvalues below 1 (together 25.5% of the variance). They are not interpreted.

### Is there a coherent interpretation?

- **PC1** is coherent as a *regional contrast* (dry interior vs coastal/eastern districts) and is stable (see the stability report). It is **not** a one-directional vulnerability axis, because small-holding share runs against the other strong variables.
- **PC2** is coherent (El Niño deficient frequency) but heavily influenced by one district (Pune).
- **PC3** is a contrast between rainfed cropping and agricultural dependence, and its composition is less firm.
- PC2 and PC3 are best read together, as a pair (see the stability report).

## 9. Implications before building an index (no decision taken here)

Taking PC1 scores directly as a vulnerability index would, through the small-holding loading, rank districts with *more* small holdings as *less* vulnerable. This contradicts the framework's own assumption. Before an index or K-Means is built, the project needs to decide how the components will be used. For example:

- combine several components with explicit direction checks;
- use PCA mainly to show the structure, with a separately justified weighting;
- revisit the small-holding variable or the feature set.

The Pune rainfall issue should also be considered, because it shapes PC2. These are open questions for the next stage. No index has been built.
