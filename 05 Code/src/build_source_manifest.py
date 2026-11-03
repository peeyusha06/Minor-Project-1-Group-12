import csv, hashlib, os, glob

RAW = "/Volumes/D/sem 5/PBL/SEM 5/data/raw"
DATE = "2026-09-27"  # IST date of download (UTC 2026-09-26 evening)

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

rows = []
def add(name, source, url, geo, time, relpath, notes, status="DOWNLOADED", date=DATE):
    p = os.path.join(RAW, relpath)
    if status == "DOWNLOADED":
        assert os.path.exists(p), p
        size, digest = os.path.getsize(p), sha(p)
    else:
        size, digest = "", ""
    rows.append(dict(dataset_name=name, source=source, URL=url, download_date=date,
                     geographic_coverage=geo, temporal_coverage=time,
                     original_filename=os.path.basename(relpath), local_path="data/raw/" + relpath,
                     size_bytes=size, sha256=digest, status=status, notes=notes))

# ENSO
add("NOAA CPC Oceanic Nino Index (ONI), ERSST.v6",
    "NOAA Climate Prediction Center",
    "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    "Nino-3.4 region (5N-5S, 120W-170W); global index", "DJF 1950 - JJA 2026 (3-month overlapping seasons)",
    "enso/oni.ascii.txt",
    "Server Last-Modified 2026-09-03. Now ERSST.v6-based (1950 DJF = -1.32 vs -1.5 in v5). Matches data/prototype/NOAA_ONI_1998_2025.csv exactly for 1998-2025 (336/336 rows). Recent values may be revised for up to 2 months.")
add("NOAA CPC Relative Oceanic Nino Index (RONI)",
    "NOAA Climate Prediction Center",
    "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt",
    "Nino-3.4 minus tropical-mean (20S-20N) SST anomaly; global index", "DJF 1950 - JJA 2026",
    "enso/RONI.ascii.txt",
    "Official NOAA ENSO index since 1 Feb 2026 (NWS PIS 26-05). Same +/-0.5 C and 5-consecutive-overlapping-season rule as ONI.")
add("RONI information circular (May 2026)", "NOAA Climate Prediction Center",
    "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/pdf/roni-info-may-2026.pdf",
    "n/a", "n/a", "enso/roni-info-may-2026.pdf", "Definition and reclassification notes for RONI; citation source.")
add("CPC ONI v6 historical episode table page (HTML snapshot)", "NOAA Climate Prediction Center",
    "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/",
    "n/a", "1950-2026", "enso/cpc_oni_v6_episode_table_page.html",
    "Saved for the official episode definition text (threshold +/-0.5 C for >=5 consecutive overlapping seasons; centered 30-yr base periods updated every 5 yrs).")
add("CPC RONI page (HTML snapshot)", "NOAA Climate Prediction Center",
    "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/",
    "n/a", "1950-2026", "enso/cpc_roni_page.html", "Saved for provenance.")
add("CPC RONI adoption announcement (HTML snapshot)", "NOAA Climate Prediction Center",
    "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/announcement.php",
    "n/a", "Feb 2026", "enso/cpc_roni_announcement_page.html", "Saved for provenance.")

# Rainfall
for p in sorted(glob.glob(os.path.join(RAW, "rainfall/imd_gridded_0p25_netcdf/ind*_rfp25.nc"))):
    y = os.path.basename(p)[3:7]
    note = "Daily 0.25 x 0.25 deg gridded rainfall (mm), 135 lon x 129 lat grid (6.5-38.5N, 66.5-100E), _FillValue -999. Cite Pai et al. (2014) MAUSAM 65(1):1-18. Downloaded via POST form field RF25=%s." % y
    if y == "2025":
        note += " NOTE: the IMD page text still says data are available 1901-2024; the 2025 file is served and contains 365 complete days, but IMD does not state whether 2025 is final or provisional."
    add("IMD 0.25 deg gridded daily rainfall %s (NetCDF)" % y,
        "India Meteorological Department, Pune (Climate Research and Services)",
        "https://www.imdpune.gov.in/cmpg/Griddata/RF25.php (POST RF25=%s; page https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html)" % y,
        "All India land grid (covers all of Maharashtra)", "%s-01-01 to %s-12-31 daily" % (y, y),
        "rainfall/imd_gridded_0p25_netcdf/" + os.path.basename(p), note)

