"""Phase 29 acceptance tests — pure + SQLite-backed runner + API.

No real PostgreSQL, no network. The runner's live-DB reads are
covered by the live dry-run/commit in the run report; here the
runner is tested with fixed seeded rows for scenario branches,
gate logic, D-05 measurement, commit/idempotency, and API shape.

Seeding uses raw SQL with explicit ids: several Phase 1-3 models
use PostgreSQL Identity primary keys, so ORM inserts without an id
fail on SQLite. Raw inserts with explicit ids dodge that without
changing production code.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.acceptance import AcceptanceRun
from app.services.acceptance import audits as audit_lib
from app.services.acceptance import defects as defect_lib
from app.services.acceptance import gate as gate_lib
from app.services.acceptance import recompute as recomp
from app.services.acceptance import runner as acc_runner
from app.services.acceptance import scenarios as scen


@pytest.fixture()
def acc_session(tmp_path: Path):  # type: ignore[no-untyped-def]
    from sqlalchemy import event

    engine = create_engine(f"sqlite:///{tmp_path}/acc.db")

    # Enforce foreign keys: without this, SQLite hides insert-order
    # bugs that PostgreSQL rejects (the acceptance child tables
    # reference acceptance_runs.run_id, a unique column, not the
    # primary key, with no ORM relationships defined).
    @event.listens_for(engine, "connect")
    def _enforce_fk(dbapi_connection, _record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _seed_data_source(session) -> None:
    from app.models.governance import DataSource

    session.add(
        DataSource(
            id=1,
            source_key="test_source",
            display_name="Test source",
            source_type="test",
            base_reference="test",
        )
    )
    session.commit()


def _seed_report_parent(session) -> None:
    session.execute(
        text(
            "INSERT INTO report_templates (id, template_key, version, title, "
            "audience, sections, methodology, disclosure, quality_status) "
            "VALUES (1, 'company_dossier', 'v1', 'T', 'analyst', '[]', '', "
            "'', 'UNVERIFIED')"
        )
    )
    session.execute(
        text(
            "INSERT INTO reports (id, template_id, template_key, "
            "template_version, subject_type, subject_key, subject_label, "
            "report_date, data_cutoff_date, audience, status, version_number, "
            "is_current, snapshot, quality_status) VALUES (1, 1, "
            "'company_dossier', 'v1', 'company', 'T1', 'T1', '2026-11-04', "
            "'2026-11-04', 'analyst', 'DRAFT', 1, 1, '{}', 'UNVERIFIED')"
        )
    )
    session.commit()


def _seed_company_security(session, company_id: int, ticker: str, legal: str) -> None:
    session.execute(
        text("INSERT INTO companies (id, legal_name, status) VALUES (:id, :legal, 'UNVERIFIED')"),
        {"id": company_id, "legal": legal},
    )
    session.execute(
        text(
            "INSERT INTO securities (id, company_id, ticker, status) "
            "VALUES (:id, :cid, :ticker, 'UNVERIFIED')"
        ),
        {"id": company_id, "cid": company_id, "ticker": ticker},
    )
    session.commit()


def _seed_decision(session, company_id: int, ticker: str, scored: int) -> None:
    session.execute(
        text(
            "INSERT INTO decisions (id, company_id, security_id, decision_date, "
            "rules_version, screening_outcome, research_conclusion, "
            "user_facing, confidence, scored_dimensions, evidence_snapshot, "
            "conflicts, gate_reasons, quality_status, version_number, "
            "is_current) "
            "VALUES (:did, :cid, :sid, '2026-11-04', "
            "'decision-rules-v1', 'SCREEN_PASS', 'HOLD_CANDIDATE', "
            "'WITHHELD', 'LOW', :scored, '{}', '[]', '[]', 'UNVERIFIED', 1, 1)"
        ),
        {"did": company_id, "cid": company_id, "sid": company_id, "scored": scored},
    )
    session.commit()


def _seed_figures(session, computed: int, insufficient: int, na: int) -> None:
    _seed_report_parent(session)
    for i in range(computed):
        session.execute(
            text(
                "INSERT INTO report_figures (id, report_id, figure_key, label, "
                "computation_status, figure_kind, source_table, source_row_ids, "
                "source_note, quality_status) VALUES (:id, 1, :key, 'x', "
                "'computed', 'sourced_fact', 't', '[]', '', 'UNVERIFIED')"
            ),
            {"id": 1000 + i, "key": f"c{i}"},
        )
    for i in range(insufficient):
        session.execute(
            text(
                "INSERT INTO report_figures (id, report_id, figure_key, label, "
                "computation_status, figure_kind, source_table, source_row_ids, "
                "source_note, quality_status) VALUES (:id, 1, :key, 'x', "
                "'insufficient_inputs', 'sourced_fact', 't', '[]', '', 'UNVERIFIED')"
            ),
            {"id": 2000 + i, "key": f"i{i}"},
        )
    for i in range(na):
        session.execute(
            text(
                "INSERT INTO report_figures (id, report_id, figure_key, label, "
                "computation_status, figure_kind, source_table, source_row_ids, "
                "source_note, quality_status) VALUES (:id, 1, :key, 'x', "
                "'not_applicable', 'sourced_fact', 't', '[]', '', 'UNVERIFIED')"
            ),
            {"id": 3000 + i, "key": f"n{i}"},
        )
    session.commit()


# --- scenario branches -------------------------------------------------


def test_no_quote_pass(acc_session) -> None:  # type: ignore[no-untyped-def]
    _seed_company_security(acc_session, 1, "AGLNCPS", "AGLNCPS LIMITED")
    outcome, _evidence, _reason = scen.scenario_no_quote(acc_session)
    assert outcome == "pass"


def test_no_quote_fail_when_priced(acc_session) -> None:  # type: ignore[no-untyped-def]
    _seed_data_source(acc_session)
    _seed_company_security(acc_session, 1, "AGLNCPS", "AGLNCPS LIMITED")
    acc_session.execute(
        text(
            "INSERT INTO market_prices (id, data_source_id, security_id, "
            "trading_date, bar_type, close_price, volume, is_adjusted, "
            "quality_status) VALUES "
            "(1, 1, 1, '2026-11-03', 'daily', 100.0, 1000, 0, 'UNVERIFIED')"
        )
    )
    acc_session.commit()
    outcome, _evidence, _reason = scen.scenario_no_quote(acc_session)
    assert outcome == "fail"


def test_ticker_rename_pass(acc_session) -> None:  # type: ignore[no-untyped-def]
    _seed_company_security(acc_session, 1, "ENGROH", "ENGRO HOLDINGS LIMITED")
    _seed_company_security(acc_session, 2, "LCI", "LUCKY CORE INDUSTRIES LIMITED")
    _seed_company_security(acc_session, 3, "CNERGY", "CNERGYICO PK LIMITED")
    outcome, _evidence, _reason = scen.scenario_ticker_rename(acc_session)
    assert outcome == "pass"


def test_restatement_not_evaluable_on_empty(acc_session) -> None:  # type: ignore[no-untyped-def]
    outcome, evidence, _reason = scen.scenario_restatement(acc_session)
    assert outcome == "not_evaluable"
    assert evidence["document_versions"] == 0


def test_suspended_not_evaluable_on_empty(acc_session) -> None:  # type: ignore[no-untyped-def]
    outcome, _evidence, _reason = scen.scenario_suspended_security(acc_session)
    assert outcome == "not_evaluable"


def test_corporate_action_fail_on_empty(acc_session) -> None:  # type: ignore[no-untyped-def]
    outcome, _evidence, _reason = scen.scenario_corporate_action(acc_session)
    assert outcome == "fail"


def test_delayed_data_fail_on_empty(acc_session) -> None:  # type: ignore[no-untyped-def]
    outcome, evidence, _reason = scen.scenario_delayed_data(acc_session)
    assert outcome == "fail"
    assert evidence["latest_price_date"] is None


def test_model_failure_fail_on_empty(acc_session) -> None:  # type: ignore[no-untyped-def]
    outcome, _evidence, _reason = scen.scenario_model_failure(acc_session)
    assert outcome == "fail"


# --- recomputation helpers ---------------------------------------------


def test_volume_median_and_top10(acc_session) -> None:  # type: ignore[no-untyped-def]
    _seed_data_source(acc_session)
    for i, volume in enumerate([10, 20, 30, 40]):
        _seed_company_security(acc_session, i + 1, f"T{i + 1}", f"T{i + 1} LIMITED")
        acc_session.execute(
            text(
                "INSERT INTO market_prices (id, data_source_id, security_id, "
                "trading_date, bar_type, close_price, volume, is_adjusted, "
                "quality_status) VALUES "
                "(:id, 1, :sid, '2026-11-03', 'daily', 100.0, :vol, 0, 'UNVERIFIED')"
            ),
            {"id": 10 + i, "sid": i + 1, "vol": volume},
        )
    acc_session.commit()
    median = recomp.check_volume_median(acc_session)
    assert median["recomputed_value"] == "25 over 4 volumes"
    top10 = recomp.check_top10_volume_share(acc_session)
    assert top10["recomputed_value"].startswith("100.000000%")


# --- gate logic ----------------------------------------------------------


def _scenario_row(key: str, outcome: str) -> dict:
    return {
        "scenario_key": key,
        "case_name": key,
        "outcome": outcome,
        "evidence": {},
        "reason": "",
    }


def _all_pass_audits() -> list:
    return [
        {"name": n, "status": "pass"}
        for n in (
            "execution_identifiers",
            "dangerous_constructs",
            "write_routes",
            "upload_endpoints",
            "docker_invocations",
            "tracked_datasets",
            "tracked_secrets",
            "branch_tip_datasets",
            "pii_columns",
        )
    ]


def _no_severe_defects() -> list:
    return [{"defect_key": "D-01", "severity": "medium", "status": "accepted"}]


def test_gate_g1_not_met_when_hbl_blocked() -> None:
    scenarios = [
        _scenario_row("chain_hubc_full", "pass"),
        _scenario_row("chain_ogdc_full", "pass"),
        _scenario_row("chain_nml_full", "pass"),
        _scenario_row("chain_hbl_partial", "blocked"),
        _scenario_row("point_in_time", "pass"),
        _scenario_row("model_failure", "pass"),
    ]
    recomputations = [
        {"check_key": "hubc_gross_margin", "matches": True},
        {"check_key": "report_figure_census", "matches": False},
    ]
    gate = gate_lib.evaluate_gate(
        scenarios, recomputations, _all_pass_audits(), _no_severe_defects()
    )
    assert gate["g1_critical_workflows"]["result"] == "not_met"
    assert gate["g2_defects_resolved"]["result"] == "met"
    assert gate["g3_no_fabrication"]["result"] == "met"
    assert gate["g4_repo_clean"]["result"] == "met"
    assert gate["g5_auditor_signoff"]["result"] == "partial"


def test_gate_g3_not_met_on_unexpected_mismatch() -> None:
    scenarios = [
        _scenario_row("point_in_time", "pass"),
        _scenario_row("model_failure", "pass"),
    ]
    recomputations = [{"check_key": "hubc_gross_margin", "matches": False}]
    gate = gate_lib.evaluate_gate(
        scenarios, recomputations, _all_pass_audits(), _no_severe_defects()
    )
    assert gate["g3_no_fabrication"]["result"] == "not_met"


def test_verdict_partially_complete() -> None:
    gate = {
        "g1_critical_workflows": {"result": "not_met", "evidence": ""},
        "g2_defects_resolved": {"result": "met", "evidence": ""},
        "g3_no_fabrication": {"result": "met", "evidence": ""},
        "g4_repo_clean": {"result": "met", "evidence": ""},
        "g5_auditor_signoff": {"result": "partial", "evidence": ""},
    }
    scenarios = [_scenario_row("chain_hbl_partial", "blocked")]
    assert gate_lib.decide_verdict(gate, scenarios) == "PARTIALLY COMPLETE"


def test_verdict_failed_on_scenario_fail() -> None:
    gate = {
        "g1_critical_workflows": {"result": "met", "evidence": ""},
        "g2_defects_resolved": {"result": "met", "evidence": ""},
        "g3_no_fabrication": {"result": "met", "evidence": ""},
        "g4_repo_clean": {"result": "met", "evidence": ""},
        "g5_auditor_signoff": {"result": "partial", "evidence": ""},
    }
    scenarios = [_scenario_row("chain_hubc_full", "fail")]
    assert gate_lib.decide_verdict(gate, scenarios) == "FAILED"


# --- D-05 measurement ----------------------------------------------------


def test_d05_fixed_when_census_and_scored_match(acc_session) -> None:  # type: ignore[no-untyped-def]
    _seed_company_security(acc_session, 1, "HUBC", "THE HUB POWER COMPANY LIMITED")
    _seed_company_security(acc_session, 2, "OGDC", "OIL AND GAS DEVELOPMENT COMPANY LIMITED")
    _seed_decision(acc_session, 1, "HUBC", 6)
    _seed_decision(acc_session, 2, "OGDC", 6)
    _seed_figures(acc_session, 335, 199, 7)
    status, _evidence = defect_lib.resolve_d05_status(acc_session)
    assert status == "fixed"


def test_d05_open_when_stale(acc_session) -> None:  # type: ignore[no-untyped-def]
    _seed_company_security(acc_session, 1, "HUBC", "THE HUB POWER COMPANY LIMITED")
    _seed_company_security(acc_session, 2, "OGDC", "OIL AND GAS DEVELOPMENT COMPANY LIMITED")
    _seed_decision(acc_session, 1, "HUBC", 5)
    _seed_decision(acc_session, 2, "OGDC", 5)
    _seed_figures(acc_session, 334, 200, 7)
    status, _evidence = defect_lib.resolve_d05_status(acc_session)
    assert status == "open"


# --- runner commit / idempotency ----------------------------------------


def test_runner_dry_run_writes_nothing(acc_session) -> None:  # type: ignore[no-untyped-def]
    report = acc_runner.accept(acc_session, run_id="test-dry", commit=False)
    assert report["committed"] is False
    assert acc_session.query(AcceptanceRun).count() == 0


def test_runner_commit_and_idempotency(acc_session) -> None:  # type: ignore[no-untyped-def]
    report = acc_runner.accept(acc_session, run_id="test-run", commit=True)
    assert report["committed"] is True
    assert report["scenarios_created"] == 15
    assert report["recomputations_created"] == 15
    assert report["defects_created"] == 14
    second = acc_runner.accept(acc_session, run_id="test-run", commit=True)
    assert second["already_exists"] is True
    assert second["scenarios_created"] == 0
    assert acc_session.query(AcceptanceRun).count() == 1


# --- audits on a synthetic tree ------------------------------------------


def test_audit_execution_identifiers_found(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "backend" / "app").mkdir(parents=True)
    (root / "backend" / "app" / "mod.py").write_text("def place_order():\n    pass\n")
    result = audit_lib.audit_execution_identifiers(root)
    assert result["status"] == "fail"
    assert result["found"] == 1


def test_audit_execution_identifiers_clean(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "backend" / "app").mkdir(parents=True)
    (root / "backend" / "app" / "mod.py").write_text("x = 1\n")
    result = audit_lib.audit_execution_identifiers(root)
    assert result["status"] == "pass"
    assert result["found"] == 0


# --- dependency pins / licence records (defect D-13) ---------------------


def test_requirements_pins_pymupdf_pdfplumber() -> None:
    root = Path(__file__).resolve().parent.parent
    text = (root / "requirements.txt").read_text()
    assert "PyMuPDF==2.1" in text
    assert "pdfplumber==0.11.10" in text


def test_licences_records_pymupdf_pdfplumber() -> None:
    root = Path(__file__).resolve().parent.parent
    text = (root / "LICENCES.md").read_text()
    assert "PyMuPDF" in text
    assert "AFFERO" in text
    assert "pdfplumber" in text
    assert "MIT" in text


# --- API shape ------------------------------------------------------------


@pytest.fixture()
def api_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):  # type: ignore[no-untyped-def]
    from app.config import get_settings
    from app.main import create_app

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/api.db")
    monkeypatch.delenv("AUTH_ENFORCEMENT", raising=False)
    get_settings.cache_clear()
    app = create_app()
    engine = app.state.engine
    tables = [t for n, t in Base.metadata.tables.items() if n.startswith("acceptance_")]
    Base.metadata.create_all(engine, tables=tables)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        session.add(
            AcceptanceRun(
                run_id="api-run-1",
                run_date=date(2026, 11, 5),
                verdict="PARTIALLY COMPLETE",
                gate_evaluation={"gate": {}},
            )
        )
        session.commit()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_api_summary_and_gate(api_client) -> None:  # type: ignore[no-untyped-def]
    summary = api_client.get("/api/v1/acceptance/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["latest_run_id"] == "api-run-1"
    assert body["verdict"] == "PARTIALLY COMPLETE"
    gate = api_client.get("/api/v1/acceptance/gate")
    assert gate.status_code == 200
    assert gate.json()["run_id"] == "api-run-1"
    missing = api_client.get("/api/v1/acceptance/scenarios", params={"run_id": "no-such-run"})
    assert missing.status_code == 404
