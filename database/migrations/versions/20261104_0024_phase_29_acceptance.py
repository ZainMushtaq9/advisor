"""phase_29_acceptance

Revision ID: 20261104_0024
Revises: 20261104_0023
Create Date: 2026-11-05

Phase 29 (end-to-end integration, system acceptance, independent
audit) tables: acceptance_runs (one row per invocation, unique
run_id idempotency key, verdict + gate evaluation JSON),
acceptance_scenarios (one row per (run, scenario): outcome pass /
fail / blocked / not_evaluable + evidence + reason; a blocked
scenario is not a system failure and a not_evaluable scenario is
recorded, not passed by default),
acceptance_recomputations (one row per (run, check): claimed value,
independently recomputed value, match flag, tolerance, method; a
mismatch row is kept, not deleted — it is the audit finding),
acceptance_defects (one row per (run, defect key): severity
critical / high / medium / low, lifecycle status open / fixed /
accepted, impact, exact unblocker or fix).

Precedent note (Phases 11-28): Phase 29 stores its own tables
rather than retrofitting Phase 3 tables. These tables carry no
quality_status: they are audit records, not business data, and no
quality-status promotion ever applies to them. No order,
execution, external-send, or publication concept exists in these
tables. No credentials are stored anywhere here.

Integer primary keys (not IdMixin Identity): see
backend/app/models/acceptance.py for the SQLite portability reason.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0024"
down_revision: str | None = "20261104_0023"
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
        "acceptance_runs",
        _pk(),
        sa.Column("run_id", sa.String(length=200), nullable=False, unique=True),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("verdict", sa.String(length=30), nullable=False),
        sa.Column("gate_evaluation", sa.JSON(), nullable=False),
        _created(),
        sa.CheckConstraint(
            "verdict IN ('COMPLETE', 'PARTIALLY COMPLETE', 'BLOCKED', 'FAILED')",
            name="ck_acceptance_runs_verdict",
        ),
    )
    op.create_table(
        "acceptance_scenarios",
        _pk(),
        sa.Column(
            "run_id",
            sa.String(length=200),
            sa.ForeignKey("acceptance_runs.run_id"),
            nullable=False,
        ),
        sa.Column("scenario_key", sa.String(length=100), nullable=False),
        sa.Column("case_name", sa.String(length=300), nullable=False),
        sa.Column("outcome", sa.String(length=30), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        _created(),
        sa.UniqueConstraint(
            "run_id", "scenario_key", name="uq_acceptance_scenario_grain"
        ),
        sa.CheckConstraint(
            "outcome IN ('pass', 'fail', 'blocked', 'not_evaluable')",
            name="ck_acceptance_scenarios_outcome",
        ),
    )
    op.create_table(
        "acceptance_recomputations",
        _pk(),
        sa.Column(
            "run_id",
            sa.String(length=200),
            sa.ForeignKey("acceptance_runs.run_id"),
            nullable=False,
        ),
        sa.Column("check_key", sa.String(length=100), nullable=False),
        sa.Column("claimed_value", sa.Text(), nullable=False),
        sa.Column("recomputed_value", sa.Text(), nullable=False),
        sa.Column("matches", sa.Boolean(), nullable=False),
        sa.Column("tolerance", sa.String(length=200), nullable=False),
        sa.Column("method", sa.Text(), nullable=False),
        _created(),
        sa.UniqueConstraint(
            "run_id", "check_key", name="uq_acceptance_recomputation_grain"
        ),
    )
    op.create_table(
        "acceptance_defects",
        _pk(),
        sa.Column(
            "run_id",
            sa.String(length=200),
            sa.ForeignKey("acceptance_runs.run_id"),
            nullable=False,
        ),
        sa.Column("defect_key", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("unblocker", sa.Text(), nullable=False),
        _created(),
        sa.UniqueConstraint("run_id", "defect_key", name="uq_acceptance_defect_grain"),
        sa.CheckConstraint(
            "severity IN ('critical', 'high', 'medium', 'low')",
            name="ck_acceptance_defects_severity",
        ),
        sa.CheckConstraint(
            "status IN ('open', 'fixed', 'accepted')",
            name="ck_acceptance_defects_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("acceptance_defects")
    op.drop_table("acceptance_recomputations")
    op.drop_table("acceptance_scenarios")
    op.drop_table("acceptance_runs")
