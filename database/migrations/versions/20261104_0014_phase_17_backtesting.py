"""phase_17_backtesting

Revision ID: 20261104_0014
Revises: 20261104_0013
Create Date: 2026-11-04

Phase 17 (backtesting, paper trading and strategy evaluation)
tables: backtest_strategies (strategy/version registry),
backtest_runs (one run per strategy per window; production runs
are NOT_RUNNABLE on a single price observation), backtest_metrics
(one metric row per run; NULL value unless computed),
paper_orders (simulator lifecycle; ZERO production rows),
paper_ledger_entries (opening positions, opening cash, valuation
snapshots re-derived from Phase 16 simulated portfolios),
backtest_bias_reports (one row per bias-audit check).

Precedent note (Phases 11-16): Phase 17 stores its own tables
rather than retrofitting Phase 3 tables. No Phase 3 backtest,
paper, or strategy table exists, and the Phase 3 ``portfolios`` /
``portfolio_holdings`` tables model user-owned portfolios, not
method-labelled simulations. They stay at 0 rows. No CSVs or PDFs
are involved; no credentials are stored anywhere. Quality
vocabulary CHECK mirrors migration 20261104_0003.

No execution concept exists in these tables: paper_orders records
a SIMULATOR lifecycle against observed prices only. There is no
broker, order-execution, or execution column, table, or
relationship anywhere in this project.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0014"
down_revision: str | None = "20261104_0013"
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
        "backtest_strategies",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rule_reference", sa.String(100), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.UniqueConstraint("name", name="uq_backtest_strategies_name"),
    )
    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        *_provenance_columns(),
        sa.Column(
            "strategy_id",
            sa.BigInteger(),
            sa.ForeignKey("backtest_strategies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("not_runnable_reasons", sa.JSON(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("price_observations", sa.BigInteger(), nullable=False),
        sa.Column("return_observations", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint(
            "strategy_id",
            "start_date",
            "end_date",
            name="uq_backtest_runs_strategy_window",
        ),
        sa.Index("ix_backtest_runs_strategy", "strategy_id"),
        sa.CheckConstraint(
            _quality_check("backtest_runs"), name="ck_backtest_runs_quality"
        ),
    )
    op.create_table(
        "backtest_metrics",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        *_provenance_columns(),
        sa.Column(
            "run_id",
            sa.BigInteger(),
            sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("value", sa.Numeric(24, 6), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.UniqueConstraint("run_id", "metric", name="uq_backtest_metrics_run_metric"),
        sa.Index("ix_backtest_metrics_run", "run_id"),
        sa.CheckConstraint(
            _quality_check("backtest_metrics"), name="ck_backtest_metrics_quality"
        ),
    )
    op.create_table(
        "paper_orders",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("portfolio_name", sa.String(100), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("units", sa.Numeric(24, 4), nullable=False),
        sa.Column("reference_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("status_reason", sa.Text(), nullable=False),
        sa.Column("proposed_date", sa.Date(), nullable=False),
        sa.Column("fill_date", sa.Date(), nullable=True),
        sa.Column("fill_price", sa.Numeric(20, 4), nullable=True),
        sa.Index("ix_paper_orders_portfolio", "portfolio_name"),
    )
    op.create_table(
        "paper_ledger_entries",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("portfolio_name", sa.String(100), nullable=False),
        sa.Column("entry_type", sa.String(30), nullable=False),
        sa.Column("ticker_key", sa.String(20), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=True),
        sa.Column("units", sa.Numeric(24, 4), nullable=True),
        sa.Column("price", sa.Numeric(20, 4), nullable=True),
        sa.Column("value", sa.Numeric(24, 4), nullable=False),
        sa.Column("cash_after", sa.Numeric(24, 4), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("source", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "portfolio_name",
            "entry_type",
            "ticker_key",
            name="uq_paper_ledger_portfolio_type_key",
        ),
        sa.Index("ix_paper_ledger_portfolio", "portfolio_name"),
    )
    op.create_table(
        "backtest_bias_reports",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("check_name", sa.String(50), nullable=False),
        sa.Column("result", sa.String(30), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.UniqueConstraint("check_name", name="uq_backtest_bias_check"),
    )


def downgrade() -> None:
    op.drop_table("backtest_bias_reports")
    op.drop_table("paper_ledger_entries")
    op.drop_table("paper_orders")
    op.drop_table("backtest_metrics")
    op.drop_table("backtest_runs")
    op.drop_table("backtest_strategies")
