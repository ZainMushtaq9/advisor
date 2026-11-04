# Phase 20 — Market Screener and Opportunity Discovery: Implementation Specification

## Objective (playbook lines 1508–1564)

Allow users and agents to find securities matching transparent
technical, fundamental, valuation, liquidity, event, and risk
criteria — with documented calculation semantics, data-quality
and missing-field indicators on every result, saved screens
that reproduce exactly, and an opportunity ranking that never
labels a screen result a guaranteed investment opportunity.

## Entry dependency — what was actually available

The brief's entry check asks for a "verified company universe
and upstream metrics, valuation, news, macro and risk APIs."
The honest state at Phase 20 entry:

- Universe: 470 Main Board / Normal Counter securities, all
  UNVERIFIED (Phase 4). 444 have a 2026-11-03 price; 26 do
  not (13 Phase 5 rejections + 13 absent).
- Upstream metrics: fundamentals for 3 companies (HUBC, NML,
  OGDC), valuations for the same 3, risk values for the same
  3, news events for the same 3 + 4 macro events, ownership
  for HUBC only, decisions for 4 companies (HUBC, NML, OGDC,
  HBL). Technical indicators: 0 calculable values.
- Nothing is VERIFIED except 6 Phase 10 macro observations
  (SBP/PBS cross-publisher agreement); every screener input
  carries its recorded quality, never higher.

Consequence for design: price/volume screens run over all 470
securities; fundamental/valuation/dividend screens run over
the 4 decision companies only. A screen that pretended to
cover 470 companies on fundamentals would be fabrication.

## Architecture

```
stored rows (Phases 4–19)
  -> runner.load_universe()      # one dict per security, no SQL from user input
  -> filters.evaluate_filter()   # pure pass/fail/missing/not_applicable
  -> ranking.score_outcomes()    # screener-score-v1: passed / scored
  -> ScreenDefinition / ScreenRun / ScreenResult (migration 0017)
  -> GET-only API (filters, screens, results, status)
  -> CLI scripts/run_screener.py (--dry-run default / --commit)
```

No arbitrary user SQL exists anywhere: filter entries are
validated against the registry (known key, supported kind,
known operator, present threshold) and raise ValueError
otherwise. Pagination is validated (limit 1..100, offset
>= 0). Sorting supports exactly two keys (score, ticker).

## Tables (migration 20261104_0017)

- `screen_definitions`: (name, version) unique; filters JSON;
  universe scope; quality UNVERIFIED.
- `screen_runs`: (definition, as_of_date) unique; universe
  size, matched count, insufficient count, status, evidence.
- `screen_results`: (run, security) unique; outcome
  MATCH / NO_MATCH / INSUFFICIENT_DATA; score (NULL when
  nothing scored); passed/scored counts; reason codes;
  evidence JSON (per-filter outcomes, decision context,
  disclaimer).

Idempotency: re-running a committed (definition, as-of)
pair writes 0 rows; the stored run is reused and reported.

## Seed screens (v1, as-of 2026-11-04, price date 2026-11-03)

| Screen | Universe | Filters | Result |
|---|---|---|---|
| liquid_leaders | 470 | price present AND volume >= 100,000 | 194 MATCH |
| volume_top_decile | 470 | volume percentile >= 90 | 44 MATCH, 26 INSUFFICIENT_DATA |
| cheap_profitable | 4 decision companies | P/E < 10 AND ROE > 0 | HUBC MATCH only |
| dividend_payers | 4 decision companies | dividend action present | HUBC, NML MATCH |
| technical_momentum | 470 | SMA(5) present | 0 MATCH, 470 INSUFFICIENT_DATA |

Total: 5 definitions, 5 runs, 1,418 results, 241 matches.

## What did NOT compute (with reasons)

- Technical filters (sma_5, rsi_14): NOT_CALCULABLE for all
  470 — Phase 6 holds 0 calculable values (5 closes needed
  for SMA(5), 15 observations for RSI(14), 1 trading date
  exists). Registered to prove null handling, never to
  fabricate a value.
- Fundamental/valuation filters for the 466 non-statement
  securities: MISSING_VALUE (no computed row), except
  HBL (COMMERCIAL BANKS): SECTOR_NOT_APPLICABLE under the
  Phase 8 banking rule — industrial ratio semantics must not
  be applied blindly to a bank.
- P/B, P/S, market cap, EV multiples, DCF, DDM, peer medians:
  not offered as filters — Phase 9 recorded them
  insufficient_inputs / not_applicable, and the screener does
  not resurrect them.
- Mean-variance or any optimized ranking: not offered —
  Phase 16 recorded mean-variance NOT_CALCULABLE (no
  validated expected returns, no covariance matrix).
- Any "opportunity" labelling, recommendation, or forecast:
  refused by design. Every result and every API response
  carries the disclaimer; Phase 15 user-facing values are
  WITHHELD and ride along as evidence only.

## Independent audit

- Direct SQL recounts agree: definitions 5, runs 5, results
  1,418, matches 241 (194 + 44 + 1 + 2 + 0).
- cheap_profitable rows re-derived by hand from stored
  values: HUBC P/E 5.1553 < 10 and ROE 0.2242 > 0 → MATCH
  1.0000; OGDC P/E 17.8816 fails, ROE 0.0535 passes → NO_MATCH
  0.5000; NML P/E missing, ROE −0.0074 fails → NO_MATCH
  0.0000 with scored 1; HBL both filters not_applicable →
  INSUFFICIENT_DATA with scored 0.
- Independent percentile SQL (strictly-below count / 444)
  reproduces 44 top-decile matches exactly.
- Untouched tables verified unchanged: statements 88,
  prices 444, decisions 4, rag_chunks 943, agents 16.
- HUBC close still 197.2400 (screener writes no price rows).
