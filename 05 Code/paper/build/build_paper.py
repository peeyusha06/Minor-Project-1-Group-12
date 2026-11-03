"""Build the IEEE conference paper (DOCX, then PDF via LibreOffice) and the Markdown version from one source.

Source:   paper/build/paper_content.md   (text with [@key] citations, $$label$$ equations, TABLE:/NOTE: blocks)
          paper/build/references.py      (verified IEEE references)
Template: paper/build/ieee_conference_template_a4_transitional.docx
          = the official IEEE A4 conference template (ieee_conference_template_a4_official.docx, downloaded from
          ieee.org/conferences/publishing/templates) re-saved by LibreOffice from Strict to Transitional Office XML so
          python-docx can open it. All IEEE paragraph styles, numbering (I., A., Fig. 1., TABLE I., [1]) and section
          layout are taken from the template.
Outputs:  paper/ieee_paper.docx, paper/ieee_paper.pdf, paper/paper_source.md

Run:  python paper/build/build_paper.py
"""
import copy
import re
import subprocess
import sys
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
sys.path.insert(0, str(HERE))
from references import REFS  # noqa: E402

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
M = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
COL_TWIPS = 4867                       # IEEE A4 column width: (11906 - 2*907 - 360) / 2


# ---------------------------------------------------------------- equations (OMML) ---------------------------------
def r(t, sty=None):
    s = f'<m:rPr><m:sty m:val="{sty}"/></m:rPr>' if sty else ""
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<m:r>{s}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>'
            f'<m:t xml:space="preserve">{t}</m:t></m:r>')


def p(t):  # plain (upright) text
    return r(t, "p")


def sub(b, s):
    return f"<m:sSub><m:e>{b}</m:e><m:sub>{s}</m:sub></m:sSub>"


def sup(b, s):
    return f"<m:sSup><m:e>{b}</m:e><m:sup>{s}</m:sup></m:sSup>"


def frac(n, d):
    return f"<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>"


def nsum(lo, hi, body):
    hi_xml = f"<m:sup>{hi}</m:sup>" if hi else "<m:sup/>"
    sup_hide = "" if hi else '<m:supHide m:val="1"/>'
    return (f'<m:nary><m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/>{sup_hide}</m:naryPr>'
            f"<m:sub>{lo}</m:sub>{hi_xml}<m:e>{body}</m:e></m:nary>")


def sqrt(x):
    return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{x}</m:e></m:rad>'


def bar(x):
    return f'<m:bar><m:barPr><m:pos m:val="top"/></m:barPr><m:e>{x}</m:e></m:bar>'


def delim(x, beg="(", end=")"):
    return f'<m:d><m:dPr><m:begChr m:val="{beg}"/><m:endChr m:val="{end}"/></m:dPr><m:e>{x}</m:e></m:d>'


def bold(t):
    return r(t, "b")


