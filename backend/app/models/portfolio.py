"""Phase 16 portfolio construction and optimization engine models.

Five tables. Design rules from the Phase 16 brief:

- SIMULATED ONLY. Every portfolio here is a hypothetical allocation
  on 2026-11-03 closing prices with a clearly labelled hypothetical
  capital (PKR 1,000,000). No portfolio is a real holding, no
  capital is real, and no execution path exists anywhere in this
  project: there is no broker, order, or execution concept in the
  model, the services, or the API, and a test in this phase scans
  the codebase to prove it.
- Eligibility is validated before any units or value are assigned:
  a ticker must exist in the central universe AND have a valid
  (non-null, positive) quote on the price date. NOT_IN_UNIVERSE
  (no security row) and IN_UNIVERSE_NO_QUOTE (security row, no
  price row) are rejected separately, and a zero or negative price
  is INVALID_QUOTE — never a zero-price position.
- Equal-weight and rule-based baselines are constructed. Mean-
  variance is NOT constructed: it requires validated expected
  returns and a covariance matrix, and neither exists (Phase 13
  computed 0 forecasts — all 120 assessments insufficient_inputs;
  the price series has 1 observation, hence 0 return observations).
  Mean-variance appears only as a NOT_CALCULABLE comparison row
  with its reasons, never as numbers.
- Expected returns, historical returns, and forecasts are shown
  SEPARATELY in every portfolio's assumptions, and each is absent
  with its reason: expected returns null (no validated source),
  historical returns null (1 price date, 0 returns), forecasts
  abstained (Phase 13). They are never mixed into a single
  invented return figure.
- Whole shares only: units = floor(target value / price), so the
  residual cash absorbs rounding and weights + cash reconcile to
  capital EXACTLY (Decimal). Target weights are recorded alongside
  actual (post-rounding) weights so the rounding is visible.
- Screening (Phase 15) and eligibility are distinct gates. HBL has
  a valid quote and is ELIGIBLE, but it is excluded from the
  rule-based portfolios because its Phase 15 screening is
  SCREEN_NOT_RUNNABLE (no statements). NML has a valid quote but
  is excluded because its screening is SCREEN_FAIL. Exclusions are
  stored as rows with reasons, never silently dropped.
- No look-ahead: only the 2026-11-03 price date and Phase 15
  decisions dated 2026-11-04 (which use publications on or before
  that date) feed construction. Nothing published after the
  decision date is used.
- Phase 3 ``portfolios`` / ``portfolio_holdings`` are intentionally
  NOT reused or altered (precedent from Phases 11-15): the Phase 3
  tables model user-owned portfolios with a user_id and no
  method, constraints, assumptions, sector allocation, exclusion,
  or comparison semantics, and their meaning (a user's portfolio)
  does not match this phase's simulated, method-labelled
  constructions. They stay at 0 rows.

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
from app.models.base import CreatedMixin, IdMixin, ProvenanceMixin, VersionMixin


class SimulatedPortfolio(IdMixin, CreatedMixin, ProvenanceMixin, VersionMixin, Base):
    """One simulated portfolio construction.

    ``method`` is equal_weight_baseline, rule_based_screen_pass, or
    mean_variance. A mean_variance row has status NOT_CALCULABLE
    and no holdings: it exists so the gating is auditable, not so
    a number can be read off it. ``capital`` is hypothetical
    simulation capital, never real funds. ``horizon`` is
    not_specified for every portfolio in this run: no horizon
    return claim is made. ``constraints`` holds the input schema
    (capital, currency, cash floor, weight caps, sector cap,
    eligible tickers, price date, profile). ``assumptions`` holds
    expected_returns / historical_returns / forecasts separately,
    each null with its reason in this run. ``binding_constraints``
    names the constraints that actually bound the construction.
    """

    __tablename__ = "simulated_portfolios"
    __table_args__ = (UniqueConstraint("name", name="uq_simulated_portfolios_name"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    method: Mapped[str] = mapped_column(String(50), nullable=False)
    capital: Mapped[object] = mapped_column(Numeric(24, 4), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    horizon: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_profile: Mapped[str] = mapped_column(String(30), nullable=False)
    price_date: Mapped[object] = mapped_column(Date, nullable=False)
    generated_date: Mapped[object] = mapped_column(Date, nullable=False)
    constraints: Mapped[dict] = mapped_column(JSON, nullable=False)
    assumptions: Mapped[dict] = mapped_column(JSON, nullable=False)
    binding_constraints: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    not_calculable_reasons: Mapped[dict] = mapped_column(JSON, nullable=False)


class SimulatedPortfolioHolding(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One position inside a simulated portfolio.

    ``target_weight`` is the method's intended weight before
    whole-share rounding; ``actual_weight`` is value / capital
    after rounding. ``units`` are whole shares (floor of target
    value / price); the residual cash is the portfolio-level
    remainder, so holdings + cash reconcile to capital exactly.
    ``eligibility_status`` is ELIGIBLE for every stored holding;
    rejected tickers never reach this table (see exclusions).
    """

    __tablename__ = "simulated_portfolio_holdings"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id",
            "security_id",
            name="uq_simulated_holdings_portfolio_security",
        ),
        Index("ix_simulated_holdings_portfolio", "portfolio_id"),
    )

    portfolio_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("simulated_portfolios.id", ondelete="CASCADE"), nullable=False
    )
    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="SET NULL"), nullable=True
    )
    company_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_weight: Mapped[object] = mapped_column(Numeric(10, 6), nullable=False)
    actual_weight: Mapped[object] = mapped_column(Numeric(10, 6), nullable=False)
    units: Mapped[object] = mapped_column(Numeric(24, 4), nullable=False)
    value: Mapped[object] = mapped_column(Numeric(24, 4), nullable=False)
    price: Mapped[object] = mapped_column(Numeric(20, 4), nullable=False)
    price_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("market_prices.id", ondelete="SET NULL"), nullable=True
    )
    price_date: Mapped[object] = mapped_column(Date, nullable=False)
    eligibility_status: Mapped[str] = mapped_column(String(30), nullable=False)


