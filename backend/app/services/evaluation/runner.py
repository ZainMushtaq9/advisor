"""Phase 26 evaluation runner: read stored rows, compute metrics,
evaluate golden cases, seed registries.

Dry-run default: computes everything and writes nothing.
--commit: upserts datasets / model cards / gates / golden cases
(by key), inserts the run + metrics + golden results, and
commits once. A second --commit with the same run_id writes
nothing (idempotency: the run row is the guard).

The runner never writes a business row, never promotes a
status, never collects new data, and never executes anything:
it reads stored rows and writes evaluation records only.
Company identity is resolved by ticker everywhere (surrogate
ids shift across fresh imports — see Phase 23 repair).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, text

from app.models.analysis import Forecast
from app.models.backtesting import BacktestMetric, BacktestRun
from app.models.decision import Decision, DecisionOutcome
from app.models.evaluation import (
    EvaluationDataset,
    EvaluationMetric,
    EvaluationRun,
    GoldenTestCase,
    GoldenTestResult,
    ModelCard,
    PromotionGate,
)
from app.models.financial import FinancialDocument
from app.models.forecasting import ForecastAssessment
from app.models.market import MarketPrice
from app.models.news_events import NewsEvent
from app.models.orchestration import AgentEvaluation
from app.models.rag import (
    RagBenchmarkCase,
    RagBenchmarkResult,
    RagChunk,
    RagDocument,
)
from app.models.reference import Company, Security
from app.models.registry import RegistryEvidence
from app.models.reports import Report, ReportFigure
from app.services.evaluation import golden as golden_suite
from app.services.evaluation import metrics as metric_lib
from app.services.evaluation import registry as registry_lib
from app.services.jobs.registry import EXPECTED_COUNTS

DEFAULT_RUN_ID = "phase26-evaluation-2026-11-05"

# Tables whose live counts are compared against the Phase 24
# baseline (EXPECTED_COUNTS). Fixed internal map — never user
# input — so the COUNT(*) queries below are safe.
DRIFT_TABLES: tuple[str, ...] = tuple(EXPECTED_COUNTS.keys())


def _company_id_by_ticker(session, ticker: str) -> int | None:
    row = (
        session.query(Security.company_id)
        .filter(Security.ticker == ticker)
        .order_by(Security.id)
        .first()
    )
    return row[0] if row else None


def _eval_row_by_case(session, case_name: str) -> AgentEvaluation | None:
    return (
        session.query(AgentEvaluation)
        .filter(AgentEvaluation.case_name == case_name)
        .order_by(AgentEvaluation.id)
        .first()
    )


def collect_inputs(session) -> dict:
    """Read every stored input the evaluation needs (read-only)."""
    assessments = session.query(ForecastAssessment).all()
    assessment_statuses: dict[str, int] = {}
    for row in assessments:
        assessment_statuses[row.computation_status] = (
            assessment_statuses.get(row.computation_status, 0) + 1
        )
    price_dates = [d[0] for d in session.query(MarketPrice.trading_date).distinct()]
    latest_price_date = max(price_dates) if price_dates else None
    origins = [d[0] for d in session.query(ForecastAssessment.origin_date).distinct()]
    origin = min(origins) if origins else latest_price_date
    matured = (
        metric_lib.matured_horizons(origin, latest_price_date)
        if origin is not None and latest_price_date is not None
        else []
    )
    matured_labels = sum(1 for row in assessments if row.horizon in matured)

    decisions = session.query(Decision).all()
    research_counts: dict[str, int] = {}
    for row in decisions:
        research_counts[row.research_conclusion] = (
            research_counts.get(row.research_conclusion, 0) + 1
        )

    agent_rows = session.query(AgentEvaluation).all()
    agent_by_category: dict[str, tuple[int, int]] = {}
    for row in agent_rows:
        passed, total = agent_by_category.get(row.category, (0, 0))
        agent_by_category[row.category] = (
            passed + (1 if row.result == "PASS" else 0),
            total + 1,
        )
    injection_row = _eval_row_by_case(session, "prompt_injection_probe")
    authority_row = _eval_row_by_case(session, "deterministic_authority_gate")
    hallucination_row = _eval_row_by_case(session, "hallucinated_value_quarantine")

    rag_cases = session.query(RagBenchmarkCase).count()
    rag_results = session.query(RagBenchmarkResult).all()
    rag_precisions = [
        float(r.citation_precision) for r in rag_results if r.citation_precision is not None
    ]

    backtest_runs = session.query(BacktestRun).all()
    backtest_metrics = session.query(BacktestMetric).all()

    reports = session.query(Report).all()
    figures = session.query(ReportFigure).all()
    figures_computed = sum(1 for f in figures if f.computation_status == "computed")

    hubc_company_id = _company_id_by_ticker(session, "HUBC")
    hbl_company_id = _company_id_by_ticker(session, "HBL")
    hubc_close = None
    if hubc_company_id is not None:
        hubc_security = (
            session.query(Security)
            .filter(Security.company_id == hubc_company_id)
            .order_by(Security.id)
            .first()
        )
        if hubc_security is not None:
            price = (
                session.query(MarketPrice)
                .filter(MarketPrice.security_id == hubc_security.id)
                .order_by(MarketPrice.trading_date.desc())
                .first()
            )
            hubc_close = price.close_price if price is not None else None
    hbl_documents = (
        session.query(FinancialDocument)
        .filter(FinancialDocument.company_id == hbl_company_id)
        .count()
        if hbl_company_id is not None
        else 0
    )
    max_summary_length = session.query(func.max(func.length(NewsEvent.summary))).scalar()

    companies_total = session.query(Company).count()
    companies_unverified = session.query(Company).filter(Company.status == "UNVERIFIED").count()
    leap_rows = (
        session.query(RegistryEvidence).filter(RegistryEvidence.source_key == "secp_leap").count()
    )

    drift_actual: dict[str, int] = {}
    for table in DRIFT_TABLES:
        drift_actual[table] = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()

    return {
        "assessments_total": len(assessments),
        "assessments_computed": assessment_statuses.get("computed", 0),
        "assessments_insufficient": assessment_statuses.get("insufficient_inputs", 0),
        "predictions_count": session.query(Forecast).count(),
        "origin": origin,
        "latest_price_date": latest_price_date,
        "matured_labels": matured_labels,
        "matured_horizons": matured,
        "decisions_total": len(decisions),
        "decisions_withheld": sum(1 for d in decisions if d.user_facing == "WITHHELD"),
        "research_counts": research_counts,
        "outcomes_total": session.query(DecisionOutcome).count(),
        "decision_date": date(2026, 11, 4),
        "agent_total": len(agent_rows),
        "agent_passed": sum(1 for r in agent_rows if r.result == "PASS"),
        "agent_by_category": agent_by_category,
        "rag_cases": rag_cases,
        "rag_hits": sum(1 for r in rag_results if r.hit),
        "rag_passed": sum(1 for r in rag_results if r.passed),
        "rag_precisions": rag_precisions,
        "backtest_runs_total": len(backtest_runs),
        "backtest_runs_runnable": sum(1 for r in backtest_runs if r.status != "NOT_RUNNABLE"),
        "backtest_metrics_total": len(backtest_metrics),
        "backtest_metrics_computed": sum(1 for m in backtest_metrics if m.status == "computed"),
        "reports_total": len(reports),
        "reports_approved": sum(1 for r in reports if r.status == "APPROVED"),
        "reports_published": sum(1 for r in reports if r.status == "PUBLISHED"),
        "figures_total": len(figures),
        "figures_computed": figures_computed,
        "hubc_close": hubc_close,
        "hbl_documents": hbl_documents,
        "max_summary_length": max_summary_length,
        "companies_total": companies_total,
        "companies_unverified": companies_unverified,
        "leap_rows": leap_rows,
        "injection_eval_result": injection_row.result if injection_row else None,
        "injection_eval_quarantined": (
            (injection_row.evidence or {}).get("quarantine") if injection_row else None
        ),
        "authority_eval_result": authority_row.result if authority_row else None,
        "rag_documents": session.query(RagDocument).count(),
        "rag_chunks": session.query(RagChunk).count(),
        "hallucination_eval_result": (hallucination_row.result if hallucination_row else None),
        "hallucination_eval_verdict": (
            (hallucination_row.evidence or {}).get("verdict") if hallucination_row else None
        ),
        "drift_expected": dict(EXPECTED_COUNTS),
        "drift_actual": drift_actual,
    }


def compute_metrics(inputs: dict) -> list[dict]:
    """All Phase 26 metrics from collected inputs (pure)."""
    out: list[dict] = []
    out.extend(
        metric_lib.forecast_metrics(
            assessments_total=inputs["assessments_total"],
            assessments_computed=inputs["assessments_computed"],
            assessments_insufficient=inputs["assessments_insufficient"],
            predictions_count=inputs["predictions_count"],
            origin=inputs["origin"] or inputs["latest_price_date"] or date(2026, 11, 3),
            latest_price_date=inputs["latest_price_date"],
            matured_labels=inputs["matured_labels"],
            matured_horizon_list=inputs["matured_horizons"],
        )
    )
    out.extend(
        metric_lib.recommendation_metrics(
            decisions_total=inputs["decisions_total"],
            withheld=inputs["decisions_withheld"],
            research_counts=inputs["research_counts"],
            outcomes_total=inputs["outcomes_total"],
            latest_price_date=inputs["latest_price_date"],
            decision_date=inputs["decision_date"],
        )
    )
    out.extend(
        metric_lib.agent_rag_metrics(
            agent_total=inputs["agent_total"],
            agent_passed=inputs["agent_passed"],
            agent_by_category=inputs["agent_by_category"],
            rag_cases=inputs["rag_cases"],
            rag_hits=inputs["rag_hits"],
            rag_passed=inputs["rag_passed"],
            rag_precisions=inputs["rag_precisions"],
        )
    )
    out.extend(
        metric_lib.backtest_report_metrics(
            runs_total=inputs["backtest_runs_total"],
            runs_runnable=inputs["backtest_runs_runnable"],
            metrics_total=inputs["backtest_metrics_total"],
            metrics_computed=inputs["backtest_metrics_computed"],
        )
    )
    out.extend(
        metric_lib.reports_qa_metrics(
            reports_total=inputs["reports_total"],
            reports_approved=inputs["reports_approved"],
            reports_published=inputs["reports_published"],
            figures_total=inputs["figures_total"],
            figures_computed=inputs["figures_computed"],
        )
    )
    out.extend(
        metric_lib.drift_metrics(
            expected=inputs["drift_expected"],
            actual=inputs["drift_actual"],
        )
    )
    return out


def evaluate_golden(inputs: dict) -> list[dict]:
    """Evaluate every golden case (pure + stored-evidence checks)."""
    results = []
    for case in golden_suite.GOLDEN_CASES:
        key = case["case_key"]
        try:
            if case["check_kind"] == "pure":
                passed, evidence = golden_suite.check_pure(key)
            else:
                passed, evidence = golden_suite.check_stored(key, inputs)
        except Exception as exc:  # a check error is a failed case, not a crash
            passed, evidence = False, {"error": str(exc)}
        results.append(
            {
                "case_key": key,
                "category": case["category"],
                "passed": passed,
                "evidence": evidence,
            }
        )
    return results


def _upsert_dataset(session, entry: dict) -> None:
    row = (
        session.query(EvaluationDataset)
        .filter(EvaluationDataset.dataset_key == entry["dataset_key"])
        .first()
    )
    if row is None:
        row = EvaluationDataset(dataset_key=entry["dataset_key"])
        session.add(row)
    row.title = entry["title"]
    row.kind = entry["kind"]
    row.version = entry["version"]
    row.split_policy = entry["split_policy"]
    row.as_of_date = date.fromisoformat(entry["as_of_date"]) if entry.get("as_of_date") else None
    row.row_count = entry["row_count"]
    row.status = entry["status"]
    row.evidence = entry.get("evidence")


def _upsert_model_card(session, entry: dict) -> None:
    row = (
        session.query(ModelCard)
        .filter(
            ModelCard.model_key == entry["model_key"],
            ModelCard.version == entry["version"],
        )
        .first()
    )
    if row is None:
        row = ModelCard(model_key=entry["model_key"], version=entry["version"])
        session.add(row)
    row.purpose = entry["purpose"]
    row.training_data = entry["training_data"]
    row.evaluation_status = entry["evaluation_status"]
    row.limitations = entry["limitations"]
    row.promotion_status = entry["promotion_status"]
    row.evidence = entry.get("evidence")


def _upsert_gate(session, entry: dict) -> None:
    row = session.query(PromotionGate).filter(PromotionGate.gate_key == entry["gate_key"]).first()
    if row is None:
        row = PromotionGate(gate_key=entry["gate_key"])
        session.add(row)
    row.applies_to = entry["applies_to"]
    row.requirement = entry["requirement"]
    row.status = entry["status"]
    row.reason = entry["reason"]
    row.evidence = entry.get("evidence")


def _upsert_golden_case(session, entry: dict) -> None:
    row = session.query(GoldenTestCase).filter(GoldenTestCase.case_key == entry["case_key"]).first()
    if row is None:
        row = GoldenTestCase(case_key=entry["case_key"])
        session.add(row)
    row.category = entry["category"]
    row.input_desc = entry["input_desc"]
    row.expected_outcome = entry["expected_outcome"]
    row.evidence = entry.get("evidence")


def evaluate(session, run_id: str = DEFAULT_RUN_ID, commit: bool = False) -> dict:
    """Run one Phase 26 evaluation. Dry-run writes nothing.

    Returns a summary dict: run_id, status (would_write /
    created / skipped_existing), metric counts, golden counts,
    drift differences, and per-metric/per-case detail for the
    run report. On --commit the whole write is one transaction:
    a failure rolls back instead of storing a partial run.
    """
    existing = session.query(EvaluationRun).filter(EvaluationRun.run_id == run_id).first()
    if existing is not None:
        return {
            "run_id": run_id,
            "status": "skipped_existing",
            "metrics_total": session.query(EvaluationMetric)
            .filter(EvaluationMetric.run_id == run_id)
            .count(),
            "golden_total": session.query(GoldenTestResult)
            .filter(GoldenTestResult.run_id == run_id)
            .count(),
            "golden_passed": session.query(GoldenTestResult)
            .filter(
                GoldenTestResult.run_id == run_id,
                GoldenTestResult.passed.is_(True),
            )
            .count(),
            "drift_differences": None,
        }

    inputs = collect_inputs(session)
    metrics = compute_metrics(inputs)
    golden = evaluate_golden(inputs)
    drift_metric = next(
        m for m in metrics if m["subject_key"] == "drift" and m["metric_key"] == "differences"
    )
    summary = {
        "run_id": run_id,
        "status": "would_write" if not commit else "created",
        "metrics_total": len(metrics),
        "metrics_computed": sum(1 for m in metrics if m["status"] == "computed"),
        "metrics_not_evaluable": sum(1 for m in metrics if m["status"] == "not_evaluable"),
        "golden_total": len(golden),
        "golden_passed": sum(1 for g in golden if g["passed"]),
        "golden_failed": [g["case_key"] for g in golden if not g["passed"]],
        "drift_differences": drift_metric["value"],
        "drift_detail": drift_metric["evidence"].get("differences", {}),
        "datasets": len(registry_lib.DATASETS),
        "model_cards": len(registry_lib.MODEL_CARDS),
        "promotion_gates": len(registry_lib.PROMOTION_GATES),
        "promoted_models": 0,
    }
    if not commit:
        return summary

    now = datetime.now(timezone.utc)
    try:
        for entry in registry_lib.DATASETS:
            _upsert_dataset(session, entry)
        for entry in registry_lib.MODEL_CARDS:
            _upsert_model_card(session, entry)
        for entry in registry_lib.PROMOTION_GATES:
            _upsert_gate(session, entry)
        for entry in golden_suite.GOLDEN_CASES:
            _upsert_golden_case(session, entry)
        run = EvaluationRun(
            run_id=run_id,
            kind="full",
            status="completed",
            started_at=now,
            finished_at=now,
            summary=summary,
        )
        session.add(run)
        for m in metrics:
            session.add(
                EvaluationMetric(
                    run_id=run_id,
                    subject_key=m["subject_key"],
                    metric_key=m["metric_key"],
                    value=m["value"],
                    status=m["status"],
                    reason=m["reason"],
                    evidence=m["evidence"],
                )
            )
        for g in golden:
            session.add(
                GoldenTestResult(
                    run_id=run_id,
                    case_key=g["case_key"],
                    passed=g["passed"],
                    evidence=g["evidence"],
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return summary