EQ = {   # label -> (LaTeX for the Markdown version, OMML)
    "departure": (r"D_{i,y} = 100\,\frac{P_{i,y} - \bar{P}_i}{\bar{P}_i}",
                  sub(r("D"), r("i,y")) + p("=100") + frac(sub(r("P"), r("i,y")) + p("−") + sub(bar(r("P")), r("i")),
                                                         sub(bar(r("P")), r("i")))),
    "slope": (r"b_i = \frac{\sum_{y}(I_y - \bar{I})(D_{i,y} - \bar{D}_i)}{\sum_{y}(I_y - \bar{I})^2}",
              sub(r("b"), r("i")) + p("=") + frac(
                  nsum(r("y"), "", delim(sub(r("I"), r("y")) + p("−") + bar(r("I"))) +
                       delim(sub(r("D"), r("i,y")) + p("−") + sub(bar(r("D")), r("i")))),
                  nsum(r("y"), "", sup(delim(sub(r("I"), r("y")) + p("−") + bar(r("I"))), p("2"))))),
    "zscore": (r"z_{ij} = \frac{s_j x_{ij} - \mu_j}{\sigma_j}",
               sub(r("z"), r("ij")) + p("=") + frac(sub(r("s"), r("j")) + sub(r("x"), r("ij")) + p("−") + sub(r("μ"), r("j")),
                                                    sub(r("σ"), r("j")))),
    "pca": (r"\mathbf{R}\mathbf{v}_k = \lambda_k \mathbf{v}_k,\quad \mathbf{R} = \tfrac{1}{34}\mathbf{Z}^{\top}\mathbf{Z}",
            bold("R") + sub(bold("v"), r("k")) + p("=") + sub(r("λ"), r("k")) + sub(bold("v"), r("k")) + p(",   ") +
            bold("R") + p("=") + frac(p("1"), p("34")) + sup(bold("Z"), p("T")) + bold("Z")),
    "loading": (r"L_{jk} = v_{jk}\sqrt{\lambda_k}",
                sub(r("L"), r("jk")) + p("=") + sub(r("v"), r("jk")) + sqrt(sub(r("λ"), r("k")))),
    "rawweight": (r"r_j = \sum_{k=1}^{3} \mathrm{EVR}_k \, |L_{jk}|",
                  sub(r("r"), r("j")) + p("=") + nsum(r("k") + p("=1"), p("3"),
                                                     sub(p("EVR"), r("k")) + delim(sub(r("L"), r("jk")), "|", "|"))),
    "weight": (r"w_j = \frac{r_j}{\sum_{l=1}^{6} r_l}",
               sub(r("w"), r("j")) + p("=") + frac(sub(r("r"), r("j")), nsum(r("l") + p("=1"), p("6"), sub(r("r"), r("l"))))),
    "score": (r"V_i = \sum_{j=1}^{6} w_j z_{ij}",
              sub(r("V"), r("i")) + p("=") + nsum(r("j") + p("=1"), p("6"), sub(r("w"), r("j")) + sub(r("z"), r("ij")))),
    "index": (r"VI_i = 100\,\frac{V_i - V_{\min}}{V_{\max} - V_{\min}}",
              sub(r("VI"), r("i")) + p("=100") + frac(sub(r("V"), r("i")) + p("−") + sub(r("V"), p("min")),
                                                     sub(r("V"), p("max")) + p("−") + sub(r("V"), p("min")))),
    "kmeans": (r"J = \sum_{g=1}^{3}\sum_{i \in G_g} (VI_i - c_g)^2",
               r("J") + p("=") + nsum(r("g") + p("=1"), p("3"), nsum(r("i") + p("∈") + sub(r("G"), r("g")), "",
                                                                     sup(delim(sub(r("VI"), r("i")) + p("−") + sub(r("c"), r("g"))), p("2"))))),
    "share": (r"s_{i,t} = \frac{d_{i,t}}{T_i}",
              sub(r("s"), r("i,t")) + p("=") + frac(sub(r("d"), r("i,t")), sub(r("T"), r("i")))),
}


# ---------------------------------------------------------------- source parsing ------------------------------------
def parse(text):
    meta, blocks, authors = {}, [], []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith("TITLE:"):
            meta["title"] = ln[6:].strip()
        elif ln.startswith("AUTHOR:"):
            authors.append([x.strip() for x in ln[7:].split("|")])
        elif ln.startswith("ABSTRACT:"):
            meta["abstract"] = ln[9:].strip()
        elif ln.startswith("KEYWORDS:"):
            meta["keywords"] = ln[9:].strip()
        elif ln.startswith("##### "):
            blocks.append(("h5", ln[6:]))
        elif ln.startswith("## "):
            blocks.append(("h2", ln[3:]))
        elif ln.startswith("# "):
            blocks.append(("h1", ln[2:]))
        elif ln.startswith("$$") and ln.endswith("$$"):
            blocks.append(("eq", ln[2:-2]))
        elif ln.startswith("!["):
            m = re.match(r"!\[(.*)\]\((.*)\)", ln)
            blocks.append(("fig", m.group(1), m.group(2)))
        elif ln.startswith("TABLE:"):
            cap, rows, note = ln[6:].strip(), [], None
            i += 1
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            if i < len(lines) and lines[i].startswith("NOTE:"):
                note = lines[i][5:].strip()
                i += 1
            blocks.append(("table", cap, rows, note))
            continue
        elif ln.startswith("- "):
            blocks.append(("bullet", ln[2:]))
        elif ln.strip():
            blocks.append(("p", ln))
        i += 1
    meta["authors"] = authors
    return meta, blocks


def number_citations(meta, blocks):
    order = []

    def texts():
        for b in blocks:
            if b[0] in ("p", "bullet", "h1", "h2"):
                yield b[1]
            elif b[0] == "fig":
                yield b[1]
            elif b[0] == "table":
                yield b[1]
                for row in b[2]:
                    yield from row
                if b[3]:
                    yield b[3]
    for t in [meta["abstract"]] + list(texts()):
        for grp in re.findall(r"\[(@[^\]]+)\]", t):
            for k in [x.strip()[1:] for x in grp.split(";")]:
                if k not in REFS:
                    raise KeyError(f"unknown reference key {k}")
                if k not in order:
                    order.append(k)
    num = {k: i + 1 for i, k in enumerate(order)}
    unused = set(REFS) - set(order)
    if unused:
        raise ValueError(f"references never cited: {sorted(unused)}")
    return order, num


