# Phase 6 completion addendum — 2026-11-04 (completion run)

Branch: `phase-06-completion`, branched from `phase-06-technical-analytics`
tip `6efede9` (remote SHA verified equal before work). No code changed in
this run; this document records re-verification and the restored live-run
bookkeeping after the third VM replacement. The original Phase 6 framework,
tests, and audit findings are unchanged.

## 1. Entry state verified (not assumed)

- Live DB (PostgreSQL 16.15, `psx_intelligence`, Alembic head
  `20261104_0005`, 57 tables): `market_prices` 444 rows, exactly one
  trading date 2026-11-03, `previous_close` NULL on all 444,
  `is_adjusted` 0; companies 470, securities 470, `trading_sessions` 0.
- Indicator tables present and empty before the re-run:
  `technical_indicator_values` 0, `technical_signal_events` 0,
  `technical_calculation_runs` 0, `technical_indicator_definitions` 0,
  `technical_indicator_configurations` 0.
- Framework files present: `backend/app/services/technical_indicators/`
  (conventions/formulas/aggregation/coverage/runner/signals),
  `scripts/run_technical_indicators.py`, `backend/app/api/v1/endpoints/indicators.py`,
  `frontend/app/indicators/page.tsx`, all 15 original `docs/phase-06/` docs.

## 2. Coverage re-run (existing DB rows only, no new collection)

Dry-run then `--commit`, run key `phase06-coverage-2026-11-03`,
as-of 2026-11-03:

- Securities assessed 470, indicators registered 62,
  securities with any calculable 0, values written 0.
- Error rows written 124, breakdown verified from the database
  (`technical_calculation_errors`): `insufficient_warmup` 61,
  `missing_data` 63, across 62 distinct indicator keys.
- Reconciliation of 124: 61 non-daily-return indicators contribute one
  `insufficient_warmup` row (444 one-bar securities) and one
  `missing_data` row (26 zero-bar securities) each = 122;
  `daily_return` contributes two `missing_data` rows (bars 1 and bars 0
  aggregate separately) = 2; 122 + 2 = 124. This matches the original
  run's pattern exactly (missing_data 63 + insufficient_warmup 61).
- Runner also seeded 62 indicator definitions and 62 configurations
  (62 distinct keys), as designed.
- Per-indicator dry-run detail (all except `daily_return`):
  `insufficient_warmup` 444 + `missing_data` 26, calculable 0.
  `daily_return` (warm-up 1): `missing_data` 470 — previous_close is
  blank, so more trading days alone do NOT unblock it under the current
  convention; it needs a present previous_close in a future source file.
- Run row: `phase06-coverage-2026-11-03 | completed | 470 | 0`.
- Re-run guard verified: a further `--commit` reported
  `already_recorded: true`, wrote 0 values and 0 error rows; DB counts
  unchanged (1 run row, 124 errors, 0 values).

## 3. Re-verification results

- Backend suite: **114 passed, 0 failed** (1 unrelated Starlette
  deprecation warning). Includes the 29 Phase 6 tests.
- Ruff check, Phase 6 scope only
  (`backend/app/services/technical_indicators`,
  `backend/app/api/v1/endpoints/indicators.py`,
  `scripts/run_technical_indicators.py`, `backend/tests`): **all checks
  passed**. Two observations, neither a Phase 6 defect:
  (a) a broad `ruff check` over `scripts/` flags 7 pre-existing issues
  in `scripts/run_phase4_pg_check.py` (Phase 4 scope, present in the
  6efede9 tree, untouched here — flagged for the parent, not fixed in
  this Phase 6 run);
  (b) `ruff format --check` under ruff 0.17.3 would reformat 7 Phase 6
  files — version drift against gate-time formatting, not a behaviour
  change; no reformatting was applied to verified files.
- Frontend: typecheck clean, lint clean, `next build` succeeds,
  Vitest **11 passed**.
