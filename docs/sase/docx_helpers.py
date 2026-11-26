#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared DOCX helpers for the Noghte proposal documents.

The helpers keep the whole document right-to-left, use one Persian font
(Vazirmatn), and build clean tables with repeating header rows.
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

FONT = "Vazirmatn"
NAVY = "1F3864"
BLUE = "2E75B6"
LIGHT_BLUE = "DDEBF7"
PALE_BLUE = "F2F6FC"
GREY = "595959"
BORDER = "B4C6E7"
TEXT = "1A1A1A"


# ---------------------------------------------------------------------------
# Low-level XML helpers
# ---------------------------------------------------------------------------
def _insert_in_order(parent, child, before_tags):
    """Insert *child* before the first existing child whose tag is in before_tags."""
    for existing in parent:
        if existing.tag in before_tags:
            existing.addprevious(child)
            return
    parent.append(child)


def _ensure_rfonts(run, name=FONT):
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), name)


def style_run(run, size=11, bold=False, color=TEXT, name=FONT, italic=False):
    """Apply font, size, colour and RTL to a run."""
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    _ensure_rfonts(run, name)

    rPr = run._r.get_or_add_rPr()
    # Complex-script size (Word uses this for Persian).
    for tag in ("w:szCs",):
        old = rPr.find(qn(tag))
        if old is not None:
            rPr.remove(old)
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), str(int(size * 2)))
    _insert_in_order(rPr, szCs, {qn("w:highlight"), qn("w:u"), qn("w:effect"),
                                 qn("w:bdr"), qn("w:shd"), qn("w:fitText"),
                                 qn("w:vertAlign"), qn("w:rtl"), qn("w:cs"),
                                 qn("w:em"), qn("w:lang")})
    # RTL run property.
    old_rtl = rPr.find(qn("w:rtl"))
    if old_rtl is not None:
        rPr.remove(old_rtl)
    rtl = OxmlElement("w:rtl")
    rtl.set(qn("w:val"), "1")
    _insert_in_order(rPr, rtl, {qn("w:cs"), qn("w:em"), qn("w:lang"),
                                qn("w:eastAsianLayout"), qn("w:specVanish"),
                                qn("w:oMath")})


def rtl_paragraph(paragraph):
    """Mark a paragraph as right-to-left and all its runs as RTL.

    LibreOffice interprets ``w:jc`` logically once ``w:bidi`` is set, so a
    literal ``right`` would align to the *end* (left) of an RTL line.  Convert
    physical alignments to their logical equivalents.
    """
    pPr = paragraph._p.get_or_add_pPr()
    if pPr.find(qn("w:bidi")) is None:
        bidi = OxmlElement("w:bidi")
        bidi.set(qn("w:val"), "1")
        _insert_in_order(pPr, bidi, {qn("w:adjustRightInd"), qn("w:snapToGrid"),
                                     qn("w:spacing"), qn("w:ind"), qn("w:jc"),
                                     qn("w:textDirection"), qn("w:textAlignment"),
                                     qn("w:outlineLvl"), qn("w:rPr")})
    jc = pPr.find(qn("w:jc"))
    if jc is not None:
        val = jc.get(qn("w:val"))
        if val == "right":
            jc.set(qn("w:val"), "start")
        elif val == "left":
            jc.set(qn("w:val"), "end")
    for run in paragraph.runs:
        rPr = run._r.get_or_add_rPr()
        if rPr.find(qn("w:rtl")) is None:
            rtl = OxmlElement("w:rtl")
            rtl.set(qn("w:val"), "1")
            _insert_in_order(rPr, rtl, {qn("w:cs"), qn("w:em"), qn("w:lang"),
                                        qn("w:eastAsianLayout"), qn("w:specVanish"),
                                        qn("w:oMath")})


def shade_paragraph(paragraph, fill):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    _insert_in_order(pPr, shd, {qn("w:tabs"), qn("w:suppressAutoHyphens"),
                                qn("w:kinsoku"), qn("w:wordWrap"),
                                qn("w:overflowPunct"), qn("w:topLinePunct"),
                                qn("w:autoSpaceDE"), qn("w:autoSpaceDN"),
                                qn("w:bidi"), qn("w:adjustRightInd"),
                                qn("w:snapToGrid"), qn("w:spacing"),
                                qn("w:ind"), qn("w:jc")})


