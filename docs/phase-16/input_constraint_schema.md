# Phase 16 — Portfolio Input / Constraint Schema

Every simulated portfolio stores its full input schema in its
`constraints` JSON, so any construction can be reproduced exactly.
No input below is a suitability claim: risk profiles are
constraint sets, and suitability is a user-side judgement the
system does not make.

## Schema

```json
{
  "capital": "1000000",
  "base_currency": "PKR",
  "horizon": "not_specified",
  "risk_profile": "balanced | conservative | growth",
  "cash_floor": "0.00 | 0.10",
  "max_single_weight": "0.50 | 1.00",
  "max_sector_weight": "0.50 | 1.00",
  "eligible_tickers": ["HUBC", "OGDC"],
  "price_date": "2026-11-03",
  "cash_value": "418.8600",
  "cash_weight": "0.00041886",
  "cap_checks": {
    "max_single_weight": {"cap": "0.50", "actual": "0.499806", "pass": true},
    "max_sector_weight": {"cap": "1.00", "actual": "0.499806", "pass": true},
    "cash_floor": {"floor": "0.00", "actual": "0.00041886", "pass": true}
  }
}
```

- `capital`: hypothetical simulation capital (PKR 1,000,000),
  never real funds.
- `horizon`: `not_specified` in this run — no horizon return
  claim is made. A horizon return would need validated expected
  returns, which do not exist (Phase 13 abstained).
- `eligible_tickers`: tickers that passed BOTH gates for this
  portfolio (universe + valid quote, plus SCREEN_PASS for
  rule-based portfolios). Excluded tickers are stored separately
  in `portfolio_exclusions` with reason codes.
- `cap_checks`: post-construction verification, not an
  aspiration. A failed check raises and stores nothing.

## Risk-profile registry

| Profile | Cash floor | Max single weight | Max sector weight | Run? |
|---|---|---|---|---|
| conservative | 0.10 | 0.50 | 0.50 | Yes |
| balanced | 0.00 | 0.50 | 1.00 | Yes |
| growth | 0.00 | 1.00 | 1.00 | Defined-not-run (collapses to balanced on the 2-name set) |

User restrictions beyond these profiles (e.g. sector bans,
ticker bans) are supported by the exclusion mechanism: any
restricted ticker is recorded as an exclusion row with its
reason. No user restriction was supplied for this run, so none
is recorded beyond the screening exclusions.

## Assumptions block (stored per portfolio, shown separately)

| Assumption | Value | Reason |
|---|---|---|
| expected_returns | null | No validated expected-return source; Phase 13 computed 0 forecasts |
| historical_returns | null | 1 price date gives 0 return observations |
| forecasts | null | Phase 13 abstained on all 120 assessments; point-only values never stored |
| transaction_costs | null | No defensible fee/spread source in scope; excluded, not invented |
