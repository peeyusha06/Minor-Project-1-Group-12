"""One page project report (DOCX/PDF) and poster (PPTX/PDF) for the PBL submission.

The one page report follows "Copy of PBL one page report.pdf" and the poster follows "Poster.pptx format.pdf" (both in
the PBL folder): same headings, order, fonts and colours, with the year changed to 2026-27. The text is a shortened
version of the project report; all numbers come from the fixed results.

Run:  python report/build/make_onepage_poster.py
"""
import sys
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Pt as PPt

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
ROOT = OUT.parent
FIG = OUT / "figures"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "paper" / "build"))
from build_paper import runs_of  # noqa: E402
from build_report import FONT, GUIDE, STUDENTS, TITLE, borders, para, to_pdf  # noqa: E402
from references import REFS  # noqa: E402

NAMES = ", ".join(n for n, _, _ in STUDENTS)
REF_KEYS = ["pai2014", "noaaroni", "swami2021", "oecd2008"]

INTRO = ("El Niño years often bring a weak monsoon and drought to Maharashtra, but how badly a district is hurt "
         "depends on how much it relies on rainfed farming and how well it can cope. This project builds a relative "
         "El Niño drought vulnerability index for 34 districts of Maharashtra. Two El Niño rainfall indicators, "
         "derived from 75 years of IMD gridded rainfall and NOAA's Relative Oceanic Niño Index (RONI), are combined "
         "with four agricultural and socioeconomic indicators from the Census 2011 and the Agriculture Census. "
         "Principal component analysis (PCA) gives the indicator weights, K-Means clustering groups the districts "
         "into Low, Medium and High vulnerability, and the result is checked against government drought declarations "
         "and shown in maps and an interactive Streamlit dashboard.")
OBJECTIVES = [
    "To collect and integrate official district-level climatic and socioeconomic data for Maharashtra, and to derive "
    "El Niño-specific rainfall indicators from 75 years of IMD rainfall and NOAA's RONI.",
    "To construct a PCA-weighted composite El Niño drought vulnerability index on a 0 to 100 scale for 34 districts.",
    "To classify the districts into Low, Medium and High vulnerability groups with K-Means clustering, and to validate "
    "the results against Government of Maharashtra drought declarations.",
    "To present the index and groups through district maps and an interactive Streamlit dashboard."]
SOFTWARE = ["Programming language: Python 3.12",
            "Data handling and statistics: pandas, NumPy, SciPy, xarray, netCDF4",
            "Machine learning: scikit-learn (StandardScaler, PCA, K-Means)",
            "Maps and dashboard: GeoPandas, Matplotlib, Streamlit",
            "Development tools: VS Code, pytest, Git, GitHub."]
CONCLUSION = ("The project gives a transparent and reproducible ranking of El Niño drought vulnerability for the "
              "districts of Maharashtra. Vulnerability is highest in Marathwada and the dry interior, where El Niño "
              "rainfall losses meet rainfed farming and lower literacy: 10 districts are in the High group, 20 in "
              "Medium and 4 in Low. The index agrees moderately with the drought declarations of 2018 (Spearman "
              "ρ = 0.585), 2023 (0.450) and 2026 (0.545), and it can support drought preparedness planning when an "
              "El Niño is forecast.")
ABSTRACT = INTRO
BACKGROUND = ("Kharif agriculture in Maharashtra depends on the June to September monsoon, and El Niño conditions in "
              "the Pacific have often weakened it. In 13 of the 18 El Niño years since 1950 the average monsoon of the "
              "study districts was below normal (Figure 1). Rainfall alone does not show who suffers most: on average "
              "64.9% of workers in these districts depend on agriculture and 81.2% of the net sown area is rainfed. "
              "Existing district studies mostly use expert or equal weights, do not link exposure to El Niño and are "
              "rarely checked against official drought records.")
