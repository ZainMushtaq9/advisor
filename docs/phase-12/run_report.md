# Phase 12 run report — 2026-11-04

Verdict: **PARTIALLY COMPLETE**.

## What ran

- Branch `phase-12-ownership-actions-breadth` from `b6c6026` (Phase 11 tip).
- Migration `20261104_0009` (head): 6 new tables — `ownership_holdings`,
  `corporate_action_records`, `market_breadth`, `liquidity_observations`,
  `investor_flows`, `adjustment_rules`.
- CLI `scripts/run_ownership_actions.py` (--dry-run default / --commit).
- GET-only API `backend/app/api/v1/endpoints/ownership.py` (6 routes).

## DB counts before / after

| Table | Before | After |
|---|---|---|
| ownership_holdings | 0 | 34 (17 categories + 16 named holders + 1 total) |
| corporate_action_records | 0 | 5 (HUBC 4, NML 1) |
| Phase 3 corporate_actions | 0 | 0 (intentionally; see registry doc) |
| adjustment_rules | 0 | 4 (all defined_not_applied) |
| market_breadth | 0 | 50 (43 computed + 6 insufficient + 1 partial) |
| liquidity_observations | 0 | 889 (444 × 2 + 1 market row) |
| investor_flows | 0 | 0 (intentionally; see coverage report) |
| market_prices | 444 | 444 (is_adjusted False on all; raw never rewritten) |

Idempotency proven: a second `--commit` wrote 0 new rows
(34 ownership, 5 actions, 50 breadth, 889 liquidity skipped).

## What computed vs NOT_CALCULABLE

Computed: HUBC ownership (two-extractor verified, sums reconcile);
5 dividend actions with per-share amounts; 4 adjustment rule
definitions; breadth for 2026-11-03 (coverage 444/470 = 94.468085%,
37 sector participations, total volume 441,360,098, median volume
54,631.5, top-10 volume share 49.249694%, zero-volume count 0);
liquidity for all 444 priced securities.

NOT_CALCULABLE (never zero-filled): advances, declines, unchanged
(previous_close NULL on all 444 rows); new highs/lows (one trading
date); turnover distribution (turnover NULL on all 444 rows);
free-float-adjusted measures (no published free-float figure);
investor flows (no verified published series loaded); any adjusted
price series (no stored action has an ex-date).

## Audit corrections made during this run

1. Model classes initially omitted `Base` from their bases and were
   never mapped (dry-run failed with an ArgumentError). Fixed by
   adding `Base` to all six classes; the failure was in new code only.
2. The ownership unique grain initially omitted `folio`, so the two
   same-name/different-folio holders (MEGA CONGLOMERATE, MUHAMMAD
   KAMRAN KAMAL) collapsed to one row each (32 rows instead of 34).
   Fixed by adding `folio` to the grain in both model and migration,
   then downgrading to 0008, re-upgrading to 0009, and re-running
   `--commit` (34 rows restored, idempotency re-proven).
3. The first migration attempt collided with the Phase 3
   `corporate_actions` table (event_date NOT NULL, adjustment-factor
   oriented). Per the Phase 11 precedent, the Phase 3 table was NOT
   retrofitted; the Phase 12 registry is `corporate_action_records`
   instead, and the Phase 3 table stays empty until an action gains a
   known ex-date.

## Tests and live checks

- Backend suite 197 passed, 0 failed (189 prior + 8 new pure tests).
- Ruff check + format clean on all new/changed files.
- Live API: ownership HUBC 200 (34 rows), NML 200 (0 rows + note),
  actions HUBC 200 (4), OGDC 200 (0), breadth 200 (50), liquidity
  HUBC 200 (2), unknown ticker 404, flows 200 (0 + explanation),
  adjustment-rules 200 (4).

## HBL pending note

Habib Bank Limited (company 277, COMMERCIAL BANKS) has no ownership,
action, or liquidity rows beyond its market liquidity row (it has a
2026-11-03 price row, so it appears in breadth/liquidity): its CY2025
statements are not loaded (PDF blocked at download; live-browser
download runs separately). Design accepts HBL via a Phase 7 load plus
a Phase 12 re-run; no redesign needed.

## Remaining blockers (exact unblockers)

1. Wider-company ownership — Phase 7 expansion beyond the 1-company
   sample (per-company issuer-document verification pass).
2. Action dates (ex/record/payment) — PSX announcement data (written
   permission evidence) or issuer notices per action.
3. Advances/declines/turnover breadth — a price source file carrying
   previous_close and turnover (Phase 5 Terms-gated).
4. Multi-day breadth/liquidity — more trading days of price data.
5. Free-float measures — a published free-float series (PSX
   free-float data, Terms-gated).
6. Investor flows — a terms-reviewed SBP SCRA/FPI monthly series or
   NCCPL published flow series.
7. Adjusted price series — ex-dates for stored actions (blocker 2).
8. VERIFIED promotion — H1 second agreeing source including an
   official source; everything stays UNVERIFIED until then.
