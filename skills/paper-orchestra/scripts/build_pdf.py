#!/usr/bin/env python3
"""
build_pdf.py — Fallback academic PDF builder (ReportLab).

Converts a Markdown research paper into a two-column IEEE-style PDF with:
  - Full-width title + abstract on page 1 (proper IEEE layout, no blank first page)
  - Two-column body starting below the abstract on the same page
  - Architecture diagram auto-injected before §4 (or at <!-- ARCH_DIAGRAM -->)
  - Clickable in-text citations [N] that jump to the reference entry
  - Prismor brand colours (slate / blue)
  - Header/footer with short title and page numbers

Usage:
    python build_pdf.py --input paper.md --output paper.pdf
    python build_pdf.py --input paper.md --output paper.pdf --title-short "Short Title"
    python build_pdf.py --input paper.md --output paper.pdf --no-diagram

Requires: reportlab >= 4.0
"""

import argparse
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    NextPageTemplate,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    FrameBreak,
)
from reportlab.platypus.flowables import AnchorFlowable

# ── Page geometry ─────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = letter          # 8.5 × 11 inches
M_TOP    = 0.75 * inch
M_BOTTOM = 0.85 * inch
M_LEFT   = 0.75 * inch
M_RIGHT  = 0.75 * inch
COL_GAP  = 0.25 * inch

BODY_W  = PAGE_W - M_LEFT - M_RIGHT
COL_W   = (BODY_W - COL_GAP) / 2
BODY_H  = PAGE_H - M_TOP - M_BOTTOM

# How much vertical space the title+abstract strip gets on page 1.
# 4.5 in comfortably holds ~200-word abstract + title block.
TITLE_STRIP_H = 4.5 * inch
COL_H_P1      = BODY_H - TITLE_STRIP_H   # column height on page 1

# ── Brand colours ─────────────────────────────────────────────────────────────

C_DARK    = colors.HexColor("#0f172a")
C_BLUE    = colors.HexColor("#1d4ed8")
C_NAVY    = colors.HexColor("#1e3a5f")
C_RULE    = colors.HexColor("#cbd5e1")
C_MUTED   = colors.HexColor("#64748b")
C_BG_CODE = colors.HexColor("#f8fafc")
C_BG_BOX  = colors.HexColor("#eff6ff")
C_BOX_BDR = colors.HexColor("#bfdbfe")
C_LINK    = colors.HexColor("#1d4ed8")

# ── Styles ────────────────────────────────────────────────────────────────────

def make_styles() -> dict:
    return {
        "title": ParagraphStyle(
            "PTitle", fontName="Times-Bold", fontSize=17, leading=21,
            textColor=C_DARK, alignment=TA_CENTER, spaceAfter=3,
        ),
        "subtitle": ParagraphStyle(
            "PSub", fontName="Times-Italic", fontSize=9.5, leading=12,
            textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=4,
        ),
        "abstract_h": ParagraphStyle(
            "PAbsH", fontName="Times-Bold", fontSize=9, leading=11,
            textColor=C_NAVY, alignment=TA_CENTER, spaceBefore=2, spaceAfter=3,
        ),
        "abstract": ParagraphStyle(
            "PAbs", fontName="Times-Roman", fontSize=8.5, leading=11.5,
            textColor=C_DARK, alignment=TA_JUSTIFY,
            leftIndent=20, rightIndent=20, spaceAfter=4,
        ),
        "section": ParagraphStyle(
            "PSec", fontName="Times-Bold", fontSize=10, leading=13,
            textColor=C_NAVY, spaceBefore=8, spaceAfter=3, keepWithNext=1,
        ),
        "subsection": ParagraphStyle(
            "PSSec", fontName="Times-BoldItalic", fontSize=9, leading=12,
            textColor=C_DARK, spaceBefore=5, spaceAfter=2, keepWithNext=1,
        ),
        "body": ParagraphStyle(
            "PBody", fontName="Times-Roman", fontSize=9, leading=12,
            textColor=C_DARK, alignment=TA_JUSTIFY,
            spaceAfter=4, firstLineIndent=12,
        ),
        "body_ni": ParagraphStyle(
            "PBodyNI", fontName="Times-Roman", fontSize=9, leading=12,
            textColor=C_DARK, alignment=TA_JUSTIFY, spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "PBul", fontName="Times-Roman", fontSize=9, leading=12,
            textColor=C_DARK, alignment=TA_JUSTIFY,
            leftIndent=12, firstLineIndent=-8, spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "PCode", fontName="Courier", fontSize=7.5, leading=10,
            textColor=C_DARK, leftIndent=8, spaceAfter=4,
            backColor=C_BG_CODE,
        ),
        "ref": ParagraphStyle(
            "PRef", fontName="Times-Roman", fontSize=8, leading=11,
            textColor=C_DARK, leftIndent=14, firstLineIndent=-14, spaceAfter=3,
        ),
        "diagram_label": ParagraphStyle(
            "PDiag", fontName="Helvetica-Bold", fontSize=8, leading=10,
            textColor=C_NAVY, alignment=TA_CENTER,
        ),
        "diagram_body": ParagraphStyle(
            "PDiagB", fontName="Helvetica", fontSize=7.5, leading=10,
            textColor=C_DARK, alignment=TA_CENTER,
        ),
        "diagram_caption": ParagraphStyle(
            "PDiagC", fontName="Times-Italic", fontSize=8, leading=10,
            textColor=C_MUTED, alignment=TA_CENTER, spaceBefore=4, spaceAfter=6,
        ),
    }