# Census
add("Census of India 2011 Primary Census Abstract (India, state/district/sub-district/town/ward)",
    "Office of the Registrar General & Census Commissioner, India",
    "NOT VERIFIED (file was downloaded by the user in Aug 2026; exact source URL not recorded). Copied unchanged from project root.",
    "All India; Maharashtra = State code 27, 35 districts (codes 497-531), 357 sub-districts", "Census reference date 1 March 2011",
    "census/2011-IndiaStateDistSbDistTwnWrd-0000.xlsx",
    "Content verified: MH total population 112,374,333; sub-districts sum exactly to state; no nulls in MH district rows. Each district has Total/Rural/Urban rows. No village rows. Thane includes the 8 talukas later split into Palghar (2014).",
    date="2026-08-18 (user download); copied 2026-09-27")
add("Census of India 2011 District Census Handbook - Village Directory, Maharashtra (state release 2700)",
    "Office of the Registrar General & Census Commissioner, India (NADA catalog)",
    "https://censusindia.gov.in/nada/index.php/catalog/830/download/36190",
    "Maharashtra, 43,665 villages in 33 districts (Mumbai City and Mumbai Suburban have no villages)", "Census 2011",
    "census/DH_2011_DCHB_Village_Release_2700.xlsx",
    "Contains village land use incl. Net Area Sown and irrigation by source. DATA QUALITY: column labels 'Total Unirrigated Land Area' and 'Area Irrigated by Source' are swapped - in 43,661 of 43,665 villages the sum of source-wise irrigated areas equals the column labelled 'Total Unirrigated'. 345 negative values in the other column. Attached to catalog 830 (Sindhudurg DCHB Part A) but covers the whole state.")

# Agriculture
add("Agriculture Census 2010-11 (Phase I) Maharashtra State Report",
    "Commissionerate of Agriculture, Government of Maharashtra (2014)",
    "https://krishi.maharashtra.gov.in/Site/Upload/Pdf/Publications/Argi.pdf",
    "Maharashtra, 33 districts (no Mumbai/Mumbai Suburban); tahsil-level Table 26", "Agriculture Census 2010-11 (with 2000-01 comparison)",
    "agriculture/agcensus/Agriculture_Census_2010-11_Maharashtra_State_Report_Argi.pdf",
    "Official. PDF tables (text-extractable) - needs table extraction. Number/area of holdings by size class (marginal <1 ha, small 1-2 ha, etc.). DATA QUALITY: Chandrapur 2010-11 row in Table 5 is nearly identical to Gondia and inconsistent with its 2000-01 row - verify before use. www. subdomain has a TLS certificate mismatch; the non-www URL works.")
for sc, desc in [("landuse", "District land use incl. net cropped area, gross cropped area (1000 ha)"),
                 ("sourcewise-irrigated-area", "District source-wise net/gross irrigated area (1000 ha)"),
                 ("operational-holdings", "District operational holdings by size class (1000 number / 1000 ha)"),
                 ("districts", "District lookup table incl. Census 2011 district codes")]:
    note = {"landuse": "MH: 36 districts listed; NET CROPPED AREA valid for 29-34 districts 1990-2017, none 2018-2020.",
            "sourcewise-irrigated-area": "MH: NET irrigated area valid only 1990-2002 (29-33 districts); essentially empty 2003-2020. NOT SUITABLE as a contemporary irrigation variable for Maharashtra.",
            "operational-holdings": "MH: census years 1990,1995,2000,2005,2010 only; 34 districts.",
            "districts": "Includes 'Indian census District Code 2011' (Palghar = -1)."}[sc]
    add("ICRISAT District Level Database (unapportioned) - %s" % sc, "ICRISAT / Tata-Cornell Institute (CC BY 4.0)",
        "http://data.icrisat.org/dldAPI/unapportioned/%s" % sc, "20 Indian states incl. Maharashtra (2015-16 district boundaries)",
        "1990-2020 (varies by variable)", "agriculture/icrisat_dld/icrisat_dld_unapportioned_%s.json" % sc,
        desc + ". JSON from the public API used by the DLD web tool (http://data.icrisat.org/dld/). " + note)
