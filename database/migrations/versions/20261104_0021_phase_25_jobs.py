"""phase_25_jobs

Revision ID: 20261104_0021
Revises: 20261104_0020
Create Date: 2026-11-05

Phase 25 (automation, scheduling, workflow recovery and job
control) tables: job_definitions (registry: handler, schedule,
dependencies, timeout/retry/backoff, priority, active/paused),
job_runs (one row per occurrence, unique idempotency key,
lease owner/expiry for overlap prevention and crash reclaim),
job_checkpoints (last successful watermark per job/key), and
job_dead_letters (terminally failed runs awaiting an explicit
operator retry).

Precedent note (Phases 11-24): Phase 25 stores its own tables
rather than retrofitting Phase 3 tables. These tables carry no
quality_status: they are automation records, not business
data, and no quality-status promotion ever applies to them.
No order, execution, external-send, or publication concept
exists in these tables. No credentials are stored anywhere.
Integer primary keys (not IdMixin Identity): see
backend/app/models/jobs.py for the SQLite portability reason.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0021"
down_revision: str | None = "20261104_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_definitions",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("job_key", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("handler_key", sa.String(length=100), nullable=False),
        sa.Column("schedule_kind", sa.String(length=20), nullable=False),
        sa.Column("schedule_spec", sa.JSON(), nullable=False),
        sa.Column("dependencies", sa.JSON(), nullable=False),
        sa.Column(
            "timeout_seconds", sa.Integer(), nullable=False, server_default="600"
        ),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column(
            "backoff_base_seconds", sa.Integer(), nullable=False, server_default="60"
        ),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("pause_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("job_key", name="uq_job_definitions_job_key"),
        sa.CheckConstraint(
            "status IN ('active', 'paused')", name="ck_job_definitions_status"
        ),
        sa.CheckConstraint(
            "schedule_kind IN ('daily', 'weekly', 'monthly', 'quarterly', "
            "'annual', 'manual')",
            name="ck_job_definitions_schedule_kind",
        ),
    )
    op.create_table(
        "job_runs",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("job_key", sa.String(length=100), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("scheduled_for", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(length=100), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_summary", sa.JSON(), nullable=True),
        sa.Column("error", sa.String(length=2000), nullable=True),
        sa.Column("blocked_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("idempotency_key", name="uq_job_runs_idempotency_key"),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'dead', "
            "'cancelled', 'blocked')",
            name="ck_job_runs_status",
        ),
    )
    op.create_table(
        "job_checkpoints",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("job_key", sa.String(length=100), nullable=False),
        sa.Column("watermark_key", sa.String(length=100), nullable=False),
        sa.Column("watermark_value", sa.String(length=200), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "job_key", "watermark_key", name="uq_job_checkpoints_job_watermark"
        ),
    )
    op.create_table(
        "job_dead_letters",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("job_key", sa.String(length=100), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("error", sa.String(length=2000), nullable=False),
        sa.Column("payload_summary", sa.JSON(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["run_id"], ["job_runs.id"]),
        sa.UniqueConstraint(
            "idempotency_key", name="uq_job_dead_letters_idempotency_key"
        ),
    )


def downgrade() -> None:
    op.drop_table("job_dead_letters")
    op.drop_table("job_checkpoints")
    op.drop_table("job_runs")
    op.drop_table("job_definitions")
