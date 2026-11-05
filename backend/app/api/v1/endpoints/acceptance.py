"""Phase 29 acceptance read-only endpoints (GET only).

Everything here is read from stored rows or explained as
absent with a reason. No endpoint writes anything: acceptance
runs execute through the CLI. An acceptance record is not a
promotion, a publication, a send, or a trade — none of those
capabilities exist in this project, and this API grants none
of them.

Endpoints:
  GET /api/v1/acceptance/summary
      Latest run: verdict, gate results, scenario outcomes,
      recomputation matches, defect counts by severity/status.
  GET /api/v1/acceptance/runs
      Acceptance runs, most recent first.
  GET /api/v1/acceptance/scenarios?run_id=
      Scenario results for a run (latest run if omitted).
  GET /api/v1/acceptance/recomputations?run_id=
      Recomputation results for a run (latest run if omitted).
  GET /api/v1/acceptance/defects?run_id=
      Defect register for a run (latest run if omitted).
  GET /api/v1/acceptance/gate?run_id=
      Gate evaluation for a run (latest run if omitted).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.database import get_session_factory
from app.models.acceptance import (
    AcceptanceDefect,
    AcceptanceRecomputation,
    AcceptanceRun,
    AcceptanceScenario,
)

router = APIRouter(tags=["acceptance"])


def _session(request: Request):
    factory = get_session_factory(request.app.state.engine)
    return factory()


def _latest_run(session):
    return session.query(AcceptanceRun).order_by(AcceptanceRun.id.desc()).first()


def _resolve_run(session, run_id: str | None):
    if run_id:
        run = session.query(AcceptanceRun).filter_by(run_id=run_id).first()
        if run is None:
            raise HTTPException(status_code=404, detail="acceptance run not found")
        return run
    return _latest_run(session)


@router.get("/acceptance/summary")
def acceptance_summary(request: Request) -> dict:
    session = _session(request)
    try:
        run = _latest_run(session)
        if run is None:
            return {
                "latest_run_id": None,
                "verdict": None,
                "gate": {},
                "scenarios": {},
                "recomputations": {},
                "defects": {},
            }
        scenarios = (
            session.query(AcceptanceScenario).filter(AcceptanceScenario.run_id == run.run_id).all()
        )
        recomputations = (
            session.query(AcceptanceRecomputation)
            .filter(AcceptanceRecomputation.run_id == run.run_id)
            .all()
        )
        defects = (
            session.query(AcceptanceDefect).filter(AcceptanceDefect.run_id == run.run_id).all()
        )
        return {
            "latest_run_id": run.run_id,
            "verdict": run.verdict,
            "gate": run.gate_evaluation.get("gate", {})
            if isinstance(run.gate_evaluation, dict)
            else {},
            "scenarios": {
                "total": len(scenarios),
                "pass": sum(1 for s in scenarios if s.outcome == "pass"),
                "fail": sum(1 for s in scenarios if s.outcome == "fail"),
                "blocked": sum(1 for s in scenarios if s.outcome == "blocked"),
                "not_evaluable": sum(1 for s in scenarios if s.outcome == "not_evaluable"),
            },
            "recomputations": {
                "total": len(recomputations),
                "matched": sum(1 for r in recomputations if r.matches),
                "mismatched": sum(1 for r in recomputations if not r.matches),
            },
            "defects": {
                "total": len(defects),
                "critical": sum(1 for d in defects if d.severity == "critical"),
                "high": sum(1 for d in defects if d.severity == "high"),
                "medium": sum(1 for d in defects if d.severity == "medium"),
                "low": sum(1 for d in defects if d.severity == "low"),
                "open": sum(1 for d in defects if d.status == "open"),
                "fixed": sum(1 for d in defects if d.status == "fixed"),
                "accepted": sum(1 for d in defects if d.status == "accepted"),
            },
        }
    finally:
        session.close()


@router.get("/acceptance/runs")
def acceptance_runs(request: Request) -> dict:
    session = _session(request)
    try:
        runs = session.query(AcceptanceRun).order_by(AcceptanceRun.id.desc()).all()
        return {
            "runs": [
                {
                    "run_id": r.run_id,
                    "run_date": str(r.run_date),
                    "verdict": r.verdict,
                }
                for r in runs
            ]
        }
    finally:
        session.close()


@router.get("/acceptance/scenarios")
def acceptance_scenarios(request: Request, run_id: str | None = None) -> dict:
    session = _session(request)
    try:
        run = _resolve_run(session, run_id)
        if run is None:
            return {"run_id": None, "scenarios": []}
        rows = (
            session.query(AcceptanceScenario)
            .filter(AcceptanceScenario.run_id == run.run_id)
            .order_by(AcceptanceScenario.id)
            .all()
        )
        return {
            "run_id": run.run_id,
            "scenarios": [
                {
                    "scenario_key": r.scenario_key,
                    "case_name": r.case_name,
                    "outcome": r.outcome,
                    "evidence": r.evidence,
                    "reason": r.reason,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/acceptance/recomputations")
def acceptance_recomputations(request: Request, run_id: str | None = None) -> dict:
    session = _session(request)
    try:
        run = _resolve_run(session, run_id)
        if run is None:
            return {"run_id": None, "recomputations": []}
        rows = (
            session.query(AcceptanceRecomputation)
            .filter(AcceptanceRecomputation.run_id == run.run_id)
            .order_by(AcceptanceRecomputation.id)
            .all()
        )
        return {
            "run_id": run.run_id,
            "recomputations": [
                {
                    "check_key": r.check_key,
                    "claimed_value": r.claimed_value,
                    "recomputed_value": r.recomputed_value,
                    "matches": r.matches,
                    "tolerance": r.tolerance,
                    "method": r.method,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/acceptance/defects")
def acceptance_defects(request: Request, run_id: str | None = None) -> dict:
    session = _session(request)
    try:
        run = _resolve_run(session, run_id)
        if run is None:
            return {"run_id": None, "defects": []}
        rows = (
            session.query(AcceptanceDefect)
            .filter(AcceptanceDefect.run_id == run.run_id)
            .order_by(AcceptanceDefect.id)
            .all()
        )
        return {
            "run_id": run.run_id,
            "defects": [
                {
                    "defect_key": r.defect_key,
                    "severity": r.severity,
                    "status": r.status,
                    "title": r.title,
                    "impact": r.impact,
                    "unblocker": r.unblocker,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/acceptance/gate")
def acceptance_gate(request: Request, run_id: str | None = None) -> dict:
    session = _session(request)
    try:
        run = _resolve_run(session, run_id)
        if run is None:
            return {"run_id": None, "gate": {}}
        gate = run.gate_evaluation.get("gate", {}) if isinstance(run.gate_evaluation, dict) else {}
        return {"run_id": run.run_id, "verdict": run.verdict, "gate": gate}
    finally:
        session.close()
