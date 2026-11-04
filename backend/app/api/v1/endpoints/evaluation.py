"""Phase 26 evaluation read-only endpoints (GET only).

Everything here is read from stored rows or explained as
absent with a reason. No endpoint writes anything: evaluation
runs, registry seeding, and golden checks run through the CLI.
An evaluation record is not a promotion, a publication, a
send, or a trade — none of those capabilities exist in this
project, and this API grants none of them.

Endpoints:
  GET /api/v1/evaluation/summary
      Latest run highlights: metric counts, golden pass/fail,
      drift differences, promoted models (always 0 until a gate
      is MET by positive evidence).
  GET /api/v1/evaluation/datasets
      Versioned evaluation dataset registry.
  GET /api/v1/evaluation/model-cards
      Model cards with promotion status (all NOT_PROMOTED).
  GET /api/v1/evaluation/gates
      Promotion gates with the exact missing evidence.
  GET /api/v1/evaluation/runs
      Evaluation runs, paginated (limit 1..100, offset >= 0).
  GET /api/v1/evaluation/runs/{run_id}
      One run with its metrics and golden results.
  GET /api/v1/evaluation/metrics?run_id=
      Metrics of one run (run_id required).
  GET /api/v1/evaluation/golden-cases
      The golden suite with expected outcomes.
  GET /api/v1/evaluation/golden-results?run_id=
      Golden results of one run (run_id required).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.database import get_session_factory
from app.models.evaluation import (
    EvaluationDataset,
    EvaluationMetric,
    EvaluationRun,
    GoldenTestCase,
    GoldenTestResult,
    ModelCard,
    PromotionGate,
)

router = APIRouter(tags=["evaluation"])


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


def _dataset_view(row: EvaluationDataset) -> dict:
    return {
        "dataset_key": row.dataset_key,
        "title": row.title,
        "kind": row.kind,
        "version": row.version,
        "split_policy": row.split_policy,
        "as_of_date": str(row.as_of_date) if row.as_of_date else None,
        "row_count": row.row_count,
        "status": row.status,
        "evidence": row.evidence,
    }


def _card_view(row: ModelCard) -> dict:
    return {
        "model_key": row.model_key,
        "version": row.version,
        "purpose": row.purpose,
        "training_data": row.training_data,
        "evaluation_status": row.evaluation_status,
        "limitations": row.limitations,
        "promotion_status": row.promotion_status,
        "evidence": row.evidence,
    }


def _gate_view(row: PromotionGate) -> dict:
    return {
        "gate_key": row.gate_key,
        "applies_to": row.applies_to,
        "requirement": row.requirement,
        "status": row.status,
        "reason": row.reason,
        "evidence": row.evidence,
    }


def _run_view(row: EvaluationRun) -> dict:
    return {
        "run_id": row.run_id,
        "kind": row.kind,
        "status": row.status,
        "summary": row.summary,
    }


def _metric_view(row: EvaluationMetric) -> dict:
    return {
        "subject_key": row.subject_key,
        "metric_key": row.metric_key,
        "value": float(row.value) if row.value is not None else None,
        "status": row.status,
        "reason": row.reason,
        "evidence": row.evidence,
    }


def _case_view(row: GoldenTestCase) -> dict:
    return {
        "case_key": row.case_key,
        "category": row.category,
        "input_desc": row.input_desc,
        "expected_outcome": row.expected_outcome,
        "evidence": row.evidence,
    }


def _result_view(row: GoldenTestResult) -> dict:
    return {
        "run_id": row.run_id,
        "case_key": row.case_key,
        "passed": row.passed,
        "evidence": row.evidence,
    }


@router.get("/evaluation/summary")
def evaluation_summary(request: Request) -> dict:
    session = _session(request)
    try:
        runs = session.query(EvaluationRun).order_by(EvaluationRun.id.desc()).limit(1).all()
        latest = runs[0] if runs else None
        metrics: list = []
        golden: list = []
        if latest is not None:
            metrics = (
                session.query(EvaluationMetric)
                .filter(EvaluationMetric.run_id == latest.run_id)
                .all()
            )
            golden = (
                session.query(GoldenTestResult)
                .filter(GoldenTestResult.run_id == latest.run_id)
                .all()
            )
        promoted = session.query(ModelCard).filter(ModelCard.promotion_status == "PROMOTED").count()
        gates_met = session.query(PromotionGate).filter(PromotionGate.status == "MET").count()
        return {
            "latest_run_id": latest.run_id if latest else None,
            "latest_run_status": latest.status if latest else None,
            "metrics_total": len(metrics),
            "metrics_computed": sum(1 for m in metrics if m.status == "computed"),
            "metrics_not_evaluable": sum(1 for m in metrics if m.status == "not_evaluable"),
            "golden_total": len(golden),
            "golden_passed": sum(1 for g in golden if g.passed),
            "golden_failed": [g.case_key for g in golden if not g.passed],
            "promoted_models": promoted,
            "gates_met": gates_met,
            "datasets": session.query(EvaluationDataset).count(),
            "model_cards": session.query(ModelCard).count(),
            "promotion_gates": session.query(PromotionGate).count(),
        }
    finally:
        session.close()


@router.get("/evaluation/datasets")
def evaluation_datasets(request: Request) -> dict:
    session = _session(request)
    try:
        rows = session.query(EvaluationDataset).order_by(EvaluationDataset.id).all()
        return {"datasets": [_dataset_view(r) for r in rows]}
    finally:
        session.close()


@router.get("/evaluation/model-cards")
def evaluation_model_cards(request: Request) -> dict:
    session = _session(request)
    try:
        rows = session.query(ModelCard).order_by(ModelCard.id).all()
        return {"model_cards": [_card_view(r) for r in rows]}
    finally:
        session.close()


@router.get("/evaluation/gates")
def evaluation_gates(request: Request) -> dict:
    session = _session(request)
    try:
        rows = session.query(PromotionGate).order_by(PromotionGate.id).all()
        return {"gates": [_gate_view(r) for r in rows]}
    finally:
        session.close()


@router.get("/evaluation/runs")
def evaluation_runs(request: Request, limit: int = 20, offset: int = 0) -> dict:
    session = _session(request)
    try:
        rows = session.query(EvaluationRun).order_by(EvaluationRun.id).all()
        return _paginate([_run_view(r) for r in rows], limit, offset)
    finally:
        session.close()


@router.get("/evaluation/runs/{run_id}")
def evaluation_run_detail(request: Request, run_id: str) -> dict:
    session = _session(request)
    try:
        row = session.query(EvaluationRun).filter(EvaluationRun.run_id == run_id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="unknown run")
        metrics = (
            session.query(EvaluationMetric)
            .filter(EvaluationMetric.run_id == run_id)
            .order_by(EvaluationMetric.id)
            .all()
        )
        golden = (
            session.query(GoldenTestResult)
            .filter(GoldenTestResult.run_id == run_id)
            .order_by(GoldenTestResult.id)
            .all()
        )
        return {
            "run": _run_view(row),
            "metrics": [_metric_view(m) for m in metrics],
            "golden_results": [_result_view(g) for g in golden],
        }
    finally:
        session.close()


@router.get("/evaluation/metrics")
def evaluation_metrics(request: Request, run_id: str) -> dict:
    session = _session(request)
    try:
        rows = (
            session.query(EvaluationMetric)
            .filter(EvaluationMetric.run_id == run_id)
            .order_by(EvaluationMetric.id)
            .all()
        )
        return {"run_id": run_id, "metrics": [_metric_view(r) for r in rows]}
    finally:
        session.close()


@router.get("/evaluation/golden-cases")
def evaluation_golden_cases(request: Request) -> dict:
    session = _session(request)
    try:
        rows = session.query(GoldenTestCase).order_by(GoldenTestCase.id).all()
        return {"golden_cases": [_case_view(r) for r in rows]}
    finally:
        session.close()


@router.get("/evaluation/golden-results")
def evaluation_golden_results(request: Request, run_id: str) -> dict:
    session = _session(request)
    try:
        rows = (
            session.query(GoldenTestResult)
            .filter(GoldenTestResult.run_id == run_id)
            .order_by(GoldenTestResult.id)
            .all()
        )
        return {"run_id": run_id, "golden_results": [_result_view(r) for r in rows]}
    finally:
        session.close()
