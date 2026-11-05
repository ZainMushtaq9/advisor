# News Intelligence Engine — Implementation Plan (Phase A)

Branch: `news-intelligence`, from `phase-30-release` 8937338 (plus the
HBL extraction cherry-pick 42bd8e2, applied cleanly as 56df2de, so the
scratch seed chain can reproduce the HBL statements; no PDF committed).
Phase A works against a SCRATCH database only
(`psx_intelligence_news_scratch`, restored from backup
2026-11-04T1230-PKT, manifest SHA verified, migrated to head
20261104_0024). NO live-database writes in Phase A. Phase B (live
seed/commit) is gated on the parent's explicit HBL-batch-completion
follow-up.

## 1. Repository audit (verified from code, not assumed)

- Phase 11 (`backend/app/services/news_events/`, migration 0008):
  8 sources in the registry dict, 5 tables (news_sources,
  company_aliases, news_events, news_event_companies,
  news_event_links). Seed events derive ONLY from stored Phase 7
  documents + Phase 10 macro events; no HTTP fetch. The PSX collector
  is a gated stub raising `PolicyBlocked`. No article-body column
  anywhere; summaries capped at 280 chars; no sentiment stored or
  served; scores are review-worthiness only. Coverage 3/470.
- Phase 19 RAG (`backend/app/services/rag/`): deterministic full-text
  + metadata + exact-identifier retrieval, one chunk per page dedup,
  snippets capped at 500 chars, injection-flagged chunks never
  returned. Vector retrieval REGISTERED BUT NOT IMPLEMENTED (no
  verified local embedding model). Assistant answer kinds:
  direct_evidence / derived_calculation / inference / uncertainty /
  missing_data; recommendation questions get uncertainty, never a
  signal.
- Phase 25 jobs (`backend/app/services/jobs/`): DB-backed,
  single-pass, operator-invoked framework; NO daemon, NO paid
  scheduler. Collection handlers are explicit stubs raising
  `CollectionNotImplemented`; the 3 collection jobs are PAUSED and
  the runner refuses paused jobs. Any news collection job follows
  the same rule: PAUSED with an exact reason until its source is
  permitted AND automated fetching is approved.
- Phase 18 orchestration: 16 agents, rule-based fallback only;
  LLM-backed execution UNAVAILABLE (no verified local model).
- Phase 26 evaluation: 9 model cards ALL NOT_PROMOTED, 5 gates ALL
  NOT_MET. Phase 27 observability: 14 SLOs (10 met, 4 unmet).
- Phase 15 decisions: 4 decisions, ALL user-facing WITHHELD.
  Phase 13 forecasts: 120 assessments, ALL insufficient,
  0 predictions. News-forecast integration therefore cannot claim
  improvement: it enforces cutoffs, keeps snapshots immutable, and
  reports INSUFFICIENT_DATA where evidence is insufficient.
- Tests never touch real PostgreSQL or network (conftest). New tests
  follow the same rule: pure unit tests + SQLite in-memory model
  tests. No new dependencies: the backend venv has no torch,
  transformers, requests, or feedparser — the engine uses stdlib
  only (urllib, xml.etree, json, re, decimal), so no new pins and
  no licence-gate changes.

## 2. Competitor feature matrix (public features only, researched 2026-11-05)

| Platform | Public features observed | Adopt / note for this project |
|---|---|---|
| PSX Invest | AI stock briefings with BUY/SELL/HOLD + confidence + target/stop-loss, 4 ML models, 14 chart patterns, intraday signals, watchlists, macro-adjusted signals, backtests with win rates, WhatsApp alerts, paid tiers (PKR 199–6,000/mo) | Adopt: calibrated-confidence idea (only with measured calibration), macro context, watchlists, backtest honesty. DELIBERATELY NOT ADOPTED: executable BUY/SELL signals with targets/stops (this project withholds user-facing decisions and never issues price targets); paid tiers (PKR 0 rule); WhatsApp delivery (in-app only) |
| Sarmaaya / Zar | Portfolio tracking incl. mutual funds/ETFs/gold/forex, watchlists + real-time alerts, KSE-100 benchmarking, CGT/Zakat/FMR filer reports, SCAN stock discovery, workshops | Adopt: benchmark comparison, payout histories, watchlist alerts. Not adopted: real-money portfolio execution, filer-specific tax products (out of scope) |
| Investify | Live prices, charts to 5y, fundamentals in plain words, 32-indicator technical summary, announcement summaries with original PDF a tap away, business-news aggregation (Dawn, Tribune, Profit), Shariah flags, demo trading | Adopt: announcement summaries linked to originals, plain-words fundamentals, per-stock news tab. Not adopted: demo trading, live prices (Terms-gated) |
| Zaryaab / PSX Swing / Capitalist | (Public store/feature pages reviewed; no distinctive news-intelligence feature beyond screening/signals found in this pass) | No feature adopted beyond the matrix rows above; recorded as reviewed, not copied |
| Business Recorder / Dawn Business / Mettis Global / Profit / Reuters | News publishing: earnings, corporate actions, sector news, macro/policy coverage; third-party reports note free RSS feeds for Business Recorder and Dawn Business | Adopt: NOTHING as a collection source until direct terms/robots verification (see §3). Their public feature shape (section feeds, per-company coverage) informs the dashboard IA only |

