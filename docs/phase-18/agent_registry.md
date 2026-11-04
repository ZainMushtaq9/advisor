# Phase 18 Agent Registry

Source of truth: `backend/app/services/orchestration/__init__.py`
(`AGENT_REGISTRY`), persisted as `agent_definitions` rows.

## The 16 brief roles

| Agent | Tier | Failure mode | Timeout (s) | Retries |
|---|---|---|---|---|
| market_data | READ_ONLY | retry_then_fail | 120 | 3 |
| company_discovery | READ_ONLY | retry_then_fail | 120 | 3 |
| historical_research | READ_ONLY | skip_with_reason | 300 | 2 |
| statements | READ_ONLY | retry_then_fail | 300 | 2 |
| fundamentals | READ_ONLY | retry_then_fail | 180 | 3 |
| technicals | READ_ONLY | abstain | 180 | 3 |
| sector | READ_ONLY | retry_then_fail | 180 | 3 |
| news | READ_ONLY | quarantine | 180 | 3 |
| macro | READ_ONLY | retry_then_fail | 180 | 3 |
| valuation | READ_ONLY | abstain | 180 | 3 |
| forecasts | READ_ONLY | abstain | 180 | 2 |
| risk | READ_ONLY | retry_then_fail | 180 | 3 |
| portfolio | READ_ONLY | retry_then_fail | 180 | 3 |
| audit | ORCHESTRATION_WRITE | quarantine | 300 | 2 |
| reports | ORCHESTRATION_WRITE | retry_then_fail | 600 | 2 |
| monitoring | ORCHESTRATION_WRITE | retry_then_fail | 120 | 3 |

Every agent: cost envelope PKR 0, execution backend `rule_based_fallback`,
status ACTIVE.

## Reconciliation: 16 vs 18

The Phase 1 spec spoke of 18 agents; the Phase 18 brief enumerates 16 worker
roles. 16 workers + the orchestrator (supervisor) + the router = 18 named
components. The orchestrator and router are runtime functions, not worker
agents, so the registry holds exactly the 16 brief roles.

## Rules that bind every agent

- Advisory only: no worker writes financial, market, registry, or
  verification rows.
- Read-only agents write nothing at all. ORCHESTRATION_WRITE agents
  (audit, reports, monitoring) write orchestration/audit tables only.
- No agent duplicates a deterministic service or merely restates another
  agent's output: deterministic work (indicators, ratios, valuations) goes
  to Python functions, never to an agent; agents quote tool results.
- Workers do not spawn each other recursively; the orchestrator owns
  decomposition, routing, and completion criteria.
- A fixed workflow is used wherever the steps are known in advance
  (most of Phases 5–10); autonomous behaviour is reserved for genuinely
  open-ended retrieval, and even then inside the bounded contract.
