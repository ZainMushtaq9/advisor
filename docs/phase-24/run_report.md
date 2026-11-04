# Phase 24 — Run Report

Date: 2026-11-05. Base: `phase-23-dashboard` tip `6662d34`.
Branch: `phase-24-security` (new, from `6662d34`).
Migration: `20261104_0019` → `20261104_0020` (applied live).
Verdict: **PARTIALLY COMPLETE** (see gate judgement below).
No register files were edited (parent consolidates).
Phase 25 was not started.

## What was built

Auth + RBAC + security headers + rate limiting + enforcement
modes + append-only audit + local-operator CLI + 8 docs
(implementation specification, RBAC model, secret-handling
guide, audit logging, incident response plan, threat model,
vulnerability test report, this report). Zero new
dependencies (stdlib PBKDF2 + opaque SHA-256 tokens; no JWT
by design). No login over HTTP by design — account management
is CLI-only, so the admin surface does not exist on the
network at all. The API remains GET-only, including the new
auth router (3 routes: `/auth/status`, `/auth/me`,
`/auth/principal`).

## Live verification (all from real runs, not fixtures)

- **Migration:** applied from the Phase 24 checkout;
  `alembic current` = `20261104_0020 (head)`. Tables
  `auth_users`, `auth_tokens`, `auth_audit_logs` exist on
  PostgreSQL (Integer PKs with sequences, as designed).
- **Counts before → after:** companies 470 → 470; prices
  444 → 444; reports 22 → 22; alerts 89 → 89; statements
  88 → 88; rag_chunks 943 → 943; data_sources 19 → 19;
  auth_users 0, auth_tokens 0, auth_audit_logs 0 (empty by
  decision, see below). No business row changed; no quality
  status changed anywhere.
- **Live API smoke** (uvicorn on 127.0.0.1:8124, live DB):
  `/api/v1/auth/status` 200 with all security headers +
  `Cache-Control: no-store`; `/api/v1/auth/me` without token
  401; `/health` 200; `/api/v1/registry/statistics` 200
  (470/470/37, all UNVERIFIED, evidence 1001 — Phase 23
  state intact).
- **Live CLI reads:** `list-users` and `audit-log` against
  the live DB return empty, exit 0, and write nothing.
- **Scratch CLI cycle** (SQLite, deleted after): bootstrap
  admin (exit 0) → list-users shows admin, no hash/salt →
  login prints ONLY the token on stdout (stderr carries the
  note) → analyst creation with admin-token proof (exit 0)
  → service token for analyst refused (`role_not_allowed`,
  exit 1) → service token for admin issued → revoke by
  prefix (exit 0) → bad login denied (exit 1) → audit-log
  shows 4 rows (`account_created`, `login_success`,
  `token_issued`, `token_revoked`) with token prefixes only,
  no secrets.

## Live-DB seed decision (recorded)

**Scratch-proof only; no live seed rows.** No parent
confirmation exists for writing auth accounts into the live
DB, and silently writing test users there is forbidden.
The live DB therefore holds the migration (empty tables)
and zero accounts. Creating the first live administrator is
a parent/user decision: run `scripts/manage_auth.py
create-user --username <name> --role administrator
--operator-user bootstrap` once, with DATABASE_URL from
`database/.env`. Until then, enforced mode has no accounts
to validate against — which is itself fail-closed (401).

## Tests

- New: `backend/tests/test_auth_phase24.py`, 20 tests,
  all passing (passwords, tokens, roles, rate limiter,
  service flows incl. lockout, API status/me/headers,
  enforced mode, role dependency, production-settings
  validation, no-execution scan, SQLi probe, traversal probes).
- Full backend suite: **368 passed, 0 failed** (348 before
  + 20 new). Ruff check + format clean on all new/changed
  files. Frontend untouched (no frontend token support in
  this phase — see blockers).

## Corrections made during this run (not hidden)

1. Auth models first inherited mixins without `Base`
   (unmapped) — fixed.
2. `IdMixin`'s `Identity(always=True)` + BigInteger PKs do
   not auto-assign on SQLite — auth models + migration use
   portable Integer PKs (documented deviation; SERIAL on PG).
3. Detached-instance 500s in `optional_principal` and
   `/auth/me` (ORM attributes read after session close) —
   fixed by building plain dicts inside the session.
4. CLI traceback on a fresh DB ("no such table") — CLI now
   ensures its three tables idempotently (no-op on live).
5. CLI traceback on closed stdin (EOFError from getpass) —
   now exits 1 with a message.
6. Test fixture seeding of companies via ORM failed on
   SQLite for the same `IdMixin` reason — fixtures seed
   with explicit ids via raw SQL (test setup only).

## What computed vs what did NOT (Phase 24 is a security
phase, not an analysis phase — nothing numeric is computed)

Computed/delivered: the auth system, RBAC matrix, headers,
rate limiting, enforcement modes, audit store, CLI, docs,
and all tests/scans above. NOT_CALCULABLE does not apply
the way it does in analysis phases: no financial output was
produced, and no input status was changed. By design, this
phase adds no rows to any business table and promotes
nothing.

## HBL-pending note (unchanged)

HBL remains pending (CY2025 PDF blocked at the issuer-site
challenge; live-browser download runs separately, no result
yet). Phase 24 touches no company data and needs no HBL
input; a 4th company later requires no Phase 24 redesign
(roles and permissions are company-agnostic; the dashboard
already resolves by ticker).

## Gate judgement: PARTIALLY COMPLETE

The acceptance gate's testable items hold (roles enforced,
secrets not exposed, high-risk probed classes resolved or
explicitly blocked, tool boundaries + audit trails tested).
COMPLETE would misrepresent the remaining gaps, all listed
with unblockers in the vulnerability test report:

- No user accounts exist in production use (live seed
  decision above — needs a parent/user go-ahead).
- No external deployment exists (enforced mode unproven
  outside local smoke tests).
- Backup encryption not implemented (age/GPG + backup.sh
  change + restore test).
- Dependency audit not run (pip-audit/safety unavailable
  offline; run with network before any production deploy).
- Frontend token support for enforced mode not implemented.
- Report approval remains CLI-procedural, not token-gated.
- Audit-log retention policy (12 months) has no purge job.
- Rate limiting is single-process in-memory only.

No new blocker was introduced by Phase 24. The pre-existing
blockers (written PSX permission evidence, more trading
days, HBL PDF, verified local embedding model, internal
review for the first APPROVED report) are unchanged.
