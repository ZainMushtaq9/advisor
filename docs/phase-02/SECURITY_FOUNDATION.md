# PSX Intelligence AI — Security Foundation (Phase 2)

## Implemented in Phase 2 (verified, not aspirational)

- **Secrets handling:** no real secret, password, token, or credential
  in code, docs, or git history (coordinator secret-scan scope: team
  files + .env.example files contain placeholders only, e.g.
  `changeme-dev-only`). Real DB password lives only in
  `database/.env` (mode 0600, gitignored). `.gitignore` excludes
  `.env`, `.venv`, `node_modules`, `__pycache__`, data/datasets.
  Backend `/api/v1/config/status` returns setting names + SET/MISSING
  + source only — never values (tested with a fake secret).
- **Input validation:** Pydantic settings + FastAPI request validation;
  422 responses contain no tracebacks. Storage helper rejects absolute
  paths, `..` traversal, and non-slug paths.
- **Error sanitisation:** JSON error handlers for 404/405/422/500 with
  no stack traces or secrets in responses (tested).
- **CORS:** restricted origins from env; wildcard CORS and
  `DEBUG=true` rejected in production (tested). Dev default is
  loopback only.
- **Database credentials:** app role `psx_app` is LOGIN, NOSUPERUSER,
  NOCREATEDB, NOCREATEROLE, with CONNECT + schema USAGE/CREATE +
  default table/sequence privileges only (Team D, verified by role
  attributes). Superuser commands must use `-U postgres` with env
  cleared of PGUSER/PGPASSWORD/PGDATABASE (Team D caution D6).
- **File access:** `storage/raw/` + `storage/backups/` 0750, other
  storage classes 0755. Raw data is never published; backup/restore
  scripts refuse live-target restore without `ALLOW_LIVE_RESTORE=1`.
- **Dependency auditing:** licence register in
  `docs/phase-02/LICENSE_REGISTER.md` (38 fixed-stack items, no payment
  required) + per-component LICENCES/requirements files. Flags carried
  forward: PyMuPDF AGPL/commercial duality (PKR 0 only under AGPL),
  Redis licence version-dependence (installed 7.0.15 is BSD-3-Clause
  era), psx-dps not on PyPI (never pip-install a similarly-named
  guess), Node.js licence file OPEN.
- **Logging:** stdlib JSON logging only; no secret values logged.
  Backend logs include request ID + duration, not request bodies
  with credentials.
- **CI secrets-sanity:** `.github/workflows/ci.yml` includes a
  secrets-sanity check; workers.yml adds eager tests + a live-broker
  job (not run in CI yet — no push was made before audit).

## Explicitly NOT implemented in Phase 2 (by design)

- No user authentication, sessions, or role-based access control yet.
  The future authentication architecture is specified in Phase 1
  (SECURITY_REQUIREMENTS.md) and is a later-phase deliverable. Do not
  claim the Phase 2 foundation is "authenticated".
- No broker connection, no trade execution, no external API keys.
  The system must not execute real trades initially (Phase 1 invariant).
- No hosted monitoring, APM, or external security scanning service
  (PKR 0). Dependency checks are local (licence register + pinned
  versions), not a hosted scanner.

## Known limitations (must be fixed or carried forward, not hidden)

1. Docker is definition-only on this VM (registry pulls fail with a
   daemon TLS handshake timeout — DOCKER_SETUP.md blocker D-05).
   Container isolation claims must not be made until a real
   `docker compose ps` all-healthy run is recorded.
2. PostgreSQL cluster start is blocked by `policy-rc.d` on this VM;
   after a reboot, run `pg_ctlcluster 16 main start` before DB work.
3. The full-stack integration test (all services up together with a
   real DATABASE_URL) was verified by the coordinator via a port-8001
   backend run, not via `scripts/dev.sh` (which deliberately invents
   no DATABASE_URL/credential). The dev.sh path therefore still
   reports backend↔DB unavailable by design — that is truthful, not
   a failure, but the README must not describe dev.sh as proving
   DB connectivity.
4. Playwright E2E was not installed; browser-level security/UX checks
   are unverified.
5. Backup rotation is manual until Phase 3 (never below the
   2-verified-backup floor).
