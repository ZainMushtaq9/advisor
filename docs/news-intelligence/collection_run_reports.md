# News Collection Run Reports (Deliverable 6)

All runs below are SCRATCH database runs (`psx_intelligence_news_scratch`),
labelled as such. No live-database collection ran in Phase A.
Scratch seed chain (Phase A, post-batch-merge code):

## Scratch seed chain

| Step | Result | Counts after |
|---|---|---|
| Backup 2026-11-04T1230-PKT restore (SHA verified) + alembic to 0024 | OK | alembic 0004 -> 0024 |
| Registry import (DPS snapshot CSV, --commit) | COMMITTED | companies 470, securities 470, sectors 37, evidence 940, all UNVERIFIED |
| Price ingestion (444-row CSV, --source-key dps_market_summary_2026-11-03) | OK | market_prices 444 (one date 2026-11-03) |
| Phase 7 extraction, default 16 maps + HBL 4 maps | OK | documents 4, statements 118, line items 2,116, opinions 4 |
| Phase 10 macro | OK | macro_events 4 |
| Phase 11 news (post-batch ticker-keyed maps) | OK, verdict PARTIALLY COMPLETE | news_events 8 (4 earnings: HUBC, NML, OGDC, HBL + 4 macro), news_event_companies 4, news_sources 8, company_aliases 1,376 |

The HBL earnings event (id 4) resolves correctly under the D-04
ticker-keyed maps — the batch fix works on a fresh seed chain.

## Engine runs on scratch

| Run | Command | Result |
|---|---|---|
| Migration 0025 | `alembic upgrade head` | 0024 -> 0025, 9 tables created, verified |
| Evaluation processing | `run_news_intelligence.py process --input /tmp/news_eval.jsonl --commit` | 20 items, 20 REVIEW, 0 REJECTED, 0 UNPROCESSED, 20 stored, 0 errors (second run after defect fixes; first run failed closed on a schema bug, see test report) |
| Enforcement | `run_news_intelligence.py enforce --commit` | 8 sources checked, 8 refused runs recorded |
| Reactions | `run_news_intelligence.py reactions --commit` | 8 events, 8 rows stored, all INSUFFICIENT_DATA (see market-reaction report) |
| Digest / reconcile / quality | read-only CLI commands | digest 20 articles; reconcile: articles 20, events 8, evidence 0, runs 8 |

Note: `news_event_evidence` is 0 because no article has been
linked to a canonical Phase 11 event yet — the evaluation items
were processed as articles, not linked as evidence. Linking is a
documented next step, not a hidden gap: the table and its unique
grain exist, the linking run does not.

## What did NOT run

- No live collection from any source (all refused/paused by design).
- No Ollama model run (hardware unblocker unmet).
- No Phase 19 re-index on scratch (not needed; RAG evaluation used
  the stored article rows directly).
