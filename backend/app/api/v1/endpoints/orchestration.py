"""Phase 18 orchestration read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent
with a reason. No value is ever fabricated, and no endpoint
writes anything. An unknown run returns 404. Nothing here is
investment advice, a buy/sell signal, or a forecast: agents are
advisory only, their outputs never override deterministic
calculations, and no order path exists anywhere in this project.

Endpoints:
  GET /api/v1/orchestration/agents
      The 16 registered agents with capability contracts.
  GET /api/v1/orchestration/runs
      Orchestration runs with status and checkpoints.
  GET /api/v1/orchestration/runs/{run_id}
      One run with its tasks, audit logs, and evaluations.
  GET /api/v1/orchestration/evaluations
      Stored evaluation case results.
  GET /api/v1/orchestration/status
      Coverage counts and the honest Phase 18 summary.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.orchestration import (
    AgentAuditLog,
    AgentDefinition,
    AgentEvaluation,
    OrchestrationRun,
    OrchestrationTask,
)

router = APIRouter(tags=["orchestration"])

SCOPE_NOTE = (
    "Scope: advisory orchestration only. The 16 registered agents "
    "read stored rows and record outputs in task checkpoints and "
    "audit logs; no agent writes a financial, market, registry, or "
    "verification row, and no agent output can override a "
    "deterministic calculation. LLM execution is unavailable (no "
    "verified local model), so every agent runs in rule-based "
    "fallback mode. Consequential tools require a recorded human "
    "approval gate; none has been granted, so they are denied to "
    "all agents. Jobs do not run when the host is off. No order "
    "path exists."
)


def _session(request: Request) -> Session:
    factory = get_session_factory(request.app.state.engine)
    return factory()


def _agent_row(r: AgentDefinition) -> dict:
    return {
        "name": r.name,
        "role": r.role,
        "scope": r.scope,
        "inputs": r.inputs,
        "outputs": r.outputs,
        "allowed_tools": r.allowed_tools,
        "permissions_tier": r.permissions_tier,
        "timeout_seconds": r.timeout_seconds,
        "max_retries": r.max_retries,
        "backoff_seconds": r.backoff_seconds,
        "cost_envelope_pkr": r.cost_envelope_pkr,
        "failure_mode": r.failure_mode,
        "execution_backend": r.execution_backend,
        "status": r.status,
    }


def _task_row(t: OrchestrationTask) -> dict:
    return {
        "task_key": t.task_key,
        "agent_name": t.agent_name,
        "depends_on": t.depends_on,
        "status": t.status,
        "idempotency_key": t.idempotency_key,
        "attempt_count": t.attempt_count,
        "checkpoint": t.checkpoint,
        "error": t.error,
    }


@router.get("/orchestration/agents")
def list_agents(request: Request):
    session = _session(request)
    try:
        rows = session.query(AgentDefinition).order_by(AgentDefinition.name).all()
        return {"scope_note": SCOPE_NOTE, "agents": [_agent_row(r) for r in rows]}
    finally:
        session.close()


@router.get("/orchestration/runs")
def list_runs(request: Request):
    session = _session(request)
    try:
        rows = session.query(OrchestrationRun).order_by(OrchestrationRun.id).all()
        return {
            "scope_note": SCOPE_NOTE,
            "runs": [
                {
                    "run_id": r.run_id,
                    "graph_name": r.graph_name,
                    "status": r.status,
                    "checkpoint": r.checkpoint,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/orchestration/runs/{run_id}")
def get_run(request: Request, run_id: str):
    session = _session(request)
    try:
        run = (
            session.query(OrchestrationRun).filter(OrchestrationRun.run_id == run_id).one_or_none()
        )
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        tasks = (
            session.query(OrchestrationTask)
            .filter(OrchestrationTask.run_id == run.id)
            .order_by(OrchestrationTask.id)
            .all()
        )
        logs = (
            session.query(AgentAuditLog)
            .filter(AgentAuditLog.run_id == run.id)
            .order_by(AgentAuditLog.id)
            .all()
        )
        evals = (
            session.query(AgentEvaluation)
            .filter(AgentEvaluation.run_id == run.id)
            .order_by(AgentEvaluation.id)
            .all()
        )
        return {
            "scope_note": SCOPE_NOTE,
            "run": {
                "run_id": run.run_id,
                "graph_name": run.graph_name,
                "status": run.status,
                "checkpoint": run.checkpoint,
            },
            "tasks": [_task_row(t) for t in tasks],
            "audit_logs": [
                {
                    "agent_name": log.agent_name,
                    "prompt_template": log.prompt_template,
                    "model_identifier": log.model_identifier,
                    "tool_calls": log.tool_calls,
                    "token_use": log.token_use,
                    "output_summary": log.output_summary,
                    "evidence": log.evidence,
                    "quarantined": log.quarantined,
                }
                for log in logs
            ],
            "evaluations": [
                {
                    "case_name": e.case_name,
                    "category": e.category,
                    "result": e.result,
                    "evidence": e.evidence,
                }
                for e in evals
            ],
        }
    finally:
        session.close()


@router.get("/orchestration/evaluations")
def list_evaluations(request: Request):
    session = _session(request)
    try:
        rows = session.query(AgentEvaluation).order_by(AgentEvaluation.id).all()
        return {
            "scope_note": SCOPE_NOTE,
            "evaluations": [
                {
                    "case_name": e.case_name,
                    "category": e.category,
                    "result": e.result,
                    "evidence": e.evidence,
                }
                for e in rows
            ],
        }
    finally:
        session.close()


@router.get("/orchestration/status")
def status(request: Request):
    session = _session(request)
    try:
        return {
            "scope_note": SCOPE_NOTE,
            "agents": session.query(AgentDefinition).count(),
            "runs": session.query(OrchestrationRun).count(),
            "tasks": session.query(OrchestrationTask).count(),
            "audit_logs": session.query(AgentAuditLog).count(),
            "evaluations": session.query(AgentEvaluation).count(),
            "evaluations_pass": session.query(AgentEvaluation)
            .filter(AgentEvaluation.result == "PASS")
            .count(),
            "quarantined_tasks": session.query(OrchestrationTask)
            .filter(OrchestrationTask.status == "QUARANTINED")
            .count(),
            "consequential_permissions_granted": 0,
            "llm_execution": "unavailable_no_verified_local_model",
            "host_off_note": "Jobs do not run when the host is off.",
        }
    finally:
        session.close()
