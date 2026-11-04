"""Phase 19 RAG runner: index, query, benchmark, access audit.

All flows are dry-run by default; --commit writes idempotently:
- Index: documents upserted by (company, type, title); chunks
  skipped when (document, page, chunk_index) already exists.
- Answers: deduped on query_text — a repeated identical query
  returns the stored answer and writes 0 new rows.
- Benchmark cases: seeded once by case_key; results deduped on
  (case_id, run_id).
- Access audits are a log, not state: each audit run appends
  one row per (role, document) pair, so re-runs are reported as
  new audit rows, never as skipped state.

No flow fetches anything: indexing reads only the three
gitignored issuer PDFs already on disk; retrieval reads only
stored rows. No document body is ever served — only capped
snippets plus page citations.
"""

from __future__ import annotations

import os
from datetime import date

from sqlalchemy.orm import Session

from app.models.financial import (
    FinancialDocument,
    FundamentalMetricDefinition,
    FundamentalMetricValue,
)
from app.models.rag import (
    RagAccessAudit,
    RagAnswer,
    RagBenchmarkCase,
    RagBenchmarkResult,
    RagChunk,
    RagDocument,
)
from app.models.reference import Security
from app.services.rag import BENCHMARK_CASES, SEED_DOCUMENTS
from app.services.rag.access import check_access, filter_documents_for_role
from app.services.rag.assistant import (
    answer_from_calculation,
    answer_from_chunks,
)
from app.services.rag.indexing import (
    index_document_pages,
    sha256_file,
)
from app.services.rag.retrieval import search_chunks

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")

# Query phrases that map to a derived calculation (Phase 8
# metric key). A derived answer is used only when no direct
# document passage answers the question — document evidence
# outranks calculation evidence for filing questions.
DERIVED_METRIC_PHRASES: tuple[tuple[str, str], ...] = (
    ("gross margin", "gross_margin"),
    ("operating margin", "operating_margin"),
    ("net margin", "net_margin"),
    ("return on assets", "roa"),
    ("return on equity", "roe_total"),
    ("current ratio", "current_ratio"),
    ("receivables days", "receivables_days"),
    ("inventory days", "inventory_days"),
)


def _ticker_to_company_id(session: Session, ticker: str) -> int | None:
    row = session.query(Security).filter(Security.ticker == ticker).first()
    return row.company_id if row else None


def index_documents(session: Session, commit: bool) -> dict:
    """Index the three seed issuer PDFs. Returns counts and
    gaps. Never writes when commit is False."""
    docs_seen = 0
    docs_written = 0
    chunks_seen = 0
    chunks_written = 0
    chunks_flagged = 0
    empty_pages = 0
    hash_mismatches: list[dict] = []
    for seed in SEED_DOCUMENTS:
        docs_seen += 1
        pdf_path = os.path.join(REPO_ROOT, seed["storage_location"])
        if not os.path.exists(pdf_path):
            return {
                "error": f"Missing PDF for {seed['ticker']}: {seed['storage_location']}",
                "docs_seen": docs_seen,
            }
        file_hash = sha256_file(pdf_path)
        # Seeds are keyed by ticker + storage path, never by surrogate
        # ids (both document and company ids shift across fresh imports).
        seed_company_id = _ticker_to_company_id(session, seed["ticker"])
        if seed_company_id is None:
            return {
                "error": f"Unknown ticker for {seed['ticker']}: no security row",
                "docs_seen": docs_seen,
            }
        source_doc = (
            session.query(FinancialDocument)
            .filter(
                FinancialDocument.company_id == seed_company_id,
                FinancialDocument.storage_location == seed["storage_location"],
            )
            .first()
        )
        if (
            source_doc is not None
            and source_doc.content_hash
            and source_doc.content_hash != file_hash
        ):
            hash_mismatches.append(
                {
                    "ticker": seed["ticker"],
                    "stored_hash": source_doc.content_hash,
                    "file_hash": file_hash,
                    "note": (
                        "Reported, never silently fixed: the file "
                        "on disk differs from the stored hash."
                    ),
                }
            )
        doc = (
            session.query(RagDocument)
            .filter(
                RagDocument.company_id == seed_company_id,
                RagDocument.document_type == seed["document_type"],
                RagDocument.title == seed["title"],
            )
            .first()
        )
        if doc is None:
            doc = RagDocument(
                company_id=seed_company_id,
                financial_document_id=source_doc.id if source_doc is not None else None,
                title=seed["title"],
                document_type=seed["document_type"],
                storage_location=seed["storage_location"],
                content_hash=file_hash,
                page_count=seed["page_count"],
                publication_date=seed["publication_date"],
                publication_date_kind=seed["publication_date_kind"],
                access_level=seed["access_level"],
                quality_status="UNVERIFIED",
                evidence={
                    "publication_date_note": seed["publication_date_note"],
                    "source": (
                        f"financial_documents row {source_doc.id}"
                        if source_doc is not None
                        else "no matching financial_documents row"
                    ),
                },
            )
            if commit:
                session.add(doc)
                session.flush()
            docs_written += 1
        chunk_rows = index_document_pages(pdf_path, seed["ticker"])
        # Count empty pages as gaps: pages with no extractable
        # text produce no chunks; the gap is reported, not
        # filled. Page counts come from the document record.
        seen_pages = {r["page_number"] for r in chunk_rows}
        empty_pages += max(0, (seed["page_count"] or 0) - len(seen_pages))
        for row in chunk_rows:
            chunks_seen += 1
            if row["injection_flag"]:
                chunks_flagged += 1
            existing = (
                session.query(RagChunk)
                .filter(
                    RagChunk.document_id == doc.id,
                    RagChunk.page_number == row["page_number"],
                    RagChunk.chunk_index == row["chunk_index"],
                )
                .first()
            )
            if existing is not None:
                continue
            if commit:
                session.add(
                    RagChunk(
                        document_id=doc.id,
                        page_number=row["page_number"],
                        section_label=row["section_label"],
                        chunk_index=row["chunk_index"],
                        text=row["text"],
                        text_hash=row["text_hash"],
                        injection_flag=row["injection_flag"],
                        injection_note=row["injection_note"],
                        quality_status="UNVERIFIED",
                    )
                )
            chunks_written += 1
        if commit:
            session.flush()
    if commit:
        session.commit()
    return {
        "docs_seen": docs_seen,
        "docs_written": docs_written,
        "chunks_seen": chunks_seen,
        "chunks_written": chunks_written,
        "chunks_flagged": chunks_flagged,
        "empty_pages_gap": empty_pages,
        "hash_mismatches": hash_mismatches,
    }


