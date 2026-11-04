# Phase 3 — Entity Catalog

This catalog records the grain, key fields and versioning rule of
every table. Full column lists are the source of truth in
`backend/app/models/` (reference.py, market.py, financial.py,
analysis.py, governance.py) and in migration `645bcd200539`.

## Counting note (read before citing a number)

Phase 1 specified 33 entities. Phase 3 implements 54 tables, and
the decomposition (corrected after audit M5 — an earlier draft
said '33 plus 21' and omitted two tables from its own enumeration)
is: 32 Phase 1 entities realised verbatim + the 'ratios' entity
split into 2 tables (fundamental_metric_definitions +
fundamental_metric_values) + 20 extension tables = 54. The 20
extensions are: company_identifiers, trading_sessions,
financial_documents, financial_document_versions,
financial_document_downloads, index_prices,
fundamental_analysis_runs, fundamental_trend_observations,
earnings_quality_observations, financial_health_assessments,
sector_metric_profiles, fundamental_warning_events,
technical_indicator_definitions, technical_indicator_configurations,
technical_indicator_values, quantitative_market_features,
market_regime_observations, technical_signal_events,
technical_calculation_runs, technical_calculation_errors.

The Phase 1 'ratios' entity is realised as definition + value
rows. Audit M5 fix: the three properties the split first dropped
are restored — fundamental_metric_values now carries security_id
(per-security multiples such as P/E), computation_status
(computed/failed/insufficient_inputs, so NULL is distinguishable
from 'not yet computed'), and input_price_ids (price linkage for
price-based multiples). input_statement_ids remains JSON, not a
foreign-key array, so dangling statement references are possible;
that gap is accepted and recorded (see phase_03_completion_report
§ audit response, M2/M5), to be validated at write time by Phase 8
services. There is no second, duplicate ratio table; a reader
looking for 'ratios' should look at the definition + value tables.

## Versioning classes (after audit-fix migration 20261104_0004;
23 triggers total)

- **Append-only, trigger-blocked on UPDATE/DELETE (12):**
  audit_logs, market_prices, raw_payloads, market_snapshots,
  announcements, news, index_prices, corporate_actions,
  symbol_history, model_versions, forecast_evaluations,
  agent_outputs.
- **Resolution-only (1):** data_quality_reports — only
  resolution_status and resolved_at may change (audit H2 fix);
  detail and all other columns are immutable.
- **Marker-only (2):** live_quotes (only is_latest may change),
  agent_executions (only status and ended_at may change as a run
  progresses).
- **Versioned, trigger allows ONLY is_current changes (8):**
  financial_statements, financial_statement_line_items,
  financial_document_versions, economic_indicators, valuations,
  forecasts, recommendations, financial_health_assessments. A
  figure change must be a new row.
- **Mutable by design (current state + audit):** companies,
  securities, sectors, portfolios, portfolio_holdings (effective
  dates), live_quotes (is_latest marker), calculation runs, users,
  roles, data_sources (registry), sector_metric_profiles.

## Provenance block (all market/financial/news/analysis rows)

data_source_id, source_key, source_timestamp (when the source says
the observation is for), collected_at (when WE fetched it, PKT),
quality_status (shared vocabulary, CHECK-enforced on 21 tables).
Collection time is never an observation time; a fetch time is never
a source timestamp.

## Money and units

Numeric columns use NUMERIC (no floats for money). Line items keep
original_displayed_value (as printed, parentheses/dashes preserved),
numeric_value, currency, reported_unit and normalized_value plus
the normalization rule. A blank, dash or missing amount is never
stored as zero unless the document explicitly supports it.
