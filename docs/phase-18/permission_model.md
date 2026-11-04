# Phase 18 Permission Model

Enforced in `backend/app/services/orchestration/permissions.py`, at the
tool-call boundary — not inside any agent's prompt.

## Tiers

1. **READ_ONLY** — safe to run unattended. No writes at all. Applies to:
   market_data, company_discovery, historical_research, statements,
   fundamentals, technicals, sector, news, macro, valuation, forecasts,
   risk, portfolio.
2. **ORCHESTRATION_WRITE** — may write orchestration/audit tables only
   (runs, tasks, audit logs, evaluations). Never protected financial
   tables. Applies to: audit, reports, monitoring.
3. **CONSEQUENTIAL** — publishes a record, changes a verification status,
   or sends anything outside the system. Requires a recorded human
   approval gate. **No agent holds this tier in this phase and no gate has
   been granted**, so consequential tools are denied to all.

## Rules

- A tool call is permitted only if the tool is in the agent's
  `allowed_tools` AND its cost does not exceed the agent's cost envelope
  (PKR 0 for every agent — any paid tool is denied).
- Unknown agents and unknown tools are denied (fail closed).
- The audit agent may FLAG (write an audit row); it may NOT promote a
  quality status. Promotion is consequential and ungranted.
- The review queue is owned by the monitoring agent, not by the agent
  that produced the output. A queued item is never presented as verified
  while it waits, and the queue never drains into approval on timeout.
- Approval gates, where the mechanism is tested, are in-process only:
  `grant_approval` records a gate in memory for the calling process. It is
  never persisted, never loaded from disk, and never granted by the runner.
  Production runs with zero granted gates.
- No agent prompt or audit log ever contains a password, token, API key,
  or database credential. Audit logs carry input references, never full
  payloads that could contain secrets.

## Protected tables

Every financial, market, registry, and verification table is protected:
no agent may write to it in this phase. Only tables prefixed `agent_` or
`orchestration_` may be written, and only by ORCHESTRATION_WRITE agents.