add("ICRISAT DLD 'About' page (HTML snapshot)", "ICRISAT", "http://data.icrisat.org/dld/src/about-dld.html",
    "n/a", "n/a", "agriculture/icrisat_dld/icrisat_dld_about_page.html", "Licence (CC BY 4.0), boundary conventions, disclaimer.")

# Boundaries
for e in ["shp", "shx", "dbf", "prj"]:
    add("DataMeet Census 2011 district boundaries (%s)" % e, "DataMeet community (CC BY 2.5 India per Districts/README)",
        "https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.%s" % e,
        "All India, 641 districts; Maharashtra 35 (ST_CEN_CD 27)", "Census 2011 boundaries",
        "boundaries/datameet_census2011_districts/2011_Dist.%s" % e,
        "EPSG:4326. Field 'censuscode' = Census 2011 district code (497-531 for MH) - joins 1:1 to the PCA file. Derived from taluk boundaries (GeoCommons/Bhuvan) + Census Administrative Atlas; not an official Survey of India product. No Palghar polygon.")
add("DataMeet Districts README", "DataMeet", "https://raw.githubusercontent.com/datameet/maps/master/Districts/README.md",
    "n/a", "n/a", "boundaries/datameet_census2011_districts/README_Districts.md", "Source and licence statement.")
for lvl, desc in [("ADM2", "current districts (boundaryYearRepresented 2021); MH 36 incl. Palghar"),
                  ("ADM3", "sub-districts (boundaryYearRepresented 2018); MH 357")]:
    add("geoBoundaries India %s" % lvl, "geoBoundaries (William & Mary geoLab); source: Pathways Data Pvt. Ltd., lgdirectory.gov.in; ODbL 1.0",
        "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IND/%s/geoBoundaries-IND-%s-all.zip" % (lvl, lvl),
        "All India; " + desc, "see description", "boundaries/geoboundaries/geoBoundaries-IND-%s-all.zip" % lvl,
        "No Census/LGD codes in attributes (shapeName, shapeID only) - name-based crosswalk required. Secondary source; use only if the Survey of India product cannot be obtained.")
    add("geoBoundaries India %s API metadata" % lvl, "geoBoundaries", "https://www.geoboundaries.org/api/current/gbOpen/IND/%s/" % lvl,
        "n/a", "n/a", "boundaries/geoboundaries/geoBoundaries-IND-%s-metadata.json" % lvl, "Metadata snapshot.")
add("Survey of India Administrative Boundary Database - Maharashtra up to Taluk level with HQ (OVSF/1M/8)",
    "Survey of India (official), Onlinemaps Portal (downloaded manually by the user; CAPTCHA-protected)",
    "https://onlinemaps.surveyofindia.gov.in/Digital_Product_Show.aspx",
    "Maharashtra: 36 districts (incl. Palghar), 359 sub-districts, 1:1M", "Current boundaries; shapefiles written 2025-12-12 (per .shp.xml geoprocessing history)",
    "boundaries/survey_of_india/SOI_OVSF_1M_8_Maharashtra_upto_taluk.zip",
    "Copied unchanged from project root file 'Survey OF India - OVSF:1M:8 MH.zip'. Layers: DISTRICT_BDY (DIST_LGD = Census 2011 district code for 35 districts; Palghar = 681), SUBDISTRICT_BDY (SUBDIS_LGD = Census 2011 sub-district code for all 355 Census talukas; extra units = Mumbai City + Andheri/Kurla/Borivali). CRS: LCC WGS84. ANOMALY: Dhule's 4 sub-districts carry DIST_LGD 598 instead of 498. Sub-district DISTRICT names are in a legacy font encoding (e.g. 'L>T@R'); use codes, not names.",
    date="2026-09-27 (user download)")

# Validation
add("Maharashtra GR: drought declared in 265 talukas (Trigger-1), Kharif 2026",
    "Government of Maharashtra, Relief & Rehabilitation Department (GR No. सवमती-2026/प्र.क्र.82/मदत-2, dated 25 Sep 2026, signed 26 Sep 2026; code 202609261117494941)",
    "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/Marathi/202609261117494941.pdf",
    "Maharashtra, taluka list by district (Annexure-1)", "Kharif 2026",
    "validation/GR_202609261117494941_drought_265_talukas_kharif2026.pdf",
    "Marathi, text-based PDF (Word-generated); annexure lists district, taluka names and counts. Some glyphs mis-extract - manual verification needed to map talukas to Census sub-district codes. HOLDOUT ONLY - not for training.")
