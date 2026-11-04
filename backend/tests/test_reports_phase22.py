"""Phase 22 pure tests (no DB, no network).

Covers the template registry, figure validation rules,
cut-off enforcement, the stale-warning threshold,
unknown-date handling, QA pass/fail, Markdown/HTML/PDF
rendering, section-order enforcement in build_draft, and the
no-execution / GET-only endpoint scans that every phase
since Phase 15 carries.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pytest

from app.services.reports import (
    DATA_CUTOFF_DATE,
    DISCLAIMER,
    TEMPLATES,
)
from app.services.reports.assembly import build_draft
from app.services.reports.evidence import (
    after_cutoff,
    check_figure,
    figure,
    fmt_value,
    stale_days,
    stale_warning,
)
from app.services.reports.render import (
    render_html,
    render_markdown,
    render_pdf,
)
from app.services.reports.validation import qa_draft


def _good_figure(**overrides):
    base = {
        "figure_key": "close_price",
        "label": "Close price",
        "kind": "sourced_fact",
        "computation_status": "computed",
        "value": 197.24,
        "unit": "PKR",
        "source_table": "market_prices",
        "source_row_ids": [1],
        "source_note": "Stored close.",
        "quality_status": "UNVERIFIED",
    }
    base.update(overrides)
    return base


def _good_draft(**overrides):
    sections = [
        {"section_key": key, "title": title, "body_markdown": "Body citing close_price."}
        for key, title in TEMPLATES["company_dossier"]["sections"]
    ]
    disclosures = sections[-1]
    disclosures["body_markdown"] = "Methodology. " + DISCLAIMER
    draft = {
        "header": {
            "template_key": "company_dossier",
            "template_version": "v1",
            "title": "Company Dossier",
            "subject_type": "company",
            "subject_key": "HUBC",
            "subject_label": "HUBC",
            "report_date": "2026-11-04",
            "data_cutoff_date": "2026-11-04",
            "price_date": "2026-11-03",
            "audience": "internal_research",
            "methodology": "Stored rows only.",
        },
        "sections": sections,
        "figures": [_good_figure()],
        "warnings": [],
    }
    draft.update(overrides)
    return draft


# ----------------------------------------------------------------
# Registry
# ----------------------------------------------------------------


def test_registry_has_eight_templates():
    assert set(TEMPLATES) == {
        "company_dossier",
        "earnings_update",
        "valuation_report",
        "sector_outlook",
        "event_brief",
        "portfolio_review",
        "risk_report",
        "market_overview",
    }
    for key, tpl in TEMPLATES.items():
        assert tpl["title"] and tpl["audience"] and tpl["methodology"]
        assert tpl["sections"], f"{key} has no sections"
        assert tpl["sections"][-1][0] == "disclosures", key


def test_no_price_target_template_or_kind():
    blob = str(TEMPLATES)
    assert "price_target" not in blob


# ----------------------------------------------------------------
# Figure validation
# ----------------------------------------------------------------


def test_computed_figure_needs_exactly_one_value_form():
    with pytest.raises(ValueError):
        figure(
            "x",
            "X",
            kind="sourced_fact",
            status="computed",
            source_table="t",
            source_row_ids=[],
            source_note="n",
        )
    with pytest.raises(ValueError):
        figure(
            "x",
            "X",
            kind="sourced_fact",
            status="computed",
            value=1,
            value_text="2026-11-03",
            source_table="t",
            source_row_ids=[],
            source_note="n",
        )
    ok = figure(
        "x",
        "X",
        kind="sourced_fact",
        status="computed",
        value=1,
        source_table="t",
        source_row_ids=[],
        source_note="n",
    )
    assert ok["value"] == 1
    ok_text = figure(
        "x",
        "X",
        kind="sourced_fact",
        status="computed",
        value_text="2026-11-03",
        source_table="t",
        source_row_ids=[],
        source_note="n",
    )
    assert ok_text["value_text"] == "2026-11-03"


def test_non_computed_figure_carries_no_value():
    with pytest.raises(ValueError):
        figure(
            "x",
            "X",
            kind="model_output",
            status="insufficient_inputs",
            value=1,
            source_table="t",
            source_row_ids=[],
            source_note="n",
        )
    ok = figure(
        "x",
        "X",
        kind="model_output",
        status="insufficient_inputs",
        source_table="t",
        source_row_ids=[],
        source_note="n",
    )
    assert ok["value"] is None and ok["value_text"] is None


def test_price_target_rejected():
    with pytest.raises(ValueError):
        figure(
            "price_target",
            "Target",
            kind="model_output",
            status="computed",
            value=250,
            source_table="t",
            source_row_ids=[],
            source_note="n",
        )
    problems = check_figure(_good_figure(figure_key="price_target"))
    assert any("price_target" in p for p in problems)


def test_analyst_inference_never_computed():
    with pytest.raises(ValueError):
        figure(
            "x",
            "X",
            kind="analyst_inference",
            status="computed",
            value_text="judgement",
            source_table="t",
            source_row_ids=[],
            source_note="n",
        )


def test_fmt_value_never_zero_fills():
    assert fmt_value(None, None) == "not available"
    assert fmt_value(0) == "0"


# ----------------------------------------------------------------
# Cut-off, stale, unknown dates
# ----------------------------------------------------------------


def test_after_cutoff():
    assert after_cutoff(date(2026, 11, 5)) is True
    assert after_cutoff(date(2026, 11, 4)) is False
    assert after_cutoff("2026-11-20") is True
    assert after_cutoff(None) is False


def test_stale_threshold_is_365_days():
    assert stale_days(date(2025, 11, 4), DATA_CUTOFF_DATE) == 365
    assert stale_warning(date(2025, 11, 4)) is None
    assert stale_days(date(2025, 11, 3), DATA_CUTOFF_DATE) == 366
    assert stale_warning(date(2025, 11, 3)) is not None
    assert stale_days(None) is None
    assert stale_warning(None) is None


# ----------------------------------------------------------------
# QA
# ----------------------------------------------------------------


def test_qa_passes_on_good_draft():
    assert qa_draft(_good_draft()) == []


def test_qa_fails_without_cutoff_or_date():
    draft = _good_draft()
    draft["header"] = {**draft["header"], "data_cutoff_date": ""}
    assert any("cut-off" in p for p in qa_draft(draft))
    draft = _good_draft()
    draft["header"] = {**draft["header"], "report_date": ""}
    assert any("report date" in p for p in qa_draft(draft))


def test_qa_fails_without_disclaimer():
    draft = _good_draft()
    draft["sections"][-1]["body_markdown"] = "No disclaimer here."
    assert any("disclaimer" in p for p in qa_draft(draft))


def test_qa_rejects_forbidden_wording():
    for wording in (
        "target price Rs 250",
        "BUY 100 shares",
        "place an order",
        "execute a trade",
        "guaranteed return",
    ):
        draft = _good_draft()
        draft["sections"][0]["body_markdown"] = f"Body citing close_price. {wording}."
        assert qa_draft(draft), wording


def test_qa_requires_section_citation_or_not_available():
    draft = _good_draft()
    draft["sections"][0]["body_markdown"] = "Body with no citation."
    assert any("cites no figure" in p for p in qa_draft(draft))
    draft["sections"][0]["body_markdown"] = "Body: not available."
    assert qa_draft(draft) == []


def test_qa_rejects_section_mismatch_and_empty_figures():
    draft = _good_draft()
    draft["sections"] = draft["sections"][:-1]
    assert any("section list mismatch" in p for p in qa_draft(draft))
    draft = _good_draft(figures=[])
    assert any("no figures" in p for p in qa_draft(draft))


def test_build_draft_enforces_section_order(monkeypatch):
    import app.services.reports.assembly as assembly

    def bad_builder(session, subject_key):
        return {
            "header": {},
            "sections": [{"section_key": "thesis", "title": "T", "body_markdown": "b"}],
            "figures": [],
            "warnings": [],
        }

    monkeypatch.setitem(assembly.BUILDERS, "company_dossier", bad_builder)
    with pytest.raises(ValueError, match="section list mismatch"):
        build_draft(None, "company_dossier", "HUBC")
    with pytest.raises(ValueError, match="unknown template"):
        build_draft(None, "no_such_template", "HUBC")


# ----------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------


def test_markdown_rendering():
    md_text = render_markdown(_good_draft())
    assert "# Company Dossier: HUBC" in md_text
    assert "## Figures" in md_text
    assert "197.24" in md_text
    assert DISCLAIMER in md_text


def test_html_rendering_escapes_and_tables():
    html_doc = render_html(_good_draft())
    assert "<h1>Company Dossier: HUBC</h1>" in html_doc
    assert "<table>" in html_doc
    assert "197.24" in html_doc


def test_pdf_rendering():
    pytest.importorskip("fpdf")
    status, payload = render_pdf(_good_draft())
    assert status == "ok"
    assert payload is not None and payload[:5] == b"%PDF-"


# ----------------------------------------------------------------
# No-execution scan + GET-only endpoints (Phase 15+ precedent)
# ----------------------------------------------------------------

EXECUTION_IDENTIFIERS = (
    "place_order",
    "execute_order",
    "submit_order",
    "execute_trade",
    "place_trade",
    "Broker",
    "broker_client",
    "/orders",
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
APP_DIR = BACKEND_DIR / "app"
SCRIPTS_DIR = BACKEND_DIR.parent / "scripts"


def test_no_execution_path_anywhere():
    hits = []
    for root in (APP_DIR, SCRIPTS_DIR):
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for ident in EXECUTION_IDENTIFIERS:
                if ident in text:
                    hits.append(f"{path}:{ident}")
    assert hits == []


def test_reports_endpoint_is_get_only():
    endpoint = APP_DIR / "api" / "v1" / "endpoints" / "reports.py"
    text = endpoint.read_text(encoding="utf-8")
    assert "@router.get" in text
    assert "@router.post" not in text
    assert "@router.put" not in text
    assert "@router.patch" not in text
    assert "@router.delete" not in text
    assert re.search(r"@router\.get\(\"/reports", text)


def test_approve_reject_lifecycle_on_in_memory_db():
    """Approval is an explicit DRAFT-only transition; APPROVED stays internal.

    Runs on an in-memory SQLite database (no live DB, no network) so the
    live seed reports all stay DRAFT: nothing here has been reviewed, so
    approving a live row just to exercise the path would misstate it.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.models.base import Base
    from app.models.reports import Report, ReportTemplate
    from app.services.reports import runner as reports_runner

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine, tables=[ReportTemplate.__table__, Report.__table__])
    session = sessionmaker(bind=engine)()
    template = ReportTemplate(
        id=1,
        template_key="company_dossier",
        version="v1",
        title="Company Dossier",
        audience="internal",
        sections=[],
        methodology="test",
        disclosure="test",
    )
    session.add(template)
    session.commit()

    def _draft_row(subject, row_id):
        row = Report(
            id=row_id,
            template_id=template.id,
            template_key="company_dossier",
            subject_type="company",
            subject_key=subject,
            subject_label=subject,
            report_date=date(2026, 11, 4),
            data_cutoff_date=date(2026, 11, 4),
            audience="internal",
            status="DRAFT",
            snapshot={},
        )
        session.add(row)
        session.commit()
        return row.id

    first = _draft_row("HUBC", 101)
    assert reports_runner.approve(session, first) == {
        "report_id": first,
        "status": "APPROVED",
    }
    assert "error" in reports_runner.approve(session, first)
    assert "error" in reports_runner.reject(session, first)
    second = _draft_row("NML", 102)
    assert reports_runner.reject(session, second) == {
        "report_id": second,
        "status": "REJECTED",
    }
    assert "error" in reports_runner.approve(session, second)
    assert reports_runner.approve(session, 999999) == {"error": "unknown report id"}
