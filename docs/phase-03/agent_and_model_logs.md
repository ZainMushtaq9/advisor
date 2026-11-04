# Phase 3 — Agent and Model Execution Logs

## Tables

agent_executions (agent_name, trigger, input_refs, started_at,
ended_at, status, model_version_id), agent_outputs (execution_id,
output_type, payload_ref, content_hash, payload JSON for
genuinely schemaless content only), model_versions (model_name +
version_string unique, config_snapshot_ref, metrics_snapshot,
status — immutable reference).

## Rules

1. **References, never secrets.** Execution logs carry input
   *references*, never payloads that could contain credentials.
   No log table has a column that could hold a password, token,
   API key or secret, and no log-writing code in Phase 3 accepts
   secret material. This is a schema + code rule, tested by
   column inspection.
2. **Version ids, not bare names.** Forecasts, valuations and
   executions reference model_versions.id. 'The model changed'
   can therefore never silently rewrite history: old rows point
   at the old version row, which is immutable.
3. **Outputs are artefacts with hashes.** Research reports are
   files on disk; agent_outputs stores reference + hash, not a
   duplicate copy. Business facts produced by an agent land in
   typed tables (prices, statements, ratios), not only in a JSON
   payload — the JSON payload is for genuinely schemaless
   content.
4. **No scheduler in Phase 3.** agent_executions records runs;
   it does not schedule them. No Celery Beat, no periodic jobs,
   no agent scheduler exists in Phase 3 (Phase 2 position carried
   forward). A run row without a scheduler row is normal.
5. **Cost/latency fields are not assumed.** Phase 1 left them
   undefined; Phase 3 does not invent cost columns. If a later
   phase defines them, they are added by migration, not by
   reinterpreting an existing column.
