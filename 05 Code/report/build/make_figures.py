"""Extra figures for the PBL minor project report (the paper figures and maps are reused as they are).

Only reads the fixed project outputs; nothing analytical is recomputed.
  fig_architecture.png   system architecture (layers of the pipeline)
  fig_flowchart.png      flowchart with start/end and decision steps
  fig_monsoon_departure.png  mean district monsoon departure 1950-2024, El Niño years marked
  fig_index_ranking.png  34 districts ranked by the 0-100 index, coloured by K-Means group

Run:  python report/build/make_figures.py
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch, Polygon, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from s19_maps import GROUP_COLORS  # noqa: E402

FIG = ROOT / "report" / "figures"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
                     "font.size": 10, "mathtext.fontset": "stix"})


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=300, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("wrote", FIG / name)


def box(ax, x, y, w, h, text, fc="#f2f2f2", ls="-", size=9, bold_first=True):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.008,rounding_size=0.012",
                                fc=fc, ec="black", lw=1, ls=ls))
    lines = text.split("\n")
    if bold_first:
        ax.text(x, y + (len(lines) - 1) * 0.011, lines[0], ha="center", va="center", fontsize=size, weight="bold")
        if len(lines) > 1:
            ax.text(x, y - 0.011, "\n".join(lines[1:]), ha="center", va="center", fontsize=size - 1, linespacing=1.3)
    else:
        ax.text(x, y, text, ha="center", va="center", fontsize=size, linespacing=1.3)


def arrow(ax, x0, y0, x1, y1, ls="-", text=None):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", lw=1.1, color="black", ls=ls, shrinkA=0, shrinkB=0))
    if text:
        ax.text((x0 + x1) / 2 + 0.01, (y0 + y1) / 2, text, fontsize=8.5, va="center", ha="left")


def architecture():
    fig, ax = plt.subplots(figsize=(7.2, 7.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0.065, 0.995)
    ax.axis("off")
    x0, x1, gap = 0.165, 0.985, 0.014
    cw = (x1 - x0 - 5 * gap) / 6                    # six columns of boxes
    col = [x0 + i * (cw + gap) + cw / 2 for i in range(6)]
    BAND_H, BOX_H = 0.15, 0.105

    def rect(x, y, w, h, fc="white", ls="-", lw=0.8):
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=fc, ec="black", lw=lw, ls=ls))

    def band(y, label, items, cols=None):
        rect(0.5, y, 0.99, BAND_H, lw=1.0)
        rect(0.0755, y, 0.141, BAND_H, fc="#e6e6e6", lw=1.0)
        ax.text(0.0755, y, label, ha="center", va="center", fontsize=9, weight="bold", linespacing=1.2)
        for c, it in zip(cols or range(len(items)), items):
            rect(col[c], y, cw, BOX_H)
            ax.text(col[c], y, it, ha="center", va="center", fontsize=7.8, linespacing=1.2)

    def down(x, y0, y1, ls="-"):
        ax.annotate("", xy=(x, y1), xytext=(x, y0),
                    arrowprops=dict(arrowstyle="-|>", lw=0.9, color="black", ls=ls, shrinkA=0, shrinkB=0))

    Y = [0.91, 0.72, 0.53, 0.34]
    band(Y[0], "Data\nlayer", ["IMD gridded\nrainfall\n(1950–2024)", "NOAA RONI\n(ENSO index)", "Census 2011\nand Village\nDirectory",
                               "Agriculture\nCensus\n2010–11", "Survey of India\nboundaries"])
    rect(col[5], Y[0], cw, BOX_H, ls="--")
    ax.text(col[5], Y[0] + 0.012, "Drought GRs\n2018, 2023,\n2026", ha="center", va="center", fontsize=7.8, linespacing=1.2)
    ax.text(col[5], Y[0] - 0.035, "(validation only)", ha="center", va="center", fontsize=6.5, style="italic")
    band(Y[1], "Processing\nlayer", ["District code\ncrosswalk\n(36 districts)", "Area-weighted\nmonsoon\nrainfall",
                                     "El Niño year\nidentification", "Socioeconomic\nand land\nindicators",
                                     "District\nfeature table"])
    band(Y[2], "Analysis\nlayer", ["Feature\nselection\n(6 indicators)", "Alignment and\nstandardisation", "PCA\nweighting",
                                   "Composite\nindex (0–100)", "K-Means\nclustering\n(K = 3)", "Validation"])
    band(Y[3], "Output\nlayer", ["Index scores\nand weights", "Low / Medium /\nHigh groups", "Sensitivity\nresults",
                                 "Validation\nstatistics", "District maps"])
    rect(0.5, 0.15, 0.99, BAND_H, lw=1.0)
    rect(0.0755, 0.15, 0.141, BAND_H, fc="#e6e6e6", lw=1.0)
    ax.text(0.0755, 0.15, "Presentation\nlayer", ha="center", va="center", fontsize=9, weight="bold", linespacing=1.2)
    rect((x0 + x1) / 2, 0.15, 0.5, BOX_H)
    ax.text((x0 + x1) / 2, 0.15, "Streamlit dashboard: district map, indicator\ncontributions, validation, district comparison",
            ha="center", va="center", fontsize=7.8, linespacing=1.2)

    mid = col[2] + (cw + gap) / 2                    # arrows between bands, centred on the box area
    for ya, yb in zip(Y, Y[1:] + [0.15]):
        down(mid, ya - BAND_H / 2, yb + BAND_H / 2)
    for i in range(5):                               # sequence inside the analysis layer
        ax.annotate("", xy=(col[i + 1] - cw / 2, Y[2]), xytext=(col[i] + cw / 2, Y[2]),
                    arrowprops=dict(arrowstyle="-|>", lw=0.8, color="black", shrinkA=0, shrinkB=0, mutation_scale=7))
    down(col[5], Y[0] - BOX_H / 2, Y[2] + BOX_H / 2, ls="--")
    save(fig, "fig_architecture.png")


def flowchart():
    fig, ax = plt.subplots(figsize=(6.6, 9.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    X, W, H = 0.42, 0.50, 0.04

    def oval(y, t):
        ax.add_patch(FancyBboxPatch((X - 0.13, y - 0.02), 0.26, 0.04, boxstyle="round,pad=0,rounding_size=0.02",
                                    fc="#d9d9d9", ec="black", lw=1))
        ax.text(X, y, t, ha="center", va="center", fontsize=10, weight="bold")

    def diamond(y, t, w=0.44, h=0.075):
        ax.add_patch(Polygon([(X, y + h / 2), (X + w / 2, y), (X, y - h / 2), (X - w / 2, y)], closed=True,
                             fc="#fff2cc", ec="black", lw=1))
        ax.text(X, y, t, ha="center", va="center", fontsize=8.5, linespacing=1.2)

    def step(y, t):
        box(ax, X, y, W, H, t, fc="#f2f2f2", size=8.8, bold_first=False)

    oval(0.975, "Start")
    step(0.905, "Load official raw files\n(IMD, NOAA, Census, Agriculture Census, SOI)")
    diamond(0.82, "Do all sources join\non district codes?")
    box(ax, 0.88, 0.82, 0.22, 0.06, "Fix crosswalk\n(e.g. rebuild Palghar)", fc="white", size=8.3, bold_first=False)
    step(0.735, "Compute monsoon rainfall, El Niño years\nand the six indicators")
    diamond(0.65, "Quality checks\npassed?")
    box(ax, 0.88, 0.65, 0.22, 0.07, "Document issue;\nkeep published values;\nadd sensitivity run", fc="white",
        size=8.3, bold_first=False)
    step(0.565, "Align directions and standardise (z-scores)")
    step(0.495, "PCA: check KMO and Bartlett,\nretain components (Kaiser, OECD-JRC)")
    step(0.425, "Weights from |loadings| × explained variance;\ncomposite index rescaled to 0–100")
    step(0.355, "K-Means (K = 3) on the index\n→ Low / Medium / High groups")
    diamond(0.27, "Ranking stable across\n6 alternative versions?")
    box(ax, 0.88, 0.27, 0.22, 0.06, "Report districts near\ngroup boundaries", fc="white", size=8.3, bold_first=False)
    step(0.185, "Validate against drought GRs\n2018, 2023 and 2026 (holdout)")
    step(0.115, "Draw district maps and run\nthe Streamlit dashboard")
    oval(0.045, "End")

    e = H / 2 + 0.008                        # half box height including the rounded pad
    for a, b in [(0.955, 0.905 + e), (0.905 - e, 0.8575), (0.7825, 0.735 + e), (0.735 - e, 0.6875),
                 (0.6125, 0.565 + e), (0.565 - e, 0.495 + e), (0.495 - e, 0.425 + e), (0.425 - e, 0.355 + e),
                 (0.355 - e, 0.3075), (0.2325, 0.185 + e), (0.185 - e, 0.115 + e), (0.115 - e, 0.065)]:
        arrow(ax, X, a, X, b)
    for y, back_to in [(0.82, 0.905), (0.65, 0.735)]:
        arrow(ax, X + 0.22, y, 0.77, y)
        ax.text(X + 0.235, y + 0.012, "No", fontsize=8.5)
        ax.plot([0.88, 0.88], [y + 0.03 + (0.005 if y == 0.65 else 0), back_to], color="black", lw=1.1)
        arrow(ax, 0.88, back_to, X + W / 2 + 0.008, back_to)
    arrow(ax, X + 0.22, 0.27, 0.77, 0.27)
    ax.text(X + 0.235, 0.282, "No", fontsize=8.5)
    ax.plot([0.88, 0.88], [0.24, 0.185], color="black", lw=1.1)
    arrow(ax, 0.88, 0.185, X + W / 2 + 0.008, 0.185)
    for y in (0.82, 0.65, 0.27):
        ax.text(X + 0.012, y - 0.05, "Yes", fontsize=8.5)
    save(fig, "fig_flowchart.png")


def monsoon_departure():
    e = pd.read_csv(ROOT / "data/interim/enso_yearly_features.csv")
    e = e[(e.year >= 1950) & (e.year <= 2024)]
    rain = pd.read_csv(ROOT / "data/interim/district_annual_monsoon_rainfall.csv")
    scope = pd.read_csv(ROOT / "data/processed/vulnerability_index_scores.csv").district_id
    dep = rain[rain.district_id.isin(scope)].groupby("year").monsoon_departure_pct.mean()
    en = e.elnino_monsoon_all_JJA_JAS.values

    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    ax.bar(dep.index, dep.values, color=["#d7301f" if f else "#bdbdbd" for f in en], width=0.8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("Monsoon rainfall departure (%)")
    ax.set_xlabel("Year")
    ax.legend(handles=[Patch(color="#d7301f", label="El Niño year"), Patch(color="#bdbdbd", label="Other year")],
              fontsize=9, loc="lower right", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "fig_monsoon_departure.png")


def index_ranking():
    k = pd.read_csv(ROOT / "data/processed/kmeans_vulnerability_classification.csv")
    k = k.sort_values("vulnerability_index_0_100")
    col = {"Low Vulnerability": GROUP_COLORS[0], "Medium Vulnerability": GROUP_COLORS[1],
           "High Vulnerability": GROUP_COLORS[2]}
    fig, ax = plt.subplots(figsize=(6.4, 7.6))
    ax.barh(k.current_district_name, k.vulnerability_index_0_100, color=k.vulnerability_group.map(col),
            edgecolor="#555555", lw=0.5)
    for y, v in enumerate(k.vulnerability_index_0_100):
        ax.text(v + 1, y, f"{v:.1f}", va="center", fontsize=7.5)
    ax.set_xlim(0, 110)
    ax.set_xlabel("Relative vulnerability index (0–100)")
    ax.tick_params(axis="y", labelsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(handles=[Patch(fc=col[g], ec="#555555", label=g) for g in reversed(list(col))], loc="lower right",
              fontsize=8.5, frameon=False)
    ax.margins(y=0.01)
    save(fig, "fig_index_ranking.png")


if __name__ == "__main__":
    architecture()
    flowchart()
    monsoon_departure()
    index_ranking()
