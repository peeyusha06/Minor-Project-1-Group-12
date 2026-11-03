# Drought-Declaration Validation of the Final Vulnerability Index

Script: `src/s18_drought_validation.py`. Tests: `tests/test_drought_validation.py`.

Outputs (`data/processed/`):

| File | Contents |
|---|---|
| `drought_validation_districts.csv` | 2018 and 2023, one row per district-year |
| `drought_validation_holdout_2026.csv` | 2026 holdout, one row per district |
| `drought_validation_summary.csv` | Correlations and group means/medians |

The fixed index (`vulnerability_index_scores.csv`) and K-Means classes (`kmeans_vulnerability_classification.csv`) were
only read, never changed (checksums identical before and after). Drought declarations were never used in feature
selection, weighting, scoring, scaling or clustering. A test checks that no index or classification table contains
declaration columns, and that steps 11–17 never read the declaration data.

## 1. Validation objective

Primary question: **do districts with higher vulnerability-index values tend to have greater drought-declaration
intensity?**

- The continuous 0–100 index is tested first, using Spearman rank correlation.
- The Low / Medium / High groups are checked second.
- The same fixed index is used for every year.

## 2. What drought declarations measure

A Government of Maharashtra drought GR lists the talukas (and in some years extra revenue circles) where drought is
declared in a given kharif season. It follows the procedure of the Drought Management Manual/Code 2016 cited in the GRs:
rainfall-deficit and other indicators (Trigger-1), then crop-condition surveys (the 2026 GR orders field surveys
(panchnamas)).

Declarations are **administrative decisions** about one season. They are not a direct measurement of drought damage, and
they depend on:
- that season's rainfall;
- the government's criteria;
- survey processes;
- decision timing.

The index, by contrast, describes long-term El Niño rainfall sensitivity plus 2010–11 agricultural and socioeconomic
conditions. Agreement between the two is therefore evidence of **consistency**, not proof.

## 3. Data sources

All files are already in `data/raw/validation/` and were transcribed or checked in the data-engineering stage.

| Year | GR | Declared | Stage |
|---|---|---|---|
| 2018 | 201810311722349219, 31-10-2018 | 151 talukas (112 severe + 39 moderate) | final declaration |
| 2018 | 201811061721013119, 06-11-2018 | 268 additional revenue circles outside those talukas | — |
| 2023 | 202310311545053419, 31-10-2023 | 40 talukas (24 severe + 16 moderate) | final declaration |
| 2023 | 202311101718225419, 10-11-2023 | 1,021 additional revenue circles | — |
| 2026 (holdout) | 202609261117494941, 25-09-2026 | 265 talukas | **Trigger-1** (first trigger), based on the June–September 2026 rainfall deficit and the Agriculture Commissioner's report of 24-09-2026 |

- **Denominator:** Census 2011 sub-districts (talukas) per district, 355 in total. All 355 match Survey of India
  sub-district codes, and Palghar is formed from its 8 official talukas.
- The transcribed taluka counts reproduce every GR total (151, 40, 265), and the listed names match the stated count on
  every district row.

## 4. The drought-intensity measure and why it was chosen

**Primary measure (all three years):**

  declared_taluka_share = talukas declared in the main GR / Census 2011 talukas in the district

- It has a **verified denominator**, is available for **all 34 districts in every year**, uses **one unit type**
  (talukas), and needs **no correction** of ambiguous records.
- 2018 and 2023 count severe + moderate talukas; 2026 counts Trigger-1 talukas.
- Secondary measure for 2018 and 2023: the severe-only taluka share.

**Why revenue circles are not used as an intensity measure:**
1. No verified source gives the total number of revenue circles per district, so no share can be computed.
2. Additional circles are listed only **outside** the declared talukas. A fully declared district such as Beed in 2018
   (11 of 11 talukas) therefore necessarily shows 0 extra circles. A circle count moves in the opposite direction to
   the taluka share in the most affected districts.
