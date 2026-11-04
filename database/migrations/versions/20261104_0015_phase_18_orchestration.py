"""phase_18_orchestration

Revision ID: 20261104_0015
Revises: 20261104_0014
Create Date: 2026-11-04

Phase 18 (multi-agent orchestration and agent runtime) tables:
agent_definitions (16 registered agents with capability
contracts), orchestration_runs (one run per task graph),
orchestration_tasks (task ledger with idempotency keys and
checkpoints), agent_audit_logs (prompt/template references,
model identifiers, tool calls, token/resource use where
available, outputs, evidence, errors), agent_evaluations
(stored evaluation case results).

Precedent note (Phases 11-17): Phase 18 stores its own tables
rather than retrofitting Phase 3 tables. No Phase 3
orchestration table exists. No CSVs or PDFs are involved; no
credentials are stored anywhere. Quality vocabulary CHECK
mirrors migration 20261104_0003.

No execution concept exists in these tables: orchestration
records task execution only. There is no broker, order, or
execution column, table, or relationship anywhere in this
project. Audit logs carry input references, never payloads
that could contain credentials.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0015"
down_revision: str | None = "20261104_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

QUALITY_VALUES = (
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "UNVERIFIED",
    "CONFLICTED",
    "MISSING",
    "REJECTED",
    "STALE",
    "PENDING_REVIEW",
)


def _quality_check(table: str) -> str:
    values = ", ".join(f"'{v}'" for v in QUALITY_VALUES)
    return f"quality_status IN ({values})"


def _provenance_columns() -> list:
    return [
        sa.Column("data_source_id", sa.BigInteger(), nullable=True),
        sa.Column("source_key", sa.String(100), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "quality_status", sa.String(30), nullable=False, server_default="UNVERIFIED"
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "agent_definitions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("outputs", sa.JSON(), nullable=False),
        sa.Column("allowed_tools", sa.JSON(), nullable=False),
        sa.Column("permissions_tier", sa.String(30), nullable=False),
        sa.Column("timeout_seconds", sa.BigInteger(), nullable=False),
        sa.Column("max_retries", sa.BigInteger(), nullable=False),
        sa.Column("backoff_seconds", sa.JSON(), nullable=False),
        sa.Column("cost_envelope_pkr", sa.BigInteger(), nullable=False),
        sa.Column("failure_mode", sa.String(50), nullable=False),
        sa.Column("execution_backend", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
    )
    op.create_table(
        "orchestration_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        *_provenance_columns(),
        sa.Column("run_id", sa.String(100), nullable=False, unique=True),
        sa.Column("graph_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("checkpoint", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            _quality_check("orchestration_runs"), name="ck_orchestration_runs_quality"
        ),
    )
    op.create_table(
        "orchestration_tasks",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "run_id",
            sa.BigInteger(),
            sa.ForeignKey("orchestration_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("task_key", sa.String(100), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("depends_on", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False, unique=True),
        sa.Column("attempt_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("checkpoint", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "run_id", "task_key", name="uq_orchestration_tasks_run_key"
        ),
        sa.Index("ix_orchestration_tasks_run", "run_id"),
    )
    op.create_table(
        "agent_audit_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "run_id",
            sa.BigInteger(),
            sa.ForeignKey("orchestration_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            sa.BigInteger(),
            sa.ForeignKey("orchestration_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("prompt_template", sa.String(100), nullable=False),
        sa.Column("model_identifier", sa.String(100), nullable=False),
        sa.Column("tool_calls", sa.JSON(), nullable=False),
        sa.Column("token_use", sa.JSON(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("quarantined", sa.Boolean(), nullable=False, server_default="false"),
        sa.Index("ix_agent_audit_logs_run", "run_id"),
    )
    op.create_table(
        "agent_evaluations",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "run_id",
            sa.BigInteger(),
            sa.ForeignKey("orchestration_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "run_id", "case_name", name="uq_agent_evaluations_run_case"
        ),
        sa.Index("ix_agent_evaluations_run", "run_id"),
    )


def downgrade() -> None:
    op.drop_table("agent_evaluations")
    op.drop_table("agent_audit_logs")
    op.drop_table("orchestration_tasks")
    op.drop_table("orchestration_runs")
    op.drop_table("agent_definitions")
