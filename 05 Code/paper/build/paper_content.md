TITLE: Artificial Intelligence-Driven Vulnerability Index Mapping for Districts in Maharashtra to El Niño Droughts Using Socioeconomic and Climatic Principal Component Analysis

AUTHOR: Prof. Pankaj Deshmukh | Dept. of Artificial Intelligence and Data Science | K. J. Somaiya Institute of Technology | Mumbai, India | pankaj@somaiya.edu
AUTHOR: Peeyusha Patki | Dept. of Artificial Intelligence and Data Science | K. J. Somaiya Institute of Technology | Mumbai, India | peeyusha.p@somaiya.edu

ABSTRACT: Drought impacts depend not only on lost monsoon rainfall but also on a district's reliance on rain-fed agriculture and its capacity to cope. This paper presents an exploratory composite index of relative El Niño drought vulnerability for 34 districts of Maharashtra, India. Six indicators were built from official sources: the sensitivity of June to September rainfall to the Relative Oceanic Niño Index and the frequency of deficient monsoons in 18 El Niño years, from India Meteorological Department gridded rainfall for 1950 to 2024; agricultural-worker share and literacy from Census 2011; rainfed share of net sown area from the Census 2011 Village Directory; and small-holding share from the Agriculture Census 2010-11. After direction alignment and standardization, principal component analysis was used only to derive indicator weights, from the absolute loadings of three retained components (74.5 percent of variance) weighted by explained variance. The weighted sum was rescaled to a relative 0 to 100 index, and K-Means clustering of the index (K = 3) identified 10 High, 20 Medium and 4 Low vulnerability districts, with the High group concentrated in Marathwada. The weights were close to equal (0.151 to 0.183), consistent with a low Kaiser-Meyer-Olkin value of 0.40, and rankings were stable across six alternative specifications (rank correlation 0.934 to 0.995). The index showed a moderate positive association with the share of talukas declared drought-affected by the state government in 2018 (Spearman 0.585), 2023 (0.450) and a 2026 holdout (0.545), offering a transparent basis for district-level drought preparedness screening.

KEYWORDS: drought vulnerability, El Niño, principal component analysis, composite index, K-Means clustering

# Introduction

Drought is a recurring hazard whose impacts arise from the interaction between a rainfall deficit and the agricultural and social systems that the deficit affects [@mishra2010; @wilhelmi2002]. In India, kharif agriculture depends heavily on the June to September southwest monsoon, and year-to-year monsoon variability is reflected in crop production [@kumar2004]. The El Niño-Southern Oscillation (ENSO) is one of the main external influences on this variability. Warm El Niño conditions in the tropical Pacific have historically been associated with below-normal Indian monsoon rainfall [@rasmusson1983; @kumar2006], although the relationship has varied over time and not every El Niño year produces a drought [@kumar1999; @kumar2006].

Maharashtra shows why rainfall alone is an incomplete guide to drought impact. Recurring drought is a major challenge in its drought-prone areas, where agriculture, including rainfed cropping and livestock, is the main income activity of much of the population [@udmale2014]. A 50-year district study of the state found that some districts were vulnerable despite low exposure to climate variability, because of their sensitivity and adaptive-capacity characteristics [@swami2021]. This agrees with the widely used view of vulnerability as a function of exposure, sensitivity and adaptive capacity [@ipcc2001; @fussel2007]. A district assessment therefore has to combine climate exposure with agricultural dependence, irrigation status, landholding structure and socioeconomic capacity.

Combining such indicators requires weights. Expert-based schemes such as the analytic hierarchy process (AHP) are common in Indian drought studies but rest on subjective judgments [@chakraborty2016; @saha2021], while equal weighting ignores the overlap between indicators. Multivariate methods such as principal component analysis (PCA) provide data-driven weights, but they need care: component signs are arbitrary, and with few spatial units the estimated structure can be unstable [@oecd2008; @jolliffe2016]. In addition, few district studies link vulnerability explicitly to El Niño-specific rainfall behaviour or test their output against independent administrative drought records.

This paper addresses these gaps for Maharashtra. Its contributions are as follows.