3. The 2023 circle list has quality problems:
   - spelling variants of taluka names;
   - Madha appears both as a declared taluka and in the circle list;
   - Gevrai (a Beed taluka) is printed under Dharashiv;
   - "Akola" is printed for Akole taluka.

Circle counts are kept in `drought_validation_districts.csv` as **context only**
(`addl_revenue_circles_count_context_only`). They are never added to the taluka measure.

**The measure is not perfectly comparable across years:**
- **2023:** the main GR covers only 40 talukas, while 1,021 revenue circles were declared separately. So the taluka
  share captures only part of the 2023 declarations. Only 15 of 34 districts have a non-zero share, and many districts
  are tied at 0.
- **2026:** this is a Trigger-1 declaration (an earlier, rainfall-led stage), not a final severe/moderate declaration.
  It is very broad (265 of 355 talukas), and 19 of 34 districts have **every** taluka declared (share = 1). This
  ceiling limits how well districts can be told apart.
- **2018:** this is a final declaration after the Trigger-2 stage (the 180-taluka Trigger-2 GR of 23-10-2018 is in
  `data/raw` but was not transcribed or used). It gives the most informative spread: 26 of 34 districts have a
  non-zero share.

## 5–8. Continuous-index results (primary validation)

Spearman ρ between the fixed index and the declared taluka share, n = 34 districts in every row. p-values are two-sided.

| Year | Role | Measure | Spearman ρ | p | Pearson r | Districts with any declaration |
|---|---|---|---|---|---|---|
| **2018** | historical | declared share (severe + moderate) | **0.585** | 0.0003 | 0.541 | 26 |
| 2018 | secondary | severe-only share | 0.591 | 0.0002 | 0.570 | 21 |
| **2023** | historical | declared share (severe + moderate) | **0.450** | 0.008 | 0.440 | 15 |
| 2023 | secondary | severe-only share | 0.428 | 0.012 | 0.507 | 10 |
| 2018 + 2023 | additional | mean of the two shares (same unit and denominator) | 0.572 | 0.0004 | 0.566 | 27 |
| **2026** | **HOLDOUT** | declared share (Trigger-1) | **0.545** | 0.0009 | 0.503 | 32 |

- **2018:** moderate positive association. Districts with higher index values tended to have a larger share of talukas
  declared.
- **2023:** weaker but still positive association (ρ = 0.45). The main-GR taluka list covers only part of the
  declarations that year, and many districts are tied at zero.
- **2026 holdout:** positive association of similar strength to the historical years (ρ = 0.55), using the fixed index
  and classes without any change. This is the unseen-data check, and it shows **correspondence consistent with the
  historical results**. It is not stronger evidence than 2018, because of the ceiling effect in the Trigger-1
  declaration.
- **Context, not used anywhere in the index:** the RONI value for June–August 2026 is +1.36 (the July–September value
  was not yet available when the file was downloaded). IMD's district snapshot of 26-09-2026 shows Marathwada at −38%
  and Vidarbha at −26% for 1 June – 26 September 2026.
- **Small sample:** with only 34 districts, statistical power is low. The correlations are moderate (0.45–0.59), and
  the size of ρ matters more than the p-value. Pearson r is shown for reference only. The shares are bounded (0–1),
  have many ties and are not normally distributed, so Spearman is the primary statistic.

## 9. Low / Medium / High (secondary validation)

Group sizes are Low 4, Medium 20 and High 10 in every year (the fixed classification).

| Year | Mean share: Low / Medium / High | Median share: Low / Medium / High | Share of districts with any declaration: Low / Medium / High |
|---|---|---|---|
| 2018 | 0.05 / 0.39 / **0.66** | 0.00 / 0.37 / **0.73** | 25% / 75% / **100%** |
| 2023 | 0.00 / 0.10 / **0.20** | 0.00 / 0.00 / **0.13** | 0% / 45% / **60%** |
| 2018 + 2023 (mean share) | 0.03 / 0.25 / **0.43** | 0.00 / 0.21 / **0.41** | 25% / 80% / **100%** |
| **2026 holdout** | 0.39 / 0.70 / **0.99** | 0.28 / 0.84 / **1.00** | 75% / 95% / **100%** |

