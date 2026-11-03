"""Step 4 - landholding structure from the Agriculture Census 2010-11 Maharashtra State Report.

Source: data/raw/agriculture/agcensus/Agriculture_Census_2010-11_Maharashtra_State_Report_Argi.pdf
(text PDF; extracted with poppler 'pdftotext -layout').

Size classes (report page 1, Technical Notes): Marginal < 1.0 ha, Small 1.0-2.0 ha,
Semi-medium 2.0-4.0, Medium 4.0-10.0, Large >= 10.0 ha.
Small holding (project definition) = Marginal + Small = holdings below 2.0 ha.

Tables used (all social groups, 2010-11 columns only):
  Table 2  (pages 21-23): district number & area - All size classes / Marginal / Small  -> PRIMARY
  Table 26 (pages 69-76): tahsil number & area by Marginal / Small / Other               -> cross-check, Palghar
  Table 5  (page 39)    : district % distribution of number of holdings                 -> cross-check only
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from common import PALGHAR_LGD, SRC, THANE, geo_dir, pdftotext, write_csv

# Names exactly as printed in the report -> Census 2011 district code (explicit, no fuzzy matching)
REPORT_NAME_TO_CODE = {
    "Thane": 517, "Raigad": 520, "Ratnagiri": 528, "Ratanagiri": 528, "Sindhudurg": 529, "Nashik": 516, "Nasik": 516,
    "Dhule": 498, "Nandurbar": 497, "Jalgaon": 499, "Ahmednagar": 522, "Pune": 521, "Solapur": 526, "Satara": 527,
    "Sangali": 531, "Sangli": 531, "Kolhapur": 530, "Aurangabad": 515, "Jalna": 514, "Beed": 523, "Latur": 524,
    "Osmanabad": 525, "Nanded": 511, "Parbhani": 513, "Parbhni": 513, "Hingoli": 512, "Buldhana": 500, "Akola": 501,
    "Washim": 502, "Amaravati": 503, "Yavatmal": 510, "Wardha": 504, "Nagpur": 505, "Bhandara": 506, "Gondia": 507,
    "Chandrapur": 509, "Gadchiroli": 508,
}
# Table 26 Thane tahsils that formed Palghar district (spellings as printed in the report)
PALGHAR_TAHSILS_AS_PRINTED = {"Wasai", "Wada", "Dahanu", "Palghar", "Vikramgad", "Jawahar", "Mokhada", "Talasari"}

NUM = r"-?\d+(?:\.\d+)?"


def pages() -> list[str]:
    return pdftotext(SRC["agcensus_report"]).split("\f")


def _find_page(pgs: list[str], *needles: str) -> str:
    hits = [p for p in pgs if all(n in p for n in needles)]
    assert len(hits) == 1, f"expected one page for {needles}, found {len(hits)}"
    return hits[0]


def parse_table2(page: str, label: str) -> pd.DataFrame:
    rows = []
    for line in page.split("\n"):
        m = re.match(rf"^\s*(\d{{1,2}})\s+([A-Za-z][A-Za-z .]*?)\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s*$", line)
        if m:
            name = m.group(2).strip()
            rows.append({"report_name": name, "district_id": REPORT_NAME_TO_CODE[name],
                         f"n_{label}_2010_11": float(m.group(3)), f"area_{label}_2010_11_ha": float(m.group(4))})
    df = pd.DataFrame(rows)
    assert len(df) == 33, f"Table 2 ({label}): parsed {len(df)} district rows, expected 33"
    return df


def parse_table5(page: str) -> pd.DataFrame:
    rows = []
    for line in page.split("\n"):
        m = re.match(rf"^\s*(\d{{1,2}})\s+([A-Za-z][A-Za-z .]*?)\s+" + r"\s+".join([f"({NUM})"] * 10) + r"\s*$", line)
        if m:
            name = m.group(2).strip()
            v = [float(m.group(i)) for i in range(3, 13)]
            rows.append({"district_id": REPORT_NAME_TO_CODE[name], "t5_pct_marginal_2010_11": v[5], "t5_pct_small_2010_11": v[6],
                         "t5_pct_marginal_2000_01": v[0], "t5_pct_small_2000_01": v[1]})
    df = pd.DataFrame(rows)
    assert len(df) == 33, f"Table 5: parsed {len(df)} rows"
    return df


def parse_table26(pgs: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    tahsils, subtotals, pending = [], [], []
    for p in pgs:
        if "Table 26" not in p:
            continue
        for line in p.split("\n"):
            toks = line.split()
            if len(toks) < 10:
                continue
            nums = toks[-9:]
            if not all(re.fullmatch(NUM, t) for t in nums):
                continue
            head = " ".join(toks[:-9])
            vals = [float(t) for t in nums]
            rec = dict(zip(["n_marginal", "area_marginal", "n_small", "area_small", "n_other", "area_other", "n_total", "area_total", "avg_size"], vals))
            sm = re.fullmatch(r"([A-Za-z][A-Za-z .]*?)\s*-\s*(\d{1,2})", head)
            tm = re.fullmatch(r"(\d{1,2})\s+(.+)", head)
            if sm:
                name = sm.group(1).strip()
                code = REPORT_NAME_TO_CODE[name]
                subtotals.append({"report_name": name, "district_id": code, **rec})
                for t in pending:
                    t["district_id"] = code
                tahsils.extend(pending)
                pending = []
            elif tm and not tm.group(2).strip().isdigit():  # skip the '1 2 3 ... 11' column-number row
                pending.append({"tahsil_as_printed": tm.group(2).strip(), **rec})
    t, s = pd.DataFrame(tahsils), pd.DataFrame(subtotals)
    assert len(s) == 33, f"Table 26: {len(s)} district subtotals"
    return t, s


def run(geo: str) -> pd.DataFrame:
    pgs = pages()
    t2_all = parse_table2(_find_page(pgs, "Table 2 :", "All Size Classes"), "all")
    t2_mar = parse_table2(_find_page(pgs, "Table 2 :", "(Marginal Size Group)"), "marginal")
    t2_sml = parse_table2(_find_page(pgs, "Table 2 :", "(Small Size Group)"), "small")
    t5 = parse_table5(_find_page(pgs, "Table 5 :", "percentage distribution of number"))
    t26, t26s = parse_table26(pgs)

    t2 = t2_all.merge(t2_mar.drop(columns="report_name"), on="district_id").merge(t2_sml.drop(columns="report_name"), on="district_id")
    feat = pd.DataFrame({"district_id": t2.district_id, "report_name": t2.report_name,
                         "n_holdings_total": t2.n_all_2010_11, "area_operated_total_ha": t2.area_all_2010_11_ha,
                         "n_holdings_marginal": t2.n_marginal_2010_11, "n_holdings_small": t2.n_small_2010_11,
                         "area_marginal_ha": t2.area_marginal_2010_11_ha, "area_small_ha": t2.area_small_2010_11_ha,
                         "source_table": "Table 2"})

    if geo == "B":
        th = t26[t26.district_id == THANE]
        pal = th[th.tahsil_as_printed.isin(PALGHAR_TAHSILS_AS_PRINTED)]
        assert len(pal) == 8, f"expected 8 Palghar tahsils in Table 26, found {len(pal)}"
        rest = th[~th.tahsil_as_printed.isin(PALGHAR_TAHSILS_AS_PRINTED)]
        feat = feat[feat.district_id != THANE]
        for code, part, label in [(PALGHAR_LGD, pal, "Palghar (Table 26 tahsils)"), (THANE, rest, "Thane minus Palghar (Table 26 tahsils)")]:
            feat = pd.concat([feat, pd.DataFrame([{
                "district_id": code, "report_name": label, "n_holdings_total": part.n_total.sum(),
                "area_operated_total_ha": part.area_total.sum(), "n_holdings_marginal": part.n_marginal.sum(),
                "n_holdings_small": part.n_small.sum(), "area_marginal_ha": part.area_marginal.sum(),
                "area_small_ha": part.area_small.sum(), "source_table": "Table 26"}])], ignore_index=True)

    feat["small_holding_share_pct"] = (feat.n_holdings_marginal + feat.n_holdings_small) / feat.n_holdings_total * 100
    feat["marginal_holding_share_pct"] = feat.n_holdings_marginal / feat.n_holdings_total * 100
    feat["small_holding_area_share_pct"] = (feat.area_marginal_ha + feat.area_small_ha) / feat.area_operated_total_ha * 100
    feat["avg_holding_size_ha"] = feat.area_operated_total_ha / feat.n_holdings_total
    feat = feat.sort_values("district_id").reset_index(drop=True)

    # --- QA: Table 2 vs Table 26 subtotals vs Table 5 percentages ---
    q = t2.merge(t26s.rename(columns=lambda c: f"t26_{c}" if c not in ("district_id",) else c), on="district_id", how="left")
    q = q.merge(t5, on="district_id", how="left")
    q["t2_pct_marginal"] = q.n_marginal_2010_11 / q.n_all_2010_11 * 100
    q["t2_pct_small"] = q.n_small_2010_11 / q.n_all_2010_11 * 100
    q["t26_pct_marginal"] = q.t26_n_marginal / q.t26_n_total * 100
    q["t26_pct_small"] = q.t26_n_small / q.t26_n_total * 100
    q["diff_total_t2_minus_t26"] = q.n_all_2010_11 - q.t26_n_total
    q["diff_pct_marginal_t2_minus_t5"] = q.t2_pct_marginal - q.t5_pct_marginal_2010_11
    q["diff_pct_small_t2_minus_t5"] = q.t2_pct_small - q.t5_pct_small_2010_11
    tahsil_sum = t26.groupby("district_id").n_total.sum()
    q["t26_tahsil_sum_minus_subtotal"] = q.district_id.map(tahsil_sum) - q.t26_n_total
    q["t26_n_tahsils"] = q.district_id.map(t26.groupby("district_id").size())
    q["flag"] = np.where((q.diff_pct_marginal_t2_minus_t5.abs() > 1) | (q.diff_pct_small_t2_minus_t5.abs() > 1),
                         "Table 5 disagrees with Table 2", "")
    # duplicate-row test: does a Table 5 2010-11 row equal another district's Table 2 distribution?
    dup = []
    for _, r in q.iterrows():
        other = q[(q.district_id != r.district_id) & ((q.t2_pct_marginal - r.t5_pct_marginal_2010_11).abs() < 0.1)
                  & ((q.t2_pct_small - r.t5_pct_small_2010_11).abs() < 0.1)]
        dup.append(";".join(other.report_name) if len(other) else "")
    q["t5_row_matches_table2_of"] = dup
    q["resolution"] = np.where(q.flag != "", "Feature uses Table 2 (consistent with Table 26); Table 5 value treated as a report error", "")

    write_csv(feat, geo_dir(geo) / "agriculture_census_features.csv")
    write_csv(q, geo_dir(geo) / "agriculture_census_qa.csv")
    write_csv(t26, geo_dir(geo) / "agriculture_census_table26_tahsils.csv")
    return feat
