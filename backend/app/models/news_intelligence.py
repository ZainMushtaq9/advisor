"""News Intelligence Engine models (Phase B of the news track).

Nine tables. They EXTEND Phase 11, they do not replace it:

- Phase 11 tables (news_sources, company_aliases, news_events,
  news_event_companies, news_event_links) are reused untouched.
- Phase 21 tables (alert_rules, alerts) are reused for news alerts:
  no separate news_alerts table exists, by design.
- The Phase 3 ``news`` table stays untouched (0 rows) for the same
  reason Phase 11 left it alone.

Copyright discipline is structural, as in Phase 11: there is NO
article-body column anywhere in this module. An article stores a
title (<=500 chars), a summary capped at 280 chars, a canonical URL
and a content hash. Full copyrighted text can never be stored here.

Quality rule (binding): new rows carry their inputs' status, never
higher. An article processed from an UNVERIFIED seed or an
unreviewed source is UNVERIFIED; the LLM (or the deterministic
fallback) never promotes a row to PARTIALLY_VERIFIED or VERIFIED.
Promotion requires the H1 rule (>=2 distinct agreeing sources
including one official) plus the recorded human approval gate, and
no such promotion path exists in this module.

No model here stores a password, API key, token or secret. No
order, execution, external-send or publication concept exists in
these tables. ``processor`` is always one of ``LLM`` or
``RULE_BASED``; a row never claims LLM processing it did not get.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, ProvenanceMixin

# Primary keys are Integer (not IdMixin BigInteger Identity), following
# the Phase 29 acceptance precedent: BigInteger Identity does not
# auto-generate on SQLite, and this package must support the
# SQLite in-memory model tests. Foreign keys to the Phase 3/11
# tables (companies, news_events) stay BigInteger to match them;
# foreign keys to tables in THIS module are Integer to match.


# Processing statuses for a stored article row. PROCESSED = passed
# schema + grounding validation; REVIEW = stored but forced to human
# review (ambiguous entity, ungrounded fact, or confidence < 0.80);
# REJECTED = malformed LLM output or failed validation, stored only
# as a rejection record with its errors, never as content;
# UNPROCESSED = the model was unavailable and no fallback was taken.
ARTICLE_STATUSES = ("PROCESSED", "REVIEW", "REJECTED", "UNPROCESSED")

# Sentiment vocabulary (prompt section 4). Sentiment is NOT a price
# prediction and is stored separately from importance, credibility
# and market reaction (see NewsImpactAssessment / NewsMarketReaction).
SENTIMENTS = ("positive", "negative", "neutral", "mixed")

# Event categories (prompt section 5; same list as the taxonomy
# module). Stored on the sentiment row, not on the article, so a
# reclassification is a new assessment row, not an edit.
EVENT_CATEGORIES = (
    "earnings",
    "dividends",
    "bonus",
    "rights",
    "buyback",
    "board_meeting",
    "board_changes",
    "merger_acquisition",
    "new_project",
    "contract_order",
    "expansion",
    "management_change",
    "regulatory_notice",
    "court_decision",
    "banking_policy",
    "interest_rate",
    "inflation",
    "exchange_rate",
    "foreign_reserves",
    "budget",
    "tax_policy",
    "energy_price",
    "oil_gas",
    "commodity_price",
    "political_geopolitical",
    "market_wide",
    "credit_rating",
    "company_default",
    "trading_suspension",
    "corporate_governance",
    "macro_release",
    "other",
)

# Impact horizons (prompt section 4).
IMPACT_HORIZONS = ("immediate", "short_term", "medium_term", "long_term", "unknown")

# Credibility classes (prompt section 13). Quality is SEPARATE from
# sentiment: a negative article from an official source is high
# credibility and negative sentiment, and both facts are stored.
CREDIBILITY_CLASSES = (
    "official_primary",
    "company_disclosure",
    "established_press",
    "secondary_reporting",
    "unverified",
)

# Collection-run outcomes. "refused" is a successful enforcement
# outcome, not a failure: the run proves a BLOCKED source was not
# collected from. "paused" means the job itself was paused and the
# runner refused to dispatch it.
COLLECTION_RUN_STATUSES = ("collected", "refused", "failed", "paused")


class NewsArticle(CreatedMixin, ProvenanceMixin, Base):
    """One collected article (metadata + capped summary only).

    ``article_id`` is the first 32 hex chars of the SHA-256 content
    hash (same grain as Phase 11 ``content_hash``), so an article and
    a Phase 11 event dedup against each other. ``published_at`` is
    NULL exactly when the publication date is unknown; an unknown
    date is never guessed. ``summary`` is capped at 280 chars by the
    processing pipeline before it reaches this table.
    """

    __tablename__ = "news_articles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __table_args__ = (
        UniqueConstraint("article_id", name="uq_news_articles_article_id"),
        UniqueConstraint("content_hash", name="uq_news_articles_content_hash"),
        Index("idx_news_articles_source", "source_key"),
        Index("idx_news_articles_published", "published_at"),
        Index("idx_news_articles_status", "status"),
    )
    article_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    summary: Mapped[str] = mapped_column(String(280), nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    processor: Mapped[str] = mapped_column(String(20), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=True)
    model_version: Mapped[str] = mapped_column(String(100), nullable=True)
    processing_timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class NewsArticleEntity(CreatedMixin, Base):
    """One resolved entity link for an article.

    ``company_id`` is a surrogate id resolved BY TICKER at write
    time; the durable identity on this row is ``ticker``. A row with
    ``match_confidence`` below 0.80, or an ambiguous alias match, is
    recorded with ``needs_review`` True and the article is forced to
    REVIEW — the match is never silently merged.
    """

    __tablename__ = "news_article_entities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __table_args__ = (
        UniqueConstraint(
            "article_id", "company_id", name="uq_news_article_entities_grain"
        ),
        Index("idx_news_article_entities_ticker", "ticker"),
        Index("idx_news_article_entities_company", "company_id"),
    )
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(30), nullable=False)
    sector_name: Mapped[str] = mapped_column(String(200), nullable=True)
    match_type: Mapped[str] = mapped_column(String(50), nullable=False)
    match_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    match_evidence: Mapped[str] = mapped_column(Text, nullable=True)
    needs_review: Mapped[bool] = mapped_column(nullable=False, default=False)


class NewsSummary(CreatedMixin, Base):
    """A capped summary for an article, kept as its own row so a
    re-summary is a new row, not an overwrite. ``summary`` is capped
    at 280 chars; ``is_llm`` records whether a model produced it, so
    a rule-based excerpt is never presented as model output.
    """

    __tablename__ = "news_summaries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __table_args__ = (
        Index("idx_news_summaries_article", "article_id"),
    )
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False
    )
    summary: Mapped[str] = mapped_column(String(280), nullable=False)
    source_link: Mapped[str] = mapped_column(Text, nullable=True)
    is_llm: Mapped[bool] = mapped_column(nullable=False, default=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=True)


class NewsSentimentAssessment(CreatedMixin, Base):
    """One sentiment + classification assessment for an article.

    Scores are [0, 1] floats validated by the pipeline before write.
    ``extracted_facts`` / ``supporting_evidence`` / ``uncertainty_notes``
    / ``risk_factors`` are JSON lists of strings; every extracted fact
    passed the grounding check (shares a significant token with the
    source text) or the article was forced to REVIEW. Sentiment is
    stored here, importance and credibility on the impact row, market
    reaction on its own row — the three are never conflated.
    """

    __tablename__ = "news_sentiment_assessments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __table_args__ = (
        Index("idx_news_sentiment_article", "article_id"),
        Index("idx_news_sentiment_sentiment", "sentiment"),
        Index("idx_news_sentiment_category", "event_category"),
    )
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False
    )
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    event_category: Mapped[str] = mapped_column(String(50), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    potential_impact_horizon: Mapped[str] = mapped_column(String(20), nullable=False)
    extracted_facts: Mapped[object] = mapped_column(JSON, nullable=False, default=list)
    supporting_evidence: Mapped[object] = mapped_column(JSON, nullable=False, default=list)
    uncertainty_notes: Mapped[object] = mapped_column(JSON, nullable=False, default=list)
    risk_factors: Mapped[object] = mapped_column(JSON, nullable=False, default=list)
    processor: Mapped[str] = mapped_column(String(20), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=True)
    model_version: Mapped[str] = mapped_column(String(100), nullable=True)


class NewsImpactAssessment(CreatedMixin, Base):
    """One impact assessment for an article, with its dimensions
    kept separate: importance, credibility, company relevance, sector
    relevance and market relevance are five different numbers, not
    one blended score. ``counterarguments`` preserves conflicting
    records side-by-side; no version is silently chosen. No
    percentage impact and no target price exists anywhere here.
    """

    __tablename__ = "news_impact_assessments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __table_args__ = (
        Index("idx_news_impact_article", "article_id"),
        Index("idx_news_impact_importance", "importance_score"),
    )
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False
    )
    importance_score: Mapped[float] = mapped_column(Float, nullable=False)
    credibility_score: Mapped[float] = mapped_column(Float, nullable=False)
    credibility_class: Mapped[str] = mapped_column(String(50), nullable=False)
    # NULL means "not applicable to this item's scope" (a macro item
    # has no company relevance; a company item with no sector match
    # has no sector relevance). NULL is never a measured zero.
    company_relevance: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector_relevance: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_relevance: Mapped[float] = mapped_column(Float, nullable=False)
    horizon: Mapped[str] = mapped_column(String(20), nullable=False)
    supporting_facts: Mapped[object] = mapped_column(JSON, nullable=False, default=list)
    counterarguments: Mapped[object] = mapped_column(JSON, nullable=False, default=list)
    uncertainty: Mapped[str] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="computed")


class NewsMarketReaction(CreatedMixin, Base):
    """One event-study row for an article (or a Phase 11 event).

    All prices are Decimal (NUMERIC) from ACTUAL stored market_price
    observations only. ``status`` is "computed" or "INSUFFICIENT_DATA";
    a window with a missing observation is INSUFFICIENT_DATA with the
    exact missing piece named in ``note`` — never zero-filled, never
    estimated. Returns are stored as a JSON object keyed by window
    ("1", "5", "10", "20") so a partially computable study keeps its
    computed windows and names its missing ones. Correlation is not
    causality: ``note`` states that on every row.
    """

    __tablename__ = "news_market_reactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __table_args__ = (
        Index("idx_news_reaction_article", "article_id"),
        Index("idx_news_reaction_event", "event_id"),
        Index("idx_news_reaction_status", "status"),
    )
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=True
    )
    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("news_events.id", ondelete="CASCADE"), nullable=True
    )
    event_date: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    pre_price: Mapped[object] = mapped_column(Numeric(20, 6), nullable=True)
    event_day_price: Mapped[object] = mapped_column(Numeric(20, 6), nullable=True)
    post_price: Mapped[object] = mapped_column(Numeric(20, 6), nullable=True)
    returns: Mapped[object] = mapped_column(JSON, nullable=False, default=dict)
    volume_change: Mapped[object] = mapped_column(Numeric(20, 6), nullable=True)
    benchmark_return: Mapped[object] = mapped_column(JSON, nullable=False, default=dict)
    sector_return: Mapped[object] = mapped_column(JSON, nullable=False, default=dict)
    excess_return: Mapped[object] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=True)


class NewsCollectionRun(CreatedMixin, Base):
    """One collection attempt for one source: collected, refused,
    failed or paused. A refused run is evidence, not an error: it
    proves a BLOCKED source was not collected from, with the exact
    policy reason recorded. Nothing here stores article bodies.
    """

    __tablename__ = "news_collection_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __table_args__ = (
        Index("idx_news_runs_source", "source_key"),
        Index("idx_news_runs_status", "status"),
    )
    source_key: Mapped[str] = mapped_column(String(100), nullable=False)
    run_started_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    run_finished_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    items_seen: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    items_stored: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    policy_reason: Mapped[str] = mapped_column(Text, nullable=True)
    error: Mapped[str] = mapped_column(Text, nullable=True)


class NewsModelEvaluation(CreatedMixin, Base):
    """One model/dataset evaluation: the metrics are always paired
    with ``dataset_size`` so a small-N result can never be quoted
    without its sample size. ``metrics`` is a JSON object (entity
    precision/recall, ticker accuracy, classification
    precision/recall, sentiment agreement, summary factuality,
    citation correctness, latency). No production accuracy claim is
    ever derived from a row here without its dataset_size.
    """

    __tablename__ = "news_model_evaluations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __table_args__ = (
        Index("idx_news_eval_model", "model_name"),
    )
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    dataset_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    metrics: Mapped[object] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class NewsEventEvidence(CreatedMixin, Base):
    """A link from a Phase 11 canonical event to a stored article
    that evidences it (or contradicts it). ``evidence_type`` is
    "supports" or "contradicts"; conflicting evidence is preserved
    side-by-side here, never resolved by deleting a row.
    """

    __tablename__ = "news_event_evidence"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    __table_args__ = (
        UniqueConstraint(
            "event_id", "article_id", name="uq_news_event_evidence_grain"
        ),
        Index("idx_news_evidence_event", "event_id"),
        Index("idx_news_evidence_article", "article_id"),
    )
    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("news_events.id", ondelete="CASCADE"), nullable=False
    )
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(String(20), nullable=False, default="supports")
    note: Mapped[str] = mapped_column(Text, nullable=True)
