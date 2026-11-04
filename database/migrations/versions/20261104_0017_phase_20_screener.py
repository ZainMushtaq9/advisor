"""phase_20_screener

Revision ID: 20261104_0017
Revises: 20261104_0016
Create Date: 2026-11-04

Phase 20 (market screener and opportunity discovery) tables:
screen_definitions (versioned, reusable filter sets),
screen_runs (one row per (definition, as-of date) pair),
screen_results (one outcome row per (run, security)).

Precedent note (Phases 11-19): Phase 20 stores its own tables
rather than retrofitting Phase 3 tables. No Phase 3 screener
table exists. Results are filter outcomes, not investment
opportunities, recommendations, or forecasts: Phase 15
user-facing values are WITHHELD and Phase 13 forecasts are
abstained, and the screener does not reintroduce either. No
order or execution concept exists in these tables: screening
is read-only filtering over stored rows plus stored results.
No CSVs or PDFs are committed by this migration. No
credentials are stored anywhere.

Quality vocabulary CHECK mirrors migration 20261104_0003.
created_at carries a server default (as in the Phase 19
migration); the ORM models do not declare it.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261104_0017"
down_revision: str | None = "20261104_0016"
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


def _quality_check(table: str, column: str = "quality_status") -> sa.CheckConstraint:
    values = ", ".join(f"'{v}'" for v in QUALITY_VALUES)
    return sa.CheckConstraint(f"{column} IN ({values})", name=f"ck_{table}_{column}")


def upgrade() -> None:
    op.create_table(
        "screen_definitions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("universe", sa.String(length=50), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column(
            "quality_status", sa.String(length=30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", name="uq_screen_definitions_name_version"),
        _quality_check("screen_definitions"),
    )
    op.create_table(
        "screen_runs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("screen_definition_id", sa.BigInteger(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("universe_size", sa.BigInteger(), nullable=False),
        sa.Column("matched_count", sa.BigInteger(), nullable=False),
        sa.Column("insufficient_count", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column(
            "quality_status", sa.String(length=30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.ForeignKeyConstraint(
            ["screen_definition_id"], ["screen_definitions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "screen_definition_id", "as_of_date", name="uq_screen_runs_definition_asof"
        ),
        _quality_check("screen_runs"),
    )
    op.create_index("ix_screen_runs_definition", "screen_runs", ["screen_definition_id"])
    op.create_table(
        "screen_results",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("screen_run_id", sa.BigInteger(), nullable=False),
        sa.Column("security_id", sa.BigInteger(), nullable=False),
        sa.Column("outcome", sa.String(length=30), nullable=False),
        sa.Column("score", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("passed_count", sa.BigInteger(), nullable=False),
        sa.Column("scored_count", sa.BigInteger(), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column(
            "quality_status", sa.String(length=30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.ForeignKeyConstraint(["screen_run_id"], ["screen_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["security_id"], ["securities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("screen_run_id", "security_id", name="uq_screen_results_run_security"),
        sa.CheckConstraint(
            "outcome IN ('MATCH','NO_MATCH','INSUFFICIENT_DATA')",
            name="ck_screen_results_outcome",
        ),
        _quality_check("screen_results"),
    )
    op.create_index("ix_screen_results_run", "screen_results", ["screen_run_id"])


def downgrade() -> None:
    op.drop_index("ix_screen_results_run", table_name="screen_results")
    op.drop_table("screen_results")
    op.drop_index("ix_screen_runs_definition", table_name="screen_runs")
    op.drop_table("screen_runs")
    op.drop_table("screen_definitions")
