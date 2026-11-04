"""phase_19_rag

Revision ID: 20261104_0016
Revises: 20261104_0015
Create Date: 2026-11-04

Phase 19 (research knowledge base and evidence retrieval / RAG)
tables: rag_documents (document registry with provenance),
rag_chunks (page-level chunks with injection flags),
rag_answers (grounded answers with citations and evidence kind),
rag_benchmark_cases (seeded retrieval cases with expected
passages), rag_benchmark_results (per-run recall / citation
precision), rag_access_audits (access-control decisions).

Precedent note (Phases 11-18): Phase 19 stores its own tables
rather than retrofitting Phase 3 tables. No Phase 3 RAG table
exists. No CSVs or PDFs are committed by this migration; the
indexed PDFs stay gitignored under storage/financial_reports/
and only page-level citations and capped snippets are served,
never full document bodies — no unlicensed document is
redistributed. No credentials are stored anywhere.

Quality vocabulary CHECK mirrors migration 20261104_0003.
Chunks carry their own quality_status (UNVERIFIED unless the
source document's verification is established elsewhere); a
retrieved passage never upgrades a statement, price, or
calculation row. No execution concept exists in these tables:
retrieval and answering are read-only over stored rows.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261104_0016"
down_revision: str | None = "20261104_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

QUALITY_VALUES = (
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "UNVERIFIED",
    "CONFLICTED",
    "MISSING",
    "REJECTED",
    "STALE",
    "PENDING_REVIEW",
)

ACCESS_LEVELS = (
    "official_public",
    "issuer_internal",
    "platform_internal",
)

ANSWER_KINDS = (
    "direct_evidence",
    "derived_calculation",
    "inference",
    "uncertainty",
    "missing_data",
)


def _quality_check(table: str, column: str = "quality_status") -> sa.CheckConstraint:
    values = ", ".join(f"'{v}'" for v in QUALITY_VALUES)
    return sa.CheckConstraint(f"{column} IN ({values})", name=f"ck_{table}_{column}")


def upgrade() -> None:
    op.create_table(
        "rag_documents",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("data_source_id", sa.BigInteger(), nullable=True),
        sa.Column("source_key", sa.String(length=100), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "quality_status", sa.String(length=30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.Column("version_number", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("supersedes_id", sa.BigInteger(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("financial_document_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("storage_location", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("page_count", sa.BigInteger(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column(
            "publication_date_kind", sa.String(length=30), nullable=False, server_default="unknown"
        ),
        sa.Column(
            "access_level", sa.String(length=30), nullable=False, server_default="issuer_internal"
        ),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default="{}"),
        sa.CheckConstraint(
            "access_level IN ('official_public', 'issuer_internal', 'platform_internal')",
            name="ck_rag_documents_access_level",
        ),
        sa.CheckConstraint(
            "publication_date_kind IN ('verified', 'proxy', 'unknown')",
            name="ck_rag_documents_publication_date_kind",
        ),
        _quality_check("rag_documents"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "document_type",
            "title",
            name="uq_rag_documents_company_type_title",
        ),
    )
    op.create_index("ix_rag_documents_company", "rag_documents", ["company_id"])

    op.create_table(
        "rag_chunks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "quality_status", sa.String(length=30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("page_number", sa.BigInteger(), nullable=False),
        sa.Column("section_label", sa.String(length=200), nullable=False, server_default="body"),
        sa.Column("chunk_index", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("injection_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("injection_note", sa.Text(), nullable=True),
        _quality_check("rag_chunks"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["rag_documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "document_id",
            "page_number",
            "chunk_index",
            name="uq_rag_chunks_doc_page_index",
        ),
    )
    op.create_index("ix_rag_chunks_document", "rag_chunks", ["document_id"])
    op.create_index(
        "ix_rag_chunks_document_page",
        "rag_chunks",
        ["document_id", "page_number"],
    )

    op.create_table(
        "rag_answers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "quality_status", sa.String(length=30), nullable=False, server_default="UNVERIFIED"
        ),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("caller_role", sa.String(length=50), nullable=False, server_default="internal"),
        sa.Column("answer_kind", sa.String(length=30), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("retrieved_chunk_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("company_id", sa.BigInteger(), nullable=True),
        sa.CheckConstraint(
            "answer_kind IN ('direct_evidence', 'derived_calculation', "
            "'inference', 'uncertainty', 'missing_data')",
            name="ck_rag_answers_answer_kind",
        ),
        _quality_check("rag_answers"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rag_benchmark_cases",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("case_key", sa.String(length=100), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("expected_ticker", sa.String(length=20), nullable=True),
        sa.Column("expected_page", sa.BigInteger(), nullable=True),
        sa.Column("expected_fragment", sa.Text(), nullable=False),
        sa.Column("expected_kind", sa.String(length=30), nullable=False),
        sa.CheckConstraint(
            "expected_kind IN ('direct_evidence', 'derived_calculation', "
            "'inference', 'uncertainty', 'missing_data')",
            name="ck_rag_benchmark_cases_expected_kind",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_key", name="uq_rag_benchmark_cases_key"),
    )

    op.create_table(
        "rag_benchmark_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("case_id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("top_k", sa.BigInteger(), nullable=False),
        sa.Column("retrieved_rank", sa.BigInteger(), nullable=True),
        sa.Column("hit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("citation_precision", sa.Numeric(10, 4), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["case_id"], ["rag_benchmark_cases.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_rag_benchmark_results_run", "rag_benchmark_results", ["run_id"])

    op.create_table(
        "rag_access_audits",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("caller_role", sa.String(length=50), nullable=False),
        sa.Column("document_id", sa.BigInteger(), nullable=True),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "decision IN ('allowed', 'denied')",
            name="ck_rag_access_audits_decision",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["rag_documents.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("rag_access_audits")
    op.drop_table("rag_benchmark_results")
    op.drop_table("rag_benchmark_cases")
    op.drop_table("rag_answers")
    op.drop_table("rag_chunks")
    op.drop_table("rag_documents")
