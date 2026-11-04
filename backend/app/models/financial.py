"""Financial statements, documents, fundamentals and technicals —
Phase 3. Statements are VERSIONED: restatements are new versions with
supersedes_id, never edits. Line items keep the company's ORIGINAL
label alongside the canonical key, because per-company formats differ
and a premature single taxonomy would lose information. Cumulative
interim figures are never added together as if they were standalone
quarters; derived standalone quarters are stored separately, marked
DERIVED, with their derivation recorded."""

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
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, IdMixin, ProvenanceMixin, VersionMixin


class FinancialStatement(IdMixin, CreatedMixin, ProvenanceMixin, VersionMixin, Base):
    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "period_start",
            "period_end",
            "statement_type",
            "version_number",
            "data_source_id",
            name="uq_financial_statements_grain",
        ),
        Index("idx_financial_statements_company_period", "company_id", "period_end"),
        # Audit M2 fix: one current row per grain. Partial index, so
        # historical (is_current = FALSE) versions are unaffected.
        Index(
            "uq_financial_statements_current",
            "company_id",
            "period_start",
            "period_end",
            "statement_type",
            "data_source_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )
    # Audit H3 fix: NOT NULL grain source (see MarketPrice).
    data_source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    statement_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # income, balance_sheet, cash_flow, changes_in_equity
    period_start: Mapped[object] = mapped_column(Date, nullable=False)
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    publication_date: Mapped[object] = mapped_column(Date, nullable=True)
    financial_year: Mapped[str] = mapped_column(String(20), nullable=True)
    fiscal_quarter: Mapped[str] = mapped_column(String(20), nullable=True)
    reporting_frequency: Mapped[str] = mapped_column(
        String(30), nullable=True
    )  # annual, quarterly, half_yearly, nine_month
    audited_status: Mapped[str] = mapped_column(
        String(30), nullable=True
    )  # audited, reviewed, unaudited
    consolidated_status: Mapped[str] = mapped_column(
        String(30), nullable=True
    )  # consolidated, unconsolidated
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PKR")
    unit_scale: Mapped[str] = mapped_column(
        String(30), nullable=True
    )  # rupees, thousands, millions, billions
    accounting_standard: Mapped[str] = mapped_column(String(100), nullable=True)
    document_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("financial_documents.id", ondelete="SET NULL"), nullable=True
    )


class FinancialStatementLineItem(IdMixin, CreatedMixin, VersionMixin, Base):
    """One row per statement version x line-item key. Original value,
    parsed value, currency and reported unit are ALL kept."""

    __tablename__ = "financial_statement_line_items"
    __table_args__ = (
        UniqueConstraint("statement_id", "line_item_key", "version_number", name="uq_fsli_grain"),
        Index("idx_fsli_statement", "statement_id"),
        # Audit M2 fix: one current row per statement x key.
        Index(
            "uq_fsli_current",
            "statement_id",
            "line_item_key",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )
    statement_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("financial_statements.id", ondelete="CASCADE"), nullable=False
    )
    line_item_key: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # canonical key, e.g. revenue, net_income
    original_label: Mapped[str] = mapped_column(String(500), nullable=False)
    original_displayed_value: Mapped[str] = mapped_column(
        String(200), nullable=True
    )  # as printed, parentheses/dashes preserved
    numeric_value: Mapped[object] = mapped_column(Numeric(24, 4), nullable=True)
    normalized_value: Mapped[object] = mapped_column(
        Numeric(24, 4), nullable=True
    )  # in base currency units, per normalization rule
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PKR")
    reported_unit: Mapped[str] = mapped_column(String(30), nullable=True)
    normalization_rule: Mapped[str] = mapped_column(Text, nullable=True)
    page_number: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(100), nullable=True)
    extraction_confidence: Mapped[object] = mapped_column(Numeric(5, 4), nullable=True)
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")
    is_derived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    derivation_formula: Mapped[str] = mapped_column(Text, nullable=True)


class FinancialDocument(IdMixin, CreatedMixin, Base):
    __tablename__ = "financial_documents"
    __table_args__ = (
        # Audit M6 fix: same company + same content hash = duplicate
        # (NULL hashes excluded; they go to review).
        Index(
            "uq_financial_documents_company_hash",
            "company_id",
            "content_hash",
            unique=True,
            postgresql_where=text("content_hash IS NOT NULL"),
        ),
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # annual_report, quarterly, half_yearly, disclosure, ...
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=True)
    storage_location: Mapped[str] = mapped_column(Text, nullable=True)  # storage-relative path
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True)  # duplicate-detection key
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)
    page_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class FinancialDocumentVersion(IdMixin, CreatedMixin, Base):
    """Revised/restated documents: new version rows, never overwrites."""

    __tablename__ = "financial_document_versions"
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("financial_documents.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    supersedes_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Audit M3 fix: document versions are versioned rows, so they
    # carry is_current like every other VersionMixin table.
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    restatement_indicator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    restatement_reason: Mapped[str] = mapped_column(Text, nullable=True)
    publication_date: Mapped[object] = mapped_column(Date, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    storage_location: Mapped[str] = mapped_column(Text, nullable=True)


class FinancialDocumentDownload(IdMixin, CreatedMixin, Base):
    __tablename__ = "financial_document_downloads"
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("financial_documents.id", ondelete="CASCADE"), nullable=False
    )
    attempted_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # success, failed, retry
    http_status: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    error_detail: Mapped[str] = mapped_column(Text, nullable=True)


class FundamentalMetricDefinition(IdMixin, CreatedMixin, Base):
    """Phase 1 'ratios' realised here: a definition row (formula,
    inputs, method version) plus value rows that reference their input
    statement versions. A ratio is never hand-entered without a method."""

    __tablename__ = "fundamental_metric_definitions"
    metric_key: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True
    )  # gross_margin, roe, current_ratio, ...
    category: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # profitability, liquidity, leverage, efficiency, growth, cash_flow
    formula_text: Mapped[str] = mapped_column(Text, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    required_inputs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)


