"""phase_10_macro

Revision ID: 20261104_0007
Revises: 20261104_0006
Create Date: 2026-11-04

Phase 10 (macro/sector intelligence) tables. Macro observations themselves
reuse the Phase 3 economic_indicators table (definition + observation in
one table, versioned grain indicator_code + observation_date +
version_number, only is_current flips allowed). This migration adds only
the three tables Phase 10 needs that do not already exist:

- company_macro_exposures: company -> macro exposure register. Every row
  must cite issuer-disclosure evidence (a Phase 7 statement line key);
  sector membership alone is never stored as an exposure. Versioned
  (only is_current flips allowed), same discipline as economic_indicators.
- macro_regimes: explainable concurrent regime labels (tightening,
  disinflation, external pressure, slowdown, fiscal consolidation) with
  the evidence basis stored as JSON. Immutable: a revised assessment is
  a new row, never an edit.
- macro_events: dated policy/release event calendar (MPC meetings, CPI
  releases, minutes). Immutable: a corrected event is a new row.

Quality vocabulary CHECK mirrors migration 20261104_0003. No CSVs or
PDFs are involved; no credentials are stored anywhere.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '20261104_0007'
down_revision: Union[str, None] = '20261104_0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

QUALITY_VALUES = (
    "VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "CONFLICTED",
    "MISSING", "REJECTED", "STALE", "PENDING_REVIEW",
)


def _quality_check(table: str) -> str:
    values = ", ".join(f"'{v}'" for v in QUALITY_VALUES)
    return f"quality_status IN ({values})"


def upgrade() -> None:
    op.create_table(
        "company_macro_exposures",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("data_source_id", sa.BigInteger(), nullable=True),
        sa.Column("source_key", sa.String(100), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_status", sa.String(30), nullable=False, server_default="UNVERIFIED"),
        sa.Column("version_number", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("supersedes_id", sa.BigInteger(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("exposure_key", sa.String(100), nullable=False),
        sa.Column("exposure_name", sa.String(300), nullable=False),
        sa.Column("direction", sa.String(50), nullable=False),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("evidence_ref", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "company_id", "exposure_key", "version_number",
            name="uq_company_macro_exposures_grain",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_company_macro_exposures_company", "company_macro_exposures", ["company_id"]
    )
    op.create_index(
        "uq_company_macro_exposures_current",
        "company_macro_exposures",
        ["company_id", "exposure_key"],
        unique=True, postgresql_where=sa.text("is_current"),
    )
    op.create_check_constraint(
        "ck_company_macro_exposures_quality_status",
        "company_macro_exposures",
        _quality_check("company_macro_exposures"),
    )
    op.execute(
        "CREATE TRIGGER trg_company_macro_exposures_versioned "
        "BEFORE UPDATE OR DELETE ON company_macro_exposures "
        "FOR EACH ROW EXECUTE FUNCTION psx_allow_only_current_flag();"
    )

    op.create_table(
        "macro_regimes",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("data_source_id", sa.BigInteger(), nullable=True),
        sa.Column("source_key", sa.String(100), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_status", sa.String(30), nullable=False, server_default="UNVERIFIED"),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("regime_label", sa.String(100), nullable=False),
        sa.Column("method_version", sa.String(50), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "observation_date", "regime_label", "method_version",
            name="uq_macro_regimes_grain",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_macro_regimes_date", "macro_regimes", ["observation_date"])
    op.create_check_constraint(
        "ck_macro_regimes_quality_status", "macro_regimes",
        _quality_check("macro_regimes"),
    )
    op.execute(
        "CREATE TRIGGER trg_macro_regimes_immutable "
        "BEFORE UPDATE OR DELETE ON macro_regimes "
        "FOR EACH ROW EXECUTE FUNCTION psx_prevent_mutation();"
    )

    op.create_table(
        "macro_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("data_source_id", sa.BigInteger(), nullable=True),
        sa.Column("source_key", sa.String(100), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_status", sa.String(30), nullable=False, server_default="UNVERIFIED"),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "event_date", "event_type", "title",
            name="uq_macro_events_grain",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_macro_events_date", "macro_events", ["event_date"])
    op.create_check_constraint(
        "ck_macro_events_quality_status", "macro_events",
        _quality_check("macro_events"),
    )
    op.execute(
        "CREATE TRIGGER trg_macro_events_immutable "
        "BEFORE UPDATE OR DELETE ON macro_events "
        "FOR EACH ROW EXECUTE FUNCTION psx_prevent_mutation();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_macro_events_immutable ON macro_events;")
    op.drop_constraint("ck_macro_events_quality_status", "macro_events", type_="check")
    op.drop_index("idx_macro_events_date", table_name="macro_events")
    op.drop_table("macro_events")

    op.execute("DROP TRIGGER IF EXISTS trg_macro_regimes_immutable ON macro_regimes;")
    op.drop_constraint("ck_macro_regimes_quality_status", "macro_regimes", type_="check")
    op.drop_index("idx_macro_regimes_date", table_name="macro_regimes")
    op.drop_table("macro_regimes")

    op.execute("DROP TRIGGER IF EXISTS trg_company_macro_exposures_versioned ON company_macro_exposures;")
    op.drop_constraint("ck_company_macro_exposures_quality_status", "company_macro_exposures", type_="check")
    op.drop_index("uq_company_macro_exposures_current", table_name="company_macro_exposures",
                  postgresql_where=sa.text("is_current"))
    op.drop_index("idx_company_macro_exposures_company", table_name="company_macro_exposures")
    op.drop_table("company_macro_exposures")
