# Phase 16 — Risk / Sector Allocation Report

Prices: 2026-11-03 closes. Capital: hypothetical PKR 1,000,000.
Each name is its own sector in this 3–4 company universe, so
sector weights equal single-name weights here — that identity
is a property of the small universe, not a general claim.

## ew_statements_3_balanced (equal-weight baseline)

| Sector | Invested value | Invested weight | Capital weight |
|---|---|---|---|
| POWER GENERATION & DISTRIBUTION (HUBC) | 333,138.36 | 33.3314% | 33.3138% |
| TEXTILE COMPOSITE (NML) | 333,252.56 | 33.3428% | 33.3253% |
| OIL & GAS EXPLORATION COMPANIES (OGDC) | 333,082.11 | 33.3258% | 33.3082% |
| Cash | 526.97 | — | 0.0527% |

Largest sector: TEXTILE COMPOSITE at 33.33% of capital.
No sector cap applies (balanced max_sector_weight 1.00).

## rule_screen_pass_balanced

| Sector | Invested value | Invested weight | Capital weight |
|---|---|---|---|
| POWER GENERATION & DISTRIBUTION (HUBC) | 499,806.16 | 50.0016% | 49.9806% |
| OIL & GAS EXPLORATION COMPANIES (OGDC) | 499,774.98 | 49.9984% | 49.9775% |
| Cash | 418.86 | — | 0.0419% |

Largest sector: POWER GENERATION & DISTRIBUTION at 49.98% of
capital — just under the 50% single-name cap after whole-share
rounding (target sat exactly at the cap: effectively binding).
Excluded: NML (SCREEN_FAIL), HBL (SCREEN_NOT_RUNNABLE).

## rule_screen_pass_conservative

| Sector | Invested value | Invested weight | Capital weight |
|---|---|---|---|
| POWER GENERATION & DISTRIBUTION (HUBC) | 449,904.44 | 49.9958% | 44.9904% |
| OIL & GAS EXPLORATION COMPANIES (OGDC) | 449,979.66 | 50.0042% | 44.9980% |
| Cash | 100,115.90 | — | 10.0116% |

Largest sector: OIL & GAS EXPLORATION COMPANIES at 45.00% of
capital — under the 50% sector cap. Cash floor binding: the
invested amount was capped at 90% of capital; actual cash
10.0116% exceeds the floor only by whole-share rounding.
Excluded: NML (SCREEN_FAIL), HBL (SCREEN_NOT_RUNNABLE).

## Residual risks

- Concentration: 2-name portfolios carry ~50% single-name and
  single-sector weights. Diversification across 37 sectors is
  NOT achieved in this run — the universe is 3 statement
  companies, and claiming otherwise would be false.
- All inputs UNVERIFIED; forecasts abstained; no series risk
  metrics exist (Phase 14: volatility, beta, drawdown, VaR/ES
  all NOT_CALCULABLE on 1 price date).
- HBL (COMMERCIAL BANKS) has no position in any rule-based
  portfolio pending its Phase 7 load; the banking sector is
  therefore unrepresented in the rule-based sets.
