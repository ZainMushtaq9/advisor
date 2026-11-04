"""Phase 11 news / event models.

Five tables. The Phase 3 ``news`` table (market.py) is intentionally NOT
reused: it has no company link, no taxonomy, no source type, no summary
cap, no match evidence and no review status, and retrofitting it would
rewrite Phase 3 history. It stays untouched (0 rows) for compatibility;
Phase 11 writes only to the tables below.

Copyright discipline is structural, not advisory: there is NO article
body column anywhere in this module. An event stores a headline (<=500
chars), a short summary (<=280 chars), a canonical URL, a publisher and
a content hash. Full copyrighted text can never be stored here.

Quality vocabulary mirrors migration 20261104_0003. Event rows carry
their inputs' status, never higher: a seed event derived from an
UNVERIFIED Phase 7 document is UNVERIFIED.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, IdMixin, ProvenanceMixin


class NewsSource(IdMixin, CreatedMixin, Base):
    """Phase 11 source registry: one row per candidate source.

    ``collection_policy`` is the gate, not a wish:
    - ALLOWED: direct reads already established (SBP, PBS).
    - ALLOWED_SAMPLED: sampled reads only, internal analysis only, no
      republication (issuer IR pages, RNS filings, SECP public pages).
    - TERMS_GATED: systematic retrieval needs prior written permission
      (PSX announcements — the Phase 5 Terms gate). A collector for a
      TERMS_GATED source MUST refuse to run without permission evidence.
    - NOT_COLLECTED: no collection in this run (reputable news: per-outlet
      terms unreviewed; social/rumour: excluded by the brief).
    """

    __tablename__ = "news_sources"
    __table_args__ = (
        UniqueConstraint("source_key", name="uq_news_sources_key"),
        Index("idx_news_sources_policy", "collection_policy"),
    )
    source_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    publisher: Mapped[str] = mapped_column(String(200), nullable=True)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # official | official_filing | regulator | secondary
    collection_policy: Mapped[str] = mapped_column(String(50), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=True)
    terms_note: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt_limit_chars: Mapped[int] = mapped_column(BigInteger, nullable=False, default=280)
    collection_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="not_collected"
    )  # collected_seed | not_collected


class CompanyAlias(IdMixin, CreatedMixin, Base):
    """Deterministic alias map, generated from the registry only.

    Alias types: TICKER, LEGAL (normalized legal name),
    LEGAL_STRIPPED (trailing suffixes stripped, same suffix list as the
    Phase 4 normalization), PAREN_STRIPPED (parenthetical qualifier
    dropped), PAREN_STRIPPED_SUFFIX (both). NO abbreviation expansion
    (IND is not INDUSTRIES), NO token merging (D G is not DG), NO fuzzy
    matching. An alias claimed by more than one company is AMBIGUOUS:
    confidence is capped at 0.50 and every match goes to review.
    """

    __tablename__ = "company_aliases"
    __table_args__ = (
        UniqueConstraint("company_id", "alias_normalized", name="uq_company_aliases_grain"),
        Index("idx_company_aliases_alias", "alias_normalized"),
        Index("idx_company_aliases_company", "company_id"),
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    alias_normalized: Mapped[str] = mapped_column(String(300), nullable=False)
    alias_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False, default=1.0)
    is_ambiguous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class NewsEvent(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One underlying event (not one article).

    ``event_date`` is NULL exactly when the publication date is unknown
    (NML 3rd Quarter Report 2025: Phase 7 records no publication date);
    an unknown date is never guessed and forces review. ``date_status``
    records known vs unknown. ``canonical_key`` is the dedup grain:
    (primary company or NULL, event type, date or 'unknown', normalized
    headline core). Syndicated coverage items link to the canonical
    event via NewsEventLink instead of creating a second event.
    ``sentiment`` is deliberately absent: the brief forbids treating
    sentiment as a factual event.
    """

    __tablename__ = "news_events"
    __table_args__ = (
        UniqueConstraint("canonical_key", name="uq_news_events_canonical"),
        Index(
            "uq_news_events_content_hash",
            "content_hash",
            unique=True,
            postgresql_where=text("content_hash IS NOT NULL"),
        ),
        Index("idx_news_events_date", "event_date"),
        Index("idx_news_events_type", "event_type"),
        Index("idx_news_events_company", "primary_company_id"),
        Index("idx_news_events_review", "review_status"),
    )
    event_date: Mapped[object] = mapped_column(Date, nullable=True)
    date_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="known"
    )  # known | unknown
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(String(280), nullable=True)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=True)
    publisher: Mapped[str] = mapped_column(String(200), nullable=True)
    source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("news_sources.id", ondelete="RESTRICT"), nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    canonical_key: Mapped[str] = mapped_column(String(500), nullable=False)
    primary_company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=True
    )
    relevance_score: Mapped[float] = mapped_column(nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending_review"
    )  # ok | pending_review | scheduled
    match_evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    macro_event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("macro_events.id", ondelete="RESTRICT"), nullable=True
    )
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("financial_documents.id", ondelete="RESTRICT"),
        nullable=True,
    )


class NewsEventCompany(IdMixin, CreatedMixin, Base):
    """Event <-> company links with match evidence and confidence.

    The primary company is also recorded on the event itself; this table
    carries every additional affected company (mergers, sector news) and
    the evidence for each match, so a link is never bare.
    """

    __tablename__ = "news_event_companies"
    __table_args__ = (
        UniqueConstraint("event_id", "company_id", name="uq_news_event_companies_grain"),
        Index("idx_news_event_companies_event", "event_id"),
    )
    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("news_events.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    match_type: Mapped[str] = mapped_column(String(50), nullable=False)
    match_confidence: Mapped[float] = mapped_column(nullable=False)
    match_evidence: Mapped[str] = mapped_column(Text, nullable=True)


class NewsEventLink(IdMixin, CreatedMixin, Base):
    """Syndication / duplicate / coverage links between events.

    ``relation``: syndicated (same story, another publisher),
    duplicate (same content hash, kept for audit), coverage (distinct
    article about the same underlying event). Links never merge rows:
    the canonical event stays canonical and the linked row stays
    queryable.
    """

    __tablename__ = "news_event_links"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "linked_event_id",
            "relation",
            name="uq_news_event_links_grain",
        ),
        Index("idx_news_event_links_event", "event_id"),
    )
    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("news_events.id", ondelete="CASCADE"), nullable=False
    )
    linked_event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("news_events.id", ondelete="CASCADE"), nullable=False
    )
    relation: Mapped[str] = mapped_column(String(50), nullable=False)