In every year, **observed declaration intensity increases from Low to Medium to High**. The Low group has only 4
districts, so its averages rest on very few values. This does not mean the groups "predict" drought. It shows that the
relative index groups are ordered in the same direction as declaration intensity.

## 10. Districts where the index and declarations disagree

Flag rule (for display only): the district's percentile rank on the index and its percentile rank on the declared share
differ by 0.5 or more. These are **not errors**. The possible reasons below are limited to what the project's data show.

| Year | Higher index, lower declaration | Lower index, higher declaration |
|---|---|---|
| 2018 | Latur (index 90.9; 1 of 10 talukas), Nanded (81.8; 3 of 16) | — |
| 2023 | Nanded (81.8; 0 of 16), Parbhani (84.0; 0 of 9) | Pune (37.3; 5 of 14), Nashik (36.8; 3 of 15) |
| 2026 | — | Nagpur (0.0, the lowest observed index; 14 of 14 talukas) |

What the project's data show about these districts:

- **Latur, Nanded and Parbhani:** in these years much of their declaration was made at **revenue-circle** level rather
  than whole talukas:
  - Latur: 42 extra circles in 2018 and 46 in 2023
  - Nanded: 14 in 2018 and 25 in 2023
  - Parbhani: 39 in 2023

  The taluka share does not capture these (section 4). The disagreement is therefore partly a difference in the
  **administrative unit** of declaration.
- **Pune and Nashik (2023):** both had talukas declared despite mid-range index values. Both also had many extra circles
  (35 and 47). Pune's rainfall series is unusual (`reports/rainfall_sensitivity_report.md`). No district-specific cause
  is claimed.
- **Nagpur (2026):** IMD's 2026 snapshot shows Nagpur district at **−33%** (Deficient) for 1 June – 26 September 2026,
  and Trigger-1 is mainly a current-season rainfall trigger. Nagpur's low index comes from its long-term profile: lower
  agricultural-worker share, higher literacy, and a weaker historical El Niño–rainfall link. A severe deficit in a
  single season can lead to declaration in a district that the index rates as relatively less vulnerable.

Other general reasons disagreement can occur:
- rainfall variation within a district that a district average misses;
- irrigation and cropping differences;
- the timing of decisions;
- non-climatic administrative factors.

## 11. Limitations

- **Small sample.** With 34 districts, power is low, and one or two districts can move ρ noticeably.
- **Declarations are administrative outcomes**, not measured drought damage or losses.
- **Measures are not identical across years:**
  - 2023 is only partly captured by talukas (most of that year's declaration was by revenue circle);
  - 2026 is a Trigger-1 stage with a ceiling effect;
  - only 2018 is a full final declaration with a good spread.
- **Only 2023 was an El Niño monsoon year** under the project's RONI rule; 2018 was not. In 2026, El Niño conditions
  were present in June–August, but the full-season classification was not yet available. So the validation tests
  general correspondence with drought declarations, not only El Niño-driven drought.
- **Different time frames.** The index describes long-term conditions (rainfall 1950–2024; Census 2011; Agriculture
  Census 2010-11), while declarations reflect one season.
- **Revenue circles** cannot be converted into a share without a verified district total of circles.
- **Mumbai City and Mumbai Suburban** are outside the index and are never listed in the GRs.

## 12. Statement

Across 2018, 2023 and the 2026 holdout, the fixed vulnerability index shows a **moderate positive association** with
the share of talukas declared drought-affected (Spearman ρ = 0.45–0.59). Declaration intensity is higher in the High
group than in the Medium and Low groups in every year. This is **consistent with** the index capturing relative drought
vulnerability.

The validation **does not establish causality**. It does not show that the index measures drought damage, and it does
not show that the index or its classes predict future droughts.