- A reproducible district dataset for 34 Maharashtra districts that links 75 years of India Meteorological Department (IMD) gridded rainfall with the Relative Oceanic Niño Index (RONI) to derive two El Niño-specific exposure indicators, combined with four census-based sensitivity and adaptive-capacity indicators.
- A PCA-based weighting procedure that uses absolute loadings, so that PCA sets the magnitude of each weight while the vulnerability framework fixes its direction, together with an explicit account of its statistical limits.
- A relative 0 to 100 index and a K-Means Low, Medium and High classification mapped at district level, with a robustness check against six alternative specifications.
- A validation against Government of Maharashtra drought declarations for 2018 and 2023, and a 2026 holdout examined only after the index and groups were fixed.

Section II reviews related work, Section III describes the study area and data, Section IV presents the methodology, Section V reports and discusses the results, Section VI states the limitations and Section VII concludes.

# Related Work

Vulnerability research separates the hazard from the characteristics of the exposed system that shape its consequences [@adger2006; @fussel2007]. Indicator-based assessments put this into practice through exposure, sensitivity and adaptive capacity, a structure taken from the Intergovernmental Panel on Climate Change (IPCC) Third Assessment Report [@ipcc2001] and widely applied to agricultural drought [@wilhelmi2002; @murthy2015].

Indian studies have applied this structure at several scales. Murthy et al. [@murthy2015] built a composite agricultural drought vulnerability index from exposure, sensitivity and adaptive capacity using geospatial data, and Sharma and Ravindranath [@sharma2019] applied the IPCC 2014 framework to hazard-specific vulnerability assessment. Chakraborty and Joshi [@chakraborty2016] mapped the disaster vulnerability of Indian districts with AHP, and Saha et al. [@saha2021] combined fuzzy logic with AHP to map drought vulnerability in Odisha. Within Maharashtra, Nair and Mirajkar [@nair2022] assessed drought vulnerability across the Vidarbha region, and Swami and Parthasarathy [@swami2021] aggregated district indicators with equal weights over 1966 to 2015. These studies show the value of combining physical and social indicators, but they mostly rely on expert or equal weights, and their climate exposure is generally not tied to ENSO.

Statistical weighting through PCA or factor analysis is a recognised option for composite indicators [@oecd2008]. Cutter et al. [@cutter2003] used factor analysis to construct the Social Vulnerability Index, and Abson et al. [@abson2012] used PCA for socio-ecological vulnerability mapping in Southern Africa. Balaganesh et al. [@balaganesh2020] derived PCA weights for a composite drought vulnerability index of Tamil Nadu districts and classified the districts by index magnitude. Kim et al. [@kim2021] combined PCA with a Gaussian mixture model to assess regional drought vulnerability and risk in South Korea, and Pinzón Flórez et al. [@pinzon2026] derived indicator weights from eigenvalues and absolute loadings for a territorial composite vulnerability index. The composite-indicator handbook of the Organisation for Economic Co-operation and Development (OECD) and the European Commission's Joint Research Centre (JRC) notes that PCA-based weights depend on correlation among the indicators and are sensitive to small samples, which is why factorability is usually checked with the Kaiser-Meyer-Olkin (KMO) measure [@kaiser1974] and Bartlett's test before such weights are used [@oecd2008].

Cluster analysis has also been used to group spatial units into vulnerability classes, for example K-Means classification of social vulnerability [@uzcategui2023]. K-Means [@lloyd1982] partitions observations by minimizing the within-cluster sum of squared distances. When it is applied to a single index, it places class boundaries at natural gaps in the values rather than at fixed cut-offs.

Compared with this literature, the present study (i) derives exposure specifically from the El Niño behaviour of long gridded rainfall records using the current official ENSO index of the U.S. National Oceanic and Atmospheric Administration (NOAA), (ii) uses sign-safe PCA weights with explicit factorability, retention and stability diagnostics, (iii) applies clustering only after the index has been constructed, and (iv) evaluates the result against administrative drought declarations that were never used in constructing the index, including a holdout year.

# Study Area and Data

