# Phase 28 — Deployment Guide

## Deployment model

Local/self-hosted, process-based, free/open-source only. No Docker (user
decision 2026-11-04), no paid cloud tier, no broker, no hosted scheduler.

| Piece | How it runs | Bind | Port |
|---|---|---|---|
| PostgreSQL 16 | System service | 127.0.0.1 | 5432 |
| Backend (FastAPI/uvicorn) | `backend/.venv` | 127.0.0.1 | 8000 |
| Frontend (Next.js) | `next start` (production build) | 127.0.0.1 | 3000 |
| Jobs | Operator-invoked CLI (`scripts/run_jobs.py run-due`) | — | — |

## Prerequisites (all free)

- Linux host (production target is this VM's OS family; see
  Windows/Linux differences below). Python 3.12, Node.js 20+,
  PostgreSQL 16, git, curl, gpg (only if backup encryption is enabled).
- A checkout of the `phase-28-deployment` branch (or later).
- `database/.env` (gitignored, mode 0600) with the `psx_app` role
  credentials — see `docs/phase-02/DATABASE_SETUP.md` for the contract
  (database `psx_intelligence`, role `psx_app`, grants on the live DB
  and on `psx_intelligence_restore_test`). Secrets live ONLY there,
  never in the repo, never in a systemd unit, never in a log.
- Frontend production build: `cd frontend && npm install && npm run build`
  (webpack; the Turbopack build fails on symlinked `node_modules` in a
  git worktree — a worktree artifact, not a code defect; use
  `next build --webpack` there, plain `npm run build` on a normal checkout).

## Clean setup (fresh environment)

```bash
git clone <advisor-remote> psx-intelligence-ai
cd psx-intelligence-ai
git checkout phase-28-deployment
python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt
python3 -m venv database/.venv && database/.venv/bin/pip install -r database/requirements.txt
cd frontend && npm install && npm run build && cd ..
cp database/.env.example database/.env   # then fill in real values; never commit
# create the databases + role per docs/phase-02/DATABASE_SETUP.md, then:
cd database && .venv/bin/alembic upgrade head && cd ..
ops/start.sh
ops/healthcheck.sh
```

A full fresh-environment run of exactly this procedure (scratch worktree
+ fresh database + migrate + boot + build) is recorded in
`fresh_environment_test.md` — the acceptance gate "system starts from
clean documented setup" rests on that measured run, not on this text.

## Ports, firewall, TLS, environment variables

- **Ports:** 5432 (postgres), 8000 (backend), 3000 (frontend). All bind
  loopback only, so no firewall rule is needed and no port is reachable
  from the network by default.
- **Firewall:** if the host firewall is ever opened for these ports, that
  is an operator change outside this guide — and exposing the backend
  without a TLS reverse proxy is NOT supported by this project.
- **TLS:** none in the local deployment (loopback traffic). If the
  system is ever exposed beyond loopback, a TLS reverse proxy is
  REQUIRED first; it is not configured here.
- **Environment variables (production):** see `ops/env.production.example`.
  Rules enforced by the backend: `ENVIRONMENT=production` requires
  `AUTH_ENFORCEMENT=on` (else it refuses to boot) and rejects a wildcard
  `CORS_ORIGINS`. `NEXT_PUBLIC_API_URL` is baked into the frontend build
  at build time — changing it requires a rebuild, not a restart.
- **CORS constraint:** backend CORS allows only port 3000 origins by
  default. Keep the frontend on port 3000, or set `CORS_ORIGINS` to the
  real frontend origin before starting.

## Docker: evaluated, NOT used

- `deployment/Dockerfile.backend`, `Dockerfile.frontend`,
  `Dockerfile.worker`, and `docker-compose.yml` exist from Phase 2.
  They are SUPERSEDED and NOT part of this deployment: the user banned
  Docker project-wide on 2026-11-04, and nothing in `ops/` invokes it
  (test-enforced).
- Licence note for the record: Docker Engine is Apache-2.0; Docker
  Desktop's licence requires a paid subscription for larger commercial
  use. Neither matters here because neither is used — but the
  distinction is why "Docker" is not one thing in licence discussions,
  and why the ban is recorded as a project decision rather than a
  licence problem.

## Licence and paid-dependency audit

- Backend pins (all free, licences in `backend/LICENCES.md`): FastAPI
  MIT, uvicorn BSD-3-Clause, pydantic MIT, pydantic-settings MIT,
  SQLAlchemy MIT, alembic MIT, psycopg LGPL-3.0-only (used unmodified
  as a library), httpx BSD-3-Clause, pytest MIT, ruff MIT, fpdf2
  (Phase 22, report PDFs) BSD-3-Clause.
- Frontend packages (all free as published): next, react, react-dom,
  clsx, lightweight-charts, tailwind-merge, plus dev tools (vitest,
  Playwright, eslint, prettier, typescript, tailwindcss, testing-library).
- No package, service, or subscription in this stack requires payment,
  a sign-up, or a credential. The gate is enforced by
  `test_deployment_phase28.py`: any new dependency fails the suite
  until its licence is reviewed and added to the allowlist deliberately.
- External operating expenses (local hardware, electricity, internet)
  are disclosed as expenses, never described as free (Phase 1 rule).
- Free cloud tiers are quota-limited and non-guaranteed: this deployment
  does not depend on any of them for 24/7 service, and none is used.

## Windows / Linux differences

| Topic | Linux (production target) | Windows (dev only) |
|---|---|---|
| Services | systemd units (`ops/systemd/`, via `ops/install.sh`) | No units shipped; run in terminals or Task Scheduler (operator's setup, not configured here) |
| PostgreSQL | `pg_ctlcluster 16 main start/stop` (system service) | PostgreSQL as a Windows service (installer default) |
| Scripts | bash (`ops/*.sh`, `database/*.sh`) | Git Bash or WSL; native cmd/PowerShell NOT supported by these scripts |
| Paths | `/` separators, case-sensitive | `\` separators; checkout path must not contain spaces for the unit templates |
| Line endings | LF | LF in the repo (git `core.autocrlf` must not convert the shell scripts) |
| Ports/TLS | Same loopback-only rule | Same loopback-only rule |

## Systemd installation (operator decision, not done by this phase)

```bash
ops/install.sh --user psx --install   # root; writes /etc/systemd/system/*.service
systemctl daemon-reload
systemctl enable --now psx-backend psx-frontend
```

`ops/install.sh` without `--install` only validates into a temp dir.
The backend unit reads secrets from `database/.env` via `EnvironmentFile`
(the secret is never in the unit file). The service user must have read
access to the checkout and the `psx_app` database role credentials in
`database/.env`.

## Uptime limitations (explicit)

Everything stops when the computer is off. Nothing runs while off (no
daemon, no hosted scheduler). No permanent public availability is
claimed: there is no verified hosting, services bind loopback only, and
any "always on" claim would be false. See `operations_handover.md` for
start/stop and catch-up.