- Live API check (uvicorn, port 8001, killed after the check):
  - `GET /api/v1/indicators/coverage` → 200: 470 assessed, 62
    registered, 0 calculable.
  - `GET /api/v1/indicators/coverage/LUCK` → 200: 1 bar, input quality
    UNVERIFIED, 0 calculable / 62 not calculable, with per-indicator
    unblocker detail (e.g. sma_5: "Needs 5 bars, only 1 available;
    4 more bars required").
  - `GET /api/v1/indicators/values` → 200, total 0, scope note present
    (Main Board / Normal Counter only; UNVERIFIED single-day prices;
    no KSE-100, full-market, or VERIFIED claim; signals never buy/sell
    recommendations).
  - `GET /api/v1/indicators/signals` → 200, total 0, "No rule is
    currently activated".
  - `GET /api/v1/indicators/coverage/NOPE123` → 404.
- Immutability triggers, corrected understanding: the Phase 6
  migration (`20261104_0005`) guards exactly four tables —
  `technical_indicator_values`, `technical_signal_events`,
  `quantitative_market_features`, `market_regime_observations`.
  `technical_calculation_runs` is intentionally NOT guarded (the runner
  itself updates run status). A transaction test on the values table
  (definition + configuration + value inserted, then UPDATE and DELETE
  attempted under savepoints) raised the append-only error both times
  ("corrections must be new rows, never edits") and rolled back with
  residue 0. An earlier probe that updated the runs table without error
  was testing the wrong table and is not a trigger failure.

## 4. Playbook Phase 6 gate assessment

| Gate item | Evidence | Verdict |
|---|---|---|
| All supported formulas pass independent tests | 114 backend tests pass, incl. hand-calculated Phase 6 cases; formulas verified on synthetic/reference inputs | PASS (on test inputs; no production values exist to test against) |
| Timeframe aggregation is correct | Aggregation code + tests pass; weekly/monthly always "partial" without a validated calendar; intraday refused | PASS for code correctness; NOT DEMONSTRATED on real multi-day data |
| Historical calculations are reproducible and point-in-time safe | Re-run reproduced the original run exactly (470/0/124, same breakdown); as-of slicing restricts inputs to the assessment date | PASS on current data |
| Production charts use only validated source data | Values API returns 0 rows; frontend shows no chart from a single point; scope notes on every response | PASS (enforced; nothing fabricated) |

## 5. Verdict: PARTIALLY COMPLETE (unchanged)

The framework, tests, APIs, and bookkeeping are verified, but COMPLETE
requires all three of the following, none available in this run:

1. **More trading days** — SMA(5) first, after 4 more trading days,
   verified via a committed run with value rows > 0. Blocked by the
   PSX Terms gate: no new collection or ingestion was performed.
2. **Written PSX Terms resolution** — the same open question that is
   Phase 5's sole blocker. It is inherited, not created, by Phase 6.
3. **Scope gaps closed or explicitly scoped out by a new instruction**
   — validated trading calendar (weekly/monthly stay "partial"),
   corporate-action adjustment methodology (none available or
   validated; no adjusted series built), activated signal rules (none;
   by design, rules need calculable inputs first), regime features
   (need calculable values first).

## 6. How Phase 4 / Phase 5 outcomes affect Phase 6

- Phase 4 (PARTIALLY COMPLETE, scoped 470 universe, all UNVERIFIED)
  defines Phase 6's input scope exactly: coverage is assessed over
  those 470 securities, and the 26 no-price securities (13 rejected +
  13 absent) are the `missing_data` population. GEM/Non-Compliant
  absence propagates unchanged.
- Phase 5 (PARTIALLY COMPLETE, sole blocker Terms resolution) supplies
  the single-day, single-source, UNVERIFIED price set. Phase 6's
  NOT_CALCULABLE headline is a consequence of that input, not of the
  indicator implementation.
- The Phase 4 SECP LEAP second-source route is field-scoped only and
  does not change Phase 6's input quality: committed prices remain
  single-source UNVERIFIED observations.

## 7. What changed in this run

- One new document (this file) on branch `phase-06-completion`.
- Live DB bookkeeping restored: 1 calculation-run row, 124 error rows,
  62 definitions, 62 configurations, 0 values, 0 signal events.
- No code, migration, or framework file changed. No merge to main.
  No push to any repository other than advisor (see commit record).
