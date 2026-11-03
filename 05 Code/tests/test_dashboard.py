import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import REQUIRED, indicator_table, load_tables  # noqa: E402

PROC = ROOT / "data" / "processed"
data = load_tables()
scores = pd.read_csv(PROC / "vulnerability_index_scores.csv").set_index("district_id")


def digest():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in REQUIRED if p.suffix == ".csv"}


def test_loaded_tables_match_fixed_outputs():
    d = data["districts"].set_index("district_id")
    assert len(d) == 34
    assert np.allclose(d.vulnerability_index_0_100, scores.loc[d.index, "vulnerability_index_0_100"])
    assert d.vulnerability_group.value_counts().to_dict() == {"Low Vulnerability": 4, "Medium Vulnerability": 20,
                                                               "High Vulnerability": 10}
    geo = data["geo"]
    assert len(geo) == 36 and geo[geo.district_id.isin([518, 519])].vulnerability_index_0_100.isna().all()


def test_six_weights_and_indicator_values():
    w = pd.read_csv(PROC / "vulnerability_index_weights.csv")
    assert np.allclose(data["weights"].weight, w.weight) and len(w) == 6
    row = data["districts"].set_index("current_district_name").loc["Nandurbar"]
    t = indicator_table(row, data["weights"])
    assert list(t["PCA weight"]) == list(w.weight.round(3))
    assert np.isclose(t.loc[0, "District value"], -7.4)          # slope shown in original units (aligned 7.43 x -1)
    assert np.isclose(t.loc[5, "District value"], 64.4)          # literacy shown as % literate
    assert np.isclose(t["Contribution (weight × z)"].sum(), row.raw_vulnerability_score, atol=0.01)


def test_app_runs_and_shows_fixed_values_for_selected_districts():
    before = digest()
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not at.exception
    hist = pd.read_csv(PROC / "drought_validation_districts.csv")
    hold = pd.read_csv(PROC / "drought_validation_holdout_2026.csv")
    for name in ("Nagpur", "Beed", "Pune", "Hingoli"):
        at.selectbox[0].select(name).run()
        assert not at.exception
        did = scores.index[scores.current_district_name == name][0]
        page = " ".join(m.value for m in at.markdown)
        assert f"{scores.loc[did, 'vulnerability_index_0_100']:.1f} / 100" in page
        for year in (2018, 2023):
            r = hist[(hist.year == year) & (hist.district_id == did)].iloc[0]
            assert f"{100 * r.drought_intensity:.0f}%" in page and f"({r.declared_talukas} of {r.total_talukas_census_2011})" in page
        r = hold[hold.district_id == did].iloc[0]
        assert f"({r.declared_talukas} of {r.total_talukas_census_2011})" in page
    at.radio[0].set_value("Vulnerability index (0–100)").run()
    assert not at.exception
    assert digest() == before                                     # the dashboard never writes the analytical CSVs
