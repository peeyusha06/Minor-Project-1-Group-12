"""Step 11 - feature-selection audit of the PCA candidates (no PCA, no scaling, no clustering).

Reads the active master table and data dictionary, and writes:
  data/interim/feature_selection_audit.csv     one row per PCA candidate, with the judgement and reason
  data/interim/feature_correlations.csv        Pearson r for every candidate pair (index-scope districts only)
  data/interim/recommended_pca_features.csv    Set A / Set B members and alternatives
  data/interim/feature_set_summary.csv         size, coverage, missingness and max |r| of each set

Run:  python src/s11_feature_selection.py
"""
import itertools

import pandas as pd

from common import INTERIM, active, load_config, variant_dir, write_csv

STRONG_R = 0.8  # threshold for reporting a correlation issue (reported only, never used to drop automatically)

# A. Exact structural redundancy: one variable is determined by the others (or, for the last two,
#    both are statistics of the same two underlying series).
EXACT = [
    ("irr_irrigated_share_of_cropped_land_pct", "irr_rainfed_share_of_cropped_land_pct", "identity: rainfed = 100 - irrigated"),
    ("soc_work_participation_rate_pct", "soc_non_worker_share_pct", "identity: non-worker = 100 - work participation"),
    ("soc_agri_worker_share_of_workers_pct", "soc_cultivator_share_of_workers_pct", "identity: agri worker = cultivator + labourer (share of workers)"),
    ("soc_agri_worker_share_of_workers_pct", "soc_agri_labourer_share_of_workers_pct", "identity: agri worker = cultivator + labourer (share of workers)"),
    ("rain_en_mean_deficit_pct", "rain_en_minus_nonen_deficit_pct", "identity: minus-version = El Nino mean deficit - non-El-Nino mean deficit"),
    ("rain_en_deficient_frequency", "rain_en_minus_nonen_deficient_frequency", "identity: minus-version = El Nino frequency - non-El-Nino frequency"),
    ("enso_rain_pearson_r", "enso_rain_spearman_rho", "same two underlying series (not an algebraic identity)"),
    ("enso_rain_pearson_r", "enso_rain_slope_pct_per_degC", "same two underlying series (not an algebraic identity)"),
]

# B. Not exact duplicates: alternative denominators for the same count, or nested measures.
ALT_MEASURES = [
    ("soc_agri_worker_share_of_workers_pct", "soc_agri_worker_share_of_population_pct", "alternative denominator for the same count (workers vs population)"),
    ("soc_marginal_worker_share_of_workers_pct", "soc_marginal_workers_per_population_pct", "alternative denominator for the same count (workers vs population)"),
    ("land_small_holding_share_pct", "land_marginal_holding_share_pct", "nested measure: holdings < 1 ha are a subset of holdings < 2 ha"),
]

