# Phase 18 Capability Contracts

Each registry entry is a contract with exactly these fields:

| Field | Meaning |
|---|---|
| `name` | Agent key (unique) |
| `role` | Human-readable role |
| `scope` | Bounded scope, including what the agent must never do |
| `inputs` | Declared inputs |
| `outputs` | Declared outputs (structured, evidence-referenced) |
| `allowed_tools` | Exact tool set the runtime permits |
| `permissions_tier` | READ_ONLY / ORCHESTRATION_WRITE / CONSEQUENTIAL |
| `timeout_seconds` | Cooperative timeout budget (checked between checkpoints) |
| `max_retries` | Retry cap |
| `backoff_seconds` | Backoff schedule per retry |
| `cost_envelope_pkr` | 0 for every agent (free only) |
| `failure_mode` | retry_then_fail / quarantine / skip_with_reason / abstain |
| `execution_backend` | `rule_based_fallback` in this phase |
| `status` | ACTIVE |

## Tool vocabulary

- Read tools (all READ_ONLY agents, plus all others):
  `read_source`, `query_db_readonly`, `read_document`, `compute_deterministic`
  (`compute_deterministic` calls a deterministic service for a value; it
  never writes a financial row).
- Orchestration tools (ORCHESTRATION_WRITE agents only):
  `write_audit`, `update_task_status`.
- Consequential tools (approval-gated; none granted in this phase):
  `write_staging`, `publish_record`, `change_quality_status`, `send_external`.
- No order tool exists in the vocabulary. No permission can grant one.

## Failure modes

- `retry_then_fail`: retry up to max_retries with backoff, then FAILED with
  a checkpoint (recovery re-queues without duplicating side effects).
- `quarantine`: output withheld on injection or mismatch; task QUARANTINED,
  evidence logged, stored values untouched.
- `skip_with_reason`: optional enrichment skipped with a recorded reason;
  never silently dropped.
- `abstain`: insufficient evidence → no output value (the forecasts /
  technicals / valuation pattern: abstention, not estimation).

## LLM path (future, not enabled)

Enabling LLM-backed execution for any agent requires, in order: a verified
local/open-weight model on this host, a licence check, a quality check
against the rule-based fallback on the same tasks, and a registry update
recording the model identifier. Until then, audit logs record
`rule-based-fallback-v1` with token use NULL, and any claim of token usage
would be fabrication.
