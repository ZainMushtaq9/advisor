# Phase 17 — Bias report (production, derived live)

| Check | Result | Evidence summary |
|---|---|---|
| point_in_time | no_bias_detected | Prices 2026-11-03, HUBC publication 2026-09-21, OGDC publication 2026-02-23 all on/before decision date 2026-11-04. Handled exception: NML publication NULL, gated out (Phase 15 SCREEN_FAIL), so no decision uses it. |
| survivorship | no_bias_detected | All 470 registry securities retained; none dropped. Limitation: no delisting feed is loaded (delisting_date NULL everywhere), so inactive-security handling is limited to retention. |
| selection | bias_disclosed | Statement-driven strategies cover 3 of 470 companies; the rest have no fundamental inputs. |
| corporate_actions | bias_disclosed | 5 dividend actions, all without dates; 0 applied. Price-based returns would carry dividend bias. |
| stale_prices | bias_disclosed | Single price date (2026-11-03); NML latest period end 2025-03-31 is 583 days old (> 365-day threshold). |
| missing_data | bias_disclosed | 26 tickers without a 2026-11-03 price (13 Phase 5 rejections + 13 absent), named in the stored evidence, never dropped. |
| cost_sensitivity | not_applicable | Zero production trades; sensitivity exists on fixtures only. |

A bias_disclosed row is a finding, not a phase failure: the bias
is documented with its evidence instead of being silently baked
into a result. The full per-check evidence is stored in
backtest_bias_reports.
