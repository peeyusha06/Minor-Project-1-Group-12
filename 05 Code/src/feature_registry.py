"""Single registry of every column in the master table and the key interim tables.

Used to (1) build data/interim/data_dictionary.csv and (2) test that no undocumented column
reaches the master table. role: identifier | pca_candidate | context | validation.
"""
from __future__ import annotations

PCA_F = "data/raw/census/2011-IndiaStateDistSbDistTwnWrd-0000.xlsx (sheet Data)"
VD_F = "data/raw/census/DH_2011_DCHB_Village_Release_2700.xlsx (sheet Village_Data_2700)"
AGC_F = "data/raw/agriculture/agcensus/Agriculture_Census_2010-11_Maharashtra_State_Report_Argi.pdf (Table 2; Table 26 for Palghar)"
IMD_F = "data/raw/rainfall/imd_gridded_0p25_netcdf/ind{1950..2024}_rfp25.nc (primary; the 2025 file is kept for sensitivity only)"
ENSO_F = "data/raw/enso/RONI.ascii.txt or data/raw/enso/oni.ascii.txt (per enso_index)"
BND_F = "data/raw/boundaries/survey_of_india/SOI_OVSF_1M_8_Maharashtra_upto_taluk.zip (active boundary source)"
PCA_S, VD_S, AGC_S = "Census of India 2011 PCA", "Census of India 2011 Village Directory", "Agriculture Census 2010-11 (Maharashtra report)"
IMD_S, ENSO_S = "IMD 0.25 deg gridded daily rainfall (Pai et al. 2014)", "NOAA CPC RONI / ONI ERSST.v6"
NO_IMPUTE = "no imputation; NaN if the source has no value"
AGRI_MISSING = "NaN for Mumbai City/Suburban (no villages / no holdings in source); no imputation"
RAIN_NOTE = "hazard features use the configured baseline, study period 1950-2024 and deficient threshold"

REG: list[dict] = []


def add(feature, group, description, source, source_file, year, level, numerator, denominator, formula, unit,
        missing=NO_IMPUTE, notes="", role="pca_candidate", table="maharashtra_district_feature_table.csv"):
    REG.append(dict(feature=feature, group=group, description=description, source=source, source_file=source_file,
                    year=year, geographic_level=level, numerator=numerator, denominator=denominator, formula=formula,
                    unit=unit, missing_value_rule=missing, notes=notes, role=role, table=table))


# ---------------- A. Geography ----------------
G = "A. Geography"
for f, d in [("district_id", "District key: Census 2011 district code (geography A) or LGD code (geography B; Palghar = 681)"),
             ("geography_version", "A = Census 2011 (35 districts), B = current (36 districts)"),
             ("census_2011_district_code", "Census 2011 district code (Palghar -> parent 517)"),
             ("census_2011_district_name", "District name as printed in the Census 2011 PCA"),
             ("current_district_name", "Current official district name"),
             ("marathi_name", "District name in Marathi"),
             ("district_boundary_id", "Boundary polygon identifier in the active boundary source")]:
    add(f, G, d, "project crosswalk", "data/interim/district_crosswalk.csv", "-", "district", "", "", "", "-",
        missing="never missing", role="identifier")
add("in_index_scope", G, "True if the district is inside the PCA/index scope (config: exclude_mumbai_from_index)", "project config",
    "config/project_decisions.yaml", "-", "district", "", "", "district not in excluded Mumbai set", "boolean", missing="never missing", role="identifier")
add("agri_data_available", G, "True if Village Directory and Agriculture Census data exist for the district", "derived",
    "-", "-", "district", "", "", "", "boolean", missing="never missing", role="identifier")
add("district_area_km2", G, "District polygon area (Albers equal-area)", "Survey of India", BND_F, "boundaries 2025", "district", "", "", "polygon area", "km2", role="context")

# ---------------- B. ENSO exposure ----------------
G = "B. ENSO exposure"
add("enso_index", G, "ENSO index used for this feature set (never mixed)", ENSO_S, ENSO_F, "1950-2024", "-", "", "", "", "-", role="identifier")
add("enso_n_study_years", G, "Number of study years with monsoon data (|T|)", "derived", IMD_F, "1950-2024", "district", "", "", "|T|", "years", role="context")
add("enso_n_elnino_years", G, "Number of El Nino monsoon years (|E|)", ENSO_S, ENSO_F, "1950-2024", "district", "", "", "|E|", "years", role="context",
    notes="episode rule: NOAA CPC; monsoon-year rule: config enso_monsoon_year_rule")
