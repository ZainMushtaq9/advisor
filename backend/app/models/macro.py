"""Phase 10 macro/sector tables.

Macro observations reuse the Phase 3 EconomicIndicator model
(economic_indicators). These three tables are new in migration
20261104_0007:

- CompanyMacroExposure: company -> macro exposure register. Every row
  cites issuer-disclosure evidence (a Phase 7 statement line key).
  Sector membership alone is never an exposure.
- MacroRegime: explainable concurrent regime labels with evidence JSON.
  Immutable: a revised assessment is a new row.
- MacroEvent: dated policy/release event calendar. Immutable.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, IdMixin, ProvenanceMixin, VersionMixin


class CompanyMacroExposure(IdMixin, CreatedMixin, ProvenanceMixin, VersionMixin, Base):
    __tablename__ = "company_macro_exposures"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "exposure_key",
            "version_number",
            name="uq_company_macro_exposures_grain",
        ),
        Index("idx_company_macro_exposures_company", "company_id"),
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    exposure_key: Mapped[str] = mapped_column(String(100), nullable=False)
    exposure_name: Mapped[str] = mapped_column(String(300), nullable=False)
    # cost | revenue | income | balance_sheet — which side of the
    # company the exposure touches.
    direction: Mapped[str] = mapped_column(String(50), nullable=False)
    # statement_line_item | disclosure_note — never sector_membership.
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. "income:finance_costs; cash_flow:interest_paid" — statement
    # type + line key from the loaded Phase 7 statements.
    evidence_ref: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class MacroRegime(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    __tablename__ = "macro_regimes"
    __table_args__ = (
        UniqueConstraint(
            "observation_date",
            "regime_label",
            "method_version",
            name="uq_macro_regimes_grain",
        ),
        Index("idx_macro_regimes_date", "observation_date"),
    )
    observation_date: Mapped[object] = mapped_column(Date, nullable=False)
    regime_label: Mapped[str] = mapped_column(String(100), nullable=False)
    method_version: Mapped[str] = mapped_column(String(50), nullable=False)
    # Basis: observation refs, thresholds applied, and labels considered
    # but NOT assigned with reasons. Forecasts are never stored here as
    # observations; outlook text lives under evidence["outlook"] marked
    # FORECAST.
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class MacroEvent(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    __tablename__ = "macro_events"
    __table_args__ = (
        UniqueConstraint(
            "event_date",
            "event_type",
            "title",
            name="uq_macro_events_grain",
        ),
        Index("idx_macro_events_date", "event_date"),
    )
    event_date: Mapped[object] = mapped_column(Date, nullable=False)
    # mpc_meeting | cpi_release | mpc_minutes | budget | gdp_release | ...
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
