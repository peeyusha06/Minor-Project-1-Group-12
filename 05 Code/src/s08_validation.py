"""Step 8 - district drought-declaration validation table (NEVER used to build the index).

Sources (Government of Maharashtra GRs, data/raw/validation/):
  2018 main   201810311722349219  (151 talukas: 112 severe + 39 moderate)   -> data/manual transcription
  2018 addl   201811061721013119  (268 revenue circles outside the 151)     -> data/manual transcription (scanned table)
  2023 main   202310311545053419  (40 talukas: 24 severe + 16 moderate)     -> data/manual transcription
  2023 addl   202311101718225419  (1021 revenue circles outside the 40)     -> parsed from PDF text here
  2026 main   202609261117494941  (265 talukas, Trigger-1)                  -> data/manual transcription; HOLDOUT ONLY
Denominator: Census 2011 sub-districts (talukas) per district, excluding the Mumbai placeholder rows (code 99999).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from common import PALGHAR_LGD, PALGHAR_SUBDISTRICTS, SRC, THANE, geo_dir, pdftotext, write_csv

OFFICIAL_TOTALS = {(2018, "severe"): 112, (2018, "moderate"): 39, (2023, "severe"): 24, (2023, "moderate"): 16, (2026, "trigger1"): 265}
OFFICIAL_CIRCLES = {2018: 268, 2023: 1021}


def load_talukas() -> pd.DataFrame:
    t = pd.read_csv(SRC["gr_talukas"])
    for (y, cat), n in OFFICIAL_TOTALS.items():
        got = t[(t.year == y) & (t.category == cat)].n_talukas_official.sum()
        assert got == n, f"{y} {cat}: transcribed {got}, GR states {n}"
    # names listed must agree with the official count on every row
    listed = t.taluka_names_as_printed.map(lambda s: 0 if s == "निरंक" else len([x for x in s.split(",") if x.strip()]))
    bad = t[listed != t.n_talukas_official]
    assert bad.empty, f"name count differs from official count:\n{bad}"
    return t


def parse_2023_circles() -> pd.DataFrame:
    text = pdftotext(SRC["gr_2023_circles"])
    pat = re.compile(r"^\s*(\d{1,4})\s+(\S+(?:\s\S+)?)\s{2,}(\S.*?)\s{2,}([A-Za-z][A-Za-z0-9 .()'\-]*?)\s{2,}(\S.*)$")
    rows = [m.groups() for line in text.splitlines() if (m := pat.match(line))]
    df = pd.DataFrame(rows, columns=["serial", "district_as_extracted", "taluka_as_extracted", "revenue_circle_en", "revenue_circle_mr"])
    df["serial"] = df.serial.astype(int)
    assert sorted(df.serial) == list(range(1, OFFICIAL_CIRCLES[2023] + 1)), "2023 circle serials incomplete"
    m = pd.read_csv(SRC["gr2023_circle_map"])
    df = df.merge(m[["district_string_as_extracted", "census_2011_district_code"]], left_on="district_as_extracted",
                  right_on="district_string_as_extracted", how="left").drop(columns="district_string_as_extracted")
    unmapped = df[df.census_2011_district_code.isna()].district_as_extracted.unique()
    assert len(unmapped) == 0, f"unmapped district strings (pdftotext version differs?): {unmapped}"
    return df


def taluka_counts(pca: pd.DataFrame, geo: str) -> pd.Series:
    sub = pca[(pca.Level == "SUB-DISTRICT") & (pca.TRU == "Total") & (pca.Subdistt != "99999")].copy()
    sub["district_id"] = sub.District.astype(int)
    if geo == "B":
        sub.loc[(sub.district_id == THANE) & sub.Subdistt.isin(PALGHAR_SUBDISTRICTS), "district_id"] = PALGHAR_LGD
    return sub.groupby("district_id").size()


def build(pca: pd.DataFrame, geo: str, ids: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    t = load_talukas()
    key = "lgd_district_code" if geo == "B" else "census_2011_district_code"
    c18 = pd.read_csv(SRC["gr2018_circles"])
    assert c18.n_revenue_circles_official.sum() == OFFICIAL_CIRCLES[2018]
    c23 = parse_2023_circles()

    v = pd.DataFrame({"district_id": ids})
    v["total_talukas_census_2011"] = v.district_id.map(taluka_counts(pca, geo)).fillna(0).astype(int)
    for y in (2018, 2023, 2026):
        ty = t[t.year == y]
        g = ty.groupby(key)
        v[f"listed_in_gr_{y}"] = v.district_id.isin(ty[key])
        v[f"declared_talukas_{y}"] = v.district_id.map(g.n_talukas_official.sum()).fillna(0).astype(int)
        if y in (2018, 2023):
            v[f"declared_severe_{y}"] = v.district_id.map(ty[ty.category == "severe"].groupby(key).n_talukas_official.sum()).fillna(0).astype(int)
            v[f"declared_moderate_{y}"] = v.district_id.map(ty[ty.category == "moderate"].groupby(key).n_talukas_official.sum()).fillna(0).astype(int)
        v[f"declared_share_{y}"] = np.where(v.total_talukas_census_2011 > 0, v[f"declared_talukas_{y}"] / v.total_talukas_census_2011, np.nan)
    # Additional revenue-circle declarations (partial talukas), as COUNTS only: the total number of
    # revenue circles per district is not available in any verified source, and taluka names in the
    # 2023 list contain spelling variants / an overlap / a probable district error (see circle QA file),
    # so a taluka-level 'any-level share' is not constructed. Thane/Palghar/Mumbai are never listed.
    # Geography B: neither circle list contains Thane or Palghar, so the Census code maps 1:1.
    v["addl_revenue_circles_2018"] = v.district_id.map(c18.groupby("census_2011_district_code").n_revenue_circles_official.sum()).fillna(0).astype(int)
    v["addl_revenue_circles_2023"] = v.district_id.map(c23.groupby("census_2011_district_code").size()).fillna(0).astype(int)
    v["holdout_only_2026"] = True
    v["use_in_training"] = False
    v["geography_version"] = geo
    return v, c23


def circle_qa(c23: pd.DataFrame) -> pd.DataFrame:
    """Distinct taluka strings per district in the 2023 circle list, with issues found on inspection."""
    t = pd.read_csv(SRC["gr_talukas"])
    declared = t[t.year == 2023].groupby("census_2011_district_code").taluka_names_as_printed.apply("; ".join)
    q = c23.groupby(["census_2011_district_code", "taluka_as_extracted"]).size().rename("n_circles").reset_index()
    q["declared_talukas_2023_same_district"] = q.census_2011_district_code.map(declared).fillna("")
    known = {
        (526, "माढा"): "overlap: Madha was already a declared (moderate) taluka in the main 2023 GR",
        (525, "गेवराई"): "probable GR error: Gevrai is a Beed taluka but is listed under Osmanabad/Dharashiv",
        (522, "अकोला"): "spelling: 'Akola' printed for Akole taluka of Ahmednagar (also listed as अकोले)",
    }
    q["issue"] = [known.get((int(d), s), "") for d, s in zip(q.census_2011_district_code, q.taluka_as_extracted)]
    q["note"] = "strings as extracted by pdftotext; several talukas appear under two spellings (e.g. बोदवड/बोधवड, यावल/यावळ, पलुस/पलूस)"
    return q


def run(pca: pd.DataFrame, geo: str, ids: list[int]) -> pd.DataFrame:
    v, c23 = build(pca, geo, ids)
    write_csv(v, geo_dir(geo) / "drought_validation.csv", 4)
    if geo == "A":
        write_csv(c23, geo_dir(geo).parent / "validation_gr2023_revenue_circles_extracted.csv")
        write_csv(circle_qa(c23), geo_dir(geo).parent / "validation_gr2023_revenue_circles_qa.csv")
    return v
