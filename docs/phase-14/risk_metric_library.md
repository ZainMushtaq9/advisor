# Phase 14 — Risk Metric Library (22 definitions)

| Metric | Category | Minimum | Window | Unit | Scope |
|---|---|---|---|---|---|
| volatility | market | 30 returns | 30 daily returns | pct | security |
| beta_vs_benchmark | market | 30 pairs | 30 daily return pairs | ratio | security |
| max_drawdown | market | 2 closes | full close series | pct | security |
| downside_deviation | market | 30 returns | 30 daily returns | pct | security |
| var95_hist | market | 251 returns | 251 daily returns | pct | security |
| es95_hist | market | 251 returns | 251 daily returns | pct | security |
| correlation_vs_market | market | 30 pairs | 30 daily return pairs | ratio | security |
| gap_risk | market | 1 session | one session with previous_close | pct | security |
| volume_liquidity_tier | liquidity | 1 session | 2026-11-03 session | shares | security |
| turnover_liquidity | liquidity | 1 session | 2026-11-03 session | pkr | security |
| sector_participation | concentration | 1 session | 2026-11-03 session | pct | sector |
| priced_coverage | concentration | 1 session | 2026-11-03 session | pct | market |
| top10_volume_share | concentration | 1 session | 2026-11-03 session | pct | market |
| largest_holder_share | concentration | 1 | as at reporting date | pct | security |
| top3_holder_share | concentration | 1 | as at reporting date | pct | security |
| sector_volume_hhi | concentration | 1 session | 2026-11-03 session | index | market |
| fx_sensitivity_coeff | sensitivity | 1 | per exposure | pkr_per_pct | security |
| rate_sensitivity_coeff | sensitivity | 1 | per exposure | pkr_per_100bps | security |
| commodity_sensitivity_coeff | sensitivity | 1 | per exposure | pkr_per_pct | security |
| forecast_abstention_rate | model | 1 | as at run date | pct | market |
| technical_coverage_rate | model | 1 | as at run date | pct | market |
| input_drift | model | 2 vintages | two vintages | pct | market |

Formulas are stated in full in `backend/app/services/risk_analytics/__init__.py`
and implemented in `formulas.py`. VaR/ES warm-ups (251) follow the
Phase 6 convention. A metric below its minimum is stored as
insufficient_inputs with the exact reason — never zero, never
estimated.

## Computed values in this run (46)

- Volume tiers: HUBC HIGH (3,218,965 shares), NML MEDIUM (445,059),
  OGDC MEDIUM (737,659); median 54,631.5; HIGH ≥ 1,000,000.
- Sector participation: 37 sectors, 66.666667%–100% (market 94.468085%).
- Top-10 volume share: 49.249694%.
- HUBC largest holder category: 38.270000% (INDIVIDUAL_LOCAL);
  top-3 categories: 69.450000%.
- Forecast abstention rate: 100.000000% (120/120 Phase 13 assessments).
- Technical coverage rate: 0.000000% (0/470).

## Insufficient values in this run (35)

- 24 series-metric rows (8 metrics × 3 securities).
- 3 turnover-liquidity rows.
- 1 sector volume HHI row.
- 6 sensitivity-coefficient rows.
- 1 input-drift row.
