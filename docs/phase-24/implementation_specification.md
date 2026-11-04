# Phase 24 — Implementation Specification

Authentication, Authorization, Security and Governance.
Brief: playbook lines 1742–1800. Base: `phase-23-dashboard` tip
`6662d34`. No database writes were made by Phase 23, so the
migration head at entry was `20261104_0019`.

## Entry state (verified, not assumed)

- No authentication code existed. The only prior "password"
  mentions in models were disclaimers that no column there
  stores a password, API key, or secret.
- CORS was already restricted (localhost:3000 / 127.0.0.1:3000
  only, wildcard rejected in production, credentials off,
  methods GET-only).
- The API was already GET-only (no POST/PUT/PATCH/DELETE
  routes); no upload endpoints; no outbound fetch of
  user-supplied URLs (no SSRF surface); no pickle, YAML load,
  eval, or exec in app code; one subprocess use (tesseract
  OCR, fixed argv, no shell, temp dir, 300 s timeout).
- Settings never log or return values (config-status reports
  names only); error handlers are generic (no stack traces).
- Installed security packages: only `cryptography` 50.0.2.
  No passlib, bcrypt, PyJWT, slowapi, pip-audit, or safety.

## Design decisions (each with its reason)

1. **No new dependencies.** Passwords use stdlib PBKDF2-HMAC-SHA256
   (600,000 iterations, 32-byte per-user salt, `hmac.compare_digest`).
   Tokens are opaque (`psx_` + 32 bytes `secrets.token_urlsafe`),
   stored as SHA-256 hex only. No JWT: opaque tokens need no
   signing-key management, are revocable by deleting one row,
   and carry no claims that could be misread as authorization.
2. **No login over HTTP.** There is deliberately no login,
   registration, password-change, or token-issue route. Account
   management happens through the local CLI (`scripts/manage_auth.py`)
   by an operator with shell access. The admin surface does not
   exist on the network at all — this is the brief's "protect
   administrative endpoints" requirement taken to its strongest
   form for a GET-only API with no account system.
3. **Two enforcement modes.** `AUTH_ENFORCEMENT=off` (development
   default): requests are anonymous unless a Bearer token is
   presented, in which case it is validated and the principal
   attached; nothing is denied for lacking a token, so the
   Phase 23 dashboard (public GET calls, no credentials) keeps
   working. `AUTH_ENFORCEMENT=on`: every `/api/v1` request
   without a valid token is 401; role/permission gates return
   403. Production refuses to boot with enforcement off.
   `/health` and `/api/v1/auth/status` stay public in both modes
   (liveness must not require credentials; status discloses
   mode and role names only, never secrets).
4. **Fail closed everywhere.** Unknown roles hold no permissions.
   Malformed tokens, expired/revoked tokens, disabled/locked
   accounts, and missing database engines all deny. Naive
   datetimes fail closed in token expiry (with one documented
   normalization: datetimes the service wrote as aware UTC are
   reattached to UTC on read, because SQLite strips tzinfo;
   PostgreSQL round-trips them aware).
5. **CSRF: not applicable today, rule for tomorrow.** The API is
   GET-only, uses no cookies, and has no state-changing route,
   so there is no ambient credential for a cross-site request
   to ride on. Any future POST/PUT/PATCH/DELETE route must use
   Bearer-token auth (never cookies) and carry a role or
   permission dependency, or it fails review.
6. **Rate limiting is single-process, in-memory** (fixed window,
   keyed by client IP + route group; general API 300/min,
   `/api/v1/auth/*` 30/min, both from settings; over-limit
   returns 429 + `Retry-After` and the handler never runs).
   Documented as NOT a substitute for edge rate limiting in a
   multi-instance deployment.
7. **Security headers on every response**: nosniff, DENY framing,
   no-referrer, restrictive Permissions-Policy, CSP
   `default-src 'none'; frame-ancestors 'none'; sandbox`.
   Auth responses add `Cache-Control: no-store`.
8. **OpenAPI docs disabled in production** (docs/redoc/openapi
   URLs set to None when `ENVIRONMENT=production`): the schema
   discloses route structure and must not be served to
   unauthenticated callers.

## What was built

| Area | Files |
|---|---|
| Models | `backend/app/models/auth.py` — `auth_users`, `auth_tokens`, `auth_audit_logs` |
| Roles | `backend/app/services/auth/__init__.py` — closed permission list + matrix |
| Passwords | `backend/app/services/auth/passwords.py` — PBKDF2, policy (12 chars, 3 of 4 classes, small blocklist floor) |
| Tokens | `backend/app/services/auth/tokens.py` — opaque, SHA-256 stored, TTLs (user 24 h, service 90 d) |
| Service | `backend/app/services/auth/service.py` — create/authenticate/issue/validate/revoke/role/active, append-only audit with secret-key stripping, lockout (5 fails, 15 min) |
| Dependencies | `backend/app/services/auth/dependencies.py` — optional/require principal, require_role, require_permission |
| Middleware | `backend/app/services/auth/middleware.py` — headers, rate limiter, enforcement |
| Config | `backend/app/config.py` — 7 new settings + production enforcement check (last in validator, so existing wildcard-CORS and DEBUG errors still raise first) |
| App wiring | `backend/app/main.py` — docs off in production, middleware mounted (enforcement → rate limit → headers; Starlette runs last-added first, so denied requests still carry headers) |
| Endpoints | `backend/app/api/v1/endpoints/auth.py` — GET-only: `/auth/status`, `/auth/me`, `/auth/principal` |
| Migration | `database/migrations/versions/20261104_0020_phase_24_auth.py` — revision `20261104_0020`, revises `20261104_0019` |
| CLI | `scripts/manage_auth.py` — create/list/disable/enable/set-role/login/issue-service-token/revoke-token/audit-log; passwords via getpass only; tokens printed once on stdout only; admin proof via `--operator-token` or first-admin bootstrap |
| Tests | `backend/tests/test_auth_phase24.py` — 20 tests |

## Deliberate deviations from the Phase 3 model pattern

- Auth tables do **not** use `IdMixin`. `IdMixin` uses
  `Identity(always=True)` (PostgreSQL-only); a BigInteger PK is
  not a rowid alias on SQLite, so inserts fail NOT NULL there.
  Auth tables use a plain Integer PK with autoincrement (SERIAL
  on PostgreSQL, INTEGER rowid alias on SQLite). The migration
  matches exactly. Account counts will never approach 2^31.
- Auth tables carry **no quality_status**: they are access-control
  records, not business data, and no quality-status promotion
  ever applies to them.

## What Phase 24 does NOT do (honest scope boundary)

- No user accounts exist in production use yet (see run report
  for the live-DB decision). No external deployment exists.
- Backup encryption is NOT implemented (`database/backup.sh`
  has no encryption). Unblocker: age/GPG key management +
  backup.sh change + restore test.
- Dependency audit tooling (pip-audit/safety) is NOT installed
  and cannot run offline; pins are recorded, no clean audit claimed.
- Frontend token support for enforced mode is NOT implemented
  (the Phase 23 dashboard calls public GET APIs without
  credentials — hence permissive mode as development default).
- Report approval remains a CLI transition with procedural
  administrator control only; the Phase 22 CLI was not modified
  to require an admin token (a Phase 25 hardening candidate).
- Audit-log retention (12-month policy, see audit_logging.md)
  has no purge job yet.
- Preemptive timeouts remain cooperative-checkpoint only
  (Phase 18 limitation, unchanged).
