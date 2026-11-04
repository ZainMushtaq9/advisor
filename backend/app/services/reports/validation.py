"""Pure QA for a Phase 22 report draft (dict form).

A draft passes only when every rule below holds. QA failure
refuses the commit: a report with a missing cut-off, a
missing disclaimer, a forbidden recommendation, an invalid
figure, or a section with no cited figure and no "not
available" statement is never stored and never exported.
"""

from __future__ import annotations

import re

from app.services.reports import DISCLAIMER, TEMPLATES
from app.services.reports.evidence import check_figure

FORBIDDEN_PATTERNS = (
    re.compile(r"target price", re.IGNORECASE),
    re.compile(r"\bBUY\b.{0,20}\bshares\b", re.IGNORECASE),
    re.compile(r"\bSELL\b.{0,20}\bshares\b", re.IGNORECASE),
    re.compile(r"place an order", re.IGNORECASE),
    re.compile(r"execute a trade", re.IGNORECASE),
    re.compile(r"guaranteed return", re.IGNORECASE),
)


def qa_draft(draft: dict) -> list[str]:
    """Return QA problems for a draft dict (empty means pass)."""
    problems: list[str] = []
    header = draft.get("header", {})
    template_key = header.get("template_key")
    template = TEMPLATES.get(template_key or "")
    if template is None:
        return [f"unknown template {template_key!r}"]
    if not header.get("data_cutoff_date"):
        problems.append("data cut-off date missing")
    if not header.get("report_date"):
        problems.append("report date missing")
    sections = draft.get("sections", [])
    expected = [key for key, _ in template["sections"]]
    actual = [s.get("section_key") for s in sections]
    if actual != expected:
        problems.append(f"section list mismatch: expected {expected}, got {actual}")
    bodies = "\n".join(s.get("body_markdown", "") for s in sections)
    if DISCLAIMER not in bodies:
        problems.append("disclaimer missing from report body")
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(bodies):
            problems.append(f"forbidden wording in body: {pattern.pattern!r}")
    figures = draft.get("figures", [])
    if not figures:
        problems.append("report has no figures")
    figure_keys = {f.get("figure_key") for f in figures}
    for fig in figures:
        for problem in check_figure(fig):
            problems.append(f"figure {fig.get('figure_key')}: {problem}")
    for sec in sections:
        if sec.get("section_key") == "disclosures":
            continue
        body = sec.get("body_markdown", "")
        cites = any(key in body for key in figure_keys)
        if not cites and "not available" not in body:
            problems.append(
                f"section {sec.get('section_key')} cites no figure "
                "and does not state 'not available'"
            )
    return problems
