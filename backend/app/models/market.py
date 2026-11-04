"""Market data tables — Phase 3. Trigger protection (migration
20261104_0003 + 20261104_0004), not just prose: market_prices,
market_snapshots, announcements and news are fully immutable;
index_prices, corporate_actions and symbol_history are immutable;
live_quotes allows ONLY the is_latest marker to change (old quote
rows cannot be edited otherwise). Grain for market_prices: one row
per security x trading date x bar type x source, so conflicting
sources are kept side-by-side, never silently merged. Prices are
stored UNADJUSTED; adjustment factors live in corporate_actions and
adjusted series are derived views, never edits."""

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
from app.models.base import CreatedMixin, IdMixin, ProvenanceMixin


class MarketPrice(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    __tablename__ = "market_prices"
    __table_args__ = (
        UniqueConstraint(
            "security_id",
            "trading_date",
            "bar_type",
            "data_source_id",
            name="uq_market_prices_grain",
        ),
        Index("idx_market_prices_security_date", "security_id", "trading_date"),
    )
    # Audit H3 fix: data_source_id is NOT NULL here (overriding the
    # nullable mixin column). PostgreSQL treats NULLs as distinct in
    # unique constraints, so a nullable grain source allowed duplicate
    # rows. Production ingest must always set a source.
    data_source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=False
    )
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    trading_session_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("trading_sessions.id", ondelete="SET NULL"), nullable=True
    )
    trading_date: Mapped[object] = mapped_column(Date, nullable=False)
    bar_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="daily"
    )  # daily, intraday_tick (today only)
    open_price: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    high_price: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    low_price: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    close_price: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    turnover: Mapped[object] = mapped_column(Numeric(20, 2), nullable=True)
    previous_close: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    is_adjusted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # False = official unadjusted


class LiveQuote(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """Append-only quote log with a current marker. is_latest marks the
    newest row per (security, source); older rows remain as history."""

    __tablename__ = "live_quotes"
    __table_args__ = (
        Index("idx_live_quotes_security_source", "security_id", "data_source_id", "quote_instant"),
    )
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    quote_instant: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    price: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    bid: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    ask: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class MarketSnapshot(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """Point-in-time whole-market / index snapshot. Never overwritten
    by the next snapshot; as-of queries resolve to the latest snapshot
    at or before a given PKT instant."""

    __tablename__ = "market_snapshots"
    __table_args__ = (Index("idx_market_snapshots_run", "snapshot_run_id", "as_of"),)
    snapshot_run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    as_of: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="SET NULL"), nullable=True
    )
    index_code: Mapped[str] = mapped_column(String(50), nullable=True)
    payload: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # snapshot values as received, with provenance on the row


class IndexPrice(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    __tablename__ = "index_prices"
    __table_args__ = (
        UniqueConstraint(
            "index_code", "trading_date", "data_source_id", name="uq_index_prices_grain"
        ),
        Index("idx_index_prices_code_date", "index_code", "trading_date"),
    )
    # Audit H3 fix: NOT NULL grain source (see MarketPrice).
    data_source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=False
    )
    index_code: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # KSE-100, KSE-30, KSE All Share, ...
    trading_date: Mapped[object] = mapped_column(Date, nullable=False)
    close_value: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    change_value: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    change_percent: Mapped[object] = mapped_column(Numeric(10, 4), nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class CorporateAction(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """Append-only dated events. Adjustment factors are stored, not
    applied destructively to historical prices."""

    __tablename__ = "corporate_actions"
    __table_args__ = (Index("idx_corp_actions_security", "security_id", "event_date"),)
    security_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # dividend, split, bonus, rights, merger, ...
    event_date: Mapped[object] = mapped_column(Date, nullable=False)
    ex_date: Mapped[object] = mapped_column(Date, nullable=True)
    record_date: Mapped[object] = mapped_column(Date, nullable=True)
    adjustment_factor: Mapped[object] = mapped_column(Numeric(20, 6), nullable=True)
    detail: Mapped[str] = mapped_column(Text, nullable=True)
    source_document_ref: Mapped[str] = mapped_column(Text, nullable=True)


class Dividend(IdMixin, CreatedMixin, Base):
    """Dividend detail, one-to-one with the dividend-type row in
    corporate_actions. Prevents double-counting across the two tables."""

    __tablename__ = "dividends"
    corporate_action_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("corporate_actions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    dividend_type: Mapped[str] = mapped_column(String(50), nullable=False)  # cash, stock
    amount: Mapped[object] = mapped_column(Numeric(20, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PKR")
    payment_date: Mapped[object] = mapped_column(Date, nullable=True)


class Announcement(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """Issuer/exchange publications. The DB row stores reference + hash,
    not a second copy of PDF bytes (files live on disk). Corrections
    are new versions, never edits."""

    __tablename__ = "announcements"
    __table_args__ = (
        Index("idx_announcements_company", "company_id", "announcement_date"),
        # Audit M6 fix: same company + same document hash = duplicate.
        # Partial index: NULL hashes are excluded (they go to review).
        Index(
            "uq_announcements_company_hash",
            "company_id",
            "document_hash",
            unique=True,
            postgresql_where=text("document_hash IS NOT NULL"),
        ),
    )
    company_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="SET NULL"), nullable=True
    )
    announcement_date: Mapped[object] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    document_url: Mapped[str] = mapped_column(Text, nullable=True)
    document_hash: Mapped[str] = mapped_column(
        String(64), nullable=True
    )  # SHA-256, the duplicate-detection key
    raw_payload_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("raw_payloads.id", ondelete="SET NULL"), nullable=True
    )


class News(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """Third-party reporting, distinguished from announcements. Neither
    is assumed to be a live feed until verified."""

    __tablename__ = "news"
    __table_args__ = (
        Index("idx_news_date", "news_date"),
        # Audit M6 fix: same content hash = duplicate (NULL hashes
        # excluded; they go to review, per duplicate_key_for_document).
        Index(
            "uq_news_content_hash",
            "content_hash",
            unique=True,
            postgresql_where=text("content_hash IS NOT NULL"),
        ),
    )
    news_date: Mapped[object] = mapped_column(Date, nullable=False)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    publisher: Mapped[str] = mapped_column(String(200), nullable=True)
    article_url: Mapped[str] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    raw_payload_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("raw_payloads.id", ondelete="SET NULL"), nullable=True
    )
