"""Phase 25 job runner: registry, claiming, execution, recovery.

Single-pass, operator-invoked, sequential execution. There
is NO resident daemon and NO hosted scheduler: the operator
(or a host cron) runs ``run-due``, which does one pass and
exits. This is the honest offline model — the system never
pretends something is watching the clock between runs, and
catch-up after an offline period is bounded and explicit.

Overlap prevention: a run is claimed with a single atomic
UPDATE (status queued -> running, only when still queued).
A second runner process claiming the same row gets zero
rows updated and skips it. A lease (owner + expiry =
timeout) bounds every claim: a run still marked running
after its lease expired is presumed crashed and reclaimed
(attempt incremented, reason recorded) or dead-lettered
when attempts are exhausted. A run inside a live lease is
never touched.

Idempotency: every occurrence has one idempotency key
(``job_key:YYYY-MM-DD``). Creating a run for an existing
key returns the existing row; re-executing a succeeded run
returns its stored result without calling the handler.
Manual runs are idempotent only when the operator supplies
a run tag (``job_key:manual:<tag>``); without one, each
invocation gets a timestamp key and is a distinct run.

Retries: exponential backoff, ``base * 2 ** (attempt - 1)``
seconds. Non-retryable errors (collection stubs, unknown
handlers) dead-letter immediately. Dependency failures do
not fail the dependent: they BLOCK it (status "blocked",
re-evaluated every invocation) until the dependency
succeeds, or until an operator cancels it.

Watermarks: a run reaching a terminal status (succeeded,
dead, cancelled) advances ``last_processed_occurrence`` for
its job in the same commit. Failed (retryable) and blocked
runs do NOT advance it, so catch-up never skips an
unresolved occurrence.

Checkpoints commit immediately (see handlers docstring):
partial progress survives a crash, so a retried run
resumes from its watermark instead of redoing finished
steps.
"""

from __future__ import annotations

import socket
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.jobs import (
    TERMINAL_RUN_STATUSES,
    JobCheckpoint,
    JobDeadLetter,
    JobDefinition,
    JobRun,
)
from app.services.jobs import calendar as cal
from app.services.jobs.handlers import HANDLERS, NON_RETRYABLE, JobContext
from app.services.jobs.registry import JOB_DEFINITIONS


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def new_lease_owner() -> str:
    """Unique per invocation: hostname + pid + short uuid."""
    return f"{socket.gethostname()}:{uuid.uuid4().hex[:8]}"


def _as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def register_definitions(session: Session) -> dict:
    """Seed the registry idempotently. Inserted rows take the
    seed status; existing rows keep their OPERATOR status
    (re-seeding never re-enables a paused job or re-pauses
    an activated one) but refresh schedule/policy fields."""
    inserted: list[str] = []
    updated: list[str] = []
    preserved: list[str] = []
    for definition in JOB_DEFINITIONS:
        existing = session.query(JobDefinition).filter_by(job_key=definition["job_key"]).first()
        if existing is None:
            session.add(
                JobDefinition(
                    job_key=definition["job_key"],
                    title=definition["title"],
                    handler_key=definition["handler_key"],
                    schedule_kind=definition["schedule_kind"],
                    schedule_spec=definition["schedule_spec"],
                    dependencies=list(definition["dependencies"]),
                    timeout_seconds=definition["timeout_seconds"],
                    max_attempts=definition["max_attempts"],
                    backoff_base_seconds=definition["backoff_base_seconds"],
                    priority=definition["priority"],
                    status=definition["status"],
                    pause_reason=definition["pause_reason"],
                )
            )
            inserted.append(definition["job_key"])
        else:
            existing.title = definition["title"]
            existing.handler_key = definition["handler_key"]
            existing.schedule_kind = definition["schedule_kind"]
            existing.schedule_spec = definition["schedule_spec"]
            existing.dependencies = list(definition["dependencies"])
            existing.timeout_seconds = definition["timeout_seconds"]
            existing.max_attempts = definition["max_attempts"]
            existing.backoff_base_seconds = definition["backoff_base_seconds"]
            existing.priority = definition["priority"]
            updated.append(definition["job_key"])
            preserved.append(f"{definition['job_key']}:{existing.status}")
    session.commit()
    return {
        "inserted": inserted,
        "updated": updated,
        "preserved_status": preserved,
    }


