"""Phase 19 research knowledge base and evidence retrieval (RAG) models.

Six tables. Design rules from the Phase 19 brief:

- Document registry with provenance: every indexed document keeps
  its source, content hash, page count, publication date (with a
  kind label: verified, proxy, or unknown — a proxy date is never
  presented as a verified publication date), access level, and
  company link. Only permitted documents are indexed: the three
  issuer reports already held for internal analysis (HUBC, NML,
  OGDC). DPS-hosted filings are NOT indexed (discovery only,
  filing-download terms not established). No document body is
  redistributed: retrieval serves capped snippets (<= 500 chars)
  plus page-level citations, never full pages or full documents.
- Chunks are page-level: chunking splits by document structure
  and page, preserving tables and reporting context through the
  section label (face pages carry their Phase 7 face label).
  Exact identifiers/tickers are indexed as tokens alongside the
  text, so a ticker query resolves deterministically.
- Injection discipline (Phase 18 precedent): document text is
  data, never instructions. A chunk carrying instructional
  language is flagged, excluded from retrieval, and recorded —
  never followed, never cited as evidence.
- Answers distinguish direct evidence, derived calculation,
  inference, uncertainty, and missing data. A missing-data
  answer carries NO citation: inventing a citation is a failure
  mode, not a fallback.
- Vector retrieval is registered but NOT implemented: no local
  embedding model has been verified on this host (Phase 18
  established LLM-backed execution as unavailable). The hybrid
  retrieval that runs is full-text + metadata + exact-identifier
  matching, all deterministic and dependency-free.
- Quality vocabulary mirrors migration 20261104_0003. A retrieved
  passage never upgrades a statement, price, calculation, or
  decision row.
- No order path exists anywhere in this project, and none is
  added here: retrieval and answering are read-only over stored
  rows.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RagDocument(Base):
    __tablename__ = "rag_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    company_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    financial_document_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    page_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    publication_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    publication_date_kind: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unknown"
    )
    access_level: Mapped[str] = mapped_column(String(30), nullable=False, default="issuer_internal")
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")
    version_number: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    supersedes_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        CheckConstraint(
            "access_level IN ('official_public', 'issuer_internal', 'platform_internal')",
            name="ck_rag_documents_access_level",
        ),
        CheckConstraint(
            "publication_date_kind IN ('verified', 'proxy', 'unknown')",
            name="ck_rag_documents_publication_date_kind",
        ),
        CheckConstraint(
            "quality_status IN ('VERIFIED', 'PARTIALLY_VERIFIED', "
            "'UNVERIFIED', 'CONFLICTED', 'MISSING', 'REJECTED', "
            "'STALE', 'PENDING_REVIEW')",
            name="ck_rag_documents_quality_status",
        ),
        UniqueConstraint(
            "company_id",
            "document_type",
            "title",
            name="uq_rag_documents_company_type_title",
        ),
        Index("ix_rag_documents_company", "company_id"),
    )


class RagChunk(Base):
    __tablename__ = "rag_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    section_label: Mapped[str] = mapped_column(String(200), nullable=False, default="body")
    chunk_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    injection_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    injection_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")

    __table_args__ = (
        CheckConstraint(
            "quality_status IN ('VERIFIED', 'PARTIALLY_VERIFIED', "
            "'UNVERIFIED', 'CONFLICTED', 'MISSING', 'REJECTED', "
            "'STALE', 'PENDING_REVIEW')",
            name="ck_rag_chunks_quality_status",
        ),
        UniqueConstraint(
            "document_id",
            "page_number",
            "chunk_index",
            name="uq_rag_chunks_doc_page_index",
        ),
        Index("ix_rag_chunks_document", "document_id"),
        Index("ix_rag_chunks_document_page", "document_id", "page_number"),
    )


class RagAnswer(Base):
    __tablename__ = "rag_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    caller_role: Mapped[str] = mapped_column(String(50), nullable=False, default="internal")
    answer_kind: Mapped[str] = mapped_column(String(30), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    retrieved_chunk_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    company_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")

    __table_args__ = (
        CheckConstraint(
            "answer_kind IN ('direct_evidence', 'derived_calculation', "
            "'inference', 'uncertainty', 'missing_data')",
            name="ck_rag_answers_answer_kind",
        ),
        CheckConstraint(
            "quality_status IN ('VERIFIED', 'PARTIALLY_VERIFIED', "
            "'UNVERIFIED', 'CONFLICTED', 'MISSING', 'REJECTED', "
            "'STALE', 'PENDING_REVIEW')",
            name="ck_rag_answers_quality_status",
        ),
    )


class RagBenchmarkCase(Base):
    __tablename__ = "rag_benchmark_cases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    case_key: Mapped[str] = mapped_column(String(100), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_ticker: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expected_page: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    expected_fragment: Mapped[str] = mapped_column(Text, nullable=False)
    expected_kind: Mapped[str] = mapped_column(String(30), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "expected_kind IN ('direct_evidence', 'derived_calculation', "
            "'inference', 'uncertainty', 'missing_data')",
            name="ck_rag_benchmark_cases_expected_kind",
        ),
        UniqueConstraint("case_key", name="uq_rag_benchmark_cases_key"),
    )


class RagBenchmarkResult(Base):
    __tablename__ = "rag_benchmark_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    case_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("rag_benchmark_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    top_k: Mapped[int] = mapped_column(BigInteger, nullable=False)
    retrieved_rank: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    citation_precision: Mapped[object | None] = mapped_column(Numeric(10, 4), nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (Index("ix_rag_benchmark_results_run", "run_id"),)


class RagAccessAudit(Base):
    __tablename__ = "rag_access_audits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    caller_role: Mapped[str] = mapped_column(String(50), nullable=False)
    document_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("rag_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "decision IN ('allowed', 'denied')",
            name="ck_rag_access_audits_decision",
        ),
    )
