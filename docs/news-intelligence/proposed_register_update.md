# Proposed Phase Completion Register Update (Deliverable 15)

PROPOSED TEXT ONLY — the parent consolidates the registers. This
text must not be copied into `docs/development/
PHASE_COMPLETION_REGISTER.md`, `PROJECT_EXECUTION_STATE.md`, or
`MASTER_EXECUTION_LOG.md` by this session.

---

## News Intelligence Engine (new work item, branch news-intelligence)

Verdict: PARTIALLY COMPLETE.

- Implementation: package `backend/app/services/news_intelligence/`
  (taxonomy, schema, guards, llm_adapter, collection, processing,
  impact, market_reaction, leakage, rag_news, assistant, runner,
  jobs_spec, jobs_handlers); models + migration 20261104_0025 (9
  tables); CLI `scripts/run_news_intelligence.py`; 6 GET-only API
  endpoints; 3 frontend pages + nav entry; 3 Phase 25 jobs (2
  paused, 1 active read-only digest).
- Evidence: backend suite 526 passed (468 post-batch + 58 new
  tests in the news-intelligence file); frontend vitest 11 passed;
  webpack build 30 static pages;
  scratch seed chain reproduced (470 companies, 444 prices, 118
  statements, 8 news events incl. HBL); scratch engine runs: 20
  evaluation articles stored, 8 refused collection runs, 8
  INSUFFICIENT_DATA reaction rows; N=20 evaluation measured
  (category 10/12 synthetic, entity P/R 91.7%/91.7%, sentiment
  15/20 strict, all fallback-labelled).
- BLOCKED: DPS/PSX systematic collection (Terms gate, user-owned,
  not cleared). No live collection from any source (all jobs
  paused except the read-only digest).
- UNVERIFIED: live local-model inference (hardware: 151 MB free /
  885 MB available, 4 CPUs, no GPU, no Ollama; unblocker is >=3 GB
  free + Ollama + <=1B Q4 model + measured latency/memory).
- NOT IMPLEMENTED: vector retrieval (no verified local embedding
  model); article <-> event evidence linking (table exists, 0 rows).
- Defects found and fixed in this work (8): sentiment lexicon
  case bug, two taxonomy rule-order bugs, RAG ticker-bonus-only
  returns, assistant cross-company answers, wrong schema column
  names, impact NULL relevances, SQLite Identity PKs. One finding
  recorded as a limitation (NEXT ticker collision), not fixed.
- Live Phase B state (see Phase B report): migration 0025 applied
  to live, news jobs registered on live (2 paused, 1 active),
  refused collection runs recorded on live. No live articles,
  reactions, or VERIFIED promotions were written by this engine.
- G5 human sign-off still pending; no signature claimed.
