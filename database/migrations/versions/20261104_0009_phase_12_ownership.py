"""phase_12_ownership

Revision ID: 20261104_0009
Revises: 20261104_0008
Create Date: 2026-11-04

Phase 12 (ownership, corporate actions, market breadth and flow
intelligence) tables. No CSVs or PDFs are involved; no credentials
are stored anywhere. Quality vocabulary CHECK mirrors migration
20261104_0003.

The investor_flows table is intentionally created empty: Phase 12
writes no flow rows (no verified published flow series loaded; flows
are never derived from price/volume).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '20261104_0009'
down_revision: Union[str, None] = '20261104_0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

QUALITY_VALUES = (
    "VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "CONFLICTED",
    "MISSING", "REJECTED", "STALE", "PENDING_REVIEW",
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
            "quality_status", sa.String(30), nullable=False,
            server_default="UNVERIFIED",
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "ownership_holdings",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *_provenance_columns(),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("holder_category", sa.String(100), nullable=False),
        sa.Column("holder_name", sa.String(300), nullable=True),
        sa.Column("folio", sa.String(100), nullable=True),
        sa.Column("reporting_date", sa.Date(), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("publication_date_note", sa.Text(), nullable=True),
        sa.Column("shareholders_count", sa.BigInteger(), nullable=True),
        sa.Column("shares_held", sa.BigInteger(), nullable=False),
        sa.Column("percentage", sa.Numeric(10, 4), nullable=True),
        sa.Column("is_total", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_evidence", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        # Folio is part of the grain: the same holder name appears under
        # two folios (MEGA CONGLOMERATE, MUHAMMAD KAMRAN KAMAL).
        sa.UniqueConstraint(
            "company_id", "holder_category", "holder_name", "folio", "reporting_date",
            name="uq_ownership_holdings_grain",
        ),
        sa.CheckConstraint(_quality_check("ownership_holdings"), name="ck_ownership_holdings_quality"),
    )
    op.create_index("idx_ownership_holdings_company", "ownership_holdings", ["company_id"])
    op.create_index("idx_ownership_holdings_date", "ownership_holdings", ["reporting_date"])

    # NOTE: the Phase 3 "corporate_actions" table is NOT reused here: it
    # requires a NOT NULL event_date and carries an adjustment_factor,
    # while Phase 12's evidenced actions have no published event date
    # at all. This registry table records the evidence; the Phase 3
    # table stays empty until an action gains a known ex-date.
    op.create_table(
        "corporate_action_records",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *_provenance_columns(),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("fiscal_year_label", sa.String(100), nullable=False),
        sa.Column("amount_per_share", sa.Numeric(20, 4), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="PKR"),
        sa.Column("total_amount", sa.Numeric(24, 4), nullable=True),
        sa.Column("total_amount_note", sa.Text(), nullable=True),
        sa.Column("announced_date", sa.Date(), nullable=True),
        sa.Column("ex_date", sa.Date(), nullable=True),
        sa.Column("record_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("date_evidence", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("source_evidence", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "company_id", "action_type", "fiscal_year_label", "amount_per_share",
            name="uq_corporate_action_records_grain",
        ),
        sa.CheckConstraint(_quality_check("corporate_action_records"), name="ck_corporate_action_records_quality"),
    )
    op.create_index("idx_corporate_action_records_company", "corporate_action_records", ["company_id"])
    op.create_index("idx_corporate_action_records_type", "corporate_action_records", ["action_type"])

    op.create_table(
        "market_breadth",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *_provenance_columns(),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("scope", sa.String(200), nullable=False),
        sa.Column("metric_key", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Numeric(24, 6), nullable=True),
        sa.Column("numerator", sa.BigInteger(), nullable=True),
        sa.Column("denominator", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("coverage_note", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "trading_date", "scope", "metric_key", name="uq_market_breadth_grain"
        ),
        sa.CheckConstraint(_quality_check("market_breadth"), name="ck_market_breadth_quality"),
    )
    op.create_index("idx_market_breadth_date", "market_breadth", ["trading_date"])

    op.create_table(
        "liquidity_observations",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *_provenance_columns(),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("scope_key", sa.String(100), nullable=False),
        sa.Column("security_id", sa.BigInteger(), nullable=True),
        sa.Column("metric_key", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Numeric(24, 6), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("coverage_note", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["security_id"], ["securities.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "trading_date", "scope_key", "metric_key",
            name="uq_liquidity_observations_grain",
        ),
        sa.CheckConstraint(_quality_check("liquidity_observations"), name="ck_liquidity_observations_quality"),
    )
    op.create_index("idx_liquidity_observations_date", "liquidity_observations", ["trading_date"])

    op.create_table(
        "investor_flows",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *_provenance_columns(),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("flow_category", sa.String(100), nullable=False),
        sa.Column("participant_category", sa.String(100), nullable=False),
        sa.Column("net_flow", sa.Numeric(24, 4), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="PKR"),
        sa.Column("source_evidence", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "observation_date", "flow_category", "participant_category",
            name="uq_investor_flows_grain",
        ),
        sa.CheckConstraint(_quality_check("investor_flows"), name="ck_investor_flows_quality"),
    )
    op.create_index("idx_investor_flows_date", "investor_flows", ["observation_date"])

    op.create_table(
        "adjustment_rules",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("rule_key", sa.String(100), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("formula", sa.Text(), nullable=False),
        sa.Column("requires", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("application_status", sa.String(50), nullable=False, server_default="defined_not_applied"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_key", name="uq_adjustment_rules_key"),
    )


def downgrade() -> None:
    op.drop_table("adjustment_rules")
    op.drop_table("investor_flows")
    op.drop_table("liquidity_observations")
    op.drop_table("market_breadth")
    op.drop_table("corporate_action_records")
    op.drop_table("ownership_holdings")
