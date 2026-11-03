"""Figures and tables for the IEEE paper, drawn ONLY from the fixed project outputs in data/processed/.

Nothing analytical is recomputed: PCA, weights, index, K-Means groups and validation shares are read from CSV files.
Maps reuse map_table(), draw_groups() and draw_continuous() from src/s19_maps.py without titles or footnotes,
because IEEE figures carry their caption below the figure.

Run:  python paper/make_figures.py
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from matplotlib import patheffects  # noqa: E402
from s19_maps import draw_continuous, draw_groups, map_table  # noqa: E402

PROC = ROOT / "data" / "processed"
FIG = ROOT / "paper" / "figures"
TAB = ROOT / "paper" / "tables"
COL = 3.5                                   # IEEE single-column width in inches
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
                     "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "legend.fontsize": 7, "mathtext.fontset": "stix"})
SHORT = {"pca_enso_rain_slope_vulnerability": "ENSO rainfall slope",
         "pca_en_deficient_frequency": "El Niño deficient freq.",
         "pca_agri_worker_share": "Agricultural workers",
         "pca_rainfed_share": "Rainfed share",
         "pca_small_holding_share": "Small holdings",
         "pca_literacy_vulnerability": "Literacy"}


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=600, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote", FIG / name)


def flowchart():
    main = [
        "Data sources\nIMD 0.25° rainfall 1950–2024, NOAA RONI, Census 2011,\nAgriculture Census 2010–11, Survey of India boundaries",
        "Preprocessing\nCode-based district crosswalk (36 districts, 34 in index),\narea-weighted June–September rainfall, El Niño years",
        "Feature construction and selection\nSix indicators: exposure, sensitivity, adaptive capacity",
        "Direction alignment and standardisation\nSlope and literacy × (−1); z-scores (StandardScaler)",
        "PCA (three components retained)\n|loading| × explained-variance indicator weights",
        "Composite index\nV = Σ w·z, rescaled to a relative 0–100 index",
        "K-Means (K = 3) on the 0–100 index\nLow / Medium / High groups ordered by centroid",
        "Maps and dashboard\nSurvey of India district maps, Streamlit app",
    ]
    fig, ax = plt.subplots(figsize=(COL, 4.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    xc, n = 0.355, len(main)
    ys = np.linspace(0.955, 0.045, n)
    box = {"boxstyle": "round,pad=0.35,rounding_size=0.2", "fc": "#f2f2f2", "ec": "black", "lw": 0.6}
    texts = [ax.text(xc, y, t, ha="center", va="center", fontsize=6, linespacing=1.2, bbox=box) for t, y in zip(main, ys)]
    side_box = dict(box, fc="white")
    sens = ax.text(0.855, ys[5], "Sensitivity analysis\nsix alternative\nindex versions", ha="center", va="center",
                   fontsize=5.6, linespacing=1.2, bbox=side_box)
    val = ax.text(0.855, (ys[6] + ys[7]) / 2, "Validation only\ndrought GRs 2018,\n2023 and 2026\n(holdout); never\nused in the index",
                  ha="center", va="center", fontsize=5.6, linespacing=1.2, bbox=dict(side_box, ls="--"))
    fig.canvas.draw()
    inv = ax.transData.inverted()
    ext = [inv.transform(t.get_bbox_patch().get_window_extent()) for t in texts]
    for a, b in zip(ext[:-1], ext[1:]):
        ax.annotate("", (xc, b[1, 1]), (xc, a[0, 1]),
                    arrowprops={"arrowstyle": "-|>", "lw": 0.7, "color": "black", "mutation_scale": 6, "shrinkA": 0, "shrinkB": 0})
    for t, src, ls in ((sens, 5, "-"), (val, 6, "--")):
        e = inv.transform(t.get_bbox_patch().get_window_extent())
        ax.annotate("", (e[0, 0], (e[0, 1] + e[1, 1]) / 2), (ext[src][1, 0], ys[src]) if src == 5 else (ext[src][1, 0], ys[src] - 0.01),
                    arrowprops={"arrowstyle": "-|>", "lw": 0.6, "ls": ls, "color": "black", "mutation_scale": 6,
                                "shrinkA": 0, "shrinkB": 0})
    save(fig, "fig1_methodology.png")


def variance():
    v = pd.read_csv(PROC / "vulnerability_index_components.csv")
    pa = pd.read_csv(PROC / "index_candidates" / "eigenvalues_retention_checks.csv")
    k = np.arange(1, 7)
    fig, ax = plt.subplots(figsize=(COL, 1.9))
    ax.bar(k, v.eigenvalue, color=["#636363"] * 3 + ["#cccccc"] * 3, edgecolor="black", lw=0.5, width=0.6,
           label="Eigenvalue (dark = retained)")
    ax.plot(k, pa.parallel_95pct_random, "k^--", ms=3.5, lw=0.7, label="Parallel analysis, 95th pct.", zorder=1)
    ax.axhline(1, color="black", lw=0.6, ls=":", label="Kaiser criterion (λ = 1)")
    ax.set_xticks(k, [f"PC{i}\n{100 * r:.1f}%" for i, r in zip(k, v.explained_variance_ratio)])
    ax.set_ylabel("Eigenvalue")
    ax.set_ylim(0, 2.45)
    ax.legend(frameon=False, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "fig2_pca_variance.png")


def loadings():
    w = pd.read_csv(PROC / "vulnerability_index_weights.csv")
    L = w[["loading_PC1", "loading_PC2", "loading_PC3"]].to_numpy()
    fig, ax = plt.subplots(figsize=(COL, 1.95))
    im = ax.imshow(L, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    for i in range(L.shape[0]):
        for j in range(L.shape[1]):
            ax.text(j, i, f"{L[i, j]:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(L[i, j]) > 0.6 else "black")
    ax.set_xticks(range(3), ["PC1 (34.3%)", "PC2 (20.8%)", "PC3 (19.4%)"])
    ax.set_yticks(range(6), [f"{SHORT[n]} (w = {x:.3f})" for n, x in zip(w.indicator, w.weight)])
    fig.colorbar(im, ax=ax, shrink=0.9, pad=0.02, label="Loading")
    save(fig, "fig3_pca_loadings.png")


# label offsets (metres, map projection) for districts whose names collide at single-column size
OFFSET = {"Jalna": (12000, 22000), "Chhatrapati Sambhajinagar": (-6000, -12000), "Bhandara": (-4000, -26000),
          "Gondia": (14000, 10000), "Nagpur": (-8000, 6000), "Wardha": (-6000, -8000), "Buldhana": (0, 16000),
          "Dhule": (-6000, -6000), "Nandurbar": (0, 12000), "Akola": (0, 6000)}
NAMES = {"Chhatrapati Sambhajinagar": "Chh. Sambhaji-\nnagar"}


def labels(ax, m, size=4.3):
    for _, r in m[m.in_index].iterrows():
        p = r.geometry.representative_point()
        dx, dy = OFFSET.get(r["name"], (0, 0))
        ax.annotate(NAMES.get(r["name"], r["name"]), (p.x + dx, p.y + dy), ha="center", va="center", fontsize=size,
                    linespacing=0.9, path_effects=[patheffects.withStroke(linewidth=1.5, foreground="white")])


def maps():
    m = map_table()
    fig, ax = plt.subplots(figsize=(COL, 3.0))
    draw_groups(ax, m, labels=False, size=4.3)
    labels(ax, m)
    leg = ax.get_legend()
    leg.set_title("Vulnerability group", prop={"size": 6})
    for t in leg.get_texts():
        t.set_fontsize(5.5)
    save(fig, "fig5_vulnerability_groups_map.png")

    fig, ax = plt.subplots(figsize=(COL, 3.0))
    draw_continuous(ax, m, "vulnerability_index_0_100", "YlOrRd", "Vulnerability index (relative, 0–100)",
                    labels=False, size=4.3)
    labels(ax, m)
    cax = fig.axes[-1]
    cax.tick_params(labelsize=6)
    cax.yaxis.label.set_size(6.5)
    save(fig, "fig4_vulnerability_index_map.png")


def validation():
    val = pd.read_csv(PROC / "drought_validation_districts.csv")
    hold = pd.read_csv(PROC / "drought_validation_holdout_2026.csv")
    summ = pd.read_csv(PROC / "drought_validation_summary.csv")
    rho = {str(r.year): r.spearman_rho for r in summ[summ.role.isin(["historical", "HOLDOUT"])].itertuples()}
    colors = {"Low Vulnerability": "#fee8c8", "Medium Vulnerability": "#fdbb84", "High Vulnerability": "#d7301f"}
    panels = [("2018", val[val.year == 2018]), ("2023", val[val.year == 2023]), ("2026 (holdout)", hold)]
    fig, axes = plt.subplots(1, 3, figsize=(COL, 1.55), sharey=True)
    for ax, (name, d) in zip(axes, panels):
        for g, c in colors.items():
            s = d[d.vulnerability_group == g]
            ax.scatter(s.vulnerability_index_0_100, 100 * s.drought_intensity, s=9, c=c, edgecolors="black",
                       linewidths=0.4, label=g.split()[0])
        ax.set_title(f"{name}\nSpearman ρ = {rho[name[:4]]:.3f}", fontsize=6.5)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        ax.set_xticks([0, 50, 100])
        ax.tick_params(labelsize=6)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Talukas declared (%)", fontsize=6.5)
    axes[1].set_xlabel("Vulnerability index (0–100)", fontsize=6.5)
    axes[2].legend(frameon=False, fontsize=5.5, loc="lower right", handletextpad=0.1, borderaxespad=0.1)
    fig.tight_layout(pad=0.2, w_pad=0.4)
    save(fig, "fig6_validation_scatter.png")


def tables():
    """CSV copies of the paper tables, built from the fixed outputs (for checking the numbers in the text)."""
    TAB.mkdir(parents=True, exist_ok=True)
    pd.read_csv(PROC / "vulnerability_index_components.csv").round(3).to_csv(TAB / "table2_pca_variance.csv", index=False)
    w = pd.read_csv(PROC / "vulnerability_index_weights.csv")
    w[["original_feature", "conceptual_dimension", "sign_multiplier", "loading_PC1", "loading_PC2", "loading_PC3",
       "raw_weight", "weight"]].round(3).to_csv(TAB / "table3_weights.csv", index=False)
    pd.read_csv(PROC / "kmeans_diagnostics.csv").round(3).to_csv(TAB / "table4_kmeans.csv", index=False)
    pd.read_csv(PROC / "drought_validation_summary.csv").round(3).to_csv(TAB / "table6_validation.csv", index=False)
    s = pd.read_csv(PROC / "vulnerability_index_sensitivity.csv").merge(
        pd.read_csv(PROC / "kmeans_sensitivity.csv")[["comparison", "n_changing_group", "changed_districts"]],
        on="comparison", how="left")
    s.round(3).to_csv(TAB / "table5_sensitivity.csv", index=False)
    print("wrote tables to", TAB)


if __name__ == "__main__":
    flowchart()
    variance()
    loadings()
    maps()
    validation()
    tables()