METHOD = [("Official data from seven sources (IMD rainfall, NOAA RONI, Census 2011, Village Directory, Agriculture "
           "Census, Survey of India boundaries and drought declarations) are joined on district codes (Figure 2)."),
          ("Six indicators are derived: ENSO rainfall slope, El Niño deficient-monsoon frequency, agricultural-worker "
           "share, rainfed share, small-holding share and literacy. They are aligned so that a higher value means "
           "more vulnerability, and standardised."),
          ("PCA keeps three components (74.5% of the variance). Indicator weights come from the absolute loadings, "
           "and the weighted sum is rescaled to a 0 to 100 index. K-Means (K = 3) then forms the Low, Medium and High "
           "groups. The drought declarations are used only at the end, for validation.")]
RESULTS = ("The six weights lie between 0.151 and 0.183. Beed is the most vulnerable district (100) and Nagpur the "
           "least (0). K-Means places 10 districts in the High group, 20 in Medium and 4 in Low (silhouette 0.587), "
           "and seven of the eight Marathwada districts are High (Figure 3). The index agrees with the share of "
           "talukas declared drought-affected in 2018 (Spearman ρ = 0.585), 2023 (0.450) and the 2026 holdout "
           "(0.545), and the ranking stays stable across six alternative methods (ρ = 0.934 to 0.995).")
POSTER_CONCLUSION = ("The project gives a transparent, reproducible ranking of El Niño drought vulnerability for "
                     "Maharashtra. Vulnerability is highest in Marathwada and the dry interior, where El Niño rainfall "
                     "losses meet rainfed farming and lower literacy. The index can support drought preparedness "
                     "planning when an El Niño is forecast.")
ACHIEVEMENT = "Paper submitted to the journal Geographical Research (Wiley), October 2026 (under review)."
ACK = "This project was guided by Prof. Pankaj Deshmukh and supported by K. J. Somaiya Institute of Technology."


# ---------------------------------------------------------------- one page report -----------------------------------
def runs(p, text, size):
    for s, b, it, _ in runs_of(text):
        r = p.add_run(s)
        r.font.size, r.bold, r.italic = Pt(size), b or None, it or None


def one_page():
    doc = docx.Document()
    st = doc.styles["Normal"]
    st.font.name, st.font.size = FONT, Pt(12)
    st.paragraph_format.space_after = Pt(0)
    s = doc.sections[0]
    s.page_width, s.page_height = Inches(8.27), Inches(11.69)
    s.left_margin = s.right_margin = Inches(1.0)
    s.top_margin, s.bottom_margin = Inches(0.8), Inches(0.8)
    C = WD_ALIGN_PARAGRAPH.CENTER
    p = para(doc, align=C, after=10)
    p.add_run().add_picture(str(FIG / "logo_onepage_header.png"), width=Inches(4.6))
    para(doc, "Academic Year 2026-27 ( ODD SEM)", 13, True, align=C, after=12)
    para(doc, "DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND DATA SCIENCE", 13, True, align=C, after=14)
    para(doc, "Project Based Learning Minor Project 1", 16, align=C, after=18)
    para(doc, "One Page Project Report", 16, True, align=C, after=6)
    para(doc, f"Title: {TITLE}", after=6, line=1.15)
    para(doc, "Project No. 12", after=6)
    para(doc, f"Guide: {GUIDE}", after=8)
    t = doc.add_table(rows=1, cols=3)
    borders(t)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for col, w in zip(t.columns, (0.7, 1.1, 4.4)):
        col.width = Inches(w)
    for row, vals in enumerate([("Sr.No.", "Roll No.", "Name of Student")]
                               + [(str(i), roll, name) for i, (name, roll, _) in enumerate(STUDENTS, 1)]):
        cells = t.rows[0].cells if row == 0 else t.add_row().cells
        for c, v, w in zip(cells, vals, (0.7, 1.1, 4.4)):
            c.width = Inches(w)
            c.paragraphs[0].alignment = C if row else WD_ALIGN_PARAGRAPH.LEFT
            c.paragraphs[0].add_run(v).font.size = Pt(12)
    para(doc, after=8)
    body = dict(align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=8, line=1.15)
    para(doc, f"Introduction: {INTRO}", **body)
    para(doc, "Objectives:", after=4)
    for i, o in enumerate(OBJECTIVES, 1):
        p = para(doc, f"{i}.\t{o}", align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=2, line=1.15)
        p.paragraph_format.left_indent, p.paragraph_format.first_line_indent = Inches(0.6), Inches(-0.25)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(0.6))
    para(doc, "Flow diagram:", before=8, after=6)
    p = para(doc, align=C, after=8)
    p.add_run().add_picture(str(FIG / "fig_flowchart.png"), width=Inches(2.6))
    para(doc, "Software:", after=6)
    for i, sw in enumerate(SOFTWARE, 1):
        para(doc, f"{i}. {sw}", after=3)
    para(doc, f"Conclusion: {CONCLUSION}", before=10, **body)
    para(doc, "References:", before=10, after=8)
    for i, k in enumerate(REF_KEYS[:3], 1):
        p = para(doc, after=5)
        runs(p, f"[{i}] {REFS[k][0]}", 12)
    out = OUT / "One Page Report.docx"
    doc.save(out)
    to_pdf(out, OUT)