No proprietary code, branding, protected content, or private data was
copied. Competitor signal/target/stop-loss behaviour is a deliberate
non-goal here, not a gap to close.

## 3. Source permission and compliance register (summary)

Full register: `source_permission_register.md`. Decisive outcomes:

- **PSX DPS announcements — BLOCKED (permission).** PSX Terms of Use
  + Data Legal Notice prohibit systematic retrieval to create
  collections/databases except with prior written permission, prohibit
  automated access except generally available third-party browsers
  unless prior written permission, and prohibit redistribution /
  republication / commercial use of Market Data without the
  respective rights/licence (contact marketdatarequest@psx.com.pk).
  Permission request sent 2026-11-04 from 5439; reply wording is
  unverifiable (user deleted it including from trash) and does NOT
  clear the gate; no resend sent. The collection layer enforces this
  in code: the DPS collector raises `PolicyBlocked` and the
  permission gate refuses any DPS collection job. No mirror, cache,
  or "just a little" collection — that is still systematic
  retrieval.
- **SBP / PBS press releases — manual reads ALLOWED, automated
  collection PAUSED.** Phase 10 established direct official reads.
  But Phase 25's macro job stays PAUSED because no automated fetch
  is approved. The engine therefore implements the collection code
  and the permission gate, but registers its SBP/PBS jobs PAUSED
  with that exact reason. A scheduled job existing does not prove
  daily collection works.
- **SECP public pages — sampled manual only.** Public pages only, no
  bulk route, no paid eServices account (Rs. 100 route explicitly
  not used). Automated collection BLOCKED pending a documented
  public route.
- **Finance Division — UNVERIFIED.** No prior project evidence;
  no collection until reviewed.
- **Issuer IR pages — ALLOWED sampled, manual only.** Phase 7 source
  matrix: sampled, internal analysis only, no republication.
  Automated polling NOT approved (Phase 25 filing job stays
  PAUSED).
- **Business Recorder / Dawn Business / Mettis Global / Profit /
  Reuters — NOT_COLLECTED (terms unreviewed).** Third-party reports
  mention free RSS feeds for Business Recorder and Dawn Business,
  but that is NOT direct verification of terms, robots, or RSS
  permission, so no collection is implemented for them. Unblocker:
  direct terms + robots.txt + RSS-permission verification per
  outlet, recorded in the register. Summaries, if ever collected,
  are capped excerpts with canonical links — never full article
  bodies (the schema has no body column, by design).
- **Social / rumour channels — EXCLUDED.** Never stored as events
  (Phase 11 rule, carried forward).

## 4. LLM layer: measure, never assume

Hardware measured 2026-11-05 (see `model_selection_report.md`):
4 CPUs, 7.7 GB RAM (only ~0.5 GB free at measurement time under the
load of two concurrent coordinators), no GPU, no Ollama installed,
no torch/transformers in the venv, 143 GB disk free. A local
instruction model is therefore NOT started during Phase A: a ~1B
Q4 model needs ~1 GB plus runtime overhead, and starting it under
current load risks OOM-killing concurrent work. The honest status
is: adapter + schema validation + deterministic fallback
implemented and tested; live local-model inference UNVERIFIED
with the exact unblocker (≥2 GB free RAM, install Ollama, pull a
≤1B Q4 open-weight instruction model, measure latency/memory).
- Provider-independent adapter (`llm_adapter.py`): `LLMAdapter`
  protocol; `OllamaAdapter` (stdlib HTTP to localhost, no keys);
  `DeterministicFallback` (rule-based, labelled RULE_BASED, never
  presented as LLM output); `NullAdapter` (raises when no model is
  configured). Changing the local model never redesigns the
  pipeline.
- Strict JSON schema (`schema.py`): the prompt §4 field list is
  enforced; malformed output is rejected; unknown tickers are
  rejected (whitelist = registry tickers passed in); scores must
  be in [0, 1]; required fields must be present. Hallucination
  guards (`guards.py`): extracted facts must be grounded in the
  input text or flagged unverified; no invented source is ever
  accepted as verified information.