class FundamentalMetricValue(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    __tablename__ = "fundamental_metric_values"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "metric_definition_id",
            "period_end",
            "calculation_version",
            name="uq_fmv_grain",
        ),
        Index("idx_fmv_company_period", "company_id", "period_end"),
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    metric_definition_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fundamental_metric_definitions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    value: Mapped[object] = mapped_column(
        Numeric(24, 6), nullable=True
    )  # NULL = NOT_CALCULABLE, never a guessed zero
    calculation_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    input_statement_ids: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # exact statement version ids used
    # Audit M5 fix: restore the three Phase 1 'ratios' properties the
    # split dropped. security_id allows per-security multiples (P/E);
    # computation_status distinguishes NOT_CALCULABLE from not yet
    # computed; input_price_ids links price-based multiples to prices.
    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="SET NULL"), nullable=True
    )
    computation_status: Mapped[str] = mapped_column(
        String(30), nullable=True
    )  # computed, failed, insufficient_inputs
    input_price_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_derived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TechnicalIndicatorDefinition(IdMixin, CreatedMixin, Base):
    __tablename__ = "technical_indicator_definitions"
    indicator_key: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True
    )  # sma, ema, rsi, macd, bollinger, atr, ...
    category: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # trend, momentum, volatility, volume
    formula_text: Mapped[str] = mapped_column(Text, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    default_parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    warmup_periods: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class TechnicalIndicatorConfiguration(IdMixin, CreatedMixin, Base):
    __tablename__ = "technical_indicator_configurations"
    indicator_definition_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("technical_indicator_definitions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=False)
    config_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TechnicalIndicatorValue(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    __tablename__ = "technical_indicator_values"
    __table_args__ = (
        UniqueConstraint(
            "security_id",
            "indicator_configuration_id",
            "observation_date",
            "timeframe",
            name="uq_tiv_grain",
        ),
        Index("idx_tiv_security_date", "security_id", "observation_date"),
    )
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    indicator_configuration_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("technical_indicator_configurations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    observation_date: Mapped[object] = mapped_column(Date, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(30), nullable=False, default="daily")
    value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    calculation_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    last_input_observation_date: Mapped[object] = mapped_column(Date, nullable=True)


class QuantitativeMarketFeature(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """Deterministic regime/feature summaries (trending, range-bound,
    high/low volatility, ...). Thresholds are versioned configs, and
    a feature may use only information available at or before its
    observation date — no look-ahead."""

    __tablename__ = "quantitative_market_features"
    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="SET NULL"), nullable=True
    )
    index_code: Mapped[str] = mapped_column(String(50), nullable=True)
    feature_key: Mapped[str] = mapped_column(String(200), nullable=False)
    observation_date: Mapped[object] = mapped_column(Date, nullable=False)
    feature_value: Mapped[str] = mapped_column(String(200), nullable=True)
    threshold_config_version: Mapped[str] = mapped_column(String(50), nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class MarketRegimeObservation(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    __tablename__ = "market_regime_observations"
    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="SET NULL"), nullable=True
    )
    index_code: Mapped[str] = mapped_column(String(50), nullable=True)
    observation_date: Mapped[object] = mapped_column(Date, nullable=False)
    regime_label: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # heuristic classification, never a proven prediction
    threshold_config_version: Mapped[str] = mapped_column(String(50), nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class TechnicalSignalEvent(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """Event candidates (crossovers, threshold crossings, breakouts).
    Stored separately from any future investment decision engine, and
    never equated with a guaranteed buying/selling opportunity."""

    __tablename__ = "technical_signal_events"
    __table_args__ = (Index("idx_tse_security_date", "security_id", "event_date"),)
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    event_date: Mapped[object] = mapped_column(Date, nullable=False)
    indicator_key: Mapped[str] = mapped_column(String(200), nullable=False)
    event_condition: Mapped[str] = mapped_column(String(300), nullable=False)
    observed_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    parameter_configuration: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    calculation_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")


class TechnicalCalculationRun(IdMixin, CreatedMixin, Base):
    __tablename__ = "technical_calculation_runs"
    run_key: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="running")
    securities_processed: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    records_written: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)


class TechnicalCalculationError(IdMixin, CreatedMixin, Base):
    __tablename__ = "technical_calculation_errors"
    run_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("technical_calculation_runs.id", ondelete="SET NULL"), nullable=True
    )
    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="SET NULL"), nullable=True
    )
    indicator_key: Mapped[str] = mapped_column(String(200), nullable=True)
    error_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # insufficient_warmup, missing_data, invalid_ohlc, ...
    detail: Mapped[str] = mapped_column(Text, nullable=True)
