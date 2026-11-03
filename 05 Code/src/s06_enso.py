"""Step 6 - ENSO yearly features from NOAA CPC ONI (ERSST.v6) and RONI.

Sources: data/raw/enso/oni.ascii.txt, data/raw/enso/RONI.ascii.txt (columns SEAS YR [TOTAL] ANOM).

Episode rule (config: enso_episode_rule, NOAA CPC):
  round the seasonal index to 0.1 degC (halves toward +infinity, as CPC's published tables do);
  warm season = value >= +0.5 within a run of >= 5 consecutive overlapping seasons;
  cold season = value <= -0.5 within a run of >= 5 consecutive overlapping seasons.
The implementation is checked against the saved CPC HTML tables (enso_cpc_table_check.csv).

Monsoon-year rule (config: enso_monsoon_year_rule, PROJECT rule): El Nino monsoon year if JJA and JAS
(the two seasons inside June-September) are both (all_JJA_JAS) or either (any_JJA_JAS) warm-episode seasons.
"""
from __future__ import annotations

import re
from decimal import ROUND_FLOOR, Decimal

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from common import INTERIM, SRC, active, write_csv

SEASONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
FILES = {"ONI_v6": ("oni", "oni_page"), "RONI": ("roni", "roni_page")}


def round_cpc(v: float, decimals: int = 1) -> float:
    q = Decimal(10) ** decimals
    return float((Decimal(str(v)) * q + Decimal("0.5")).to_integral_value(ROUND_FLOOR) / q)


def classify(index: str, cfg: dict) -> pd.DataFrame:
    rule = cfg["decisions"]["enso_episode_rule"]
    d = pd.read_csv(SRC[FILES[index][0]], sep=r"\s+")
    d["season_no"] = d.SEAS.map(SEASONS.index)
    d = d.sort_values(["YR", "season_no"]).reset_index(drop=True)
    d["value_rounded"] = d.ANOM.map(lambda v: round_cpc(v, rule["rounding_decimals"]))
    thr, n = rule["threshold_degC"], rule["min_consecutive_seasons"]
    for name, cond in (("warm", d.value_rounded >= thr), ("cold", d.value_rounded <= -thr)):
        flag = np.zeros(len(d), bool)
        run = 0
        for k, c in enumerate(cond.values):
            run = run + 1 if c else 0
            if run >= n:
                flag[k - run + 1:k + 1] = True
        d[f"{name}_episode"] = flag
    d["index"] = index
    return d


def cpc_table_check(index: str, d: pd.DataFrame) -> pd.DataFrame:
    soup = BeautifulSoup(open(SRC[FILES[index][1]], encoding="utf-8", errors="ignore").read(), "lxml")
    rows = []
    for tr in soup.find_all("tr"):
        th, tds = tr.find("th"), tr.find_all("td")
        first = th.get_text(strip=True) if th else (tds[0].get_text(strip=True) if tds else "")
        cells = tds if th else tds[1:]
        if not (first.isdigit() and len(first) == 4):
            continue
        for i, td in enumerate(cells[:12]):
            sp = td.find("span")
            cls = " ".join(sp.get("class", [])) if sp else ""
            style = (td.get("style") or "") + str(sp.get("style") if sp else "")
            col = "warm" if ("warm" in cls or re.search(r"red|#ff0000", style, re.I)) else (
                "cold" if ("cold" in cls or re.search(r"blue|#0000ff", style, re.I)) else "")
            rows.append({"YR": int(first), "SEAS": SEASONS[i], "cpc_class": col, "cpc_shown": td.get_text(strip=True)})
    p = pd.DataFrame(rows).merge(d, on=["YR", "SEAS"], how="inner")
    p["pipeline_class"] = np.where(p.warm_episode, "warm", np.where(p.cold_episode, "cold", ""))
    p["match"] = p.cpc_class == p.pipeline_class
    p["index"] = index
    return p[["index", "YR", "SEAS", "ANOM", "value_rounded", "cpc_shown", "cpc_class", "pipeline_class", "match"]]


def yearly(d: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    sp = cfg["decisions"]["study_period"]
    piv = d.pivot(index="YR", columns="SEAS", values="ANOM")[SEASONS]
    warm = d.pivot(index="YR", columns="SEAS", values="warm_episode")[SEASONS]
    cold = d.pivot(index="YR", columns="SEAS", values="cold_episode")[SEASONS]
    y = pd.DataFrame(index=piv.index)
    y.index.name = "year"
    y["selected_index"] = d["index"].iloc[0]
    for s in SEASONS:
        y[f"index_{s}"] = piv[s]
    y["monsoon_index_mean_JJA_JAS"] = piv[["JJA", "JAS"]].mean(axis=1)
    y["monsoon_index_max_MJJ_to_SON"] = piv[["MJJ", "JJA", "JAS", "ASO", "SON"]].max(axis=1)
    y["annual_index_mean"] = piv.mean(axis=1)
    y["n_warm_episode_seasons_in_year"] = warm.sum(axis=1)
    y["elnino_monsoon_all_JJA_JAS"] = warm[["JJA", "JAS"]].fillna(False).all(axis=1) & piv[["JJA", "JAS"]].notna().all(axis=1)
    y["elnino_monsoon_any_JJA_JAS"] = warm[["JJA", "JAS"]].fillna(False).any(axis=1)
    y["lanina_monsoon_all_JJA_JAS"] = cold[["JJA", "JAS"]].fillna(False).all(axis=1) & piv[["JJA", "JAS"]].notna().all(axis=1)
    rule = active(cfg, "enso_monsoon_year_rule")
    y["episode_flag"] = y[f"elnino_monsoon_{rule}"]
    y["episode_flag_rule"] = f"NOAA warm episode; monsoon rule {rule}"
    y = y.reset_index()
    y["in_study_period"] = y.year.between(sp["first_year"], sp["last_year"])
    return y


def run(cfg: dict) -> dict:
    out, checks = {}, []
    for index in FILES:
        d = classify(index, cfg)
        checks.append(cpc_table_check(index, d))
        y = yearly(d, cfg)
        write_csv(y, INTERIM / "variants" / f"enso_yearly_features_{index}.csv", 3)
        out[index] = y
    chk = pd.concat(checks)
    write_csv(chk, INTERIM / "enso_cpc_table_check.csv", 3)
    cmp = out["ONI_v6"][["year", "monsoon_index_mean_JJA_JAS", "elnino_monsoon_all_JJA_JAS", "elnino_monsoon_any_JJA_JAS"]].merge(
        out["RONI"][["year", "monsoon_index_mean_JJA_JAS", "elnino_monsoon_all_JJA_JAS", "elnino_monsoon_any_JJA_JAS"]],
        on="year", suffixes=("_ONI_v6", "_RONI"))
    cmp = cmp.rename(columns={"elnino_monsoon_all_JJA_JAS_ONI_v6": "ONI_v6_episode", "elnino_monsoon_all_JJA_JAS_RONI": "RONI_episode"})
    cmp["indices_agree_all_rule"] = cmp.ONI_v6_episode == cmp.RONI_episode
    cmp["indices_agree_any_rule"] = cmp.elnino_monsoon_any_JJA_JAS_ONI_v6 == cmp.elnino_monsoon_any_JJA_JAS_RONI
    sp = cfg["decisions"]["study_period"]
    cmp["in_study_period"] = cmp.year.between(sp["first_year"], sp["last_year"])
    write_csv(cmp, INTERIM / "enso_index_comparison.csv", 3)
    act = active(cfg, "enso_index")
    write_csv(out[act], INTERIM / "enso_yearly_features.csv", 3)
    return out
