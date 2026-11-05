"""Phase 27 observability tests — pure + SQLite-backed runner + API.

No real PostgreSQL, no network. The runner's live-DB reads are
covered by the live dry-run/commit in the run report; here the
runner is tested with fixed seeded rows for SLO measurement,
commit/idempotency, exception queueing, and API shape.

Every acceptance item is tested: major failures diagnosable
from logs and metrics (correlation ids, structured redacted
logs, readiness endpoint); data-quality SLOs measurable (14
definitions, per-category targets, NULL never zero); recovery
tests pass (corrupted rows rejected, DB disconnect reported,
idempotent re-runs); no sensitive values are logged (redaction
unit tests + formatter test).
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import check_database
from app.main import create_app
from app.models.governance import DataSource
from app.models.jobs import JobRun
from app.models.market import MarketPrice
from app.models.reference import Company, Security
from app.models.registry import RegistryEvidence
from app.services.market_data.validation import validate_row
from app.services.observability import runner as obs_runner
from app.services.observability import slos as slo_lib
from app.services.observability.logging_config import (
    StructuredFormatter,
    redact_value,
)


@pytest.fixture()
def obs_session(tmp_path: Path):  # type: ignore[no-untyped-def]
    from app.database import Base

    engine = create_engine(f"sqlite:///{tmp_path}/obs.db")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(
        DataSource(
            id=1,
            source_key="test_source",
            display_name="Test source",
            source_type="test",
            base_reference="test",
        )
    )
    session.add(Company(id=1, legal_name="Company A"))
    session.add(Company(id=2, legal_name="Company B"))
    session.add(Security(id=1, company_id=1, ticker="AAA"))
    session.add(Security(id=2, company_id=2, ticker="BBB"))
    session.add(
        RegistryEvidence(
            id=1,
            entity_type="company",
            entity_id=1,
            source_key="test_source",
            source_record_key="r1",
        )
    )
    session.add(
        MarketPrice(
            id=1,
            security_id=1,
            data_source_id=1,
            trading_date=date(2026, 11, 3),
            bar_type="daily",
            open_price=10,
            high_price=11,
            low_price=9,
            close_price=10.5,
            volume=100,
            previous_close=None,
        )
    )
    session.add(
        JobRun(
            id=1,
            job_key="system_health",
            idempotency_key="k1",
            status="succeeded",
        )
    )
    from app.models.evaluation import GoldenTestResult

    session.add(GoldenTestResult(id=1, run_id="r1", case_key="c1", passed=True))
    session.commit()
    yield session
    session.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# Pure: redaction
# ---------------------------------------------------------------------------


def test_redact_removes_secrets() -> None:
    cleaned = redact_value(
        {
            "password": "hunter2",
            "api_key": "sk-live-123",
            "token": "psx_abc",
            "database_url": "postgresql://user:pass@host/db",
            "ticker": "HUBC",
            "nested": {"authorization": "Bearer xyz", "count": 3},
        }
    )
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["token"] == "[REDACTED]"
    assert cleaned["database_url"] == "[REDACTED]"
    assert cleaned["ticker"] == "HUBC"
    assert cleaned["nested"]["authorization"] == "[REDACTED]"
    assert cleaned["nested"]["count"] == 3
    assert redact_value("postgresql://user:pass@host/db") == "[REDACTED]"
    assert redact_value("plain text") == "plain text"


def test_structured_formatter_never_emits_secret() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="event happened",
        args=(),
        exc_info=None,
    )
    record.fields = {"password": "hunter2", "ticker": "HUBC"}  # type: ignore[attr-defined]
    line = StructuredFormatter().format(record)
    assert "hunter2" not in line
    assert "[REDACTED]" in line
    assert "HUBC" in line
    assert "\n" not in line
    parsed = json.loads(line)
    assert parsed["password"] == "[REDACTED]"
    assert parsed["ticker"] == "HUBC"


# ---------------------------------------------------------------------------
# SLO measurement on seeded rows
# ---------------------------------------------------------------------------


def test_slo_measurements_on_seeded_fixture(obs_session) -> None:  # type: ignore[no-untyped-def]
    measurements = {
        m["slo_key"]: m for m in slo_lib.measure_slos(obs_session, run_date=date(2026, 11, 5))
    }
    assert len(measurements) == len(slo_lib.SLO_DEFINITIONS)
    assert measurements["registry_evidence_coverage"]["value"] == 0.5
    assert measurements["registry_evidence_coverage"]["status"] == "unmet"
    assert measurements["price_coverage_latest_day"]["value"] == 0.5
    assert measurements["price_coverage_latest_day"]["status"] == "unmet"
    assert measurements["price_session_gap_weekdays"]["value"] == 2
    assert measurements["price_session_gap_weekdays"]["status"] == "unmet"
    assert measurements["previous_close_completeness"]["value"] == 0
    assert measurements["previous_close_completeness"]["status"] == "unmet"
    assert measurements["ohlc_validity_rate"]["value"] == 1
    assert measurements["ohlc_validity_rate"]["status"] == "met"
    assert measurements["duplicate_ticker_rate"]["value"] == 0
    assert measurements["duplicate_ticker_rate"]["status"] == "met"
    assert measurements["statement_document_lineage"]["value"] is None
    assert measurements["statement_document_lineage"]["status"] == "not_evaluable"
    assert measurements["news_company_coverage"]["value"] == 0
    assert measurements["news_company_coverage"]["status"] == "unmet"
    assert measurements["reports_published_externally"]["value"] == 0
    assert measurements["reports_published_externally"]["status"] == "met"
    assert measurements["job_success_rate"]["value"] == 1
    assert measurements["job_success_rate"]["status"] == "met"
    assert measurements["golden_pass_rate"]["value"] == 1
    assert measurements["golden_pass_rate"]["status"] == "met"
    assert measurements["drift_difference_count"]["status"] == "unmet"
    assert measurements["drift_difference_count"]["value"] > 0


def test_runner_dry_run_writes_nothing_then_commit_then_idempotent(obs_session) -> None:  # type: ignore[no-untyped-def]
    from app.models.observability import ObservabilityRun

    dry = obs_runner.observe(obs_session, run_id="test-obs-1", commit=False)
    assert dry["committed"] is False
    assert obs_session.query(ObservabilityRun).count() == 0
    first = obs_runner.observe(obs_session, run_id="test-obs-1", commit=True)
    assert first["committed"] is True
    assert first["slos_total"] == len(slo_lib.SLO_DEFINITIONS)
    assert obs_session.query(ObservabilityRun).count() == 1
    second = obs_runner.observe(obs_session, run_id="test-obs-1", commit=True)
    assert second["committed"] is False
    assert second["skipped_existing"] is True
    assert obs_session.query(ObservabilityRun).count() == 1


def test_drift_reason_capped_for_varchar_1000() -> None:  # type: ignore[no-untyped-def]
    # The HBL re-run batch grew the drift list past 1000 chars
    # and the observability commit failed on truncation; the
    # display reason must stay within the column while the
    # full pairs live in evidence.
    many = [{"table": f"table_{i:03d}_with_a_long_name", "expected": 0, "live": 1} for i in range(60)]
    reason = slo_lib._drift_reason(many)
    assert len(reason) <= 1000
    assert reason.endswith("...")
    assert slo_lib._drift_reason([]) == "Live business counts match the Phase 24 baseline."
    short = slo_lib._drift_reason([{"table": "financial_documents", "expected": 3, "live": 4}])
    assert "financial_documents" in short and "1 count(s)" in short


def test_runner_exceptions_include_known_states(obs_session) -> None:  # type: ignore[no-untyped-def]
    from app.models.observability import ObservabilityException

    obs_runner.observe(obs_session, run_id="test-obs-2", commit=True)
    keys = {row.exception_key for row in obs_session.query(ObservabilityException).all()}
    # HBL re-run batch: known_hbl_pending RESOLVED (HBL statements
    # loaded, Phases 8-22 re-run), so it is no longer seeded.
    assert "known_hbl_pending" not in keys
    assert "known_collection_jobs_paused" in keys
    assert "slo_unmet_previous_close_completeness" in keys
    assert all(row.status == "open" for row in obs_session.query(ObservabilityException).all())


# ---------------------------------------------------------------------------
# Reliability: corrupted rows, DB disconnect, no execution identifiers
# ---------------------------------------------------------------------------


def test_corrupted_csv_row_rejected_not_stored() -> None:
    row, reason = validate_row(
        {
            "ticker": "HUBC",
            "trading_date": "2026-11-03",
            "open": "not-a-number",
            "high": "11",
            "low": "9",
            "close": "10.5",
            "volume": "100",
        },
        known_tickers={"HUBC"},
    )
    assert row is None
    assert reason is not None
    row2, reason2 = validate_row(
        {
            "ticker": "ZZZZ",
            "trading_date": "2026-11-03",
            "open": "10",
            "high": "11",
            "low": "9",
            "close": "10.5",
            "volume": "100",
        },
        known_tickers={"HUBC"},
    )
    assert row2 is None
    assert reason2 is not None


def test_check_database_reports_unavailable_truthfully() -> None:
    probe = check_database(None, None)
    assert probe["status"] == "unavailable"
    assert probe["reachable"] is False


def test_no_execution_identifiers_in_observability_code() -> None:
    path = Path(__file__).resolve().parent.parent / "app" / "services" / "observability"
    forbidden = (
        "place_order",
        "execute_order",
        "submit_order",
        "execute_trade",
        "place_trade",
    )
    for file in path.glob("*.py"):
        text = file.read_text()
        for token in forbidden:
            assert token not in text, f"{token} found in {file.name}"


# ---------------------------------------------------------------------------
# API: correlation ids, readiness honesty, summary shape
# ---------------------------------------------------------------------------


def test_correlation_id_header_set_and_echoed(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers.get("x-correlation-id")
    echoed = client.get("/api/v1/health", headers={"X-Correlation-ID": "test-corr-1234"})
    assert echoed.headers.get("x-correlation-id") == "test-corr-1234"


def test_readiness_reports_unavailable_db_truthfully(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/observability/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["database"]["reachable"] is False
    assert body["ready"] is False
    assert body["migration_matches"] is False


def _seed_alembic_head(api_client, version: str) -> None:  # type: ignore[no-untyped-def]
    engine = api_client.app.state.engine
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:v)"),
            {"v": version},
        )


def test_readiness_matches_current_head(api_client) -> None:  # type: ignore[no-untyped-def]
    # Regression for the Phase 27 artifact: the endpoint hardcoded
    # 20261104_0023 and reported ready False against the then-current
    # head. The live head is now 20261104_0025 (news-intelligence
    # migration 0025); with the head at 0025 it must report ready.
    _seed_alembic_head(api_client, "20261104_0025")
    response = api_client.get("/api/v1/observability/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["database"]["reachable"] is True
    assert body["migration_head"] == "20261104_0025"
    assert body["migration_expected"] == "20261104_0025"
    assert body["migration_matches"] is True
    assert body["ready"] is True


def test_readiness_detects_stale_head(api_client) -> None:  # type: ignore[no-untyped-def]
    # The stale-head case must still be detected, not papered over:
    # a DB at the previous head 0024 is not ready against the 0025
    # expectation.
    _seed_alembic_head(api_client, "20261104_0024")
    response = api_client.get("/api/v1/observability/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["migration_head"] == "20261104_0024"
    assert body["migration_expected"] == "20261104_0025"
    assert body["migration_matches"] is False
    assert body["ready"] is False


@pytest.fixture()
def api_client(tmp_path: Path, monkeypatch):  # type: ignore[no-untyped-def]
    db_path = tmp_path / "api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.delenv("AUTH_ENFORCEMENT", raising=False)
    get_settings.cache_clear()
    from app.database import Base
    from app.models.observability import (
        ObservabilityException,
        ObservabilityIncident,
        ObservabilityRun,
        PerformanceBaseline,
        SloDefinition,
        SloMeasurement,
        SourceHealth,
    )

    app = create_app()
    engine = app.state.engine
    tables = [t for n, t in Base.metadata.tables.items() if n.startswith("observability_")]
    Base.metadata.create_all(engine, tables=tables)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        session.add(
            SloDefinition(
                slo_key="price_coverage_latest_day",
                category="market_prices",
                metric_key="priced_securities_ratio",
                target_value=0.95,
                comparison="ge",
                unit="ratio",
                rationale="Test definition.",
            )
        )
        session.add(
            ObservabilityRun(
                run_id="api-obs-1",
                kind="full",
                status="completed",
                summary={"slos_total": 1},
            )
        )
        session.add(
            SloMeasurement(
                run_id="api-obs-1",
                slo_key="price_coverage_latest_day",
                value=0.5,
                status="unmet",
                reason="Seeded test value.",
                evidence={},
            )
        )
        session.add(
            SourceHealth(
                run_id="api-obs-1",
                source_key="market_prices",
                category="market_prices",
                latest_observation_date=date(2026, 11, 3),
                coverage_numerator=1,
                coverage_denominator=2,
                freshness_days=2,
                status="stale",
                notes="Seeded test row.",
            )
        )
        session.add(
            ObservabilityException(
                run_id="api-obs-1",
                exception_key="slo_unmet_price_coverage_latest_day",
                severity="medium",
                title="SLO unmet: price_coverage_latest_day",
                evidence={},
                status="open",
            )
        )
        session.add(
            ObservabilityIncident(
                incident_key="incident_test",
                severity="sev4",
                title="Test incident",
                evidence={},
                runbook_ref="docs/phase-27/incident_playbooks.md",
                status="resolved",
                resolution_note="Test resolution.",
            )
        )
        session.add(
            PerformanceBaseline(
                run_id="api-obs-1",
                probe_key="db_count_market_prices",
                metric_key="query_latency_ms",
                value=1.234,
                unit="ms",
                notes="Seeded test probe.",
            )
        )
        session.commit()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_api_summary_slos_health_exceptions_incidents_performance(api_client) -> None:  # type: ignore[no-untyped-def]
    summary = api_client.get("/api/v1/observability/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["latest_run_id"] == "api-obs-1"
    assert body["slos_total"] == 1
    assert body["slos_unmet"] == 1
    assert body["sources_total"] == 1
    assert body["sources_stale"] == ["market_prices"]
    assert body["exceptions_open"] == 1
    assert body["incidents_open"] == 0
    assert body["performance_probes"] == 1

    slos = api_client.get("/api/v1/observability/slos")
    assert slos.status_code == 200
    assert slos.json()["items"][0]["latest_value"] == 0.5
    assert slos.json()["items"][0]["latest_status"] == "unmet"

    health = api_client.get("/api/v1/observability/source-health")
    assert health.json()["items"][0]["status"] == "stale"

    exceptions = api_client.get("/api/v1/observability/exceptions?status=open")
    assert len(exceptions.json()["items"]) == 1
    bad = api_client.get("/api/v1/observability/exceptions?status=bogus")
    assert bad.status_code == 400

    incidents = api_client.get("/api/v1/observability/incidents")
    assert incidents.json()["items"][0]["status"] == "resolved"

    performance = api_client.get("/api/v1/observability/performance")
    assert performance.json()["items"][0]["probe_key"] == "db_count_market_prices"

    runs = api_client.get("/api/v1/observability/runs")
    assert runs.json()["total"] == 1
    bad_page = api_client.get("/api/v1/observability/runs?limit=0")
    assert bad_page.status_code == 400
