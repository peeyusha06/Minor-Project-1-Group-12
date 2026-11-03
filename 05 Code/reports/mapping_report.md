# Mapping Report — Maharashtra District Maps

Script: `src/s19_maps.py`. Tests: `tests/test_maps.py`. Maps: `outputs/maps/`.

The maps only **display** fixed outputs. No index value, K-Means group or declaration share was recomputed or changed:
all processed CSV files and the boundary ZIP have the same checksums before and after this stage.

Three different things are mapped and should not be confused:

| Term | Meaning | Maps |
|---|---|---|
| **Vulnerability index** | The continuous 0–100 composite score (PCA-weighted sum of six direction-aligned indicators, rescaled across the 34 districts) | 2 |
| **Vulnerability group** | Low / Medium / High from K-Means (K = 3) on that index, ordered by centroid | 1, 6 |
| **Drought-declaration intensity** | The share of a district's talukas declared drought-affected in a Government of Maharashtra GR. This is an administrative outcome, not a measure of crop loss or rainfall, and was never used to build the index. | 3, 4, 5, 6 |

## 1. Boundary source

Survey of India, Administrative Boundary Database OVSF/1M/8 (Maharashtra), stored unchanged at
`data/raw/boundaries/survey_of_india/SOI_OVSF_1M_8_Maharashtra_upto_taluk.zip`. It was downloaded by the user from the
Survey of India portal and is recorded in `data/raw/source_manifest.csv`.

## 2. Boundary layer

`27/MAHARASHTRA_DISTRICT_BDY.shp`, read directly from the ZIP. The original file is not modified.

- **36 district polygons**, one per district, with unique `DIST_LGD` codes.
- **Palghar** is a separate polygon (LGD 681), distinct from Thane (517).
- **Mumbai City** (`MUMBAI`, 519) and **Mumbai Suburban** (518) are both present.
- **Geometry:** all 36 geometries are valid and non-empty (22 Polygon, 14 MultiPolygon), so no repair was needed.
- **Fields:** `DISTRICT` (upper-case name), `DIST_LGD` (district code), `STATE_LGD` (27).

## 3. Join key

`DIST_LGD` (as an integer) = `district_id`, the identifier used by every project table. The same code is also the Census
2011 district code for 35 districts, and LGD 681 for Palghar.

- **No name matching** is used for joins.
- Display names come from `data/manual/district_reference.csv`, joined on the same code. They are the current official
  names (e.g. Ahilyanagar, Dharashiv, Chhatrapati Sambhajinagar); the layer's upper-case `DISTRICT` field is not used.
- Every merge is checked as one-to-one (`validate="one_to_one"`).
- The script stops if any in-scope district lacks a value, if any value is duplicated, or if a Mumbai district receives
  a value.

## 4. CRS

The layer's native projection is used unchanged: Lambert Conformal Conic on WGS 84 (metres; standard parallels
12.47° N and 35.17° N, central meridian 80° E, origin 24° N). This is the Survey of India's national projection, so the
state is drawn without the east–west stretching of plain longitude/latitude. All six maps use the same projection,
extent style, figure style, boundary line (0.5 pt dark grey) and label style.

## 5. Mumbai City and Mumbai Suburban

- Both are drawn **grey with hatching** and labelled "Mumbai City & Mumbai Suburban (not in index)" with a leader line,
  because the two polygons are tiny at state scale.
- They have **no index value, no group and no declaration share** on any map (tested).
- Reason: the Village Directory and Agriculture Census report no agricultural or landholding data for them, so they
  are outside the 34-district index scope.

## 6. Map 1: vulnerability groups (`maharashtra_vulnerability_groups.png`)

- **Input:** `kmeans_vulnerability_classification.csv`, joined on `district_id`.
- **Colours:** ColorBrewer OrRd, 3 classes. It is an ordered light-to-dark palette that ColorBrewer rates as safe for
  colour-blind readers: Low = light, Medium = mid, High = dark red.
- **Counts:** the legend shows the group sizes, **4 Low / 20 Medium / 10 High**, unchanged and tested.
- **Labels:** all 34 in-scope districts are named.
- **Notes on the map:** K-Means (K = 3) on the final 0–100 index; groups relative to the 34 districts; not drought
  predictions; Survey of India source.

