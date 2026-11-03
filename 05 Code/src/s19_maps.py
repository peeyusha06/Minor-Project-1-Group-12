"""Step 19 - Maharashtra district maps from the FIXED outputs (nothing analytical is recomputed).

Boundaries: Survey of India OVSF/1M/8, layer 27/MAHARASHTRA_DISTRICT_BDY (36 districts), native Lambert Conformal
Conic projection. Join key: DIST_LGD (integer) = district_id used throughout the project. No name matching.
Mumbai City (519) and Mumbai Suburban (518) are drawn grey and hatched: not included in the index.

Outputs (outputs/maps/):
  maharashtra_vulnerability_groups.png, maharashtra_vulnerability_index.png,
  maharashtra_drought_2018.png, maharashtra_drought_2023.png, maharashtra_drought_2026_holdout.png,
  maharashtra_index_vs_2026.png

Run:  python src/s19_maps.py   (after s18)
"""
import matplotlib

matplotlib.use("Agg")                       # write PNG files without opening windows
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import patheffects  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from common import ROOT, SRC, soi_layer  # noqa: E402

OUT = ROOT / "outputs" / "maps"
PROC = ROOT / "data" / "processed"
MUMBAI = {518, 519}
GROUPS = ["Low Vulnerability", "Medium Vulnerability", "High Vulnerability"]
GROUP_COLORS = ["#fee8c8", "#fdbb84", "#d7301f"]   # ColorBrewer OrRd, 3 classes (colour-blind safe)
GREY = "#d9d9d9"
BOUNDARY_NOTE = "Boundaries: Survey of India, Administrative Boundary Database OVSF/1M/8 (Maharashtra)."
MUMBAI_NOTE = "Grey hatched: Mumbai City and Mumbai Suburban - not included in index (no agricultural/landholding data)."


def map_table():
    """36 district polygons joined by district_id to the fixed index, groups and declaration shares."""
    g = soi_layer("DISTRICT_BDY")[["DIST_LGD", "DISTRICT", "geometry"]].copy()
    g["district_id"] = g.DIST_LGD.astype(int)
    assert len(g) == 36 and g.district_id.is_unique and g.is_valid.all() and not g.is_empty.any()
    ref = pd.read_csv(SRC["district_reference"])[["current_lgd_district_code", "current_district_name"]]
    idx = pd.read_csv(PROC / "vulnerability_index_scores.csv")[["district_id", "vulnerability_index_0_100"]]
    grp = pd.read_csv(PROC / "kmeans_vulnerability_classification.csv")[["district_id", "vulnerability_group"]]
    val = pd.read_csv(PROC / "drought_validation_districts.csv")
    hold = pd.read_csv(PROC / "drought_validation_holdout_2026.csv")

    m = g.merge(ref.rename(columns={"current_lgd_district_code": "district_id", "current_district_name": "name"}),
                on="district_id", how="left", validate="one_to_one")
    m = m.merge(idx, on="district_id", how="left", validate="one_to_one")
    m = m.merge(grp, on="district_id", how="left", validate="one_to_one")
    for year, d in ((2018, val[val.year == 2018]), (2023, val[val.year == 2023]), (2026, hold)):
        d = d[["district_id", "drought_intensity"]].rename(columns={"drought_intensity": f"declared_share_{year}"})
        m = m.merge(d, on="district_id", how="left", validate="one_to_one")

    # join checks: every in-scope district has exactly one value, the two Mumbai districts have none
    assert m.name.notna().all() and len(m) == 36
    in_scope = m.vulnerability_index_0_100.notna()
    assert in_scope.sum() == 34 and set(m.district_id[~in_scope]) == MUMBAI
    for c in ["vulnerability_group", "declared_share_2018", "declared_share_2023", "declared_share_2026"]:
        assert (m[c].notna() == in_scope).all(), c
    assert m.vulnerability_group.value_counts().to_dict() == {"Medium Vulnerability": 20, "High Vulnerability": 10,
                                                               "Low Vulnerability": 4}
    assert m.vulnerability_index_0_100.min() == 0 and m.vulnerability_index_0_100.max() == 100
    m["in_index"] = in_scope
    return m


def label(name):
    return name.replace(" ", "\n") if len(name) > 12 else name


def draw_base(ax, m, labels=True, size=6.5):
    """Grey hatched Mumbai districts, district outlines and (optionally) district names."""
    m[~m.in_index].plot(ax=ax, color=GREY, hatch="////", edgecolor="#636363", linewidth=0.4)
    m.boundary.plot(ax=ax, color="#4d4d4d", linewidth=0.5)
    ax.set_axis_off()
    if labels:
        for _, r in m[m.in_index].iterrows():
            p = r.geometry.representative_point()
            ax.annotate(label(r["name"]), (p.x, p.y), ha="center", va="center", fontsize=size,
                        path_effects=[patheffects.withStroke(linewidth=2, foreground="white")])
    mum = m[~m.in_index].geometry.union_all().centroid
    ax.annotate("Mumbai City &\nMumbai Suburban\n(not in index)", (mum.x, mum.y), xytext=(mum.x - 170000, mum.y - 60000),
                fontsize=size, ha="center", arrowprops={"arrowstyle": "-", "color": "#636363", "lw": 0.6})


