# Phase 19 — Implementation Specification

## Scope

Research Knowledge Base and Evidence Retrieval (RAG), per the playbook
brief (lines 1448–1507). Grounded search across company filings,
official disclosures, research notes, economic documents and the
platform's own calculation evidence — descriptive and analytical only.

## What was built

| Component | Location | Notes |
|---|---|---|
| Migration 20261104_0016 | `database/migrations/versions/20261104_0016_phase_19_rag.py` | 6 tables, revises 0015, head now 0016 |
| Models | `backend/app/models/rag.py` (+ registration in `models/__init__.py`) | RagDocument, RagChunk, RagAnswer, RagBenchmarkCase, RagBenchmarkResult, RagAccessAudit |
| Indexing | `backend/app/services/rag/indexing.py` | PyMuPDF page extraction, paragraph chunks, face pages whole |
| Retrieval | `backend/app/services/rag/retrieval.py` | Deterministic scoring, no embedding model |
| Access control | `backend/app/services/rag/access.py` | Role → access-level map, fail closed |
| Assistant | `backend/app/services/rag/assistant.py` | Answer kinds, recommendation refusal |
| Runner | `backend/app/services/rag/runner.py` | Index / corpus / answer / benchmark / audit |
| CLI | `scripts/run_rag.py` | `--index`, `--query`, `--benchmark`, `--access-audit`; dry-run default |
| API (GET-only) | `backend/app/api/v1/endpoints/rag.py` | 6 GET routes, no write routes |
| Tests | `backend/tests/test_rag_phase19.py` | 21 pure tests, no DB, no network |

## Schema

- `rag_documents`: registry row per indexed document. Unique on
  (company_id, document_type, title). Carries provenance: source_url,
  file SHA-256, page count, publication date + kind
  (verified / proxy / unknown), access level, and an optional
  `supersedes_id` — a revised report is a NEW row, never an overwrite.
- `rag_chunks`: one row per page chunk. Unique on
  (document_id, page_number, chunk_index). Carries page number, section
  label, text, SHA-256 of the text, injection flag + note.
- `rag_answers`: stored answers, deduped on (query_text, caller_role).
  The role is part of the key by design: deduping on query alone would
  let an external caller retrieve a stored internal answer.
- `rag_benchmark_cases` / `rag_benchmark_results`: cases deduped on
  case_key; results deduped on (case_id, run_id).
- `rag_access_audits`: append-only log of (role, document, decision,
  reason). Re-runs append new rows; they are a log, not state.

## Design decisions (each with a reason, not a preference)

1. **No vector retrieval in this phase.** No local/open-weight
   embedding model has been verified on this host, and Phase 18
   established LLM-backed execution as unavailable. The method is
   registered (`vector`) but raises NOT_IMPLEMENTED; no embedding is
   computed, stored, or claimed. Unblocker: a verified local embedding
   model plus licence and quality checks.
2. **Face pages kept whole.** Statement faces (P&L, SFP, cash flow,
   changes in equity, auditor opinion) are indexed as one chunk per
   page (bound 12,000 chars) so table rows stay with their labels.
   Body pages split at 1,500 chars. This fixed benchmark run 1's
   split-table failures.
3. **Derived-first answering.** A question naming a computed Phase 8
   metric is answered from the calculation row first (labelled "not
   document text"); document evidence is the fallback. Quoting a
   document passage that mentions "gross profit" as if it stated the
   margin (0.4174) was benchmark run 1's derived-case failure.
4. **Snippet is a preview, not the evidence container.** Snippets are
   capped at 500 chars (redistribution discipline). Traceability is
   page/chunk level: ticker + title + page + section + chunk_id.
   Benchmark direct cases verify the chunk's full text contains the
   expected fragment. See `retrieval_method.md` for the snippet
   limitation (table headers are dense in query tokens).
5. **Access filtering in the corpus loader, not the endpoint.**
   `load_corpus` returns only chunks the caller role may see, so no
   route can leak an issuer_internal passage to an external caller.
6. **Injection-flagged chunks are excluded before scoring**, never
   cited, never followed. The scan patterns deliberately avoid
   ordinary financial wording ("the board resolved", "act as trustee")
   so legitimate passages are not quarantined.
7. **No execution path.** The endpoint file carries only
   `@router.get` decorators; a test scans application source for
   execution identifiers (0 hits required), following Phase 15.
8. **No status promotion.** New rows carry their inputs' status
   (UNVERIFIED). No VERIFIED / PARTIALLY_VERIFIED promotion anywhere.

## Not built (with reasons)

- Vector retrieval (no verified local embedding model).
- HBL document (PDF not yet downloaded; parent-owned browser task).
- Wider-company coverage (Phase 7 expansion is the unblocker).
- Row-label-aware table parsing (the snippet-precision unblocker).
- Any write route, execution route, or approval gate (none granted).