The study area is Maharashtra in its current administrative form of 36 districts. Palghar, which was separated from Thane after the 2011 Census, was reconstructed from its eight Census 2011 sub-districts in every source. Mumbai City and Mumbai Suburban have no villages in the Census 2011 Village Directory and no holdings in the Agriculture Census report, so the agricultural and landholding indicators do not exist for them. They were excluded from the index, which therefore covers 34 districts. All tables were joined on numeric Census 2011 and Local Government Directory district codes, and names were never used as join keys. Renamed districts (Ahilyanagar, Chhatrapati Sambhajinagar and Dharashiv) keep their original codes.

Climate data were taken from the IMD 0.25 × 0.25 degree gridded daily rainfall product [@pai2014] for 1950 to 2024, the primary study period. The ENSO index is the NOAA Climate Prediction Center's RONI, which compares the Niño-3.4 sea surface temperature anomaly with the tropical-mean anomaly so that background warming does not inflate it [@vanoldenborgh2021]. RONI values were taken from NOAA's published series [@noaaroni], and RONI became NOAA's official ENSO index in February 2026 [@noaaannounce]. The conventional Oceanic Niño Index (ONI) was used only as a sensitivity check.

The agricultural-worker share and literacy rate were computed from the Census 2011 Primary Census Abstract [@census2011]. The rainfed share of net sown area was computed from the Census 2011 District Census Handbook Village Directory [@censusvd], and the small-holding share from the Agriculture Census 2010-11 Maharashtra State Report [@agcensus2014]. District polygons came from the Survey of India Administrative Boundary Database [@soi]. Table I lists the six indicators.

TABLE: Final Indicators, Vulnerability Dimensions and Sources
| No. | Indicator (unit) | Dimension | Sign | Source |
| 1 | ENSO rainfall slope (% per °C) | Exposure | −1 | IMD, RONI |
| 2 | El Niño deficient frequency (fraction) | Exposure | +1 | IMD, RONI |
| 3 | Agricultural-worker share (% of workers) | Sensitivity | +1 | Census 2011 |
| 4 | Rainfed share of net sown area (%) | Sensitivity | +1 | Village Directory 2011 |
| 5 | Small-holding share, below 2 ha (% of holdings) | Sensitivity | +1 | Agriculture Census 2010-11 |
| 6 | Literacy rate, age 7 and above (%) | Adaptive capacity | −1 | Census 2011 |
NOTE: Sign is the multiplier applied so that a higher aligned value means greater vulnerability.

Drought declarations issued by the Government of Maharashtra for the kharif seasons of 2018 [@gr2018] and 2023 [@gr2023], and the Trigger-1 declaration of 2026 [@gr2026], were used for validation only. They follow the staged procedure of the national Manual for Drought Management [@dmm2016]. Socioeconomic data refer to 2011 and landholding data to 2010-11.

# Methodology

The workflow is shown in Fig. 1. Every methodological choice, its alternatives and the active option were recorded in a project decision file, the alternatives were kept for sensitivity analysis, and the pipeline was implemented in Python with scikit-learn [@pedregosa2011].

![Methodology of the vulnerability mapping framework. Drought declarations enter only at the validation stage.](figures/fig1_methodology.png)

## Data Preprocessing

Each 0.25 degree grid cell was represented by its box around the grid point. The weight of a cell for a district was the area of the box inside the district polygon, computed in an Albers equal-area projection. Daily district rainfall was the area-weighted mean over cells, and the monsoon total *P*_{i,y} of district *i* in year *y* was the sum over June to September. The baseline *P̄*_{i} was the district's own mean monsoon rainfall over 1971 to 2020, IMD's current normal period, and the departure was

$$departure$$

Two data-quality issues were handled without editing the raw files. In the Village Directory, the columns labelled irrigated and unirrigated area are interchanged: the source-wise irrigated areas sum to the column labelled unirrigated in 43,661 of 43,665 villages, so the processing code maps the columns explicitly. In the IMD grid, ten district-years exceed twice the district baseline, for example Pune in 2005 (4.87 times) and 2009 (2.03 times). No published correction was found, so all published values were kept in the primary analysis and a version excluding Pune's two flagged years was computed for sensitivity only. No values were imputed.

