# Phase 19 — Grounded Research Assistant

## Answer kinds (exactly five, never mixed)

| Kind | When | Citations |
|---|---|---|
| direct_evidence | A retrieved passage answers the question | Retrieved chunks (ticker + title + page + section + chunk_id) |
| derived_calculation | The question names a computed Phase 8 metric | The calculation row (table + row id + metric + inputs + period_end), explicitly labelled "not document text" |
| inference | Not produced by any current path | — |
| uncertainty | Recommendation questions; or evidence exists but does not settle the question | Retrieved evidence marked descriptive only, or none |
| missing_data | No allowed document, or no retrieved passage | Zero citations, always |

## What the assistant never does

- Never invents a citation or claims an inaccessible document was read.
- Never answers a recommendation question with a buy/sell signal:
  Phase 15 user-facing values are WITHHELD, and the assistant states
  that plainly instead of generating a signal.
- Never presents a forecast as fact (Phase 13 abstained on every
  target), a backtest result from a single observation (Phase 17
  ruled NOT_RUNNABLE), or a decision as executable (Phase 15
  proposals are research opinions only).
- Never quotes another company's figures for a company with no
  indexed document (the HBL path: missing_data with a ticker-specific
  note, zero citations).
- Never promotes a quality status. All answers inherit UNVERIFIED.

## Questions the assistant supports (examples, verified live)

- "What was HUBC net profit for the year ended 30 June 2026?" →
  direct_evidence, HUBC p. 275 (profit_and_loss), chunk contains
  56,257,178.
- "What did HUBC auditor conclude on the consolidated statements?" →
  direct_evidence, HUBC p. 271 (auditor_opinion), chunk contains
  "true and fair view".
- "What was Nishat Mills profit or loss for nine months ended
  31 March 2025?" → direct_evidence, NML p. 37, chunk contains
  1,182,815. The nine-month figure is a LOSS (1,182,815) and must not
  be confused with FY2025 PAT 6,013,519 from DPS summaries.
- "What was OGDC profit for the six months ended 31 December 2025?" →
  direct_evidence, OGDC p. 8, chunk contains 73,019,248.
- "What is HUBC gross margin for FY2026?" → derived_calculation,
  gross_margin 0.417400 from the Phase 8 row (not document text).
- "What was HBL profit for the year ended 31 December 2025?" →
  missing_data, zero citations (HBL not indexed yet).
- "Should I buy HUBC?" → uncertainty, Phase 15 WITHHELD explanation.

## API (GET-only)

| Route | Purpose |
|---|---|
| GET `/api/v1/rag/documents` | Indexed document registry (role-filtered) |
| GET `/api/v1/rag/search?q=&role=&top_k=` | Ranked chunks with snippets |
| GET `/api/v1/rag/answer?q=&role=&top_k=` | Computed answer (writes nothing, even here) |
| GET `/api/v1/rag/benchmarks` | Cases + latest result each |
| GET `/api/v1/rag/access-audit` | Latest 100 audit rows, newest first |
| GET `/api/v1/rag/status` | Counts + honest PARTIALLY COMPLETE note + `hbl_indexed: False` + `vector_retrieval_implemented: False` |

Unknown tickers/documents return empty results with reasons, never
invented rows. The scope note on the status route states coverage,
the snippet cap, vector-not-implemented, HBL not indexed, and the
no-advice / no-forecast / no-order-path rules.
