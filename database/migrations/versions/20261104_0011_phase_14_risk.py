"""phase_14_risk

Revision ID: 20261104_0011
Revises: 20261104_0010
Create Date: 2026-11-04

Phase 14 (risk management and exposure analytics) tables. No CSVs or
PDFs are involved; no credentials are stored anywhere. Quality
vocabulary CHECK mirrors migration 20261104_0003.

Precedent note (Phases 11-13): Phase 14 stores its own tables
rather than retrofitting Phase 3 tables. In particular no Phase 3
``portfolios`` / ``portfolio_holdings`` row is written: the only
portfolio in this phase is a SIMULATED equal-weight reference
portfolio whose definition lives in code and in stress-result
evidence, never as a real holding.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0011"
down_revision: str | None = "20261104_0010"
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
            "quality_status",
            sa.String(30),
            nullable=False,
            server_default="UNVERIFIED",
        ),
    ]


def _id_created() -> list:
    return [
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "risk_metric_definitions",
        *_id_created(),
        sa.Column("metric_key", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("formula", sa.Text(), nullable=False),
        sa.Column("min_observations", sa.BigInteger(), nullable=False),
        sa.Column("window", sa.String(100), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.UniqueConstraint("metric_key", name="uq_risk_metric_definitions_key"),
    )
    op.create_table(
        "risk_metric_values",
        *_id_created(),
        *_provenance_columns(),
        sa.Column("metric_key", sa.String(100), nullable=False),
        sa.Column("scope_key", sa.String(100), nullable=False),
        sa.Column("security_id", sa.BigInteger(), nullable=True),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(24, 6), nullable=True),
        sa.Column("computation_status", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.UniqueConstraint(
            "metric_key", "scope_key", "as_of_date", name="uq_risk_metric_values_grain"
        ),
        sa.Index("ix_risk_metric_values_scope", "scope_key"),
        sa.CheckConstraint(
            _quality_check("risk_metric_values"), name="ck_risk_metric_values_quality"
        ),
    )
    op.create_table(
        "risk_flags",
        *_id_created(),
        *_provenance_columns(),
        sa.Column("flag_type", sa.String(100), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=True),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.UniqueConstraint(
            "flag_type", "company_id", "as_of_date", name="uq_risk_flags_grain"
        ),
        sa.Index("ix_risk_flags_company", "company_id"),
        sa.CheckConstraint(_quality_check("risk_flags"), name="ck_risk_flags_quality"),
    )
    op.create_table(
        "risk_controls",
        *_id_created(),
        sa.Column("control_key", sa.String(100), nullable=False),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("rule", sa.JSON(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.UniqueConstraint(
            "control_key", "version", name="uq_risk_controls_key_version"
        ),
    )
    op.create_table(
        "risk_control_checks",
        *_id_created(),
        *_provenance_columns(),
        sa.Column("control_key", sa.String(100), nullable=False),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("scope_key", sa.String(100), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("outcome", sa.String(30), nullable=False),
        sa.Column("observed_value", sa.Numeric(24, 6), nullable=True),
        sa.Column("threshold_value", sa.Numeric(24, 6), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.UniqueConstraint(
            "control_key",
            "version",
            "scope_key",
            "as_of_date",
            name="uq_risk_control_checks_grain",
        ),
        sa.CheckConstraint(
            _quality_check("risk_control_checks"), name="ck_risk_control_checks_quality"
        ),
    )
    op.create_table(
        "stress_scenarios",
        *_id_created(),
        sa.Column("scenario_key", sa.String(100), nullable=False),
        sa.Column("shock", sa.Text(), nullable=False),
        sa.Column("applies_to", sa.String(100), nullable=False),
        sa.Column("method", sa.Text(), nullable=False),
        sa.UniqueConstraint("scenario_key", name="uq_stress_scenarios_key"),
    )
    op.create_table(
        "stress_results",
        *_id_created(),
        *_provenance_columns(),
        sa.Column("scenario_key", sa.String(100), nullable=False),
        sa.Column("scope_key", sa.String(100), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("impact_pct", sa.Numeric(24, 6), nullable=True),
        sa.Column("computation_status", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.UniqueConstraint(
            "scenario_key", "scope_key", "as_of_date", name="uq_stress_results_grain"
        ),
        sa.CheckConstraint(
            _quality_check("stress_results"), name="ck_stress_results_quality"
        ),
    )


def downgrade() -> None:
    op.drop_table("stress_results")
    op.drop_table("stress_scenarios")
    op.drop_table("risk_control_checks")
    op.drop_table("risk_controls")
    op.drop_table("risk_flags")
    op.drop_table("risk_metric_values")
    op.drop_table("risk_metric_definitions")
