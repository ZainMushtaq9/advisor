"""Phase 25 job automation models: registry, runs, checkpoints, dead letters.

Four tables, all owned by this phase (precedent: Phases 11-22 store
their own tables rather than retrofitting Phase 3 tables):

- ``job_definitions``: one row per registered job type: its handler,
  its schedule (matching the real source cadence), its dependency
  list, its timeout/retry/backoff policy, its priority, and its
  operator status (active/paused + the reason when paused). A
  paused job is NEVER executed by the runner; pausing is the
  enforcement mechanism for Terms-gated collection jobs.
- ``job_runs``: one row per scheduled occurrence (or manual run),
  keyed by a unique idempotency key (``job_key:occurrence``).
  A second claim of the same key never re-executes the handler:
  it returns the prior result. ``lease_owner`` /
  ``lease_expires_at`` implement overlap prevention: only the
  lease holder may run the row, and an expired lease is
  reclaimable after a crash (attempt incremented, reason
  recorded) — never silently re-run while a live lease holds.
- ``job_checkpoints``: last successful watermark per job
  (``(job_key, watermark_key)`` unique). Handlers record
  progress here; a resumed run continues from the watermark
  instead of redoing finished steps. The runner also records
  ``last_processed_occurrence`` here so catch-up after an
  offline period is bounded and ordered, never a storm.
- ``job_dead_letters``: one row per terminally failed run
  (attempts exhausted or a non-retryable error). The operator
  retries a dead letter explicitly (new run, new idempotency
  key, dead letter marked resolved) — never automatically.

These tables carry no quality_status: they are automation
records, not business data, and no quality-status promotion
ever applies to them. No order, execution, external-send, or
publication concept exists in these tables. No credentials are
stored anywhere here.

ID deviation, deliberate (same reason as Phase 24 auth
tables): these tables do NOT use ``IdMixin``. ``IdMixin`` uses
``Identity(always=True)`` (PostgreSQL-only) and a BigInteger PK
is not a rowid alias on SQLite, so inserts fail NOT NULL
there. The job tables use a plain Integer primary key with
autoincrement — SERIAL on PostgreSQL, INTEGER rowid alias on
SQLite — so the same code runs on both. The migration matches
this exactly.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin

JOB_STATUSES = ("active", "paused")

SCHEDULE_KINDS = ("daily", "weekly", "monthly", "quarterly", "annual", "manual")

RUN_STATUSES = (
    "queued",
    "running",
    "succeeded",
    "failed",
    "dead",
    "cancelled",
    "blocked",
)

# Terminal for watermark purposes: once a run reaches one of
# these, its occurrence is processed and catch-up moves past it.
# "failed" (retryable) and "blocked" (waiting on a dependency)
# are NOT terminal: the next invocation re-evaluates them.
TERMINAL_RUN_STATUSES = ("succeeded", "dead", "cancelled")


class JobDefinition(CreatedMixin, Base):
    """One registered job type and its schedule/policy."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "job_definitions"
    __table_args__ = (
        UniqueConstraint("job_key", name="uq_job_definitions_job_key"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in JOB_STATUSES)})",
            name="ck_job_definitions_status",
        ),
        CheckConstraint(
            f"schedule_kind IN ({', '.join(repr(s) for s in SCHEDULE_KINDS)})",
            name="ck_job_definitions_schedule_kind",
        ),
    )

    job_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    handler_key: Mapped[str] = mapped_column(String(100), nullable=False)
    # Schedule spec JSON, e.g. {"time": "16:30", "weekdays": [0, 1, 2, 3, 4]}
    # for daily; see app.services.jobs.calendar for the full spec.
    schedule_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    schedule_spec: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    dependencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=600)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    backoff_base_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    # Lower runs first within one invocation.
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # Required when paused: the exact reason (e.g. Terms evidence pending).
    pause_reason: Mapped[str | None] = mapped_column(String(500))


class JobRun(CreatedMixin, Base):
    """One scheduled occurrence (or manual run) of one job."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "job_runs"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_job_runs_idempotency_key"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in RUN_STATUSES)})",
            name="ck_job_runs_status",
        ),
    )

    job_key: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_for: Mapped[object | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(100))
    lease_expires_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    next_attempt_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    result_summary: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(String(2000))
    blocked_reason: Mapped[str | None] = mapped_column(String(500))


class JobCheckpoint(CreatedMixin, Base):
    """Last successful watermark for one job and one watermark key."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "job_checkpoints"
    __table_args__ = (
        UniqueConstraint("job_key", "watermark_key", name="uq_job_checkpoints_job_watermark"),
    )

    job_key: Mapped[str] = mapped_column(String(100), nullable=False)
    watermark_key: Mapped[str] = mapped_column(String(100), nullable=False)
    watermark_value: Mapped[str] = mapped_column(String(200), nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSON)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class JobDeadLetter(CreatedMixin, Base):
    """One terminally failed run, awaiting an explicit operator retry."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "job_dead_letters"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_job_dead_letters_idempotency_key"),
    )

    job_key: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_runs.id"), nullable=False)
    error: Mapped[str] = mapped_column(String(2000), nullable=False)
    payload_summary: Mapped[dict | None] = mapped_column(JSON)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
