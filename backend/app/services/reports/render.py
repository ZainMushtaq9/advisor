"""Renderers for Phase 22 report drafts: Markdown (canonical),
HTML (standalone page), PDF (fpdf2, free pure-Python).

Layout QA rule: a render that raises is a failure, never a
partial file. Callers write files only after the full render
succeeds. The PDF renderer returns ("not_available", None)
when fpdf2 is not installed instead of failing the whole run;
genuine rendering errors propagate.
"""

from __future__ import annotations

import html as html_lib
import re

from app.services.reports.evidence import fmt_figure


def render_markdown(draft: dict) -> str:
    header = draft["header"]
    lines: list[str] = [
        f"# {header['title']}: {header['subject_label']}",
        "",
        f"Report date: {header['report_date']} | "
        f"Data cut-off: {header['data_cutoff_date']} | "
        f"Price date: {header.get('price_date') or 'not available'} | "
        f"Audience: {header['audience']} | Status: DRAFT",
        "",
    ]
    for sec in draft["sections"]:
        lines.append(f"## {sec['title']}")
        lines.append("")
        lines.append(sec["body_markdown"])
        lines.append("")
    lines.append("## Figures")
    lines.append("")
    lines.append("| Figure | Value | Status | Kind | Source |")
    lines.append("|---|---|---|---|---|")
    for fig in draft["figures"]:
        lines.append(
            f"| {fig['label']} | {fmt_figure(fig)}"
            f"{' ' + fig['unit'] if fig.get('unit') else ''} | "
            f"{fig['computation_status']} | {fig['kind']} | "
            f"{fig['source_table']} |"
        )
    lines.append("")
    if draft["warnings"]:
        lines.append("## Warnings")
        lines.append("")
        for warning in draft["warnings"]:
            lines.append(f"- [{warning['warning_kind']}] {warning['message']}")
        lines.append("")
    return "\n".join(lines)


def _md_to_html(md_text: str) -> str:
    """Small converter for the emitted subset only: ##
    headings, paragraphs, bullet lists, **bold**."""
    out: list[str] = []
    in_list = False
    for raw in md_text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h2>{html_lib.escape(line[3:].strip())}</h2>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            body = html_lib.escape(line[2:].strip())
            body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
            out.append(f"<li>{body}</li>")
        elif line == "":
            if in_list:
                out.append("</ul>")
                in_list = False
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            body = html_lib.escape(line)
            body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
            out.append(f"<p>{body}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def render_html(draft: dict) -> str:
    header = draft["header"]
    parts: list[str] = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'>",
        f"<title>{html_lib.escape(header['title'])}: "
        f"{html_lib.escape(header['subject_label'])}</title>",
        "<style>body{font-family:sans-serif;max-width:900px;margin:auto;"
        "padding:1em}table{border-collapse:collapse}td,th{border:1px "
        "solid #ccc;padding:4px 8px;text-align:left}</style>",
        "</head><body>",
        f"<h1>{html_lib.escape(header['title'])}: {html_lib.escape(header['subject_label'])}</h1>",
        f"<p>Report date: {header['report_date']} | Data cut-off: "
        f"{header['data_cutoff_date']} | Price date: "
        f"{header.get('price_date') or 'not available'} | Audience: "
        f"{header['audience']} | Status: DRAFT</p>",
    ]
    for sec in draft["sections"]:
        parts.append(f"<h2>{html_lib.escape(sec['title'])}</h2>")
        parts.append(_md_to_html(sec["body_markdown"]))
    parts.append("<h2>Figures</h2>")
    parts.append(
        "<table><tr><th>Figure</th><th>Value</th><th>Status</th><th>Kind</th><th>Source</th></tr>"
    )
    for fig in draft["figures"]:
        parts.append(
            f"<tr><td>{html_lib.escape(fig['label'])}</td>"
            f"<td>{html_lib.escape(fmt_figure(fig))}"
            f"{' ' + html_lib.escape(fig['unit']) if fig.get('unit') else ''}</td>"
            f"<td>{fig['computation_status']}</td>"
            f"<td>{fig['kind']}</td>"
            f"<td>{html_lib.escape(fig['source_table'])}</td></tr>"
        )
    parts.append("</table>")
    if draft["warnings"]:
        parts.append("<h2>Warnings</h2><ul>")
        for warning in draft["warnings"]:
            parts.append(
                f"<li>[{html_lib.escape(warning['warning_kind'])}] "
                f"{html_lib.escape(warning['message'])}</li>"
            )
        parts.append("</ul>")
    parts.append("</body></html>")
    return "\n".join(parts)


def render_pdf(draft: dict):
    """Return ("ok", bytes) or ("not_available", None)."""
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError:
        return "not_available", None
    header = draft["header"]
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(
        0, 8, f"{header['title']}: {header['subject_label']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0,
        6,
        f"Report date: {header['report_date']} | Data cut-off: "
        f"{header['data_cutoff_date']} | Price date: "
        f"{header.get('price_date') or 'not available'} | Status: DRAFT",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    for sec in draft["sections"]:
        pdf.set_font("Helvetica", "B", 12)
        pdf.multi_cell(0, 7, sec["title"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        safe = sec["body_markdown"].encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 6, safe, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 12)
    pdf.multi_cell(0, 7, "Figures", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    for fig in draft["figures"]:
        line = (
            f"{fig['label']}: {fmt_figure(fig)}"
            f"{' ' + fig['unit'] if fig.get('unit') else ''} "
            f"[{fig['computation_status']}]"
        )
        pdf.multi_cell(
            0,
            6,
            line.encode("latin-1", "replace").decode("latin-1"),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
    if draft["warnings"]:
        pdf.set_font("Helvetica", "B", 12)
        pdf.multi_cell(0, 7, "Warnings", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        for warning in draft["warnings"]:
            text = f"[{warning['warning_kind']}] {warning['message']}"
            pdf.multi_cell(
                0,
                6,
                text.encode("latin-1", "replace").decode("latin-1"),
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
    return "ok", bytes(pdf.output())
