# Phase 3 — Schema Reference (54 tables)

All tables use BIGINT identity primary keys and tz-aware
`created_at` (server default `now()`). Grain and key rules are in
`entity_catalog.md`; this file is the quick index.

## Reference / masters

| Table | Grain | Notes |
|---|---|---|
| exchanges | code | PSX primary; timezone Asia/Karachi |
| sectors | source + source_sector_name | Both 38- and 37-sector taxonomies kept as rows; never harmonised before verification (G-03) |
| companies | legal issuer | NOT per ticker; status lifecycle incl. DELISTED/SUSPENDED |
| company_identifiers | type + value | Previous identifiers kept, never overwritten |
| securities | tradable instrument | Current ticker only; history in symbol_history |
| symbol_history | security + effective_date | Append-only; ENGRO -> ENGROH is the verified case |
| trading_calendars | exchange + date | Absence = unknown, NOT closed |
| trading_sessions | exchange + date | Status: completed/partial/missing/holiday/unknown |
| users, roles, user_role_assignments | person / role | Display identity only; NO credential columns |

## Market (append-only)

market_prices (security x date x bar_type x source; unadjusted only),
live_quotes (security x source x instant; is_latest marker),
market_snapshots (run x as-of x security/index), index_prices
(index_code x date x source), corporate_actions (security x event),
dividends (1:1 with dividend corporate_actions), announcements
(hash + URL, no PDF bytes), news (hash, third-party, distinct from
announcements).

## Financial / fundamentals / technicals

financial_statements (company x period x type x version x source),
financial_statement_line_items (statement version x key; original
label + displayed value + normalized value + unit + rule),
financial_documents / _versions / _downloads (company + hash
partial unique index on documents; versions carry is_current),
fundamental_metric_definitions + _values (Phase 1 'ratios' realised
here — no second ratio table), technical_indicator_definitions /
_configurations / _values, quantitative_market_features,
market_regime_observations, technical_signal_events,
technical_calculation_runs / _errors.

## Economics / analysis / portfolios / governance

economic_indicators (code x observation_date x version; revision
preserved), valuations, forecasts (interval_low, interval_high and uncertainty NOT NULL;
bear/base/bull scenarios and probabilities nullable, correctly —
a method that cannot produce them flags that instead of inventing
them),
forecast_evaluations, recommendations (versioned, probabilistic),
portfolios + portfolio_holdings (paper only; securities.id, never a
bare ticker), agent_executions + agent_outputs (references only, no
secrets), model_versions, data_sources, data_quality_reports,
raw_payloads (SHA-256 hash-addressed), audit_logs (append-only),
fundamental_analysis_runs, fundamental_trend_observations,
earnings_quality_observations, financial_health_assessments
(score NULL = INSUFFICIENT_DATA, never a credit rating),
sector_metric_profiles, fundamental_warning_events.
