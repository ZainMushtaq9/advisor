"""Phase 25 operations dashboard read-only endpoints (GET only).

Everything here is read from stored rows or explained as
absent with a reason. No endpoint writes anything: job
registration, execution, retry, cancellation and retention
run through the CLI. A job is an automation record, not a
trade, a publication, a send, or a promotion — none of
those capabilities exist in this project, and this API
grants none of them.

Endpoints:
  GET /api/v1/jobs/definitions
      Registered job types with schedules and pause reasons.
  GET /api/v1/jobs/runs
      Job runs, paginated and filterable (limit 1..100,
      offset >= 0; job_key, status optional).
  GET /api/v1/jobs/runs/{id}
      One run with its summary and error.
  GET /api/v1/jobs/checkpoints
      Last successful watermarks per job.
  GET /api/v1/jobs/dead-letters
      Terminally failed runs awaiting operator retry.
  GET /api/v1/jobs/status
      Operations status: run counts, stuck runs, paused
      definitions, unresolved dead letters, watermarks.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.database import get_session_factory
from app.models.jobs import (
    JobCheckpoint,
    JobDeadLetter,
    JobDefinition,
    JobRun,
)
from app.services.jobs import runner as jobs_runner

router = APIRouter(tags=["jobs"])


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


def _definition_view(row: JobDefinition) -> dict:
    return {
        "job_key": row.job_key,
        "title": row.title,
        "handler_key": row.handler_key,
        "schedule_kind": row.schedule_kind,
        "schedule_spec": row.schedule_spec,
        "dependencies": row.dependencies,
        "timeout_seconds": row.timeout_seconds,
        "max_attempts": row.max_attempts,
        "backoff_base_seconds": row.backoff_base_seconds,
        "priority": row.priority,
        "status": row.status,
        "pause_reason": row.pause_reason,
    }


def _run_view(row: JobRun) -> dict:
    return {
        "id": row.id,
        "job_key": row.job_key,
        "idempotency_key": row.idempotency_key,
        "scheduled_for": row.scheduled_for.isoformat() if row.scheduled_for else None,
        "status": row.status,
        "attempt": row.attempt,
        "lease_owner": row.lease_owner,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        "next_attempt_at": row.next_attempt_at.isoformat() if row.next_attempt_at else None,
        "result_summary": row.result_summary,
        "error": row.error,
        "blocked_reason": row.blocked_reason,
    }


@router.get("/jobs/definitions")
def list_definitions(request: Request):
    session = _session(request)
    try:
        rows = (
            session.query(JobDefinition)
            .order_by(JobDefinition.priority, JobDefinition.job_key)
            .all()
        )
        return {"definitions": [_definition_view(r) for r in rows]}
    finally:
        session.close()


@router.get("/jobs/runs")
def list_runs(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    job_key: str | None = None,
    status: str | None = None,
):
    session = _session(request)
    try:
        query = session.query(JobRun)
        if job_key:
            query = query.filter_by(job_key=job_key)
        if status:
            query = query.filter_by(status=status)
        rows = query.order_by(JobRun.id.desc()).all()
        return _paginate([_run_view(r) for r in rows], limit, offset)
    finally:
        session.close()


@router.get("/jobs/runs/{run_id}")
def get_run(request: Request, run_id: int):
    session = _session(request)
    try:
        row = session.query(JobRun).filter_by(id=run_id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="unknown run")
        return _run_view(row)
    finally:
        session.close()


@router.get("/jobs/checkpoints")
def list_checkpoints(request: Request):
    session = _session(request)
    try:
        rows = (
            session.query(JobCheckpoint)
            .order_by(JobCheckpoint.job_key, JobCheckpoint.watermark_key)
            .all()
        )
        return {
            "checkpoints": [
                {
                    "job_key": r.job_key,
                    "watermark_key": r.watermark_key,
                    "watermark_value": r.watermark_value,
                    "detail": r.detail,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in rows
            ]
        }
    finally:
        session.close()


@router.get("/jobs/dead-letters")
def list_dead_letters(request: Request):
    session = _session(request)
    try:
        rows = session.query(JobDeadLetter).order_by(JobDeadLetter.id.desc()).all()
        return {
            "dead_letters": [
                {
                    "id": r.id,
                    "job_key": r.job_key,
                    "idempotency_key": r.idempotency_key,
                    "run_id": r.run_id,
                    "error": r.error,
                    "payload_summary": r.payload_summary,
                    "resolved": r.resolved,
                    "failed_at": r.failed_at.isoformat() if r.failed_at else None,
                }
                for r in rows
            ]
        }
    finally:
        session.close()


@router.get("/jobs/status")
def jobs_status(request: Request):
    session = _session(request)
    try:
        return jobs_runner.status(session)
    finally:
        session.close()