def get_definition(session: Session, job_key: str) -> JobDefinition | None:
    return session.query(JobDefinition).filter_by(job_key=job_key).first()


# ---------------------------------------------------------------------------
# Checkpoints / watermarks
# ---------------------------------------------------------------------------


def write_checkpoint(
    session: Session,
    job_key: str,
    watermark_key: str,
    watermark_value: str,
    detail: dict | None = None,
) -> None:
    """Upsert one checkpoint. Commits immediately so partial
    progress survives a crash (see module docstring)."""
    row = (
        session.query(JobCheckpoint).filter_by(job_key=job_key, watermark_key=watermark_key).first()
    )
    now = now_utc()
    if row is None:
        session.add(
            JobCheckpoint(
                job_key=job_key,
                watermark_key=watermark_key,
                watermark_value=watermark_value,
                detail=detail,
                updated_at=now,
            )
        )
    else:
        row.watermark_value = watermark_value
        row.detail = detail
        row.updated_at = now
    session.commit()


def read_checkpoint(session: Session, job_key: str, watermark_key: str) -> JobCheckpoint | None:
    return (
        session.query(JobCheckpoint).filter_by(job_key=job_key, watermark_key=watermark_key).first()
    )


def last_processed_occurrence(session: Session, job_key: str) -> date | None:
    row = read_checkpoint(session, job_key, "last_processed_occurrence")
    if row is None:
        return None
    return date.fromisoformat(row.watermark_value)


def _advance_watermark(session: Session, job_key: str, occurrence: date) -> None:
    """Advance only forward, never backward."""
    previous = last_processed_occurrence(session, job_key)
    if previous is not None and occurrence <= previous:
        return
    row = read_checkpoint(session, job_key, "last_processed_occurrence")
    now = now_utc()
    if row is None:
        session.add(
            JobCheckpoint(
                job_key=job_key,
                watermark_key="last_processed_occurrence",
                watermark_value=occurrence.isoformat(),
                detail=None,
                updated_at=now,
            )
        )
    else:
        row.watermark_value = occurrence.isoformat()
        row.updated_at = now


# ---------------------------------------------------------------------------
# Due computation / materialisation
# ---------------------------------------------------------------------------


def compute_due(session: Session, today: date) -> list[dict]:
    """Due occurrences for active, scheduled jobs, oldest
    first, catch-up capped. Paused and manual jobs are
    reported as skipped, never materialised."""
    due: list[dict] = []
    skipped_paused: list[str] = []
    definitions = session.query(JobDefinition).order_by(JobDefinition.priority).all()
    for definition in definitions:
        if definition.schedule_kind == "manual":
            continue
        if definition.status != "active":
            skipped_paused.append(definition.job_key)
            continue
        last = last_processed_occurrence(session, definition.job_key)
        for occurrence in cal.due_occurrences(
            definition.schedule_kind,
            definition.schedule_spec,
            last,
            today,
        ):
            key = cal.idempotency_key(definition.job_key, occurrence)
            existing = session.query(JobRun).filter_by(idempotency_key=key).first()
            if existing is not None:
                continue  # retry / re-evaluate path owns it
            due.append(
                {
                    "job_key": definition.job_key,
                    "occurrence": occurrence,
                    "idempotency_key": key,
                }
            )
    return due


def materialise_due(session: Session, today: date) -> dict:
    """Create queued runs for due occurrences (insert-if-
    absent; the unique key is the backstop against races)."""
    due = compute_due(session, today)
    created: list[str] = []
    for item in due:
        run = JobRun(
            job_key=item["job_key"],
            idempotency_key=item["idempotency_key"],
            scheduled_for=item["occurrence"],
            status="queued",
        )
        session.add(run)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            continue  # another invoker created it first
        created.append(item["idempotency_key"])
    return {"due": len(due), "created": created}


# ---------------------------------------------------------------------------
# Claiming / reclaim
# ---------------------------------------------------------------------------


