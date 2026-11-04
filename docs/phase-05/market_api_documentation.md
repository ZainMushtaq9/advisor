# Phase 5 — Market API Documentation

Base: `/api/v1` (see `backend/app/api/v1/router.py`). All market
endpoints are GET only: CORS allows GET only, and ingestion
happens via the CLI, never via a POST API. There is deliberately
no write endpoint.

## GET /api/v1/market/prices

Query: `ticker` (optional), `from_date`, `to_date` (ISO dates),
`quality_status` (one of the Phase 5 vocabulary), `skip`,
`limit` (1–200, default per existing endpoint convention).
Response: newest-first rows, each with ticker, trading_date,
bar_type, open, high, low, close, volume, turnover,
previous_close, is_adjusted (always false in v1: official
unadjusted), quality_status, freshness (STALE / CURRENT /
UNKNOWN, v1 rule only), source_key, source_timestamp,
collected_at. An unknown ticker in the list endpoint returns an
empty list (not an error); an empty market returns counts/rows
of 0 with the scope note, never fabricated rows. Invalid
`skip`/`limit`/dates return 422 with a field message.

## GET /api/v1/market/prices/{ticker}/latest

Latest stored daily observation for the ticker, same row shape
as above. Known ticker with no observations → 200 with
observation null. Unknown ticker → 404, mirroring the registry
single-resource lookups.

## GET /api/v1/market/status

Coverage summary: market_prices total, securities with
observations, trading-date range (or null when empty), counts
by all 8 quality statuses, the scope note ("470 Main Board /
Normal Counter snapshot securities"), and the freshness rule
note. Current production truth: total 0, securities with
observations 0, range null — the engine is ready, no
observation has been ingested.

## Unavailable state

When DATABASE_URL is unset, endpoints answer 503 with
"Database is not configured (DATABASE_URL is not set).",
exactly like the existing endpoints — never a fake empty
market. Error responses are generic JSON with no stack traces
and no secrets (see `backend/app/main.py`).

## Scope and honesty notes

- Scope is never "KSE-100" or "full-market" in any response.
- `is_adjusted=false` means official unadjusted prices; no
  adjusted/total-return series is served in v1.
- `freshness` is the v1 rule only (collected >30 days after
  trading_date → STALE); UNKNOWN means the rule cannot be
  applied, never a freshness claim.