# Judgement for each candidate:
# (domain, what the dataset measures, dimension, direction as used by the framework, derived_from, interpretability, action, reason)
# The direction text is a framework assumption unless the variable is itself a measured climate relationship.
AUDIT = {
    "enso_rain_pearson_r": ("ENSO-rainfall link", "Correlation between the monsoon ENSO index and district monsoon departure, 1950-2024", "Exposure",
        "more negative = El Nino years more strongly associated with lower monsoon rainfall; treated as greater exposure", "", "medium",
        "Exclude", "Same two series as the slope (r = 0.92) but unitless; the slope also carries the size of the rainfall response."),
    "enso_rain_spearman_rho": ("ENSO-rainfall link", "Rank correlation between the same two series", "Exposure",
        "more negative = stronger association; treated as greater exposure", "enso_rain_pearson_r", "low",
        "Exclude", "Robustness version of the Pearson correlation, not separate information (r = 0.92 with Pearson, 0.95 with slope)."),
    "enso_rain_slope_pct_per_degC": ("ENSO-rainfall link", "Average change in monsoon departure (%) per 1 degC of the monsoon ENSO index, 1950-2024", "Exposure",
        "more negative = larger average rainfall decrease associated with El Nino warming; treated as greater exposure", "", "high",
        "Set A core", "Uses all 75 years (1950-2024) and is the most stable climate variable (r = 0.98 between RONI and ONI versions); easy unit. Describes a historical association, not a demonstrated cause."),
    "rain_monsoon_cv_pct": ("Rainfall variability", "Coefficient of variation of June-September rainfall", "Exposure",
        "higher = more variable monsoon; treated as greater exposure", "", "high",
        "Exclude", "General rainfall variability, not specific to El Nino; strongly skewed by the suspect Pune/Jalna IMD values (skew 3.0)."),
    "rain_en_mean_deficit_pct": ("El Nino drought hazard", "Mean monsoon deficit in El Nino years", "Exposure",
        "higher = larger average deficit in El Nino years; treated as greater exposure", "", "high",
        "Alternative", "Direct and easy to explain, but unstable: r = 0.59 between RONI and ONI versions; Pune is an outlier (z = 2.6) partly because of suspect IMD values."),
    "rain_en_max_deficit_pct": ("El Nino drought hazard", "Largest monsoon deficit in any El Nino year", "Exposure",
        "higher = worse worst-case El Nino monsoon; treated as greater exposure", "", "high",
        "Set B", "Worst-case magnitude, stable across indices (r = 0.98); depends on a single year per district, so sensitive to single-year data errors."),
    "rain_en_deficient_frequency": ("El Nino drought hazard", "Share of El Nino years with a deficient monsoon (IMD: departure <= -20%)", "Exposure",
        "higher = El Nino years more often deficient; treated as greater exposure", "", "high",
        "Set A core", "Measures how often El Nino years were deficient in this district, using IMD's own category; reasonably stable (r = 0.87 RONI vs ONI). Concern: Pune z = 3.6, partly from suspect IMD years."),
    "rain_en_mean_spi": ("El Nino drought hazard", "Mean monsoon SPI in El Nino years", "Exposure",
        "more negative = drier El Nino years; treated as greater exposure", "rain_en_mean_deficit_pct", "low",
        "Exclude", "Another scale for the mean El Nino deficit (r = -0.90); least stable across indices (r = 0.42); harder to explain."),
    "rain_en_minus_nonen_deficit_pct": ("El Nino drought hazard", "El Nino mean deficit minus non-El-Nino mean deficit", "Exposure",
        "higher = El Nino years drier than other years; treated as greater exposure", "rain_en_mean_deficit_pct", "medium",
        "Exclude", "Exactly determined by the mean deficit and the non-El-Nino deficit; unstable across indices (r = 0.48); overlaps with the slope (r = -0.87)."),
    "rain_en_minus_nonen_deficient_frequency": ("El Nino drought hazard", "El Nino deficient frequency minus non-El-Nino deficient frequency", "Exposure",
        "higher = deficient monsoons more frequent in El Nino years; treated as greater exposure", "rain_en_deficient_frequency", "medium",
        "Exclude", "Exactly determined by the two frequencies (r = 0.91 with El Nino frequency); less stable (r = 0.71 across indices)."),
    "soc_rural_population_share_pct": ("Population", "Rural share of population (Census 2011)", "Sensitivity",
        "higher is treated as greater sensitivity, on the assumption that rural livelihoods depend more on local rainfall", "", "high",
        "Alternative", "Overlaps with agricultural worker share (r = 0.87), which measures farm-based work more directly."),
    "soc_literacy_rate_7plus_pct": ("Education", "Literacy rate, population aged 7+ (Census 2011)", "Adaptive capacity",
        "higher is used as an adaptive-capacity indicator (treated as lower vulnerability); the framework assumes literacy helps access to information, credit, relief and non-farm work, which this dataset does not test", "", "high",
        "Set A core", "Only clean adaptive-capacity indicator available; clear direction under the framework; no redundancy."),
    "soc_work_participation_rate_pct": ("Employment", "Workers as share of population (Census 2011)", "not clearly assignable",
        "unclear: high participation can reflect more earners or distress work", "", "low",
        "Exclude", "Direction of vulnerability is unclear; exact complement of non-worker share."),
    "soc_non_worker_share_pct": ("Employment", "Non-workers as share of population (Census 2011)", "not clearly assignable",
        "unclear", "soc_work_participation_rate_pct", "low",
        "Exclude", "Exactly 100 - work participation rate; direction unclear."),
    "soc_agri_worker_share_of_workers_pct": ("Livelihood", "Cultivators + agricultural labourers as share of workers (Census 2011)", "Sensitivity",
        "higher is treated as greater sensitivity because a larger share of workers is employed in agriculture, which the framework assumes is rainfall-dependent", "", "high",
        "Set A core", "Directly measures agricultural employment ('agricultural dependency' in the proposal); same formula as the prototype."),
    "soc_agri_worker_share_of_population_pct": ("Livelihood", "Agricultural workers as share of total population (Census 2011)", "Sensitivity",
        "higher treated as greater sensitivity (same assumption)", "", "medium",
        "Exclude", "Alternative denominator for the same count (r = 0.98 with the worker-based version); keep one (config: agricultural_worker_denominator)."),
    "soc_cultivator_share_of_workers_pct": ("Livelihood", "Cultivators as share of workers (Census 2011)", "Sensitivity",
        "higher treated as greater sensitivity (same assumption)", "soc_agri_worker_share_of_workers_pct", "medium",
        "Exclude", "Component of agricultural worker share."),
    "soc_agri_labourer_share_of_workers_pct": ("Livelihood", "Agricultural labourers as share of workers (Census 2011)", "Sensitivity",
        "higher treated as greater sensitivity, on the assumption that wage labourers lose work when crops fail", "soc_agri_worker_share_of_workers_pct", "high",
        "Alternative", "Component of agricultural worker share, but conceptually sharper (landless labour); could replace the total if the guide prefers."),
    "soc_marginal_worker_share_of_workers_pct": ("Livelihood", "Marginal workers (worked < 6 months) as share of workers (Census 2011)", "Sensitivity",
        "higher treated as greater sensitivity, on the assumption that seasonal work is less secure", "", "high",
        "Set B", "Distinct information (max |r| 0.74 with cropped land); corrected denominator. Skewed (1.6) by tribal districts."),
    "soc_marginal_workers_per_population_pct": ("Livelihood", "Marginal workers as share of population (prototype definition)", "Sensitivity",
        "higher treated as greater sensitivity (same assumption)", "", "medium",
        "Exclude", "Alternative denominator for the same count (r = 0.98 with the worker-based version); kept only for comparison with the prototype."),
    "soc_sc_share_pct": ("Social group", "Scheduled Caste share of population (Census 2011)", "Sensitivity (indirect)",
        "if retained, higher is treated as greater sensitivity as an indirect social-vulnerability indicator; the dataset does not measure household poverty or income", "", "medium",
        "Alternative", "Indirect social-vulnerability indicator with no drought mechanism measured here; small spread (3-20%). Option if the guide wants a social-vulnerability dimension."),
    "soc_st_share_pct": ("Social group", "Scheduled Tribe share of population (Census 2011)", "Sensitivity (indirect)",
        "if retained, higher is treated as greater sensitivity as an indirect social-vulnerability indicator; the dataset does not measure household poverty or income", "", "medium",
        "Set B", "Indirect social-vulnerability indicator (no verified district poverty variable exists in the sources); very skewed (2.4, Nandurbar 69%), so one district can dominate a component."),
    "agri_cropped_land_share_pct": ("Agricultural exposure", "Net area sown as share of village area (Village Directory 2011)", "Exposure",
        "higher is treated as greater exposure because more land is under crops that a rainfall deficit can affect", "", "high",
        "Set B", "Represents agricultural exposure; overlaps with the climate slope (r = -0.78) because cropland is concentrated in the dry interior."),
    "irr_irrigated_share_of_cropped_land_pct": ("Irrigation", "Irrigated area as share of net area sown (Village Directory 2011)", "Adaptive capacity",
        "higher is treated as lower vulnerability, on the assumption that irrigation buffers rainfall deficits", "", "high",
        "Alternative", "Exact complement of rainfed share; use one. Same information as the chosen rainfed share, opposite sign."),
    "irr_rainfed_share_of_cropped_land_pct": ("Irrigation", "Unirrigated (rainfed) area as share of net area sown (Village Directory 2011)", "Sensitivity",
        "higher is treated as greater sensitivity, on the assumption that rainfed crops depend on the monsoon", "irr_irrigated_share_of_cropped_land_pct", "high",
        "Set A core", "Irrigation dependence (named in the proposal); chosen over irrigated share so that higher = more vulnerable like most other variables."),
    "irr_well_share_of_irrigated_pct": ("Irrigation", "Wells/tube wells share of irrigated area (Village Directory 2011)", "not clearly assignable",
        "unclear: wells may buffer a single bad season but may fail in multi-year droughts", "", "medium",
        "Exclude", "Direction of vulnerability is ambiguous; share of an already-small irrigated area in many districts."),
    "land_small_holding_share_pct": ("Landholding", "Holdings below 2 ha as share of all holdings (Agriculture Census 2010-11)", "Sensitivity",
        "higher is treated as greater sensitivity because smaller operational holdings are hypothesised to give less capacity to absorb a failed season", "", "high",
        "Set A core", "Standard 'small and marginal farmer' definition; no missing values in scope."),
    "land_marginal_holding_share_pct": ("Landholding", "Holdings below 1 ha as share of all holdings (Agriculture Census 2010-11)", "Sensitivity",
        "higher treated as greater sensitivity (same hypothesis)", "", "medium",
        "Exclude", "Nested within small holding share (r = 0.96); keep one."),
    "land_small_holding_area_share_pct": ("Landholding", "Area operated by holdings below 2 ha as share of total area", "Sensitivity",
        "higher treated as greater sensitivity (same hypothesis)", "", "medium",
        "Exclude", "Overlaps with small holding share (r = 0.72) and is harder to explain than the share of holdings."),
    "land_avg_holding_size_ha": ("Landholding", "Average operational holding size", "Sensitivity",
        "higher treated as lower sensitivity (same hypothesis)", "", "high",
        "Exclude", "Near-mirror of small holding share (r = -0.99); both come from the same Agriculture Census table."),
}


