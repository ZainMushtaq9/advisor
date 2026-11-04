# Phase 3 — Relationships and Constraints

## Foreign-key policy

- Securities reference companies.id (RESTRICT on delete: a company
  with securities cannot be deleted out from under them).
- Prices, quotes, holdings, forecasts, valuations and
  recommendations reference securities.id, never a bare ticker
  string, so renames (symbol_history) cannot corrupt history.
- Statement line items CASCADE from their statement version; a
  version is never deleted in practice (versioned trigger), the
  CASCADE exists for schema hygiene, not as a data-deletion path.
- Provenance data_source_id is SET NULL on source deletion, so a
  registry cleanup can never silently orphan the fact that a row
  came from a source — the source_key string remains on the row.
- Dividends are UNIQUE on corporate_action_id (one-to-one), so a
  dividend event cannot be double-counted across the two tables.

## Uniqueness = grain enforcement

- market_prices: (security, trading_date, bar_type, data_source_id)
- index_prices: (index_code, trading_date, data_source_id)
- financial_statements: (company, period_start, period_end,
  statement_type, version_number, data_source_id)
- financial_statement_line_items: (statement, line_item_key,
  version_number)
- fundamental_metric_values: (company, metric_definition,
  period_end, calculation_version)
- technical_indicator_values: (security, configuration,
  observation_date, timeframe)
- economic_indicators: (indicator_code, observation_date,
  version_number)
- trading_calendars / trading_sessions: (exchange, date)
- sectors: (source, source_sector_name)
- company_identifiers: (identifier_type, identifier_value)
- sector_metric_profiles: (sector, metric_key)
- model_versions: (model_name, version_string)
- data_sources: source_key; raw_payloads: content_hash.

Audit H3 fix: data_source_id is NOT NULL on the three grain
tables whose unique constraint includes it (market_prices,
index_prices, financial_statements), so the NULL-source duplicate
hole is closed at the schema level, not merely by an ingest rule.
Other provenance tables keep a nullable source (computed values
have no external source row), and their grains do not include the
source, so the hole does not apply there. Hash uniqueness
(audit M6 fix): announcements (company_id + document_hash),
financial_documents (company_id + content_hash) and news
(content_hash) carry partial unique indexes excluding NULL hashes;
NULL-hash rows go to human review, per the duplicate-key helper.

## CHECK constraints (migration 20261104_0003)

quality_status vocabulary on 21 tables. Forecast interval_low,
interval_high and uncertainty are NOT NULL by column definition.
No CHECK exists for lifecycle statuses (company/security status)
because those vocabularies are still being verified in Phase 4;
they are documented strings, not yet constrained.
