# Phase 3 — Indexing Strategy

Indexes follow the query patterns the later phases need, not a
generic "index everything" rule. Every UNIQUE grain constraint also
creates an index; the additional indexes below are the ones that
matter for time-series access.

## Time-series access (the hot path)

- market_prices (security_id, trading_date) — price history per
  security, the Phase 5/6 hot path.
- technical_indicator_values (security_id, observation_date).
- index_prices (index_code, trading_date).
- financial_statements (company_id, period_end).
- fundamental_metric_values (company_id, period_end).
- technical_signal_events (security_id, event_date).
- market_snapshots (snapshot_run_id, as_of) — as-of queries resolve
  to the latest snapshot at or before a PKT instant.
- symbol_history (security_id, effective_date) — rename resolution.
- audit_logs (entity_type, entity_id) — "who changed this row".
- data_quality_reports (affected_entity, affected_row_id).
- live_quotes (security_id, data_source_id, quote_instant).
- announcements (company_id, announcement_date).
- news (news_date).
- economic_indicators (indicator_code, observation_date).
- valuations / forecasts / recommendations (security_id, date /
  horizon / valid_from).

## Measured, not assumed

- 10,000-row bulk insert into market_prices: 0.49s (PostgreSQL,
  this VM, rolled-back test transaction).
- Count query over those 10,000 rows by security: 0.014s.
- With one row in a table, PostgreSQL correctly chooses a
  sequential scan; the Phase 3 test therefore asserts index
  *existence* in pg_indexes, not a planner choice. Planner behaviour
  at real scale is a Phase 5/6 measurement, not a Phase 3 claim.

## Deliberately NOT indexed (yet)

No partial indexes, no BRIN, no partitioning in Phase 3. The table
sizes in Phase 3 are zero production rows; partitioning a
zero-row fact table would be premature optimisation. Partitioning
by trading year is a Phase 5 decision, to be made after measuring
real ingest volumes.
