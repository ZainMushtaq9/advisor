# PSX Intelligence AI — Phase 2 Compatibility Report (Team A)

**Date:** 2026-11-04. **Basis:** `ENVIRONMENT_AUDIT.md` (commands actually
run). No benchmark was measured in this workspace; performance statements
below are limits derived from the audited hardware, labelled as such, not
measured figures (gate G-08).

## 1. Pinned versions (actually installed/present — the only pins Team A makes)

| Item | Pinned version | How verified |
|---|---|---|
| Python | 3.12.3 | `python3 --version` |
| Node.js | v24.22.1 | `node --version` |
| npm | 10.9.4 | `npm --version` |
| Git | 2.43.0 | `git --version` |
| Ubuntu | 24.04.5 LTS (noble) | `/etc/os-release` |
| PostgreSQL server | 16.15 (installed by concurrent work, NOT Team A) | `psql --version`, dpkg, `pg_isready` |
| Redis server | 7.0.15 (installed by concurrent work, NOT Team A) | `redis-cli --version`, `redis-cli ping` → PONG, dpkg |
| next / react / react-dom | 16.4.5 / 19.3.0 / 19.3.0 (installed by frontend team) | `frontend/node_modules/*/package.json` |
| typescript / tailwindcss / eslint | 5.9.3 / 4.3.4 / 9.39.5 (installed by frontend team) | `frontend/node_modules/*/package.json` |

**Everything else is NOT pinned by Team A.** `LICENSE_REGISTER.md` records
latest-observed registry versions (2026-11-04) for reference only. A library
version becomes a pin only when a team actually installs it, in a lockfile
(`package-lock.json`, `requirements.txt` + hashes, or equivalent) — never by
copying a version from a snippet, a search result, or this report.

## 2. Hardware suitability for local AI inference — limits stated explicitly

Audited hardware: 4 vCPUs (host CPU AMD EPYC 9D25), 7.7 GiB total RAM with
only ~0.8 GiB available at audit time, 0 B swap, no GPU evidence, 147 GiB
free disk under `/home`.

- **Core product work (API, PostgreSQL, Redis, analytics, PDF extraction):
  SUITABLE.** These are the Phase 1 design workloads; disk is ample and the
  stack is CPU-based. Nothing in this skeleton needs a GPU.
- **Local LLM inference: SEVERELY LIMITED on this machine as audited.**
  (a) No GPU — any inference is CPU-only and slow. (b) ~0.8 GiB RAM
  available with no swap means even a small open-weight model cannot be
  assumed to load alongside the API, database, Redis, and a browser — the
  audit-time headroom is below the working set of a typical small model
  plus its runtime. (c) Load average was already ~3.36 on 4 vCPUs.
  Conclusion: **do NOT download or run an Ollama model on this machine
  during Phase 2 setup.** The Phase 1 design already requires this posture:
  every core feature works with Ollama absent or with no model downloaded,
  and LLM text is an optional research-draft layer. A model may be evaluated
  later only via the ADR-007 gate (PSX research tasks, tool-calling accuracy,
  local hardware fit, licence compatibility) on a machine with measured
  headroom — and that evaluation must measure memory first, not assume it.
- **PyTorch: NOT installed and NOT a default.** Conditional only, on a
  written justification for a task classical models demonstrably cannot do
  (Phase 1 §2.8). Its CPU weight on 4 vCPUs / ~0.8 GiB available headroom
  is a further reason not to install it "just in case".
- **Disk is not the constraint:** 147 GiB free under `/home` covers
  PostgreSQL data, Parquet exports, PDFs, and (later, elsewhere) model files.
  The constraint is RAM + no GPU, not disk.

## 3. What works WITHOUT each missing/uninstalled tool

| Without… | Still works | Blocked until it exists |
|---|---|---|
| Docker Engine | Everything in the no-Docker path: venv + npm, SQLite dev DB, local services | Containerised packaging; Compose-based service orchestration |
| Ollama / any model | All core features: data, deterministic indicators, computed reports, UI scaffold | LLM research-draft features only (optional layer) |
| Tesseract | Text-layer PDF extraction (PyMuPDF primary, pypdf fallback) | OCR of scanned/image-only PDF pages |
| MinIO (NOT ADOPTED) | Everything: local filesystem is the default store | Nothing — no feature depends on MinIO |
| PyTorch | All classical analytics (pandas/NumPy, scikit-learn, statsmodels) | Only a justified deep-learning task |
| GitHub remote / push | All local work; local git history is complete | Remote backup / CI — deferred until Phase 2 acceptance (user decision) |

