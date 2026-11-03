"""Step 18 - validation of the FIXED vulnerability index and K-Means groups against drought declarations.

Strictly downstream: reads the final index and classification, never changes them.
Drought measure (same unit and denominator every year):
  declared_taluka_share = talukas declared in the main Government of Maharashtra GR / Census 2011 talukas
  2018: final GR 31-10-2018, severe + moderate (151 talukas)
  2023: final GR 31-10-2023, severe + moderate (40 talukas)
  2026: GR 25-09-2026, Trigger-1 stage (265 talukas)  -> HOLDOUT, reported separately
Additional revenue-circle declarations (2018, 2023) are kept as counts for context only: they are listed only
OUTSIDE declared talukas and no verified total of circles per district exists, so they are not an intensity measure.

Outputs (data/processed/):
  drought_validation_districts.csv     2018 and 2023, one row per district-year
  drought_validation_holdout_2026.csv  2026 holdout, one row per district
  drought_validation_summary.csv       correlations and group means/medians per year and measure

Run:  python src/s18_drought_validation.py   (after s17)
"""
import numpy as np
import pandas as pd
from scipy import stats

from common import INTERIM, ROOT, write_csv

OUT = ROOT / "data" / "processed"
GROUPS = ["Low Vulnerability", "Medium Vulnerability", "High Vulnerability"]
DEPARTURE = 0.5          # flag districts whose index and declaration percentile ranks differ by >= 0.5 (display only)


def district_table(base, val, year, measure, count_col):
    """One row per district: fixed index/group plus the declaration measure for one year."""
    d = base.copy()
    d["year"] = year
    d["drought_measure"] = measure
    d["drought_unit_type"] = "taluka"
    d["total_talukas_census_2011"] = d.district_id.map(val.total_talukas_census_2011)
    d["declared_talukas"] = d.district_id.map(val[count_col])
    d["drought_intensity"] = d.declared_talukas / d.total_talukas_census_2011
    d["drought_rank"] = d.drought_intensity.rank(ascending=False, method="min").astype(int)   # 1 = highest share
    d["index_pct_rank"] = d.vulnerability_index_0_100.rank(pct=True)
    d["drought_pct_rank"] = d.drought_intensity.rank(pct=True)
    gap = d.index_pct_rank - d.drought_pct_rank
    d["disagreement"] = np.select([gap >= DEPARTURE, gap <= -DEPARTURE],
                                  ["higher index, lower declaration", "lower index, higher declaration"], "")
    return d


def summarise(d, role):
    x, y = d.vulnerability_index_0_100, d.drought_intensity
    rho, p_rho = stats.spearmanr(x, y)
    r, p_r = stats.pearsonr(x, y)
    row = {"year": d.year.iloc[0], "role": role, "drought_measure": d.drought_measure.iloc[0], "n_districts": len(d),
           "n_districts_with_declaration": int((y > 0).sum()), "spearman_rho": rho, "spearman_p_two_sided": p_rho,
           "pearson_r": r, "pearson_p_two_sided": p_r}
    for g in GROUPS:
        s = y[d.vulnerability_group == g]
        short = g.split()[0].lower()
        row[f"n_{short}"] = len(s)
        row[f"mean_{short}"] = s.mean()
        row[f"median_{short}"] = s.median()
        row[f"share_with_declaration_{short}"] = (s > 0).mean()
    return row


def main():
    scores = pd.read_csv(OUT / "vulnerability_index_scores.csv")
    groups = pd.read_csv(OUT / "kmeans_vulnerability_classification.csv")
    val = pd.read_csv(INTERIM / "drought_validation.csv").set_index("district_id")

    base = scores[["district_id", "census_2011_district_code", "current_district_name", "vulnerability_index_0_100"]].merge(
        groups[["district_id", "vulnerability_group"]], on="district_id", how="inner", validate="one_to_one")
    assert len(base) == 34 and base.district_id.is_unique
    assert base.district_id.isin(val.index).all()
    assert (val.loc[base.district_id, "total_talukas_census_2011"] > 0).all()

    measures = [
        (2018, "declared taluka share (severe + moderate), final GR 31-10-2018", "declared_talukas_2018", "historical"),
        (2023, "declared taluka share (severe + moderate), final GR 31-10-2023", "declared_talukas_2023", "historical"),
        (2018, "severe-only taluka share, final GR 31-10-2018", "declared_severe_2018", "historical, secondary measure"),
        (2023, "severe-only taluka share, final GR 31-10-2023", "declared_severe_2023", "historical, secondary measure"),
        (2026, "declared taluka share (Trigger-1), GR 25-09-2026", "declared_talukas_2026", "HOLDOUT"),
    ]
    tables = {(y, c): district_table(base, val, y, m, c) for y, m, c, _ in measures}
    summary = [summarise(tables[(y, c)], role) for y, m, c, role in measures]

    # additional analysis: mean of the 2018 and 2023 shares (same unit, same denominator)
    pooled = tables[(2018, "declared_talukas_2018")].copy()
    pooled["year"] = "2018+2023"
    pooled["drought_measure"] = "mean of 2018 and 2023 declared taluka shares"
    pooled["drought_intensity"] = (pooled.drought_intensity + tables[(2023, "declared_talukas_2023")].drought_intensity.to_numpy()) / 2
    summary.append(summarise(pooled, "historical, additional pooled analysis"))
    summary = pd.DataFrame(summary)

    hist = pd.concat([tables[(2018, "declared_talukas_2018")], tables[(2023, "declared_talukas_2023")]], ignore_index=True)
    for y in (2018, 2023):
        m = hist.year == y
        hist.loc[m, "declared_severe_talukas"] = hist.district_id[m].map(val[f"declared_severe_{y}"])
        # context only - a different unit type, never added to the taluka measure
        hist.loc[m, "addl_revenue_circles_count_context_only"] = hist.district_id[m].map(val[f"addl_revenue_circles_{y}"])
    assert not hist.duplicated(["year", "district_id"]).any()
    holdout = tables[(2026, "declared_talukas_2026")]

    write_csv(hist.sort_values(["year", "vulnerability_index_0_100"], ascending=[True, False]), OUT / "drought_validation_districts.csv")
    write_csv(holdout.sort_values("vulnerability_index_0_100", ascending=False), OUT / "drought_validation_holdout_2026.csv")
    write_csv(summary, OUT / "drought_validation_summary.csv")

    pd.set_option("display.width", 250)
    cols = ["year", "role", "n_districts", "n_districts_with_declaration", "spearman_rho", "spearman_p_two_sided", "pearson_r",
            "mean_low", "mean_medium", "mean_high", "median_low", "median_medium", "median_high"]
    print(summary[cols].round(3).to_string(index=False))
    for d in (tables[(2018, "declared_talukas_2018")], tables[(2023, "declared_talukas_2023")], holdout):
        flagged = d[d.disagreement != ""]
        print(f"\n{d.year.iloc[0]} disagreement districts:")
        print(flagged[["current_district_name", "vulnerability_index_0_100", "vulnerability_group", "declared_talukas",
                       "total_talukas_census_2011", "drought_intensity", "disagreement"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
