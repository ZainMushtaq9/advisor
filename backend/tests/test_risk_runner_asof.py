"""Phase 14 risk runner --as-of-date tests (blocker-resolution run).

The model-risk section (forecast_abstention_rate, technical_coverage_rate,
input_drift) is keyed by (metric_key, scope_key, as_of_date) and the
runner skips existing grains, so a model row's evidence could never be
refreshed after its inputs changed. The ``model_as_of`` parameter lets
a new as-of date write NEW versioned rows while preserving old ones.

SQLite note: the models use BigInteger IDENTITY primary keys, which
SQLite does not auto-generate. The fixture below assigns ids in a
session-scoped before_flush listener — a test-only workaround for
that dialect limitation, scoped to this fixture's session so no other
test is affected. Product logic is exercised unchanged.
"""

from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.forecasting import ForecastAssessment
from app.models.risk import RiskMetricValue
from app.services.risk_analytics import runner


@pytest.fixture()
def risk_session(tmp_path: Path):  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{tmp_path}/risk_asof.db")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    def _assign_ids(sess, _flush_context, _instances):  # type: ignore[no-untyped-def]
        seen: dict[type, int] = {}
        for obj in sess.new:
            if hasattr(obj, "id") and getattr(obj, "id") is None:
                cls = type(obj)
                if cls not in seen:
                    row = sess.query(cls.id).order_by(cls.id.desc()).first()
                    seen[cls] = row[0] if row else 0
                seen[cls] += 1
                obj.id = seen[cls]

    event.listen(session, "before_flush", _assign_ids)
    for i in range(1, 4):
        session.add(
            ForecastAssessment(
                id=i,
                security_id=None,
                target_key="t",
                horizon="h",
                origin_date=date(2026, 11, 3),
                method="m",
                computation_status="insufficient_inputs",
            )
        )
    session.commit()
    yield session
    session.close()


def _model_rows(session, as_of: date):  # type: ignore[no-untyped-def]
    return (
        session.query(RiskMetricValue)
        .filter(
            RiskMetricValue.scope_key == "MARKET",
            RiskMetricValue.as_of_date == as_of,
            RiskMetricValue.metric_key.in_(
                [
                    "forecast_abstention_rate",
                    "technical_coverage_rate",
                    "input_drift",
                ]
            ),
        )
        .order_by(RiskMetricValue.metric_key)
        .all()
    )


def test_model_as_of_default_keeps_analysis_date(risk_session) -> None:  # type: ignore[no-untyped-def]
    runner.run_risk(risk_session, commit=True)
    risk_session.commit()
    rows = _model_rows(risk_session, date(2026, 11, 4))
    assert [r.metric_key for r in rows] == [
        "forecast_abstention_rate",
        "input_drift",
        "technical_coverage_rate",
    ]
    abstention = next(r for r in rows if r.metric_key == "forecast_abstention_rate")
    assert abstention.evidence == {"assessments": 3, "insufficient": 3}
    assert str(abstention.value) == "100.000000"


def test_model_as_of_writes_new_versioned_rows_and_preserves_old(risk_session) -> None:  # type: ignore[no-untyped-def]
    runner.run_risk(risk_session, commit=True)
    risk_session.commit()
    before = risk_session.query(RiskMetricValue).count()

    report = runner.run_risk(risk_session, commit=True, model_as_of=date(2026, 11, 5))
    risk_session.commit()
    after = risk_session.query(RiskMetricValue).count()
    # Exactly the 3 model rows are new; every other grain already
    # existed and was skipped.
    assert report["values_written"] == 3
    assert after - before == 3

    new_rows = _model_rows(risk_session, date(2026, 11, 5))
    assert [r.metric_key for r in new_rows] == [
        "forecast_abstention_rate",
        "input_drift",
        "technical_coverage_rate",
    ]
    abstention = next(r for r in new_rows if r.metric_key == "forecast_abstention_rate")
    assert abstention.evidence == {"assessments": 3, "insufficient": 3}
    # Old vintage preserved untouched.
    old_rows = _model_rows(risk_session, date(2026, 11, 4))
    assert len(old_rows) == 3
    assert next(
        r for r in old_rows if r.metric_key == "forecast_abstention_rate"
    ).evidence == {"assessments": 3, "insufficient": 3}


def test_model_as_of_repeat_writes_nothing(risk_session) -> None:  # type: ignore[no-untyped-def]
    runner.run_risk(risk_session, commit=True)
    risk_session.commit()
    runner.run_risk(risk_session, commit=True, model_as_of=date(2026, 11, 5))
    risk_session.commit()
    before = risk_session.query(RiskMetricValue).count()
    report = runner.run_risk(risk_session, commit=True, model_as_of=date(2026, 11, 5))
    risk_session.commit()
    assert report["values_written"] == 0
    assert risk_session.query(RiskMetricValue).count() == before


# --- CLI threading -------------------------------------------------------


def _load_cli():  # type: ignore[no-untyped-def]
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_risk_analytics.py"
    spec = importlib.util.spec_from_file_location("run_risk_analytics_cli", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_report():  # type: ignore[no-untyped-def]
    return {
        "definitions_written": 0,
        "definitions_skipped": 0,
        "values_written": 0,
        "values_skipped": 0,
        "values_computed": 0,
        "values_insufficient": 0,
        "flags_written": 0,
        "flags_skipped": 0,
        "checks_written": 0,
        "checks_pass": 0,
        "checks_breach": 0,
        "checks_blocked": 0,
        "stress_written": 0,
        "stress_skipped": 0,
        "stress_computed": 0,
    }


def test_cli_as_of_date_threaded_to_runner(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict = {}

    def fake_run_risk(session, commit=False, company_filter=None, model_as_of=None):  # type: ignore[no-untyped-def]
        captured["model_as_of"] = model_as_of
        captured["commit"] = commit
        return _fake_report()

    monkeypatch.setattr(runner, "run_risk", fake_run_risk)
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setattr("sys.argv", ["run_risk_analytics.py", "--commit", "--as-of-date", "2026-11-05"])
    assert _load_cli().main() == 0
    assert captured["model_as_of"] == date(2026, 11, 5)
    assert captured["commit"] is True


def test_cli_as_of_date_rejects_bad_date(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        "sys.argv", ["run_risk_analytics.py", "--dry-run", "--as-of-date", "2026-13-99"]
    )
    assert _load_cli().main() == 2
