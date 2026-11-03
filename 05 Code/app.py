"""Streamlit dashboard - presentation layer only. It READS the fixed project outputs and never recomputes
the index, weights, K-Means groups or drought measures.

Run:  streamlit run app.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from s19_maps import GROUP_COLORS, GROUPS, draw_continuous, draw_groups, map_table  # noqa: E402

PROC = ROOT / "data" / "processed"
REQUIRED = [PROC / f for f in (
    "vulnerability_index_scores.csv", "vulnerability_index_weights.csv", "vulnerability_index_components.csv",
    "kmeans_vulnerability_classification.csv", "drought_validation_districts.csv",
    "drought_validation_holdout_2026.csv", "drought_validation_summary.csv")] + [
    ROOT / "data" / "raw" / "boundaries" / "survey_of_india" / "SOI_OVSF_1M_8_Maharashtra_upto_taluk.zip"]

# display names and units for the six fixed indicators (keys = columns of vulnerability_index_scores.csv)
INDICATORS = {
    "pca_enso_rain_slope_vulnerability": ("El Niño rainfall sensitivity", "% change in monsoon rain per +1 °C RONI"),
    "pca_en_deficient_frequency": ("El Niño deficient-monsoon frequency", "% of El Niño monsoons ≤ −20%"),
    "pca_agri_worker_share": ("Agricultural-worker share", "% of workers"),
    "pca_rainfed_share": ("Rainfed share of cropped land", "% of cropped land"),
    "pca_small_holding_share": ("Small-holding share", "% of holdings < 2 ha"),
    "pca_literacy_vulnerability": ("Literacy (aligned: lower literacy = greater vulnerability)", "% literate, age 7+"),
}


def load_tables():
    """Read every fixed output once. Joins use district_id only."""
    scores = pd.read_csv(REQUIRED[0])
    weights = pd.read_csv(REQUIRED[1])
    groups = pd.read_csv(REQUIRED[3])
    hist = pd.read_csv(REQUIRED[4])
    hold = pd.read_csv(REQUIRED[5])
    summary = pd.read_csv(REQUIRED[6])
    districts = scores.merge(groups[["district_id", "vulnerability_group"]], on="district_id", validate="one_to_one")
    assert len(districts) == 34 and districts.district_id.is_unique
    assert list(weights.indicator) == list(INDICATORS)
    geo = map_table()                              # same 36 SOI polygons and checks as the report maps
    assert len(geo) == 36 and geo.vulnerability_index_0_100.notna().sum() == 34
    return {"districts": districts, "weights": weights, "hist": hist, "hold": hold, "summary": summary, "geo": geo}


def indicator_table(row, weights):
    """Six indicators for one district: value in natural units, z-score, fixed weight and contribution."""
    out = []
    for _, w in weights.iterrows():
        name, unit = INDICATORS[w.indicator]
        value = row[w.indicator] * w.sign_multiplier          # undo the direction alignment for display only
        if w.indicator == "pca_en_deficient_frequency":
            value *= 100
        z = row["z_" + w.indicator.removeprefix("pca_")]
        out.append({"Indicator": name, "District value": round(value, 1), "Unit": unit,
                    "Dimension": w.conceptual_dimension, "PCA weight": round(w.weight, 3),
                    "Standardised (z)": round(z, 2), "Contribution (weight × z)": round(w.weight * z, 3)})
    return pd.DataFrame(out)


def district_map(geo, view, selected_id):
    fig, ax = plt.subplots(figsize=(9, 7.2))
    if view == "Vulnerability group":
        draw_groups(ax, geo, size=6)
    else:
        draw_continuous(ax, geo, "vulnerability_index_0_100", "YlOrRd", "Relative vulnerability index (0–100)", size=6)
    geo[geo.district_id == selected_id].boundary.plot(ax=ax, color="#08306b", linewidth=2.2)
    fig.tight_layout()
    return fig


def main():
    st.set_page_config(page_title="Maharashtra El Niño Drought Vulnerability", layout="wide")
    missing = [p for p in REQUIRED if not p.exists()]
    if missing:
        st.error("Required project file(s) missing - run the pipeline first:\n\n" +
                 "\n".join(f"- `{p.relative_to(ROOT)}`" for p in missing))
        st.stop()

    data = st.cache_resource(load_tables)()
    d, weights, geo = data["districts"], data["weights"], data["geo"]

    st.title("AI-Driven Vulnerability Index Mapping for Districts in Maharashtra to El Niño Droughts Using Socio-Economic and Climatic PCA")
    st.caption("District-level composite vulnerability index using climatic, agricultural and socioeconomic indicators "
               "· 34 in-scope Maharashtra districts · RONI · 1950–2024")

    names = d.sort_values("current_district_name").current_district_name.tolist()
    left, right = st.columns([3, 2])

    with right:
        st.subheader("Select a district")
        name = st.selectbox("District", names, index=names.index("Beed"), label_visibility="collapsed")
        row = d[d.current_district_name == name].iloc[0]
        color = GROUP_COLORS[GROUPS.index(row.vulnerability_group)]
        st.markdown(
            f"<div style='border:1px solid #bbb;border-left:10px solid {color};padding:12px 16px;border-radius:6px'>"
            f"<div style='font-size:1.5rem;font-weight:700'>{name}</div>"
            f"<div>Relative vulnerability index</div><div style='font-size:2.2rem;font-weight:700'>"
            f"{row.vulnerability_index_0_100:.1f} / 100</div>"
            f"<div>Vulnerability group: <b>{row.vulnerability_group}</b></div></div>", unsafe_allow_html=True)
        st.caption("Relative to the 34 in-scope districts (0 = lowest observed, 100 = highest observed). "
                   "Not a probability and not a predicted drought risk.")
        counts = d.vulnerability_group.value_counts()
        st.markdown("**Districts per group:** " + " · ".join(f"{g.split()[0]}: {counts[g]}" for g in GROUPS))

    with left:
        st.subheader("Maharashtra vulnerability map")
        view = st.radio("View", ["Vulnerability group", "Vulnerability index (0–100)"], horizontal=True)
        st.pyplot(district_map(geo, view, int(row.district_id)))
        st.caption("Selected district outlined in dark blue. Grey hatched: Mumbai City and Mumbai Suburban - "
                   "not included in index. Boundaries: Survey of India OVSF/1M/8.")

    st.divider()
    st.subheader(f"Six underlying indicators - {name}")
    table = indicator_table(row, weights)
    st.dataframe(table, hide_index=True, width="stretch")
    assert np.isclose(table["Contribution (weight × z)"].sum(), row.raw_vulnerability_score, atol=0.01)
    st.caption(f"Contributions add up to the district's raw score ({row.raw_vulnerability_score:.3f}); "
               "positive = pushes the district above the Maharashtra average. The 0–100 index is this raw score rescaled.")

    st.subheader("Why the score looks this way")
    st.write("The vulnerability index combines six direction-aligned indicators. PCA was used to obtain relative "
             "statistical weights, and the weighted standardized indicators were combined into a composite score from 0 to 100.")
    wt = pd.DataFrame({"Indicator": [INDICATORS[i][0] for i in weights.indicator], "Dimension": weights.conceptual_dimension,
                       "PCA weight": weights.weight.round(3), "Weight (%)": weights.percentage_weight.round(1)})
    st.dataframe(wt, hide_index=True, width="stretch")
    st.warning("The index is relative to the 34 in-scope Maharashtra districts. It is an exploratory composite index, "
               "not a causal model or a probability of drought.")

    st.divider()
    st.subheader(f"Drought validation - {name}")
    st.info("Government-declared taluka share is used as a validation indicator. It was not used to build the vulnerability index.")
    h = data["hist"][data["hist"].district_id == row.district_id].set_index("year")
    o = data["hold"][data["hold"].district_id == row.district_id].iloc[0]
    c1, c2, c3 = st.columns(3)
    for col, year, r, note in (
            (c1, "2018", h.loc[2018], "Final declaration (severe + moderate), GR 31-10-2018."),
            (c2, "2023", h.loc[2023], "Main-order taluka declarations shown; separately listed revenue-circle declarations are "
                                      "not included because no verified district-level revenue-circle denominator was available."),
            (c3, "2026 Trigger-1 holdout", o, "Trigger-1 is an earlier rainfall-led declaration stage and is used as a holdout check.")):
        with col:
            st.markdown(f"**{year}**")
            st.markdown(f"<div style='font-size:1.8rem;font-weight:700;color:#08519c'>{100 * r.drought_intensity:.0f}%</div>"
                        f"<div>of talukas declared ({int(r.declared_talukas)} of {int(r.total_talukas_census_2011)})</div>",
                        unsafe_allow_html=True)
            st.caption(note)

    st.subheader("Validation summary (all 34 districts)")
    s = data["summary"]
    s = s[s.drought_measure.str.startswith("declared taluka share")]
    st.dataframe(pd.DataFrame({"Year": ["2018", "2023", "2026 holdout"],
                               "Spearman rho": s.spearman_rho.round(3).to_numpy(),
                               "p-value": s.spearman_p_two_sided.map(lambda p: f"{p:.4f}").to_numpy(),
                               "Districts": s.n_districts.to_numpy()}), hide_index=True)
    st.write("Across all three validation years, higher vulnerability index values were positively associated with "
             "larger government-declared taluka shares.")

    st.divider()
    st.subheader("Compare two districts")
    a, b = st.columns(2)
    name_a = a.selectbox("District A", names, index=names.index("Beed"))
    name_b = b.selectbox("District B", names, index=names.index("Nagpur"))
    ra = d[d.current_district_name == name_a].iloc[0]
    rb = d[d.current_district_name == name_b].iloc[0]
    ta, tb = indicator_table(ra, weights), indicator_table(rb, weights)
    comp = pd.DataFrame({"": ["Relative vulnerability index (0–100)", "Vulnerability group"] + list(ta.Indicator),
                         name_a: [f"{ra.vulnerability_index_0_100:.1f}", ra.vulnerability_group] +
                                 [f"{v} {u}" for v, u in zip(ta["District value"], ta.Unit)],
                         name_b: [f"{rb.vulnerability_index_0_100:.1f}", rb.vulnerability_group] +
                                 [f"{v} {u}" for v, u in zip(tb["District value"], tb.Unit)]})
    if name_a == name_b:
        comp = comp.iloc[:, :2]
    st.dataframe(comp, hide_index=True, width="stretch")

    with st.expander("Methodology"):
        st.markdown(
            "Raw data (IMD gridded rainfall, NOAA RONI, Census 2011, Agriculture Census 2010-11)  \n"
            "↓ Six selected indicators  \n↓ Direction alignment (higher = more vulnerable)  \n↓ Standardization  \n"
            "↓ PCA (first 3 components)  \n↓ PCA-derived weights  \n↓ Vulnerability Index (0–100)  \n↓ K-Means (K = 3)  \n"
            "↓ Low / Medium / High  \n↓ Validation against drought declarations (2018, 2023, 2026 holdout)\n\n"
            "Maharashtra, 34 in-scope districts (Mumbai City and Mumbai Suburban excluded: no agricultural data) · "
            "ENSO index: NOAA RONI · study period 1950–2024 · rainfall baseline 1971–2020. "
            "Details: `reports/final_vulnerability_index_report.md`, `reports/kmeans_classification_report.md`, "
            "`reports/drought_validation_report.md`.")


if __name__ == "__main__":
    main()
