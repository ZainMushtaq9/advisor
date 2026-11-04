"""phase_26_evaluation

Revision ID: 20261104_0022
Revises: 20261104_0021
Create Date: 2026-11-05

Phase 26 (model evaluation, forecast monitoring and research
quality benchmarking) tables: evaluation_datasets (versioned
dataset registry with out-of-sample split policies),
model_cards (one card per model/version, all NOT_PROMOTED),
promotion_gates (all NOT_MET until positive evidence exists),
evaluation_runs (one row per evaluation invocation, unique
run_id idempotency key), evaluation_metrics (value or NULL +
status + reason + evidence; NOT_EVALUABLE is a stored fact,
never a zero-fill), golden_test_cases (fixed suite for source
matching, entity resolution, tool selection, citations,
extraction, summarization, refusal/abstention, injection
resistance, conflicting sources), golden_test_results (one
row per run x case).

Precedent note (Phases 11-25): Phase 26 stores its own tables
rather than retrofitting Phase 3 tables. These tables carry no
quality_status: they are evaluation records, not business
data, and no quality-status promotion ever applies to them.
No order, execution, external-send, or publication concept
exists in these tables. No credentials are stored anywhere.
Integer primary keys (not IdMixin Identity): see
backend/app/models/evaluation.py for the SQLite portability reason.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0022"
down_revision: str | None = "20261104_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _pk() -> sa.Column:
    return sa.Column(
        "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
    )


def _created() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


def upgrade() -> None:
    op.create_table(
        "evaluation_datasets",
        _pk(),
        sa.Column("dataset_key", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("split_policy", sa.String(length=1000), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("evidence", sa.JSON(), nullable=True),
        _created(),
        sa.UniqueConstraint("dataset_key", name="uq_evaluation_datasets_key"),
        sa.CheckConstraint(
            "status IN ('defined', 'active', 'retired')",
            name="ck_evaluation_datasets_status",
        ),
    )
    op.create_table(
        "model_cards",
        _pk(),
        sa.Column("model_key", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("purpose", sa.String(length=1000), nullable=False),
        sa.Column("training_data", sa.String(length=1000), nullable=False),
        sa.Column("evaluation_status", sa.String(length=1000), nullable=False),
        sa.Column("limitations", sa.String(length=2000), nullable=False),
        sa.Column(
            "promotion_status",
            sa.String(length=20),
            nullable=False,
            server_default="NOT_PROMOTED",
        ),
        sa.Column("evidence", sa.JSON(), nullable=True),
        _created(),
        sa.UniqueConstraint(
            "model_key", "version", name="uq_model_cards_key_version"
        ),
        sa.CheckConstraint(
            "promotion_status IN ('NOT_PROMOTED', 'PROMOTED')",
            name="ck_model_cards_promotion_status",
        ),
    )
    op.create_table(
        "promotion_gates",
        _pk(),
        sa.Column("gate_key", sa.String(length=100), nullable=False),
        sa.Column("applies_to", sa.String(length=100), nullable=False),
        sa.Column("requirement", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="NOT_MET"),
        sa.Column("reason", sa.String(length=1000), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        _created(),
        sa.UniqueConstraint("gate_key", name="uq_promotion_gates_key"),
        sa.CheckConstraint(
            "status IN ('NOT_MET', 'MET', 'BLOCKED')",
            name="ck_promotion_gates_status",
        ),
    )
    op.create_table(
        "evaluation_runs",
        _pk(),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False, server_default="full"),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="completed"
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=True),
        _created(),
        sa.UniqueConstraint("run_id", name="uq_evaluation_runs_run_id"),
        sa.CheckConstraint(
            "kind IN ('forecast', 'recommendation', 'agent_rag', 'backtest', "
            "'reports_qa', 'drift', 'golden', 'full')",
            name="ck_evaluation_runs_kind",
        ),
        sa.CheckConstraint(
            "status IN ('completed', 'failed')",
            name="ck_evaluation_runs_status",
        ),
    )
    op.create_table(
        "evaluation_metrics",
        _pk(),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("subject_key", sa.String(length=100), nullable=False),
        sa.Column("metric_key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Numeric(24, 6), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.String(length=1000), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        _created(),
        sa.UniqueConstraint(
            "run_id", "subject_key", "metric_key", name="uq_evaluation_metrics_grain"
        ),
        sa.CheckConstraint(
            "status IN ('computed', 'insufficient_inputs', 'not_applicable', "
            "'not_evaluable')",
            name="ck_evaluation_metrics_status",
        ),
    )
    op.create_table(
        "golden_test_cases",
        _pk(),
        sa.Column("case_key", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("input_desc", sa.String(length=1000), nullable=False),
        sa.Column("expected_outcome", sa.String(length=1000), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        _created(),
        sa.UniqueConstraint("case_key", name="uq_golden_test_cases_key"),
    )
    op.create_table(
        "golden_test_results",
        _pk(),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("case_key", sa.String(length=100), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("evidence", sa.JSON(), nullable=True),
        _created(),
        sa.UniqueConstraint(
            "run_id", "case_key", name="uq_golden_test_results_grain"
        ),
    )


def downgrade() -> None:
    op.drop_table("golden_test_results")
    op.drop_table("golden_test_cases")
    op.drop_table("evaluation_metrics")
    op.drop_table("evaluation_runs")
    op.drop_table("promotion_gates")
    op.drop_table("model_cards")
    op.drop_table("evaluation_datasets")