# ── Header / footer ───────────────────────────────────────────────────────────

def on_page(canvas, doc, short_title: str, byline: str = ""):
    canvas.saveState()
    y_h = PAGE_H - M_TOP + 8
    canvas.setStrokeColor(C_RULE)
    canvas.setLineWidth(0.5)
    canvas.line(M_LEFT, y_h, PAGE_W - M_RIGHT, y_h)
    canvas.setFont("Times-Italic", 7.5)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(M_LEFT, y_h + 2, short_title)
    if byline:
        canvas.drawRightString(PAGE_W - M_RIGHT, y_h + 2, byline)
    y_f = M_BOTTOM - 12
    canvas.line(M_LEFT, y_f, PAGE_W - M_RIGHT, y_f)
    canvas.drawCentredString(PAGE_W / 2, y_f - 10, str(doc.page))
    canvas.restoreState()


# ── Page templates ────────────────────────────────────────────────────────────

def build_doc(out_path: str, short_title: str,
              title_meta: str = "", author_meta: str = "",
              byline: str = "") -> BaseDocTemplate:
    doc = BaseDocTemplate(
        out_path, pagesize=letter,
        leftMargin=M_LEFT, rightMargin=M_RIGHT,
        topMargin=M_TOP, bottomMargin=M_BOTTOM,
        title=title_meta or short_title,
        author=author_meta,
    )

    cb = lambda c, d: on_page(c, d, short_title, byline)

    # Page 1: full-width title+abstract strip at top, two columns below
    title_y = PAGE_H - M_TOP - TITLE_STRIP_H   # y-coordinate (from bottom) of bottom of title frame
    f_title = Frame(M_LEFT, title_y, BODY_W, TITLE_STRIP_H, id="title",
                    showBoundary=0)
    f_p1_l  = Frame(M_LEFT,                    M_BOTTOM, COL_W, COL_H_P1, id="p1_left",
                    showBoundary=0)
    f_p1_r  = Frame(M_LEFT + COL_W + COL_GAP,  M_BOTTOM, COL_W, COL_H_P1, id="p1_right",
                    showBoundary=0)

    # Pages 2+: pure two-column
    f_l = Frame(M_LEFT,                   M_BOTTOM, COL_W, BODY_H, id="left",  showBoundary=0)
    f_r = Frame(M_LEFT + COL_W + COL_GAP, M_BOTTOM, COL_W, BODY_H, id="right", showBoundary=0)

    pt_first  = PageTemplate(id="First",  frames=[f_title, f_p1_l, f_p1_r], onPage=cb)
    pt_twocol = PageTemplate(id="TwoCol", frames=[f_l, f_r],                 onPage=cb)

    doc.addPageTemplates([pt_first, pt_twocol])
    return doc


