# K-Means Classification of the Final Vulnerability Index

Script: `src/s17_kmeans_classification.py`. Settings: `config/project_decisions.yaml` → `kmeans_classification` (FIXED).
Tests: `tests/test_kmeans_classification.py`.

Outputs (`data/processed/`):

| File | Contents |
|---|---|
| `kmeans_vulnerability_classification.csv` | One row per district, sorted by index (highest first) for presentation only |
| `kmeans_diagnostics.csv` | K = 2, 3, 4 comparison |
| `kmeans_sensitivity.csv` | Group changes under the comparison versions of the index and under tertiles |
| `kmeans_secondary_pc_patterns.csv` | Secondary, exploratory district patterns (section 12) |

The final index (`vulnerability_index_scores.csv`) was not changed. No drought validation, 2026 data, maps or dashboard
were used or produced.

**Districts were grouped into Low, Medium and High vulnerability classes according to the relative magnitude of their
final composite vulnerability index.**

## 1. Why K-Means

The project needs Low / Medium / High classes for mapping. K-Means (the project's machine-learning step) chooses the
class boundaries from the data. It places them where the gaps between districts' index values are largest, instead of
using fixed cut-offs chosen by hand. In one dimension this means it groups districts with similar index values and
separates groups at natural breaks.

## 2. Why K = 3 is fixed

The project's output is three classes: Low, Medium and High. K = 2 and K = 4 were run **only** as diagnostics
(section 7) and do not change the primary K.

## 3. What was clustered

- **Only** `vulnerability_index_0_100` for the 34 in-scope districts.
- Not the six indicators, their z-scores, PCA scores, 2026 data or drought-declaration data.
- **No scaling** was applied. With a single variable already on a 0–100 scale, multiplying it by a constant would not
  change which districts end up together.
- Settings: sklearn `KMeans(n_clusters=3, random_state=2026, n_init=20)`.
- Re-running gives identical output files (checked, and tested).

## 4. Why cluster numbers were re-ordered

K-Means numbers its clusters arbitrarily (here Medium = cluster 0, High = 1, Low = 2). The script therefore:
1. computes each cluster's centroid (the mean index of its members);
2. assigns lowest centroid → **Low**, middle → **Medium**, highest → **High**.

This rule is deterministic and tested, including on a toy example where the raw cluster numbers are not in order.

## 5–6. Cluster sizes and centroids

| Group | Districts | Centroid (mean index) | Index range | Boundary with next group |
|---|---|---|---|---|
| Low Vulnerability | 4 | 13.8 | 0.0 – 25.6 | 29.8 |
| Medium Vulnerability | 20 | 45.9 | 32.6 – 62.7 | 64.1 |
| High Vulnerability | 10 | 82.4 | 65.9 – 100.0 | — |

In one dimension, each boundary is the midpoint between neighbouring centroids. The groups do not overlap.

- **High (10):** Beed 100.0, Jalna 91.8, Latur 90.9, Dharashiv 89.4, Parbhani 84.0, Nanded 81.8, Nandurbar 75.4,
  Ahilyanagar 75.2, Solapur 69.4, Hingoli 65.9
- **Medium (20):** Washim 62.7, Buldhana 61.2, Satara 58.6, Sangli 53.7, Dhule 53.1, Akola 51.9,
  Chhatrapati Sambhajinagar 49.1, Palghar 45.9, Ratnagiri 45.7, Kolhapur 45.2, Jalgaon 43.4, Amravati 42.6,
  Yavatmal 42.2, Sindhudurg 42.0, Gadchiroli 41.1, Pune 37.3, Nashik 36.8, Raigad 36.5, Chandrapur 35.3, Wardha 32.6
- **Low (4):** Bhandara 25.6, Gondia 18.7, Thane 10.9, Nagpur 0.0

The groups are unequal in size because K-Means follows the gaps in the data rather than making equal groups. The Low
group is small because the low end of the index is spread out, with large gaps between neighbouring districts:
Nagpur to Thane is 10.9 points, Thane to Gondia 7.8, and Bhandara to Wardha 7.0. So only four districts sit clearly
apart below the large middle block.

## 7. Silhouette score and K = 2 / 3 / 4 diagnostics

The silhouette score runs from −1 to 1; higher means districts sit closer to their own group than to the next one.

| K | Inertia (within-cluster sum of squares) | Silhouette | Sizes (low → high) | Centroids |
|---|---|---|---|---|
| 2 | 5946.5 | 0.594 | 21 / 13 | 37.6 / 77.4 |
| **3 (primary)** | **2868.9** | **0.587** | **4 / 20 / 10** | **13.8 / 45.9 / 82.4** |
| 4 | 1456.3 | 0.571 | 4 / 14 / 8 / 8 | 13.8 / 41.1 / 59.6 / 86.1 |

- A silhouette of 0.59 for K = 3 indicates **reasonably separated** groups (values above about 0.5 are usually read
  as a reasonable structure).
- K = 2 is only marginally higher (0.594 vs 0.587). This does not change the fixed K = 3.
- K = 4 splits the Medium group and is slightly less separated.

## 8. K-Means vs tertiles

As a simple non-machine-learning check, the 34 districts were split into thirds by index value (12 / 11 / 11).

- **25 of 34 districts (73.5%) are in the same class under both methods; 9 differ.**
- The 9 that differ are all Medium under K-Means:
  - one moves to the upper third: Washim
  - eight move to the lower third: Wardha, Gadchiroli, Chandrapur, Yavatmal, Nashik, Raigad, Pune and Sindhudurg
- The difference is structural. Tertiles force equal group sizes, whereas K-Means puts the boundary at the natural gaps.
  That is why its Low group is smaller and its Medium group larger.
- The High groups are almost the same (10 under K-Means vs 11 in the upper third).

Tertiles are a comparison only; the primary classification remains K-Means.

## 9. Sensitivity of the Low / Medium / High classes

Each comparison version of the index (from the index stage) was rescaled to 0–100 and classified with the same
procedure (K = 3, same seed, groups ordered by centroid).

| Comparison version (sensitivity only) | Spearman ρ with primary index | Districts changing group | % | Which |
|---|---|---|---|---|
| PCA \|loading\|, all 6 components | 0.995 | 1 | 2.9 | Wardha (Medium → Low) |
| Pune-excluded rainfall | 0.995 | 1 | 2.9 | Hingoli (High → Medium) |
| Hazard + social | 0.991 | 1 | 2.9 | Hingoli (High → Medium) |
| Equal weights | 0.993 | 2 | 5.9 | Wardha (Medium → Low), Hingoli (High → Medium) |
| OECD/JRC factor weights | 0.934 | 2 | 5.9 | Buldhana, Washim (Medium → High) |
| ONI v6 instead of RONI | 0.961 | 4 | 11.8 | Buldhana, Washim, Satara (Medium → High); Solapur (High → Medium) |

- **The classification is stable.** At most 4 of 34 districts (12%) change group, and usually 1 or 2.
- No district ever jumps two classes (Low ↔ High).
- The districts that change are the **boundary districts**, closest to the cut-offs of 29.8 and 64.1: Wardha (32.6),
  Hingoli (65.9), Washim (62.7) and Buldhana (61.2). Their class should be described as less certain.

## 10. Limitations

- **Small sample.** With 34 districts, one or two districts near a boundary can change class under reasonable
  alternative choices (section 9).
- **Relative classes.** Low / Medium / High are **relative to the 34 districts in this study**. "Low" means low compared
  with other Maharashtra districts on this index, **not safe** from drought. "High" does **not** mean drought is
  guaranteed, and "Medium" is not an "average risk" probability.
- **K-Means finds groups, not truth.** K-Means on one variable only finds natural breaks in the index values. It does
  not discover objectively "true" vulnerability categories, does not establish causality, and does not predict future
  drought outcomes.
- **Inherited limitations.** The classes carry every limitation of the index itself: exploratory PCA weights
  (KMO = 0.40), framework-defined directions, Pune rainfall and a 2011-era socioeconomic base (see
  `final_vulnerability_index_report.md`).
- **Not yet validated.** The classes have not yet been compared with drought declarations. That is the next stage (2018
  and 2023, then the 2026 holdout).

## 11. Statement of interpretation

These are **relative vulnerability groups** based on the final composite vulnerability index. They are not guaranteed
drought outcomes, not predictions of drought impact, and not causal findings.

## 12. SECONDARY / EXPLORATORY: district patterns from PC1–PC3 (not part of the primary result)

K-Means (K = 3, same seed) was also run on the primary PCA scores PC1–PC3 to see broad district **patterns**. These
are **not vulnerability classes** and are not labelled Low / Medium / High.

| Pattern | Districts | Mean PC1 / PC2 / PC3 | Members |
|---|---|---|---|
| A | 18 | +1.16 / −0.01 / −0.05 | Mostly the dryland interior: Beed, Jalna, Latur, Dharashiv, Parbhani, Nanded, Hingoli, Nandurbar, Dhule, Jalgaon, Buldhana, Washim, Yavatmal, Wardha, Chandrapur, Gadchiroli, Ahilyanagar, Solapur |
| B | 5 | −1.87 / +1.17 / −1.16 | Gondia, Bhandara, Kolhapur, Satara, Pune |
| C | 11 | −1.05 / −0.52 / +0.60 | Konkan (Thane, Palghar, Raigad, Ratnagiri, Sindhudurg), Nagpur, Nashik, Amravati, Akola, Sangli, Chhatrapati Sambhajinagar |

- The silhouette is **0.28**, a **weak** structure. The patterns are loose, and B in particular mixes very different
  districts (east Vidarbha rice districts with Pune and western Maharashtra).
- All 10 High-vulnerability districts are in Pattern A, but Pattern A also contains 8 Medium districts.
- This analysis is descriptive only and is **not used** for the vulnerability classification.
