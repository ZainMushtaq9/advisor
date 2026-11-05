# PSX Intelligence AI

## Release status — Phase 30 handover (2026-11-05) — READ THIS FIRST

**System verdict: PARTIALLY COMPLETE.** Phases 1–3 are COMPLETE; Phases
4–29 are PARTIALLY COMPLETE; Phase 30 is the release + handover snapshot
(tag `v0.2.0-handover` on branch `phase-30-release`). This is NOT a production release and NOT a merge to `main` (remote `main` is README-only, unrelated history; no merge without a separate approval).

**What actually exists:** 470-company registry (Main Board / Normal
Counter only, all UNVERIFIED); 444 price rows on ONE trading date
(2026-11-03, all UNVERIFIED, previous_close NULL); statements for 4
companies (HUBC, NML, OGDC, HBL at statement level only — HBL ratios,
valuations, and decisions do not exist yet; the Phases 8+ HBL re-runs
are sequenced after Phase 30); 22 DRAFT reports (0 approved, 0
published); 89 in-app alerts; 3 SIMULATED portfolios; 0 forecasts
(all 120 assessments abstained); all user-facing decisions WITHHELD;
all backtests NOT_RUNNABLE; no live auth accounts; no external
notifications; no broker/order path; no real trades, ever.

**Corrections to the Phase 2-era text below:** the sections describing
Phase 2 as "this foundation" are historical (Phases 3–30 followed; see
`docs/phase-30/handover_report.md` for the current state). Docker is
NOT used anywhere in this project (user decision 2026-11-04); the
Phase 2 Docker definitions below are history only, and the ops scripts
contain no docker invocations (enforced by test). Full current state,
limitations, and roadmap: `docs/phase-30/handover_report.md`. User
guide: `docs/phase-30/user_guide.md`. Developer guide:
`docs/phase-30/developer_guide.md`.

**Budget: PKR 0 absolute.** No paid hosting, database, storage, monitoring, or
AI subscription in any configuration. Local hardware, electricity, and internet
are external operating expenses — disclosed, never called free. No permanent
free hosting is assumed. If a future step would cost anything, it stops and
needs a separate, explicit approval.

**No real trades initially — invariant.** This system must NOT execute real
trades. There is no broker connection, no order-placement path, and no
execution branch. Any future execution proposal is a new design decision
requiring separate approval.

## What this is

An intelligence platform for Pakistan Stock Exchange (PSX) data: market data,
financial reports, announcements, sector and macro analysis, forecasting
research, and audited decision support — built on deterministic calculations.
**An LLM must NEVER invent a numerical financial result.** Every number shown
comes from a deterministic function run over stored, provenance-tagged data.

Phase 1 (specification) is accepted as a checkpoint — see
`docs/phase-01/PHASE_1_ACCEPTANCE_REPORT.md`. Phase 2 (this foundation)
is implemented and independently audited — see
`docs/phase-02/PHASE_2_ACCEPTANCE_REPORT.md`. It provides a working
frontend shell, backend API, PostgreSQL + Alembic infrastructure,
local storage with integrity checks, Redis + Celery workers, and a
verified no-Docker local execution path. No data ingestion, no model
download, no Phase 3 schema, and no live PSX collection happens in
Phase 2. Docker is definition-only on this VM (see DOCKER_SETUP.md);
Playwright E2E is a documented follow-up (see PHASE_2_TEST_REPORT.md).

## Fixed stack (Phase 1 decisions, unchanged)

| Layer | Stack |
|---|---|
| Frontend | Next.js (App Router) + React + TypeScript + Tailwind CSS + shadcn/ui |
| Charting | TradingView Lightweight Charts (renderer only; attribution required) |
| Backend | Python 3.12 + FastAPI + Pydantic v2 + Uvicorn |
| Database | PostgreSQL (production, self-hosted) + SQLAlchemy + Alembic; SQLite dev-only |
| Bulk storage | Local filesystem + Apache Parquet (via PyArrow) |
| Object storage | Local filesystem default. Self-hosted MinIO is OPTIONAL and NOT ADOPTED — do not adopt a paid tier |
| Background | Celery + Redis (both self-hosted) |
| Analytics | pandas + NumPy, scikit-learn, statsmodels; PyTorch only where justified in writing |
| PDF | PyMuPDF (primary) + pypdf (fallback only) + Tesseract OCR (scanned pages only) |
| Local AI | Ollama, LOCAL inference only. No external AI API, no Ollama Cloud, no `:cloud` models, no API key |
| Testing | pytest (backend) + Playwright (frontend E2E, local dev only) |
| Version control / CI | Git + GitHub Free + GitHub Actions (within free limits); local git + local tests are the fallback |
| Containers | NOT USED — Docker definitions exist from Phase 2 only as history; user decision 2026-11-04 bans Docker anywhere; ops scripts contain no docker invocations (enforced by test) |

Full decisions: `docs/phase-01/TECH_STACK_DECISIONS.md` and the ADRs in
`docs/phase-01/ADR/`. Licence status for every planned dependency:
`docs/phase-02/LICENSE_REGISTER.md`.

