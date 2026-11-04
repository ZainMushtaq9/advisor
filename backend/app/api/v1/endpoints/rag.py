"""Phase 19 RAG read-only endpoints (GET only).

Everything here is read from stored rows or explained as absent
with a reason. No value is ever fabricated, and no endpoint
writes anything — including /answer, which serves a stored
answer when one exists and otherwise computes one in memory
without persisting it. Unknown tickers and unknown documents
return 404-style empty results with reasons, never invented
rows. Snippets are capped at 500 characters: no document body
is ever served, so no unlicensed document is redistributed.
Nothing here is investment advice, a buy/sell signal, or a
forecast: Phase 15 user-facing values are WITHHELD, Phase 13
forecasts are abstained, and this assistant does not reintroduce
either. No order path exists anywhere in this project.

Endpoints:
  GET /api/v1/rag/documents
      The indexed document registry with provenance.
  GET /api/v1/rag/search?q=...&role=internal&top_k=5
      Hybrid retrieval over stored chunks (injection-flagged
      chunks never returned).
  GET /api/v1/rag/answer?q=...&role=internal&top_k=5
      One grounded answer with citations and evidence kind
      (computed in memory, not stored, by this endpoint).
  GET /api/v1/rag/benchmarks
      Seeded benchmark cases with their latest results.
  GET /api/v1/rag/access-audit
      Recorded access-control decisions.
  GET /api/v1/rag/status
      Coverage counts and the honest Phase 19 summary.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.database import get_session_factory
from app.models.rag import (
    RagAccessAudit,
    RagAnswer,
    RagBenchmarkCase,
    RagBenchmarkResult,
    RagChunk,
    RagDocument,
)
from app.services.rag import RETRIEVAL_METHODS
from app.services.rag.retrieval import search_chunks
from app.services.rag.runner import answer_query, load_corpus

router = APIRouter(tags=["rag"])

SCOPE_NOTE = (
    "Scope: grounded retrieval over the three indexed issuer "
    "reports (HUBC, NML, OGDC) plus platform calculation rows. "
    "Answers cite actual retrieved passages to ticker + title + "
    "page + section, or state missing data with no citation. "
    "Snippets are capped at 500 characters; no document body is "
    "served. Vector retrieval is registered but not implemented "
    "(no verified local embedding model). HBL has no indexed "
    "document (its statements are not loaded). Nothing here is "
    "investment advice, a buy/sell signal, or a forecast. No "
    "order path exists."
)


def _session(request: Request):
    factory = get_session_factory(request.app.state.engine)
    return factory()


@router.get("/rag/documents")
def list_documents(request: Request):
    session = _session(request)
    try:
        docs = session.query(RagDocument).order_by(RagDocument.id).all()
        return {
            "scope": SCOPE_NOTE,
            "documents": [
                {
                    "id": d.id,
                    "company_id": d.company_id,
                    "title": d.title,
                    "document_type": d.document_type,
                    "storage_location": d.storage_location,
                    "page_count": d.page_count,
                    "publication_date": str(d.publication_date) if d.publication_date else None,
                    "publication_date_kind": d.publication_date_kind,
                    "access_level": d.access_level,
                    "quality_status": d.quality_status,
                }
                for d in docs
            ],
        }
    finally:
        session.close()


@router.get("/rag/search")
def search(request: Request, q: str, role: str = "internal", top_k: int = 5):
    session = _session(request)
    try:
        chunks, denied = load_corpus(session, role)
        results = search_chunks(q, chunks, top_k=top_k)
        return {
            "scope": SCOPE_NOTE,
            "query": q,
            "role": role,
            "results": [r.citation() | {"score": r.score} for r in results],
            "denied_documents": [
                {"id": d["id"], "title": d["title"], "reason": d["denial_reason"]} for d in denied
            ],
            "methods": {name: meta["implemented"] for name, meta in RETRIEVAL_METHODS.items()},
        }
    finally:
        session.close()


@router.get("/rag/answer")
def answer(request: Request, q: str, role: str = "internal", top_k: int = 5):
    session = _session(request)
    try:
        result = answer_query(session, q, caller_role=role, top_k=top_k, commit=False)
        result["scope"] = SCOPE_NOTE
        return result
    finally:
        session.close()


@router.get("/rag/benchmarks")
def benchmarks(request: Request):
    session = _session(request)
    try:
        cases = session.query(RagBenchmarkCase).order_by(RagBenchmarkCase.id).all()
        out = []
        for case in cases:
            latest = (
                session.query(RagBenchmarkResult)
                .filter(RagBenchmarkResult.case_id == case.id)
                .order_by(RagBenchmarkResult.id.desc())
                .first()
            )
            out.append(
                {
                    "case_key": case.case_key,
                    "query": case.query_text,
                    "expected_ticker": case.expected_ticker,
                    "expected_page": case.expected_page,
                    "expected_kind": case.expected_kind,
                    "latest": (
                        {
                            "run_id": latest.run_id,
                            "retrieved_rank": latest.retrieved_rank,
                            "hit": latest.hit,
                            "citation_precision": str(latest.citation_precision),
                            "passed": latest.passed,
                        }
                        if latest
                        else None
                    ),
                }
            )
        return {"scope": SCOPE_NOTE, "cases": out}
    finally:
        session.close()


@router.get("/rag/access-audit")
def access_audit(request: Request):
    session = _session(request)
    try:
        rows = session.query(RagAccessAudit).order_by(RagAccessAudit.id.desc()).limit(100).all()
        return {
            "scope": SCOPE_NOTE,
            "audits": [
                {
                    "caller_role": r.caller_role,
                    "document_id": r.document_id,
                    "decision": r.decision,
                    "reason": r.reason,
                }
                for r in rows
            ],
        }
    finally:
        session.close()


@router.get("/rag/status")
def status(request: Request):
    session = _session(request)
    try:
        docs = session.query(RagDocument).count()
        chunks = session.query(RagChunk).count()
        flagged = session.query(RagChunk).filter(RagChunk.injection_flag.is_(True)).count()
        answers = session.query(RagAnswer).count()
        cases = session.query(RagBenchmarkCase).count()
        return {
            "scope": SCOPE_NOTE,
            "documents": docs,
            "chunks": chunks,
            "injection_flagged_chunks": flagged,
            "stored_answers": answers,
            "benchmark_cases": cases,
            "vector_retrieval_implemented": RETRIEVAL_METHODS["vector"]["implemented"],
            "hbl_indexed": False,
            "note": (
                "PARTIALLY COMPLETE expected: 3-company coverage, "
                "vector retrieval not implemented (no verified "
                "local embedding model), HBL pending."
            ),
        }
    finally:
        session.close()