add("IMD district rainfall distribution (cumulative 1 Jun - 26 Sep 2026) snapshot",
    "India Meteorological Department, Hydromet Division, New Delhi",
    "https://mausam.imd.gov.in/Rainfall/DISTRICT_RAINFALL_DISTRIBUTION_COUNTRY_INDIA_cd.pdf",
    "All India districts incl. Maharashtra", "Day 26-09-2026 and season 01-06-2026 to 26-09-2026",
    "validation/IMD_DISTRICT_RAINFALL_DISTRIBUTION_snapshot_2026-09-26_period_2026-06-01_to_2026-09-26.pdf",
    "The URL is overwritten daily; this is a dated snapshot. Real-time (provisional) station-based district values. HOLDOUT/validation only.")
add("Maharashtra GR: drought declared in 151 talukas, Kharif 2018",
    "Government of Maharashtra, Revenue and Forest Department (GR No. एससीवाय-2018/प्र.क्र.89/म-7, dated 31 Oct 2018; code 201810311722349219)",
    "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/Marathi/201810311722349219.pdf",
    "Maharashtra, taluka list by district", "Kharif 2018",
    "validation/GR_201810311722349219_drought_151_talukas_kharif2018.pdf",
    "Marathi PDF, 5 pages. Content verified: title and date confirmed by text extraction. Matches news reports of 151 talukas/26 districts. HOLDOUT ONLY - not for training.")
add("Maharashtra GR: drought-like conditions in 180 talukas, Trigger-2, Kharif 2018-19",
    "Government of Maharashtra, Revenue and Forest Department (code 201810231643431719, dated 23 Oct 2018)",
    "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/Marathi/201810231643431719.pdf",
    "Maharashtra, taluka list", "Kharif 2018-19",
    "validation/GR_201810231643431719_drought_180_talukas_trigger2_2018-19.pdf",
    "Marathi PDF, 9 pages. Precedes and is superseded/complemented by the 151-taluka GR above - relationship between the 180 and 151 lists not yet reconciled. HOLDOUT ONLY.")
add("Maharashtra GR: additional 268 revenue circles declared drought-like, 2018",
    "Government of Maharashtra, Revenue and Forest Department (code 201811061721013119, dated 06 Nov 2018)",
    "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/Marathi/201811061721013119.pdf",
    "Maharashtra, revenue-circle list, beyond the 151 declared talukas", "2018",
    "validation/GR_201811061721013119_drought_268_revenue_circles_addl_2018.pdf",
    "Marathi PDF, 6 pages. Sub-taluka (revenue circle) level addition to the 151-taluka declaration. HOLDOUT ONLY.")
add("Maharashtra GR: drought declared in 40 talukas, Kharif 2023",
    "Government of Maharashtra, Revenue and Forest Department (GR No. एससीवाय-2023/प्र.क्र.37/म-7, dated 31 Oct 2023; code 202310311545053419)",
    "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/Marathi/202310311545053419.pdf",
    "Maharashtra, taluka list by district", "Kharif 2023",
    "validation/GR_202310311545053419_drought_40_talukas_kharif2023.pdf",
    "Marathi PDF. Content verified: this is exactly reference #4 cited in the 2026 drought GR (एससीवाय-2023/प्र.क्र.37/म-7, 31 Oct 2023). HOLDOUT ONLY - not for training.")
add("Maharashtra GR: additional 1021 revenue circles declared drought-like, 2023",
    "Government of Maharashtra, Revenue and Forest Department (code 202311101718225419, dated 10 Nov 2023)",
    "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/Marathi/202311101718225419.pdf",
    "Maharashtra, revenue-circle list, beyond the 40 declared talukas", "2023",
    "validation/GR_202311101718225419_drought_1021_revenue_circles_addl_2023.pdf",
    "Marathi PDF, 33 pages. Sub-taluka (revenue circle) level addition to the 40-taluka declaration. HOLDOUT ONLY.")

with open(os.path.join(RAW, "source_manifest.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(len(rows), "rows written")
