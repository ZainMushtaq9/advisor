# Database Migration Documentation (Deliverable 5)

## Migration 20261104_0025 (`news_intelligence_engine`)

- Revision: `20261104_0025`, revises `20261104_0024` (head after
  this migration). No other migration in the chain was modified.
- Applied to scratch: 0024 -> 0025, verified (`alembic current`
  = `20261104_0025 (head)`). Live application is a Phase B step
  (see the Phase B report, not this document).
- Downgrade drops the nine tables in reverse dependency order
  (verified on scratch: downgrade to 0024 then upgrade to head).

## Tables created

| Table | Purpose |
|---|---|
| news_articles | Article metadata + 280-char summary + link + hash. NO body column. |
| news_article_entities | Resolved entity links (durable identity = ticker). |
| news_summaries | Capped summaries as separate rows (re-summary = new row). |
| news_sentiment_assessments | Sentiment + category + scores + facts/evidence/notes. |
| news_impact_assessments | Separated importance/credibility/relevance dimensions. |
| news_market_reactions | Event-study rows (Decimal prices, JSON windows). |
| news_collection_runs | Collection attempts incl. refused runs (evidence). |
| news_model_evaluations | Metrics always paired with dataset_size. |
| news_event_evidence | Article <-> Phase 11 event links (supports/contradicts). |

## Design decisions recorded in the migration

- CHECK constraints on quality_status vocabulary and on status /
  sentiment / horizon / credibility vocabularies (Phase 3 precedent:
  enforcement in the database, not just application code).
- Primary keys Integer autoincrement (Phase 29 precedent:
  BigInteger Identity does not auto-generate on SQLite, and this
  package must support SQLite in-memory model tests).
- Foreign keys to this module's own tables are Integer (to match);
  foreign keys to companies / news_events stay BigInteger (to match
  those tables).
- company_relevance / sector_relevance are NULLABLE: NULL means
  "not applicable to this item's scope" (a macro item has no
  company relevance), never a measured zero. This was fixed during
  Phase A after the scratch run failed on a macro item's NULL
  relevances — the schema now matches the impact module's
  semantics instead of forcing a fake zero.
- No promotion path to VERIFIED / PARTIALLY_VERIFIED exists in
  this migration or its models. New rows carry their inputs'
  status, never higher.
- No order, execution, external-send, publication, credential, or
  PII concept exists in these tables.