PostgreSQL and Redis are no longer "missing" at the 11:37 re-check (see
audit §6), but their configuration belongs to their installing teams; until
those teams document connection details, developers should still be able to
run with the SQLite dev database and with workers disabled (see the local-dev
guide).

## 4. Compatibility matrix (Phase 1 §3, re-checked against this audit)

| Pair | Compatible? | Note |
|---|---|---|
| Next.js 16.4.5 + React 19.3.0 + TypeScript 5.9.3 | Yes (installed, frontend team) | Versions read from installed packages, not assumed |
| Next.js + Tailwind 4.3.4 + shadcn/ui | Yes, with setup check | shadcn/ui's current primitive (Radix vs Base UI, reported change July 2026) still to be confirmed by the frontend team at component install |
| Next.js + Lightweight Charts | Yes | Plain npm package; pin the installed major version at install (series API differs across majors). Licence: Apache-2.0; keep attribution enabled |
| Next.js → FastAPI (HTTP/JSON) | Yes | OpenAPI contract from FastAPI; frontend types mirror backend schemas |
| Python 3.12.3 + FastAPI + Pydantic v2 + Uvicorn | Yes (design pairing) | Not installed by Team A; backend team pins at install |
| FastAPI + SQLAlchemy + Alembic | Yes | Same models for PostgreSQL and SQLite; migrations must pass on PostgreSQL before release |
| SQLAlchemy + PostgreSQL 16.15 | Yes | Server present (concurrent install); driver variant pinned by backend team at install |
| SQLAlchemy + SQLite | Yes, dev-only | Known divergences: type strictness, single-writer concurrency, sequences, PostgreSQL-specific types/indexes |
| FastAPI + Celery + Redis 7.0.15 | Yes | Redis 7.0.15 is pre-7.4, i.e. the BSD-3-Clause era — if the team later upgrades to Redis 8, the tri-licence (RSALv2/SSPLv1/AGPLv3) option must be recorded then |
| pandas + NumPy + scikit-learn + statsmodels | Yes | System Python already carries numpy 1.26.4 / pandas 2.1.4+dfsg as OS packages — project venv pins are separate and still required |
| PostgreSQL + Parquet (PyArrow) | Yes, distinct roles | PostgreSQL is system of record; Parquet is regenerable derived export |
| Local filesystem + (optional) MinIO | Yes, optional | MinIO NOT ADOPTED; default is plain filesystem |
| PyMuPDF → pypdf fallback → Tesseract | Yes, staged | Sequential stages, never two extractors on the same page in one run; method logged. Licence flag: PyMuPDF's registry licence is dual AGPLv3/commercial — see LICENSE_REGISTER.md |
| Ollama (local API) + own tool loop | Yes, when Ollama exists | Ollama absent today; core features do not depend on it |
| Ollama + "no model" default | Yes, by design | LLM features disabled, not broken, with no model downloaded |
| psx-dps / psxdata → collector → storage | Yes, by design | psx-dps is NOT on PyPI under that name (404 on 2026-11-04) — install only from its actual distribution source; psxdata observed at 1.2.0 vs Phase 1 alpha 0.1.0a1 — pin at install, isolate behind one adapter |
| GitHub Actions + pytest + Playwright | Yes, within free limits | CI file in this skeleton runs env/hygiene checks only; test jobs come with the suites |
| Docker Engine + all above | Yes, Phase 2 definition | Engine NOT installed; Compose file not yet written (later Phase 2 deliverable) |

## 5. Known traps (do not work around silently)

- SQLite ≠ PostgreSQL (see §4). A migration passing only on SQLite is not done.
- psxdata alpha-era APIs may change; adapter isolation limits blast radius.
- psx-dps multi-node 404 quirk: a 404 from one node is a node problem, not "no data".
- Lightweight Charts major-version API differences: write chart code against the installed major only.
- Redis licence changes at 7.4/8.x: the installed 7.0.15 is BSD-era; an upgrade is a licence event, not a routine bump.
- PyMuPDF AGPLv3 option: free to use under AGPL, but network-service obligations apply if served — record the licence path decision at install (see LICENSE_REGISTER.md).
- Sector/universe counts unresolved (G-03): 38 vs 37 sectors, ~496 vs ~1029 vs 1000+ symbols — never harmonise silently.
