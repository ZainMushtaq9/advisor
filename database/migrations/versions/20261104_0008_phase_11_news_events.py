"""phase_11_news_events

Revision ID: 20261104_0008
Revises: 20261104_0007
Create Date: 2026-11-04

Phase 11 (news, corporate announcements, event intelligence) tables.
The Phase 3 ``news`` table is intentionally NOT reused or altered: it
has no company link, taxonomy, source type, summary cap, match evidence
or review status, and it holds 0 rows. Phase 11 writes only here.

Copyright discipline is structural: no table below has an article-body
column. An event stores a headline (<=500), a short summary (<=280),
a canonical URL, a publisher and a content hash. Full copyrighted text
can never be stored in this schema.

Quality vocabulary CHECK mirrors migration 20261104_0003. No CSVs or
PDFs are involved; no credentials are stored anywhere.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '20261104_0008'
down_revision: Union[str, None] = '20261104_0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

QUALITY_VALUES = (
    "VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "CONFLICTED",
    "MISSING", "REJECTED", "STALE", "PENDING_REVIEW",
)


def _quality_check(table: str) -> str:
    values = ", ".join(f"'{v}'" for v in QUALITY_VALUES)
    return f"quality_status IN ({values})"


def _provenance_columns() -> list:
    return [
        sa.Column("data_source_id", sa.BigInteger(), nullable=True),
        sa.Column("source_key", sa.String(100), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "quality_status", sa.String(30), nullable=False,
            server_default="UNVERIFIED",
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "news_sources",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source_key", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("publisher", sa.String(200), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("collection_policy", sa.String(50), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("terms_note", sa.Text(), nullable=False),
        sa.Column("excerpt_limit_chars", sa.BigInteger(), nullable=False, server_default="280"),
        sa.Column("collection_status", sa.String(50), nullable=False, server_default="not_collected"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key", name="uq_news_sources_key"),
    )
    op.create_index("idx_news_sources_policy", "news_sources", ["collection_policy"])

    op.create_table(
        "company_aliases",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("alias_normalized", sa.String(300), nullable=False),
        sa.Column("alias_type", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_ambiguous", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("company_id", "alias_normalized", name="uq_company_aliases_grain"),
    )
    op.create_index("idx_company_aliases_alias", "company_aliases", ["alias_normalized"])
    op.create_index("idx_company_aliases_company", "company_aliases", ["company_id"])

    op.create_table(
        "news_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *_provenance_columns(),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("date_status", sa.String(20), nullable=False, server_default="known"),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("headline", sa.String(500), nullable=False),
        sa.Column("summary", sa.String(280), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("publisher", sa.String(200), nullable=True),
        sa.Column("source_id", sa.BigInteger(), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("canonical_key", sa.String(500), nullable=False),
        sa.Column("primary_company_id", sa.BigInteger(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("review_status", sa.String(50), nullable=False, server_default="pending_review"),
        sa.Column("match_evidence", sa.JSON(), nullable=True),
        sa.Column("macro_event_id", sa.BigInteger(), nullable=True),
        sa.Column("document_id", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["primary_company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["macro_event_id"], ["macro_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_id"], ["financial_documents.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("canonical_key", name="uq_news_events_canonical"),
        sa.CheckConstraint(_quality_check("news_events"), name="ck_news_events_quality"),
    )
    op.create_index(
        "uq_news_events_content_hash", "news_events", ["content_hash"],
        unique=True, postgresql_where=sa.text("content_hash IS NOT NULL"),
    )
    op.create_index("idx_news_events_date", "news_events", ["event_date"])
    op.create_index("idx_news_events_type", "news_events", ["event_type"])
    op.create_index("idx_news_events_company", "news_events", ["primary_company_id"])
    op.create_index("idx_news_events_review", "news_events", ["review_status"])

    op.create_table(
        "news_event_companies",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("event_id", sa.BigInteger(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("match_type", sa.String(50), nullable=False),
        sa.Column("match_confidence", sa.Float(), nullable=False),
        sa.Column("match_evidence", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["event_id"], ["news_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("event_id", "company_id", name="uq_news_event_companies_grain"),
    )
    op.create_index("idx_news_event_companies_event", "news_event_companies", ["event_id"])

    op.create_table(
        "news_event_links",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("event_id", sa.BigInteger(), nullable=False),
        sa.Column("linked_event_id", sa.BigInteger(), nullable=False),
        sa.Column("relation", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["event_id"], ["news_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["linked_event_id"], ["news_events.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "event_id", "linked_event_id", "relation", name="uq_news_event_links_grain"
        ),
    )
    op.create_index("idx_news_event_links_event", "news_event_links", ["event_id"])


def downgrade() -> None:
    op.drop_table("news_event_links")
    op.drop_table("news_event_companies")
    op.drop_table("news_events")
    op.drop_table("company_aliases")
    op.drop_table("news_sources")
