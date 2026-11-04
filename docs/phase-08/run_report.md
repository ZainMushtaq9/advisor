# Phase 8 — Run report (calculation version 1.0, health-v1)

Verdict: **PARTIALLY COMPLETE** (see blockers below). The engine,
tests, API, and committed runs are complete and verified; COMPLETE
is blocked by input coverage, not by implementation.

## Run summary

- Run key: `phase08-fundamental-1.0`. First `--commit`: 108 value
  rows, 24 health rows, 8 warning rows, 108 sector-profile rows
  written. Second `--commit`: 0 new rows, 108 values skipped as
  existing — idempotency proven.
- Stored values are rounded to 6 decimals by the Numeric(24,6)
  column; full-precision values are in the CLI JSON report.
- All written rows are UNVERIFIED (0 non-UNVERIFIED rows).
  Statements/line items unchanged (88 / 1,316).

## Per-company results

| Company | Period | Computed | Insufficient | Not applicable |
|---|---|---|---|---|
| HUBC (289) | FY2026 annual | 32 | 4 (roic, pe, pb, div_yield) | 0 |
| NML (394) | 9M to 31 Mar 2025 | 31 | 5 (+ roe_owners) | 0 |
| OGDC (403) | 6M to 31 Dec 2025 | 28 | 7 (+ op_margin, roce, roe_owners) | 1 (interest_coverage) |

### Headline values (reconciled against independent precomputation)

HUBC FY2026: gross margin 0.4174, operating margin 0.4790, net
margin 0.7909 (includes Rs 45,315,750 thousand post-tax associate
profit — see sector_profiles.md), ROA 0.1344, ROE total 0.2242,
ROE owners 0.2181, ROCE 0.1034, current 1.4171, quick 1.2877, cash
0.3870, debt/assets 0.3894, debt/equity 0.6378, interest coverage
3.7291x, receivables days 157.5, inventory days 65.3, payables
days 292.2 (upper bound — total payables as printed), revenue
growth −0.1467, PAT growth +0.0866, EPS growth +0.0759, OCF
Rs 11,428,574 thousand, FCF Rs 10,493,558 thousand, cash
conversion 0.2031, dividend coverage 0.2802x, accruals
Rs 44,828,604 thousand.

NML 9M Mar 2025: gross margin 0.1552, operating margin 0.0676,
net margin −0.0076 (LOSS of Rs 1,182,815 thousand), ROA −0.0042,
ROE total −0.0074, ROCE 0.0421, current 1.3664, quick 0.5607, cash
0.1146, debt/assets 0.4544, debt/equity 0.8330, interest coverage
1.5288x, receivables days 57.0, inventory days 145.7, payables
days 42.3, revenue growth −0.0213, PAT growth −1.1480
(sign-change flagged), EPS growth −1.0242 (sign-change flagged),
OCF Rs −5,371,036 thousand, FCF Rs −13,560,990 thousand, cash
conversion 4.5409 (both-negative flag — not strength), dividend
coverage −2.0602x, accruals Rs 4,188,221 thousand.

OGDC 6M Dec 2025: gross margin 0.5365, net margin 0.3787, ROA
0.0437, ROE total 0.0535, current 9.6215, quick 9.3567, cash
0.0989, debt/assets 0.1796, debt/equity 0.2190, IB debt/equity
0.0018 (leases only), receivables days 571.3, inventory days
63.1, payables days 244.9, revenue growth −0.0659, PAT growth
−0.1145, EPS growth −0.1142, OCF Rs 50,012,941 thousand, FCF
Rs −3,926,587 thousand, cash conversion 0.6849, dividend
coverage 1.3679x, accruals Rs 23,006,307 thousand.

### Health-v1 dimension scores

| Dimension | HUBC | NML | OGDC |
|---|---|---|---|
| profitability | 100.0000 | 0.0000 | 73.3333 |
| liquidity | 73.3333 | 46.6667 | 73.3333 |
| solvency | 100.0000 | 73.3333 | 100.0000 |
| efficiency | 60.0000 | 80.0000 | 60.0000 |
| cash_flow | 46.6667 | 20.0000 | 46.6667 |
| growth | 40.0000 | 0.0000 | 0.0000 |
| earnings_quality | 20.0000 | 60.0000 | 40.0000 |
| sector | NULL | NULL | NULL |

Descriptive only — NOT a credit rating, NOT investment advice, NOT
a buy/sell signal. No aggregate grade is produced.

### Warning events (8, all review-only)

- HUBC: low_cash_conversion, receivables_growing_faster_than_revenue.
- NML: negative_profit_after_tax, negative_operating_cash_flow,
  pat_growth_sign_change, eps_growth_sign_change,
  cash_conversion_both_negative.
- OGDC: receivables_days_over_one_year.

## Verification

- Backend suite 147 passed, 0 failed (140 prior + 7 new).
- Ruff check + format clean on all new/changed files.
- Dry-run values reconciled against an independent
  precomputation: 60 ratio values exact; 7 days values within
  0.001 (precomputation intermediate quantisation).
- Live API: ratios 200 (36 metrics), health 200, HBL pending 200,
  unknown ticker 404, sector-profiles 200 (empty until commit).
- Second `--commit` idempotency: 0 new rows.

## HBL pending

Habib Bank Limited (company 277, COMMERCIAL BANKS) has no ratios,
health rows, warnings, or sector profile: its CY2025 statements are
not loaded (PDF blocked at download; live-browser download runs
separately). Adding it needs one PERIODS entry + one KEY_MAP entry
plus a banking sector profile (industrial ratios must not be
applied blindly to a bank).

## Remaining blockers (exact unblockers)

1. **KSE-100 / wider-company expansion** — unblocker: Phase 7
   expansion beyond the 3-company sample (per-company source
   verification pass). Phase 8 computes only for companies with
   loaded statements.
2. **HBL statements** — unblocker: the separate live-browser
   download of the HBL CY2025 PDF, then a Phase 7 load, then a
   Phase 8 re-run with HBL added.
3. **Market multiples (pe/pb/div_yield)** — unblocker: an adjusted
   price series with a corporate-action methodology, share-count
   data, and statement-publication alignment.
4. **ROIC** — unblocker: a validated NOPAT tax-allocation
   methodology that separates post-tax associate earnings.
5. **OGDC operating margin / ROCE / interest coverage** —
   unblocker: operating-profit and finance-cost lines in OGDC
   statements (or an explicit structural ruling that they do not
   exist for this issuer).
6. **VERIFIED promotion of any output** — unblocker: H1 second
   agreeing source including an official source; all inputs and
   outputs stay UNVERIFIED until then.
7. **TTM ratios** — unblocker: full-year income rows for NML/OGDC
   (or a validated TTM construction rule).
