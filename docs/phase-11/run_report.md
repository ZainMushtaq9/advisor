# Phase 11 Run Report — 2026-11-04

Branch: `phase-11-news-events` (from `9df2266`). Migration head:
`20261104_0008`. Verdict: **PARTIALLY COMPLETE**.

## DB counts before / after (live DB verified)

| Measure | Before | After |
|---|---|---|
| news_sources | 0 | 8 |
| company_aliases | 0 | 1,376 (20 ambiguous rows = 10 aliases × 2 claimants) |
| news_events | 0 | 7 |
| news_event_companies | 0 | 3 |
| news_event_links | 0 | 0 (no syndicated duplicates in seed) |
| data_sources | 11 | 19 (+8 news source rows) |
| financial_statements / line items / prices / valuations / macro events | 88 / 1,316 / 444 / 51 / 4 | unchanged |

Idempotency proven: a further `--commit` wrote 0 new rows (7 events and
1,376 aliases skipped as existing).

## Tests and live checks

- Backend suite: **189 passed, 0 failed** (179 prior + 10 new).
- Ruff check + format clean on all new/changed files.
- Live API (TestClient): `/news` 200 (7 events), `/news/sources` 200
  (8), `/news/aliases?ticker=HUBC` 200 (3 aliases), `/news/aliases?
  ticker=HBL` 200 (3 aliases, no events — HBL pending pattern),
  unknown ticker 404, `/news/quality` 200 (3/470 companies covered,
  1,376 alias rows, 20 ambiguous, review 5 pending + 2 scheduled).
- Audit fix during this run: the API session dependency first passed
  the Request object to `get_session_factory()` (500 on `/news`);
  fixed to the Phase 10 pattern (`request.app.state.engine`); all
  endpoints then verified. See `implementation_specification.md`.

## Seed events (7)

HUBC earnings 2026-09-21, NML earnings date-unknown, OGDC earnings
2026-02-23, SBP MPC 2026-10-26, PBS CPI 2026-11-02, SBP minutes due
2026-11-20 (scheduled), SBP meeting 2026-12-14 (scheduled). Full
table in `implementation_specification.md`.

## Remaining blockers (exact unblockers)

1. Universe-wide news coverage — written PSX permission evidence,
   verified for its exact terms (PSX announcements), plus per-outlet
   terms review (reputable news).
2. HBL events — live-browser HBL CY2025 PDF download, then a Phase 7
   load, then a Phase 11 re-run with HBL added.
3. Wider-company coverage — Phase 7 expansion beyond the 3-company
   sample (per-company source verification pass).
4. VERIFIED promotion — H1 second agreeing source including an official
   source; all document-derived events stay UNVERIFIED until then.
5. SECP announcements — a documented SECP announcements route (public
   pages only).