def claim_run(session: Session, run: JobRun, owner: str, lease_seconds: int) -> bool:
    """Atomic queued -> running claim. Returns True only
    when this caller won the claim (rowcount 1). A blocked
    run whose dependency has cleared is claimable too: the
    caller (execute_run) checks dependency state first."""
    now = now_utc()
    result = session.execute(
        update(JobRun)
        .where(JobRun.id == run.id, JobRun.status.in_(("queued", "blocked")))
        .values(
            status="running",
            lease_owner=owner,
            lease_expires_at=now + timedelta(seconds=lease_seconds),
            started_at=now,
            attempt=JobRun.attempt + 1,
        )
    )
    session.commit()
    if result.rowcount != 1:
        session.expire(run)
        return False
    session.refresh(run)
    return True


def reclaim_stale(session: Session, now: datetime | None = None) -> dict:
    """Runs still 'running' past their lease are presumed
    crashed: re-queue while attempts remain, else dead-letter.
    Runs inside a live lease are never touched."""
    now = now or now_utc()
    stale = (
        session.query(JobRun)
        .filter_by(status="running")
        .filter(JobRun.lease_expires_at.isnot(None))
        .all()
    )
    requeued: list[int] = []
    dead: list[int] = []
    for run in stale:
        expires = _as_aware(run.lease_expires_at)
        if expires is not None and expires >= now:
            continue
        definition = get_definition(session, run.job_key)
        max_attempts = definition.max_attempts if definition else 3
        if run.attempt < max_attempts:
            run.status = "queued"
            run.lease_owner = None
            run.lease_expires_at = None
            run.next_attempt_at = now
            run.error = "reclaimed_after_lease_expiry"
            requeued.append(run.id)
        else:
            run.status = "dead"
            run.finished_at = now
            run.error = "reclaimed_after_lease_expiry_attempts_exhausted"
            session.add(
                JobDeadLetter(
                    job_key=run.job_key,
                    idempotency_key=run.idempotency_key,
                    run_id=run.id,
                    error=run.error,
                    payload_summary=run.result_summary,
                    failed_at=now,
                )
            )
            if run.scheduled_for is not None:
                _advance_watermark(session, run.job_key, run.scheduled_for)
            dead.append(run.id)
    if requeued or dead:
        session.commit()
    return {"requeued": requeued, "dead": dead}


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def dependency_state(session: Session, run: JobRun) -> tuple[str, str | None]:
    """('ok' | 'waiting' | 'failed', reason). Manual runs
    (no scheduled date) skip dependency gating: the operator
    invoked them explicitly."""
    if run.scheduled_for is None:
        return "ok", None
    definition = get_definition(session, run.job_key)
    if definition is None:
        return "failed", "definition_missing"
    for dependency_key in definition.dependencies or []:
        dep_key = cal.idempotency_key(dependency_key, run.scheduled_for)
        dep_run = session.query(JobRun).filter_by(idempotency_key=dep_key).first()
        if dep_run is None:
            # Dependency not due on this date: nothing to wait for.
            continue
        if dep_run.status == "succeeded":
            continue
        if dep_run.status in TERMINAL_RUN_STATUSES:
            return "failed", f"dependency_{dependency_key}_{dep_run.status}"
        return "waiting", f"dependency_{dependency_key}_{dep_run.status}"
    return "ok", None


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def _dead_letter(session: Session, run: JobRun, error: str, now: datetime) -> None:
    existing = session.query(JobDeadLetter).filter_by(idempotency_key=run.idempotency_key).first()
    if existing is None:
        session.add(
            JobDeadLetter(
                job_key=run.job_key,
                idempotency_key=run.idempotency_key,
                run_id=run.id,
                error=error,
                payload_summary=run.result_summary,
                failed_at=now,
            )
        )