## ENSO and Rainfall Characterization

Warm ENSO seasons were identified with NOAA's rule: the three-month index, rounded to 0.1 °C, is at least +0.5 °C for at least five consecutive overlapping seasons. The implementation reproduced all 919 seasons of NOAA's published ONI table and 915 of 919 seasons of the RONI table; the four differences lie in a 1984 La Niña run and affect no El Niño season. A year was treated as an El Niño monsoon year when both the June to August and July to September seasons fell inside a warm episode. This gave 18 El Niño monsoon years under RONI between 1950 and 2024.

The first exposure indicator is the ordinary least-squares slope *b*_{i} of the departure *D*_{i,y} on *I*_{y}, the mean of the June to August and July to September RONI values, over all 75 years:

$$slope$$

A negative slope means that warmer ENSO conditions have historically been associated with lower monsoon rainfall in that district. The second indicator, *f*_{i}, is the share of the 18 El Niño years in which *D*_{i,y} ≤ −20 percent, the lower bound of IMD's deficient category, evaluated on the unrounded departure. The slope uses all years and describes the typical association, while the frequency records how often El Niño monsoons were actually deficient; the two are only weakly correlated (r = 0.33 after alignment).

## Feature Selection and Vulnerability Dimensions

Thirty candidate indicators were audited before any modelling. Exact identities (for example, rainfed share equals 100 minus irrigated share), alternative denominators and nested measures were reduced to one member each, and variables without a clear vulnerability direction were excluded. The resulting six indicators in Table I cover exposure (the two ENSO indicators), sensitivity (agricultural-worker share, rainfed share and small-holding share) and adaptive capacity (literacy). The largest absolute correlation between any two of them is 0.45. The direction of each indicator is an assumption of the exposure, sensitivity and adaptive-capacity framework and is not tested by this study.

## Direction Alignment and Standardization

The ENSO slope and literacy were multiplied by −1, and the other four indicators by +1, so that a higher aligned value means greater vulnerability for all six. Each aligned indicator was then standardized over the 34 districts with scikit-learn's StandardScaler:

$$zscore$$

where *s*_{j} is the sign in Table I, *x*_{ij} is the original value, and *μ*_{j} and *σ*_{j} are the mean and population standard deviation of the aligned indicator *j*. No logarithmic transformation was applied, so the indicators keep their direct interpretation.

## Principal Component Analysis

PCA was applied to the 34 × 6 standardized matrix, which is equivalent to the eigen-decomposition of the correlation matrix **R** [@jolliffe2016]:

$$pca$$

The eigenvalues *λ*_{k} sum to 6, the explained-variance ratio is EVR_{k} = *λ*_{k}/6, and the loading of indicator *j* on component *k*, its correlation with the component, is

$$loading$$

The number of retained components was chosen with the Kaiser rule (eigenvalue above 1) [@kaiser1960], the OECD and JRC practice of eigenvalues above 1, each component above 10 percent and a cumulative share above 60 percent, and the Jolliffe threshold of 0.7, both as described in the handbook [@oecd2008]. Horn's parallel analysis [@horn1965], based on 5,000 random 34 × 6 data sets, and a leave-one-district-out refit of the scaler and PCA were used as diagnostics. Factorability was summarized by the KMO measure [@kaiser1974] and Bartlett's test of sphericity.

## PCA-Based Vulnerability Index Construction

PCA was used only to derive indicator weights; the index is not a principal component. With *K* = 3 retained components, the raw weight of indicator *j* and its normalized weight are

$$rawweight$$

$$weight$$

Absolute loadings are used because the sign of a principal component is arbitrary, whereas the direction of each indicator is fixed by the framework through the alignment step. In these data, the small-holding share loads opposite to the other strong indicators on the first component, so signed aggregation of components would give it a negative weight and contradict its stated direction. The absolute-loading form lets PCA determine how much each indicator counts, while alignment determines which way it counts. The resulting weights are exploratory statistical weights and do not represent theoretical importance.

The composite score of district *i* and its rescaled index are

$$score$$

$$index$$