def cite(text, num):
    def repl(m):
        ns = sorted(num[x.strip()[1:]] for x in m.group(1).split(";"))
        out, run = [], [ns[0]]
        for n in ns[1:]:
            if n == run[-1] + 1:
                run.append(n)
            else:
                out.append(run)
                run = [n]
        out.append(run)
        parts = [f"[{a[0]}]–[{a[-1]}]" if len(a) >= 3 else ", ".join(f"[{x}]" for x in a) for a in out]
        return ", ".join(parts)
    return re.sub(r"\[(@[^\]]+)\]", repl, text)


# ---------------------------------------------------------------- inline formatting ---------------------------------
TOKEN = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|_\{[^}]*\}|\^\{[^}]*\})")


def runs_of(text):
    """Split text into (string, bold, italic, vert) pieces. *x* italic, **x** bold, _{..} subscript, ^{..} superscript."""
    out = []
    for tok in TOKEN.split(text):
        if not tok:
            continue
        if tok.startswith("**"):
            out.append((tok[2:-2], True, False, None))
        elif tok.startswith("*"):
            out.append((tok[1:-1], False, True, None))
        elif tok.startswith("_{"):
            s = tok[2:-1]
            out.append((s, False, bool(re.fullmatch(r"[a-z,]+", s)), "subscript"))
        elif tok.startswith("^{"):
            out.append((tok[2:-1], False, False, "superscript"))
        else:
            out.append((tok, False, False, None))
    return out


def add_runs(par, text, size=None, italic_all=False):
    for s, b, it, vert in runs_of(text):
        run = par.add_run(s)
        if b:
            run.bold = True
        if it or italic_all:
            run.italic = True
        if vert == "subscript":
            run.font.subscript = True
        elif vert == "superscript":
            run.font.superscript = True
        if size:
            run.font.size = Pt(size)


def plain(text):
    """Markdown rendering of the inline syntax."""
    text = re.sub(r"_\{([^}]*)\}", r"<sub>\1</sub>", text)
    return re.sub(r"\^\{([^}]*)\}", r"<sup>\1</sup>", text)


# ---------------------------------------------------------------- DOCX helpers --------------------------------------
def set_borders(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:tcBorders {W}>' + "".join(
        f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="000000"/>' for e in ("top", "left", "bottom", "right"))
        + "</w:tcBorders>"))


def no_numbering(par):
    pPr = par._p.get_or_add_pPr()
    pPr.append(parse_xml(f'<w:numPr {W}><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'))


CELL_PAD = 60          # left and right cell margin (twips)
CHAR = 96              # approximate width of one 8 pt Times character (twips)


def col_widths(rows):
    """Column widths (twips): numeric or short columns get exactly what they need, text columns share the rest."""
    def clean(t):
        return re.sub(r"[*_{}^]", "", t)
    fixed, need = {}, {}
    for j in range(len(rows[0])):
        body = [clean(r[j]) for r in rows[1:]]
        head_word = max(len(w) for w in clean(rows[0][j]).split())
        if all(re.fullmatch(r"[−+\-0-9.,/ %()]+", t) or len(t) <= 9 for t in body):
            fixed[j] = 2 * CELL_PAD + CHAR * max([len(t) for t in body] + [head_word]) + 20
        else:
            need[j] = max(min(len(t), 26) for t in body)
    rest = COL_TWIPS - sum(fixed.values())
    widths = []
    for j in range(len(rows[0])):
        widths.append(int(fixed[j]) if j in fixed else int(rest * need[j] / sum(need.values())))
    return widths


def add_table(doc, cap, rows, note, num):
    c = doc.add_paragraph(style="table head")
    c.paragraph_format.keep_with_next = True
    add_runs(c, cite(cap, num))
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = col_widths(rows)
    tblPr = t._tbl.tblPr
    tblPr.append(parse_xml(f'<w:tblW {W} w:w="{COL_TWIPS}" w:type="dxa"/>'))
    tblPr.append(parse_xml(f'<w:tblLayout {W} w:type="fixed"/>'))
    tblPr.append(parse_xml(f'<w:tblCellMar {W}><w:left w:w="{CELL_PAD}" w:type="dxa"/>'
                           f'<w:right w:w="{CELL_PAD}" w:type="dxa"/></w:tblCellMar>'))
    grid = t._tbl.tblGrid
    for gc, wd in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(wd))
    for i, row in enumerate(rows):
        tr = t.rows[i]
        if i == 0:
            tr._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {W}/>'))
        tr._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {W}/>'))
        for j, val in enumerate(row):
            cell = tr.cells[j]
            cell.width = widths[j] * 635          # twips -> EMU
            set_borders(cell)
            par = cell.paragraphs[0]
            par.style = doc.styles["table col head" if i == 0 else "table copy"]
            numeric = re.fullmatch(r"[−+\-0-9.,/ %]+|[0-9.]+ to [0-9.]+", val) is not None
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER if (i == 0 or numeric or j > 0 and len(val) < 12) else WD_ALIGN_PARAGRAPH.LEFT
            add_runs(par, cite(val, num))
            if i < len(rows) - 1:
                par.paragraph_format.keep_with_next = True       # keep the table in one column
    if note:
        f = doc.add_paragraph(style="table footnote")
        no_numbering(f)
        f.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_runs(f, cite(note, num), size=7)
    else:
        sp = doc.add_paragraph(style="table footnote")
        no_numbering(sp)