# ── Architecture diagram ──────────────────────────────────────────────────────

def make_arch_diagram(styles: dict, col_width: float) -> list:
    S = styles
    W = col_width - 8

    def cell(title, lines, bg):
        rows = [[Paragraph(title, S["diagram_label"])]] + \
               [[Paragraph(l, S["diagram_body"])] for l in lines]
        t = Table(rows, colWidths=[W - 12])
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (0, 0),  bg),
            ("BACKGROUND",   (0, 1), (-1, -1), colors.white),
            ("BOX",          (0, 0), (-1, -1), 0.75, C_BOX_BDR),
            ("INNERGRID",    (0, 0), (-1, -1), 0.3,  C_RULE),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    warden = cell("Warden: Runtime Monitor", [
        "PreToolUse / PostToolUse hooks",
        "YAML policy engine  •  25+ rules",
        "Shell  •  File  •  Network  •  MCP  •  Prompt",
        "Observe mode  |  Enforce mode",
        "SQLite + JSONL audit trail",
    ], colors.HexColor("#dbeafe"))

    cloak = cell("Cloak: Secret Prevention", [
        "@@SECRET:name@@ placeholder convention",
        "PreToolUse: decloak at execution time",
        "sed-wrap scrubs stdout before recording",
        "UserPromptSubmit: intercepts pasted keys",
        "PostToolUse: scrubs MCP responses",
    ], colors.HexColor("#fef9c3"))

    sweep = cell("Sweep: Secret Cleanup", [
        "Gitleaks-powered residue scan",
        "Claude  •  Cursor  •  Windsurf caches",
        "AES-256-CBC vault  •  Redact / Restore",
        "Run on-demand or via Stop hook",
    ], colors.HexColor("#dcfce7"))

    agent_box = Table(
        [[Paragraph("IDE / Agent  (Claude Code  •  Cursor  •  Windsurf)", S["diagram_body"])]],
        colWidths=[W - 12],
    )
    agent_box.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX",          (0, 0), (-1, -1), 1.0, C_NAVY),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))

    arrow = Paragraph("hooks", S["diagram_body"])

    outer = Table(
        [[agent_box], [arrow], [warden], [arrow], [cloak], [arrow], [sweep]],
        colWidths=[W],
    )
    outer.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))

    return [
        Spacer(1, 6),
        outer,
        Paragraph(
            "Figure 1. Prismor Immunity Agent: three-layer defense architecture.",
            S["diagram_caption"],
        ),
        Spacer(1, 4),
    ]


# ── Inline markdown → ReportLab XML ──────────────────────────────────────────

# Citation pattern: [1], [1, 2], [1–3] etc.
_CIT_RE = re.compile(r'\[(\d[\d,\s\-–]*\d|\d)\]')