def execute_run(
    session: Session,
    run: JobRun,
    owner: str,
    params: dict | None = None,
) -> dict:
    """Claim and execute one run. Returns the run outcome.
    Idempotent: a succeeded run returns its stored result
    without calling the handler again."""
    if run.status == "succeeded":
        return {
            "run_id": run.id,
            "status": "succeeded",
            "idempotent_replay": True,
            "result_summary": run.result_summary,
        }
    if run.status in ("dead", "cancelled"):
        return {
            "run_id": run.id,
            "status": run.status,
            "error": "terminal run cannot be re-executed; use retry-dead for dead runs",
        }
    definition = get_definition(session, run.job_key)
    if definition is None:
        return {"run_id": run.id, "status": "error", "error": "definition_missing"}
    if run.scheduled_for is not None:
        state, reason = dependency_state(session, run)
        if state != "ok":
            run.status = "blocked"
            run.blocked_reason = reason
            session.commit()
            return {
                "run_id": run.id,
                "status": "blocked",
                "blocked_reason": reason,
            }
    lease_seconds = definition.timeout_seconds
    if run.status == "failed":
        # Retry path: failed -> running directly (the run was
        # already queued for retry by its next_attempt_at).
        now = now_utc()
        result = session.execute(
            update(JobRun)
            .where(JobRun.id == run.id, JobRun.status == "failed")
            .values(
                status="running",
                lease_owner=owner,
                lease_expires_at=now + timedelta(seconds=lease_seconds),
                started_at=now,
                attempt=JobRun.attempt + 1,
                next_attempt_at=None,
            )
        )
        session.commit()
        if result.rowcount != 1:
            session.refresh(run)
            return {"run_id": run.id, "status": run.status}
        session.refresh(run)
    elif not claim_run(session, run, owner, lease_seconds):
        session.refresh(run)
        return {"run_id": run.id, "status": run.status}
    handler = HANDLERS.get(definition.handler_key)
    now = now_utc()

    def _checkpoint(key: str, value: str, detail: dict | None = None) -> None:
        write_checkpoint(session, run.job_key, key, value, detail)

    if handler is None:
        error = f"unknown handler: {definition.handler_key}"
        run.status = "dead"
        run.finished_at = now
        run.error = error
        _dead_letter(session, run, error, now)
        if run.scheduled_for is not None:
            _advance_watermark(session, run.job_key, run.scheduled_for)
        session.commit()
        return {"run_id": run.id, "status": "dead", "error": error}
    ctx = JobContext(
        session=session,
        run=run,
        params=params or {},
        checkpoint=_checkpoint,
    )
    try:
        summary = handler(ctx)
    except NON_RETRYABLE as exc:
        error = f"{type(exc).__name__}: {exc}"
        run.status = "dead"
        run.finished_at = now_utc()
        run.error = error
        _dead_letter(session, run, error, now_utc())
        if run.scheduled_for is not None:
            _advance_watermark(session, run.job_key, run.scheduled_for)
        session.commit()
        return {"run_id": run.id, "status": "dead", "error": error}
    except Exception as exc:  # noqa: BLE001 - runner records, never hides
        error = f"{type(exc).__name__}: {exc}"
        if run.attempt >= definition.max_attempts:
            run.status = "dead"
            run.finished_at = now_utc()
            run.error = error
            _dead_letter(session, run, error, now_utc())
            if run.scheduled_for is not None:
                _advance_watermark(session, run.job_key, run.scheduled_for)
            session.commit()
            return {"run_id": run.id, "status": "dead", "error": error}
        backoff = definition.backoff_base_seconds * (2 ** (run.attempt - 1))
        run.status = "failed"
        run.finished_at = now_utc()
        run.error = error
        run.next_attempt_at = now_utc() + timedelta(seconds=backoff)
        session.commit()
        return {
            "run_id": run.id,
            "status": "failed",
            "error": error,
            "next_attempt_at": run.next_attempt_at.isoformat(),
            "attempt": run.attempt,
        }
    run.status = "succeeded"
    run.finished_at = now_utc()
    run.result_summary = summary
    run.error = None
    run.lease_owner = None
    run.lease_expires_at = None
    if run.scheduled_for is not None:
        _advance_watermark(session, run.job_key, run.scheduled_for)
    session.commit()
    return {
        "run_id": run.id,
        "status": "succeeded",
        "result_summary": summary,
    }