def load_corpus(session: Session, caller_role: str) -> tuple[list[dict], list[dict]]:
    """Load (allowed chunk dicts, denied document dicts) for a
    caller role. Chunks carry their document's metadata so the
    pure search function can filter and cite."""
    documents = session.query(RagDocument).all()
    doc_dicts = [
        {
            "id": d.id,
            "company_id": d.company_id,
            "title": d.title,
            "document_type": d.document_type,
            "access_level": d.access_level,
            "publication_date": d.publication_date,
        }
        for d in documents
    ]
    allowed_docs, denied_docs = filter_documents_for_role(doc_dicts, caller_role)
    allowed_ids = {d["id"] for d in allowed_docs}
    ticker_by_company = {s.company_id: s.ticker for s in session.query(Security).all()}
    doc_by_id = {d["id"]: d for d in allowed_docs}
    chunks: list[dict] = []
    for chunk in session.query(RagChunk).all():
        if chunk.document_id not in allowed_ids:
            continue
        doc = doc_by_id[chunk.document_id]
        chunks.append(
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "ticker": ticker_by_company.get(doc["company_id"], "?"),
                "title": doc["title"],
                "document_type": doc["document_type"],
                "publication_date": doc["publication_date"],
                "page_number": chunk.page_number,
                "section_label": chunk.section_label,
                "text": chunk.text,
                "injection_flag": chunk.injection_flag,
            }
        )
    return chunks, denied_docs


def _derived_lookup(session: Session, query: str) -> dict | None:
    """Map a metric question to a computed Phase 8 value row.
    Returns an answer dict or None. A NOT_CALCULABLE (NULL)
    value is never presented as a number."""
    lowered = query.lower()
    metric_key = None
    for phrase, key in DERIVED_METRIC_PHRASES:
        if phrase in lowered:
            metric_key = key
            break
    if metric_key is None:
        return None
    import re

    tickers = set(re.findall(r"[A-Z]{2,10}\d?", query.upper()))
    definition = (
        session.query(FundamentalMetricDefinition)
        .filter(FundamentalMetricDefinition.metric_key == metric_key)
        .first()
    )
    if definition is None:
        return None
    for ticker in sorted(tickers):
        company_id = _ticker_to_company_id(session, ticker)
        if company_id is None:
            continue
        value_row = (
            session.query(FundamentalMetricValue)
            .filter(
                FundamentalMetricValue.company_id == company_id,
                FundamentalMetricValue.metric_definition_id == definition.id,
                FundamentalMetricValue.computation_status == "computed",
            )
            .order_by(FundamentalMetricValue.period_end.desc())
            .first()
        )
        if value_row is None or value_row.value is None:
            continue
        return answer_from_calculation(
            query,
            metric_key,
            ticker,
            value_row.value,
            definition.unit or "",
            {
                "table": "fundamental_metric_values",
                "row_id": value_row.id,
                "period_end": str(value_row.period_end),
                "input_statement_ids": value_row.input_statement_ids,
                "computation_status": value_row.computation_status,
            },
        )
    return None


