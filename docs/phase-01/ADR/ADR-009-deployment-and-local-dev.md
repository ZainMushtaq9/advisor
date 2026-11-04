# ADR-009 — Deployment and local dev: GitHub Free + Docker Engine; no-Docker path retained

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04

## Context

The stack must be deployable and developable at PKR 0 absolute, on the team's
own machine, without assuming any permanent free hosting. Docker, `psql`, and
`redis-cli` are NOT installed on this machine (VERIFIED), so local development
cannot assume them today.

## Decision

- **Version control / CI:** Git + GitHub Free + GitHub Actions, kept within the
  Free tier's limits (exact limits UNVERIFIED — confirm at setup). If limits
  are exceeded or terms change, the fallback is local git + local test runs —
  never a paid tier under this budget.
- **Packaging:** Docker Engine (Linux) + Dockerfile / Compose file, written in
  Phase 2, packaging the API, Celery worker, PostgreSQL, Redis, and (if used)
  Ollama consistently. Docker Desktop's terms are a different product and are
  UNVERIFIED here — do not assume them; Linux local dev uses Engine.
- **Local dev — two paths (see Decisions §7):** Path A (Docker Engine services
  for PostgreSQL/Redis) and Path B (no-Docker: venv + npm + native OS packages,
  SQLite dev database). Both are Phase 2 setup instructions; neither is
  performed or claimed working in Phase 1.
- **Logging/monitoring (Phase 1):** Python stdlib JSON-structured logging +
  a `/health` endpoint (API up, database reachable, last collection run,
  Celery worker heartbeat when workers exist) + the CI test gate. No paid APM,
  no hosted logging.

## Consequences

- Positive: reproducible packaging; CI gate on every change; PKR 0.
- Negative: Docker Engine install is a Phase 2 setup step; GitHub Free is a
  vendor tier, not a permanent guarantee (hence the local fallback).
- Constraint: no deployment step in Phase 1 may require a payment, an account
  with a paid tier, or a key. Self-hosting means a machine that is off serves
  nothing — a stated limit, not a hidden one.

## Alternatives considered

- Vercel-only deployment — rejected: the frontend could deploy there, but the
  Python backend and database need their own host; a single-vendor story would
  hide that split, and no free tier is assumed permanent.
- Kubernetes — rejected: orchestration for a scale Phase 1 does not have.
- Prometheus + Grafana now — deferred: two more services for metrics Phase 1
  does not yet define; adopt only once SLIs are defined (both are free
  self-hosted tools, so this is a complexity deferral, not a cost decision).
- Paid APM / hosted logging / managed hosts — **excluded**: paid, violate
  PKR 0.

## Verification / open checks

- [ ] At Phase 2 setup: confirm GitHub Free limits; install Docker Engine;
  read its LICENSE file (UNVERIFIED in Phase 1); verify Compose brings up
  PostgreSQL + Redis locally.
