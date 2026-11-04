# Phase 19 — Run Report (2026-11-04)

## Verdict: PARTIALLY COMPLETE

The benchmark gate passes fully (6/6, recall@5 = 1.0) and page-level
traceability works, but the phase is PARTIALLY COMPLETE because
coverage is 3 companies, vector retrieval is not implemented, HBL
is pending, and every input stays UNVERIFIED. The benchmark pass
and the phase verdict are different things and are not conflated.

## Acceptance gate (brief, all mandatory)

| Gate item | Status |
|---|---|
| Answers cite actual retrieved passages | PASS (chunk-level; see snippet limitation in `retrieval_method.md`) |
| Page-level traceability works | PASS (ticker + title + page + section + chunk_id on every citation) |
| No unlicensed documents redistributed | PASS (snippets ≤ 500 chars, no body served, PDFs gitignored) |
| Prompt-injection tests pass | PASS (fixture tests; 0 production flagged chunks, stated honestly) |
| Access-control tests pass | PASS (pure tests + live audit: external/auditor denied issuer_internal) |

## DB counts (live DB, before → after)

| Table | Before | After |
|---|---|---|
| rag_documents | 0 | 3 |
| rag_chunks | 0 | 943 (was 953 before the face-page re-index; derived rows truncated once after chunk boundaries changed, documents untouched) |
| rag_chunks injection-flagged | 0 | 0 |
| rag_answers | 0 | 0 (answers computed on demand; benchmark uses commit=False for answers) |
| rag_benchmark_cases | 0 | 6 |
| rag_benchmark_results | 0 | 18 (6 each for r1, r2, r3; history preserved) |
| rag_access_audits | 0 | 9 |
| All prior tables (statements 88, prices 444, fundamental values 108, valuations 51, decisions 4, simulated portfolios 3, backtest runs 5, orchestration runs 1) | — | Unchanged |

Migration head: 20261104_0015 → 20261104_0016.

## Index runs

- Dry-run: 3 docs, 953 chunks, 0 flagged, 16 empty-page gaps, 0 hash
  mismatches.
- Commit: same counts.
- Re-index after the face-page correction (chunks truncated once,
  documents idempotent): 3 docs seen / 0 written, 943 chunks,
  0 flagged, 16 gaps, 0 hash mismatches.
- Idempotency re-proof: second `--index --commit` wrote 0 docs and
  0 chunks; second `--benchmark --commit` with run_id r3 added 0
  results (total stayed 18).
- Hash note: `hash_mismatches` was empty because no stored
  `financial_documents.content_hash` differed at comparison time.
  This is NOT a claim of independent re-verification against the
  Phase 7 SHA-256 values — do not over-claim it.

## Tests

- Pure Phase 19 suite: 21 passed.
- Full backend suite: 293 passed (272 prior + 21 new), 0 failed.
- Ruff check + format: clean on all Phase 19 files.
- Live API check (TestClient, all 7 GET routes): 200 — documents 3,
  search 5 results, answer direct_evidence 5 citations,
  recommendation answer uncertainty, access-audit 9 rows, status
  counts. The answer endpoint writes nothing.
- No-execution-path scan: 0 hits (same idiom as Phase 15).

## What did NOT compute (with reasons)

| Output | Status | Reason |
|---|---|---|
| Vector retrieval | NOT_IMPLEMENTED | No verified local embedding model on this host |
| HBL answers | missing_data | HBL CY2025 PDF not yet downloaded (parent browser task) |
| Wider-company answers | missing_data | Only 3 companies indexed (Phase 7 expansion unblocker) |
| Figure-level snippet precision | Limited | Table-header token density (row-label-aware parsing is the unblocker) |
| Any VERIFIED promotion | Never | H1 needs a second agreeing source including an official source; no approval gate granted |
| Inference answers | Not produced | No current path produces them; uncertainty/missing_data instead |

## Remaining blockers (exact unblockers)

1. Wider-company / KSE-100 expansion — Phase 7 expansion beyond the
   3-company sample (per-company source verification pass).
2. HBL coverage — live-browser HBL CY2025 PDF download (parent-owned
   browser task), then a Phase 7 load, then a Phase 19 re-index +
   re-run with HBL added.
3. Vector retrieval — a verified local/open-weight embedding model
   plus licence and quality checks.
4. VERIFIED promotion — H1 second agreeing source including an
   official source, plus a recorded human approval gate (none granted).
5. CI-in-CI — a main/development push or PR (separate approval;
   remote/local main have unrelated histories; no PR exists).
