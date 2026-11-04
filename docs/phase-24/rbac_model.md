# Phase 24 — RBAC Model (least privilege)

## Permission names (closed list — nothing else is grantable)

| Permission | Meaning |
|---|---|
| `read:public` | Read public API data (registry, prices, published summaries) |
| `read:internal` | Read internal analysis rows (fundamentals, valuations, risk, decisions detail) |
| `read:audit` | Read audit trails (auth, agent, RAG access, alert runs) |
| `manage:users` | Create/disable/enable accounts, change roles (CLI only) |
| `manage:tokens` | Issue/revoke bearer tokens (CLI only) |

Nothing in this matrix grants an order, a publication, an
external send, or a quality-status promotion. Those actions
have **no permission name on purpose**: they cannot be granted
by role, because they do not exist as capabilities (no order
path, no publish step, no external-send path, no promotion
gate granted).

## Role matrix

| Role | Permissions |
|---|---|
| `user` | `read:public` |
| `analyst` | `read:public`, `read:internal`, `read:audit` |
| `administrator` | all five |
| `read_only_agent` | `read:public` |
| `service_process` | `read:public`, `read:internal` |

Rules:

- Unknown roles hold **no** permissions (fail closed).
- Administrators pass **every** role gate (documented here, so
  the `require_role` behaviour is a spec, not a surprise).
- `require_permission` returns 401 without a token, 403
  without the permission. `require_role` returns 401 without a
  token, 403 for a lesser role.
- Service tokens may be issued only for `service_process` and
  `administrator` accounts. User tokens may be issued for any
  active account. Disabled accounts get no token.
- Every role/permission check is a single function
  (`require_permission` in the service, mirrored by the
  FastAPI dependencies) used by both CLI and HTTP paths, so
  the two cannot drift apart.

## Phase 19 RAG role mapping (separate scheme, not merged)

Phase 19's document-level access control uses caller roles
`internal`, `external`, `auditor` with denials audited in
`rag_access_audits`. That scheme is about **which documents a
caller may see** (issuer-internal vs public), while this
scheme is about **which API/CLI operations an account may
perform**. They are deliberately not merged into one matrix:

| RAG caller role | Closest Phase 24 account role | Note |
|---|---|---|
| `internal` | `analyst` | Sees internal analysis + issuer documents already indexed |
| `external` | `user` | Public summaries only; RAG external answers are still denied where Phase 19 denies them |
| `auditor` | `analyst` (with `read:audit`) | Audit trails readable; never issuer-internal documents (Phase 19 rule preserved) |

Where both schemes apply (a future RAG HTTP endpoint), the
caller must satisfy **both**: a valid Phase 24 token with
`read:internal` (or `read:public` for public answers) AND the
Phase 19 document-level rule. The stricter denial wins.

## Phase 18 agent permission model (unchanged, referenced)

Phase 18 agents run under least privilege at the tool
boundary: consequential tools require a recorded human
approval gate; no gate has been granted, so they are denied
to every agent including the audit agent, which may FLAG but
never promote. Phase 24 does not change that model and does
not grant any agent a promotion capability. A future
Phase 24 account of role `read_only_agent` is the HTTP
equivalent of a Phase 18 read-only worker: it can read
public data and nothing else.

## Enforcement points

- HTTP: `EnforcementMiddleware` (enforced mode only) +
  `require_principal` / `require_role` / `require_permission`
  dependencies on routes. Today the API is GET-only, so these
  dependencies are exercised by tests against a mounted dummy
  route and documented as the mandatory pattern for any route
  added later. **A route that performs a state change without
  one of these dependencies is a review failure.**
- CLI: `manage_auth.py` requires administrator proof
  (`--operator-token` with a valid administrator bearer token,
  or first-admin bootstrap) for create-user, disable/enable,
  set-role, and revoke-token. Login needs no operator token
  (it IS the authentication).