- The LLM NEVER performs authoritative financial calculations —
  all financial math is deterministic Python with Decimal
  (`market_reaction.py`, reusing Phase 8/9/12 conventions).
- Sentiment is NOT a price prediction. No percentage impact
  estimates are fabricated. Sentiment, importance, credibility,
  relevance, actual market reaction, and forecast output are kept
  SEPARATE. Where evidence is insufficient, the result is
  INSUFFICIENT_DATA.

## 5. Architecture

New package `backend/app/services/news_intelligence/`:

| Module | Responsibility |
|---|---|
| `taxonomy.py` | Event taxonomy (prompt §5), configurable entries, Phase 11 type mapping |
| `schema.py` | Strict LLM output JSON schema + validation |
| `llm_adapter.py` | Provider-independent adapter, Ollama adapter, deterministic fallback, null adapter |
| `guards.py` | Hallucination safeguards, grounding checks, confidence rules |
| `collection.py` | Permission-gated collection framework: RSS/permitted-endpoint parsing (stdlib), dedup keys, bounded exponential backoff, PKT timezone handling, weekend awareness (no holiday calendar is claimed) |
| `processing.py` | Article → validated intelligence record pipeline (resolve → classify → score → assess), reusing Phase 11 resolver/aliases/dedup |
| `impact.py` | Explainable impact assessment (sentiment/importance/credibility/relevance kept separate; no % impact) |
| `market_reaction.py` | Event-study math on ACTUAL observations only (pre/post prices, 1/5/10/20-day returns, volume change, benchmark/sector returns where valid, excess return); INSUFFICIENT_DATA with reasons |
| `leakage.py` | Cutoff enforcement: news usable only if published_at ≤ prediction timestamp; snapshot immutability checks |
| `rag_news.py` | News RAG retrieval over stored articles/events: deterministic full-text, labelled FULL_TEXT_FALLBACK; vector path registered-not-implemented |
| `assistant.py` | AI news assistant over stored rows: answers the prompt §11D example questions with source links; recommendation questions → uncertainty (Phase 19 rule) |
| `runner.py` | CLI runner: dry-run default, --commit; refuses BLOCKED sources; records collection runs |
| `jobs_spec.py` | Job definitions for the Phase 25 system (registered PAUSED with exact reasons in scratch; live registration is Phase B) |

New migration `20261104_0025` (only because new entities are
genuinely needed): news_articles, news_article_entities,
news_summaries, news_sentiment_assessments,
news_impact_assessments, news_market_reactions,
news_collection_runs, news_model_evaluations,
news_event_evidence. REUSED, not duplicated: news_sources,
news_events, news_event_companies, company_aliases (Phase 11);
alerts/alert_rules (Phase 21) for news alerts — no separate
news_alerts table (prompt §14 lists it as "potential"; reuse wins
over duplication). No article-body column anywhere (copyright
discipline, same as Phase 11); summaries capped at 280 chars.

API (GET-only, `endpoints/news_intelligence.py`, wired into
`api/v1/router.py`): `/news-intelligence/feed` (filters: company,
ticker, sector, source, sentiment, event category, publication
date, importance, freshness), `/news-intelligence/companies/{ticker}/news`,
`/news-intelligence/impact`, `/news-intelligence/assistant?q=`,
`/news-intelligence/sources` (permission register),
`/news-intelligence/quality` (source health + freshness).

CLI: `scripts/run_news_intelligence.py` (dry-run default,
--commit). Frontend: `/news-intelligence` (feed + filters),
`/news-intelligence/impact`, `/news-intelligence/assistant`,
plus nav entry; the company detail "News & reports" tab already
exists and is reused (its data source gains the new endpoints in
Phase B wiring — Phase A ships the new pages).

Jobs (Phase 25 system, scratch-registered PAUSED):
`news_collection_daily` (paused: no automated fetch approved),
`news_reconciliation_post_close` (paused: same), `news_digest`
(read-only digest over stored rows; runnable). The runner refuses
paused jobs — that is enforcement, not a label.

## 6. Evaluation (honest, small-N)

Evaluation dataset (`evaluation_dataset.md` + JSON fixture in
tests): hand-labelled by the implementer. 12 synthetic headlines
(clearly labelled SYNTHETIC — they measure the pipeline, not the
world) + the 7 real stored seed events with hand labels. Metrics
measured, never inflated: entity precision/recall, ticker
accuracy, classification precision/recall, sentiment agreement
(fallback only), summary factuality (grounding check),
citation correctness, latency. Sample size is disclosed with
every metric; a 19-item set cannot support a production accuracy
claim, and none is made.