def md_inline(text: str, linkify_cites: bool = False) -> str:
    """
    Convert inline markdown to ReportLab paragraph XML.
    Backtick spans processed first to prevent italic regex firing on
    underscores inside code text (LD_PRELOAD, NODE_OPTIONS, etc.).
    If linkify_cites=True, [N] patterns become internal hyperlinks.
    """
    parts = re.split(r'`([^`]+)`', text)
    out = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            safe = (part.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;"))
            out.append(f'<font name="Courier" size="8">{safe}</font>')
        else:
            safe = (part.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;"))
            safe = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', safe)
            safe = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', safe)
            safe = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', safe)
            safe = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', safe)
            if linkify_cites:
                # Link [N] → #ref_N  and  [N, M] → links for each number
                def _link_cit(m):
                    raw = m.group(0)       # e.g. "[1, 3]"
                    nums = re.findall(r'\d+', raw)
                    if len(nums) == 1:
                        n = nums[0]
                        return (f'<link href="#ref_{n}" '
                                f'color="{C_LINK.hexval()}">{raw}</link>')
                    # Multiple numbers: link each individually
                    inner = ", ".join(
                        f'<link href="#ref_{n}" color="{C_LINK.hexval()}">{n}</link>'
                        for n in nums
                    )
                    return f"[{inner}]"
                safe = _CIT_RE.sub(_link_cit, safe)
            out.append(safe)
    return "".join(out)


# ── Abstract extraction ───────────────────────────────────────────────────────

def extract_abstract(md_text: str) -> str:
    """Pull the abstract block out of the markdown. Returns plain text."""
    lines = md_text.splitlines()
    in_abs = False
    buf = []
    for line in lines:
        if line.startswith("## ") and line[3:].strip().lower() == "abstract":
            in_abs = True
            continue
        if in_abs:
            if line.startswith("## "):   # next section
                break
            if line.strip() in ("---", "***", "___"):
                break
            buf.append(line.strip())
    return " ".join(b for b in buf if b)


# ── ASCII table parser ────────────────────────────────────────────────────────

def _is_ascii_table(lines: list[str]) -> bool:
    """Return True if the block looks like a +---+ style ASCII table."""
    content = [l for l in lines if l.strip()]
    if len(content) < 2:
        return False
    sep_lines  = [l for l in content if re.match(r'^\s*\+[-+]+\+\s*$', l)]
    pipe_lines = [l for l in content if l.strip().startswith("|")]
    return len(sep_lines) >= 1 and len(pipe_lines) >= 1


def _col_widths_from_sep(sep_line: str, available_w: float) -> list[float]:
    """Derive proportional column widths from a +---+---+ separator line."""
    # Each segment between + markers gives a relative width in chars
    segs = re.split(r'\+', sep_line.strip())
    segs = [s for s in segs if s]   # remove empties at start/end
    if not segs:
        return []
    chars = [len(s) for s in segs]
    total = sum(chars)
    return [available_w * c / total for c in chars]


def _parse_rows(lines: list[str]) -> list[list[str]]:
    """
    Parse an ASCII table into logical rows.

    Separator lines (+---+) delimit rows.  Content lines (| ... |) between
    separators belong to the same logical row; multi-line cells are joined
    with a space.
    """
    logical_rows: list[list[str]] = []
    current_lines: list[list[str]] = []   # list of column-text lists

    def flush():
        if not current_lines:
            return
        # Merge multi-line cells column-by-column
        num_cols = max(len(r) for r in current_lines)
        merged = []
        for c in range(num_cols):
            parts = []
            for row_line in current_lines:
                if c < len(row_line):
                    v = row_line[c].strip()
                    if v:
                        parts.append(v)
            merged.append(" ".join(parts))
        logical_rows.append(merged)
        current_lines.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'^\+[-+]+\+$', stripped):
            flush()
        elif stripped.startswith("|"):
            # Split on | and strip whitespace from each cell
            cells = [c.strip() for c in stripped.split("|")]
            # Remove empty strings that come from leading/trailing |
            cells = cells[1:-1] if len(cells) > 2 else cells
            current_lines.append(cells)

    flush()
    return logical_rows


def try_parse_ascii_table(code_lines: list[str],
                           styles: dict,
                           col_width: float) -> list | None:
    """
    If code_lines is an ASCII table, parse and return ReportLab flowables.
    Returns None if the block is not a table.
    """
    if not _is_ascii_table(code_lines):
        return None

    # Derive column widths from the first separator line
    sep_line = next((l for l in code_lines if re.match(r'^\s*\+[-+]+\+', l)), None)
    col_widths = _col_widths_from_sep(sep_line, col_width - 4) if sep_line else []

    rows = _parse_rows(code_lines)
    if not rows:
        return None

    S = styles

    # Build Paragraph cells
    tbl_style = ParagraphStyle(
        "TblCell", fontName="Helvetica", fontSize=7, leading=9,
        textColor=C_DARK, alignment=TA_LEFT,
    )
    hdr_style = ParagraphStyle(
        "TblHdr", fontName="Helvetica-Bold", fontSize=7, leading=9,
        textColor=colors.white, alignment=TA_LEFT,
    )

    para_rows = []
    for r_idx, row in enumerate(rows):
        style = hdr_style if r_idx == 0 else tbl_style
        para_rows.append([Paragraph(cell, style) for cell in row])

    # Normalise column count
    max_cols = max(len(r) for r in para_rows)
    for row in para_rows:
        while len(row) < max_cols:
            row.append(Paragraph("", tbl_style))

    # Column widths: use proportional if available, else equal
    if col_widths and len(col_widths) == max_cols:
        cw = col_widths
    else:
        cw = [col_width / max_cols] * max_cols

    t = Table(para_rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0),  C_NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        # Data rows alternating
        ("BACKGROUND",    (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f1f5f9")]),
        # Grid
        ("BOX",           (0, 0), (-1, -1), 0.5, C_RULE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, C_RULE),
        # Padding
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))

    return [Spacer(1, 4), t, Spacer(1, 6)]


# ── Markdown → flowable list ──────────────────────────────────────────────────

def parse_markdown(md_text: str, styles: dict, col_width: float,
                   inject_diagram: bool = True,
                   skip_abstract: bool = False) -> list:
    """
    Parse markdown into ReportLab flowables.
    skip_abstract=True: skip the ## Abstract section (already in title block).
    """
    lines = md_text.splitlines()
    S = styles
    flowables = []

    in_abstract = False
    in_refs = False
    diagram_injected = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # H1 title — skip (rendered in title block)
        if line.startswith("# ") and not line.startswith("## "):
            i += 1
            continue

        # Byline / date line
        if line.startswith("**Prismor Security"):
            i += 1
            continue

        # Explicit diagram marker (only honored when --demo-diagram is set)
        if line.strip() == "<!-- ARCH_DIAGRAM -->":
            if inject_diagram:
                flowables.extend(make_arch_diagram(S, col_width))
                diagram_injected = True
            i += 1
            continue

        # Horizontal rule
        if line.strip() in ("---", "***", "___"):
            if not in_abstract:
                flowables.append(HRFlowable(
                    width="100%", thickness=0.5, color=C_RULE,
                    spaceAfter=4, spaceBefore=4,
                ))
            i += 1
            continue

        # H2 section
        if line.startswith("## "):
            txt = line[3:].strip()

            if txt.lower() == "abstract":
                if skip_abstract:
                    in_abstract = True
                    i += 1
                    continue
                else:
                    in_abstract = False
                    flowables.append(Paragraph("Abstract", S["abstract_h"]))
                    i += 1
                    continue

            # Leaving abstract
            in_abstract = False

            if txt.lower().startswith("reference"):
                in_refs = True
            else:
                in_refs = False

            # Auto-inject diagram before §4
            if inject_diagram and not diagram_injected:
                m = re.match(r'^(\d+)\.', txt)
                if m and int(m.group(1)) >= 4:
                    flowables.extend(make_arch_diagram(S, col_width))
                    diagram_injected = True

            flowables.append(Paragraph(md_inline(txt), S["section"]))
            i += 1
            continue

        # H3 subsection
        if line.startswith("### "):
            in_abstract = False
            txt = line[4:].strip()
            flowables.append(Paragraph(md_inline(txt), S["subsection"]))
            i += 1
            continue

        # H4
        if line.startswith("#### "):
            txt = line[5:].strip()
            flowables.append(Paragraph(f"<b>{md_inline(txt)}</b>", S["body_ni"]))
            i += 1
            continue

        # Skip abstract lines when skip_abstract is True
        if in_abstract and skip_abstract:
            if line.startswith("## "):
                in_abstract = False
                continue   # re-process this line
            i += 1
            continue

        # Blank line
        if not line.strip():
            i += 1
            continue

        # Bullet
        if line.strip().startswith(("- ", "* ", "• ")):
            in_abstract = False
            txt = re.sub(r'^[\s\-\*•]+', '', line)
            flowables.append(Paragraph("• " + md_inline(txt, linkify_cites=True),
                                       S["bullet"]))
            i += 1
            continue

        # Numbered list
        if re.match(r'^\d+\.\s', line.strip()):
            in_abstract = False
            txt = re.sub(r'^\d+\.\s+', '', line.strip())
            flowables.append(Paragraph("• " + md_inline(txt, linkify_cites=True),
                                       S["bullet"]))
            i += 1
            continue

        # Fenced code block
        if line.strip().startswith("```"):
            in_abstract = False
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            if code_lines:
                # If the block looks like an ASCII table, render it properly
                tbl = try_parse_ascii_table(code_lines, S, col_width)
                if tbl is not None:
                    flowables.extend(tbl)
                else:
                    xml = "<br/>".join(
                        f'<font name="Courier" size="7">'
                        + l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        + '</font>'
                        for l in code_lines[:25]
                    )
                    flowables.append(Paragraph(xml, S["code"]))
            continue

        # Reference line: [N] Author...
        if in_refs and re.match(r'^\[(\d+)\]', line.strip()):
            m = re.match(r'^\[(\d+)\]', line.strip())
            ref_n = m.group(1)
            # Insert an anchor so citations can jump here
            flowables.append(AnchorFlowable(f"ref_{ref_n}"))
            flowables.append(Paragraph(md_inline(line.strip()), S["ref"]))
            i += 1
            continue

        # Normal body text
        if line.strip() and not in_abstract:
            flowables.append(Paragraph(md_inline(line.strip(), linkify_cites=True),
                                       S["body"]))
        i += 1

    return flowables


# ── Title block (fills the full-width title frame on page 1) ─────────────────

def build_title_block(styles: dict, title_text: str, abstract_text: str,
                      byline: str = "") -> list:
    S = styles
    flows = [
        Spacer(1, 0.08 * inch),
        Paragraph(md_inline(title_text), S["title"]),
        Spacer(1, 0.04 * inch),
        HRFlowable(width="55%", thickness=1.5, color=C_BLUE,
                   hAlign="CENTER", spaceBefore=2, spaceAfter=3),
    ]
    if byline:
        flows.append(Paragraph(byline, S["subtitle"]))
    if abstract_text:
        flows += [
            Paragraph("Abstract", S["abstract_h"]),
            Paragraph(md_inline(abstract_text), S["abstract"]),
        ]
    flows += [Spacer(1, 0.06 * inch)]
    return flows


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input",       required=True, help="Input Markdown file")
    p.add_argument("--output",      required=True, help="Output PDF path")
    p.add_argument("--title",       default=None,
                   help="Full paper title (read from first # heading if omitted)")
    p.add_argument("--title-short", dest="title_short", default=None,
                   help="Short title for header")
    p.add_argument("--byline",      default="",
                   help="Optional byline / venue strap shown under the title and "
                        "in the right side of the page header (e.g. "
                        "'NeurIPS 2026 Submission' or 'GC Biopharma · April 2026')")
    p.add_argument("--author",      default="",
                   help="Author string written into PDF metadata")
    p.add_argument("--demo-diagram", dest="demo_diagram", action="store_true",
                   help="Insert the legacy Prismor Immunity Agent demo "
                        "architecture diagram (auto-injected before §4 and on "
                        "<!-- ARCH_DIAGRAM --> markers). Off by default.")
    args = p.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        print(f"ERROR: {md_path} not found", file=sys.stderr)
        return 1

    md_text = md_path.read_text(encoding="utf-8")

    # Extract title
    title = args.title
    if not title:
        m = re.search(r'^# (.+)', md_text, re.MULTILINE)
        title = m.group(1).strip() if m else md_path.stem

    short_title = args.title_short or (title[:60] + "..." if len(title) > 60 else title)

    # Extract abstract separately so it goes into the full-width title frame
    abstract_text = extract_abstract(md_text)

    styles = make_styles()
    doc    = build_doc(args.output, short_title,
                       title_meta=title, author_meta=args.author,
                       byline=args.byline)

    # Title block (full-width): title + abstract
    title_block = build_title_block(styles, title, abstract_text,
                                    byline=args.byline)

    # Body flowables: skip the abstract (already in title block)
    # FrameBreak pushes remaining title-frame space into the two-column area
    body_flows = (
        [FrameBreak()]   # end title frame, start left column on page 1
        + [NextPageTemplate("TwoCol")]
        + parse_markdown(
            md_text, styles, col_width=COL_W,
            inject_diagram=args.demo_diagram,
            skip_abstract=True,
        )
    )

    story = title_block + body_flows
    doc.build(story)

    size_kb = Path(args.output).stat().st_size // 1024
    print(f"PDF written: {args.output}  ({size_kb} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
