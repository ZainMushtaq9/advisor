"""Phase 22 report runner (DB writes live here; assembly only
reads, rendering only formats).

Idempotency: templates by (template_key, version); reports by
(template_key, subject_key, report_date, data_cutoff_date,
template_version) among current rows; sections/figures/
warnings/exports are written once per report id, so a second
--commit reuses the report and writes nothing new.

Approval: DRAFT -> APPROVED or DRAFT -> REJECTED only, via the
CLI. APPROVED means internally reviewed; there is no publish
step and no external send anywhere, so an APPROVED report is
still internal. A report is never edited in place; a newer
version supersedes it.

Exports: Markdown and HTML are written under
docs/phase-22/reports/ (committed as the readable archive).
PDFs are written under storage/research_reports/ (gitignored;
the project never commits PDFs) and only their SHA-256 and
path are recorded in report_exports.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import date as _date

from app.models.reports import (
    Report,
    ReportExport,
    ReportFigure,
    ReportSection,
    ReportTemplate,
    ReportWarning,
)
from app.services.reports import DATA_CUTOFF_DATE, REPORT_DATE, TEMPLATES
from app.services.reports.assembly import SEED_REPORTS, build_draft
from app.services.reports.render import (
    render_html,
    render_markdown,
    render_pdf,
)
from app.services.reports.validation import qa_draft


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()


def repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    # backend/app/services/reports/runner.py -> repo root is
    # four levels up (reports -> services -> app -> backend ->
    # root).
    return os.path.abspath(os.path.join(here, "..", "..", "..", ".."))


def seed_templates(session) -> dict:
    """Insert missing template rows; return counts."""
    created = 0
    for key, tpl in TEMPLATES.items():
        existing = session.query(ReportTemplate).filter_by(template_key=key, version="v1").first()
        if existing is None:
            session.add(
                ReportTemplate(
                    template_key=key,
                    version="v1",
                    title=tpl["title"],
                    audience=tpl["audience"],
                    sections=[{"key": k, "title": t} for k, t in tpl["sections"]],
                    methodology=tpl["methodology"],
                    disclosure="See app.services.reports.DISCLAIMER.",
                )
            )
            created += 1
    return {"created": created}


def find_report(session, template_key: str, subject_key: str):
    return (
        session.query(Report)
        .filter_by(
            template_key=template_key,
            subject_key=subject_key,
            report_date=REPORT_DATE,
            data_cutoff_date=DATA_CUTOFF_DATE,
            template_version="v1",
            is_current=True,
        )
        .first()
    )


def _write_export_files(draft: dict, report: Report) -> list[dict]:
    """Render all formats and write files. Returns export rows
    to insert (format, sha256, location). Raises on any render
    failure before any file is written for that format."""
    root = repo_root()
    md_dir = os.path.join(root, "docs", "phase-22", "reports")
    pdf_dir = os.path.join(root, "storage", "research_reports")
    os.makedirs(md_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    stem = (
        f"{draft['header']['template_key']}__"
        f"{slug(draft['header']['subject_key'])}__{REPORT_DATE.isoformat()}"
    )
    markdown = render_markdown(draft)
    html_doc = render_html(draft)
    pdf_status, pdf_bytes = render_pdf(draft)
    exports: list[dict] = []
    for name, content, subdir in (
        ("markdown", markdown, md_dir),
        ("html", html_doc, md_dir),
    ):
        ext = "md" if name == "markdown" else "html"
        path = os.path.join(subdir, f"{stem}.{ext}")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        exports.append(
            {
                "export_format": name,
                "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "storage_location": os.path.relpath(path, root),
            }
        )
    if pdf_status == "ok" and pdf_bytes is not None:
        path = os.path.join(pdf_dir, f"{stem}.pdf")
        with open(path, "wb") as handle:
            handle.write(pdf_bytes)
        exports.append(
            {
                "export_format": "pdf",
                "content_hash": hashlib.sha256(pdf_bytes).hexdigest(),
                "storage_location": os.path.relpath(path, root),
            }
        )
    return exports


def _persist_draft(session, draft: dict, template_row: ReportTemplate) -> Report:
    header = draft["header"]
    report = Report(
        template_id=template_row.id,
        template_key=header["template_key"],
        template_version=header["template_version"],
        subject_type=header["subject_type"],
        subject_key=header["subject_key"],
        subject_label=header["subject_label"],
        report_date=REPORT_DATE,
        data_cutoff_date=DATA_CUTOFF_DATE,
        audience=header["audience"],
        status="DRAFT",
        snapshot={
            "methodology": header["methodology"],
            "template_sections": [s["section_key"] for s in draft["sections"]],
        },
    )
    if header.get("price_date"):
        year, month, day = (int(p) for p in header["price_date"].split("-"))
        report.price_date = _date(year, month, day)
    session.add(report)
    session.flush()
    for position, sec in enumerate(draft["sections"]):
        session.add(
            ReportSection(
                report_id=report.id,
                section_key=sec["section_key"],
                title=sec["title"],
                position=position,
                body_markdown=sec["body_markdown"],
            )
        )
    for fig in draft["figures"]:
        session.add(
            ReportFigure(
                report_id=report.id,
                figure_key=fig["figure_key"],
                label=fig["label"],
                value=fig["value"],
                value_text=fig.get("value_text"),
                unit=fig.get("unit"),
                computation_status=fig["computation_status"],
                figure_kind=fig["kind"],
                source_table=fig["source_table"],
                source_row_ids=fig["source_row_ids"],
                source_note=fig["source_note"],
                quality_status=fig["quality_status"],
            )
        )
    for warning in draft["warnings"]:
        session.add(
            ReportWarning(
                report_id=report.id,
                warning_kind=warning["warning_kind"],
                message=warning["message"],
                source_table=warning["source_table"],
                source_row_ids=warning["source_row_ids"],
            )
        )
    for export in _write_export_files(draft, report):
        session.add(
            ReportExport(
                report_id=report.id,
                export_format=export["export_format"],
                content_hash=export["content_hash"],
                storage_location=export["storage_location"],
            )
        )
    return report


def generate(
    session, template_key: str | None = None, subject_key: str | None = None, commit: bool = False
) -> dict:
    """Generate drafts for the seed list (optionally filtered),
    QA each, and commit the passing ones idempotently."""
    seed_templates(session)
    targets = [
        (t, s)
        for (t, s) in SEED_REPORTS
        if (template_key is None or t == template_key) and (subject_key is None or s == subject_key)
    ]
    if not targets:
        return {"error": "no matching seed reports", "generated": []}
    results: list[dict] = []
    for tpl_key, subj_key in targets:
        try:
            draft = build_draft(session, tpl_key, subj_key)
        except Exception as exc:  # noqa: BLE001 - reported, not hidden
            session.rollback()
            results.append(
                {
                    "template": tpl_key,
                    "subject": subj_key,
                    "status": "build_failed",
                    "error": str(exc),
                }
            )
            continue
        problems = qa_draft(draft)
        if problems:
            results.append(
                {
                    "template": tpl_key,
                    "subject": subj_key,
                    "status": "qa_failed",
                    "problems": problems,
                }
            )
            continue
        existing = find_report(session, tpl_key, subj_key)
        if existing is not None:
            results.append(
                {
                    "template": tpl_key,
                    "subject": subj_key,
                    "status": "skipped_existing",
                    "report_id": existing.id,
                    "figures": len(draft["figures"]),
                    "warnings": len(draft["warnings"]),
                }
            )
            continue
        if not commit:
            results.append(
                {
                    "template": tpl_key,
                    "subject": subj_key,
                    "status": "would_write",
                    "figures": len(draft["figures"]),
                    "warnings": len(draft["warnings"]),
                    "sections": len(draft["sections"]),
                }
            )
            continue
        template_row = (
            session.query(ReportTemplate).filter_by(template_key=tpl_key, version="v1").first()
        )
        report = _persist_draft(session, draft, template_row)
        session.commit()
        results.append(
            {
                "template": tpl_key,
                "subject": subj_key,
                "status": "created",
                "report_id": report.id,
                "figures": len(draft["figures"]),
                "warnings": len(draft["warnings"]),
                "sections": len(draft["sections"]),
            }
        )
    if not commit:
        session.rollback()
    return {"generated": results}


def approve(session, report_id: int) -> dict:
    report = session.query(Report).filter_by(id=report_id).first()
    if report is None:
        return {"error": "unknown report id"}
    if report.status != "DRAFT":
        return {"error": f"cannot approve from status {report.status}"}
    report.status = "APPROVED"
    session.commit()
    return {"report_id": report_id, "status": "APPROVED"}


def reject(session, report_id: int) -> dict:
    report = session.query(Report).filter_by(id=report_id).first()
    if report is None:
        return {"error": "unknown report id"}
    if report.status != "DRAFT":
        return {"error": f"cannot reject from status {report.status}"}
    report.status = "REJECTED"
    session.commit()
    return {"report_id": report_id, "status": "REJECTED"}


def list_reports(session) -> list[dict]:
    rows = (
        session.query(Report)
        .filter_by(is_current=True)
        .order_by(Report.template_key, Report.subject_key)
        .all()
    )
    return [
        {
            "id": r.id,
            "template": r.template_key,
            "subject": r.subject_key,
            "subject_label": r.subject_label,
            "report_date": r.report_date.isoformat(),
            "status": r.status,
        }
        for r in rows
    ]
