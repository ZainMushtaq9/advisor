# Phase 14 — Run Report (2026-11-04)

## Branch and commit

- Branch: `phase-14-risk-management`, from `9eb2f41` (phase-13-forecasting).
- Base tip unmoved; `main` untouched at `eb6025b`.
- Migration head: 20261104_0011.

## DB counts before / after

| Measure | Before | After |
|---|---|---|
| risk_metric_definitions | 0 | 22 |
| risk_metric_values | 0 | 81 (46 computed + 35 insufficient_inputs) |
| risk_flags | 0 | 17 |
| risk_controls | 0 | 5 (v1) |
| risk_control_checks | 0 | 7 (5 pass + 1 breach + 1 blocked) |
| stress_scenarios | 0 | 5 |
| stress_results | 0 | 10 (4 computed + 6 insufficient_inputs) |
| financial_statements | 88 | 88 (untouched) |
| market_prices | 444 | 444 (untouched) |
| valuations | 51 | 51 (untouched) |
| economic_indicators | 12 | 12 (untouched) |
| news_events | 7 | 7 (untouched) |
| ownership_holdings | 34 | 34 (untouched) |
| forecast_assessments | 120 | 120 (untouched) |
| Phase 3 forecasts | 0 | 0 (untouched) |
| Phase 3 portfolios | 0 | 0 (untouched; reference portfolio is simulated only) |

Idempotency: second `--commit` wrote 0 new rows (all skipped).

## Tests and live checks

- New tests: 14 passed (pure: formulas, gating, registries).
- Full backend suite: 224 passed, 0 failed (210 prior + 14 new).
- Ruff check + format clean on all new/changed files.
- Live API: /risk/metrics, /risk/profile, /risk/market,
  /risk/controls, /risk/stress, /risk/status — all 200; unknown
  ticker 404; HBL profile 200 with no rows + pending note.

## Independent audit

- Hand-recomputed: HUBC largest category 38.27%, top-3 69.45%;
  market shock −10.000000%; idiosyncratic −6.666667% each;
  volumes and median match Phase 12 breadth rows.
- Audit corrections during this run: (1) beta/correlation test
  fixtures changed from constant to varying series — constant
  series have zero variance, so the functions correctly return
  None; (2) correlation test uses a 1e-9 tolerance for float
  sqrt rounding.
- No status promoted: every Phase 14 row is UNVERIFIED.

## HBL pending note

Habib Bank Limited (company 277, COMMERCIAL BANKS) has no risk
values, flags, checks or stress rows: its CY2025 statements are
not loaded (PDF blocked at download; live-browser download runs
separately). Design accepts HBL via a Phase 7 load plus a Phase 14
re-run; no redesign needed. The banking sector profile rule from
Phase 8 applies: industrial ratios must not be applied blindly
to a bank.

## Remaining blockers (exact unblockers)

1. Series risk metrics — more trading days of price data (Phase 5
   Terms-gated): 2 closes unlock drawdown; 30 returns unlock
   volatility/beta/correlation/downside; 251 unlock VaR/ES.
2. Gap risk — a price source file carrying previous_close
   (Phase 5 Terms-gated).
3. Turnover liquidity — a price source file carrying turnover
   (Phase 5 Terms-gated).
4. Sensitivity coefficients — floating/fixed debt splits,
   FX-denominated amounts, revenue elasticity (issuer documents
   or verified disclosures).
5. Sector volume HHI — per-sector volume shares (a breadth
   extension, not a new collection).
6. HBL rows — live-browser HBL CY2025 PDF download, then a
   Phase 7 load, then a Phase 14 re-run.
7. Wider-company coverage — Phase 7 expansion beyond the
   3-company sample.
8. VERIFIED promotion — H1 second agreeing source including an
   official source; everything stays UNVERIFIED until then.