# ---------------------------------------------------------------- poster ---------------------------------------------
PT_PER_PX = 1701 / 896                      # the template PDF was measured at 896 px wide
RED, HEAD, DARK, BRIGHT = (RGBColor(0xC0, 0, 0), RGBColor(0xA0, 0x15, 0x15), RGBColor(0xB7, 0x1F, 0x2E),
                           RGBColor(0xEC, 0x1A, 0x23))
BODY, H2, CAP = 22, 34, 18
TNR = {False: "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
       True: "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"}


def n_lines(text, size, width_pt, bold=False):
    """Lines the text wraps to in a box width_pt wide (greedy word wrap with the real font widths)."""
    font = ImageFont.truetype(TNR[bold], size * 4)
    lines, cur = 1, ""
    for w in text.replace("*", "").split():
        trial = f"{cur} {w}".strip()
        if font.getlength(trial) / 4 > width_pt and cur:
            lines, cur = lines + 1, w
        else:
            cur = trial
    return lines


class Column:
    """Stacks headings, text and figures down one poster column; y is the next free position in points."""

    def __init__(self, slide, x, y, w):
        self.s, self.x, self.y, self.w = slide, x, y, w

    def text(self, text, size=BODY, bold=False, color=None, align=PP_ALIGN.JUSTIFY, after=10, bullet=False,
             italic=False):
        inner = self.w - 14 - (34 if bullet else 0)
        h = n_lines(text, size, inner, bold) * size * 1.2 + 10
        box = self.s.shapes.add_textbox(PPt(self.x), PPt(self.y), PPt(self.w), PPt(h))
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = PPt(7)
        tf.margin_top = tf.margin_bottom = PPt(2)
        p = tf.paragraphs[0]
        p.alignment = align
        if bullet:
            box.left, box.width = PPt(self.x + 34), PPt(self.w - 34)
            dot = self.s.shapes.add_textbox(PPt(self.x), PPt(self.y), PPt(34), PPt(size * 1.3))
            dot.text_frame.margin_left = PPt(7)
            r = dot.text_frame.paragraphs[0].add_run()
            r.text, r.font.size, r.font.name = "●", PPt(size * 0.8), FONT
        for s, b, it, _ in runs_of(text):
            r = p.add_run()
            r.text = s
            r.font.size, r.font.name, r.font.bold, r.font.italic = PPt(size), FONT, bold or b, italic or it
            if color:
                r.font.color.rgb = color
        self.y += h + after

    def heading(self, text):
        self.text(text, H2, True, HEAD, PP_ALIGN.LEFT, after=4)

    def figure(self, path, width, caption):
        w, h = Image.open(path).size
        height = width * h / w
        self.s.shapes.add_picture(str(path), PPt(self.x + (self.w - width) / 2), PPt(self.y), PPt(width),
                                  PPt(height))
        self.y += height + 8
        self.text(caption, CAP, align=PP_ALIGN.CENTER, after=18, italic=True)


