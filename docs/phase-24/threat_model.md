# Phase 24 — Threat Model

## Assets

1. Stored financial data (registry, prices, statements, ratios,
   valuations, macro, reports) — integrity matters more than
   confidentiality here: all inputs are UNVERIFIED and the
   harm is a wrong number being trusted, not a leak.
2. Credentials (DB role password, user passwords, bearer
   tokens) — hashes only, by design.
3. Administrative capability (account/token management) —
   CLI-only, shell access required.
4. Audit trails — tamper-evidence matters: append-only stores.
5. The codebase itself — a malicious commit could add an
   execution path where none exists today.

## Actors

| Actor | Capability | Out of scope |
|---|---|---|
| Local operator (shell access) | Everything via CLI + DB | — (trusted by definition; shell access IS the admin boundary) |
| Dashboard visitor (browser) | Public GET APIs in permissive mode | Cannot write, order, publish, or promote anything (no such routes) |
| Bearer-token holder | Reads per role (enforced mode) | Cannot exceed role; cannot promote quality status; cannot order |
| Network attacker (no token) | Sees public GET data in permissive mode; 401 in enforced mode | Cannot reach the DB directly (no DB port exposure in this setup) |
| Malicious content (retrieved documents, news, user input) | Can reach agent inputs and API filters | Treated as untrusted data (Phase 18 quarantine; parameterized queries; capped snippets) |

## Threats and mitigations (STRIDE, project-scoped)

| Threat | Mitigation in place | Residual risk |
|---|---|---|
| Spoofing (stolen token) | Tokens opaque, hashed, expiring (24 h / 90 d), revocable by prefix; lockout on passwords | Token theft within its TTL window; no device binding (accepted: local-only use) |
| Tampering (SQL injection) | ORM parameterized queries everywhere; injection-shaped input tested to return 0 rows | LIKE wildcards (`%`, `_`) in the companies search are functional, not a bypass — search returns registry rows only, which are public universe data |
| Tampering (path traversal) | No file-serving from user input; no upload endpoints; traversal probes return 404/422 | None identified |
| Tampering (audit deletion) | Auth audit has no update/delete function; agent/RAG audits append-only | A shell-access operator (DB superuser) could still delete rows — that is the trusted-operator boundary, not an app flaw |
| Repudiation | Every account/token/admin action audited with actor + outcome | Validation successes not audited per call (volume decision; `last_used_at` is the record) |
| Information disclosure (secrets) | Hashes only; secret-key stripping in audit writer; names-only config reporting; generic errors; docs off in production | Backup files unencrypted (known gap, see run report) |
| Information disclosure (data) | Quality + computation-status badges; UNVERIFIED labels; snippets capped at 500 chars; no document bodies served | Permissive mode serves all GET data to any local visitor — intended for local development, NOT for a network deployment |
| Denial of service | In-memory rate limits (300/min API, 30/min auth) + 429 | Single-process only; a multi-instance deployment needs edge limiting (documented) |
| Elevation of privilege | Closed permission list; unknown roles get nothing; admin proof required for CLI admin commands; administrators pass role gates by explicit design | CLI bootstrap path: first-admin creation requires shell access AND zero existing administrators — safe only because shell access is the trust boundary |
| Prompt injection (agent) | Phase 18 quarantine (probe quarantined, stored HUBC close unchanged at 197.2400); retrieved content treated as untrusted data | No LLM-backed execution exists to inject into (fallback only) — the threat is latent, not live, until a local model is verified |
| Supply chain (dependencies) | All pins recorded in `backend/requirements.txt`; no new dependencies added in this phase | No dependency audit tool run (pip-audit/safety unavailable offline) — must run before any production deployment |
| Execution path introduction | No-execution source scan (0 hits) run in this phase and as a test | A future commit could add one — the scan test must stay in the suite and be run on every phase |

## Trust boundaries (diagram in words)

```
browser (Phase 23 dashboard, no credentials)
    │  HTTP, permissive mode: anonymous GET only
    ▼
FastAPI app ── headers + rate limit + (enforcement, when on)
    │  Bearer token validated per request (enforced mode)
    ▼
PostgreSQL (local) ── role password from database/.env only
    │
CLI operator (shell) ── getpass passwords, stdout-once tokens
    └── admin proof required for account/token management
```

The shell boundary is the security boundary: anyone with
shell access can already read `database/.env` and the DB.
Phase 24 does not pretend otherwise — it protects the
network surface and the operator workflow, and it says so.

## Threat-model updates

This document is versioned with the phase. It must be
revisited when any of these change: first external deployment,
first real user account in production use, first verified
local LLM (agent execution becomes live), first publish step,
or any new write route. Each change re-opens the rows above.
