"""Step 2 - district features from the Census 2011 Primary Census Abstract (PCA).

Source: data/raw/census/2011-IndiaStateDistSbDistTwnWrd-0000.xlsx, sheet 'Data'.
Rows used: State = 27, Level = DISTRICT (TRU = Total/Rural/Urban). For geography B the
Palghar district is rebuilt from the 8 Level = SUB-DISTRICT rows listed in
common.PALGHAR_SUBDISTRICTS, and present-day Thane = Census 2011 Thane minus Palghar.
"""
from __future__ import annotations

import pandas as pd

from common import PALGHAR_LGD, PALGHAR_SUBDISTRICTS, SRC, THANE, geo_dir, write_csv

# raw PCA column -> analytical count name (TRU = Total unless stated)
COUNT_COLUMNS = {
    "No_HH": "households",
    "TOT_P": "total_population",
    "P_06": "population_0_6",
    "P_LIT": "literates",
    "TOT_WORK_P": "total_workers",
    "MAINWORK_P": "main_workers",
    "MARGWORK_P": "marginal_workers",
    "NON_WORK_P": "non_workers",
    "MAIN_CL_P": "main_cultivators",
    "MARG_CL_P": "marginal_cultivators",
    "MAIN_AL_P": "main_agricultural_labourers",
    "MARG_AL_P": "marginal_agricultural_labourers",
    "P_SC": "sc_population",
    "P_ST": "st_population",
}

# (feature, numerator, denominator, formula) - evaluated on the count table
DERIVED = [
    ("literacy_rate_7plus_pct", "literates", "population_7plus", "literates / (total_population - population_0_6) * 100"),
    ("rural_population_share_pct", "rural_population", "total_population", "rural_population / total_population * 100"),
    ("work_participation_rate_pct", "total_workers", "total_population", "total_workers / total_population * 100"),
    ("non_worker_share_pct", "non_workers", "total_population", "non_workers / total_population * 100"),
    ("agri_worker_share_of_workers_pct", "agricultural_workers", "total_workers", "(cultivators + agricultural_labourers) / total_workers * 100"),
    ("agri_worker_share_of_population_pct", "agricultural_workers", "total_population", "(cultivators + agricultural_labourers) / total_population * 100"),
    ("cultivator_share_of_workers_pct", "cultivators", "total_workers", "cultivators / total_workers * 100"),
    ("agri_labourer_share_of_workers_pct", "agricultural_labourers", "total_workers", "agricultural_labourers / total_workers * 100"),
    ("marginal_worker_share_of_workers_pct", "marginal_workers", "total_workers", "marginal_workers / total_workers * 100"),
    ("marginal_workers_per_population_pct", "marginal_workers", "total_population", "marginal_workers / total_population * 100  (5-district prototype definition)"),
    ("sc_share_pct", "sc_population", "total_population", "sc_population / total_population * 100"),
    ("st_share_pct", "st_population", "total_population", "st_population / total_population * 100"),
]


def load_pca() -> pd.DataFrame:
    df = pd.read_excel(SRC["census_pca"], sheet_name="Data",
                       dtype={"State": str, "District": str, "Subdistt": str, "Town/Village": str, "Ward": str, "EB": str})
    return df[df.State == "27"].copy()


def _counts(rows: pd.DataFrame) -> pd.Series:
    """Sum raw counts over the given rows for Total, plus Rural/Urban population."""
    tot = rows[rows.TRU == "Total"][list(COUNT_COLUMNS)].sum().rename(COUNT_COLUMNS)
    tot["rural_population"] = rows.loc[rows.TRU == "Rural", "TOT_P"].sum()
    tot["urban_population"] = rows.loc[rows.TRU == "Urban", "TOT_P"].sum()
    return tot


def district_counts(pca: pd.DataFrame, geo: str) -> pd.DataFrame:
    dist = pca[pca.Level == "DISTRICT"]
    out = {int(code): _counts(g) for code, g in dist.groupby("District")}
    if geo == "B":
        sub = pca[(pca.Level == "SUB-DISTRICT") & (pca.District == str(THANE)) & (pca.Subdistt.isin(PALGHAR_SUBDISTRICTS))]
        assert sub.Subdistt.nunique() == 8, "expected 8 Palghar sub-districts"
        palghar = _counts(sub)
        out[PALGHAR_LGD] = palghar
        out[THANE] = out[THANE] - palghar
    c = pd.DataFrame(out).T
    c.index.name = "district_id"
    c = c.reset_index().astype({"district_id": int})
    c["cultivators"] = c.main_cultivators + c.marginal_cultivators
    c["agricultural_labourers"] = c.main_agricultural_labourers + c.marginal_agricultural_labourers
    c["agricultural_workers"] = c.cultivators + c.agricultural_labourers
    c["population_7plus"] = c.total_population - c.population_0_6
    return c


def derive(c: pd.DataFrame) -> pd.DataFrame:
    f = c.copy()
    for name, num, den, _ in DERIVED:
        f[name] = f[num] / f[den] * 100
    return f


def checks(c: pd.DataFrame) -> pd.DataFrame:
    q = pd.DataFrame({"district_id": c.district_id})
    q["main_plus_marginal_equals_total_workers"] = (c.main_workers + c.marginal_workers) == c.total_workers
    q["workers_plus_nonworkers_equals_population"] = (c.total_workers + c.non_workers) == c.total_population
    q["rural_plus_urban_equals_total"] = (c.rural_population + c.urban_population) == c.total_population
    return q


def run(pca: pd.DataFrame, geo: str) -> pd.DataFrame:
    c = district_counts(pca, geo)
    f = derive(c)
    q = checks(c)
    assert q.drop(columns="district_id").all().all(), q[~q.drop(columns="district_id").all(axis=1)]
    cols = ["district_id"] + [v for v in COUNT_COLUMNS.values()] + [
        "rural_population", "urban_population", "population_7plus", "cultivators",
        "agricultural_labourers", "agricultural_workers"] + [d[0] for d in DERIVED]
    f = f[cols].sort_values("district_id")
    write_csv(f, geo_dir(geo) / "census_district_features.csv")
    write_csv(q, geo_dir(geo) / "census_consistency_checks.csv")
    return f


def prototype_denominator_comparison(f: pd.DataFrame) -> pd.DataFrame:
    """Shows why the prototype's 'Marginal_Worker_Share_pct' was mislabelled."""
    cols = ["district_id", "marginal_workers", "total_workers", "total_population",
            "marginal_workers_per_population_pct", "marginal_worker_share_of_workers_pct"]
    return f[cols].copy()
