"""Phase 22 report center read-only endpoints (GET only).

Everything here is read from stored rows or explained as
absent with a reason. No value is ever fabricated, and no
endpoint writes anything: report generation, approval, and
rejection run through the CLI. A report is an internal
research document: it is not an investment opportunity, not a
recommendation, and not a forecast, and it is never published
externally. Phase 15 user-facing values are WITHHELD, Phase
13 forecasts are abstained, and this phase reintroduces
neither. No price target appears in any report. No order path
exists anywhere in this project.

Endpoints:
  GET /api/v1/reports/templates
      Seeded report template definitions.
  GET /api/v1/reports
      Reports, paginated and filterable (limit 1..100,
      offset >= 0; template, subject_key, status optional).
  GET /api/v1/reports/{id}
      One report with its sections, figures, warnings, and
      exports.
  GET /api/v1/reports/status
      Counts by template and status.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.database import get_session_factory
from app.models.reports import (
    Report,
    ReportExport,
    ReportFigure,
    ReportSection,
    ReportWarning,
)
from app.services.reports import TEMPLATES
from app.services.reports.evidence import fmt_figure

router = APIRouter(tags=["reports"])


def _session(request: Request):
    factory = get_session_factory(request.app.state.engine)
    return factory()


def _paginate(items: list, limit: int, offset: int) -> dict:
    if limit < 1 or limit > 100 or offset < 0:
        raise HTTPException(status_code=400, detail="bad pagination")
    return {
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "items": items[offset : offset + limit],
    }


def _report_view(row: Report) -> dict:
    return {
        "id": row.id,
        "template_key": row.template_key,
        "template_version": row.template_version,
        "subject_type": row.subject_type,
        "subject_key": row.subject_key,
        "subject_label": row.subject_label,
        "report_date": row.report_date.isoformat(),
        "data_cutoff_date": row.data_cutoff_date.isoformat(),
        "price_date": row.price_date.isoformat() if row.price_date else None,
        "audience": row.audience,
        "status": row.status,
        "quality_status": row.quality_status,
    }


@router.get("/reports/templates")
def list_templates():
    return {
        "templates": [
            {
                "template_key": key,
                "title": tpl["title"],
                "audience": tpl["audience"],
                "sections": [k for k, _ in tpl["sections"]],
                "methodology": tpl["methodology"],
            }
            for key, tpl in TEMPLATES.items()
        ]
    }


@router.get("/reports")
def list_reports(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    template: str | None = None,
    subject_key: str | None = None,
    status: str | None = None,
):
    session = _session(request)
    try:
        query = session.query(Report).filter_by(is_current=True)
        if template:
            query = query.filter_by(template_key=template)
        if subject_key:
            query = query.filter_by(subject_key=subject_key)
        if status:
            query = query.filter_by(status=status)
        rows = query.order_by(Report.template_key, Report.subject_key).all()
        views = [_report_view(r) for r in rows]
        return _paginate(views, limit, offset)
    finally:
        session.close()


@router.get("/reports/status")
def reports_status(request: Request):
    session = _session(request)
    try:
        rows = session.query(Report).filter_by(is_current=True).all()
        by_template: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for row in rows:
            by_template[row.template_key] = by_template.get(row.template_key, 0) + 1
            by_status[row.status] = by_status.get(row.status, 0) + 1
        return {
            "total": len(rows),
            "by_template": by_template,
            "by_status": by_status,
            "published_externally": 0,
            "note": "No report is ever published externally; APPROVED "
            "means internally reviewed only.",
        }
    finally:
        session.close()


@router.get("/reports/{report_id}")
def get_report(request: Request, report_id: int):
    session = _session(request)
    try:
        row = session.query(Report).filter_by(id=report_id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="unknown report")
        sections = (
            session.query(ReportSection)
            .filter_by(report_id=report_id)
            .order_by(ReportSection.position)
            .all()
        )
        figures = (
            session.query(ReportFigure)
            .filter_by(report_id=report_id)
            .order_by(ReportFigure.figure_key)
            .all()
        )
        warnings = (
            session.query(ReportWarning)
            .filter_by(report_id=report_id)
            .order_by(ReportWarning.id)
            .all()
        )
        exports = (
            session.query(ReportExport)
            .filter_by(report_id=report_id)
            .order_by(ReportExport.export_format)
            .all()
        )
        view = _report_view(row)
        view["sections"] = [
            {
                "section_key": s.section_key,
                "title": s.title,
                "body_markdown": s.body_markdown,
            }
            for s in sections
        ]
        view["figures"] = [
            {
                "figure_key": f.figure_key,
                "label": f.label,
                "value": fmt_figure(
                    {
                        "value": f.value,
                        "value_text": f.value_text,
                    }
                ),
                "unit": f.unit,
                "computation_status": f.computation_status,
                "figure_kind": f.figure_kind,
                "source_table": f.source_table,
                "source_row_ids": f.source_row_ids,
                "source_note": f.source_note,
                "quality_status": f.quality_status,
            }
            for f in figures
        ]
        view["warnings"] = [
            {
                "warning_kind": w.warning_kind,
                "message": w.message,
                "source_table": w.source_table,
                "source_row_ids": w.source_row_ids,
            }
            for w in warnings
        ]
        view["exports"] = [
            {
                "export_format": e.export_format,
                "content_hash": e.content_hash,
                "storage_location": e.storage_location,
            }
            for e in exports
        ]
        return view
    finally:
        session.close()
