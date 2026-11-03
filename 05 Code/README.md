# AI-Driven Vulnerability Index Mapping for Districts in Maharashtra to El Niño Droughts Using Socio-Economic and Climatic PCA

T.Y. Minor Project (K. J. Somaiya Institute of Technology, AI & DS, Group 12). **Working repository (temporary) — the final repository will be created later.**

**Study scope:** Maharashtra, district level (title unchanged, per project guide).

## Current status

| Stage | Status |
|---|---|
| 5-district Amravati Division prototype (Colab) | Done — prototype only (`Copy of intial_project.ipynb`, `data/prototype/`) |
| Data acquisition (verified official sources) | Done — `data/raw/source_manifest.csv` |
| Data engineering / feature construction | Done — `data/interim/`, `reports/data_quality_report.md` |
| Feature-selection audit | Done — `reports/feature_selection_report.md` |
| Methodological decisions | Fixed — `config/project_decisions.yaml` (geography B, 34 districts in scope, RONI, 1950-2024, Set A) |
| Primary PCA + leave-one-district-out stability | Done (exploratory) — `reports/pca_primary_report.md`, `reports/pca_stability_report.md` |
| Pune rainfall sensitivity + PCA-to-index method comparison (candidates only) | Done — `reports/rainfall_sensitivity_report.md`, `reports/pca_weighting_methods_report.md` |
| Final primary vulnerability index (PCA \|loading\| weights, K = 3, 0–100) | Done — `reports/final_vulnerability_index_report.md`, `data/processed/vulnerability_index_*.csv` |
| K-Means Low/Medium/High classification (K = 3 on the final index) | Done — `reports/kmeans_classification_report.md`, `data/processed/kmeans_*.csv` |
| Drought-declaration validation (2018, 2023, 2026 holdout) | Done — `reports/drought_validation_report.md`, `data/processed/drought_validation_*.csv` |
| Maharashtra district maps (groups, index, 2018/2023/2026 declarations) | Done — `reports/mapping_report.md`, `outputs/maps/*.png` |
| Streamlit dashboard (read-only presentation of the fixed outputs) | Done — `app.py`, `reports/dashboard_report.md` |

## Key files

- `config/project_decisions.yaml` — every methodological choice, its options, the active default and whether it is UNRESOLVED
- `data/interim/maharashtra_district_feature_table.csv` — one row per district, all candidate variables (primary: geography B, RONI)
- `data/interim/pca_input_primary.csv` — the six Set A variables, original and direction-aligned (34 districts)
- `data/processed/` — PCA variance, loadings, scores and leave-one-district-out results
- `data/interim/data_dictionary.csv` — source, formula, unit and missing-value rule for every feature
- `data/interim/drought_validation.csv` — drought-declaration shares 2018/2023/2026 (validation only; 2026 holdout)
- `data/interim/variants/` — all alternatives: geography A (35 districts, Census 2011) / B (36, current) × ENSO index RONI / ONI v6
- `reports/data_quality_report.md` — district count, sources, missingness, redundancy, anomalies, open decisions
- `data/raw/source_manifest.csv` — every raw file with URL, download date, SHA-256 and notes
- `data/manual/` — hand transcriptions (drought GR annexures, district name reference) with notes

## Data sources

IMD 0.25° gridded daily rainfall (Pai et al. 2014); NOAA CPC RONI and ONI (ERSST.v6); Census of India 2011 Primary Census Abstract and Village Directory; Agriculture Census 2010-11 Maharashtra State Report; Survey of India administrative boundaries (OVSF/1M/8); Government of Maharashtra drought GRs (2018, 2023, 2026). Details and URLs are in the manifest.

## Dashboard

The dashboard only reads the committed outputs in `data/processed/` and the Survey of India boundary ZIP, so it runs
from a fresh clone without re-running the pipeline or downloading the IMD rainfall files.

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

The deployed version is live at https://maharashtra-elnino-vulnerability.streamlit.app. Run locally, it opens at http://localhost:8501. It shows the district map (group or 0–100 index view), a district selector with the
relative vulnerability index, the six indicators and PCA weights, 2018 / 2023 / 2026-holdout drought-declaration shares,
the validation summary and a two-district comparison. It performs no modelling (see `reports/dashboard_report.md`).

## Reproduce

Requires Python 3.12 and poppler `pdftotext` (macOS `brew install poppler`; Ubuntu/Colab `apt-get install poppler-utils`).

```bash
pip install -r requirements.txt
python src/download_large_raw.py      # IMD rainfall NetCDF (1.9 GB, not stored in Git), hash-checked
python src/run_pipeline.py            # ~1 minute; writes data/interim/ and reports/
python src/s13_pca_primary.py         # primary PCA + stability (data/processed/)
python src/s14_rainfall_sensitivity.py  # flagged-rainfall sensitivity PCA (data/processed/sensitivity/)
python src/s15_index_methods.py       # candidate index weighting methods (data/processed/index_candidates/)
python src/s16_vulnerability_index.py # final primary vulnerability index (data/processed/vulnerability_index_*.csv)
python src/s17_kmeans_classification.py # K-Means Low/Medium/High groups (data/processed/kmeans_*.csv)
python src/s18_drought_validation.py  # validation against drought GRs (data/processed/drought_validation_*.csv)
python src/s19_maps.py                # district maps (outputs/maps/*.png)
python -m pytest tests -q             # integrity checks
```

Not stored in Git (size): the 76 IMD rainfall NetCDF files and the optional geoBoundaries zips (`python src/download_large_raw.py --optional`).

## Pipeline steps (`src/`)

`s01_crosswalk` district crosswalk (A/B) · `s02_census_pca` Census 2011 features · `s03_village_directory` land use and irrigation (documents the swapped irrigation column labels) · `s04_agcensus` landholdings · `s05_rainfall` IMD area-weighted district rainfall · `s06_enso` NOAA episode classification (verified against CPC tables) · `s07_climate_features` El Niño hazard features · `s08_validation` drought GRs · `s09_merge` master table · `s10_dictionary_report` dictionary and QA report · `s11_feature_selection` feature audit · `s12_pca_input` direction-aligned PCA input · `s13_pca_primary` PCA and stability · `s14_rainfall_sensitivity` flagged-rainfall sensitivity · `s15_index_methods` candidate PCA-to-index methods · `s16_vulnerability_index` final primary index · `s17_kmeans_classification` Low/Medium/High groups · `s18_drought_validation` validation against drought declarations · `s19_maps` district maps (s13–s19 run separately).
