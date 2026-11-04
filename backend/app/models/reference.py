"""Reference / master tables — Phase 3: exchanges, sectors, companies,
securities, identifiers, symbol history, trading calendars/sessions,
users, roles. One row per company (legal issuer), NOT per ticker; one
row per security (tradable instrument). History joins through the
security's stable surrogate id, never through the ticker string alone
(ENGRO -> ENGROH is the verified PSX rename case)."""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, IdMixin


class Exchange(IdMixin, CreatedMixin, Base):
    __tablename__ = "exchanges"
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)  # PSX
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    timezone_name: Mapped[str] = mapped_column(String(100), nullable=False, default="Asia/Karachi")
    country: Mapped[str] = mapped_column(String(100), nullable=True)


class Sector(IdMixin, CreatedMixin, Base):
    """Source taxonomy preserved: source_sector_name + canonical name.
    The 38-vs-37 sector discrepancy (psx-dps vs psxdata) is handled by
    keeping both taxonomies as rows with different sources, NOT by
    picking a winner before verification (Phase 1 gate G-03)."""

    __tablename__ = "sectors"
    __table_args__ = (
        UniqueConstraint("source", "source_sector_name", name="uq_sectors_source_name"),
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # canonical name
    source_sector_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    canonical_sector_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sectors.id", ondelete="SET NULL"), nullable=True
    )


class Company(IdMixin, CreatedMixin, Base):
    __tablename__ = "companies"
    __table_args__ = (Index("idx_companies_status", "status"),)
    legal_name: Mapped[str] = mapped_column(String(300), nullable=False)
    short_name: Mapped[str] = mapped_column(String(200), nullable=True)
    sector_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sectors.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING_REVIEW")
    # Lifecycle: VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, CONFLICTED,
    # INACTIVE, SUSPENDED, DELISTED, PENDING_REVIEW
    listing_date: Mapped[object] = mapped_column(Date, nullable=True)
    delisting_date: Mapped[object] = mapped_column(Date, nullable=True)
    website: Mapped[str] = mapped_column(Text, nullable=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)


class CompanyIdentifier(IdMixin, CreatedMixin, Base):
    """All known identifiers for a company (ISIN, PSX code, registrar
    codes, ...). Previous identifiers are kept, never overwritten."""

    __tablename__ = "company_identifiers"
    __table_args__ = (
        UniqueConstraint(
            "identifier_type", "identifier_value", name="uq_company_identifiers_type_value"
        ),
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    identifier_type: Mapped[str] = mapped_column(String(100), nullable=False)
    identifier_value: Mapped[str] = mapped_column(String(200), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    valid_from: Mapped[object] = mapped_column(Date, nullable=True)
    valid_to: Mapped[object] = mapped_column(Date, nullable=True)


class Security(IdMixin, CreatedMixin, Base):
    __tablename__ = "securities"
    __table_args__ = (Index("idx_securities_company", "company_id"),)
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    exchange_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("exchanges.id", ondelete="SET NULL"), nullable=True
    )
    ticker: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # current ticker only; history in symbol_history
    security_type: Mapped[str] = mapped_column(
        String(100), nullable=True
    )  # ordinary, preference, ...
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING_REVIEW")
    isin: Mapped[str] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)


class SymbolHistory(IdMixin, CreatedMixin, Base):
    """Append-only rename/transfer history for a security."""

    __tablename__ = "symbol_history"
    __table_args__ = (Index("idx_symbol_history_security", "security_id", "effective_date"),)
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="CASCADE"), nullable=False
    )
    previous_ticker: Mapped[str] = mapped_column(String(50), nullable=False)
    new_ticker: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_company_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    new_company_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    effective_date: Mapped[object] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    source_evidence: Mapped[str] = mapped_column(Text, nullable=True)


class TradingCalendar(IdMixin, CreatedMixin, Base):
    """One row per exchange per calendar date. Absence of a row means
    'unknown', NOT 'closed' — that is what makes missing-session
    detection possible."""

    __tablename__ = "trading_calendars"
    __table_args__ = (
        UniqueConstraint("exchange_id", "calendar_date", name="uq_trading_calendars_exchange_date"),
    )
    exchange_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("exchanges.id", ondelete="CASCADE"), nullable=False
    )
    calendar_date: Mapped[object] = mapped_column(Date, nullable=False)
    is_trading_day: Mapped[bool] = mapped_column(Boolean, nullable=False)
    session_type: Mapped[str] = mapped_column(String(50), nullable=True)  # full, half, closed
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class TradingSession(IdMixin, CreatedMixin, Base):
    """A market session that actually occurred (or was expected). Prices
    reference a session; a missing session is recorded here / in the
    quality registry, never filled with an estimated price."""

    __tablename__ = "trading_sessions"
    __table_args__ = (
        UniqueConstraint("exchange_id", "session_date", name="uq_trading_sessions_exchange_date"),
    )
    exchange_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("exchanges.id", ondelete="CASCADE"), nullable=False
    )
    session_date: Mapped[object] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unknown"
    )  # completed, partial, missing, holiday
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class User(IdMixin, CreatedMixin, Base):
    """Display identity only. NO credential storage is specified in
    Phase 1/3 — no column here stores a password, API key or secret."""

    __tablename__ = "users"
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_ref: Mapped[str] = mapped_column(
        String(200), nullable=True
    )  # e.g. email reference, not a credential
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)


class Role(IdMixin, CreatedMixin, Base):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    permission_scope: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # scope data, not enforcement logic


class UserRoleAssignment(IdMixin, CreatedMixin, Base):
    __tablename__ = "user_role_assignments"
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    valid_from: Mapped[object] = mapped_column(Date, nullable=True)
    valid_to: Mapped[object] = mapped_column(Date, nullable=True)
