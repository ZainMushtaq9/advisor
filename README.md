# PSX Intelligence AI

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
`docs/phase-01/PHASE_1_ACCEPTANCE_REPORT.md`. Phase 2 (this skeleton) sets up
the repository and development environment only. No data ingestion, no model
download, and no live collection happens in this skeleton.

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
| Containers | Docker Engine (Linux) + Dockerfile / Compose (definition, Phase 2); local dev also has a no-Docker path |

Full decisions: `docs/phase-01/TECH_STACK_DECISIONS.md` and the ADRs in
`docs/phase-01/ADR/`. Licence status for every planned dependency:
`docs/phase-02/LICENSE_REGISTER.md`.

## Repository layout (Phase 2 skeleton)

```text
frontend/    Next.js app (scaffold present; see frontend/README.md)
backend/     FastAPI app (app/ owned by the backend team)
database/    Migrations, seeds, schemas (SQLAlchemy/Alembic in Phase 2)
storage/     Local data tiers: raw, processed, financial_reports, parquet,
             research_reports, backups — READMEs only; NO data committed
workers/     Celery tasks, schedulers, monitoring
shared/      Cross-service schemas and contracts
scripts/     Developer utilities (e.g. scripts/check_env.sh)
tests/       Cross-cutting tests (backend tests live in backend/tests)
deployment/  Deployment definitions (Phase 2; no Compose file yet)
monitoring/  Health/monitoring definitions (Phase 2)
docs/phase-01/  Accepted Phase 1 specification (do not rewrite)
docs/phase-02/  Phase 2 setup docs (this team's deliverables)
.github/     CI workflows
```

Every directory carries a README explaining its purpose and status. No file in
this skeleton is a placeholder for future functionality without saying so.

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

# 4. Backend (once the backend team lands requirements — not in this skeleton)
python3 -m venv .venv && source .venv/bin/activate
#    pip install -r backend/requirements.txt   # file owned by backend team

# 5. Frontend (scaffold present; install is the frontend team's step)
cd frontend && npm install && npm run dev
```

**Services you may still need to install (NOT done by Team A):** Docker Engine,
PostgreSQL, Redis, Ollama — see `docs/phase-02/ENVIRONMENT_AUDIT.md` for the
free installation method for each, and `docs/phase-02/COMPATIBILITY_REPORT.md`
for what works without them. Local dev works without Docker, PostgreSQL, and
Redis (SQLite dev database; workers disabled until Redis exists).

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
x86_64, 4 CPUs, 7.7 GiB RAM. Docker, `psql`, and `redis-cli` NOT installed.
Full evidence: `docs/phase-02/ENVIRONMENT_AUDIT.md`.

## Contributing

See `CONTRIBUTING.md`. In short: no secrets in git history, no fabricated PSX
data, no silent harmonisation of conflicting values, no paid dependency, no
per-email-style bypass of any approval gate that applies to your work, and no
commit of another team's in-progress work.

## Changelog

See `CHANGELOG.md`.