Because the scaling uses the observed minimum and maximum, the index is relative to the 34 districts: 0 marks the lowest observed score, not an absence of vulnerability, and the index is not a probability.

Six alternative versions were computed for sensitivity analysis only: equal weights, the OECD and JRC factor-analysis weighting with varimax-rotated squared loadings [@oecd2008], a hazard and social version that averages the two exposure indicators and the four other indicators as equally weighted sub-indices, absolute-loading weights from all six components, rainfall indicators recomputed without Pune's two flagged years, and ONI instead of RONI. Each was compared with the primary index by Spearman rank correlation, rank shifts and changes of group.

## K-Means Classification

K-Means [@lloyd1982] was applied to the final 0 to 100 index only, not to the indicators or principal component scores, to obtain three relative groups. It minimizes

$$kmeans$$

where *c*_{g} is the centroid of group *g*. The scikit-learn implementation was used with *K* = 3, random_state = 2026 and n_init = 20, so the result is reproducible. Because K-Means numbers its clusters arbitrarily, the clusters were ordered by centroid and labelled Low, Medium and High. No rescaling was needed for a single variable. The silhouette coefficient [@rousseeuw1987], solutions for *K* = 2 and *K* = 4, and a tertile split were computed as diagnostics only.

## Drought-Declaration Validation

The validation asks whether districts with higher index values tended to have a larger share of their talukas declared drought-affected. For district *i* and year *t*, the declared share is

$$share$$

where *d*_{i,t} is the number of talukas declared in the main Government Resolution (GR) and *T*_{i} is the number of Census 2011 talukas (355 in total). For 2018 and 2023 the numerator counts severe and moderate talukas in the final declaration; for 2026 it counts Trigger-1 talukas. Revenue circles declared in separate supplementary orders were not added, because no verified total of revenue circles per district exists to form a share.

The primary statistic is Spearman's rank correlation between the fixed index and the declared share (n = 34), chosen because the shares are bounded with many ties. Group means of the share are a secondary check. The declarations were never used in feature selection, weighting, scaling or clustering, and the 2026 declaration was examined only after the index and groups had been fixed.

# Results and Discussion

## PCA Results

The six indicators share little common structure. The KMO measure is 0.40, below the 0.6 usually recommended for PCA-based weighting [@oecd2008], although Bartlett's test rejects an identity correlation matrix (χ² = 35.5, 15 degrees of freedom, p = 0.002). This is largely a consequence of feature selection, which removed redundant indicators. It means that the data contain weak common-factor structure, so the PCA-derived weights should be interpreted as exploratory statistical weights rather than as evidence of a strong latent vulnerability construct.

TABLE: PCA Eigenvalues and Explained Variance
| Component | Eigenvalue | EVR (%) | Cum. (%) | PA 95th pct. |
| PC1 | 2.056 | 34.3 | 34.3 | 1.874 |
| PC2 | 1.246 | 20.8 | 55.0 | 1.465 |
| PC3 | 1.165 | 19.4 | 74.5 | 1.194 |
| PC4 | 0.663 | 11.1 | 85.5 | 0.994 |
| PC5 | 0.616 | 10.3 | 95.8 | 0.819 |
| PC6 | 0.253 | 4.2 | 100.0 | 0.636 |
NOTE: EVR: explained-variance ratio. PA 95th pct.: 95th percentile of eigenvalues from parallel analysis of 5,000 random 34 × 6 data sets.

Table II and Fig. 2 show that three components have eigenvalues above 1 and together explain 74.5 percent of the variance, so the Kaiser, OECD and JRC, and Jolliffe rules all retain three. Horn's parallel analysis retains only PC1, the only eigenvalue clearly above the random-data benchmark, which reflects the uncertainty of a 34-district sample. The leave-one-district-out analysis supports PC1: its direction barely changes (median absolute cosine 0.999; minimum 0.948 when Pune is omitted). PC2 and PC3 have close eigenvalues and can swap order when Pune or Ratnagiri is omitted, but the plane they span remains stable (projection of at least 0.926).

![Eigenvalues of the six principal components with explained-variance percentages, the Kaiser criterion and the 95th percentile of eigenvalues from parallel analysis.](figures/fig2_pca_variance.png)