def answer_query(
    session: Session,
    query: str,
    caller_role: str = "internal",
    top_k: int = 5,
    as_of: date | None = None,
    commit: bool = False,
) -> dict:
    """Answer one question. A question naming a computed metric
    is answered by the calculation engine FIRST (a document
    passage mentioning "gross profit" does not state the
    margin); document evidence is the fallback when no computed
    row exists; otherwise the answer is missing_data with no
    citation."""
    # Answers are deduped on (query_text, caller_role): an
    # internal answer's issuer snippets must never leak to an
    # external caller through a stored row.
    existing = (
        session.query(RagAnswer)
        .filter(
            RagAnswer.query_text == query,
            RagAnswer.caller_role == caller_role,
        )
        .first()
    )
    if existing is not None:
        return {
            "answer_kind": existing.answer_kind,
            "answer_text": existing.answer_text,
            "citations": existing.citations,
            "retrieved_chunk_ids": existing.retrieved_chunk_ids,
            "stored": True,
            "written": False,
        }
    chunks, denied = load_corpus(session, caller_role)
    # A ticker in the query that has no allowed document is a
    # missing-data answer, not a licence to search other
    # companies' documents for its figures. Only registry
    # tickers count as tickers: ordinary words must not be
    # mistaken for a company.
    import re

    registry_tickers = {s.ticker for s in session.query(Security).all()}
    query_tickers = set(re.findall(r"[A-Z]{2,10}\d?", query.upper())) & registry_tickers
    known_tickers = {c["ticker"] for c in chunks}
    asked_missing = query_tickers - known_tickers
    known_in_query = query_tickers & known_tickers
    retrieved = search_chunks(query, chunks, top_k=top_k, as_of=as_of)
    if asked_missing and not known_in_query:
        # The question names only companies with no indexed
        # document: answer missing_data even if other
        # companies' passages match generic words like
        # "profit" — quoting another company's figures as the
        # answer would be a fabrication.
        result = answer_from_chunks(query, [], ticker=sorted(asked_missing)[0])
    else:
        # Derived lookup first for metric questions (see
        # docstring); document evidence is the fallback.
        derived = _derived_lookup(session, query)
        if derived is not None:
            result = derived
        elif retrieved:
            result = answer_from_chunks(query, retrieved)
        elif asked_missing:
            result = answer_from_chunks(query, [], ticker=sorted(asked_missing)[0])
        else:
            result = answer_from_chunks(query, [])
    result["denied_documents"] = [
        {"id": d["id"], "title": d["title"], "reason": d["denial_reason"]} for d in denied
    ]
    result["stored"] = False
    result["written"] = False
    if commit:
        session.add(
            RagAnswer(
                query_text=query,
                caller_role=caller_role,
                answer_kind=result["answer_kind"],
                answer_text=result["answer_text"],
                citations=result["citations"],
                retrieved_chunk_ids=result["retrieved_chunk_ids"],
                quality_status="UNVERIFIED",
            )
        )
        session.commit()
        result["stored"] = True
        result["written"] = True
    return result


def seed_benchmark_cases(session: Session, commit: bool) -> int:
    written = 0
    for case in BENCHMARK_CASES:
        existing = (
            session.query(RagBenchmarkCase)
            .filter(RagBenchmarkCase.case_key == case["case_key"])
            .first()
        )
        if existing is not None:
            continue
        if commit:
            session.add(
                RagBenchmarkCase(
                    case_key=case["case_key"],
                    query_text=case["query_text"],
                    expected_ticker=case["expected_ticker"],
                    expected_page=case["expected_page"],
                    expected_fragment=case["expected_fragment"],
                    expected_kind=case["expected_kind"],
                )
            )
        written += 1
    if commit:
        session.commit()
    return written


