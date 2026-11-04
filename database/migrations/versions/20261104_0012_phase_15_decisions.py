"""phase_15_decisions

Revision ID: 20261104_0012
Revises: 20261104_0011
Create Date: 2026-11-04

Phase 15 (investment decision and recommendation engine) tables:
decision_rules (one versioned rule set), decisions (screening
outcome, research conclusion, user-facing value, confidence,
scores, evidence snapshot, conflicts, gates), decision_outcomes
(observed subsequent outcomes; 0 rows until a later observation
arrives — nothing backfilled).

Precedent note (Phases 11-14): Phase 15 stores its own tables
rather than retrofitting the Phase 3 ``recommendations`` table:
the Phase 3 table has no screening/research/user-facing split,
no rule version, no evidence snapshot, no conflicts, and no
gate reasons, and its semantics (a recommendation) do not match
this phase's three-level design. No CSVs or PDFs are involved;
no credentials are stored anywhere. Quality vocabulary CHECK
mirrors migration 20261104_0003.

No execution concept exists in these tables: there is no broker,
order, or execution column, table, or relationship anywhere in
this project.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0012"
down_revision: str | None = "20261104_0011"
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


def _version_columns() -> list:
    return [
        sa.Column("version_number", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("supersedes_id", sa.BigInteger(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
    ]


def upgrade() -> None:
    op.create_table(
        "decision_rules",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("dimensions", sa.JSON(), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("thresholds", sa.JSON(), nullable=False),
        sa.Column("gates", sa.JSON(), nullable=False),
        sa.Column("precedence", sa.JSON(), nullable=False),
        sa.Column("confidence_rules", sa.JSON(), nullable=False),
        sa.UniqueConstraint("version", name="uq_decision_rules_version"),
    )
    op.create_table(
        "decisions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        *_provenance_columns(),
        *_version_columns(),
        sa.Column("company_id", sa.BigInteger(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("security_id", sa.BigInteger(), sa.ForeignKey("securities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=False),
        sa.Column("rules_version", sa.String(50), nullable=False),
        sa.Column("screening_outcome", sa.String(30), nullable=False),
        sa.Column("research_conclusion", sa.String(30), nullable=False),
        sa.Column("user_facing", sa.String(30), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("total_score", sa.Numeric(10, 4), nullable=True),
        sa.Column("scored_dimensions", sa.BigInteger(), nullable=False),
        sa.Column("completeness", sa.Numeric(10, 4), nullable=True),
        sa.Column("evidence_snapshot", sa.JSON(), nullable=False),
        sa.Column("conflicts", sa.JSON(), nullable=False),
        sa.Column("gate_reasons", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "company_id", "decision_date", "rules_version", name="uq_decisions_grain"
        ),
        sa.Index("ix_decisions_company", "company_id"),
    )
    op.create_table(
        "decision_outcomes",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        *_provenance_columns(),
        sa.Column("decision_id", sa.BigInteger(), sa.ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("outcome_date", sa.Date(), nullable=False),
        sa.Column("outcome_type", sa.String(100), nullable=False),
        sa.Column("value", sa.Numeric(24, 6), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.UniqueConstraint(
            "decision_id", "outcome_type", "outcome_date", name="uq_decision_outcomes_grain"
        ),
        sa.Index("ix_decision_outcomes_decision", "decision_id"),
    )


def downgrade() -> None:
    op.drop_table("decision_outcomes")
    op.drop_table("decisions")
    op.drop_table("decision_rules")
