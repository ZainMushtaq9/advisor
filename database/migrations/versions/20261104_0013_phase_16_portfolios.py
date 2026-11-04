"""phase_16_portfolios

Revision ID: 20261104_0013
Revises: 20261104_0012
Create Date: 2026-11-04

Phase 16 (portfolio construction and optimization engine) tables:
simulated_portfolios (method-labelled hypothetical constructions),
simulated_portfolio_holdings (whole-share positions with target
and actual weights), portfolio_exclusions (rejected tickers with
reasons), portfolio_sector_allocations (sector weights, two
denominators), portfolio_comparisons (methods vs the equal-weight
baseline, including the NOT_CALCULABLE mean-variance row).

Precedent note (Phases 11-15): Phase 16 stores its own tables
rather than retrofitting the Phase 3 ``portfolios`` /
``portfolio_holdings`` tables: the Phase 3 tables model
user-owned portfolios with a user_id and no method, constraints,
assumptions, sector allocation, exclusion, or comparison
semantics, and their meaning (a user's portfolio) does not match
this phase's simulated, method-labelled constructions. No CSVs or
PDFs are involved; no credentials are stored anywhere. Quality
vocabulary CHECK mirrors migration 20261104_0003.

No execution concept exists in these tables: there is no broker,
order, or execution column, table, or relationship anywhere in
this project.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0013"
down_revision: str | None = "20261104_0012"
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
        sa.Column("quality_status", sa.String(30), nullable=False, server_default="UNVERIFIED"),
    ]


def _version_columns() -> list:
    return [
        sa.Column("version_number", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("supersedes_id", sa.BigInteger(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
    ]


def upgrade() -> None:
    op.create_table(
        "simulated_portfolios",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        *_provenance_columns(),
        *_version_columns(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("method", sa.String(50), nullable=False),
        sa.Column("capital", sa.Numeric(24, 4), nullable=False),
        sa.Column("base_currency", sa.String(10), nullable=False),
        sa.Column("horizon", sa.String(50), nullable=False),
        sa.Column("risk_profile", sa.String(30), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("generated_date", sa.Date(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("binding_constraints", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("not_calculable_reasons", sa.JSON(), nullable=False),
        sa.UniqueConstraint("name", name="uq_simulated_portfolios_name"),
        sa.CheckConstraint(_quality_check("simulated_portfolios"), name="ck_simulated_portfolios_quality"),
    )
    op.create_table(
        "simulated_portfolio_holdings",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        *_provenance_columns(),
        sa.Column("portfolio_id", sa.BigInteger(), sa.ForeignKey("simulated_portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("security_id", sa.BigInteger(), sa.ForeignKey("securities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_id", sa.BigInteger(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("sector", sa.String(200), nullable=True),
        sa.Column("target_weight", sa.Numeric(10, 6), nullable=False),
        sa.Column("actual_weight", sa.Numeric(10, 6), nullable=False),
        sa.Column("units", sa.Numeric(24, 4), nullable=False),
        sa.Column("value", sa.Numeric(24, 4), nullable=False),
        sa.Column("price", sa.Numeric(20, 4), nullable=False),
        sa.Column("price_id", sa.BigInteger(), sa.ForeignKey("market_prices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("eligibility_status", sa.String(30), nullable=False),
        sa.UniqueConstraint("portfolio_id", "security_id", name="uq_simulated_holdings_portfolio_security"),
        sa.Index("ix_simulated_holdings_portfolio", "portfolio_id"),
        sa.CheckConstraint(_quality_check("simulated_portfolio_holdings"), name="ck_simulated_holdings_quality"),
    )
    op.create_table(
        "portfolio_exclusions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("portfolio_id", sa.BigInteger(), sa.ForeignKey("simulated_portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("reason_code", sa.String(50), nullable=False),
        sa.Column("reason_detail", sa.Text(), nullable=False),
        sa.UniqueConstraint("portfolio_id", "ticker", name="uq_portfolio_exclusions_portfolio_ticker"),
        sa.Index("ix_portfolio_exclusions_portfolio", "portfolio_id"),
    )
    op.create_table(
        "portfolio_sector_allocations",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("portfolio_id", sa.BigInteger(), sa.ForeignKey("simulated_portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sector", sa.String(200), nullable=False),
        sa.Column("invested_value", sa.Numeric(24, 4), nullable=False),
        sa.Column("invested_weight", sa.Numeric(10, 6), nullable=False),
        sa.Column("capital_weight", sa.Numeric(10, 6), nullable=False),
        sa.UniqueConstraint("portfolio_id", "sector", name="uq_portfolio_sectors_portfolio_sector"),
        sa.Index("ix_portfolio_sectors_portfolio", "portfolio_id"),
    )
    op.create_table(
        "portfolio_comparisons",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("subject_name", sa.String(100), nullable=False),
        sa.Column("baseline_name", sa.String(100), nullable=True),
        sa.Column("method_compared", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.UniqueConstraint("subject_name", "method_compared", name="uq_portfolio_comparisons_subject_method"),
    )


def downgrade() -> None:
    op.drop_table("portfolio_comparisons")
    op.drop_table("portfolio_sector_allocations")
    op.drop_table("portfolio_exclusions")
    op.drop_table("simulated_portfolio_holdings")
    op.drop_table("simulated_portfolios")
