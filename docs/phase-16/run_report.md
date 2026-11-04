# Phase 16 — Run Report (2026-11-04)

## Verdict: PARTIALLY COMPLETE

The construction engine, constraint schema, sector reports, and
GET-only APIs are complete and independently verified. The verdict
is PARTIALLY COMPLETE (not COMPLETE) because mean-variance is
NOT_CALCULABLE, coverage is 3–4 companies, and HBL has no
rule-based position pending its Phase 7 load. Nothing mandatory
is claimed as done that is not evidenced.

## DB counts before / after

- Before: 0 Phase 16 rows; migration head 20261104_0012.
- After: +3 simulated portfolios (all CONSTRUCTED, all
  UNVERIFIED), +7 holdings, +5 exclusions, +7 sector
  allocations, +3 comparisons (2 COMPUTED + 1 NOT_CALCULABLE).
  Phase 3 portfolios still 0; statements 88, prices 444,
  decisions 4 — all untouched. Migration head 20261104_0013.
- Idempotency proven: second `--commit` wrote 0 new rows
  (3 portfolios + 3 comparisons skipped). Holdings/sectors/
  exclusions are skipped implicitly via their portfolio skip.

## What computed vs NOT_CALCULABLE

**Constructed (3):** ew_statements_3_balanced (3 holdings,
invested 999,473.03, cash 526.97); rule_screen_pass_balanced
(2 holdings, invested 999,581.14, cash 418.86);
rule_screen_pass_conservative (2 holdings, invested 899,884.10,
cash 100,115.90). Every holding + cash reconciles to
PKR 1,000,000 exactly (Decimal values; weights stored at 6dp).

**Hand-verification (independent recomputation from DB prices):**
HUBC 197.24, NML 123.61, OGDC 303.63 on 2026-11-03. EW units
1689/2696/1097 with values 333,138.36/333,252.56/333,082.11;
balanced units 2534/1646 with values 499,806.16/499,774.98;
conservative units 2281/1482 with values 449,904.44/449,979.66.
All match the committed rows exactly.

**Eligibility probes (validation evidence):** ZZZZ =
NOT_IN_UNIVERSE (no security row); AGLNCPS =
IN_UNIVERSE_NO_QUOTE (security row, 0 price rows); HBL =
ELIGIBLE quote-wise (286.16) but rule-excluded
(SCREEN_NOT_RUNNABLE). Zero/negative prices are INVALID_QUOTE
by unit test (no such price exists in the 2026-11-03 set).

**NOT_CALCULABLE (never numbered):** mean-variance (no validated
expected returns — Phase 13 computed 0 forecasts; no covariance
— 0 return observations from 1 price date). Growth profile:
defined-not-run (collapses to balanced on the 2-name set).

## Tests and live checks

- New tests: 11 passed (pure: reconciliation, floor rounding,
  eligibility four-way distinction, mean-variance gating,
  profile registry, no-execution scan, GET-only endpoint).
- Full backend suite: see the commit verification (all prior
  suites plus the 11 new tests).
- Ruff check + format clean on all new/changed files.
- Live API: /portfolios 200 (3 portfolios, all reconcile);
  /portfolios/{name} 200 with holdings/sectors/exclusions;
  /portfolios/comparisons 200 (3 rows incl. mean-variance
  NOT_CALCULABLE); /portfolios/status 200; unknown portfolio 404.
- Execution-denied proof: the no-execution test scans
  application source (app + scripts, excluding tests) for
  execution identifiers (0 hits) and asserts the portfolios
  endpoint carries only @router.get decorators.

## HBL pending note

Habib Bank Limited (company 277, COMMERCIAL BANKS) has a valid
quote and appears in the eligibility evidence, but has no
rule-based position: its CY2025 statements are not loaded (PDF
blocked at download; live-browser download runs separately). A
Phase 7 load plus a Phase 16 re-run adds HBL's evidence without
redesign; the banking rule (no industrial ratios blindly
applied) carries forward.

## Remaining blockers (exact unblockers)

1. **Mean-variance** — validated expected returns (Phase 13
   evaluations on longer series) + a covariance matrix (≥2
   closes per security for one return; more for a stable
   estimate).
2. **HBL positions** — live-browser HBL CY2025 PDF download,
   then a Phase 7 load, then a Phase 16 re-run.
3. **Wider-company coverage** — Phase 7 expansion beyond the
   3-company sample (per-company source verification pass).
4. **Multi-day / risk-aware optimization** — more trading days
   of price data (Phase 5 Terms-gated) for returns, covariance,
   and series risk metrics.
5. **VERIFIED promotion** — H1 second agreeing source including
   an official source; everything stays UNVERIFIED until then.
