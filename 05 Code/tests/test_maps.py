import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from s19_maps import OUT, map_table  # noqa: E402

m = map_table()
MAPS = ["maharashtra_vulnerability_groups.png", "maharashtra_vulnerability_index.png", "maharashtra_drought_2018.png",
        "maharashtra_drought_2023.png", "maharashtra_drought_2026_holdout.png", "maharashtra_index_vs_2026.png"]


def test_36_boundary_districts_one_row_each():
    assert len(m) == 36 and m.district_id.is_unique and m.geometry.notna().all()
    assert 681 in set(m.district_id) and 517 in set(m.district_id)          # Palghar separate from Thane


def test_34_index_and_group_records_matched():
    assert m.vulnerability_index_0_100.notna().sum() == 34
    assert m.vulnerability_group.notna().sum() == 34
    for c in ("declared_share_2018", "declared_share_2023", "declared_share_2026"):
        assert m[c].notna().sum() == 34


def test_mumbai_has_no_index_or_group():
    mum = m[m.district_id.isin([518, 519])]
    assert len(mum) == 2
    assert mum[["vulnerability_index_0_100", "vulnerability_group", "declared_share_2026"]].isna().all().all()


def test_fixed_values_unchanged_on_the_map():
    assert m.vulnerability_group.value_counts().to_dict() == {"Low Vulnerability": 4, "Medium Vulnerability": 20,
                                                               "High Vulnerability": 10}
    assert m.vulnerability_index_0_100.min() == 0 and m.vulnerability_index_0_100.max() == 100


def test_map_files_are_png_images():
    for name in MAPS:
        f = OUT / name
        assert f.exists() and f.stat().st_size > 50_000, name
        assert f.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", name