class PortfolioExclusion(IdMixin, CreatedMixin, Base):
    """One ticker excluded from one simulated portfolio, with reason.

    ``reason_code`` is NOT_IN_UNIVERSE, IN_UNIVERSE_NO_QUOTE,
    INVALID_QUOTE, SCREEN_FAIL, or SCREEN_NOT_RUNNABLE.
    ``reason_detail`` carries the evidence (e.g. the Phase 15 gate
    reasons for a screening exclusion). Exclusions are stored so
    the construction is auditable: a reader can see exactly why a
    name is absent instead of guessing.
    """

    __tablename__ = "portfolio_exclusions"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "ticker", name="uq_portfolio_exclusions_portfolio_ticker"),
        Index("ix_portfolio_exclusions_portfolio", "portfolio_id"),
    )

    portfolio_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("simulated_portfolios.id", ondelete="CASCADE"), nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_detail: Mapped[str] = mapped_column(Text, nullable=False)


class PortfolioSectorAllocation(IdMixin, CreatedMixin, Base):
    """One sector's weight inside one simulated portfolio.

    ``invested_weight`` is the sector's share of invested value;
    ``capital_weight`` is its share of total capital (cash excluded
    from the numerator, included in the denominator). Both are
    reported so the cash treatment is unambiguous.
    """

    __tablename__ = "portfolio_sector_allocations"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "sector", name="uq_portfolio_sectors_portfolio_sector"),
        Index("ix_portfolio_sectors_portfolio", "portfolio_id"),
    )

    portfolio_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("simulated_portfolios.id", ondelete="CASCADE"), nullable=False
    )
    sector: Mapped[str] = mapped_column(String(200), nullable=False)
    invested_value: Mapped[object] = mapped_column(Numeric(24, 4), nullable=False)
    invested_weight: Mapped[object] = mapped_column(Numeric(10, 6), nullable=False)
    capital_weight: Mapped[object] = mapped_column(Numeric(10, 6), nullable=False)


class PortfolioComparison(IdMixin, CreatedMixin, Base):
    """One method compared against the equal-weight baseline.

    ``subject_name`` names the portfolio or method compared;
    ``baseline_name`` names the equal-weight baseline portfolio.
    For mean_variance the status is NOT_CALCULABLE, metrics is
    empty, and reasons carries the gating evidence (no validated
    expected returns, no covariance). For constructed portfolios
    the metrics compare holdings count, cash, largest single-name
    weight, and largest sector weight against the baseline.
    """

    __tablename__ = "portfolio_comparisons"
    __table_args__ = (
        UniqueConstraint(
            "subject_name", "method_compared", name="uq_portfolio_comparisons_subject_method"
        ),
    )

    subject_name: Mapped[str] = mapped_column(String(100), nullable=False)
    baseline_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    method_compared: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    reasons: Mapped[dict] = mapped_column(JSON, nullable=False)