def run_due(session: Session, today: date, owner: str | None = None) -> dict:
    """One full pass: reclaim stale, materialise due,
    re-evaluate blocked, retry due failures, execute queued
    runs in dependency/priority order. Sequential by design:
    no two handlers run concurrently in one invocation, so
    one run cannot exhaust resources for another."""
    owner = owner or new_lease_owner()
    now = now_utc()
    reclaimed = reclaim_stale(session, now)
    materialised = materialise_due(session, today)
    summary: dict[str, object] = {
        "reclaimed": reclaimed,
        "materialised": materialised,
        "executed": [],
        "blocked": [],
        "skipped_dependency_failed": [],
    }
    # Loop while progress is made: each iteration either
    # executes a run or marks one blocked. Blocked runs are
    # re-evaluated after every execution (a dependency may
    # just have succeeded).
    while True:
        progressed = False
        # 1. Re-evaluate blocked runs first.
        for run in session.query(JobRun).filter_by(status="blocked").all():
            state, reason = dependency_state(session, run)
            if state == "ok":
                run.status = "queued"
                run.blocked_reason = None
                session.commit()
                progressed = True
            elif state == "failed":
                # Still blocked (dependency terminally failed);
                # keep waiting for an operator retry of it.
                run.blocked_reason = reason
                session.commit()
        # 2. Pick the next executable run: due retries first,
        # then queued, ordered by date then priority.
        candidates: list[JobRun] = []
        for run in session.query(JobRun).filter(JobRun.status.in_(("queued", "failed"))).all():
            if run.status == "failed":
                nxt = _as_aware(run.next_attempt_at)
                if nxt is not None and nxt > now:
                    continue  # backoff still running
            candidates.append(run)
        if not candidates:
            break
        definitions = {d.job_key: d for d in session.query(JobDefinition).all()}
        candidates.sort(
            key=lambda r: (
                r.scheduled_for is None,
                r.scheduled_for or date.min,
                definitions.get(r.job_key).priority if definitions.get(r.job_key) else 99,
            )
        )
        executed_any = False
        for run in candidates:
            state, reason = dependency_state(session, run)
            if state == "waiting":
                run.status = "blocked"
                run.blocked_reason = reason
                session.commit()
                summary["blocked"].append({"run_id": run.id, "reason": reason})
                progressed = True
                continue
            if state == "failed":
                run.status = "blocked"
                run.blocked_reason = reason
                session.commit()
                summary["skipped_dependency_failed"].append({"run_id": run.id, "reason": reason})
                progressed = True
                continue
            outcome = execute_run(session, run, owner)
            summary["executed"].append(outcome)
            executed_any = True
            progressed = True
            break  # re-evaluate blocked/ordering after each run
        if not executed_any and not progressed:
            break
        if not progressed:
            break
    return summary


# ---------------------------------------------------------------------------
# Operator actions
# ---------------------------------------------------------------------------


def run_one(
    session: Session,
    job_key: str,
    scheduled_for: date | None = None,
    run_tag: str | None = None,
    params: dict | None = None,
    owner: str | None = None,
) -> dict:
    """Execute one job explicitly. Paused jobs are refused
    without creating a run. A succeeded run for the same
    idempotency key replays its stored result."""
    definition = get_definition(session, job_key)
    if definition is None:
        return {"job_key": job_key, "error": "unknown job"}
    if definition.status != "active":
        return {
            "job_key": job_key,
            "error": "job is paused",
            "pause_reason": definition.pause_reason,
        }
    if scheduled_for is not None:
        key = cal.idempotency_key(job_key, scheduled_for)
    elif run_tag:
        key = f"{job_key}:manual:{run_tag}"
    else:
        key = f"{job_key}:manual:{now_utc().strftime('%Y%m%dT%H%M%S')}"
    existing = session.query(JobRun).filter_by(idempotency_key=key).first()
    if existing is not None:
        if existing.status == "succeeded":
            return {
                "run_id": existing.id,
                "status": "succeeded",
                "idempotent_replay": True,
                "result_summary": existing.result_summary,
            }
        if existing.status in ("dead", "cancelled"):
            return {
                "run_id": existing.id,
                "status": existing.status,
                "error": "terminal run; use retry-dead for dead runs",
            }
        return execute_run(session, existing, owner or new_lease_owner(), params)
    run = JobRun(
        job_key=job_key,
        idempotency_key=key,
        scheduled_for=scheduled_for,
        status="queued",
    )
    session.add(run)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.query(JobRun).filter_by(idempotency_key=key).first()
        if existing is not None and existing.status == "succeeded":
            return {
                "run_id": existing.id,
                "status": "succeeded",
                "idempotent_replay": True,
                "result_summary": existing.result_summary,
            }
        return {"job_key": job_key, "error": "run already exists", "key": key}
    return execute_run(session, run, owner or new_lease_owner(), params)