add("enso_elnino_years", G, "El Nino monsoon years used (E)", ENSO_S, ENSO_F, "1950-2024", "district", "", "", "sorted list", "years", role="context")
add("enso_rain_pearson_r", G, "Correlation between the JJA/JAS-mean ENSO index and district monsoon departure", f"{IMD_S}; {ENSO_S}",
    f"{IMD_F}; {ENSO_F}", "1950-2024", "district", "", "", "pearson(I_y, D_y) over T", "r", notes="negative = El Nino dries the district; " + RAIN_NOTE)
add("enso_rain_pearson_p", G, "Two-sided p-value of enso_rain_pearson_r", "derived", "-", "1950-2024", "district", "", "", "", "p", role="context")
add("enso_rain_spearman_rho", G, "Rank correlation between ENSO index and monsoon departure", f"{IMD_S}; {ENSO_S}", f"{IMD_F}; {ENSO_F}",
    "1950-2024", "district", "", "", "spearman(I_y, D_y) over T", "rho", notes="robust alternative to pearson_r (redundant with it)")
add("enso_rain_slope_pct_per_degC", G, "Change in monsoon departure per 1 degC of the ENSO index", f"{IMD_S}; {ENSO_S}", f"{IMD_F}; {ENSO_F}",
    "1950-2024", "district", "D_y", "I_y", "OLS slope of D_y on I_y over T", "% per degC", notes="negative = drier under El Nino")

# ---------------- C. Rainfall hazard ----------------
G = "C. Rainfall hazard"
add("rain_baseline_monsoon_mm", G, "District mean June-September rainfall over the baseline period", IMD_S, IMD_F, "baseline 1971-2020",
    "district", "", "", "mean(monsoon_mm over baseline years)", "mm", role="context")
add("rain_monsoon_cv_pct", G, "Coefficient of variation of June-September rainfall", IMD_S, IMD_F, "1950-2024", "district",
    "std(monsoon_mm)", "mean(monsoon_mm)", "std / mean * 100 over T", "%")
add("rain_en_mean_deficit_pct", G, "Mean monsoon deficit in El Nino years (positive = drier than baseline)", f"{IMD_S}; {ENSO_S}",
    f"{IMD_F}; {ENSO_F}", "El Nino years 1950-2024", "district", "", "", "mean over E of -(monsoon - baseline)/baseline*100", "%", notes=RAIN_NOTE)
add("rain_en_max_deficit_pct", G, "Largest monsoon deficit in any El Nino year", f"{IMD_S}; {ENSO_S}", f"{IMD_F}; {ENSO_F}",
    "El Nino years 1950-2024", "district", "", "", "max over E of -D_y", "%", notes=RAIN_NOTE)
add("rain_en_deficient_frequency", G, "Share of El Nino years with a deficient monsoon (IMD: departure <= -20%)", f"{IMD_S}; {ENSO_S}",
    f"{IMD_F}; {ENSO_F}", "El Nino years 1950-2024", "district", "El Nino years with D_y <= -20 (unrounded departure)", "El Nino years",
    "count / |E|", "fraction 0-1", notes="threshold from config deficient_monsoon_threshold")
add("rain_en_mean_spi", G, "Mean monsoon SPI in El Nino years (negative = drier)", f"{IMD_S}; {ENSO_S}", f"{IMD_F}; {ENSO_F}",
    "El Nino years 1950-2024", "district", "", "", "mean over E of SPI_y (gamma fit on baseline years)", "z", notes="closely related to rain_en_mean_deficit_pct")
add("rain_nonen_mean_deficit_pct", G, "Mean monsoon deficit in non-El-Nino years", IMD_S, f"{IMD_F}; {ENSO_F}", "1950-2024", "district",
    "", "", "mean over N of -D_y", "%", role="context")
