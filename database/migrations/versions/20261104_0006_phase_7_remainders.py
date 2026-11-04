"""phase_7_remainders

Revision ID: 20261104_0006
Revises: 20261104_0005
Create Date: 2026-11-04

Phase 7 remainders: cash-flow + changes-in-equity faces and the
structured auditor-opinion module.

- financial_statements.statement_scope (nullable): disambiguates
  matrix faces (changes-in-equity). Ordinary faces keep NULL; one
  statement per equity component per movement block carries the
  component key. Postgres treats NULLs as distinct in unique
  constraints, so existing rows are unaffected by adding the column
  to the grain constraint and the partial current index.
- auditor_opinions: structured opinion records with source wording
  preserved verbatim, plus explicit absence records for unaudited
  interim statements. Versioned-table discipline (only is_current
  flips allowed) and the shared quality_status vocabulary CHECK,
  mirroring migration 20261104_0003.

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '20261104_0006'
down_revision: Union[str, None] = '20261104_0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

QUALITY_VALUES = (
    "VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "CONFLICTED",
    "MISSING", "REJECTED", "STALE", "PENDING_REVIEW",
)


def upgrade() -> None:
    op.add_column(
        "financial_statements",
        sa.Column("statement_scope", sa.String(100), nullable=True),
    )
    op.drop_constraint(
        "uq_financial_statements_grain", "financial_statements", type_="unique"
    )
    op.create_unique_constraint(
        "uq_financial_statements_grain",
        "financial_statements",
        ["company_id", "period_start", "period_end", "statement_type",
         "version_number", "data_source_id", "statement_scope"],
    )
    op.drop_index(
        "uq_financial_statements_current", table_name="financial_statements",
        postgresql_where=sa.text("is_current"),
    )
    op.create_index(
        "uq_financial_statements_current",
        "financial_statements",
        ["company_id", "period_start", "period_end", "statement_type",
         "data_source_id", "statement_scope"],
        unique=True, postgresql_where=sa.text("is_current"),
    )

    op.create_table(
        "auditor_opinions",
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
        sa.Column("document_id", sa.BigInteger(), nullable=True),
        sa.Column("opinion_scope", sa.String(50), nullable=False),
        sa.Column("opinion_type", sa.String(50), nullable=False),
        sa.Column("firm_name", sa.String(200), nullable=True),
        sa.Column("engagement_partner", sa.String(200), nullable=True),
        sa.Column("opinion_date", sa.Date(), nullable=True),
        sa.Column("udin", sa.String(100), nullable=True),
        sa.Column("opinion_text", sa.Text(), nullable=True),
        sa.Column("going_concern_material_uncertainty", sa.Boolean(), nullable=True),
        sa.Column("going_concern_note", sa.Text(), nullable=True),
        sa.Column("absence_note", sa.Text(), nullable=True),
        sa.Column("opinion_page", sa.BigInteger(), nullable=True),
        sa.Column("signature_page", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_id"], ["financial_documents.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "company_id", "document_id", "opinion_scope", "version_number",
            name="uq_auditor_opinions_grain",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_auditor_opinions_company", "auditor_opinions", ["company_id"]
    )
    op.create_index(
        "uq_auditor_opinions_current",
        "auditor_opinions",
        ["company_id", "document_id", "opinion_scope"],
        unique=True, postgresql_where=sa.text("is_current"),
    )
    values = ", ".join(f"'{v}'" for v in QUALITY_VALUES)
    op.create_check_constraint(
        "ck_auditor_opinions_quality_status", "auditor_opinions",
        f"quality_status IN ({values})",
    )
    op.execute(
        "CREATE TRIGGER trg_auditor_opinions_versioned "
        "BEFORE UPDATE OR DELETE ON auditor_opinions "
        "FOR EACH ROW EXECUTE FUNCTION psx_allow_only_current_flag();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_auditor_opinions_versioned ON auditor_opinions;")
    op.drop_constraint(
        "ck_auditor_opinions_quality_status", "auditor_opinions", type_="check"
    )
    op.drop_index("uq_auditor_opinions_current", table_name="auditor_opinions",
                  postgresql_where=sa.text("is_current"))
    op.drop_index("idx_auditor_opinions_company", table_name="auditor_opinions")
    op.drop_table("auditor_opinions")

    op.drop_index(
        "uq_financial_statements_current", table_name="financial_statements",
        postgresql_where=sa.text("is_current"),
    )
    op.create_index(
        "uq_financial_statements_current",
        "financial_statements",
        ["company_id", "period_start", "period_end", "statement_type", "data_source_id"],
        unique=True, postgresql_where=sa.text("is_current"),
    )
    op.drop_constraint(
        "uq_financial_statements_grain", "financial_statements", type_="unique"
    )
    op.create_unique_constraint(
        "uq_financial_statements_grain",
        "financial_statements",
        ["company_id", "period_start", "period_end", "statement_type",
         "version_number", "data_source_id"],
    )
    op.drop_column("financial_statements", "statement_scope")
