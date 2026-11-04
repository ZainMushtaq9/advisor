# ADR-004 — Background processing: Celery + Redis (both self-hosted)

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04
- **Supersedes:** The first draft's APScheduler-as-primary position, withdrawn
  under the revised brief (fixed stack names Redis; the background choice must
  be Redis-consistent).

## Context

Collection runs, PDF extraction, and report generation are long, retryable jobs
that must not block HTTP requests and must survive a process restart. The
revised brief fixes Redis and requires a Redis-consistent choice, at PKR 0
absolute, with no paid/managed service.

## Decision

- **Task queue:** Celery (BSD-3-Clause, noted in public pages read).
- **Broker + result backend:** Redis, self-hosted, on the team's own machine.
- **Job code:** plain Python modules shared with the API (same code, called
  from a worker instead of a route handler); job payloads validated with
  Pydantic v2; job state visible in PostgreSQL / via the API.
- **Local dev:** Redis via Docker Engine (Phase 2 setup installs it) or via a
  native OS package; `redis-cli` is NOT installed on this machine today
  (VERIFIED), so no worker runs in Phase 1 — this ADR is a decision, not a
  running system.

## Consequences

- Positive: durable tasks, retries, multiple workers later; standard,
  well-understood pairing; PKR 0 licence fee for self-hosted use.
- Negative: a broker + workers to operate (more moving parts than an
  in-process scheduler); Redis licence complexity (below) must be managed.
- **Redis licence — read carefully (VERIFIED):** Redis ≤ 7.2 was BSD-3-Clause;
  from 7.4 RSALv2 or SSPLv1 (neither OSI-approved); Redis 8 added AGPLv3 as a
  third option (tri-licensed RSALv2/SSPLv1/AGPLv3). Self-hosted use costs
  PKR 0 under any option, but Phase 2 setup MUST record which option it
  operates under. This project does not modify Redis and does not offer it as
  a managed service, so the restrictive clauses do not bite — but that
  reasoning must be re-checked if either fact changes.

## Alternatives considered

- APScheduler (in-process) — rejected as primary under the revised brief:
  no durable retries across restarts, no multi-worker story, and keeping it
  alongside Celery would duplicate the scheduler role.
- RQ / Dramatiq / arq — rejected: each still needs a broker, and none is the
  fixed-stack choice.
- cron + shell scripts — rejected: no retries, no job state, no API visibility.
- Valkey (BSD-3-Clause Linux Foundation fork of Redis 7.2.4, VERIFIED in
  outline) as broker — **noted as a licence-risk alternative only, NOT the
  primary**, because the fixed stack names Redis. Swapping to Valkey is a new
  decision recorded at that time, never a silent change.
- Managed Redis — **excluded**: paid, violates PKR 0.

## Verification / open checks

- [ ] At Phase 2 setup: install Redis + Celery; record the Redis licence option
  operated under; read Celery's LICENSE file; confirm a worker heartbeat
  appears on the `/health` endpoint.
