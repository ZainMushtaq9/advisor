# Phase 14 — Control Rules v1 and Checks

Rules are versioned configuration for SIMULATED portfolios only.
No rule here executes, orders, or trades anything. A new version
supersedes the old one; old versions are never edited.

## Rules v1 (effective 2026-11-04)

| Control | Threshold | Rationale |
|---|---|---|
| single_name_cap_pct | 25% | No single name above 25% in a simulated portfolio |
| sector_cap_pct | 50% | No single sector above 50% |
| drawdown_warning_pct | −10% | Warn when portfolio drawdown reaches −10% |
| min_daily_volume_shares | 50,000 | Near the 2026-11-03 median volume (54,631.5 shares) |
| min_diversification_names | 3 | At least 3 names |

## Checks against the simulated reference portfolio

Reference portfolio: equal-weight HUBC/NML/OGDC (simulation only).

| Control | Scope | Outcome | Observed | Threshold | Reason |
|---|---|---|---|---|---|
| single_name_cap_pct | SIMULATED_PORTFOLIO | breach | 33.333333% | 25% | 3-name equal weight breaches by construction — the breach is the finding, not a reason to move the threshold |
| sector_cap_pct | SIMULATED_PORTFOLIO | pass | 33.333333% | 50% | Each name in a different sector |
| drawdown_warning_pct | SIMULATED_PORTFOLIO | blocked | — | −10% | No drawdown computable from one price date; blocked, never passed by default |
| min_diversification_names | SIMULATED_PORTFOLIO | pass | 3 | 3 | Meets the minimum |
| min_daily_volume_shares | HUBC | pass | 3,218,965 | 50,000 | 2026-11-03 volume |
| min_daily_volume_shares | NML | pass | 445,059 | 50,000 | 2026-11-03 volume |
| min_daily_volume_shares | OGDC | pass | 737,659 | 50,000 | 2026-11-03 volume |

## Missing-data rule (acceptance gate)

A check that cannot run is BLOCKED, and a blocked check never
counts as a pass. Downstream decisions requiring a blocked input
(forecast, drawdown, gap, turnover) are blocked with the same
reason, not downgraded silently.