add("rain_nonen_deficient_frequency", G, "Share of non-El-Nino years with a deficient monsoon", IMD_S, f"{IMD_F}; {ENSO_F}", "1950-2024",
    "district", "", "", "count / |N|", "fraction 0-1", role="context")
add("rain_en_minus_nonen_deficit_pct", G, "Extra monsoon deficit in El Nino years relative to other years", f"{IMD_S}; {ENSO_S}",
    f"{IMD_F}; {ENSO_F}", "1950-2024", "district", "", "", "en_mean_deficit - nonen_mean_deficit", "% points")
add("rain_en_minus_nonen_deficient_frequency", G, "Extra frequency of deficient monsoons in El Nino years", f"{IMD_S}; {ENSO_S}",
    f"{IMD_F}; {ENSO_F}", "1950-2024", "district", "", "", "en_deficient_frequency - nonen_deficient_frequency", "fraction")

# ---------------- D. Socioeconomic sensitivity ----------------
G = "D. Socioeconomic sensitivity"
add("soc_total_population", G, "Total population", PCA_S, PCA_F, "2011", "district", "", "", "TOT_P (TRU=Total)", "persons", role="context")
add("soc_rural_population_share_pct", G, "Rural share of population", PCA_S, PCA_F, "2011", "district", "TOT_P (TRU=Rural)", "TOT_P (TRU=Total)", "rural / total * 100", "%")
add("soc_literacy_rate_7plus_pct", G, "Literacy rate, population aged 7+", PCA_S, PCA_F, "2011", "district", "P_LIT", "TOT_P - P_06",
    "P_LIT / (TOT_P - P_06) * 100", "%", notes="adaptive capacity: higher = less vulnerable")
add("soc_work_participation_rate_pct", G, "Workers as share of population", PCA_S, PCA_F, "2011", "district", "TOT_WORK_P", "TOT_P",
    "TOT_WORK_P / TOT_P * 100", "%", notes="exactly 100 - soc_non_worker_share_pct (redundant pair)")
add("soc_non_worker_share_pct", G, "Non-workers as share of population", PCA_S, PCA_F, "2011", "district", "NON_WORK_P", "TOT_P",
    "NON_WORK_P / TOT_P * 100", "%", notes="exactly 100 - work participation rate (redundant pair)")
add("soc_agri_worker_share_of_workers_pct", G, "Cultivators + agricultural labourers (main + marginal) as share of workers", PCA_S, PCA_F,
    "2011", "district", "MAIN_CL_P + MARG_CL_P + MAIN_AL_P + MARG_AL_P", "TOT_WORK_P", "numerator / TOT_WORK_P * 100", "%",
    notes="config agricultural_worker_denominator = workers (active); same formula as prototype")
add("soc_agri_worker_share_of_population_pct", G, "Agricultural workers as share of total population", PCA_S, PCA_F, "2011", "district",
    "MAIN_CL_P + MARG_CL_P + MAIN_AL_P + MARG_AL_P", "TOT_P", "numerator / TOT_P * 100", "%", notes="alternative denominator (config)")
add("soc_cultivator_share_of_workers_pct", G, "Cultivators (main + marginal) as share of workers", PCA_S, PCA_F, "2011", "district",
    "MAIN_CL_P + MARG_CL_P", "TOT_WORK_P", "numerator / TOT_WORK_P * 100", "%", notes="component of agri worker share")
add("soc_agri_labourer_share_of_workers_pct", G, "Agricultural labourers (main + marginal) as share of workers", PCA_S, PCA_F, "2011",
    "district", "MAIN_AL_P + MARG_AL_P", "TOT_WORK_P", "numerator / TOT_WORK_P * 100", "%", notes="component of agri worker share; landless labour")
add("soc_marginal_worker_share_of_workers_pct", G, "Marginal workers (< 6 months work) as share of all workers", PCA_S, PCA_F, "2011",
    "district", "MARGWORK_P", "TOT_WORK_P", "MARGWORK_P / TOT_WORK_P * 100", "%",
    notes="config marginal_worker_denominator = workers (active). CORRECTS the prototype, which divided by TOT_P but called it a worker share")
add("soc_marginal_workers_per_population_pct", G, "Marginal workers as share of total population (prototype definition)", PCA_S, PCA_F,
    "2011", "district", "MARGWORK_P", "TOT_P", "MARGWORK_P / TOT_P * 100", "%", notes="alternative denominator kept for comparison with the prototype")