## 7. Map 2: vulnerability index (`maharashtra_vulnerability_index.png`)

- **Input:** `vulnerability_index_scores.csv`, joined on `district_id`.
- **Colours:** sequential YlOrRd scale fixed to 0–100. The minimum is 0 (Nagpur, the lowest observed) and the maximum
  is 100 (Beed, the highest observed), both tested.
- **Notes on the map:** the index is relative to the 34 districts.

## 8. Map 3: 2018 declarations (`maharashtra_drought_2018.png`)

- **Input:** `drought_validation_districts.csv`, year 2018. The measure is the declared taluka share (severe +
  moderate, GR 31-10-2018, 151 talukas) ÷ Census 2011 talukas, shown as a percentage.
- **Colours:** sequential Blues, 0–100%. This deliberately differs from the index colours, so declarations are not
  mistaken for vulnerability.
- **Notes on the map:** this is the government-declared taluka share, not a direct measure of crop loss or rainfall.

## 9. Map 4: 2023 declarations (`maharashtra_drought_2023.png`)

- **Design:** the same as 2018. The source is GR 31-10-2023 (40 talukas).
- **Notes on the map:** the map shows **only the main-order taluka declarations**. The 1,021 revenue circles listed
  separately (GR 10-11-2023) are not represented, because no district total of revenue circles exists to form a share.
  No revenue-circle denominator was invented.

## 10. Map 5: 2026 holdout (`maharashtra_drought_2026_holdout.png`)

- **Input:** `drought_validation_holdout_2026.csv`. Titled **"2026 Trigger-1 holdout"**, not "final drought
  declaration".
- **Notes on the map:**
  - Trigger-1 is an earlier, rainfall-led stage (GR 25-09-2026, 265 talukas);
  - 19 of 34 districts have 100% of talukas declared;
  - so the map has a ceiling effect and separates districts less well.

**Map 6** (`maharashtra_index_vs_2026.png`) shows the two maps side by side: the vulnerability groups on the left and
the 2026 Trigger-1 declared share on the right. There is no overlay and no dual axis. One colour bar is attached to both
panels so the two maps are drawn at the same size. The note records that the index and groups were fixed before 2026
was examined, and gives the Spearman ρ (0.55, n = 34, from `drought_validation_summary.csv`).

## 11. Geometry and join issues

**None.** Details:
- All 36 geometries are valid; no repair or simplification was applied.
- All 34 in-scope districts matched exactly one polygon; no polygon matched more than one record; no districts were
  dropped; the only unmatched polygons are Mumbai City and Mumbai Suburban, as intended.
- A cosmetic point: at 200 dpi a few labels sit close to district borders (e.g. Bhandara/Gondia, and Nandurbar's narrow
  neck). They remain legible. Long names are wrapped onto two lines (Chhatrapati Sambhajinagar).

**Known issue carried over from the data audit:**
- The SOI boundaries are the current (2025) administrative lines, while the socioeconomic data are from 2011. Small
  boundary changes since 2011 are possible (see `config/project_decisions.yaml`, `boundary_source.known_issues`).
- The SOI **sub-district** layer's Dhule code error does not affect these maps, which use only the district layer.

## 12. Output files

`outputs/maps/` (PNG, 200 dpi):

| File | Content |
|---|---|
| `maharashtra_vulnerability_groups.png` | Map 1: Low / Medium / High groups |
| `maharashtra_vulnerability_index.png` | Map 2: continuous 0–100 index |
| `maharashtra_drought_2018.png` | Map 3: 2018 declared taluka share |
| `maharashtra_drought_2023.png` | Map 4: 2023 declared taluka share (main order only) |
| `maharashtra_drought_2026_holdout.png` | Map 5: 2026 Trigger-1 holdout |
| `maharashtra_index_vs_2026.png` | Map 6: side-by-side groups vs 2026 |

**Dependency:** `matplotlib>=3.8` was added to `requirements.txt` (tested with 3.11.2). No other plotting library was
added.
