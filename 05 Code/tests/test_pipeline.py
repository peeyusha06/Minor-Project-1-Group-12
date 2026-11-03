"""Reproducibility and integrity checks. Run from the project root:  python -m pytest tests -q"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from common import (ENSO_INDICES, GEOGRAPHIES, INTERIM, PALGHAR_LGD, RAW, SRC, THANE, district_ids, district_polygons,  # noqa: E402
                    geo_dir, load_config, rel, sha256, variant_dir)
from feature_registry import REG  # noqa: E402

CFG = load_config()
VARIANTS = [(g, i) for g in GEOGRAPHIES for i in ENSO_INDICES]
SHARE_PREFIXES = ("soc_", "agri_", "irr_", "land_")
N_DISTRICTS = {"A": 35, "B": 36}


def master(geo, index):
    return pd.read_csv(variant_dir(geo, index) / "maharashtra_district_feature_table.csv")


def test_raw_source_hashes_match_manifest():
    man = pd.read_csv(SRC["manifest"]).dropna(subset=["sha256"])
    by_path = dict(zip(man.local_path, man.sha256))
    used = [p for k, p in SRC.items() if str(p).startswith(str(RAW)) and Path(p).is_file() and k != "manifest"]
    used += sorted(SRC["imd_dir"].glob("ind*_rfp25.nc"))
    assert used
    for p in used:
        assert rel(p) in by_path, f"{rel(p)} not in manifest"
        assert sha256(p) == by_path[rel(p)], f"hash changed: {rel(p)}"


@pytest.mark.parametrize("geo,index", VARIANTS)
def test_master_one_row_per_district(geo, index):
    m = master(geo, index)
    assert m.district_id.is_unique
    assert len(m) == N_DISTRICTS[geo]
    assert sorted(m.district_id) == sorted(district_ids(geo))
    assert (m.enso_index == index).all() and (m.geography_version == geo).all()


@pytest.mark.parametrize("geo", GEOGRAPHIES)
def test_rainfall_complete_and_unique(geo):
    sp = CFG["decisions"]["study_period"]
    years = set(range(sp["first_year"], sp["last_year"] + 1))
    a = pd.read_csv(geo_dir(geo) / "district_annual_monsoon_rainfall.csv")
    assert not a.duplicated(["district_id", "year"]).any()
    for d, g in a.groupby("district_id"):
        assert set(g.year) == years, f"district {d} missing years"
    assert a.monsoon_rainfall_mm.notna().all()
    mth = pd.read_csv(geo_dir(geo) / "district_monthly_rainfall.csv")
    assert not mth.duplicated(["district_id", "year", "month"]).any()
    assert len(mth) == N_DISTRICTS[geo] * len(years) * 12
    assert (mth.rainfall_mm >= 0).all()


@pytest.mark.parametrize("geo,index", VARIANTS)
def test_percentages_in_valid_range(geo, index):
    m = master(geo, index)
    cols = [c for c in m.columns if c.startswith(SHARE_PREFIXES) and c.endswith("_pct")]
    assert cols
    for c in cols:
        v = m[c].dropna()
        assert ((v >= 0) & (v <= 100)).all(), c
    for c in ("rain_en_deficient_frequency", "rain_nonen_deficient_frequency"):
        assert m[c].between(0, 1).all(), c


@pytest.mark.parametrize("geo", GEOGRAPHIES)
def test_irrigated_plus_rainfed_equals_cropped(geo):
    """Identity holds exactly except in villages recorded in the QA table (2 of 43,665 in the source)."""
    v = pd.read_csv(geo_dir(geo) / "village_directory_district_features.csv")
    q = pd.read_csv(geo_dir(geo) / "village_directory_qa.csv").set_index("district_id")
    total = v.irrigated_share_of_cropped_land_pct + v.rainfed_share_of_cropped_land_pct
    assert ((total - 100).abs() <= 0.5).all()
    off = v.loc[(total - 100).abs() > 1e-6, "district_id"]
    assert (q.loc[off, "villages_irr_plus_unirr_ne_nas"] > 0).all(), "identity broken in a district with no documented village"
    assert q.villages_irr_plus_unirr_ne_nas.sum() <= 2


def test_village_directory_label_swap_evidence():
    q = pd.read_csv(INTERIM / "village_directory_qa.csv")
    assert q.villages_sources_match_col387.sum() / q.n_villages.sum() > 0.999


@pytest.mark.parametrize("geo,index", VARIANTS)
def test_no_validation_or_2026_in_training_features(geo, index):
    m = master(geo, index)
    banned = ("declared", "gr_", "validation", "2026", "holdout", "revenue_circle")
    assert not [c for c in m.columns if any(b in c.lower() for b in banned)]
    long = pd.read_csv(variant_dir(geo, index) / "district_year_enso_rainfall.csv")
    assert long.year.max() <= CFG["decisions"]["study_period"]["last_year"]
    assert not any("2026" in str(y) for y in m.enso_elnino_years)


@pytest.mark.parametrize("geo", GEOGRAPHIES)
def test_validation_2026_holdout_and_totals(geo):
    v = pd.read_csv(geo_dir(geo) / "drought_validation.csv")
    assert v.holdout_only_2026.all() and (~v.use_in_training).all()
    assert v.declared_talukas_2018.sum() == 151 and v.declared_talukas_2023.sum() == 40 and v.declared_talukas_2026.sum() == 265
    assert v.addl_revenue_circles_2018.sum() == 268 and v.addl_revenue_circles_2023.sum() == 1021
    assert (v.declared_talukas_2026 <= v.total_talukas_census_2011).all()


@pytest.mark.parametrize("geo", GEOGRAPHIES)
def test_all_districts_have_geography_mappings(geo):
    cw = pd.read_csv(INTERIM / "district_crosswalk.csv")
    c = cw[cw.geography_version == geo]
    assert sorted(c.district_id) == sorted(district_ids(geo))
    assert c.district_boundary_id.notna().all() and c.census_2011_district_code.notna().all()
    polys = district_polygons(geo, CFG["decisions"]["boundary_source"]["active"])
    assert sorted(polys.district_id) == sorted(district_ids(geo))
    names = c.set_index("district_id").current_district_name
    assert names[515] == "Chhatrapati Sambhajinagar" and names[522] == "Ahilyanagar" and names[525] == "Dharashiv"


def test_palghar_reconstruction_is_additive():
    a = pd.read_csv(geo_dir("A") / "census_district_features.csv").set_index("district_id")
    b = pd.read_csv(geo_dir("B") / "census_district_features.csv").set_index("district_id")
    for col in ("total_population", "total_workers", "marginal_workers", "agricultural_workers", "st_population"):
        assert b.loc[THANE, col] + b.loc[PALGHAR_LGD, col] == a.loc[THANE, col], col
    assert b.loc[PALGHAR_LGD, "total_population"] == 2990116  # official Census 2011 Palghar population
    va = pd.read_csv(geo_dir("A") / "village_directory_district_features.csv").set_index("district_id")
    vb = pd.read_csv(geo_dir("B") / "village_directory_district_features.csv").set_index("district_id")
    assert vb.loc[THANE, "n_villages"] + vb.loc[PALGHAR_LGD, "n_villages"] == va.loc[THANE, "n_villages"]
    ga = pd.read_csv(geo_dir("A") / "agriculture_census_features.csv").set_index("district_id")
    gb = pd.read_csv(geo_dir("B") / "agriculture_census_features.csv").set_index("district_id")
    assert gb.loc[THANE, "n_holdings_total"] + gb.loc[PALGHAR_LGD, "n_holdings_total"] == ga.loc[THANE, "n_holdings_total"]


def test_agcensus_table2_equals_table26():
    q = pd.read_csv(INTERIM / "agriculture_census_qa.csv")
    assert (q.diff_total_t2_minus_t26 == 0).all() and (q.t26_tahsil_sum_minus_subtotal == 0).all()


def test_enso_rule_reproduces_cpc_tables():
    chk = pd.read_csv(INTERIM / "enso_cpc_table_check.csv")
    assert chk[chk["index"] == "ONI_v6"].match.all()
    mism = chk[~chk.match]
    assert (mism.cpc_class.fillna("") != "warm").all() and (mism.pipeline_class.fillna("") != "warm").all(), "El Nino season mismatch"


def test_registry_documents_every_master_column():
    documented = {r["feature"] for r in REG}
    for g, i in VARIANTS:
        assert set(master(g, i).columns) <= documented
    d = pd.read_csv(INTERIM / "data_dictionary.csv")
    for col in ("feature", "description", "source", "source_file", "year", "geographic_level", "numerator",
                "denominator", "formula", "unit", "missing_value_rule", "notes"):
        assert col in d.columns


def test_active_outputs_match_config():
    geo = CFG["decisions"]["district_geography"]["active"]
    idx = CFG["decisions"]["enso_index"]["active"]
    top = pd.read_csv(INTERIM / "maharashtra_district_feature_table.csv")
    pd.testing.assert_frame_equal(top, master(geo, idx))


def test_mumbai_flagged_not_dropped():
    for g, i in VARIANTS:
        m = master(g, i).set_index("district_id")
        assert 518 in m.index and 519 in m.index
        assert not m.loc[[518, 519], "in_index_scope"].any()
        assert m.loc[[518, 519], "irr_irrigated_share_of_cropped_land_pct"].isna().all()
