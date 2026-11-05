"""news_intelligence_engine

Revision ID: 20261104_0025
Revises: 20261104_0024
Create Date: 2026-11-05

News Intelligence Engine tables (prompt sections 3-4, 13-14). They
EXTEND Phase 11 and reuse its tables (news_sources,
company_aliases, news_events, news_event_companies); Phase 21 alert
tables are reused for news alerts, so no news_alerts table is
created here. No article-body column exists anywhere in this
migration: titles (<=500), summaries (<=280) and canonical URLs
only, by copyright discipline.

Vocabulary enforcement follows the Phase 3 precedent (migrations
0003/0004): CHECK constraints on quality_status and on the status /
sentiment / category / horizon / credibility vocabularies, so an
invalid value fails at the database, not just in application code.

Primary keys are Integer (not BigInteger Identity), following the
Phase 29 acceptance precedent (migration 0024): BigInteger Identity
does not auto-generate on SQLite, and this package must support
the SQLite in-memory model tests.

Quality rule: new rows carry their inputs' status, never higher.
No promotion path to VERIFIED / PARTIALLY_VERIFIED exists in this
migration or in the models that map to these tables.

Downgrade drops the nine tables in reverse dependency order.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0025"
down_revision: str | None = "20261104_0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _pk() -> sa.Column:
    return sa.Column(
        "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
    )


def _created() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


def _provenance() -> list[sa.Column]:
    return [
        sa.Column(
            "data_source_id",
            sa.BigInteger(),
            sa.ForeignKey("data_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_key", sa.String(length=100), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "quality_status",
            sa.String(length=30),
            nullable=False,
            server_default="UNVERIFIED",
        ),
    ]


QUALITY_CK = (
    "quality_status IN ('VERIFIED', 'PARTIALLY_VERIFIED', 'UNVERIFIED', "
    "'CONFLICTED', 'MISSING', 'REJECTED', 'STALE', 'PENDING_REVIEW')"
)


def upgrade() -> None:
    op.create_table(
        "news_articles",
        _pk(),
        sa.Column("article_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source", sa.String(length=200), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="en"),
        sa.Column("summary", sa.String(length=280), nullable=False, server_default=""),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("processor", sa.String(length=20), nullable=False),
        sa.Column("model_name", sa.String(length=200), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("processing_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        *_provenance(),
        _created(),
        sa.UniqueConstraint("article_id", name="uq_news_articles_article_id"),
        sa.UniqueConstraint("content_hash", name="uq_news_articles_content_hash"),
        sa.Index("idx_news_articles_source", "source_key"),
        sa.Index("idx_news_articles_published", "published_at"),
        sa.Index("idx_news_articles_status", "status"),
        sa.CheckConstraint(QUALITY_CK, name="ck_news_articles_quality"),
        sa.CheckConstraint(
            "status IN ('PROCESSED', 'REVIEW', 'REJECTED', 'UNPROCESSED')",
            name="ck_news_articles_status",
        ),
        sa.CheckConstraint(
            "processor IN ('LLM', 'RULE_BASED')",
            name="ck_news_articles_processor",
        ),
    )
    op.create_table(
        "news_article_entities",
        _pk(),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("news_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            sa.BigInteger(),
            sa.ForeignKey("companies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(length=30), nullable=False),
        sa.Column("sector_name", sa.String(length=200), nullable=True),
        sa.Column("match_type", sa.String(length=50), nullable=False),
        sa.Column("match_confidence", sa.Float(), nullable=False),
        sa.Column("match_evidence", sa.Text(), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default="false"),
        _created(),
        sa.UniqueConstraint(
            "article_id", "company_id", name="uq_news_article_entities_grain"
        ),
        sa.Index("idx_news_article_entities_ticker", "ticker"),
        sa.Index("idx_news_article_entities_company", "company_id"),
    )
    op.create_table(
        "news_summaries",
        _pk(),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("news_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("summary", sa.String(length=280), nullable=False),
        sa.Column("source_link", sa.Text(), nullable=True),
        sa.Column("is_llm", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("model_name", sa.String(length=200), nullable=True),
        _created(),
        sa.Index("idx_news_summaries_article", "article_id"),
    )
    op.create_table(
        "news_sentiment_assessments",
        _pk(),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("news_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sentiment", sa.String(length=20), nullable=False),
        sa.Column("event_category", sa.String(length=50), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("impact_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("potential_impact_horizon", sa.String(length=20), nullable=False),
        sa.Column("extracted_facts", sa.JSON(), nullable=False),
        sa.Column("supporting_evidence", sa.JSON(), nullable=False),
        sa.Column("uncertainty_notes", sa.JSON(), nullable=False),
        sa.Column("risk_factors", sa.JSON(), nullable=False),
        sa.Column("processor", sa.String(length=20), nullable=False),
        sa.Column("model_name", sa.String(length=200), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        _created(),
        sa.Index("idx_news_sentiment_article", "article_id"),
        sa.Index("idx_news_sentiment_sentiment", "sentiment"),
        sa.Index("idx_news_sentiment_category", "event_category"),
        sa.CheckConstraint(
            "sentiment IN ('positive', 'negative', 'neutral', 'mixed')",
            name="ck_news_sentiment_sentiment",
        ),
        sa.CheckConstraint(
            "potential_impact_horizon IN ('immediate', 'short_term', "
            "'medium_term', 'long_term', 'unknown')",
            name="ck_news_sentiment_horizon",
        ),
        sa.CheckConstraint(
            "relevance_score BETWEEN 0 AND 1 AND impact_score BETWEEN 0 "
            "AND 1 AND confidence_score BETWEEN 0 AND 1",
            name="ck_news_sentiment_scores",
        ),
    )
    op.create_table(
        "news_impact_assessments",
        _pk(),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("news_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("importance_score", sa.Float(), nullable=False),
        sa.Column("credibility_score", sa.Float(), nullable=False),
        sa.Column("credibility_class", sa.String(length=50), nullable=False),
        # NULL = not applicable to this item's scope (see models file).
        sa.Column("company_relevance", sa.Float(), nullable=True),
        sa.Column("sector_relevance", sa.Float(), nullable=True),
        sa.Column("market_relevance", sa.Float(), nullable=False),
        sa.Column("horizon", sa.String(length=20), nullable=False),
        sa.Column("supporting_facts", sa.JSON(), nullable=False),
        sa.Column("counterarguments", sa.JSON(), nullable=False),
        sa.Column("uncertainty", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="computed"),
        _created(),
        sa.Index("idx_news_impact_article", "article_id"),
        sa.Index("idx_news_impact_importance", "importance_score"),
        sa.CheckConstraint(
            "credibility_class IN ('official_primary', 'company_disclosure', "
            "'established_press', 'secondary_reporting', 'unverified')",
            name="ck_news_impact_credibility",
        ),
        sa.CheckConstraint(
            "importance_score BETWEEN 0 AND 1 AND credibility_score BETWEEN 0 "
            "AND 1 AND company_relevance BETWEEN 0 AND 1 AND "
            "sector_relevance BETWEEN 0 AND 1 AND market_relevance BETWEEN 0 "
            "AND 1 AND confidence BETWEEN 0 AND 1",
            name="ck_news_impact_scores",
        ),
    )
    op.create_table(
        "news_market_reactions",
        _pk(),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("news_articles.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "event_id",
            sa.BigInteger(),
            sa.ForeignKey("news_events.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pre_price", sa.Numeric(20, 6), nullable=True),
        sa.Column("event_day_price", sa.Numeric(20, 6), nullable=True),
        sa.Column("post_price", sa.Numeric(20, 6), nullable=True),
        sa.Column("returns", sa.JSON(), nullable=False),
        sa.Column("volume_change", sa.Numeric(20, 6), nullable=True),
        sa.Column("benchmark_return", sa.JSON(), nullable=False),
        sa.Column("sector_return", sa.JSON(), nullable=False),
        sa.Column("excess_return", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        _created(),
        sa.Index("idx_news_reaction_article", "article_id"),
        sa.Index("idx_news_reaction_event", "event_id"),
        sa.Index("idx_news_reaction_status", "status"),
        sa.CheckConstraint(
            "status IN ('computed', 'INSUFFICIENT_DATA')",
            name="ck_news_reaction_status",
        ),
    )
    op.create_table(
        "news_collection_runs",
        _pk(),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("run_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("run_finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("items_seen", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("items_stored", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("policy_reason", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        _created(),
        sa.Index("idx_news_runs_source", "source_key"),
        sa.Index("idx_news_runs_status", "status"),
        sa.CheckConstraint(
            "status IN ('collected', 'refused', 'failed', 'paused')",
            name="ck_news_runs_status",
        ),
    )
    op.create_table(
        "news_model_evaluations",
        _pk(),
        sa.Column("model_name", sa.String(length=200), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("dataset_name", sa.String(length=200), nullable=False),
        sa.Column("dataset_size", sa.BigInteger(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        _created(),
        sa.Index("idx_news_eval_model", "model_name"),
    )
    op.create_table(
        "news_event_evidence",
        _pk(),
        sa.Column(
            "event_id",
            sa.BigInteger(),
            sa.ForeignKey("news_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("news_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("evidence_type", sa.String(length=20), nullable=False, server_default="supports"),
        sa.Column("note", sa.Text(), nullable=True),
        _created(),
        sa.UniqueConstraint(
            "event_id", "article_id", name="uq_news_event_evidence_grain"
        ),
        sa.Index("idx_news_evidence_event", "event_id"),
        sa.Index("idx_news_evidence_article", "article_id"),
        sa.CheckConstraint(
            "evidence_type IN ('supports', 'contradicts')",
            name="ck_news_evidence_type",
        ),
    )


def downgrade() -> None:
    op.drop_table("news_event_evidence")
    op.drop_table("news_model_evaluations")
    op.drop_table("news_collection_runs")
    op.drop_table("news_market_reactions")
    op.drop_table("news_impact_assessments")
    op.drop_table("news_sentiment_assessments")
    op.drop_table("news_summaries")
    op.drop_table("news_article_entities")
    op.drop_table("news_articles")
