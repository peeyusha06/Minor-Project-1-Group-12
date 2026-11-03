# Dashboard Report

App: `app.py` (Streamlit). Theme: `.streamlit/config.toml` (light). Tests: `tests/test_dashboard.py`.
Launch: `streamlit run app.py`.

## 1. Objective

The dashboard is an interactive **presentation layer** for the finished project. It lets a user:
- see the Maharashtra vulnerability map;
- pick a district and read its relative vulnerability index, group, six indicators and PCA weights;
- see how the index compares with drought declarations in 2018, 2023 and the 2026 holdout.

**It performs no modelling.** It does not run PCA, K-Means, scaling or any drought calculation. It only reads the fixed
outputs, and a test confirms that the analytical CSV files are byte-identical after the app runs.

## 2. Files read

| File | Used for |
|---|---|
| `data/processed/vulnerability_index_scores.csv` | Index (0–100), raw score, aligned indicator values, z-scores |
| `data/processed/vulnerability_index_weights.csv` | The six fixed PCA weights, dimensions, sign multipliers |
| `data/processed/vulnerability_index_components.csv` | Checked as present (component information for the methodology) |
| `data/processed/kmeans_vulnerability_classification.csv` | Low / Medium / High groups |
| `data/processed/drought_validation_districts.csv` | 2018 and 2023 declared taluka shares per district |
| `data/processed/drought_validation_holdout_2026.csv` | 2026 Trigger-1 holdout share per district |
| `data/processed/drought_validation_summary.csv` | Spearman ρ and p-values |
| `data/raw/boundaries/survey_of_india/SOI_OVSF_1M_8_Maharashtra_upto_taluk.zip` | District polygons |

- The boundaries and joins come from **`map_table()` in `src/s19_maps.py`**, the same function that drew the report
  maps. It checks for 36 polygons, 34 in-scope matches and no values for Mumbai City or Mumbai Suburban.
- All joins use `district_id`; no name matching is used.
- If any required file is missing, the app shows a red error listing the missing file(s) and stops. It never
  fabricates values.

## 3. Fixed analytical outputs shown (unchanged)

| Output | Value |
|---|---|
| Index | 34 districts, 0–100 (Nagpur 0.0, Beed 100.0) |
| Groups | 4 Low / 20 Medium / 10 High (the count line on the page is computed from the classification file) |
| Weights | 0.168, 0.151, 0.183, 0.173, 0.161, 0.164 |
| Validation, Spearman ρ | 2018 = 0.585, 2023 = 0.450, 2026 holdout = 0.545 |

## 4. Dashboard sections

1. **Title and subtitle.**
2. **Map** with a view toggle: *Vulnerability group* (Low / Medium / High) or *Vulnerability index (0–100)*.
3. **District selector and card:** "Relative vulnerability index XX.X / 100" and the vulnerability group, with the note
   "Not a probability and not a predicted drought risk".
4. **Six underlying indicators** for the selected district. Columns: indicator, district value in natural units, unit,
   dimension, PCA weight, standardised value (z) and contribution (weight × z).
5. **Why the score looks this way:** a one-paragraph explanation, the six weights, and the limitation box.
6. **Drought validation for the district:** 2018, 2023 and "2026 Trigger-1 holdout", each as the percentage and count of
   talukas declared, with the required notes.
7. **Validation summary:** Spearman ρ, p-value and n for each year, with the "associated with" statement.
8. **Compare two districts:** a side-by-side table of index, group and the six indicators.
9. **Methodology** (collapsed by default): a one-line flow from raw data to validation, plus the scope (Maharashtra,
   34 districts, RONI, 1950–2024, baseline 1971–2020).

**Display-only conversions** (no new analysis):
- **Indicator values** are shown in their natural units by undoing the direction alignment with the fixed sign
  multipliers. For example, the ENSO slope is shown as the actual % change per °C, and literacy as % literate. The
  deficient frequency is shown as a percentage.
- **Contributions** (weight × z) are a breakdown of the district's stored raw score. The app checks that they add up to
  the stored `raw_vulnerability_score`.

## 5. District selection

- A dropdown of the 34 in-scope districts, sorted alphabetically (default: Beed).
- The selected district is outlined in dark blue on the map.
- Click-to-select on the map was not implemented. Matplotlib maps in Streamlit are static images, and click selection
  would need an extra mapping library. As the brief allows, a dropdown was chosen for reliability.

## 6. Map design

- The map uses the same drawing functions as `outputs/maps/`: Survey of India districts in their native Lambert
  projection, and ColorBrewer OrRd for the groups (Low light, Medium mid, High dark red).
- The continuous index uses YlOrRd with a 0–100 legend.
- Mumbai City and Mumbai Suburban are drawn grey and hatched, labelled "not in index", and never given a value.
- Drought-declaration figures use **blue**, to keep them visually separate from vulnerability.

## 7. Validation display

- The display reads the stored shares only; nothing is recalculated.
- It states that declared taluka share is a **validation indicator that was not used to build the index**.
- **2023** is labelled as main-order taluka declarations only. Separately listed revenue circles are excluded because
  there is no verified district total of revenue circles.
- **2026** is labelled "2026 Trigger-1 holdout", with the note that Trigger-1 is an earlier rainfall-led stage used as
  a holdout check.
- The summary wording uses **"associated with"**, never "predicted" or "caused".

## 8. Interpretation limits (shown in the app)

- The index is **relative** to the 34 in-scope districts: 0 = lowest observed, 100 = highest observed.
- It is an **exploratory composite index**, not a causal model, a probability or a drought forecast.
- Groups are relative magnitude classes from K-Means (K = 3) on the index.
- Declarations are administrative outcomes, not measured drought damage.

## Testing

`tests/test_dashboard.py` uses Streamlit's `AppTest` to run the real app headlessly. It checks that:
- the app starts without exceptions;
- for **Nagpur, Beed, Pune and Hingoli**, the card shows exactly the stored index, and the 2018, 2023 and 2026 figures
  match the validation files;
- the map-view toggle works;
- the loaded tables match the fixed files: 34 districts, 4/20/10 groups, Mumbai with no values, and the six weights;
- all analytical CSVs are unchanged after the run.

The app was also launched with `streamlit run app.py`, and the map, card, tables and validation section were checked
in a browser.