## Repository layout (Phase 2 foundation)

```text
frontend/    Next.js 16.4.5 app — 7 foundation-shell routes, no fabricated data
backend/     FastAPI app — 4 /api/v1 endpoints, config redaction, Alembic baseline
database/    PostgreSQL 16.15 infrastructure — probe migration only, backup/restore
storage/     Local storage + SHA-256 integrity helper, verified backups (gitignored)
workers/     Celery 5.6.3 + Redis 7.0.15 — live proof OK, no scheduler yet
shared/      Cross-service schemas (provenance contract)
scripts/     check_env.sh, dev.sh, healthcheck.sh, stop_dev.sh, run_celery_proof.sh
tests/       Cross-cutting placeholder; team tests live with their components
deployment/  Compose + Dockerfiles — DEFINITION ONLY (Docker not verified running)
monitoring/  Health/monitoring placeholders
docs/phase-01/  Accepted Phase 1 specification (do not rewrite)
docs/phase-02/  Phase 2 setup, test, audit, and acceptance docs
docs/development/  Execution state, log, defect register, push log,
                   live test report, technical debt, account register
.github/     CI workflows (env + secrets-sanity; workers eager/live-broker, not run in CI yet)
```

## Quick start for a new developer

```bash
# 1. Check your machine against the audit (no installs performed by this script)
bash scripts/check_env.sh

# 2. Read the environment audit and the local-dev guide
#    docs/phase-02/ENVIRONMENT_AUDIT.md
#    docs/phase-02/LOCAL_DEVELOPMENT_GUIDE.md

# 3. Configure (placeholders only — never commit your .env)
cp .env.example .env
#    Edit .env with your own local values. See the config contract in
#    docs/phase-02/LOCAL_DEVELOPMENT_GUIDE.md.
#    NOTE: DATABASE_URL is optional in the backend config. Without it the
#    backend starts and truthfully reports database unavailable. To connect
#    the local PostgreSQL, set DATABASE_URL from gitignored database/.env.

# 4. Backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# 5. Frontend
cd frontend && npm install && npm run dev   # http://localhost:3000

# 6. Full local stack (no Docker — Docker is not used by this project)
bash scripts/dev.sh
bash scripts/healthcheck.sh
bash scripts/stop_dev.sh
```

**Services installed in Phase 2 on this VM (free, apt/npm):** PostgreSQL
16.15, Redis 7.0.15, Docker Engine 29.1.3 (daemon runs; registry pulls
fail with a TLS handshake timeout, so no container has run — see
`docs/phase-02/DOCKER_SETUP.md`). Ollama is NOT installed and no model
was downloaded (local AI inference is severely limited on this VM:
no GPU, ~0.8–1.1 GiB RAM available with the stack up). After a VM
reboot, run `pg_ctlcluster 16 main start` before DB work.

## Gates carried forward from Phase 1 — do not silently resolve these

- **G-01 — UNVERIFIED for machine use:** SECP, SBP, PBS, Finance Division,
  World Bank, IMF, FRED interfaces. Do not ingest from them.
- **G-02 — Licences:** see `docs/phase-02/LICENSE_REGISTER.md`. Registry
  licences recorded 2026-11-04; the installing team must re-read each shipped
  LICENSE file at install and update the register. If any item required
  payment, it stops and is replaced.
- **G-03 — Unresolved counts, never harmonise silently:** ~496 trading symbols
  vs ~1029 listed instruments vs 1000+ tickers; 38 sectors (psx-dps) vs 37
  sectors (psxdata). Keep both values with provenance.
- **G-04 — Versions:** only the runtimes below are pinned as actually
  verified on this machine. Library versions are pinned only when actually
  installed, in a lockfile — never copied from a snippet.
- **G-06 — FRED:** gated OUT of AI training, caching, and commercial output
  until its Terms are re-read.
- **G-07 — MinIO:** OPTIONAL / NOT ADOPTED. Do not adopt a paid tier.
- **G-08 — No measured figures:** any figure asserted in docs must carry its
  method and date.

## Verified environment (2026-11-04, re-verified by running commands)

Python 3.12.3, Node v24.22.1, npm 10.9.4, Git 2.43.0, Ubuntu 24.04.5 LTS,
x86_64, 4 CPUs, 7.7 GiB RAM, PostgreSQL 16.15, Redis 7.0.15,
Docker Engine 29.1.3 (daemon only, pulls blocked). Full evidence:
`docs/phase-02/ENVIRONMENT_AUDIT.md` and
`docs/phase-02/PHASE_2_TEST_REPORT.md`.

## Contributing

See `CONTRIBUTING.md`. In short: no secrets in git history, no fabricated PSX
data, no silent harmonisation of conflicting values, no paid dependency, no
per-email-style bypass of any approval gate that applies to your work, and no
commit of another team's in-progress work.

## Changelog

See `CHANGELOG.md`.