def draw_groups(ax, m, labels=True, size=6.5):
    for grp, col in zip(GROUPS, GROUP_COLORS):
        m[m.vulnerability_group == grp].plot(ax=ax, color=col)
    draw_base(ax, m, labels, size)
    handles = [Patch(facecolor=c, edgecolor="#4d4d4d", label=f"{g} ({(m.vulnerability_group == g).sum()})")
               for g, c in zip(GROUPS, GROUP_COLORS)]
    handles.append(Patch(facecolor=GREY, hatch="////", edgecolor="#636363", label="Not included in index"))
    ax.legend(handles=handles, loc="lower right", fontsize=8, frameon=True, title="Vulnerability group", title_fontsize=9)


def draw_continuous(ax, m, column, cmap, legend_label, labels=True, size=6.5, legend=True):
    m[m.in_index].plot(ax=ax, column=column, cmap=cmap, vmin=0, vmax=100, legend=legend,
                       legend_kwds={"label": legend_label, "shrink": 0.55, "pad": 0.01})
    draw_base(ax, m, labels, size)


def save(fig, ax, title, notes, name):
    ax.set_title(title, fontsize=14, fontweight="bold", loc="left")
    fig.text(0.02, 0.015, "\n".join(notes + [BOUNDARY_NOTE, MUMBAI_NOTE]), fontsize=7.5, va="bottom", color="#333333")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", OUT / name)


def main():
    m = map_table()
    for year in (2018, 2023, 2026):
        m[f"declared_pct_{year}"] = 100 * m[f"declared_share_{year}"]

    fig, ax = plt.subplots(figsize=(11, 9))
    draw_groups(ax, m)
    save(fig, ax, "El Niño drought vulnerability groups - Maharashtra districts",
         ["Groups: K-Means (K = 3) on the final 0-100 vulnerability index; clusters ordered by centroid (Low < Medium < High).",
          "Groups are relative to the 34 in-scope districts; they are not drought predictions."],
         "maharashtra_vulnerability_groups.png")

    fig, ax = plt.subplots(figsize=(11, 9))
    draw_continuous(ax, m, "vulnerability_index_0_100", "YlOrRd", "Vulnerability index (0 = lowest, 100 = highest observed)")
    save(fig, ax, "El Niño drought vulnerability index (0-100) - Maharashtra districts",
         ["Index: PCA-weighted sum of six standardised, direction-aligned indicators, rescaled 0-100 across the 34 in-scope districts.",
          "Values are relative to these 34 districts (0 = lowest observed, 100 = highest observed)."],
         "maharashtra_vulnerability_index.png")

    declared = "Government-declared share of each district's talukas (Census 2011 taluka count); not a direct measure of crop loss or rainfall."
    drought_maps = [
        (2018, "Drought declaration 2018 - share of talukas declared (severe + moderate)",
         ["Source: Government of Maharashtra GR 31-10-2018 (151 talukas). " + declared],
         "maharashtra_drought_2018.png"),
        (2023, "Drought declaration 2023 - share of talukas declared (severe + moderate)",
         ["Source: Government of Maharashtra GR 31-10-2023 (40 talukas). " + declared,
          "Shows the main-order taluka declarations only; the 1,021 separately listed revenue-circle declarations (GR 10-11-2023) are not included."],
         "maharashtra_drought_2023.png"),
        (2026, "2026 Trigger-1 holdout - share of talukas declared",
         ["Source: Government of Maharashtra GR 25-09-2026 (265 talukas, Trigger-1). " + declared,
          "Trigger-1 is an earlier, rainfall-led stage, not a final severe/moderate declaration. 19 of 34 districts have 100% of talukas",
          "declared, so this map has a ceiling effect and separates districts less well."],
         "maharashtra_drought_2026_holdout.png"),
    ]
    for year, title, notes, name in drought_maps:
        fig, ax = plt.subplots(figsize=(11, 9))
        draw_continuous(ax, m, f"declared_pct_{year}", "Blues", f"% of talukas declared ({year})")
        save(fig, ax, title, notes, name)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17, 7.5))
    draw_groups(a1, m, size=5.5)
    a1.set_title("Vulnerability group (fixed index, K-Means K = 3)", fontsize=11, loc="left")
    draw_continuous(a2, m, "declared_pct_2026", "Blues", "", size=5.5, legend=False)
    # one colour bar attached to both panels keeps the two maps the same size
    bar = plt.cm.ScalarMappable(norm=plt.Normalize(0, 100), cmap="Blues")
    fig.colorbar(bar, ax=[a1, a2], shrink=0.5, pad=0.01, label="% of talukas declared (2026 Trigger-1)")
    a2.set_title("2026 Trigger-1 holdout: share of talukas declared", fontsize=11, loc="left")
    fig.suptitle("Vulnerability groups vs 2026 drought declarations (holdout)", fontsize=14, fontweight="bold", x=0.02, ha="left")
    fig.text(0.02, 0.01, "Index and groups were fixed before the 2026 declarations were examined. Spearman rho (index vs 2026 share) = 0.55, n = 34.\n"
             "2026 is a Trigger-1 stage with many districts at 100% (ceiling effect). " + BOUNDARY_NOTE + "\n" + MUMBAI_NOTE,
             fontsize=7.5, va="bottom", color="#333333")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "maharashtra_index_vs_2026.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", OUT / "maharashtra_index_vs_2026.png")


if __name__ == "__main__":
    main()