add("soc_sc_share_pct", G, "Scheduled Caste share of population", PCA_S, PCA_F, "2011", "district", "P_SC", "TOT_P", "P_SC / TOT_P * 100", "%")
add("soc_st_share_pct", G, "Scheduled Tribe share of population", PCA_S, PCA_F, "2011", "district", "P_ST", "TOT_P", "P_ST / TOT_P * 100", "%")

# ---------------- E. Agricultural exposure ----------------
G = "E. Agricultural exposure"
add("agri_n_villages", G, "Number of villages in the Village Directory", VD_S, VD_F, "2011", "village -> district", "", "", "count", "villages",
    missing=AGRI_MISSING, role="context")
add("agri_net_area_sown_ha", G, "Net area sown", VD_S, VD_F, "2011", "village -> district", "", "", "sum of 'Net Area Sown (in Hectares)'", "ha",
    missing=AGRI_MISSING, role="context")
add("agri_cropped_land_share_pct", G, "Net area sown as share of total village geographical area", VD_S, VD_F, "2011", "village -> district",
    "Net Area Sown", "Total Geographical Area (villages only)", "NAS / geographical area * 100", "%", missing=AGRI_MISSING,
    notes="denominator excludes town area (villages only)")
add("agri_forest_share_pct", G, "Forest area as share of village geographical area", VD_S, VD_F, "2011", "village -> district",
    "Forest Area", "Total Geographical Area", "forest / area * 100", "%", missing=AGRI_MISSING, role="context")
add("agri_fallow_share_pct", G, "Current + other fallows as share of village geographical area", VD_S, VD_F, "2011", "village -> district",
    "Current Fallows + Fallows other than current", "Total Geographical Area", "fallow / area * 100", "%", missing=AGRI_MISSING, role="context")

# ---------------- F. Irrigation / rainfed exposure ----------------
G = "F. Irrigation / rainfed exposure"
add("irr_irrigated_share_of_cropped_land_pct", G, "Irrigated area as share of net area sown", VD_S, VD_F, "2011", "village -> district",
    "raw column labelled 'Total Unirrigated Land Area' (= irrigated; label swap)", "Net Area Sown", "irrigated / NAS * 100", "%",
    missing=AGRI_MISSING, notes="label swap documented in config village_directory_irrigation_labels; adaptive capacity")
add("irr_rainfed_share_of_cropped_land_pct", G, "Unirrigated (rainfed) area as share of net area sown", VD_S, VD_F, "2011",
    "village -> district", "raw column labelled 'Area Irrigated by Source' (= unirrigated; label swap)", "Net Area Sown",
    "unirrigated / NAS * 100", "%", missing=AGRI_MISSING, notes="= 100 - irrigated share (perfectly redundant pair; keep one for PCA)")
add("irr_well_share_of_irrigated_pct", G, "Wells/tube wells share of source-wise irrigated area", VD_S, VD_F, "2011", "village -> district",
    "Wells/Tube Wells Area", "sum of source-wise irrigated areas", "wells / sources * 100", "%", missing=AGRI_MISSING,
    notes="groundwater dependence; wells fail in multi-year drought")
add("irr_canal_share_of_irrigated_pct", G, "Canal share of source-wise irrigated area", VD_S, VD_F, "2011", "village -> district",
    "Canals Area", "sum of source-wise irrigated areas", "canals / sources * 100", "%", missing=AGRI_MISSING, role="context")
add("irr_tank_share_of_irrigated_pct", G, "Tanks/lakes share of source-wise irrigated area", VD_S, VD_F, "2011", "village -> district",
    "Tanks/Lakes Area", "sum of source-wise irrigated areas", "tanks / sources * 100", "%", missing=AGRI_MISSING, role="context")

# ---------------- G. Landholding structure ----------------
G = "G. Landholding structure"
add("land_n_holdings_total", G, "Number of operational holdings (all size classes)", AGC_S, AGC_F, "2010-11", "district", "", "",
    "Table 2 All Size Classes, Number 2010-11", "holdings", missing=AGRI_MISSING, role="context")
