"""Phase 17 backtesting, paper trading and strategy evaluation models.

Six tables. Design rules from the Phase 17 brief:

- SIMULATION ONLY. Nothing here is a real holding, a real order, or
  real performance. Every ledger entry and every metric row is
  labelled simulation, and no broker, order-execution, or execution
  concept exists anywhere in this project: ``paper_orders`` records
  a SIMULATOR lifecycle (proposed / accepted / filled /
  partially_filled / cancelled / rejected) against observed prices
  only, and a test in this phase scans the codebase to prove no
  execution path exists.
- No look-ahead: a backtest window may only use prices and
  publications dated on or before the simulated decision date.
  With exactly one price date (2026-11-03) the production windows
  contain zero return intervals, so every production backtest run
  is NOT_RUNNABLE and every return-based metric is
  insufficient_inputs (or not_applicable for benchmark-relative
  return, where no benchmark series exists at all). Nothing is
  zero-filled, nothing is estimated, and a single-day snapshot is
  never presented as a backtest result.
- The paper ledger IS computable in production: it re-derives the
  Phase 16 simulated portfolios' opening positions, opening cash
  (capital minus holdings, recomputed, never copied blindly), and
  a valuation snapshot dated 2026-11-03. No paper order is
  generated in production: Phase 15 user-facing values are all
  WITHHELD, so no decision-driven order may be created, and no
  price exists after 2026-11-03 for a fill. The order lifecycle
  engine exists, is fixture-tested, and holds zero production rows.
- Bias is reported, not hidden: the bias table records one row per
  check with its evidence, including disclosed biases (3/470
  statement coverage, 26 tickers without prices, dividend actions
  without dates, single price date, stale NML statement).
- Phase 3 tables are not reused: no Phase 3 backtest, paper, or
  strategy table exists, and the Phase 3 ``portfolios`` /
  ``portfolio_holdings`` tables model user-owned portfolios, not
  method-labelled simulations. They stay at 0 rows.

Quality vocabulary mirrors migration 20261104_0003.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, IdMixin, ProvenanceMixin


class BacktestStrategy(IdMixin, CreatedMixin, Base):
    """One registered strategy version.

    ``rule_reference`` names the rule set the strategy implements
    (e.g. Phase 15 decision-rules-v1, a Phase 16 construction
    profile, or buy-and-hold). ``parameters`` holds the strategy's
    declared inputs (universe, rebalance rule, cost assumptions by
    reference). Registration is not a result: a registered strategy
    with no runnable window still has no backtest result.
    """

    __tablename__ = "backtest_strategies"
    __table_args__ = (UniqueConstraint("name", name="uq_backtest_strategies_name"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rule_reference: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class BacktestRun(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One backtest run of one strategy over one window.

    ``status`` is NOT_RUNNABLE when the window contains fewer than
    two price observations (zero return intervals), which is the
    case for every production run: the only price date is
    2026-11-03. ``assumptions`` records the execution assumptions
    (fees, taxes, slippage in basis points, risk-free convention)
    even for NOT_RUNNABLE runs, so the assumption set is auditable.
    ``price_observations`` and ``return_observations`` are counted
    from the database, never assumed.
    """

    __tablename__ = "backtest_runs"
    __table_args__ = (
        UniqueConstraint(
            "strategy_id",
            "start_date",
            "end_date",
            name="uq_backtest_runs_strategy_window",
        ),
        Index("ix_backtest_runs_strategy", "strategy_id"),
    )

    strategy_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("backtest_strategies.id", ondelete="CASCADE"), nullable=False
    )
    start_date: Mapped[object] = mapped_column(Date, nullable=False)
    end_date: Mapped[object] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    not_runnable_reasons: Mapped[dict] = mapped_column(JSON, nullable=False)
    assumptions: Mapped[dict] = mapped_column(JSON, nullable=False)
    price_observations: Mapped[int] = mapped_column(BigInteger, nullable=False)
    return_observations: Mapped[int] = mapped_column(BigInteger, nullable=False)


