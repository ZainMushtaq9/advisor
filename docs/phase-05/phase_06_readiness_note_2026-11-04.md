# Phase 6 readiness note — PREPARATION ONLY (2026-11-04)

**Phase 6 is NOT started.** No indicator formula has been coded, no
calculation has been run, no signal event has been created. This note
is preparation written while Phase 5 finishes, so Phase 6 can start
cleanly on its own branch (`phase-06-technical-analytics`) once its
gate passes. It lives under `docs/phase-05/` deliberately: it is a
Phase 5 handoff note, not a Phase 6 deliverable.

## Spec source

User-supplied full Phase 6 spec ("Technical Indicators, Quantitative
Analytics and Market Feature Engine"), preserved in the project
memory (2026-11-04 Phase 6 spec entry). Headline rules:

- Deterministic, reproducible Python calculations only — no LLM
  calculating indicators; consistent formulas/parameters (no silent
  mixing of conventions, e.g. Wilder's RSI smoothing vs
  simple-average, Bollinger/ATR conventions).
- Indicators: SMA 5/10/20/50/100/200, EMA 5/10/12/20/26/50/200, RSI
  (14 default), MACD (12/26/9), Stochastic, ROC/Momentum/Williams %R/
  CCI, Bollinger Bands, ATR, rolling/annualized volatility, drawdown
  and historical tail-risk measures labelled historical not
  predictive, volume analytics (volume SMA, relative volume, OBV,
  Accumulation/Distribution, MFI, spikes — volume increase never
  automatically read as buying pressure); ADX, Parabolic SAR,
  Ichimoku, Fibonacci, pivots, Donchian/Keltner only after
  formula/input/data-sufficiency validation.
- Timeframes daily/weekly/monthly (intraday only if validated
  intraday data exists); correct OHLC/volume aggregation; missing
  sessions never create fabricated prices; partial vs completed
  periods distinguished.
- Phase 5 quality governance: rejected/conflicted never silently
  included. Every calculated value stored with security, indicator,
  parameters, frequency, calculation timestamp, last input date,
  quality status, version and source lineage; version history never
  overwritten. Backfill with warm-up, incremental recalculation,
  correction propagation, tested no-look-ahead rule.
- Signal-event engine kept separate from the future investment
  decision engine; events never equated with guaranteed buy/sell
  opportunities.
- APIs/frontend/charts on real validated observations only, with
  formula/parameter/timestamp/version/quality transparency and an
  explanation when an indicator cannot be calculated.
- Mathematical validation via hand-calculated cases and independent
  references; edge cases (constant prices, zero changes, short
  histories, extreme moves, zero volume, gaps, suspensions,
  insufficient warm-up); independent audit; performance tests.
- STOP after Phase 6 (no automatic Phase 7).

## Section 2 verification checklist — status as of 2026-11-04 ~17:41 PKT

Section 2 requires verifying Phase 1 architecture, Phase 2
environment, Phase 3 database, Phase 4 registry and Phase 5
market-data pipeline, and inspecting actual market records in
PostgreSQL (timestamps, OHLCV, provenance, quality statuses),
historical coverage / missing-data reports, and whether
corporate-action adjustments are available and reliable. It also
requires: do NOT mark Phase 5 complete merely because collectors
exist; if historical data is insufficient/unreliable for an
indicator, report the limitation instead of generating misleading
results.

| Check | Status |
|---|---|
| Phase 1 architecture docs | Present (67 files, spec checkpoint) |
| Phase 2 environment | Partial — Docker never ran, Playwright E2E never ran |
| Phase 3 database schema | Present in code/migrations; live DB lost to VM replacement, recovery in progress |
| Phase 4 registry | 470-row Main Board / Normal Counter snapshot verified twice (dry-run + commit 2026-11-04); live DB lost to VM replacement, re-import required after recovery |
| Phase 5 pipeline | Engine verified (85 backend tests); market_prices 0; real CLI dry-run passed 2026-11-04 (444 would-ingest, 13 rejected) |
| Phase 5 commit | BLOCKED on verified written PSX permission (no reply in mailbox as of 2026-11-04 ~17:37 PKT re-check) |
| Corporate-action adjustments | Not available / not validated — prices stored is_adjusted=False only |
| Actual market records to inspect | None yet (market_prices 0) |

**Gate verdict: FAILS today.** Phase 6 cannot start implementation
until the DB is recovered, the registry is re-imported, the dry-run
re-passes, permission is verified, the commit lands, and Phase 5 is
honestly re-judged. The permanent autonomous authorization does not
override this dependency gate.

## Data-sufficiency finding (the key honest limit)

Even after the commit lands, the database will hold **one trading
day (2026-11-03) × 444 securities**. Warm-up requirements then
decide what Phase 6 can calculate:

- SMA 5 / EMA 5 need 5 sessions; SMA 20 / Bollinger (20) / ATR (14) /
  RSI (14) need 14–20; MACD (12/26/9) needs 26+9; SMA 50/100/200 and
  EMA 50/200 need 50–200 sessions. **Almost every named indicator
  is NOT_CALCULABLE on day 1.**
- Daily return needs a previous close; the current mapped file
  leaves previous_close BLANK (field-9 unverified), so even returns
  are NOT_CALCULABLE from this file alone until a verified previous
  close is sourced.
- Volume analytics, volatility, drawdown, regime features and any
  signal event all need multi-day history and are NOT_CALCULABLE
  on day 1.

So Phase 6's first honest output after the commit is the
calculation framework + validation harness + NOT_CALCULABLE
explanations — not a full indicator table. Indicators become
meaningful only as further trading days accumulate. No indicator
value may be fabricated to fill the gap.

## Next steps, in order

1. DB recovery: install PostgreSQL, restore 2026-11-04T1230 backup,
   migrate to head a909e8449cdd, re-import registry, re-run CLI
   dry-run.
2. Verify written PSX permission; commit 444 UNVERIFIED rows for
   2026-11-03 (13 rejected + 13 absent reported alongside, never
   zero-filled).
3. Re-judge Phase 5 acceptance honestly (still PARTIAL: single day,
   single source, GEM/Non-Compliant/KSE-100/ISIN gaps remain).
4. Re-run this Section 2 gate, then start Phase 6 on
   `phase-06-technical-analytics` — implementation only for what
   the data actually supports.