def paragraph_bottom_border(paragraph, color=BLUE, size=6, space=3):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), str(space))
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    _insert_in_order(pPr, pBdr, {qn("w:shd"), qn("w:tabs"),
                                 qn("w:suppressAutoHyphens"), qn("w:kinsoku"),
                                 qn("w:wordWrap"), qn("w:overflowPunct"),
                                 qn("w:topLinePunct"), qn("w:autoSpaceDE"),
                                 qn("w:autoSpaceDN"), qn("w:bidi"),
                                 qn("w:adjustRightInd"), qn("w:snapToGrid"),
                                 qn("w:spacing"), qn("w:ind"), qn("w:jc")})


# ---------------------------------------------------------------------------
# Paragraph builders
# ---------------------------------------------------------------------------
def body(doc, text, size=11, bold=False, color=TEXT, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         space_before=0, space_after=5, line=1.45, first_indent=0, keep_next=False):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if first_indent:
        pf.first_line_indent = Cm(first_indent)
    pf.keep_with_next = keep_next
    run = p.add_run(text)
    style_run(run, size=size, bold=bold, color=color)
    rtl_paragraph(p)
    return p


def bullet(doc, text, size=11, level=0, color=TEXT):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.right_indent = Cm(0.55 + 0.45 * level)
    pf.first_line_indent = Cm(-0.40)
    pf.space_before = Pt(0)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.4
    r = p.add_run("•  ")
    style_run(r, size=size, bold=True, color=BLUE)
    r2 = p.add_run(text)
    style_run(r2, size=size, color=color)
    rtl_paragraph(p)
    return p


def numbered(doc, number, text, size=11):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.right_indent = Cm(0.55)
    pf.first_line_indent = Cm(-0.45)
    pf.space_before = Pt(0)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.4
    r = p.add_run(f"{number}.  ")
    style_run(r, size=size, bold=True, color=NAVY)
    r2 = p.add_run(text)
    style_run(r2, size=size)
    rtl_paragraph(p)
    return p


