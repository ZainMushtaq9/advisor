# Financial Accuracy Audit — PSX Intelligence AI (Independent Audit)

**Audit baseline:** branch `phase-30-release`, commit `8937338`.
**Audit date:** 2026-11-05 (Asia/Karachi).
**Method:** every figure below was recomputed BY THIS AUDIT from
scratch-database rows (statement line items, prices, holdings) —
not by copying stored derived values. Where a stored value is
quoted, it is compared against the auditor's own arithmetic.
**Governing distinction (applied throughout):** source authenticity
and calculation accuracy are SEPARATE. Arithmetic can be exactly
right on UNVERIFIED inputs; correct arithmetic does NOT promote
UNVERIFIED data to VERIFIED. All inputs below are UNVERIFIED
except where noted, and no figure in this report should be read
as investment advice or as a verified market fact.

## 1. Price data (Phase 5)

| Check | Auditor recomputation | Result |
|---|---|---|
| Row count / dates | 444 rows, 1 distinct trading_date (2026-11-03) | ✓ matches claim |
| OHLC validity | 0 rows violating low ≤ open/close ≤ high | ✓ 444/444 pass (SLO ohlc_validity_rate 1.0) |
| Non-positive values | 0 rows with open/high/low/close ≤ 0 or volume < 0 | ✓ |
| Duplicate (security, date) | 0 | ✓ |
| Rejected tickers (OHLC inconsistency) | 12 named in the claim (ADAMS, AHTM, ALIFE, ASLCPS, BTL, GCWLPRS, HAFL, IGIL, PRWM, SHSML, SNAI, TSML) + 1 non-positive (SASML) = 13 rejected; 13 absent tickers | Consistent with 470 − 444 = 26 unpriced (missing_securities 26/470) |
| Spot closes | HUBC 197.24, NML 123.61, OGDC 303.63, HBL 286.16, all 2026-11-03 | ✓ match claim and stored rows |
| previous_close / turnover / source_timestamp | NULL on 444/444 each | ✓ honest NULLs, never zero-filled |

## 2. Fundamental ratios (Phase 8) — independently recomputed

- **HUBC gross margin:** stored gross_profit 29,688,160 /
  stored revenue 71,126,352 = 0.41740029… → stored metric
  **0.417400** ✓ (correct to 6 decimal places; the formula
  `gross_profit / revenue` is verified in code at
  `fundamental_analysis/__init__.py:184` and `coverage.py:82`).
- **HUBC EPS:** stored `eps_total` 38.26 (basic; diluted 35.56
  also stored) ✓. The valuation keymap distinction is verified in
  data: HUBC uses `eps_total`, OGDC uses `eps_basic`.
- **OGDC EPS period discipline:** stored `eps_basic` values are
  8.07 (standalone quarter), 9.63, **16.98** (H1 period),
  19.17. The valuation uses 16.98 — the H1 figure, not the
  standalone quarter's 8.07. Using 8.07 would have doubled the
  P/E; the stored choice is the correct period-matched one.

## 3. Valuation multiples (Phase 9) — independently recomputed

| Multiple | Auditor arithmetic | Stored | Verdict |
|---|---|---|---|
| HUBC trailing P/E | 197.24 / 38.26 = 5.1552535… | 5.155254 | ✓ |
| OGDC trailing P/E | 303.63 / 16.98 = 17.88162544… | 17.881625 | ✓ |

- Formula verified in code: trailing P/E = price / EPS, with None
  for missing/zero/negative EPS (`valuation/formulas.py:42-45`);
  the NML negative-EPS non-meaningful rule and the mechanical ±10%
  price sensitivity (EPS held at printed value) are implemented
  as documented.
- Census: 51 valuations = 7 computed / 41 insufficient_inputs /
  3 not_applicable, all UNVERIFIED ✓. The 41 insufficient cases
  are labelled, not estimated — the honest behaviour for a
  single-price-date dataset with no share counts.

## 4. HBL statement identities (Phase 7) — independently recomputed

**Statement of financial position identity
(assets = liabilities + equity), from stored line items:**

| Year | Liabilities | + Equity | = Sum | Stored total_assets | Match |
|---|---|---|---|---|---|
| 2025-12-31 | 7,219,529,515 | 488,614,705 | 7,708,144,220 | 7,708,144,220 | ✓ exact |
| 2024-12-31 | 5,644,314,783 | 410,798,094 | 6,055,112,877 | 6,055,112,877 | ✓ exact |