The loadings in Fig. 3 give PC1 a clear regional meaning. It loads positively on the ENSO slope (0.74), agricultural-worker share (0.71) and low literacy (0.67), and negatively on the small-holding share (−0.66). It therefore contrasts the dry agrarian interior, where El Niño rainfall losses are large, with coastal and eastern districts where small holdings are common. PC2 is dominated by the deficient frequency (0.88), and Pune has by far the highest PC2 score; PC3 contrasts rainfed cropping (0.69) with agricultural employment (−0.53). Because the small-holding share runs against the other strong indicators, PC1 cannot itself serve as a vulnerability score, which is why the index is built from absolute-loading weights.

![Loadings of the six aligned indicators on the three retained components, with the final weight of each indicator.](figures/fig3_pca_loadings.png)

## Final Vulnerability Index

TABLE: Final PCA-Derived Indicator Weights
| Indicator | *L*_{1} | *L*_{2} | *L*_{3} | *r*_{j} | *w*_{j} |
| ENSO rainfall slope | 0.739 | 0.329 | 0.102 | 0.341 | 0.168 |
| El Niño deficient frequency | 0.192 | 0.880 | 0.303 | 0.307 | 0.151 |
| Agricultural-worker share | 0.712 | −0.119 | −0.529 | 0.372 | 0.183 |
| Rainfed share | 0.290 | −0.562 | 0.690 | 0.350 | 0.173 |
| Small-holding share | −0.661 | 0.080 | −0.425 | 0.326 | 0.161 |
| Literacy | 0.667 | −0.166 | −0.356 | 0.332 | 0.164 |
NOTE: Loadings refer to the aligned indicators. The raw weights sum to 2.029. For the ENSO slope, r = 0.343 × 0.739 + 0.208 × 0.329 + 0.194 × 0.102 = 0.341 and w = 0.341 / 2.029 = 0.168.

Table III gives the final weights. All six are positive and lie between 0.151 and 0.183, close to the equal weight of 0.167. Agricultural-worker share and rainfed share receive the largest weights and the deficient frequency the smallest. The near-equal weights follow directly from the weak correlation structure: PCA finds no strong reason to weight any indicator far above the others, so the index draws on climatic, agricultural and socioeconomic information in similar proportions.

The rescaled index has a mean of 52.8, a median of 47.5, a sample standard deviation of 23.8 and an interquartile range of 38.2 to 68.5. Beed has the highest observed score (raw score 0.838, index 100) and Nagpur the lowest (raw score −0.939, index 0). Beed combines a rainfall slope of −23.5 percent per °C, deficient monsoons in 8 of 18 El Niño years, an agricultural-worker share of 78.0 percent, a rainfed share of 82.3 percent and a literacy rate of 77.0 percent. Nagpur, by contrast, has an agricultural-worker share of 33.7 percent, literacy of 88.4 percent and a weaker slope of −10.7 percent per °C. The spatial pattern of the index is shown in Fig. 4.

![Relative 0 to 100 El Niño drought vulnerability index for the 34 in-scope districts. Mumbai City and Mumbai Suburban (hatched) are outside the index.](figures/fig4_vulnerability_index_map.png)

## Low/Medium/High Vulnerability Groups

TABLE: K-Means Vulnerability Groups (K = 3)
| Group | n | Centroid | Index range | Districts |
| High | 10 | 82.4 | 65.9 to 100.0 | Beed, Jalna, Latur, Dharashiv, Parbhani, Nanded, Nandurbar, Ahilyanagar, Solapur, Hingoli |
| Medium | 20 | 45.9 | 32.6 to 62.7 | Remaining 20 districts |
| Low | 4 | 13.8 | 0.0 to 25.6 | Bhandara, Gondia, Thane, Nagpur |
NOTE: Boundaries between groups lie at 29.8 and 64.1. Silhouette coefficient 0.587.

