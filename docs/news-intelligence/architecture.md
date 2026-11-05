# News Intelligence Architecture (Deliverable 3)

Companion to `implementation_plan.md` (audit findings, competitor
matrix, compliance summary, initial feature table). This document
describes the as-built architecture on branch `news-intelligence`
after the Phase B merge of `phase-hbl-reruns` (c71469a).

## Package layout

```
backend/app/services/news_intelligence/
  taxonomy.py        prompt section 5 categories + keyword rules
  schema.py          strict prompt section 4 field list + validation
  guards.py          grounding, confidence caps, ticker/source checks
  llm_adapter.py     LLMAdapter protocol, NullAdapter, OllamaAdapter,
                     DeterministicFallback (RULE_BASED)
  collection.py      gate, backoff, PKT timestamps, freshness, RSS parse
  processing.py      pipeline: resolve -> classify -> ground -> cap
  impact.py          separated importance/credibility/relevance
  market_reaction.py Decimal event-study math (actual observations only)
  leakage.py         look-ahead guards (published_at <= prediction time)
  rag_news.py        deterministic full-text retrieval (FULL_TEXT_FALLBACK)
  assistant.py       answers from stored rows only, with citations
  runner.py          persistence, collection-run records, digest, reactions
  jobs_spec.py       3 Phase 25 job definitions (single source of truth)
  jobs_handlers.py   handlers wired into Phase 25 HANDLERS
```

## Data flow (no step can invent)

1. Input: an article dict (title + headline/excerpt text only —
   never a full body) from a permitted source, or a scratch
   evaluation item. BLOCKED sources never reach this step: the
   collection gate refuses them first and records the refusal.
2. Entity resolution: Phase 11 resolver (exact ticker tokens and
   exact full-alias phrases, word boundaries only). Ambiguous
   matches cap at 0.50 and force review. Tickers resolve through
   company_id -> registry ticker maps, never guessed from text.
3. Classification + sentiment: LLM adapter if configured and
   reachable, else the deterministic fallback (labelled RULE_BASED).
   LLM JSON is schema-validated; malformed output is REJECTED with
   errors, never repaired.
4. Grounding: every extracted fact must share a significant token
   with the source text, or the record is forced to REVIEW.
5. Confidence capping: ambiguous or unvalidated input caps at
   0.50; below 0.80 forces REVIEW.
6. Persistence (runner only): PROCESSED/REVIEW rows stored with
   entity, summary, sentiment, and impact rows; UNPROCESSED stored
   metadata-only; REJECTED never persisted as content; duplicates
   skipped by content_hash.
7. Impact, market reaction, RAG, and assistant all read stored rows
   only. The LLM never performs authoritative financial math (all
   Decimal, deterministic Python). Sentiment, importance,
   credibility, relevance, reaction, and forecast output stay
   separate fields.

## Reused, not duplicated

- Phase 11: news_sources, company_aliases, news_events,
  news_event_companies, news_event_links, resolver, dedup grain,
  PolicyBlocked.
- Phase 21: alert_rules / alerts for news alerts (no news_alerts
  table — the prompt lists it as "potential"; reuse wins).
- Phase 25: job system (register/list/run via `scripts/run_jobs.py`).
- Phase 19: retrieval contract (metadata filters before scoring,
  token/phrase/ticker scoring, 500-char snippets, injection-flagged
  chunks never returned) — full-text only; vector retrieval is
  registered-not-implemented.

## New tables (migration 20261104_0025)

news_articles, news_article_entities, news_summaries,
news_sentiment_assessments, news_impact_assessments,
news_market_reactions, news_collection_runs,
news_model_evaluations, news_event_evidence. See
`migration_doc.md`. Primary keys are Integer (Phase 29 precedent:
BigInteger Identity does not auto-generate on SQLite).
company_relevance / sector_relevance are NULLABLE: NULL means "not
applicable to this item's scope", never a measured zero.

## API (GET-only) and frontend

- `/news-intelligence/feed` (ticker, sector, source, sentiment,
  category, publication date, importance filters)
- `/news-intelligence/companies/{ticker}/news`
- `/news-intelligence/impact`
- `/news-intelligence/assistant?q=`
- `/news-intelligence/sources` (permission register)
- `/news-intelligence/quality` (source health + freshness)
- Frontend: `/news-intelligence` (feed + filters),
  `/news-intelligence/impact`, `/news-intelligence/assistant`,
  plus nav entry. The company detail "News & reports" tab already
  exists and is reused (its data source gains the new endpoints).

## Jobs

- `news_collection_daily` — PAUSED (no automated fetch approved;
  handler enforces the gate and records refused runs).
- `news_reconciliation_post_close` — PAUSED (first live run belongs
  to Phase B; handler is read-only).
- `news_digest` — ACTIVE (read-only digest over stored rows; sends
  nothing anywhere).