add("land_small_holding_share_pct", G, "Holdings below 2.0 ha (marginal + small) as share of all holdings", AGC_S, AGC_F, "2010-11",
    "district", "marginal (<1 ha) + small (1-2 ha) holdings", "all holdings", "(marginal + small) / total * 100", "%",
    missing=AGRI_MISSING, notes="Table 2; Chandrapur's Table 5 row is a report error and is not used")
add("land_marginal_holding_share_pct", G, "Holdings below 1.0 ha as share of all holdings", AGC_S, AGC_F, "2010-11", "district",
    "marginal holdings", "all holdings", "marginal / total * 100", "%", missing=AGRI_MISSING, notes="component of small holding share")
add("land_small_holding_area_share_pct", G, "Operated area in holdings below 2.0 ha as share of total operated area", AGC_S, AGC_F,
    "2010-11", "district", "area of marginal + small holdings", "total operated area", "area ratio * 100", "%", missing=AGRI_MISSING)
add("land_avg_holding_size_ha", G, "Average size of an operational holding", AGC_S, AGC_F, "2010-11", "district", "total operated area",
    "number of holdings", "area / number", "ha", missing=AGRI_MISSING, notes="inverse relation with small holding share")

# ---------------- interim tables (not in master) ----------------
for f, d, u in [("rainfall_mm", "District area-weighted rainfall total for the month", "mm")]:
    add(f, "interim", d, IMD_S, IMD_F, "1950-2024", "district x month", "", "", "sum of daily area-weighted district means", u,
        missing="NaN if any day has no valid grid cell", role="context", table="district_monthly_rainfall.csv")
for f, d, form, u in [
    ("june_rainfall_mm", "June rainfall", "monthly total", "mm"), ("july_rainfall_mm", "July rainfall", "monthly total", "mm"),
    ("august_rainfall_mm", "August rainfall", "monthly total", "mm"), ("september_rainfall_mm", "September rainfall", "monthly total", "mm"),
    ("monsoon_rainfall_mm", "June-September rainfall", "June + July + August + September", "mm"),
    ("baseline_monsoon_mm", "District baseline monsoon rainfall", "mean over baseline years", "mm"),
    ("monsoon_departure_pct", "Departure from baseline", "(monsoon - baseline) / baseline * 100", "%"),
    ("deficient_monsoon", "Deficient monsoon (IMD category)", "departure_pct <= -20 (unrounded)", "boolean"),
    ("spi_monsoon", "Standardized Precipitation Index of the monsoon total", "gamma fit on baseline years -> normal quantile", "z"),
    ("annual_rainfall_mm", "January-December rainfall", "sum of 12 monthly totals", "mm"),
    ("extreme_value_flag", "District-year above flag_ratio x baseline (suspected product artefact; values NOT altered)",
     "monsoon_mm > rainfall_extreme_values.flag_ratio * baseline", "boolean"),
    ("extreme_low_review_flag", "District-year below low_flag_ratio x baseline (review only; many are real droughts, e.g. 1972)",
     "monsoon_mm < rainfall_extreme_values.low_flag_ratio * baseline", "boolean"),
    ("baseline_monsoon_excl_flagged_mm", "Baseline recomputed without flagged district-years (sensitivity only)",
     "mean over baseline years not flagged", "mm")]:
    add(f, "interim", d, IMD_S, IMD_F, "1950-2024", "district x year", "", "", form, u, role="context", table="district_annual_monsoon_rainfall.csv")
for f, d in [("declared_talukas_{2018,2023,2026}", "Talukas declared drought-hit in the main GR"),
             ("declared_share_{2018,2023,2026}", "declared talukas / Census 2011 talukas"),
             ("addl_revenue_circles_{2018,2023}", "Revenue circles declared drought(-like) outside the declared talukas (count only; no verified denominator)")]:
    add(f, "H. Validation (separate table)", d, "Government of Maharashtra drought GRs", "data/raw/validation/GR_*.pdf; data/manual/*.csv",
        "2018, 2023, 2026", "taluka -> district", "", "Census 2011 sub-districts per district", "count / total", "fraction",
        missing="0 if district not listed in the GR", notes="2026 is holdout-only; never used in index construction", role="validation",
        table="drought_validation.csv")