Table IV and Fig. 5 summarize the groups. Seven of the eight Marathwada districts fall in the High group; the eighth, Chhatrapati Sambhajinagar, is Medium (49.1). The High group also includes Ahilyanagar and Solapur in the dry interior and Nandurbar in the north-west, which has the lowest literacy rate of the 34 districts (64.4 percent). On average, High-group districts have an ENSO slope of −19.9 percent per °C, compared with −8.0 percent per °C in the Low group, and a literacy rate of 75.2 percent against 86.1 percent. The largest mean weighted contributions in the High group come from the ENSO slope and literacy. The Low group consists of two predominantly urban districts, Nagpur and Thane (Census 2011 rural population shares of 31.7 and 13.8 percent; agricultural-worker shares of 33.7 and 8.3 percent), and the east Vidarbha districts of Bhandara and Gondia, which have the lowest rainfed shares (45.3 and 46.4 percent) and weak ENSO slopes.

![K-Means (K = 3) vulnerability groups. Groups are relative to the 34 districts and are not drought predictions.](figures/fig5_vulnerability_groups_map.png)

The groups are unequal in size because K-Means follows gaps in the index rather than forcing equal groups. The low end of the index is spread out, so only four districts sit clearly below the large middle block. The silhouette coefficient of 0.587 indicates reasonably separated groups. *K* = 2 gives a marginally higher value (0.594) and *K* = 4 a lower one (0.571), so three groups are a reasonable fit for the required three-level classification. A tertile split agrees with K-Means for 25 of the 34 districts; all nine differences are K-Means Medium districts, because tertiles impose equal group sizes.

## Sensitivity and Robustness Analysis

TABLE: Rank Agreement of Alternative Index Versions with the Primary Index
| Alternative version | ρ | Max. rank shift | Districts changing group |
| PCA absolute loadings, all 6 components | 0.995 | 3 | 1 |
| Pune flagged years excluded | 0.995 | 3 | 1 |
| Equal weights | 0.993 | 5 | 2 |
| Hazard and social sub-indices | 0.991 | 6 | 1 |
| ONI instead of RONI | 0.961 | 6 | 4 |
| OECD and JRC factor weights | 0.934 | 10 | 2 |

Table V shows that the district ordering is robust. Every alternative has a Spearman correlation of at least 0.934 with the primary index, and all but the OECD and JRC version are at or above 0.961. At most four of the 34 districts change group, and no district moves between Low and High in any version. The districts that change are close to a group boundary, for example Wardha (32.6), Hingoli (65.9), Washim (62.7) and Buldhana (61.2), and their classification should be treated as less certain. The very high agreement with equal weights (0.993) confirms that the ranking does not hinge on the precise PCA weights. Excluding Pune's two flagged rainfall years lowers Pune's index from 37.3 to 35.3 and leaves the ranking almost unchanged. The OECD and JRC method differs most because it rewards indicators that belong clearly to a single rotated factor, which gives the ENSO slope a low weight (0.092). With ONI instead of RONI, Jalna rather than Beed has the highest index.

## Drought Validation

TABLE: Drought Declarations Used for Validation and Results
| Item | 2018 | 2023 | 2026 (holdout) |
| Declaration stage | Final | Final | Trigger-1 |
| GR date | 31-10-2018 | 31-10-2023 | 25-09-2026 |
| Talukas declared (main GR) | 151 | 40 | 265 |
| Districts with any declaration | 26 | 15 | 32 |
| Spearman ρ (index vs. share) | 0.585 | 0.450 | 0.545 |
| p (two-sided) | 0.0003 | 0.008 | 0.0009 |
| Mean share, Low group | 0.05 | 0.00 | 0.39 |
| Mean share, Medium group | 0.39 | 0.10 | 0.70 |
| Mean share, High group | 0.66 | 0.20 | 0.99 |
NOTE: n = 34 districts in every year. Share: talukas declared divided by Census 2011 talukas.

Table VI and Fig. 6 show that the index has a moderate positive association with the declared taluka share in all three years. In 2018, the most informative year with 26 districts declared, districts with higher index values tended to have a larger share of talukas declared (ρ = 0.585). The association is weaker in 2023 (ρ = 0.450), when the main GR covered only 40 talukas and the remaining declarations were made by revenue circle. In the 2026 holdout, the fixed index and groups show an association of similar strength (ρ = 0.545). In every year the mean declared share rises from the Low group to the Medium and High groups.

