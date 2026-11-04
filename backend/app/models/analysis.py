"""Analysis, economics, portfolios and fundamental-health tables —
Phase 3. Forecasts are probabilistic by design: a forecast row is not
valid without uncertainty fields. Recommendations are versioned,
probabilistic and audited — no guarantee language anywhere. Portfolios
are PAPER-TRADING ONLY: no brokerage account identifiers, no order
path, no real trades."""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
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


class EconomicIndicator(IdMixin, CreatedMixin, ProvenanceMixin, VersionMixin, Base):
    """Definition + observation in one table per Phase 1: indicator_code
    + observation_date grain, verification_status defaults to
    'unverified'. Revisions are new versions, never edits. SECP/SBP/
    PBS/Finance/World Bank/IMF/FRED machine-use is UNVERIFIED (G-01)."""

    __tablename__ = "economic_indicators"
    __table_args__ = (
        UniqueConstraint(
            "indicator_code",
            "observation_date",
            "version_number",
            name="uq_economic_indicators_grain",
        ),
        Index("idx_economic_code_date", "indicator_code", "observation_date"),
    )
    indicator_code: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # CPI, policy_rate, reserves, ...
    indicator_name: Mapped[str] = mapped_column(String(300), nullable=False)
    observation_date: Mapped[object] = mapped_column(Date, nullable=False)
    value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    unit: Mapped[str] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str] = mapped_column(String(30), nullable=True)  # monthly, quarterly, annual


class Valuation(IdMixin, CreatedMixin, ProvenanceMixin, VersionMixin, Base):
    __tablename__ = "valuations"
    __table_args__ = (Index("idx_valuations_security", "security_id", "valuation_date"),)
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    valuation_date: Mapped[object] = mapped_column(Date, nullable=False)
    method: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # dcf, multiples, dividend, asset_based, residual_income
    estimated_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    value_low: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    value_high: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    assumptions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sensitivity: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    input_statement_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    input_price_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True
    )


class Forecast(IdMixin, CreatedMixin, ProvenanceMixin, VersionMixin, Base):
    """Probabilistic: point estimate + interval + quantiles + horizon +
    model version + feature snapshot reference. Uncertainty is NOT NULL
    by design — see the NOT NULL constraints on interval fields."""

    __tablename__ = "forecasts"
    __table_args__ = (
        Index("idx_forecasts_security_horizon", "security_id", "horizon", "forecast_date"),
    )
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    forecast_date: Mapped[object] = mapped_column(Date, nullable=False)
    horizon: Mapped[str] = mapped_column(String(30), nullable=False)  # 1d, 1w, 1m, 3m, 6m, 12m
    point_estimate: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    interval_low: Mapped[object] = mapped_column(Numeric(24, 6), nullable=False)
    interval_high: Mapped[object] = mapped_column(Numeric(24, 6), nullable=False)
    bear_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    base_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    bull_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    probability_bear: Mapped[object] = mapped_column(Numeric(5, 4), nullable=True)
    probability_base: Mapped[object] = mapped_column(Numeric(5, 4), nullable=True)
    probability_bull: Mapped[object] = mapped_column(Numeric(5, 4), nullable=True)
    uncertainty: Mapped[object] = mapped_column(Numeric(24, 6), nullable=False)
    model_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True
    )
    feature_snapshot_ref: Mapped[str] = mapped_column(Text, nullable=True)
    assumptions: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ForecastEvaluation(IdMixin, CreatedMixin, Base):
    """Append-only: one row per forecast x evaluation date x metric,
    referencing the exact forecast row and the realised value's
    provenance. This is how 'was the forecast any good?' is answered
    from data, not from memory."""

    __tablename__ = "forecast_evaluations"
    forecast_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("forecasts.id", ondelete="CASCADE"), nullable=False
    )
    evaluation_date: Mapped[object] = mapped_column(Date, nullable=False)
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    realised_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    realised_value_provenance: Mapped[str] = mapped_column(Text, nullable=True)