class BacktestMetric(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One performance metric for one backtest run.

    ``value`` is NULL unless ``status`` is computed. Production
    rows are all insufficient_inputs (too few observations) except
    benchmark_relative_return, which is not_applicable (no
    benchmark series is loaded at all). ``evidence`` records the
    observation counts and the minimum the metric requires, so the
    gating is auditable per metric.
    """

    __tablename__ = "backtest_metrics"
    __table_args__ = (
        UniqueConstraint("run_id", "metric", name="uq_backtest_metrics_run_metric"),
        Index("ix_backtest_metrics_run", "run_id"),
    )

    run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False
    )
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[object | None] = mapped_column(Numeric(24, 6), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False)


class PaperOrder(IdMixin, CreatedMixin, Base):
    """One simulated order in the paper-trading lifecycle.

    Statuses: proposed, accepted, filled, partially_filled,
    cancelled, rejected. A fill requires an observed price on or
    after the proposal date (the next eligible price rule); a
    proposal with no later observed price can never fill. This
    table holds ZERO production rows: Phase 15 user-facing values
    are all WITHHELD, so no decision-driven order may be created,
    and no price exists after 2026-11-03. The lifecycle exists as
    engine + fixture tests, not as production orders.
    """

    __tablename__ = "paper_orders"
    __table_args__ = (Index("ix_paper_orders_portfolio", "portfolio_name"),)

    portfolio_name: Mapped[str] = mapped_column(String(100), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    units: Mapped[object] = mapped_column(Numeric(24, 4), nullable=False)
    reference_price: Mapped[object | None] = mapped_column(Numeric(20, 4), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    status_reason: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_date: Mapped[object] = mapped_column(Date, nullable=False)
    fill_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    fill_price: Mapped[object | None] = mapped_column(Numeric(20, 4), nullable=True)


class PaperLedgerEntry(IdMixin, CreatedMixin, Base):
    """One entry in a simulated paper portfolio ledger.

    ``entry_type`` is opening_position, opening_cash, or
    valuation_snapshot. ``ticker_key`` is the ticker, or __CASH__
    for cash entries and __TOTAL__ for valuation snapshots, so the
    (portfolio, type, key) grain is unique and the runner is
    idempotent. ``source`` records the Phase 16 holding or
    portfolio the entry was re-derived from; values are recomputed
    (units x price), never copied without recomputation. Every
    entry is dated 2026-11-03, the only price date, and is a
    SIMULATION, never a real position.
    """

    __tablename__ = "paper_ledger_entries"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_name",
            "entry_type",
            "ticker_key",
            name="uq_paper_ledger_portfolio_type_key",
        ),
        Index("ix_paper_ledger_portfolio", "portfolio_name"),
    )

    portfolio_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False)
    ticker_key: Mapped[str] = mapped_column(String(20), nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(20), nullable=True)
    units: Mapped[object | None] = mapped_column(Numeric(24, 4), nullable=True)
    price: Mapped[object | None] = mapped_column(Numeric(20, 4), nullable=True)
    value: Mapped[object] = mapped_column(Numeric(24, 4), nullable=False)
    cash_after: Mapped[object] = mapped_column(Numeric(24, 4), nullable=False)
    entry_date: Mapped[object] = mapped_column(Date, nullable=False)
    source: Mapped[dict] = mapped_column(JSON, nullable=False)


class BacktestBiasReport(IdMixin, CreatedMixin, Base):
    """One bias-audit check for the Phase 17 backtest set.

    ``result`` is no_bias_detected, bias_disclosed, or
    not_applicable. A bias_disclosed row is a finding, not a phase
    failure: the bias is documented with its evidence instead of
    being silently baked into a result. ``evidence`` carries the
    counts, names, and dates the check examined.
    """

    __tablename__ = "backtest_bias_reports"
    __table_args__ = (UniqueConstraint("check_name", name="uq_backtest_bias_check"),)

    check_name: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False)