![Vulnerability index against the share of talukas declared drought-affected in 2018, 2023 and the 2026 holdout, by K-Means group.](figures/fig6_validation_scatter.png)

The districts where the two measures disagree are informative. Latur and Nanded in 2018, and Nanded and Parbhani in 2023, have high index values but few declared talukas. Much of their declaration was made at revenue-circle level (for example, 42 additional circles in Latur in 2018 and 46 in 2023), which the taluka share does not capture. In 2026, Nagpur, the district with the lowest index, had all 14 talukas declared. IMD reported a seasonal rainfall departure of −33 percent for Nagpur up to 26 September 2026, and Trigger-1 is a rainfall-led stage, so a severe single-season deficit can lead to declaration in a district that the index rates as relatively less vulnerable. These cases illustrate the difference between long-term relative vulnerability and the outcome of one season.

Overall, the validation is consistent with the index capturing relative drought vulnerability. Only 2023 was an El Niño monsoon year under the RONI rule, so the validation tests general correspondence with drought declarations rather than El Niño-driven drought alone. It does not establish causality and does not show that the index predicts future droughts.

# Limitations

The study has several limitations. First, the primary index covers only 34 districts, which limits statistical power; parallel analysis retains only one component, and the second and third components are not separately stable. Second, the KMO value of 0.40 indicates weak common-factor structure, so the weights are exploratory and close to equal weighting, and the small-holding share is negatively correlated with the other aligned indicators, so its direction is set by the framework rather than shown by the data. Third, the socioeconomic and agricultural indicators refer to 2011 and 2010-11 and are combined with current Survey of India boundaries, and adaptive capacity is represented only by literacy because no verified district data on income, credit or infrastructure were available. Fourth, some published IMD rainfall values, notably Pune's in 2005 and 2009, are implausibly high; they were kept as published, and whether they are errors could not be verified. Fifth, drought declarations are administrative decisions rather than direct observations of crop loss: the 2023 taluka list captures only part of that year's declarations, and the 2026 holdout is an early Trigger-1 stage in which 19 of 34 districts were fully declared, which limits discrimination. Finally, the 0 to 100 index is relative to the districts studied, and the analysis identifies associations rather than causal effects.

# Conclusion and Future Work

This study developed an exploratory composite index of relative El Niño drought vulnerability for 34 districts of Maharashtra by combining two El Niño-specific rainfall indicators with four agricultural and socioeconomic indicators. PCA was used to derive sign-safe weights from absolute loadings, the weighted sum was rescaled to a relative 0 to 100 index, and K-Means grouped the districts into 10 High, 20 Medium and 4 Low vulnerability districts. The highest vulnerability is concentrated in Marathwada and the adjoining dry interior, where large El Niño rainfall losses coincide with high agricultural dependence and lower literacy. The weights were close to equal, the ranking was stable across six alternative specifications, and the index showed a moderate positive association with drought declarations in 2018, 2023 and a 2026 holdout. The framework is transparent and reproducible and can support district-level screening for drought preparedness, provided its relative and exploratory nature is respected.

Future work can update the socioeconomic indicators when the next census becomes available, add verified adaptive-capacity variables such as irrigation infrastructure, credit access and income, and extend the analysis to taluka level and to other states. Validation can be strengthened with crop-loss or yield data and with the final 2026 declaration when it is issued.

##### Acknowledgment

The authors thank the Department of Artificial Intelligence and Data Science, K. J. Somaiya Institute of Technology, for its support, and the India Meteorological Department, NOAA Climate Prediction Center, Office of the Registrar General and Census Commissioner, Government of Maharashtra and Survey of India for making the data used in this study available. The authors also thank Saad Patel and Tanishq Mewada for their contributions to the minor project on which this work is based.

The authors used Claude (Anthropic), an AI assistant, to draft and edit the manuscript text, to prepare and format the documents, including the references, tables and figures, and to assist with writing and formatting the data-processing and analysis code. The authors reviewed, checked and edited all text, code and results, and take full responsibility for the content of this article.