class Recommendation(IdMixin, CreatedMixin, ProvenanceMixin, VersionMixin, Base):
    __tablename__ = "recommendations"
    __table_args__ = (Index("idx_recommendations_security", "security_id", "valid_from"),)
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    signal: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # BUY, HOLD, SELL, WATCHLIST — probabilistic proposal only
    confidence: Mapped[object] = mapped_column(Numeric(5, 4), nullable=True)
    evidence: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # links to forecasts, valuations, ratios
    valid_from: Mapped[object] = mapped_column(Date, nullable=True)
    valid_to: Mapped[object] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active"
    )  # active, superseded, expired


class Portfolio(IdMixin, CreatedMixin, Base):
    """Paper / tracked portfolios only. This design does not connect
    to a broker and stores no brokerage account identifiers."""

    __tablename__ = "portfolios"
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    portfolio_type: Mapped[str] = mapped_column(String(50), nullable=False, default="paper")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PKR")
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)


class PortfolioHolding(IdMixin, CreatedMixin, Base):
    """Current holding is mutable, but every change is audit-logged and
    the table carries effective dates so full holding history is an
    additive change, not a redesign. References securities.id, never a
    bare ticker string, so renames do not corrupt holdings."""

    __tablename__ = "portfolio_holdings"
    portfolio_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False
    )
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[object] = mapped_column(Numeric(24, 4), nullable=False)
    average_cost: Mapped[object] = mapped_column(Numeric(24, 4), nullable=True)
    valid_from: Mapped[object] = mapped_column(Date, nullable=True)
    valid_to: Mapped[object] = mapped_column(Date, nullable=True)


class FundamentalAnalysisRun(IdMixin, CreatedMixin, Base):
    __tablename__ = "fundamental_analysis_runs"
    run_key: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="running")
    companies_processed: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)


class FundamentalTrendObservation(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    __tablename__ = "fundamental_trend_observations"
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    observation_date: Mapped[object] = mapped_column(Date, nullable=False)
    trend_type: Mapped[str] = mapped_column(String(100), nullable=False)
    direction: Mapped[str] = mapped_column(String(50), nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class EarningsQualityObservation(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """Warnings use POTENTIAL_WARNING / REQUIRES_REVIEW /
    UNUSUAL_PATTERN / INSUFFICIENT_EVIDENCE language, each with
    supporting evidence — never an automatic fraud classification."""

    __tablename__ = "earnings_quality_observations"
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    warning_level: Mapped[str] = mapped_column(String(50), nullable=False)
    measure_key: Mapped[str] = mapped_column(String(200), nullable=False)
    measure_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class FinancialHealthAssessment(IdMixin, CreatedMixin, ProvenanceMixin, VersionMixin, Base):
    """Transparent health layer: published formulas/weights/thresholds
    live in docs; the row stores category scores + evidence + version.
    A score here is NOT an established credit rating."""

    __tablename__ = "financial_health_assessments"
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # profitability, growth, liquidity, solvency, efficiency, cash_flow, earnings_quality, sector
    score: Mapped[object] = mapped_column(Numeric(10, 4), nullable=True)  # NULL = INSUFFICIENT_DATA
    scoring_method_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SectorMetricProfile(IdMixin, CreatedMixin, Base):
    """Configurable sector-specific analysis profiles: applicability
    and source requirements documented per profile; an unavailable
    metric is UNAVAILABLE, never estimated without justification."""

    __tablename__ = "sector_metric_profiles"
    __table_args__ = (
        UniqueConstraint("sector_id", "metric_key", name="uq_sector_metric_profiles_grain"),
    )
    sector_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False
    )
    metric_key: Mapped[str] = mapped_column(String(200), nullable=False)
    applicability: Mapped[str] = mapped_column(Text, nullable=True)
    source_requirements: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FundamentalWarningEvent(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    __tablename__ = "fundamental_warning_events"
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    event_date: Mapped[object] = mapped_column(Date, nullable=False)
    warning_type: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