def evidence(f):
    """What this project itself shows about the variable (vs what the framework assumes)."""
    if f.startswith(("rain_", "enso_")):
        return "measured here: historical rainfall/ENSO statistics 1950-2024 (association, not causation)"
    return "measured here: the share itself; its link to drought impact is a framework assumption not tested in this project"


SET_A = ["enso_rain_slope_pct_per_degC", "rain_en_deficient_frequency", "soc_agri_worker_share_of_workers_pct",
         "irr_rainfed_share_of_cropped_land_pct", "land_small_holding_share_pct", "soc_literacy_rate_7plus_pct"]
SET_B = SET_A + ["rain_en_max_deficit_pct", "agri_cropped_land_share_pct", "soc_marginal_worker_share_of_workers_pct", "soc_st_share_pct"]
ALTERNATIVES = {
    "rain_en_mean_deficit_pct": "rain_en_deficient_frequency",
    "irr_irrigated_share_of_cropped_land_pct": "irr_rainfed_share_of_cropped_land_pct",
    "soc_agri_labourer_share_of_workers_pct": "soc_agri_worker_share_of_workers_pct",
    "soc_rural_population_share_pct": "soc_agri_worker_share_of_workers_pct",
    "soc_sc_share_pct": "soc_st_share_pct",
}


