from __future__ import annotations

import os
import re
import tempfile
from html import escape
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)


def sanitize_download_stem(raw: str) -> str:
    """Filesystem-safe basename stem (no path separators)."""
    stem = re.sub(r"[^\w.\-]+", "_", raw, flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem).strip("._") or "itinerary"
    return stem[:180]


def write_temp_markdown(text: str, stem: str) -> str:
    fd, path_str = tempfile.mkstemp(prefix=f"{stem}_", suffix=".md", text=True)
    os.close(fd)
    path = Path(path_str)
    path.write_text(text, encoding="utf-8")
    return str(path)


def _inline_md_to_reportlab_html(line: str) -> str:
    """Escape then apply a small subset of inline markdown for ReportLab Paragraph."""
    s = escape(line)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"__(.+?)__", r"<b>\1</b>", s)
    s = re.sub(r"(?<![*])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", s)
    return s


def _markdown_table_block(lines: list[str]) -> tuple[str, int]:
    """If lines start a GFM table, return (preformatted text, num lines consumed)."""
    if len(lines) < 2 or "|" not in lines[0]:
        return "", 0
    sep = lines[1].strip()
    if not re.match(r"^\|?[\s\-:|]+\|", sep):
        return "", 0
    block: list[str] = []
    i = 0
    while i < len(lines) and "|" in lines[i]:
        block.append(lines[i])
        i += 1
    return "\n".join(block) + "\n", i


def write_temp_pdf(text: str, stem: str) -> str:
    """Render markdown to a simple PDF (headers, lists, paragraphs, code blocks, tables as monospace)."""
    _, path_str = tempfile.mkstemp(prefix=f"{stem}_", suffix=".pdf")
    path = Path(path_str)

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=10,
            spaceBefore=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontSize=13,
            spaceAfter=8,
            spaceBefore=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H3",
            parent=styles["Heading3"],
            fontSize=11,
            spaceAfter=6,
            spaceBefore=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeMono",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=8.5,
            leading=11,
        )
    )

    code_style = styles["CodeMono"]
    story: list = []
    raw_lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    in_code = False
    code_buf: list[str] = []

    while i < len(raw_lines):
        line = raw_lines[i]

        if line.strip().startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_buf), code_style, maxLineLength=120))
                story.append(Spacer(1, 0.12 * inch))
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 0.08 * inch))
            i += 1
            continue

        table_text, consumed = _markdown_table_block(raw_lines[i:])
        if consumed:
            story.append(Preformatted(table_text.rstrip(), code_style, maxLineLength=None))
            story.append(Spacer(1, 0.1 * inch))
            i += consumed
            continue

        if stripped.startswith("# "):
            story.append(Paragraph(_inline_md_to_reportlab_html(stripped[2:]), styles["H1"]))
        elif stripped.startswith("## "):
            story.append(Paragraph(_inline_md_to_reportlab_html(stripped[3:]), styles["H2"]))
        elif stripped.startswith("### "):
            story.append(Paragraph(_inline_md_to_reportlab_html(stripped[4:]), styles["H3"]))
        elif re.match(r"^[\-\*]\s+", stripped):
            bullets: list[str] = []
            while i < len(raw_lines):
                s = raw_lines[i].strip()
                m = re.match(r"^[\-\*]\s+(.+)$", s)
                if not m:
                    break
                bullets.append(m.group(1))
                i += 1
            items = [
                ListItem(Paragraph(_inline_md_to_reportlab_html(b), styles["BodySmall"]))
                for b in bullets
            ]
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=18))
            story.append(Spacer(1, 0.08 * inch))
            continue
        elif re.match(r"^\d+\.\s+", stripped):
            items: list[str] = []
            while i < len(raw_lines):
                s = raw_lines[i].strip()
                m = re.match(r"^\d+\.\s+(.+)$", s)
                if not m:
                    break
                items.append(m.group(1))
                i += 1
            numbered = [
                ListItem(Paragraph(_inline_md_to_reportlab_html(t), styles["BodySmall"]))
                for t in items
            ]
            story.append(ListFlowable(numbered, bulletType="1", leftIndent=22))
            story.append(Spacer(1, 0.08 * inch))
            continue
        else:
            # Optional: treat --- as horizontal rule
            if re.match(r"^[\-\*_]{3,}\s*$", stripped):
                story.append(Spacer(1, 0.12 * inch))
            else:
                story.append(Paragraph(_inline_md_to_reportlab_html(line), styles["BodySmall"]))

        i += 1

    if in_code and code_buf:
        story.append(Preformatted("\n".join(code_buf), code_style, maxLineLength=120))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
    )
    doc.build(story)
    return str(path)


def build_download_file(markdown_text: str, stem: str, format_choice: str) -> str | None:
    """Return path to temp file or None when there is nothing to export."""
    if not markdown_text.strip():
        return None
    safe = sanitize_download_stem(stem)
    fmt = format_choice.strip().lower()
    if fmt.startswith("pdf"):
        return write_temp_pdf(markdown_text, safe)
    return write_temp_markdown(markdown_text, safe)
