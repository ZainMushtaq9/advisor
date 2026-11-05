"""Phase 26 evaluation tests — pure + SQLite-backed runner + API.

No real PostgreSQL, no network. The runner's live-DB reads are
covered by the live dry-run/commit in the run report; here the
runner is tested with fixed inputs (monkeypatched collection)
for commit/idempotency, and the API is tested against seeded
evaluation tables. Pure metric and golden checks run against
current code with fixed inputs.

Every acceptance item is tested: reproducible out-of-sample
rules (maturity only after the horizon elapses, decision date
as the split, fixed golden sets); baselines and negative
outcomes included (abstentions, WITHHELD values, NOT_RUNNABLE
runs, NOT_EVALUABLE metrics with NULL values — never zero);
promotion governed by evidence (all cards NOT_PROMOTED, all
gates NOT_MET); no unsupported accuracy claims (evaluated
claims cite stored rows; unevaluated claims are NULL).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.main import create_app
from app.models.evaluation import (
    EvaluationDataset,
    EvaluationMetric,
    EvaluationRun,
    GoldenTestCase,
    GoldenTestResult,
    ModelCard,
    PromotionGate,
)
from app.services.evaluation import golden as golden_suite
from app.services.evaluation import metrics as metric_lib
from app.services.evaluation import registry as registry_lib
from app.services.evaluation import runner as eval_runner

EVAL_TABLES = (
    "evaluation_datasets",
    "evaluation_runs",
    "evaluation_metrics",
    "golden_test_cases",
    "golden_test_results",
    "model_cards",
    "promotion_gates",
)


# ---------------------------------------------------------------------------
# Pure: horizon maturity
# ---------------------------------------------------------------------------


def test_matured_horizons_none_when_latest_equals_origin() -> None:
    origin = date(2026, 11, 3)
    assert metric_lib.matured_horizons(origin, origin) == []


def test_matured_horizons_partial_after_30_days() -> None:
    origin = date(2026, 11, 3)
    assert metric_lib.matured_horizons(origin, date(2026, 12, 3)) == [
        "1d",
        "1w",
        "1m",
    ]


# ---------------------------------------------------------------------------
# Pure: forecast metrics
# ---------------------------------------------------------------------------


def test_forecast_metrics_abstained_seed() -> None:
    out = metric_lib.forecast_metrics(
        assessments_total=120,
        assessments_computed=0,
        assessments_insufficient=120,
        predictions_count=0,
        origin=date(2026, 11, 3),
        latest_price_date=date(2026, 11, 3),
        matured_labels=0,
        matured_horizon_list=[],
    )
    by_key = {(m["subject_key"], m["metric_key"]): m for m in out}
    assert by_key[("forecast", "predictions_count")]["value"] == 0
    assert by_key[("forecast", "matured_labels")]["value"] == 0
    for key in (
        "mae",
        "rmse",
        "directional_accuracy",
        "interval_coverage",
        "baseline_relative_performance",
    ):
        row = by_key[("forecast", key)]
        assert row["status"] == "not_evaluable"
        assert row["value"] is None


# ---------------------------------------------------------------------------
# Pure: recommendation metrics
# ---------------------------------------------------------------------------


def test_recommendation_metrics_abstention_computed_performance_not() -> None:
    out = metric_lib.recommendation_metrics(
        decisions_total=4,
        withheld=4,
        research_counts={"HOLD_CANDIDATE": 2, "INSUFFICIENT_EVIDENCE": 2},
        outcomes_total=0,
        latest_price_date=date(2026, 11, 3),
        decision_date=date(2026, 11, 4),
    )
    by_key = {(m["subject_key"], m["metric_key"]): m for m in out}
    assert by_key[("recommendation", "user_facing_abstention_rate")]["value"] == 1.0
    assert by_key[("recommendation", "outcomes_recorded")]["value"] == 0
    assert by_key[("recommendation", "adverse_outcomes_observed")]["value"] == 0
    # The reason must clarify that 0 means "none recorded", never
    # "none occurred".
    assert "not a claim that" in by_key[("recommendation", "adverse_outcomes_observed")]["reason"]
    for key in (
        "subsequent_return",
        "benchmark_relative_return",
        "event_classification_precision",
        "event_classification_recall",
        "calibration",
    ):
        row = by_key[("recommendation", key)]
        assert row["status"] == "not_evaluable"
        assert row["value"] is None


# ---------------------------------------------------------------------------
# Pure: agent/RAG metrics
# ---------------------------------------------------------------------------


def test_agent_rag_metrics_from_stored_rows() -> None:
    out = metric_lib.agent_rag_metrics(
        agent_total=6,
        agent_passed=6,
        agent_by_category={"prompt_injection": (1, 1)},
        rag_cases=6,
        rag_hits=6,
        rag_passed=6,
        rag_precisions=[0.2, 0.2, 0.2, 0.2, 1.0, 1.0],
    )
    by_key = {(m["subject_key"], m["metric_key"]): m for m in out}
    assert by_key[("agent", "pass_rate")]["value"] == 1.0
    assert by_key[("rag", "recall_at_5")]["value"] == 1.0
    assert abs(by_key[("rag", "mean_citation_precision")]["value"] - 0.466667) < 1e-5
    assert by_key[("rag", "vector_retrieval")]["status"] == "not_applicable"
    assert by_key[("rag", "vector_retrieval")]["value"] is None


# ---------------------------------------------------------------------------
# Pure: drift metrics
# ---------------------------------------------------------------------------


def test_drift_metrics_clean_and_dirty() -> None:
    clean = metric_lib.drift_metrics(expected={"companies": 470}, actual={"companies": 470})
    assert clean[0]["value"] == 0
    assert len(clean) == 1
    dirty = metric_lib.drift_metrics(expected={"companies": 470}, actual={"companies": 471})
    assert dirty[0]["value"] == 1
    assert dirty[1]["metric_key"] == "drift_companies"
    assert dirty[1]["value"] is None  # a drift metric carries no invented value


# ---------------------------------------------------------------------------
# Pure: registry sanity
# ---------------------------------------------------------------------------


def test_registry_all_cards_unpromoted_all_gates_unmet() -> None:
    assert len(registry_lib.DATASETS) == 8
    assert len(registry_lib.MODEL_CARDS) == 9
    assert len(registry_lib.PROMOTION_GATES) == 5
    assert len(golden_suite.GOLDEN_CASES) == 14
    assert all(c["promotion_status"] == "NOT_PROMOTED" for c in registry_lib.MODEL_CARDS)
    assert all(g["status"] == "NOT_MET" for g in registry_lib.PROMOTION_GATES)
    categories = {c["category"] for c in golden_suite.GOLDEN_CASES}
    for required in (
        "source_matching",
        "entity_resolution",
        "tool_selection",
        "citation",
        "extraction",
        "summarization",
        "refusal_abstention",
        "injection_resistance",
        "hallucination",
        "conflicting_sources",
    ):
        assert required in categories


# ---------------------------------------------------------------------------
# Pure: golden pure checks
# ---------------------------------------------------------------------------


def test_golden_pure_checks_all_pass() -> None:
    for case in golden_suite.GOLDEN_CASES:
        if case["check_kind"] != "pure":
            continue
        passed, _evidence = golden_suite.check_pure(case["case_key"])
        assert passed, case["case_key"]


def test_golden_stored_checks_pass_and_fail_honestly() -> None:
    # HBL re-run batch: the HBL refusal premise retired (exactly
    # one HBL document now) and the index totals moved to 4/2020.
    good = {
        "max_summary_length": 280,
        "hbl_documents": 1,
        "decisions_total": 4,
        "decisions_withheld": 4,
        "injection_eval_result": "PASS",
        "injection_eval_quarantined": True,
        "companies_total": 470,
        "companies_unverified": 470,
        "leap_rows": 61,
        "rag_documents": 4,
        "rag_chunks": 2020,
        "hallucination_eval_result": "PASS",
        "hallucination_eval_verdict": "QUARANTINE_NO_EVIDENCE",
        "authority_eval_result": "PASS",
        "hubc_close": 197.24,
    }
    for case in golden_suite.GOLDEN_CASES:
        if case["check_kind"] != "stored":
            continue
        passed, _evidence = golden_suite.check_stored(case["case_key"], good)
        assert passed, case["case_key"]
    bad = dict(good, hbl_documents=0, hubc_close=200.00)
    assert golden_suite.check_stored("golden_hbl_indexed_evidence", bad)[0] is False
    assert golden_suite.check_stored("golden_deterministic_authority", bad)[0] is False


# ---------------------------------------------------------------------------
# SQLite: runner commit + idempotency (fixed inputs)
# ---------------------------------------------------------------------------


def _fixed_inputs() -> dict:
    return {
        "assessments_total": 120,
        "assessments_computed": 0,
        "assessments_insufficient": 120,
        "predictions_count": 0,
        "origin": date(2026, 11, 3),
        "latest_price_date": date(2026, 11, 3),
        "matured_labels": 0,
        "matured_horizons": [],
        "decisions_total": 4,
        "decisions_withheld": 4,
        "research_counts": {"HOLD_CANDIDATE": 2, "INSUFFICIENT_EVIDENCE": 2},
        "outcomes_total": 0,
        "decision_date": date(2026, 11, 4),
        "agent_total": 6,
        "agent_passed": 6,
        "agent_by_category": {"prompt_injection": (1, 1)},
        "rag_cases": 6,
        "rag_hits": 6,
        "rag_passed": 6,
        "rag_precisions": [0.2, 0.2, 0.2, 0.2, 1.0, 1.0],
        "backtest_runs_total": 5,
        "backtest_runs_runnable": 0,
        "backtest_metrics_total": 55,
        "backtest_metrics_computed": 0,
        "reports_total": 22,
        "reports_approved": 0,
        "reports_published": 0,
        "figures_total": 541,
        "figures_computed": 335,
        "hubc_close": 197.24,
        # HBL re-run batch values (see the golden-case test above).
        "hbl_documents": 1,
        "max_summary_length": 200,
        "companies_total": 470,
        "companies_unverified": 470,
        "leap_rows": 61,
        "injection_eval_result": "PASS",
        "injection_eval_quarantined": True,
        "authority_eval_result": "PASS",
        "rag_documents": 4,
        "rag_chunks": 2020,
        "hallucination_eval_result": "PASS",
        "hallucination_eval_verdict": "QUARANTINE_NO_EVIDENCE",
        "drift_expected": {"companies": 470},
        "drift_actual": {"companies": 470},
    }


@pytest.fixture()
def eval_session(tmp_path: Path):  # type: ignore[no-untyped-def]
    from app.database import Base

    engine = create_engine(f"sqlite:///{tmp_path}/eval.db")
    tables = [t for n, t in Base.metadata.tables.items() if n in EVAL_TABLES]
    Base.metadata.create_all(engine, tables=tables)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def test_runner_commit_then_idempotent(eval_session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(eval_runner, "collect_inputs", lambda session: _fixed_inputs())
    first = eval_runner.evaluate(eval_session, run_id="test-run-1", commit=True)
    assert first["status"] == "created"
    assert first["golden_total"] == 14
    assert first["golden_passed"] == 14
    assert first["drift_differences"] == 0
    assert first["promoted_models"] == 0
    assert eval_session.query(EvaluationRun).count() == 1
    assert eval_session.query(EvaluationDataset).count() == 8
    assert eval_session.query(ModelCard).count() == 9
    assert eval_session.query(PromotionGate).count() == 5
    assert eval_session.query(GoldenTestCase).count() == 14
    assert eval_session.query(GoldenTestResult).count() == 14
    assert eval_session.query(EvaluationMetric).count() == first["metrics_total"]
    assert (
        eval_session.query(EvaluationMetric)
        .filter(EvaluationMetric.status == "not_evaluable")
        .count()
        == first["metrics_not_evaluable"]
    )
    second = eval_runner.evaluate(eval_session, run_id="test-run-1", commit=True)
    assert second["status"] == "skipped_existing"
    assert eval_session.query(EvaluationRun).count() == 1
    assert eval_session.query(EvaluationMetric).count() == first["metrics_total"]


def test_runner_dry_run_writes_nothing(eval_session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(eval_runner, "collect_inputs", lambda session: _fixed_inputs())
    summary = eval_runner.evaluate(eval_session, run_id="dry-1", commit=False)
    assert summary["status"] == "would_write"
    assert eval_session.query(EvaluationRun).count() == 0
    assert eval_session.query(EvaluationMetric).count() == 0


# ---------------------------------------------------------------------------
# SQLite: API (GET-only, seeded evaluation tables)
# ---------------------------------------------------------------------------


@pytest.fixture()
def api_client(tmp_path: Path, monkeypatch):  # type: ignore[no-untyped-def]
    db_path = tmp_path / "api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.delenv("AUTH_ENFORCEMENT", raising=False)
    get_settings.cache_clear()
    from app.database import Base

    app = create_app()
    engine = app.state.engine
    tables = [t for n, t in Base.metadata.tables.items() if n in EVAL_TABLES]
    Base.metadata.create_all(engine, tables=tables)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        session.add(
            EvaluationRun(
                run_id="api-run-1",
                kind="full",
                status="completed",
                summary={"golden_passed": 14},
            )
        )
        session.add(
            EvaluationMetric(
                run_id="api-run-1",
                subject_key="rag",
                metric_key="recall_at_5",
                value=1.0,
                status="computed",
                reason="Stored benchmark rows.",
                evidence={},
            )
        )
        session.add(
            GoldenTestResult(run_id="api-run-1", case_key="golden_qa_citation_rule", passed=True)
        )
        session.add(
            ModelCard(
                model_key="decision_rules",
                version="decision-rules-v1",
                purpose="Seven-dimension scoring.",
                training_data="Stored rows only.",
                evaluation_status="Abstention measurable.",
                limitations="Confidence caps at LOW.",
                promotion_status="NOT_PROMOTED",
            )
        )
        session.commit()
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    get_settings.cache_clear()


def test_api_summary_and_detail(api_client) -> None:  # type: ignore[no-untyped-def]
    summary = api_client.get("/api/v1/evaluation/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["latest_run_id"] == "api-run-1"
    assert body["promoted_models"] == 0
    assert body["golden_passed"] == 1
    detail = api_client.get("/api/v1/evaluation/runs/api-run-1")
    assert detail.status_code == 200
    assert detail.json()["metrics"][0]["metric_key"] == "recall_at_5"
    assert api_client.get("/api/v1/evaluation/runs/nope").status_code == 404
    assert api_client.get("/api/v1/evaluation/metrics?run_id=api-run-1").status_code == 200
    assert api_client.get("/api/v1/evaluation/runs?limit=0").status_code == 400


# ---------------------------------------------------------------------------
# Scans: no execution path, GET-only endpoints
# ---------------------------------------------------------------------------


def test_no_execution_identifiers_in_new_code() -> None:
    import re

    root = Path(__file__).resolve().parent.parent / "app"
    hits = []
    pattern = re.compile(
        r"place_order|execute_order|submit_order|execute_trade|place_trade|"
        r"Broker|/orders"
    )
    for path in (
        root / "services" / "evaluation",
        root / "api" / "v1" / "endpoints" / "evaluation.py",
        root / "models" / "evaluation.py",
    ):
        files = [path] if path.is_file() else list(path.rglob("*.py"))
        for f in files:
            if pattern.search(f.read_text()):
                hits.append(str(f))
    assert hits == []


def test_evaluation_endpoints_get_only() -> None:
    from app.api.v1.endpoints import evaluation as eval_api

    for route in eval_api.router.routes:
        assert set(route.methods) == {"GET"}, route.path
