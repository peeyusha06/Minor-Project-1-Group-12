# Minor Project 1, Group 12

**AI-Driven Vulnerability Index Mapping for Districts in Maharashtra to El Niño Droughts Using Socio-Economic and Climatic PCA**

Project Based Learning, Minor Project 1, T.Y. B.Tech (Semester V), Academic Year 2026-27
Department of Artificial Intelligence and Data Science, K. J. Somaiya Institute of Technology, Sion, Mumbai

| Roll No. | Name |
|---|---|
| 34 | Tanishq Mewada |
| 47 | Saad Patel |
| 48 | Peeyusha Patki |

**Guide:** Prof. Pankaj Deshmukh

**Live dashboard:** https://maharashtra-elnino-vulnerability.streamlit.app

## Contents

| Folder | What it contains |
|---|---|
| [01 One Page Report](01%20One%20Page%20Report) | One page project report (DOCX and PDF) |
| [02 Logbook](02%20Logbook) | Scanned copy of the project logbook |
| [03 Report](03%20Report) | Full project report (DOCX and PDF) |
| [04 PPT](04%20PPT) | Final presentation (PPTX, with a PDF copy) |
| [05 Code](05%20Code) | Complete code with the datasets (see below) |
| [06 Research Paper](06%20Research%20Paper) | Research paper in IEEE format (DOCX and PDF) |
| [07 Poster](07%20Poster) | Project poster (PPTX and PDF) |

`streamlit_app.py`, `requirements.txt` and `.streamlit/` at the top level only start the online dashboard on Streamlit Community Cloud. The dashboard code is `05 Code/app.py`. A scheduled GitHub Action (`.github/workflows/keep-streamlit-awake.yml`) opens the dashboard every 6 hours so that it does not go to sleep.

## Code and datasets (05 Code)

- `src/`: the analysis pipeline, steps s01 to s19, run in order by `src/run_pipeline.py`
- `app.py`: the Streamlit dashboard
- `data/raw/`: the original downloaded datasets, unchanged; `data/raw/source_manifest.csv` lists the source URL, download date and SHA-256 checksum of every file
- `data/interim/`, `data/processed/`: intermediate and final tables (index, groups, validation)
- `outputs/maps/`: district maps; `reports/`: a report for each pipeline stage
- `config/project_decisions.yaml`: every methodological choice with its reason
- `tests/`: pytest tests
- `report/build/`, `paper/build/`: scripts that generate the report, poster and paper figures

To run:

```
cd "05 Code"
pip install -r requirements.txt
python src/download_large_raw.py      # downloads the IMD rainfall files (see below)
python src/run_pipeline.py
streamlit run app.py
```

## Raw data links

All datasets are included in `05 Code/data/raw/` except the IMD gridded rainfall, which is about 1.8 GB and too large for GitHub.

| Dataset | Source and link |
|---|---|
| IMD 0.25° gridded daily rainfall, 1950 to 2025 (**not included**, download from the link) | India Meteorological Department, Pune: https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html (file list and checksums in `05 Code/data/raw/rainfall/imd_gridded_0p25_netcdf/README.md`) |
| Relative Oceanic Niño Index (RONI) | NOAA Climate Prediction Center: https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt |
| Oceanic Niño Index (ONI) | NOAA Climate Prediction Center: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt |
| Census 2011 Primary Census Abstract | Office of the Registrar General and Census Commissioner, India: https://censusindia.gov.in |
| Census 2011 District Census Handbook, Village Directory, Maharashtra | https://censusindia.gov.in/nada/index.php/catalog/830 |
| Agriculture Census 2010-11, Maharashtra State Report | Commissionerate of Agriculture, Maharashtra: https://krishi.maharashtra.gov.in/Site/Upload/Pdf/Publications/Argi.pdf |
| ICRISAT District Level Database | http://data.icrisat.org/dld/src/about-dld.html |
| Survey of India administrative boundaries, Maharashtra (OVSF/1M/8) | https://onlinemaps.surveyofindia.gov.in/Digital_Product_Show.aspx |
| DataMeet Census 2011 district boundaries | https://github.com/datameet/maps/tree/master/Districts/Census_2011 |
| geoBoundaries India ADM2 and ADM3 | https://www.geoboundaries.org (release 9469f09 on GitHub: https://github.com/wmgeolab/geoBoundaries) |
| Drought declarations (GRs) 2018, 2023, 2026 | Government of Maharashtra GR portal: https://gr.maharashtra.gov.in (exact GR links in `source_manifest.csv`) |
| IMD district rainfall distribution, 2026 | https://mausam.imd.gov.in/Rainfall/DISTRICT_RAINFALL_DISTRIBUTION_COUNTRY_INDIA_cd.pdf |
