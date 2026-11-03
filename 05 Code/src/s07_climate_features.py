"""Step 7 - district climate-impact (hazard / ENSO-exposure) candidate features.

Inputs: district_annual_monsoon_rainfall.csv (step 5, one geography) and the yearly ENSO table
(step 6, one index). The two ENSO indices are NEVER mixed: each (geography, index) pair is a
separate feature set.

Notation per district d:  T = study-period years with monsoon data (1950-2024),
E = El Nino monsoon years in T (episode_flag), N = T minus E,
D_y = monsoon departure % from the district baseline, deficit_y = -D_y,
S_y = monsoon SPI, I_y = mean of the JJA and JAS seasonal ENSO index values.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from common import variant_dir, write_csv

FEATURE_FORMULAS = {
    "n_study_years": "|T|",
    "n_elnino_years": "|E|",
    "elnino_years": "sorted list of years in E",
    "baseline_monsoon_mm": "mean June-September rainfall over the baseline period",
    "monsoon_cv_pct": "std(monsoon_mm over T) / mean(monsoon_mm over T) * 100",
    "en_mean_deficit_pct": "mean over E of (-D_y)",
    "en_max_deficit_pct": "max over E of (-D_y)",
    "en_deficient_frequency": "share of years in E with D_y <= deficient threshold (unrounded)",
    "en_mean_spi": "mean over E of S_y",
    "nonen_mean_deficit_pct": "mean over N of (-D_y)",
    "nonen_deficient_frequency": "share of years in N with D_y <= deficient threshold (unrounded)",
    "en_minus_nonen_deficit_pct": "en_mean_deficit_pct - nonen_mean_deficit_pct",
    "en_minus_nonen_deficient_frequency": "en_deficient_frequency - nonen_deficient_frequency",
    "enso_rain_pearson_r": "Pearson correlation of I_y and D_y over T",
    "enso_rain_pearson_p": "two-sided p-value of enso_rain_pearson_r",
    "enso_rain_spearman_rho": "Spearman rank correlation of I_y and D_y over T",
    "enso_rain_slope_pct_per_degC": "OLS slope of D_y on I_y over T (% departure per 1 degC)",
}


def features(annual: pd.DataFrame, enso: pd.DataFrame, index: str, geo: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    e = enso[enso.in_study_period][["year", "episode_flag", "monsoon_index_mean_JJA_JAS"]]
    a = annual.merge(e, on="year", how="inner")
    rows = []
    for d, g in a.groupby("district_id"):
        g = g.dropna(subset=["monsoon_departure_pct"])
        en, non = g[g.episode_flag], g[~g.episode_flag]
        r, p = stats.pearsonr(g.monsoon_index_mean_JJA_JAS, g.monsoon_departure_pct)
        rho = stats.spearmanr(g.monsoon_index_mean_JJA_JAS, g.monsoon_departure_pct).statistic
        slope = stats.linregress(g.monsoon_index_mean_JJA_JAS, g.monsoon_departure_pct).slope
        rows.append({
            "district_id": d, "enso_index": index, "geography_version": geo,
            "n_study_years": len(g), "n_elnino_years": len(en),
            "elnino_years": ";".join(map(str, sorted(en.year))),
            "baseline_monsoon_mm": g.baseline_monsoon_mm.iloc[0],
            "monsoon_cv_pct": g.monsoon_rainfall_mm.std() / g.monsoon_rainfall_mm.mean() * 100,
            "en_mean_deficit_pct": -en.monsoon_departure_pct.mean(),
            "en_max_deficit_pct": -en.monsoon_departure_pct.min(),
            "en_deficient_frequency": en.deficient_monsoon.mean(),
            "en_mean_spi": en.spi_monsoon.mean(),
            "nonen_mean_deficit_pct": -non.monsoon_departure_pct.mean(),
            "nonen_deficient_frequency": non.deficient_monsoon.mean(),
            "enso_rain_pearson_r": r, "enso_rain_pearson_p": p, "enso_rain_spearman_rho": rho,
            "enso_rain_slope_pct_per_degC": slope,
        })
    f = pd.DataFrame(rows)
    f["en_minus_nonen_deficit_pct"] = f.en_mean_deficit_pct - f.nonen_mean_deficit_pct
    f["en_minus_nonen_deficient_frequency"] = f.en_deficient_frequency - f.nonen_deficient_frequency
    long = a[["district_id", "year", "monsoon_rainfall_mm", "monsoon_departure_pct", "spi_monsoon", "deficient_monsoon",
              "episode_flag", "monsoon_index_mean_JJA_JAS"]].copy()
    long["enso_index"] = index
    return f, long


def run(annual: pd.DataFrame, enso: pd.DataFrame, geo: str, index: str) -> pd.DataFrame:
    f, long = features(annual, enso, index, geo)
    d = variant_dir(geo, index)
    write_csv(f, d / "climate_vulnerability_features.csv")
    write_csv(long, d / "district_year_enso_rainfall.csv", 4)
    return f
