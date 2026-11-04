# Phase 18 Agent Evaluation and Audit Logs

## Evaluation categories (stored as `agent_evaluations` rows)

| Category | Case | What PASS means |
|---|---|---|
| prompt_injection | prompt_injection_probe | Injected instruction flagged and quarantined |
| tool_failure | tool_failure_recovery | Tool failing twice recovers on attempt 3 within max_retries |
| loop_termination | loop_termination_guard | Never-converging loop terminates at MAX_LOOP_ITERATIONS |
| duplicate_action | duplicate_action_idempotency | Repeated idempotency key recognised as duplicate |
| hallucinated_value | hallucinated_value_quarantine | Numeric claim without evidence quarantined |
| deterministic_authority | deterministic_authority_gate | Claim disagreeing with the deterministic value quarantined |

An extra pure case (not a stored category) proves the permission boundary
itself: read-only write denial, no order tool in the vocabulary, and
consequential denial without a gate.

## Audit logs (`agent_audit_logs`)

One row per task, carrying: prompt/template reference, model identifier
(`rule-based-fallback-v1` in this phase), tool calls, token/resource use
where available (NULL for rule-based fallback — token use is not
applicable, and any claimed figure would be fabrication), output summary,
evidence references, error, and the quarantined flag.

Audit logs never carry full payloads that could contain credentials, and
never carry a secret. Input references, not input dumps, are the rule.

## What is NOT claimed

- No token/context measurement is asserted: with rule-based fallback there
  is no model context to measure. When an LLM path is ever enabled, token
  behaviour must be measured and recorded before any figure is asserted.
- No article figure (e.g. tool-result share of context, few-shot sizing,
  confidence thresholds) is adopted as a PSX fact. Thresholds must be
  calibrated per agent on measured behaviour, not copied.
- Paid security/monitoring products remain excluded: their functions are
  covered inside the fixed stack (PostgreSQL audit logs, FastAPI request
  validation, the audit agent). No PSX record is routed through a
  third-party moderation or guardrail API.
