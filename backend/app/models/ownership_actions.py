"""Phase 12 ownership, corporate actions, breadth and flow models.

Six tables. Design rules from the Phase 12 brief:

- Every ownership/action record carries dates and a source. Where a
  date is NOT published in the loaded source, the column is NULL and
  the reason is recorded in ``date_evidence`` — a missing date is
  never invented, and a NULL date never silently becomes "today".
- Beneficial ownership is never inferred: only categories and named
  holders printed in the source document are stored.
- Raw prices are never rewritten by an adjustment. Adjustment rules
  are definitions; adjusted values are computed on read from the
  action registry, and no adjusted price series is stored in this
  phase (no ex-date exists for any stored action yet).
- Breadth completeness is visible: every breadth metric carries its
  numerator/denominator (or an explicit insufficient_inputs reason),
  so a partial snapshot can never be mistaken for the whole market.
- Investor flows: the table exists but holds ZERO rows in this run.
  No verified published flow series was loaded, and flows are never
  invented from price/volume alone. Producing no flow claim is the
  brief-compliant outcome; the unblocker is documented in the run
  report.

Quality vocabulary mirrors migration 20261104_0003. New rows carry
their inputs' status, never higher: HUBC ownership comes from a single
issuer document (UNVERIFIED); breadth comes from UNVERIFIED prices.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
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


class OwnershipHolding(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One ownership row: a category total or one named holder.

    ``holder_category`` is the printed category (e.g. INDIVIDUAL_LOCAL,
    ASSOCIATED_COMPANY, DIRECTOR). ``holder_name`` is NULL for category
    totals and set for named key holders. ``shareholders_count`` is
    NULL for named holders (the document gives no per-holder count).
    ``is_total`` marks the dataset totals row (80,377 / 1,297,154,387).
    """

    __tablename__ = "ownership_holdings"
    __table_args__ = (
        # Folio is part of the grain: the same holder name appears under
        # two folios (MEGA CONGLOMERATE, MUHAMMAD KAMRAN KAMAL) and both
        # rows must be stored, never merged.
        UniqueConstraint(
            "company_id",
            "holder_category",
            "holder_name",
            "folio",
            "reporting_date",
            name="uq_ownership_holdings_grain",
        ),
        Index("idx_ownership_holdings_company", "company_id"),
        Index("idx_ownership_holdings_date", "reporting_date"),
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    holder_category: Mapped[str] = mapped_column(String(100), nullable=False)
    holder_name: Mapped[str] = mapped_column(String(300), nullable=True)
    folio: Mapped[str] = mapped_column(String(100), nullable=True)
    reporting_date: Mapped[object] = mapped_column(Date, nullable=False)
    publication_date: Mapped[object] = mapped_column(Date, nullable=True)
    publication_date_note: Mapped[str] = mapped_column(Text, nullable=True)
    shareholders_count: Mapped[int] = mapped_column(BigInteger, nullable=True)
    shares_held: Mapped[int] = mapped_column(BigInteger, nullable=False)
    percentage: Mapped[object] = mapped_column(Numeric(10, 4), nullable=True)
    is_total: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_evidence: Mapped[dict] = mapped_column(JSON, nullable=True)


class CorporateActionRecord(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One corporate action event, as published — the evidence registry.

    The Phase 3 ``corporate_actions`` table is intentionally NOT
    reused: it requires a NOT NULL event_date and carries an
    adjustment_factor for application, while the actions evidenced in
    this run have NO published event/ex/record/payment dates at all.
    Writing them there would force inventing an event date. This
    registry records what was published, with every unpublished date
    NULL and explained in ``date_evidence``. When an action later
    gains a known ex-date, the application layer writes the
    adjustment row to the Phase 3 table (which stays empty until
    then); this registry row remains the evidence of record.

    ``total_amount`` is NULL whenever statement faces report different
    totals for the same action (never averaged, never picked
    silently); the per-share amount, which is unambiguous in the
    label, is always stored.
    """

    __tablename__ = "corporate_action_records"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "action_type",
            "fiscal_year_label",
            "amount_per_share",
            name="uq_corporate_action_records_grain",
        ),
        Index("idx_corporate_action_records_company", "company_id"),
        Index("idx_corporate_action_records_type", "action_type"),
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    fiscal_year_label: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_per_share: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PKR")
    total_amount: Mapped[object] = mapped_column(Numeric(24, 4), nullable=True)
    total_amount_note: Mapped[str] = mapped_column(Text, nullable=True)
    announced_date: Mapped[object] = mapped_column(Date, nullable=True)
    ex_date: Mapped[object] = mapped_column(Date, nullable=True)
    record_date: Mapped[object] = mapped_column(Date, nullable=True)
    effective_date: Mapped[object] = mapped_column(Date, nullable=True)
    payment_date: Mapped[object] = mapped_column(Date, nullable=True)
    date_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    source_evidence: Mapped[dict] = mapped_column(JSON, nullable=True)


class MarketBreadth(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One breadth/liquidity metric for one trading date and scope.

    ``scope`` is MARKET or SECTOR:<sector name>. ``status`` is
    computed | insufficient_inputs | not_applicable | partial. A row
    with status != computed has a NULL value and a reason in
    ``coverage_note`` — it is never zero-filled.
    """

    __tablename__ = "market_breadth"
    __table_args__ = (
        UniqueConstraint("trading_date", "scope", "metric_key", name="uq_market_breadth_grain"),
        Index("idx_market_breadth_date", "trading_date"),
    )
    trading_date: Mapped[object] = mapped_column(Date, nullable=False)
    scope: Mapped[str] = mapped_column(String(200), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    numerator: Mapped[int] = mapped_column(BigInteger, nullable=True)
    denominator: Mapped[int] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    coverage_note: Mapped[str] = mapped_column(Text, nullable=False)


class LiquidityObservation(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One liquidity observation: per-security volume or a market row.

    ``scope_key`` is SEC:<ticker> for a security row or MARKET for a
    market aggregate. Volume share is volume / total market volume on
    the same date. No turnover-based row exists: turnover is NULL for
    every stored price row, so turnover liquidity is insufficient.
    """

    __tablename__ = "liquidity_observations"
    __table_args__ = (
        UniqueConstraint(
            "trading_date",
            "scope_key",
            "metric_key",
            name="uq_liquidity_observations_grain",
        ),
        Index("idx_liquidity_observations_date", "trading_date"),
    )
    trading_date: Mapped[object] = mapped_column(Date, nullable=False)
    scope_key: Mapped[str] = mapped_column(String(100), nullable=False)
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=True
    )
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    coverage_note: Mapped[str] = mapped_column(Text, nullable=False)


class InvestorFlow(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """Investor-flow observation. INTENTIONALLY EMPTY in Phase 12.

    The table exists so a future verified published flow series (SBP
    SCRA/FPI monthly data or NCCPL published flows, after a terms
    review) has a home. No row is written in this run: flows are never
    derived from price/volume alone.
    """

    __tablename__ = "investor_flows"
    __table_args__ = (
        UniqueConstraint(
            "observation_date",
            "flow_category",
            "participant_category",
            name="uq_investor_flows_grain",
        ),
        Index("idx_investor_flows_date", "observation_date"),
    )
    observation_date: Mapped[object] = mapped_column(Date, nullable=False)
    flow_category: Mapped[str] = mapped_column(String(100), nullable=False)
    participant_category: Mapped[str] = mapped_column(String(100), nullable=False)
    net_flow: Mapped[object] = mapped_column(Numeric(24, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PKR")
    source_evidence: Mapped[dict] = mapped_column(JSON, nullable=True)


class AdjustmentRule(IdMixin, CreatedMixin, Base):
    """A price-adjustment rule definition (not an applied adjustment).

    ``formula`` states the rule in words and symbols; ``requires`` lists
    the fields that must exist before the rule may be applied. A rule
    with unmet requirements is defined but never applied — in this run
    every rule is unapplied because no stored action has an ex-date.
    """

    __tablename__ = "adjustment_rules"
    __table_args__ = (UniqueConstraint("rule_key", name="uq_adjustment_rules_key"),)
    rule_key: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    requires: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    application_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="defined_not_applied"
    )
