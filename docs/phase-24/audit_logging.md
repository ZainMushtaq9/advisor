# Phase 24 — Audit Logging

## Unified audit map (all four audit stores, one reading)

| Store | Table | What it records | Who writes | Mutable? |
|---|---|---|---|---|
| Phase 18 agent audit | `agent_audit_logs` | Agent actions, tool calls, quarantine decisions | Orchestration runner | Append-only by design (no update path) |
| Phase 19 RAG access | `rag_access_audits` | Document access allow/deny by caller role | RAG assistant | Append-only |
| Phase 21 alert runs | `alert_runs` + `alert_deliveries` | Alert evaluation runs, delivery outcomes | Alert runner | Append-only runs; alert lifecycle states change, runs do not |
| Phase 24 auth audit | `auth_audit_logs` | Account + token + access events (below) | Auth service | **Append-only: no update or delete function exists in the module** (tested) |

Reading rule: no single store tells the whole story. A
security review joins them by time window: an auth denial
(`auth_audit_logs`) at the same time as an agent quarantine
(`agent_audit_logs`) and a RAG denial (`rag_access_audits`)
is one incident with three witnesses, not three incidents.

## Phase 24 auth audit events

| Action | Outcome | Recorded on |
|---|---|---|
| `account_created` | success / failure (duplicate, weak password, unknown role) | Every create attempt |
| `login_success` / `login_failed` | success / failure (`bad_password`, `disabled`, `locked`) | Every authenticate attempt; locked accounts are denied WITHOUT checking the password (so a lockout cannot be used as a password oracle) |
| `token_issued` | success / failure (`role_not_allowed`, `disabled`) | Every issue attempt |
| `token_validated` | denied (`revoked`, `expired`, `disabled`, `locked`, `unknown_token`, `malformed_token`) | Every failed validation; successes stamp `last_used_at` but write no audit row (to avoid one row per API call — see note) |
| `token_revoked` | success | Every revoke-by-prefix |
| `role_changed` / `account_disabled` / `account_enabled` | success / failure | Every admin change |
| `access_denied` | denied | Every CLI admin-proof failure (with reason) |

Audit rows carry: actor, action, target, outcome, detail
(JSON, secret-stripped), created_at. The token itself, its
hash, and any password never appear (tested). Token rows are
referenced by prefix only.

Note on validation successes: they are NOT audited per call
(deliberate volume decision — every enforced API call would
otherwise write a row). `last_used_at` on the token row is the
lightweight success record. If per-call success auditing is
ever required, it must be added as a sampled or buffered
writer, not a row per request.

## Retention policy (documented, not yet enforced)

- Auth audit logs: retain 12 months, then purge by a
  scheduled job that deletes rows older than 12 months and
  writes a single summary row (count purged, date range).
  **No purge job exists yet** — this is a Phase 25 candidate,
  and until it exists, logs accumulate (acceptable: the table
  is small and the deployment is local-only).
- Agent, RAG, and alert audit rows: retain per their own
  phase policies (no change in this phase).

## Review procedure

1. `scripts/manage_auth.py audit-log [--limit 50]` lists
   recent auth events (human-readable, no secrets).
2. Investigate in this order: repeated `login_failed` from
   one actor (brute-force signal — lockout should already
   have fired at 5); `access_denied` on CLI admin commands
   (privilege-escalation attempt); `token_validated` denials
   with reason `revoked` (use of a revoked token — possible
   replay after a suspected exposure).
3. Cross-check against `agent_audit_logs` (quarantines) and
   `rag_access_audits` (denials) in the same window before
   concluding.