def run_benchmark(
    session: Session,
    run_id: str,
    top_k: int = 5,
    caller_role: str = "internal",
    commit: bool = False,
) -> dict:
    """Run every seeded benchmark case. A direct case passes
    only when a retrieved chunk matches the expected ticker +
    page AND the chunk's full text contains the expected
    fragment (comma normalised). Traceability is page/chunk
    level, per the brief ("page-level traceability works"):
    the 500-char snippet is a redistribution-capped preview,
    not the evidence container, so snippet containment is NOT
    the criterion — table headers are dense in query tokens
    and a snippet window cannot reliably isolate one figure
    row from token heuristics alone (documented limitation;
    row-label-aware table parsing is the unblocker). A
    derived case passes only when the derived answer names
    the expected metric. A missing-data case passes only
    when the answer is missing_data with zero citations.
    Citation precision = matching citations / all citations
    (1.0 when no citation is given for a missing-data case)."""
    seed_benchmark_cases(session, commit=commit)
    cases = session.query(RagBenchmarkCase).order_by(RagBenchmarkCase.id).all()
    corpus_chunks, _ = load_corpus(session, caller_role)
    chunk_text_by_id = {c["id"]: c["text"] for c in corpus_chunks}
    results: list[dict] = []
    for case in cases:
        answer = answer_query(
            session,
            case.query_text,
            caller_role=caller_role,
            top_k=top_k,
            commit=False,
        )
        citations = answer["citations"]
        if case.expected_kind == "missing_data":
            passed = answer["answer_kind"] == "missing_data" and len(citations) == 0
            precision = 1.0 if passed else 0.0
            rank = None
            hit = passed
        elif case.expected_kind == "derived_calculation":
            matched = [c for c in citations if c.get("metric") == case.expected_fragment]
            hit = len(matched) > 0
            precision = len(matched) / len(citations) if citations else 0.0
            rank = 1 if hit else None
            passed = hit and answer["answer_kind"] == "derived_calculation"
        else:
            fragment = case.expected_fragment.replace(",", "").lower()
            rank = None
            for index, citation in enumerate(citations, start=1):
                chunk_text = chunk_text_by_id.get(citation.get("chunk_id"), "")
                if (
                    citation.get("ticker") == case.expected_ticker
                    and citation.get("page") == case.expected_page
                    and fragment in chunk_text.replace(",", "").lower()
                ):
                    rank = index
                    break
            hit = rank is not None
            matching = sum(
                1
                for c in citations
                if c.get("ticker") == case.expected_ticker
                and c.get("page") == case.expected_page
                and fragment in chunk_text_by_id.get(c.get("chunk_id"), "").replace(",", "").lower()
            )
            precision = matching / len(citations) if citations else 0.0
            passed = hit and answer["answer_kind"] == "direct_evidence"
        results.append(
            {
                "case_key": case.case_key,
                "expected_kind": case.expected_kind,
                "answer_kind": answer["answer_kind"],
                "retrieved_rank": rank,
                "hit": hit,
                "citation_precision": round(precision, 4),
                "passed": passed,
            }
        )
        if commit:
            existing = (
                session.query(RagBenchmarkResult)
                .filter(
                    RagBenchmarkResult.case_id == case.id,
                    RagBenchmarkResult.run_id == run_id,
                )
                .first()
            )
            if existing is None:
                session.add(
                    RagBenchmarkResult(
                        case_id=case.id,
                        run_id=run_id,
                        top_k=top_k,
                        retrieved_rank=rank,
                        hit=hit,
                        citation_precision=round(precision, 4),
                        passed=passed,
                        evidence={"answer_kind": answer["answer_kind"]},
                    )
                )
    if commit:
        session.commit()
    passed_count = sum(1 for r in results if r["passed"])
    recall = passed_count / len(results) if results else 0.0
    return {
        "run_id": run_id,
        "top_k": top_k,
        "cases": len(results),
        "passed": passed_count,
        "recall_at_k": round(recall, 4),
        "results": results,
    }


def run_access_audit(session: Session, commit: bool) -> dict:
    """Record one audit row per (role, document) pair. Returns
    counts of allowed vs denied decisions."""
    documents = session.query(RagDocument).all()
    allowed = 0
    denied = 0
    rows: list[dict] = []
    for role in ("internal", "external", "auditor"):
        for doc in documents:
            ok, reason = check_access(role, doc.access_level)
            if ok:
                allowed += 1
            else:
                denied += 1
            rows.append(
                {
                    "caller_role": role,
                    "document_id": doc.id,
                    "title": doc.title,
                    "decision": "allowed" if ok else "denied",
                    "reason": reason,
                }
            )
            if commit:
                session.add(
                    RagAccessAudit(
                        caller_role=role,
                        document_id=doc.id,
                        decision="allowed" if ok else "denied",
                        reason=reason,
                    )
                )
    if commit:
        session.commit()
    return {"allowed": allowed, "denied": denied, "rows": rows}