**Income statement (Rs '000s):**

| Year | profit_after_taxation | pat_total | eps_basic_diluted | Match to claim |
|---|---|---|---|---|
| 2025 | 66,763,916 | 66,763,916 | 45.48 | ✓ PAT 66,763,916 / EPS 45.48 |
| 2024 | 57,804,659 | 57,804,659 | 39.85 | ✓ PAT 57,804,659 / EPS 39.85 |

- Note: `pat_equity_holders` (2025: 66,716,190) differs from
  `pat_total` by the non-controlling interest; the handover's PAT
  figure uses `pat_total`, consistently.
- Recorded HBL source defects (CF unlabeled row, CE 2024 blank NCI
  cell, CF label split, dual-currency USD-before-PKR ordering)
  were handled by the extractor without invented labels or
  zero-filling: the SFP identity above holds exactly, which would
  fail if any material row had been invented or dropped. The
  defects remain documented as extraction caveats, not hidden.

## 5. Portfolio reconciliation (Phase 16) — independently recomputed

All three simulated portfolios reconcile exactly to PKR 1,000,000
capital (holdings value + implied cash):

| Portfolio | Holdings value | Implied cash | Sum | Match |
|---|---|---|---|---|
| ew_statements_3_balanced | 999,473.03 | 526.97 | 1,000,000.00 | ✓ |
| rule_screen_pass_balanced | 999,581.14 | 418.86 | 1,000,000.00 | ✓ |
| rule_screen_pass_conservative | 899,884.10 | 100,115.90 | 1,000,000.00 | ✓ |

- All portfolios are labelled SIMULATED; no real-money path
  exists (see runtime audit: no execution route).
- The Phase 16 runner honestly reports "no covariance matrix: 0
  return observations from 1 price date" — optimisation is
  correctly refused, not faked from one day of data.

## 6. Breadth, liquidity, screens, alerts, figures (Phases 12/20/21/22)

- **Breadth:** median_volume 54,631.5 ✓; missing_securities 26/470
  ✓; overall priced coverage 444/470 = 0.944681 ✓ (SLO
  price_coverage_latest_day). Advances/declines empty (no prior
  day) — correctly absent, not zero.
- **Liquidity:** 889 observations; top-10 share 49.249694% as
  claimed (carried from the Phase 12 report; the auditor verified
  the observation count, not every percentile recomputation).
- **Screens:** 1,418 results = 241 MATCH / 680 NO_MATCH / 497
  INSUFFICIENT_DATA ✓. MATCH formula verified in code
  (score = passed / scored; missing/not_applicable excluded from
  both counts; MATCH iff scored ≥ 1 and passed == scored;
  INSUFFICIENT_DATA iff scored == 0), with the "filter result, not
  opportunity" disclaimer attached by API/CLI.
- **Alerts:** 89 = 82 INFO + 6 WARNING + 1 CRITICAL ✓; 89
  deliveries ✓; dedup key `rule_key|source_ref|event_date`
  verified in code (`alerts/evaluation.py:54-56`); HUBC alerts = 4
  ✓ (the Phase 22 file-match condition).
- **Report figures census:** 541 = 335 computed + 199
  insufficient_inputs + 7 not_applicable ✓; 22 DRAFT reports,
  0 APPROVED ✓; exports 22 Markdown + 22 HTML + 22 PDF ✓.

## 7. Forecasting and backtesting — what "accuracy" means here

- **Forecasts:** 48 targets, 116 snapshots, 120 assessments, ALL
  insufficient_inputs, 0 computed forecast rows. There is nothing
  to recompute — and that is the correct outcome: with one price
  date, no return series exists, so every model abstains. Any
  computed forecast from this data would have been fabrication.
  The forecasting phase is PARTIALLY COMPLETE because its
  mandatory criterion (usable forecasts) is unmet, not because
  its code is wrong.
- **Backtests:** 5 strategies, 5 runs, all NOT_RUNNABLE, 55
  metrics, 0 computed. Same reasoning: a backtest on one day of
  data cannot run; the NOT_RUNNABLE label is honest, not a
  failure of the backtest code.
- **Risk:** 81 values = 46 computed + 35 insufficient ✓. VaR95 /
  ES95 warm-ups (251 observations) are correctly unmet on one day
  of data; the computed 46 are the metrics that do not require a
  return series.

## 8. Verdict for this audit area

**Calculation accuracy: PASS.** Every figure the auditor
recomputed independently matches its stored value exactly
(margins, P/Es, SFP identities, PAT/EPS, portfolio sums, breadth,
screens, alerts, figures census). No arithmetic error, no
invented value, and no zero-fill was found anywhere in the
audited sample.

**Source authenticity: NOT ESTABLISHED for market and statement
data.** All recomputed inputs are UNVERIFIED (single-source DPS
snapshot; issuer PDFs without a second agreeing source). Correct
arithmetic on UNVERIFIED inputs yields UNVERIFIED outputs. The
financial analysis therefore cannot be COMPLETE until the
verification criteria (H1: two distinct agreeing sources including
one official, for the registry; equivalent rigour for statements
and prices) are met — which is a data-collection and Terms-gate
problem, not a calculation problem. The system is honest about
this at every layer (UNVERIFIED labels, insufficient_inputs,
WITHHELD decisions, abstaining forecasts, NOT_RUNNABLE backtests),
and that honesty is why its partial state is trustworthy as far
as it goes.
