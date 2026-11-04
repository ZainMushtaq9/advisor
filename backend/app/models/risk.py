"""Phase 14 risk management and exposure analytics models.

Seven tables. Design rules from the Phase 14 brief:

- Risk is descriptive and analytical only. No row here is investment
  advice, a buy/sell signal (Phase 15 owns proposals), or a forecast
  presented as fact (Phase 13 owns forecasting and it abstained on
  every target — this phase does not reintroduce point forecasts
  through the back door).
- A NOT_CALCULABLE risk metric is a stored fact (value NULL,
  status insufficient_inputs, reason in evidence), never a zero and
  never an estimate. Market-risk series metrics (volatility, beta,
  drawdown, downside deviation, VaR/ES, correlation, gap risk) all
  need a price series; with one trading date (2026-11-03) and
  previous_close NULL on all 444 rows, every one of them is
  insufficient_inputs for every security, with the exact reason.
- Flags never infer fraud, default or solvency from one anomaly.
  They record the observed fact (a Phase 8 warning, an absent
  auditor opinion, a NULL publication date, a stale statement,
  an abstained forecast) with severity info/warning only.
- Controls are versioned rules for SIMULATED portfolios only. No
  live execution exists anywhere in this project; a control check
  that cannot run (no series for a drawdown warning) is BLOCKED,
  never passed by default.
- Stress scenarios are transparent arithmetic on a stated
  simulated portfolio. Scenarios whose sensitivity coefficient
  does not exist in stored data (rate shock needs a floating/fixed
  debt split; FX shock needs FX-denominated amounts; commodity
  shock needs a revenue elasticity) are insufficient_inputs, never
  computed from an assumed coefficient.
- New rows carry their inputs' status, never higher: every Phase 14
  row is UNVERIFIED, matching its inputs (Phase 10 macro rows are
  the only VERIFIED inputs in the pipeline, and no risk value here
  depends solely on one — sector participation comes from
  UNVERIFIED Phase 12 breadth rows).

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


class RiskMetricDefinition(IdMixin, CreatedMixin, Base):
    """One metric in the Phase 14 risk metric library.

    ``min_observations`` is the series length the formula needs
    before it may produce a value at all. ``scope`` is
    security / sector / market.
    """

    __tablename__ = "risk_metric_definitions"
    __table_args__ = (UniqueConstraint("metric_key", name="uq_risk_metric_definitions_key"),)

    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    min_observations: Mapped[int] = mapped_column(BigInteger, nullable=False)
    window: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    scope: Mapped[str] = mapped_column(String(50), nullable=False)


class RiskMetricValue(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One computed or insufficient risk metric value.

    ``scope_key`` is a ticker, a sector name (SECTOR:* rows reuse
    the Phase 12 breadth scope strings), or MARKET. ``value`` is
    NULL exactly when ``computation_status`` is not ``computed``.
    ``as_of_date`` is the observation date (2026-11-03 for price
    derived rows); a window is stated in evidence, never hidden.
    """

    __tablename__ = "risk_metric_values"
    __table_args__ = (
        UniqueConstraint(
            "metric_key",
            "scope_key",
            "as_of_date",
            name="uq_risk_metric_values_grain",
        ),
        Index("ix_risk_metric_values_scope", "scope_key"),
    )

    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(100), nullable=False)
    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="SET NULL"), nullable=True
    )
    as_of_date: Mapped[object] = mapped_column(Date, nullable=False)
    value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    computation_status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class RiskFlag(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One risk flag for a company or for the market.

    ``flag_type`` names the observed fact (e.g.
    auditor_opinion_absent, statement_stale, forecast_abstention).
    ``severity`` is info or warning only — never a default,
    fraud or solvency conclusion. ``company_id`` is NULL for
    market-level flags.
    """

    __tablename__ = "risk_flags"
    __table_args__ = (
        UniqueConstraint(
            "flag_type",
            "company_id",
            "as_of_date",
            name="uq_risk_flags_grain",
        ),
        Index("ix_risk_flags_company", "company_id"),
    )

    flag_type: Mapped[str] = mapped_column(String(100), nullable=False)
    company_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    as_of_date: Mapped[object] = mapped_column(Date, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class RiskControl(IdMixin, CreatedMixin, Base):
    """One versioned control rule for simulated portfolios.

    Rules are configuration, not data: ``rule`` holds the threshold
    and its rationale. A new version supersedes the old one; old
    versions are never edited.
    """

    __tablename__ = "risk_controls"
    __table_args__ = (
        UniqueConstraint("control_key", "version", name="uq_risk_controls_key_version"),
    )

    control_key: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rule: Mapped[dict] = mapped_column(JSON, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    effective_date: Mapped[object] = mapped_column(Date, nullable=False)


class RiskControlCheck(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One application of a control rule to a scope.

    ``outcome`` is pass, breach, or blocked (blocked = the check
    cannot run because a required input is absent; a blocked check
    never counts as a pass). ``scope_key`` is SIMULATED_PORTFOLIO
    or a ticker.
    """

    __tablename__ = "risk_control_checks"
    __table_args__ = (
        UniqueConstraint(
            "control_key",
            "version",
            "scope_key",
            "as_of_date",
            name="uq_risk_control_checks_grain",
        ),
    )

    control_key: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    scope_key: Mapped[str] = mapped_column(String(100), nullable=False)
    as_of_date: Mapped[object] = mapped_column(Date, nullable=False)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    observed_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    threshold_value: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class StressScenario(IdMixin, CreatedMixin, Base):
    """One transparent stress scenario definition.

    ``shock`` states the shock in plain terms (e.g. market -10%).
    No scenario here executes anything: every result is arithmetic
    on stored closes, labelled simulation only.
    """

    __tablename__ = "stress_scenarios"
    __table_args__ = (UniqueConstraint("scenario_key", name="uq_stress_scenarios_key"),)

    scenario_key: Mapped[str] = mapped_column(String(100), nullable=False)
    shock: Mapped[str] = mapped_column(Text, nullable=False)
    applies_to: Mapped[str] = mapped_column(String(100), nullable=False)
    method: Mapped[str] = mapped_column(Text, nullable=False)


class StressResult(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One stress-test result: a computed portfolio impact, or an
    insufficient_inputs row with the exact missing coefficient.

    ``scope_key`` is SIMULATED_PORTFOLIO or a ticker (for the
    idiosyncratic single-name shock). ``impact_pct`` is NULL
    exactly when the result is not computed.
    """

    __tablename__ = "stress_results"
    __table_args__ = (
        UniqueConstraint(
            "scenario_key",
            "scope_key",
            "as_of_date",
            name="uq_stress_results_grain",
        ),
    )

    scenario_key: Mapped[str] = mapped_column(String(100), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(100), nullable=False)
    as_of_date: Mapped[object] = mapped_column(Date, nullable=False)
    impact_pct: Mapped[object] = mapped_column(Numeric(24, 6), nullable=True)
    computation_status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