def add_equation(doc, label, n):
    par = doc.add_paragraph(style="equation")
    par.add_run("\t")
    par._p.append(parse_xml(f"<m:oMath {M} {W}>{EQ[label][1]}</m:oMath>"))
    tail = par.add_run(f"\t({n})")
    tail.font.name = "Times New Roman"
    tail._r.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Times New Roman")


def add_figure(doc, path, caption, num):
    par = doc.add_paragraph(style="Normal")
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.keep_with_next = True
    par.paragraph_format.space_before = Pt(6)
    par.add_run().add_picture(str(PAPER / path), width=Inches(3.3))
    cap = doc.add_paragraph(style="figure caption")
    add_runs(cap, cite(caption, num))


def fix_sectpr(sp, top=None, cols=None, space=None):
    pgMar = sp.find(qn("w:pgMar"))
    pgMar.set(qn("w:left"), "907")
    pgMar.set(qn("w:right"), "907")
    pgMar.set(qn("w:header"), "720")
    pgMar.set(qn("w:footer"), "720")
    if top:
        pgMar.set(qn("w:top"), str(top))
    if cols:
        c = sp.find(qn("w:cols"))
        c.set(qn("w:num"), str(cols))
        if space:
            c.set(qn("w:space"), str(space))


# ---------------------------------------------------------------- build ---------------------------------------------
def build():
    meta, blocks = parse((HERE / "paper_content.md").read_text())
    order, num = number_citations(meta, blocks)
    doc = docx.Document(str(HERE / "ieee_conference_template_a4_transitional.docx"))
    body = doc.element.body
    P = doc.paragraphs

    # title
    title = P[0]
    for rr in list(title.runs):
        rr._r.getparent().remove(rr._r)
    title.add_run(meta["title"])
    title_sect = P[3]._p.pPr.find(qn("w:sectPr"))
    fix_sectpr(title_sect, top=540)
    P[1]._p.getparent().remove(P[1]._p)                       # template note about sub-titles

    # authors in a balanced two-column section (equal-height blocks, so the columns split them evenly)
    P = doc.paragraphs
    author_pars = [p_ for p_ in P[:12] if p_.style.name == "Author" and "Given Name" in p_.text]
    a = meta["authors"]
    left, right = a[0::2], a[1::2]
    for n, (par, info) in enumerate(zip(author_pars, left + right)):
        for rr in list(par.runs):
            rr._r.getparent().remove(rr._r)
        name, dept, org, city, email = (info + [""] * 5)[:5]
        par.add_run(name).add_break()
        d = par.add_run(dept)
        d.italic = True
        d.add_break()
        o = par.add_run(org)
        o.italic = True
        o.add_break()
        c_ = par.add_run(city)
        if email:
            c_.add_break()
            par.add_run(email)
    for i in (len(left) - 1, len(a) - 1):                     # gap before the abstract under each column
        author_pars[i].paragraph_format.space_after = Pt(12)
    for par in author_pars[len(a):]:
        par._p.getparent().remove(par._p)
    P = doc.paragraphs
    sect_pars = [p_ for p_ in P if p_._p.pPr is not None and p_._p.pPr.find(qn("w:sectPr")) is not None]
    author_sect = sect_pars[1]._p.pPr.find(qn("w:sectPr"))
    fix_sectpr(author_sect, top=450, cols=2, space=360)

    # remove everything after the author section (template guidance text, sample table, frames)
    body_sect_par = sect_pars[3]._p                             # carries the two-column body section properties
    started = False
    for el in list(body):
        if el is sect_pars[1]._p:
            started = True
            continue
        if not started or el.tag == qn("w:sectPr") or el is body_sect_par:
            continue
        body.remove(el)
    body_sect = body_sect_par.pPr.find(qn("w:sectPr"))
    fix_sectpr(body_sect, top=1080, cols=2, space=360)
    fix_sectpr(body.find(qn("w:sectPr")), top=1080)

    # abstract and keywords
    ab = doc.add_paragraph(style="Abstract")
    x = ab.add_run("Abstract")
    x.italic = True
    add_runs(ab, "—" + cite(meta["abstract"], num))
    kw = doc.add_paragraph(style="Keywords")
    kw.add_run("Keywords—" + meta["keywords"])

    eq_n, md = 0, []
    md.append(f"# {meta['title']}\n")
    for a_ in meta["authors"]:
        md.append("**" + a_[0] + "**, " + ", ".join(x for x in a_[1:] if x) + "  ")
    md.append("")
    md.append(f"***Abstract*—{meta['abstract']}**\n")
    md.append(f"***Keywords*—{meta['keywords']}**\n")
    roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    h1 = h2 = tab = fig = 0
    for b in blocks:
        kind = b[0]
        if kind == "h1":
            h1, h2 = h1 + 1, 0
            doc.add_paragraph(b[1], style="Heading 1")
            md.append(f"\n## {roman[h1 - 1]}. {b[1].upper()}\n")
        elif kind == "h2":
            h2 += 1
            doc.add_paragraph(b[1], style="Heading 2")
            md.append(f"\n### {chr(64 + h2)}. {b[1]}\n")
        elif kind == "h5":
            doc.add_paragraph(b[1], style="Heading 5")
            md.append(f"\n## {b[1].upper()}\n")
        elif kind == "p":
            if md and md[-1].startswith("- "):
                md.append("")
            par = doc.add_paragraph(style="Body Text")
            add_runs(par, cite(b[1], num))
            md.append(plain(cite(b[1], num)) + "\n")
        elif kind == "bullet":
            par = doc.add_paragraph(style="bullet list")
            add_runs(par, cite(b[1], num))
            md.append("- " + plain(cite(b[1], num)))
        elif kind == "eq":
            eq_n += 1
            add_equation(doc, b[1], eq_n)
            md.append(f"\n$$ {EQ[b[1]][0]} \\qquad ({eq_n}) $$\n")
        elif kind == "fig":
            fig += 1
            add_figure(doc, b[2], b[1], num)
            md.append(f"\n![Fig. {fig}]({b[2]})\n\n*Fig. {fig}. {plain(cite(b[1], num))}*\n")
        elif kind == "table":
            tab += 1
            _, cap, rows, note = b
            add_table(doc, cap, rows, note, num)
            md.append(f"\n**TABLE {roman[tab - 1]}. {cap.upper()}**\n")
            md.append("| " + " | ".join(plain(c) for c in rows[0]) + " |")
            md.append("|" + "---|" * len(rows[0]))
            for row in rows[1:]:
                md.append("| " + " | ".join(plain(cite(c, num)) for c in row) + " |")
            if note:
                md.append(f"\n*{plain(cite(note, num))}*")
            md.append("")
        if kind == "bullet":
            continue
    # references
    doc.add_paragraph("References", style="Heading 5")
    md.append("\n## REFERENCES\n")
    for i, k in enumerate(order, 1):
        par = doc.add_paragraph(style="references")
        if "Available:" in REFS[k][0] or "doi:" in REFS[k][0]:
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_runs(par, REFS[k][0])
        md.append(f"[{i}] {REFS[k][0]}  ")
    # the two-column section ends after the references; the final one-column section balances the last page
    body.remove(body_sect_par)
    body.insert(list(body).index(body.find(qn("w:sectPr"))), body_sect_par)

    # first-page footer: remove the template's copyright placeholder (inserted by the conference after acceptance)
    for s in doc.sections:
        for f in (s.first_page_footer, s.footer, s.even_page_footer):
            for fp in f.paragraphs:
                for rr in fp.runs:
                    rr.text = ""
    cp = doc.core_properties
    cp.title = meta["title"]
    cp.author = "; ".join(x[0] for x in meta["authors"])
    cp.subject = "IEEE conference paper"
    cp.keywords = meta["keywords"]
    cp.comments = ""
    out = PAPER / "ieee_paper.docx"
    doc.save(str(out))
    (PAPER / "paper_source.md").write_text("\n".join(md) + "\n")
    print("wrote", out, "and paper_source.md;", len(order), "references,", eq_n, "equations,", tab, "tables,", fig, "figures")
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(PAPER), str(out)],
                   check=True, capture_output=True)
    print("wrote", PAPER / "ieee_paper.pdf")


if __name__ == "__main__":
    build()
