# Phase 6 — Completion report

## Verdict: PARTIALLY COMPLETE

Branch: phase-06-technical-analytics.
Commit: 5342e2b (29 files, +4500/−1; completion report itself
committed separately as the tip — see git log).
Push: NOT pushed (standing GitHub credential failure + the
user's keep-local choice). Merge to main: NOT merged (needs
separate user approval).

## What was built

- Deterministic indicator framework (pure Decimal Python, no
  network, no clock, no LLM): 62 registered indicator outputs
  across trend / momentum / volatility / volume / risk, with
  documented formula conventions (Wilder smoothing, SMA-seeded
  EMA, population-std Bollinger, nearest-rank VaR/ES,
  prior-bar pivots, no-look-ahead Ichimoku storage).
- Validation harness + coverage engine: every indicator for
  every security answered CALCULABLE or NOT_CALCULABLE with a
  reason and the exact unblocker; conflicted inputs flagged,
  never silently included; quality inherited, never upgraded.
- Aggregation: daily -> weekly (ISO weeks) / monthly, always
  partial without a validated calendar, missing OHLC raised
  cleanly, intraday refused.
- Signal engine, kept separate, with an empty activated-rule
  set: zero events, no decision engine, no buy/sell language.
- Read-only APIs (coverage, per-ticker coverage, stored
  values, stored signals) with the scope note on every
  response; CLI with --dry-run / --commit and a re-run guard;
  /indicators frontend page with API-driven totals and
  truthful empty states, no chart from a single point.
- Migration 20261104_0005: immutability triggers on the four
  output tables (proven to fire on UPDATE and DELETE with
  zero residue). No new tables — Phase 3's model was reused.

## What the data supports today (and only this)

- The framework, validated on synthetic multi-day series.
- The coverage verdicts, the run/error records, the APIs with
  transparent explanations, and immutability enforcement.
- NOTHING ELSE. Zero indicator values, zero signal events,
  zero regime features exist on production data.

## The honest headline (unchanged by the audit)

All 62 indicators are NOT_CALCULABLE for all 470 securities:
insufficient_warmup for the 444 one-bar securities (except
daily_return, which is missing_data for all 470 because
previous_close is blank on every row), missing_data for the
26 zero-bar securities. Full matrix with unblockers:
coverage_and_limitations.md.

## Test and audit evidence

- Backend: 114 passed, 0 failed. Ruff clean. Frontend:
  typecheck, lint, build (12 routes), Vitest 11 passed.
- Live API inspection: coverage 200 (470/62/0, as_of
  2026-11-03 after the audit fix); OGDC 1 bar, 0 calculable;
  values 0; signals 0; 404/422 paths verified.
- Live run: phase06-coverage-2026-11-03, completed, 470
  processed, 0 values, 124 error rows (63 missing_data, 61
  insufficient_warmup). A second --commit reported
  already_recorded and wrote nothing.
- Independent audit: PASS WITH LIMITATIONS. All findings
  (H1–H4, M1–M10, L1–L11) FIXED; see independent_audit.md.

## What would unblock each item

- Short-window indicators: more trading days (SMA(5) after 4
  more days; SMA(200) after 199; VaR/ES after 250).
- Daily return: a present previous_close in a future source
  file (value would remain UNVERIFIED on single-source data).
- Aggregated indicators: many trading days AND a validated
  trading calendar.
- Regime features: calculable values first, then versioned
  thresholds. Signal events: activated rules with evaluators
  plus calculable inputs.
- Adjusted indicators: a validated corporate-action
  methodology (none exists).
- COMPLETE verdict: calculable values on real data (value
  rows > 0 through a committed run) AND written resolution of
  the PSX Terms internal-use question.

## Terms and scope statements (do not soften)

- Terms NOT cleared: permission requested 2026-11-04 16:58
  PKT; the reply was reported then permanently deleted; the
  Phase 5 commit landed on the user's explicit override; the
  user is handling the permission side later. Phase 6 sent no
  PSX email and collected no new external data.
- Scope: Main Board / Normal Counter only (470 securities).
  GEM (5) and Non-Compliant (93) not captured. KSE-100
  completeness not established. All prices UNVERIFIED
  single-source. No VERIFIED, full-market, or KSE-100 claim.
- Phase 5 remains PARTIALLY COMPLETE; Phase 6 does not mark
  it complete.
- No publication, redistribution, sale, or commercial use of
  PSX data. Local private use only. No real trades, no
  broker/order path, no guaranteed returns, no paid services.

## STOP

Phase 6 ends here. Phase 7 is NOT started (spec truncated;
remainder must be requested from the user, never invented).