def rect(slide, x, y, w, h, color):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, PPt(x), PPt(y), PPt(w), PPt(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return sh


def centred(slide, y, h, text, size, bold, color=None):
    box = slide.shapes.add_textbox(PPt(0), PPt(y), PPt(1701), PPt(h))
    tf = box.text_frame
    tf.word_wrap, tf.vertical_anchor = True, MSO_ANCHOR.TOP
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text, r.font.size, r.font.bold, r.font.name = line, PPt(size), bold, FONT
        if color:
            r.font.color.rgb = color


def poster():
    prs = Presentation()
    prs.slide_width, prs.slide_height = PPt(1701), PPt(2551)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    px = lambda v: v * PT_PER_PX  # noqa: E731
    # header, as in the template
    s.shapes.add_picture(str(FIG / "logo_somaiya_vidyavihar.jpg"), PPt(px(10)), PPt(px(36)), height=PPt(px(48)))
    s.shapes.add_picture(str(FIG / "logo_trust.png"), PPt(px(795)), PPt(px(28)), height=PPt(px(58)))
    centred(s, 22, 150, "K. J. SOMAIYA INSTITUTE OF\nTECHNOLOGY", 54, True, RED)
    centred(s, 168, 50, "Department of  Artificial Intelligence and Data Science", 36, True, RED)
    rect(s, 0, px(122), 1701, 6, RED)
    centred(s, 262, 140, TITLE.replace(" to El Niño", "\nto El Niño"), 50, True)
    centred(s, 408, 90, f"{NAMES}\nGuide: {GUIDE}", 34, False)
    top = 520
    rect(s, px(37), top, px(862) - px(37), 6, RED)
    rect(s, px(445), top, 6, px(1305) - top, RED)
    rect(s, px(863), px(1165), 1701 - px(863), 2551 - px(1165), DARK)
    rect(s, px(475), px(1307), 1701 - px(475), 2551 - px(1307), DARK)
    rect(s, px(475), px(1307), px(48), 2551 - px(1307), BRIGHT)

    left = Column(s, 90, top + 40, px(420) - 90)
    left.heading("Abstract")
    left.text(ABSTRACT)
    left.heading("Background")
    left.text(BACKGROUND)
    left.figure(FIG / "fig_monsoon_departure.png", left.w - 30,
                "Figure 1: Average June to September rainfall departure of the 34 districts, 1950 to 2024 "
                "(El Niño years in red)")
    left.heading("Objectives")
    for o in OBJECTIVES:
        left.text(o, bullet=True, after=4)
    left.y += 10
    left.heading("Methodology")
    for m in METHOD:
        left.text(m, after=8)

    right = Column(s, px(470), top + 40, px(850) - px(470))
    right.figure(FIG / "fig_architecture.png", 390, "Figure 2: System architecture of the vulnerability mapping system")
    right.heading("Result and Discussion")
    right.text(RESULTS)
    right.figure(ROOT / "paper" / "figures" / "fig5_vulnerability_groups_map.png", 500,
                 "Figure 3: K-Means vulnerability groups of the 34 districts")
    right.heading("Conclusion")
    right.text(POSTER_CONCLUSION)
    right.heading("Achievements")
    right.text(ACHIEVEMENT)
    right.heading("Acknowledgement")
    right.text(ACK)
    right.heading("References")
    for i, k in enumerate(REF_KEYS[:3], 1):
        right.text(f"[{i}] {REFS[k][0]}", 18, after=4)
    print("left ends", left.y, "right ends", right.y, "limit", px(1300))
    for col, limit in ((left, px(1300)), (right, px(1300))):
        assert col.y < limit, f"poster column overflows by {col.y - limit:.0f} pt"
    out = OUT / "Poster.pptx"
    prs.save(out)
    to_pdf(out, OUT)


if __name__ == "__main__":
    one_page()
    poster()
    print("wrote One Page Report and Poster in", OUT)
