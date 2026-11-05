# Developer Guide (Deliverable 12)

## Running the engine

```bash
# DATABASE_URL must be set, e.g. from database/.env
# Dry-run (default): processes everything, rolls back, writes nothing.
python scripts/run_news_intelligence.py process --input items.jsonl
# Commit run: writes articles + entities + summaries + sentiment + impact.
python scripts/run_news_intelligence.py process --input items.jsonl --commit
# Record refused runs for policy-blocked sources (enforcement evidence).
python scripts/run_news_intelligence.py enforce --commit
# Reactions for stored Phase 11 events (INSUFFICIENT_DATA rows included).
python scripts/run_news_intelligence.py reactions --commit
# Read-only: digest, reconcile, quality.
python scripts/run_news_intelligence.py digest
python scripts/run_news_intelligence.py reconcile
python scripts/run_news_intelligence.py quality
```

Input JSONL shape per line: `{article_id, title, source,
canonical_url, published_at, retrieved_at, language?, text,
source_key?, _credibility_class?}`. `text` is headline + excerpt
only — never a full article body. Dates are ISO-8601; naive
values are treated as Asia/Karachi local, never silently UTC.

## Adding a local model

Implement the `LLMAdapter` protocol (`process(article_text,
instruction) -> str`) or use `OllamaAdapter(model=...)`. The
pipeline validates the raw JSON with the strict schema; malformed
output is REJECTED, never repaired. Never add a paid-API adapter
(OpenAI/Gemini/Groq/etc.) — the PKR 0 rule forbids it. Label the
processor honestly: `LLM` only when a model actually ran.

## Adding a source

1. Add the source to the Phase 11 `news_sources` registry with its
   real policy and terms note.
2. Record the terms/robots/RSS review in
   `source_permission_register.md` BEFORE any collection code.
3. Only a source with policy `COLLECTABLE` AND an approved
   automated fetch passes `collection_allowed()`. `ALLOWED`
   (manual reads) is not an automated-fetch approval.
4. Never store article bodies. Summaries stay <= 280 chars.

## Adding a job

Add the definition to `jobs_spec.py` (single source of truth);
`registry.py` extends `JOB_DEFINITIONS` from it. Add the handler
to `jobs_handlers.py` and wire its key into Phase 25 `HANDLERS`.
Seed status: paused unless the handler is read-only and its run
is explicitly approved (news_digest is the only active news job).

## Conventions that bite

- Resolve companies BY TICKER. Surrogate company ids shift across
  fresh imports; never hardcode one. (D-04 fixed the Phase 11
  maps to ticker-keying; this engine follows the same rule.)
- Real column names: `companies.legal_name` (not company_name),
  `sectors.name` (not sector_name). A regression test guards the
  ticker-map query.
- Models use Integer primary keys (Phase 29 precedent: BigInteger
  Identity does not auto-generate on SQLite).
- Tests never touch real PostgreSQL or the network: pure unit
  tests + SQLite in-memory model tests only.
- Never stage the `backend/.venv` / `database/.venv` symlinks
  (same gitignore quirk as Phase 30): use explicit `git add`.
