# Changelog

All notable changes to this repository are documented here. Dates are in
Asia/Karachi (PKT) unless stated otherwise.

## [Unreleased]

- (Reserved for Phase 2 team work; each team appends its own entries here.
  Do not back-fill entries for work that has not landed.)

## [0.1.0] — 2026-11-04 — Phase 2, Team A: environment audit, Git foundation, monorepo structure, config

### Added

- Git repository initialised inside `~/workspace/psx-intelligence-ai/` only,
  with branches `main`, `development`, `feature/frontend-foundation`,
  `feature/backend-foundation`, `feature/database-foundation`.
- Monorepo skeleton: `frontend/`, `backend/`, `database/`, `storage/`,
  `workers/`, `shared/`, `scripts/`, `tests/`, `deployment/`, `monitoring/`,
  `.github/` — each major directory documented with a README stating its
  purpose and status. No empty placeholder files for future functionality.
- `.gitignore` (excludes `.env`, `.venv`, `node_modules`, `__pycache__`,
  data files, large datasets, secrets), `README.md`, `CONTRIBUTING.md`,
  this `CHANGELOG.md`.
- `.env.example` with frontend / backend / database / Redis / storage /
  logging / dev / test / prod sections, placeholder values only.
- `docs/phase-02/ENVIRONMENT_AUDIT.md` — full audit with actual command
  outputs (2026-11-04): Ubuntu 24.04.5 LTS, x86_64, 4 CPUs, 7.7 GiB RAM,
  Python 3.12.3, Node v24.22.1, npm 10.9.4, Git 2.43.0; Docker, `psql`,
  `redis-cli` NOT installed; no GPU evidence.
- `docs/phase-02/COMPATIBILITY_REPORT.md` — hardware suitability for local
  AI inference (limits stated explicitly), what works without each missing
  tool, and free installation methods.
- `docs/phase-02/LICENSE_REGISTER.md` — licence recording for the Phase 2
  stack (gate G-02): registry-declared licences checked 2026-11-04 plus
  locally read licence files where present; no item required payment, so no
  replacement was needed. Installing teams must re-read each shipped LICENSE
  file at install and update the register.
- `docs/phase-02/LOCAL_DEVELOPMENT_GUIDE.md` — local setup guide including
  the environment-variable configuration contract.
- `scripts/check_env.sh` — runnable environment check (no installs).
- `shared/schemas/provenance.schema.json` — draft provenance contract
  (source, source_timestamp, collected_at_pkt, freshness) from the Phase 1
  architecture, for backend/frontend teams to adopt.
- `.github/workflows/ci.yml` — minimal CI running only the environment
  check and a secrets-sanity check; test jobs are added by backend/frontend
  teams when their suites exist.

### Explicitly NOT done by Team A (other teams' scope)

- No PostgreSQL, Redis, Docker, or Ollama installation.
- No backend requirements/lockfile, no frontend dependency installation.
- No data ingestion, no Ollama model download, no Phase 3 work.
- No commit of other teams' in-progress files (frontend scaffold,
  backend `app/` modules, Phase 1 docs remain untracked unless their owners
  commit them).

## [Phase 1] — 2026-11-04 — Specification checkpoint (accepted)

- See `docs/phase-01/PHASE_1_ACCEPTANCE_REPORT.md` (67 files, 0 empty).
  Phase 1 produced documentation only — no application code, no installs,
  no live collection.
