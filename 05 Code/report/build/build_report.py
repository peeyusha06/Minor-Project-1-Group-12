"""Build the PBL minor project report (DOCX, then PDF via LibreOffice) from report_content.md.

Follows the college report format PDF (cover page, certificate, table of contents, ten
chapters) with the year changed to 2026-27, and the TruthLens sample report for chapter layout. The front pages keep the
format's font sizes, alignment and logos (logos extracted unchanged from the format PDF). Chapter text is Times New
Roman 12 pt, chapter headings 16 pt, section headings 14 pt.

Equations and IEEE references are reused from the paper build (paper/build). The table of contents page numbers are
filled from a first PDF pass.

Run:  python report/build/build_report.py
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from PIL import Image, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
ROOT = OUT.parent
sys.path.insert(0, str(ROOT / "paper" / "build"))
from build_paper import EQ, M, W, runs_of  # noqa: E402
from references import REFS  # noqa: E402

FIG = OUT / "figures"
NAME = "PBL Minor Project 1 Report 2026-27 - El Nino Drought Vulnerability"
TITLE = "AI-Driven Vulnerability Index Mapping for Districts in Maharashtra to El Niño Droughts Using Socio-Economic and Climatic PCA"
STUDENTS = [("Tanishq Mewada", "34", "26255067"), ("Saad Patel", "47", "26255089"), ("Peeyusha Patki", "48", "26255090")]  # roll, seat no.
GUIDE = "Prof. Pankaj Deshmukh"
TOC_LABELS = ["Introduction", "Aim & Objective", "Literature Survey", "Social Impact/Effect of Problem", "System Design",
              "Flow Chart", "System Implementation", "Results and Analysis", "Conclusion", "References"]  # as in the format
FONT = "Times New Roman"
PAGE_W, PAGE_H = 8.27, 11.69                   # A4
TEXT_W = PAGE_W - 2 * 0.875
DECK = ROOT / "Final PPT.pptx"                  # final presentation deck (backup slides removed)
DECK_SLIDES = 28
ABBR = [("AHP", "Analytic Hierarchy Process"), ("AI", "Artificial Intelligence"),
        ("CPC", "Climate Prediction Center"), ("CSV", "Comma-Separated Values"),
        ("ENSO", "El Niño-Southern Oscillation"), ("EVR", "Explained-Variance Ratio"),
        ("GIS", "Geographic Information System"), ("GMM", "Gaussian Mixture Model"),
        ("GR", "Government Resolution"), ("IMD", "India Meteorological Department"),
        ("IPCC", "Intergovernmental Panel on Climate Change"), ("JRC", "Joint Research Centre"),
        ("KMO", "Kaiser-Meyer-Olkin measure"), ("ML", "Machine Learning"),
        ("NetCDF", "Network Common Data Form"), ("NOAA", "National Oceanic and Atmospheric Administration"),
        ("OECD", "Organisation for Economic Co-operation and Development"), ("ONI", "Oceanic Niño Index"),
        ("PC", "Principal Component"), ("PCA", "Principal Component Analysis"),
        ("RONI", "Relative Oceanic Niño Index"), ("SHA", "Secure Hash Algorithm"),
        ("SPEI", "Standardised Precipitation Evapotranspiration Index"), ("SPI", "Standardised Precipitation Index"),
        ("YAML", "YAML Ain't Markup Language")]
PUBLICATIONS = [  # status as of November 2026
    "P. Deshmukh and P. Patki, “Socioeconomic and Climatic Vulnerability to El Niño Droughts in Maharashtra,” "
    "paper submitted to the journal *Geographical Research* (Wiley), October 2026 (under review)."]
ANNEXURES = ("Annexure I: Source Code", "List of Publications", "Annexure II: Presentation Slides")  # guide's order
CODE = [("s13_pca_primary.py", "principal component analysis"),
        ("s16_vulnerability_index.py", "PCA weights and the 0 to 100 index"),
        ("s17_kmeans_classification.py", "K-Means grouping"),
        ("s18_drought_validation.py", "validation against drought declarations")]  # core modules only
ROMAN = "i ii iii iv v vi vii viii ix x xi xii".split()


# ---------------------------------------------------------------- helpers -------------------------------------------
def para(doc_or_cell, text="", size=12, bold=False, italic=False, align=None, before=0, after=0, line=None,
         underline=False):
    p = doc_or_cell.add_paragraph()
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    if line:
        pf.line_spacing = line
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        r.font.size, r.bold, r.italic, r.underline = Pt(size), bold, italic, underline
    return p


def add_runs(p, text, size=12, italic_all=False):
    for s, b, it, vert in runs_of(text):
        r = p.add_run(s)
        r.font.size = Pt(size)
        r.bold = b or None
        r.italic = (it or italic_all) or None
        if vert == "subscript":
            r.font.subscript = True
        elif vert == "superscript":
            r.font.superscript = True


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def borders(table, on=True):
    v = "single" if on else "nil"
    xml = (f'<w:tblBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           + "".join(f'<w:{e} w:val="{v}" w:sz="4" w:space="0" w:color="000000"/>'
                     for e in ("top", "left", "bottom", "right", "insideH", "insideV"))
           + "</w:tblBorders>")
    table._tbl.tblPr.append(parse_xml(xml))


def no_split(row):
    row._tr.get_or_add_trPr().append(parse_xml(
        '<w:cantSplit xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))


def picture(doc, path, width=None, height=None, align=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=0):
    p = para(doc, align=align, before=before, after=after)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=width and Inches(width), height=height and Inches(height))
    return p


# ---------------------------------------------------------------- citations -----------------------------------------
def number_citations(text):
    order = []
    for grp in re.findall(r"\[(@[^\]]+)\]", text):
        for k in [x.strip()[1:] for x in grp.split(";")]:
            if k not in REFS:
                raise KeyError(f"unknown reference key {k}")
            if k not in order:
                order.append(k)
    num = {k: i + 1 for i, k in enumerate(order)}

    def repl(m):
        ns = sorted(num[x.strip()[1:]] for x in m.group(1).split(";"))
        return ", ".join(f"[{n}]" for n in ns)
    return re.sub(r"\[(@[^\]]+)\]", repl, text), order


# ---------------------------------------------------------------- front pages ---------------------------------------
def cover(doc):
    C = WD_ALIGN_PARAGRAPH.CENTER
    para(doc, "K J Somaiya Institute of Technology", 22, True, align=C, after=10)
    para(doc, "An Autonomous Institute Permanently Affiliated to University of Mumbai.", 14, True, align=C, after=17)
    para(doc, "A Project Based Learning", 14, True, align=C, after=17)
    para(doc, "Report On", 14, True, align=C, after=12)
    picture(doc, FIG / "logo_mu_cover.png", width=2.12, height=1.45, after=14)
    p = para(doc, align=C, after=0)
    for t, s in (("“", 22), (TITLE, 22), ("”", 22)):
        r = p.add_run(t)
        r.font.size, r.bold = Pt(s), True
    para(doc, "SUBMITTED BY", 13, True, align=C, before=2, after=12)
    for name, roll, _ in STUDENTS:
        para(doc, f"{name} --(TY A {roll})", 16, True, align=C, after=14)
    para(doc, "Guide", 13, True, align=C, before=26, after=12)
    para(doc, GUIDE, 16, True, align=C, after=12)
    para(doc, "Department of Artificial Intelligence and Data Science", 16, True, align=C, after=12)
    para(doc, "2026-27", 16, True, align=C)
    page_break(doc)


def certificate(doc):
    C = WD_ALIGN_PARAGRAPH.CENTER
    t = doc.add_table(rows=1, cols=2)
    borders(t, False)
    left, right = t.rows[0].cells
    left.paragraphs[0].add_run().add_picture(str(FIG / "logo_mu.png"), width=Inches(0.98), height=Inches(1.07))
    right.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    right.paragraphs[0].add_run().add_picture(str(FIG / "logo_somaiya.png"), width=Inches(1.04), height=Inches(0.96))
    para(doc, "K J Somaiya Institute of Technology", 22, True, align=C, before=18, after=20)
    para(doc, "UNIVERSITY OF MUMBAI", 14, True, align=C, after=28)
    para(doc, "CERTIFICATE", 14, True, align=C, after=12)
    body = dict(size=13, align=WD_ALIGN_PARAGRAPH.LEFT, line=Pt(22))
    para(doc, f"This is to certify that the project titled “{TITLE}” is completed under my supervision and guidance "
              "in partial fulfilment of the requirements of the course Project Based Learning - Minor Project 1, "
              "by the following students:", after=10, **body)
    for name, _, seat in STUDENTS:
        para(doc, f"{name}--({seat})", 16, True, align=C, after=12)
    para(doc, "The course is a part of semester V of the Department of Artificial Intelligence and Data Science "
              "during the academic year 2026-2027. The said work has been assessed and is found to be satisfactory.",
         before=4, **body)
    p = para(doc, "(Internal guide name and sign.)\t(External Examiner name and sign.)", 14, before=80)
    p.paragraph_format.tab_stops.add_tab_stop(Pt(255))
    p = para(doc, "College seal", 14, before=50)
    p.paragraph_format.left_indent = Pt(175)


def dotted_list(doc, title, header, rows, first_w=0.9, bold_top=True):
    """Borderless two-column table: number | text, dot leader and page number. rows are (number, text, level,
    page); level 0 rows are bold (when bold_top), deeper levels are indented. The page number shares the text's
    paragraph because LibreOffice draws no leader for a tab at the end of a paragraph."""
    para(doc, title, 16, True, underline=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)
    widths = (first_w, TEXT_W - first_w)
    t = doc.add_table(rows=0, cols=2)
    borders(t, False)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for col, w in zip(t.columns, widths):
        col.width = Inches(w)
    for i, (num, text, level, page) in enumerate([(header[0], header[1], 0, header[2])] + rows):
        tr = t.add_row()
        no_split(tr)
        if i == 0:
            tr._tr.get_or_add_trPr().append(parse_xml(f"<w:tblHeader {W}/>"))
        bold = i == 0 or bold_top and level == 0
        left, right = tr.cells
        left.width, right.width = Inches(widths[0]), Inches(widths[1])
        for c in (left, right):
            c.paragraphs[0].paragraph_format.space_before = c.paragraphs[0].paragraph_format.space_after = Pt(3)
        lp = left.paragraphs[0]
        lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = lp.add_run(num)
        r.font.size, r.bold = Pt(12), bold or None
        rp = right.paragraphs[0]
        rp.paragraph_format.left_indent = Inches(0.35 * level) if level else None
        rp.paragraph_format.right_indent = Inches(0.6)          # wrapped titles stay clear of the page column
        rp.paragraph_format.tab_stops.add_tab_stop(Inches(widths[1] - 0.2), WD_TAB_ALIGNMENT.RIGHT,
                                                   WD_TAB_LEADER.SPACES if i == 0 else WD_TAB_LEADER.DOTS)
        r = rp.add_run(text)
        r.font.size, r.bold = Pt(12), bold or None
        r = rp.add_run(f"\t{page}")
        r.font.size, r.bold = Pt(12), (i == 0) or None


def toc_rows(text, pages):
    """Table of contents rows: front lists, chapters with their numbered sections, references and annexures."""
    rows = [("", name, 0, pages.get(name, "")) for name in ("List of Figures", "List of Tables",
                                                            "List of Abbreviations")]
    ch = 0
    for hashes, head in re.findall(r"^(#{1,3}) (.+)$", text, re.M):
        if len(hashes) == 1:
            ch += 1
            rows.append((str(ch), TOC_LABELS[ch - 1], 0, pages.get(ch, "")))
        else:
            rows.append(("", head, len(hashes) - 1, pages.get(head, "")))
    rows.append((str(ch + 1), TOC_LABELS[ch], 0, pages.get(ch + 1, "")))
    rows += [("", a, 0, pages.get(a, "")) for a in ANNEXURES]
    return rows


def captions(text):
    """(number, short title) of every figure and table, in order; the title stops at the first full stop."""
    figs = re.findall(r"^!\[Figure ([\d.]+): (.*?)\]\(", text, re.M)
    tabs = re.findall(r"^TABLE: Table ([\d.]+): (.*)$", text, re.M)
    short = lambda s: re.split(r"(?<=[a-z0-9)])\. ", s)[0].rstrip(".")  # noqa: E731
    return [(n, short(s)) for n, s in figs], [(n, short(s)) for n, s in tabs]


def front_lists(doc, text, pages):
    figs, tabs = captions(text)
    dotted_list(doc, "Table of Contents", ("Sr. No.", "Content", "Page No."), toc_rows(text, pages))
    page_break(doc)
    dotted_list(doc, "List of Figures", ("Figure No.", "Title", "Page No."),
                [(n, s, 0, pages.get(f"Figure {n}", "")) for n, s in figs], 1.1, False)
    page_break(doc)
    dotted_list(doc, "List of Tables", ("Table No.", "Title", "Page No."),
                [(n, s, 0, pages.get(f"Table {n}", "")) for n, s in tabs], 1.1, False)
    page_break(doc)
    para(doc, "List of Abbreviations", 16, True, underline=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)
    t = doc.add_table(rows=0, cols=2)
    borders(t, False)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (a, full) in enumerate([("Abbreviation", "Full Form")] + ABBR):
        cells = t.add_row().cells
        for c, v, w in zip(cells, (a, full), (1.6, TEXT_W - 1.6)):
            c.width = Inches(w)
            p = c.paragraphs[0]
            p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(3)
            r = p.add_run(v)
            r.font.size, r.bold = Pt(12), (i == 0) or None


# ---------------------------------------------------------------- body ----------------------------------------------
def heading(doc, text, first):
    num, rest = text.split(" ", 1)
    p = para(doc, f"{num} {rest.upper()}", 16, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=18)
    p.paragraph_format.page_break_before = not first


def subheading(doc, text):
    p = para(doc, text, 14, True, before=12, after=6)
    p.paragraph_format.keep_with_next = True


def body_par(doc, text, indent=0.0, after=8, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = para(doc, align=align, after=after, line=1.5)
    p.paragraph_format.left_indent = Inches(indent) if indent else None
    add_runs(p, text)
    return p


def list_item(doc, text, marker, after=4):
    p = para(doc, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=after, line=1.5)
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.25)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(0.5))
    add_runs(p, f"{marker}\t{text}")


def equation(doc, label, n):
    p = para(doc, after=6, before=2)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_W / 2), WD_TAB_ALIGNMENT.CENTER)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_W), WD_TAB_ALIGNMENT.RIGHT)
    p.add_run("\t")
    omml = EQ[label][1].replace("Cambria Math", FONT)      # keep the whole report in Times New Roman
    p._p.append(parse_xml(f"<m:oMath {M} {W}>{omml}</m:oMath>"))
    r = p.add_run(f"\t({n})")
    r.font.size = Pt(12)


def bordered(path, width, tmp):
    """Copy of the image with a little white margin and a thin black frame (about 0.75 pt at the printed width)."""
    im = Image.open(path).convert("RGB")
    ppi = im.width / width
    pad, line = round(ppi * 0.06), max(1, round(ppi * 0.75 / 72))
    framed = Image.new("RGB", (im.width + 2 * (pad + line), im.height + 2 * (pad + line)), "black")
    framed.paste(Image.new("RGB", (im.width + 2 * pad, im.height + 2 * pad), "white"), (line, line))
    framed.paste(im, (line + pad, line + pad))
    out = Path(tmp) / Path(path).name
    framed.save(out, dpi=(ppi, ppi))
    return out


def figure(doc, caption, path, width):
    with tempfile.TemporaryDirectory() as tmp:
        picture(doc, bordered((HERE / path).resolve(), width, tmp), width=width, before=6, after=4)
    p = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)
    add_runs(p, caption)


FONTS = Path("/System/Library/Fonts/Supplemental")


def word_width(word, size, bold):
    """Printed width of a word in inches (Times New Roman)."""
    f = ImageFont.truetype(str(FONTS / f"Times New Roman{' Bold' if bold else ''}.ttf"), size * 10)
    return f.getlength(word) / 720


def column_widths(rows, size, pad):
    """Each column is at least as wide as its longest word (lines also break after hyphens); the rest of the text
    width is shared in proportion to the longest cell. Returns None when the words alone do not fit."""
    ncol = len(rows[0])
    minw = [max(word_width(w, size, i == 0) for i, r in enumerate(rows) for w in re.split(r"(?<=-)|\s+", r[j]) if w)
            + 2 * pad + 0.03 for j in range(ncol)]
    if sum(minw) > TEXT_W:
        return None
    lens = [min(max(len(r[j]) for r in rows), 45) for j in range(ncol)]
    return [m + (TEXT_W - sum(minw)) * n / sum(lens) for m, n in zip(minw, lens)]


def table(doc, caption, rows, note):
    """Table with its caption underneath. Wide tables (the literature summary) use the largest of 10, 9 or 8 pt
    at which no word has to be split, with narrower cell padding."""
    ncol = len(rows[0])
    wide = ncol >= 7
    pad = 0.04 if wide else 0.08
    size, widths = next((sz, w) for sz in ((10, 9, 8) if wide else (12, 11, 10))
                        if (w := column_widths(rows, sz, pad)))
    para(doc, after=2)
    t = doc.add_table(rows=0, cols=ncol)
    borders(t)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    if wide:
        m = round(pad * 1440)
        t._tbl.tblPr.append(parse_xml(f'<w:tblCellMar {W}><w:left w:w="{m}" w:type="dxa"/>'
                                      f'<w:right w:w="{m}" w:type="dxa"/></w:tblCellMar>'))
    for col, w in zip(t.columns, widths):
        col.width = Inches(w)
    left = [any(len(r[j]) > 14 for r in rows[1:]) for j in range(ncol)]
    for i, row in enumerate(rows):
        tr = t.add_row()
        no_split(tr)
        if i == 0:
            tr._tr.get_or_add_trPr().append(parse_xml(f"<w:tblHeader {W}/>"))
        for j, (c, v, w) in enumerate(zip(tr.cells, row, widths)):
            c.width = Inches(w)
            cp = c.paragraphs[0]
            cp.paragraph_format.space_before = cp.paragraph_format.space_after = Pt(1)
            # short tables stay on one page with their caption; long ones keep at least the last row with it
            cp.paragraph_format.keep_with_next = i == 0 or len(rows) <= 10 or i == len(rows) - 1
            cp.alignment = WD_ALIGN_PARAGRAPH.LEFT if left[j] and i else WD_ALIGN_PARAGRAPH.CENTER
            add_runs(cp, f"**{v}**" if i == 0 else v, size=size)
    p = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, before=4, after=4 if note else 12)
    p.paragraph_format.keep_with_next = bool(note)
    add_runs(p, f"**{caption}**")
    if note:
        p = para(doc, after=12)
        add_runs(p, note, size=11, italic_all=True)


def body(doc, text):
    eq_n, first = 0, True
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith("# "):
            heading(doc, ln[2:], first)
            first = False
        elif ln.startswith("## "):
            subheading(doc, ln[3:])
        elif ln.startswith("$$"):
            eq_n += 1
            equation(doc, ln.strip("$"), eq_n)
        elif ln.startswith("!["):
            m = re.match(r"!\[(.*)\]\((.*)\)\{([\d.]+)\}", ln)
            figure(doc, m.group(1), m.group(2), float(m.group(3)))
        elif ln.startswith("TABLE:"):
            cap, rows = ln[6:].strip(), []
            i += 1
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            note = None
            if i < len(lines) and lines[i].startswith("NOTE:"):
                note = lines[i][5:].strip()
                i += 1
            table(doc, cap, rows, note)
            continue
        elif ln.startswith("- "):
            list_item(doc, ln[2:], "•")
        elif re.match(r"\d+\. ", ln):
            n, rest = ln.split(" ", 1)
            list_item(doc, rest, n, after=2)
        elif ln.startswith("> "):
            body_par(doc, ln[2:], indent=0.5)
        elif ln.strip():
            body_par(doc, ln)
        i += 1


def references(doc, order):
    p = para(doc, "10. REFERENCES", 16, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=18)
    p.paragraph_format.page_break_before = True
    for n, k in enumerate(order, 1):
        p = para(doc, align=WD_ALIGN_PARAGRAPH.LEFT, after=8, line=1.15)
        p.paragraph_format.left_indent = Inches(0.45)
        p.paragraph_format.first_line_indent = Inches(-0.45)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(0.45))
        add_runs(p, f"[{n}]\t{REFS[k][0]}")


def annexures(doc, slides):
    p = para(doc, "ANNEXURE I: SOURCE CODE", 16, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)
    p.paragraph_format.page_break_before = True
    body_par(doc, "The complete pipeline has 19 numbered Python modules (src/s01 to src/s19) and the dashboard "
                  "(app.py). The four core modules of the analysis are reproduced below.")
    for n, (name, what) in enumerate(CODE, 1):
        subheading(doc, f"I.{n} src/{name} ({what})")
        p = para(doc, after=6)
        r = p.add_run((ROOT / "src" / name).read_text().rstrip("\n"))
        r.font.name, r.font.size = "Courier New", Pt(8)
    p = para(doc, "LIST OF PUBLICATIONS", 16, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=18)
    p.paragraph_format.page_break_before = True
    for n, pub in enumerate(PUBLICATIONS, 1):
        p = para(doc, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=8, line=1.5)
        p.paragraph_format.left_indent = Inches(0.45)
        p.paragraph_format.first_line_indent = Inches(-0.45)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(0.45))
        add_runs(p, f"[{n}]\t{pub}")
    p = para(doc, "ANNEXURE II: PRESENTATION SLIDES", 16, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)
    p.paragraph_format.page_break_before = True
    with tempfile.TemporaryDirectory() as tmp:
        for n, png in enumerate(slides, 1):
            pic = picture(doc, bordered(png, 5.6, tmp), width=5.6, before=4, after=2)
            pic.paragraph_format.page_break_before = n > 1 and n % 2 == 1   # two slides per page
            para(doc, f"Slide {n}", 11, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=10)


# ---------------------------------------------------------------- document --------------------------------------------
def page_numbers(section, fmt):
    """Centred PAGE field in the footer; numbering restarts at 1 in the given format (lowerRoman or decimal)."""
    section.footer.is_linked_to_previous = False
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    r.font.size = Pt(12)
    for xml in ('<w:fldChar {} w:fldCharType="begin"/>', '<w:instrText {} xml:space="preserve"> PAGE </w:instrText>',
                '<w:fldChar {} w:fldCharType="end"/>'):
        r._r.append(parse_xml(xml.format(W)))
    sp = section._sectPr
    for old in sp.findall(qn("w:pgNumType")):
        sp.remove(old)
    sp.find(qn("w:cols")).addprevious(parse_xml(f'<w:pgNumType {W} w:fmt="{fmt}" w:start="1"/>'))


def build(pages, slides):
    text, order = number_citations((HERE / "report_content.md").read_text())
    assert len(re.findall(r"^# ", text, re.M)) == len(TOC_LABELS) - 1

    doc = docx.Document()
    st = doc.styles["Normal"]
    st.font.name, st.font.size = FONT, Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st.element.rPr.rFonts.set(qn("w:cs"), FONT)
    st.paragraph_format.space_after = Pt(0)
    for s in ("Header", "Footer"):
        doc.styles[s].font.name = FONT
    s0 = doc.sections[0]
    s0.page_width, s0.page_height = Inches(PAGE_W), Inches(PAGE_H)
    s0.left_margin = s0.right_margin = Inches(0.875)
    s0.top_margin, s0.bottom_margin = Inches(0.7), Inches(0.7)

    cover(doc)
    certificate(doc)
    s1 = doc.add_section(WD_SECTION.NEW_PAGE)          # front lists, roman page numbers
    s1.top_margin, s1.bottom_margin = Inches(1.0), Inches(0.9)
    page_numbers(s1, "lowerRoman")
    front_lists(doc, text, pages)
    page_numbers(doc.add_section(WD_SECTION.NEW_PAGE), "decimal")   # chapters, from 1
    body(doc, text)
    references(doc, order)
    annexures(doc, slides)

    doc.core_properties.title = TITLE
    doc.core_properties.author = "Tanishq Mewada, Saad Patel, Peeyusha Patki"
    out = OUT / f"{NAME}.docx"
    doc.save(out)
    to_pdf(out, out.parent)
    return out.with_suffix(".pdf"), text


def to_pdf(path, outdir):
    """LibreOffice does not pick up macOS's Times New Roman and Arial (it substitutes Liberation fonts), so the fonts
    are copied into a throwaway LibreOffice profile, which LibreOffice loads."""
    with tempfile.TemporaryDirectory() as prof:
        fonts = Path(prof) / "user" / "fonts"
        fonts.mkdir(parents=True)
        for pat in ("Times New Roman*.ttf", "Arial*.ttf", "Courier New*.ttf"):
            for f in Path("/System/Library/Fonts/Supplemental").glob(pat):
                shutil.copy(f, fonts)
        subprocess.run(["soffice", f"-env:UserInstallation=file://{prof}", "--headless", "--convert-to", "pdf",
                        "--outdir", str(outdir), str(path)], check=True, capture_output=True)


def slide_images(tmp):
    """PNG of each main slide of the final deck (rendered through LibreOffice)."""
    to_pdf(DECK, tmp)
    pdf = Path(tmp) / f"{DECK.stem}.pdf"
    subprocess.run(["pdftoppm", "-png", "-r", "150", "-l", str(DECK_SLIDES), str(pdf), str(Path(tmp) / "slide")],
                   check=True)
    return sorted(Path(tmp).glob("slide-*.png"))


def find_pages(pdf, text):
    """Printed page number of every table of contents and list entry, read from the PDF text. Front pages are
    numbered i, ii, ... from the table of contents; chapters are numbered 1, 2, ... from Chapter 1."""
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    pdf_pages = txt.split("\f")
    figs, tabs = captions(text)
    front = {n: rf"^\s*{n}\s*$" for n in ("List of Figures", "List of Tables", "List of Abbreviations")}
    keys = {n + 1: rf"^\s*{n + 1}\. [A-Z /&]{{4,}}\s*$" for n in range(len(TOC_LABELS))}
    keys |= {h: rf"^\s*{re.escape(h)}\s*$" for h in re.findall(r"^#{2,3} (.+)$", text, re.M)}
    keys |= {f"Figure {n}": rf"^\s*Figure {re.escape(n)}:" for n, _ in figs}
    keys |= {f"Table {n}": rf"^\s*Table {re.escape(n)}:" for n, _ in tabs}
    keys |= {a: rf"^\s*{re.escape(a.upper())}\s*$" for a in ANNEXURES}
    body_start = next(i for i, pg in enumerate(pdf_pages) if re.search(keys[1], pg, re.M))
    pages = {}
    for idx, pg in enumerate(pdf_pages):
        for k, rx in (front if idx < body_start else keys).items():
            if k not in pages and re.search(rx, pg, re.M):
                pages[k] = ROMAN[idx - 2] if idx < body_start else str(idx - body_start + 1)
    missing = [k for k in [*front, *keys] if k not in pages]
    assert not missing, f"not found in the PDF: {missing}"
    return pages


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        slides = slide_images(tmp)
        pages = {}
        for _ in range(4):          # filling in the numbers can move pages, so repeat until they settle
            pdf, text = build(pages, slides)
            new = find_pages(pdf, text)
            if new == pages:
                break
            pages = new
        else:
            raise RuntimeError("page numbers did not settle")
    print("pages:", pages)
    print("wrote", pdf, "and .docx")