## 7. Feature status (initial — updated after tests run)

| Feature | Status | Evidence / reason |
|---|---|---|
| Source inventory + permission register | PARTIALLY COMPLETE | Register written; DPS BLOCKED with evidence; media outlets NOT_COLLECTED pending direct verification |
| Collection framework (permission-gated, RSS, dedup, backoff, PKT) | PARTIALLY COMPLETE | Implemented + tested pure; live collection PAUSED (no automated fetch approved) |
| DPS collection | BLOCKED | Terms gate (see §3) |
| LLM adapter + strict schema + guards | PARTIALLY COMPLETE | Implemented + tested; live local-model inference UNVERIFIED (hardware/load, see §4) |
| Deterministic fallback processor | COMPLETE (as fallback) | Rule-based, labelled, tested; it is not LLM output |
| Event taxonomy + classification | PARTIALLY COMPLETE | Implemented + tested on fixtures; production accuracy unmeasured (small-N evaluation) |
| Entity resolution + ticker rejection | PARTIALLY COMPLETE | Reuses Phase 11 resolver (tested); ambiguous matches capped + forced to review |
| Impact assessment | PARTIALLY COMPLETE | Implemented, separated dimensions, no % impact; market-reaction evidence mostly INSUFFICIENT_DATA (one price date) |
| Market reaction / event study | PARTIALLY COMPLETE | Math implemented + tested on fixtures; production windows INSUFFICIENT_DATA (single price date 2026-11-03) |
| Forecast integration (leakage guards) | PARTIALLY COMPLETE | Cutoff enforcement implemented + tested; no improvement claim (forecasts abstain: 120/120 insufficient) |
| RAG news integration | PARTIALLY COMPLETE | Full-text fallback implemented + labelled; vector retrieval NOT IMPLEMENTED (no verified embedding model) |
| Dashboard (feed, impact, assistant) | PARTIALLY COMPLETE | Pages + GET-only APIs implemented; live data coverage still 3/470 companies (seed only) |
| Alerts (in-app) | PARTIALLY COMPLETE | Reuses Phase 21 alerts; news alert rules defined; external delivery NOT offered (no separate authorization) |
| Source quality framework | PARTIALLY COMPLETE | Classes implemented; conflict preservation side-by-side; H1 verification never claimed without evidence |
| Tests + regression | PARTIALLY COMPLETE | Suite in `test_news_intelligence.py`; full counts after the run |
| Documentation (15 deliverables) | PARTIALLY COMPLETE | Written in `docs/news-intelligence/`; live-run reports (collection runs, market-reaction evaluation) are scratch-only in Phase A |

## 8. Blockers (exact unblockers)

1. Written PSX permission evidence (user-owned) → DPS collection.
2. Automated-fetch approval (separate decision) → SBP/PBS/issuer
   live collection jobs (code + gates exist; jobs stay PAUSED).
3. Direct per-outlet terms/robots/RSS verification → media
   collection.
4. Local model verification (≥2 GB free RAM, Ollama install,
   ≤1B Q4 model pull, latency/memory measurement) → live LLM
   inference.
5. Verified local embedding model → vector retrieval.
6. More trading days (Terms-gated) → event-study windows,
   forecast evaluation, backtests.
7. Phase B gate: parent's HBL-batch-completion follow-up → any
   live-database seed/commit.
8. Wider company coverage (Phase 7 expansion) → news coverage
   beyond 3/470.

## Post-batch update (Phase B, 2026-11-05) — supersedes plan figures where they differ

- Branch merged `origin/phase-hbl-reruns` (c71469a) cleanly into
  `news-intelligence` (merge commit 54e312f, no conflicts): the
  batch's D-04 ticker-keyed news maps, HBL seed event, and updated
  EXPECTED_COUNTS are now in this branch. The batch's HBL
  extraction content was byte-identical to this branch's
  cherry-pick (56df2de), so no duplication resulted.
- Figures from the Phase A plan that are now stale: news coverage
  is 4 companies / 8 events (not 3/470 / 7); Phase 11 scope is 4
  companies; D-04 is FIXED (not open); acceptance G1 is MET (not
  NOT_MET); backend suite baseline is 468 (not 453); RAG chunks
  are 2,020 (not 943); decisions are 5 (not 4). The deliverable
  docs in this directory carry the post-batch figures.
- Evaluation dataset grew from the planned 19 items to N=20 (12
  synthetic + 8 real seed events, reflecting the HBL event).
- The remaining work items in this plan's section 7 that are still
  open are: live local-model inference (hardware unblocker),
  per-outlet news terms review, evidence linking (0 rows),
  wider company coverage, and G5 human sign-off.