def _fa_digits(value):
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def h1(doc, text, number=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pf = p.paragraph_format
    pf.space_before = Pt(14)
    pf.space_after = Pt(7)
    pf.keep_with_next = True
    r = p.add_run("▌ ")
    style_run(r, size=14, bold=True, color=BLUE)
    label = f"{_fa_digits(number)}. {text}" if number is not None else text
    r2 = p.add_run(label)
    style_run(r2, size=13.5, bold=True, color=NAVY)
    paragraph_bottom_border(p, color=BLUE, size=6, space=2)
    rtl_paragraph(p)
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pf = p.paragraph_format
    pf.space_before = Pt(9)
    pf.space_after = Pt(3)
    pf.keep_with_next = True
    r = p.add_run(text)
    style_run(r, size=11.8, bold=True, color=BLUE)
    rtl_paragraph(p)
    return p


def qlabel(doc, text):
    """The official questionnaire label, with a pale blue band."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pf = p.paragraph_format
    pf.space_before = Pt(8)
    pf.space_after = Pt(4)
    pf.keep_with_next = True
    r = p.add_run(text)
    style_run(r, size=11.5, bold=True, color=NAVY)
    shade_paragraph(p, "EAF1FB")
    rtl_paragraph(p)
    return p


def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(5)
    pf.space_after = Pt(3)
    pf.keep_with_next = True
    r = p.add_run(text)
    style_run(r, size=9, bold=True, color=GREY)
    rtl_paragraph(p)
    return p


def note(doc, text, size=9):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(5)
    pf.line_spacing = 1.25
    r = p.add_run(text)
    style_run(r, size=size, color=GREY)
    rtl_paragraph(p)
    return p


def checkbox_line(doc, checked, label, size=11):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.35
    box = "☑" if checked else "☐"
    r = p.add_run(box + "  ")
    style_run(r, size=13, color=NAVY, name="DejaVu Sans")
    r2 = p.add_run(label)
    style_run(r2, size=size, bold=checked)
    rtl_paragraph(p)
    return p


def page_break(doc):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)
    p.paragraph_format.space_after = Pt(0)


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------
def _shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def _cell_text(cell, text, bold=False, size=9.5, color=TEXT,
               align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(1)
    pf.space_after = Pt(1)
    pf.line_spacing = 1.12
    r = p.add_run(str(text))
    style_run(r, size=size, bold=bold, color=color)
    rtl_paragraph(p)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def _table_borders(table, color=BORDER, size=4):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def _cell_margins(table, top=35, bottom=35, left=70, right=70):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def _fixed_layout(table):
    tblPr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)


def _bidi_table(table):
    tblPr = table._tbl.tblPr
    bidi = OxmlElement("w:bidiVisual")
    bidi.set(qn("w:val"), "1")
    style = tblPr.find(qn("w:tblStyle"))
    if style is not None:
        style.addnext(bidi)
    else:
        tblPr.insert(0, bidi)


def _cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn("w:cantSplit")) is None:
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)


def _repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    h = OxmlElement("w:tblHeader")
    h.set(qn("w:val"), "true")
    trPr.append(h)
    _cant_split(row)


def add_table(doc, headers, rows, widths, font_size=9.5, total_row=False,
              center_cols=None, header_fill=NAVY, align_first_right=False):
    """Build a clean RTL table.

    widths: list of column widths in cm (sum <= 16.6).
    """
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.allow_autofit = False
    _bidi_table(table)
    _table_borders(table)
    _fixed_layout(table)
    _cell_margins(table)

    hdr = table.rows[0]
    _repeat_header(hdr)
    for i, text in enumerate(headers):
        cell = hdr.cells[i]
        _shade_cell(cell, header_fill)
        _cell_text(cell, text, bold=True, size=font_size, color="FFFFFF")
        cell.width = Cm(widths[i])

    center_cols = set(center_cols or [])
    for ri, row in enumerate(rows):
        tr = table.add_row()
        _cant_split(tr)
        cells = tr.cells
        is_total = total_row and ri == len(rows) - 1
        for ci, value in enumerate(row):
            cell = cells[ci]
            if is_total:
                _shade_cell(cell, LIGHT_BLUE)
            elif ri % 2 == 1:
                _shade_cell(cell, PALE_BLUE)
            align = WD_ALIGN_PARAGRAPH.CENTER
            if ci == 0 or (align_first_right and ci == 1):
                align = WD_ALIGN_PARAGRAPH.RIGHT
            _cell_text(cell, value, bold=is_total, size=font_size, align=align)
            cell.width = Cm(widths[ci])

    for i, w in enumerate(widths):
        table.columns[i].width = Cm(w)
    return table


def keep_table_together(table):
    """Ask Word/LibreOffice to keep all rows of a small table on one page."""
    rows = list(table.rows)
    for row in rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True


def add_info_table(doc, rows, widths=(4.6, 12.0), font_size=10):
    """Borderless two-column table for cover/identity information."""
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.allow_autofit = False
    _bidi_table(table)
    _fixed_layout(table)
    for label, value in rows:
        cells = table.add_row().cells
        _cell_text(cells[0], label, bold=True, size=font_size, color=NAVY,
                   align=WD_ALIGN_PARAGRAPH.RIGHT)
        _cell_text(cells[1], value, size=font_size,
                   align=WD_ALIGN_PARAGRAPH.RIGHT)
        cells[0].width = Cm(widths[0])
        cells[1].width = Cm(widths[1])
    for i, w in enumerate(widths):
        table.columns[i].width = Cm(w)
    return table


# ---------------------------------------------------------------------------
# Fields, headers, footers
# ---------------------------------------------------------------------------
def _field(paragraph, instr, size=8.5, color=GREY):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = f" {instr} "
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr_el)
    run._r.append(fld_sep)
    run._r.append(fld_end)
    style_run(run, size=size, color=color)


def add_header(section, text):
    header = section.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pf = p.paragraph_format
    pf.space_after = Pt(2)
    r = p.add_run(text)
    style_run(r, size=8, color="808080")
    paragraph_bottom_border(p, color="D9E2F3", size=4, space=2)
    rtl_paragraph(p)


def add_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("صفحه ")
    style_run(r, size=8.5, color=GREY)
    _field(p, "PAGE")
    r2 = p.add_run(" از ")
    style_run(r2, size=8.5, color=GREY)
    _field(p, "NUMPAGES")
    rtl_paragraph(p)


def setup_document(title, subject, author="علی ذوقی"):
    doc = Document()
    doc.core_properties.title = title
    doc.core_properties.subject = subject
    doc.core_properties.author = author
    doc.core_properties.language = "fa-IR"

    # Normal style
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor.from_string(TEXT)
    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), FONT)

    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.header_distance = Cm(0.9)
    section.footer_distance = Cm(0.9)
    section.different_first_page_header_footer = True
    return doc
