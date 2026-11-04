# Phase 21 — Alert Rule Registry (v1)

Evaluation date 2026-11-04; price date 2026-11-03. Event times
are stored event dates at midnight Asia/Karachi; processing
time is the real run time, also Asia/Karachi.

| Rule | Category | Origin | Severity | Max age | Daily limit | Seed expectation |
|---|---|---|---|---|---|---|
| macro_release | MACRO_RELEASE | OFFICIAL | INFO | 30d | none | 2 alerts (MPC 2026-10-26, CPI 2026-11-02); 2 future scheduled suppressed |
| earnings_disclosure | FINANCIAL_DISCLOSURE | OFFICIAL | INFO | 90d | none | 1 alert (HUBC 2026-09-21); OGDC 2026-02-23 suppressed STALE; NML suppressed UNKNOWN_DATE |
| risk_flag_raised | RISK_BREACH | MODEL_WARNING | mapped | 30d | none | 17 alerts (6 WARNING, 11 INFO), one per stored flag |
| control_breach | RISK_BREACH | MODEL_WARNING | CRITICAL | 30d | none | 1 alert (single-name cap, SIMULATED portfolio only) |
| high_volume | PRICE_VOLUME_THRESHOLD | DERIVED | INFO | 7d | 100 | 68 alerts (volume >= 1,000,000 on 2026-11-03) |
| dividend_declared | DIVIDEND_ACTION | OFFICIAL | INFO | 90d | none | 0 alerts: all 5 stored actions dateless (NO_EVENT_DATE) |
| valuation_change | VALUATION_CHANGE | DERIVED | INFO | 30d | none | 0 alerts: one valuation run only (NO_SERIES) |
| technical_event | TECHNICAL_EVENT | DERIVED | INFO | 7d | none | 0 alerts: 0 calculable indicators (NO_SERIES) |
| price_move | PRICE_VOLUME_THRESHOLD | DERIVED | INFO | 7d | none | 0 alerts: previous_close NULL on all rows (NO_SERIES) |

Expected seed total: 89 alerts (2 + 1 + 17 + 1 + 68), all
starting NEW, all delivered in-app (seed profile has no quiet
window and no muted rules).

Taxonomy coverage: price/volume thresholds (high_volume,
price_move), technical events (technical_event), financial
disclosures (earnings_disclosure), dividend/corporate actions
(dividend_declared), news events (earnings_disclosure,
macro_release), valuation changes (valuation_change), macro
releases (macro_release), data failures (risk_flag_raised
market flags: missing_tickers_26, previous_close_absent,
turnover_absent, technical_coverage_zero), risk breaches
(risk_flag_raised, control_breach).

Severity mapping for risk flags: flag severity is carried
unchanged (info -> INFO, warning -> WARNING). No flag is
upgraded. The control breach is CRITICAL by rule definition
because it is a breached control, not because it is a real
position: its scope is the SIMULATED reference portfolio.