def partners(f, pairs):
    return [(b if a == f else a, why) for a, b, why in pairs if f in (a, b)]


def main():
    master = pd.read_csv(INTERIM / "maharashtra_district_feature_table.csv")
    dic = pd.read_csv(INTERIM / "data_dictionary.csv")
    dic = dic[dic.table == "maharashtra_district_feature_table.csv"].set_index("feature")
    candidates = dic[dic.role == "pca_candidate"].index.tolist()
    assert set(candidates) == set(AUDIT), "audit list and data dictionary disagree"
    scope = master[master.in_index_scope]

    # empirical correlations, index-scope districts only
    corr = scope[candidates].corr()
    kind = {frozenset(p[:2]): "exact: " + p[2] for p in EXACT}
    kind.update({frozenset(p[:2]): "alternative: " + p[2] for p in ALT_MEASURES})
    pairs = []
    for a, b in itertools.combinations(candidates, 2):
        r = corr.loc[a, b]
        pairs.append({"feature_1": a, "feature_2": b, "pearson_r": r, "abs_r": abs(r),
                      "structural_relation": kind.get(frozenset((a, b)), "")})
    pairs = pd.DataFrame(pairs).sort_values("abs_r", ascending=False)

    # does the climate variable change much when the ENSO index changes? (active geography, same districts)
    geo = active(load_config(), "district_geography")
    roni = pd.read_csv(variant_dir(geo, "RONI") / "maharashtra_district_feature_table.csv")
    oni = pd.read_csv(variant_dir(geo, "ONI_v6") / "maharashtra_district_feature_table.csv")
    in_scope = roni.in_index_scope

    rows = []
    for f in candidates:
        domain, measured, dim, direction, derived, interp, action, reason = AUDIT[f]
        exact = partners(f, EXACT)
        alt = partners(f, ALT_MEASURES)
        strong = pairs[((pairs.feature_1 == f) | (pairs.feature_2 == f)) & (pairs.abs_r >= STRONG_R)]
        strong_txt = "; ".join(f"{r.feature_2 if r.feature_1 == f else r.feature_1} (r={r.pearson_r:.2f})" for r in strong.itertuples())
        uses_enso = f.startswith("enso_") or f.startswith("rain_en")
        rows.append({
            "feature": f, "group": dic.loc[f, "group"], "domain": domain, "meaning": measured,
            "source": dic.loc[f, "source"], "year": dic.loc[f, "year"], "formula": dic.loc[f, "formula"],
            "conceptual_dimension": dim, "vulnerability_direction": direction, "evidence_in_this_project": evidence(f),
            "exact_structural_redundancy": "yes" if exact else "no",
            "redundant_with": "; ".join(f"{p} ({why})" for p, why in exact),
            "alternative_measure_of": "; ".join(f"{p} ({why})" for p, why in alt),
            "correlation_issue": strong_txt, "derived_from": derived,
            "stability_RONI_vs_ONI_r": roni[in_scope][f].corr(oni[in_scope][f]) if uses_enso else None,
            "skewness_in_scope": scope[f].skew(), "missing_in_scope": int(scope[f].isna().sum()),
            "interpretability": interp, "candidate_action": action, "reason": reason,
        })
    audit = pd.DataFrame(rows)

    rec = []
    for f in dict.fromkeys(SET_B + list(ALTERNATIVES)):
        a = AUDIT[f]
        status = "Set A core" if f in SET_A else ("Set B addition" if f in SET_B else "alternative")
        rec.append({"feature": f, "conceptual_dimension": a[2], "vulnerability_direction": a[3], "in_set_A": f in SET_A,
                    "in_set_B": f in SET_B, "status": status, "alternative_for": ALTERNATIVES.get(f, ""), "reason": a[7]})
    rec = pd.DataFrame(rec)

    summary = []
    for name, cols in [("Set A (compact candidate)", SET_A), ("Set B (broader candidate)", SET_B)]:
        c = scope[cols].corr().abs()
        top = max(((c.loc[a, b], a, b) for a, b in itertools.combinations(cols, 2)))
        dims = pd.Series([AUDIT[f][2] for f in cols]).value_counts()
        summary.append({"set": name, "n_variables": len(cols), "n_districts": len(scope),
                        "districts_per_variable": round(len(scope) / len(cols), 1), "variables": "; ".join(cols),
                        "dimension_coverage": "; ".join(f"{k}: {v}" for k, v in dims.items()),
                        "exact_redundancy_remaining": sum(a in cols and b in cols for a, b, _ in EXACT),
                        "alternative_measure_pairs_remaining": sum(a in cols and b in cols for a, b, _ in ALT_MEASURES),
                        "missing_values_in_scope": int(scope[cols].isna().sum().sum()),
                        "max_abs_r": round(top[0], 2), "max_abs_r_pair": f"{top[1]} / {top[2]}"})
    summary = pd.DataFrame(summary)

    write_csv(audit, INTERIM / "feature_selection_audit.csv", 3)
    write_csv(pairs, INTERIM / "feature_correlations.csv", 3)
    write_csv(rec, INTERIM / "recommended_pca_features.csv")
    write_csv(summary, INTERIM / "feature_set_summary.csv")
    print(f"{len(scope)} districts in scope, {len(candidates)} candidates")
    print(audit.candidate_action.value_counts().to_string())
    print(summary.drop(columns=["variables", "dimension_coverage"]).to_string())


if __name__ == "__main__":
    main()
