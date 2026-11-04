# Phase 20 — Run Report (2026-11-04)

## Verdict: PARTIALLY COMPLETE

The screener engine is complete and independently verified
end-to-end (registry → filters → scoring → saved screens →
API → commit → push). The verdict is PARTIALLY COMPLETE,
not COMPLETE, because the brief's entry dependency (verified
universe and upstream APIs) is unmet in the strong sense —
all inputs are UNVERIFIED — and because coverage is 470
securities for price/volume but only 4 companies for
fundamentals/valuation/dividends, technical filters match
nothing, and HBL has no rule-based fundamental coverage
pending its Phase 7 load. Nothing mandatory is claimed as
done that is not evidenced.

## Run summary (as-of 2026-11-04, price date 2026-11-03)

| Screen | Universe | MATCH | INSUFFICIENT_DATA |
|---|---|---|---|
| liquid_leaders | 470 | 194 | 0 |
| volume_top_decile | 470 | 44 | 26 |
| cheap_profitable | 4 | 1 (HUBC) | 1 (HBL) |
| dividend_payers | 4 | 2 (HUBC, NML) | 0 |
| technical_momentum | 470 | 0 | 470 |

Totals: 5 definitions, 5 runs, 1,418 results, 241 matches.
Second `--commit`: 0 new rows (5 runs reused, definitions
already seeded) — idempotency proven.

## Corrections made during this run (audit findings, fixed)

1. **Dividend action type**: the runner first matched
   `action_type == "dividend"` and loaded zero dividends.
   Stored types are DIVIDEND_CASH (Phase 12). Fixed to match
   the DIVIDEND family; HUBC 10.00 and NML 5.00 now load.
   Caught by the dry-run showing 0 dividend matches against
   the known 5 stored actions.
2. **Dry-run before first commit**: run_screen initially
   errored when the definition row did not exist yet, so a
   dry-run could not evaluate anything. Fixed: dry-run
   evaluates fresh without a stored definition row and
   reports would-write counts; commit path still seeds
   first. Nothing is written in dry-run.
3. **API score sorting (live-check catch)**: the results
   endpoint stringified scores before sorting, so
   score-descending sort raised TypeError on the string
   (500 on first live check). Fixed: scores stay Decimal
   through sort and pagination and are stringified only on
   the final page. Re-verified live: cheap_profitable
   returns HUBC 1.0000, OGDC 0.5000, NML 0.0000, HBL NULL in
   that order.
4. **Unknown-screen 404 wording**: the app's global 404
   handler rewrites every 404 detail to "No route matches
   {path}" (pre-existing app behavior, main.py line ~102).
   The endpoint does return 404 for unknown screens; the
   wording is the handler's, not a routing failure. Left
   unchanged — app-level behavior, not Phase 20 scope.

## Tests and live checks

- New tests: 19 passed (pure: filter semantics, percentile
  math, sector applicability, technical null handling,
  presence semantics, scoring, seed-screen fixtures,
  validation, pagination, sorting, registry coverage,
  GET-only routes, no-execution scan).
- Full backend suite: 312 passed, 0 failed (293 prior +
  19 new).
- Ruff check + format clean on all new/changed files
  (including the migration file).
- Live API (TestClient): filters 200 (18 filters); screens
  200 with correct matched counts; results 200 with correct
  ordering; outcome filter 200 (44 top-decile matches);
  unknown screen 404; invalid limit/sort 400; status 200
  (5 / 5 / 1,418 / 241).
- Independent audit: direct SQL recounts agree (5 / 5 /
  1,418 / 241); cheap_profitable rows hand-derived from
  stored values match exactly; independent percentile SQL
  reproduces 44; untouched tables unchanged (statements 88,
  prices 444, decisions 4, rag_chunks 943, agents 16);
  HUBC close still 197.2400.

## HBL pending note

Habib Bank Limited (company 277, COMMERCIAL BANKS) has a
valid quote and appears in price/volume screens, but its
fundamental/valuation filters are SECTOR_NOT_APPLICABLE and
its cheap_profitable outcome is INSUFFICIENT_DATA: its
CY2025 statements are not loaded (PDF blocked at download;
live-browser download runs separately). A Phase 7 load plus
a Phase 20 re-run adds HBL's evidence without redesign;
the banking rule (no industrial ratios blindly applied)
carries forward.

## Remaining blockers (exact unblockers)

1. **Wider-company fundamental coverage** — Phase 7
   expansion beyond the 3-company sample (per-company
   source verification pass).
2. **HBL coverage** — live-browser HBL CY2025 PDF download,
   then a Phase 7 load, then a Phase 20 re-run.
3. **Technical filters** — calculable technical values
   (Phase 6 needs more trading days: 5 closes for SMA(5),
   15 observations for RSI(14)).
4. **Share-count filters (P/B, P/S, market cap, EV)** — an
   authoritative shares-outstanding source (Phase 9
   blocker).
5. **Mean-variance / optimized ranking** — validated
   expected returns (Phase 13 evaluations on longer series)
   + a covariance matrix (≥ 2 closes per security).
6. **VERIFIED promotion** — H1 second agreeing source
   including an official source; everything stays
   UNVERIFIED until then.
7. **CI-in-CI** — a main/development push or PR (separate
   approval; remote/local main have unrelated histories;
   no PR exists).