def cancel_run(session: Session, run_id: int) -> dict:
    """Cancel a queued or blocked run (terminal: advances
    the watermark). A running run cannot be cancelled from
    here — the operator waits for it or lets its lease
    expire, so a half-finished handler is never orphaned
    by a blind kill."""
    run = session.query(JobRun).filter_by(id=run_id).first()
    if run is None:
        return {"run_id": run_id, "error": "unknown run"}
    if run.status == "running":
        return {
            "run_id": run_id,
            "status": run.status,
            "error": "running run cannot be cancelled; wait for completion or lease expiry",
        }
    if run.status in TERMINAL_RUN_STATUSES:
        return {"run_id": run_id, "status": run.status}
    run.status = "cancelled"
    run.finished_at = now_utc()
    if run.scheduled_for is not None:
        _advance_watermark(session, run.job_key, run.scheduled_for)
    session.commit()
    return {"run_id": run_id, "status": "cancelled"}


def retry_dead_letter(session: Session, dead_letter_id: int) -> dict:
    """Create a fresh queued run for a dead letter (new
    idempotency key, attempts reset) and mark the letter
    resolved. The new run is NOT executed here: the
    operator runs it via run-due or run-one."""
    letter = session.query(JobDeadLetter).filter_by(id=dead_letter_id).first()
    if letter is None:
        return {"dead_letter_id": dead_letter_id, "error": "unknown dead letter"}
    if letter.resolved:
        return {"dead_letter_id": dead_letter_id, "error": "already resolved"}
    original = session.query(JobRun).filter_by(id=letter.run_id).first()
    siblings = (
        session.query(JobRun)
        .filter(JobRun.idempotency_key.like(f"{letter.idempotency_key}:retry-%"))
        .count()
    )
    new_key = f"{letter.idempotency_key}:retry-{siblings + 1}"
    run = JobRun(
        job_key=letter.job_key,
        idempotency_key=new_key,
        scheduled_for=original.scheduled_for if original else None,
        status="queued",
    )
    session.add(run)
    letter.resolved = True
    session.commit()
    return {
        "dead_letter_id": dead_letter_id,
        "new_run_id": run.id,
        "new_idempotency_key": new_key,
        "status": "queued",
    }


def status(session: Session, now: datetime | None = None) -> dict:
    """Operations status: run counts, stuck runs, paused
    definitions, unresolved dead letters, watermarks."""
    now = now or now_utc()
    by_status: dict[str, int] = {}
    for run in session.query(JobRun).all():
        by_status[run.status] = by_status.get(run.status, 0) + 1
    stuck = []
    for run in session.query(JobRun).filter_by(status="running").all():
        expires = _as_aware(run.lease_expires_at)
        if expires is not None and expires < now:
            stuck.append({"run_id": run.id, "job_key": run.job_key, "lease_owner": run.lease_owner})
    paused = [
        {"job_key": d.job_key, "pause_reason": d.pause_reason}
        for d in session.query(JobDefinition).filter_by(status="paused").all()
    ]
    unresolved = session.query(JobDeadLetter).filter_by(resolved=False).count()
    watermarks = {
        f"{c.job_key}:{c.watermark_key}": c.watermark_value
        for c in session.query(JobCheckpoint).all()
    }
    return {
        "runs_by_status": by_status,
        "runs_total": sum(by_status.values()),
        "stuck_runs": stuck,
        "paused_definitions": paused,
        "unresolved_dead_letters": unresolved,
        "watermarks": watermarks,
    }
