# Phase 27 — Implementation Specification

## Objective (brief lines 1917–1973)

Make the complete system diagnosable, measurable, and maintainable
under realistic local/free-resource constraints: structured logs,
correlation IDs, job/agent run IDs, API metrics, error tracking,
health/readiness checks, source freshness, collection success,
missing-data rates, data-quality failures, model drift, runtime
errors, per-category data-quality SLOs, exception queues,
evidence-backed incident reports, performance profiling with
measured-bottleneck-only optimization, resource limits, and
reliability testing (crashes, outages, format changes, corrupted
downloads, disconnects, disk pressure) with severity, escalation,
rollback, and recovery procedures.

## What was built

| Component | Location | Notes |
|---|---|---|
| Structured logging + redaction + correlation IDs | `backend/app/services/observability/logging_config.py` | JSON lines, `[REDACTED]` values, `X-Correlation-ID` middleware wired in `app/main.py` |
| SLO definitions + measurement | `backend/app/services/observability/slos.py` | 14 SLOs, per-category targets, NULL never zero |
| Source health | `backend/app/services/observability/source_health.py` | 9 sources, per-source freshness thresholds |
| Performance probes | `backend/app/services/observability/performance.py` | DB timings, ticker lookup, PG sizes; SQLite storage probe returns NULL with reason |
| Runner | `backend/app/services/observability/runner.py` | Dry-run default, `--commit`, idempotent on run_id |
| Models | `backend/app/models/observability.py` | 7 tables, portable Integer PKs (no IdMixin) |
| Migration | `database/migrations/versions/20261104_0023_phase_27_observability.py` | 0022 → 0023 |
| API | `backend/app/api/v1/endpoints/observability.py` | 8 GET-only routes: summary, readiness, slos, source-health, exceptions, incidents, performance, runs |
| CLI | `scripts/run_observability.py` | `--run-id`, `--commit` |
| Dashboard | `frontend/app/admin/observability/page.tsx` + nav entry | 26 routes in production build |
| Tests | `backend/tests/test_observability_phase27.py` | 11 tests; full backend suite 419 passed |
| Playwright | `frontend/e2e/phase27/observability.spec.ts` + `playwright.phase27.config.ts` | 6 passed (3 specs × desktop + mobile) |

## Design rules carried over

- Reads stored rows, writes observability records only. No business
  row is written, no status is promoted, no data is collected, no
  order/execution/publication/send capability is added (the
  no-execution scan covers the new service directory).
- Company identity resolved by ticker everywhere (surrogate ids
  shift across fresh imports — Phase 23 repair).
- RegistryEvidence is keyed by entity_type/entity_id, not by a
  company_id column: company evidence is entity_type 'company'
  (a bug caught during implementation, fixed before any run).
- News freshness uses the latest OBSERVED event date only:
  scheduled future events (SBP meeting 2026-12-14) are noted,
  never dated as observations (a negative-freshness bug caught
  during the live dry-run, fixed before commit).
- No log text is stored in the database. Structured logs go to
  stdout/stderr; the database holds measurements, not messages.

## Seed run (live, committed)

Run `phase27-observability-2026-11-05`, run date 2026-11-05:
14 SLO measurements (10 met, 4 unmet, 0 not_evaluable),
9 source-health rows (1 stale: market_prices; 0 unknown),
6 exceptions (all open), 3 incidents (all resolved),
13 performance probes. Second `--commit`: skipped_existing,
0 new rows (idempotency proven).

## Resource limits (documented, not just claimed)

- Jobs: single-pass, operator-invoked, max 7 occurrences/pass,
  in-memory rate limits (300/min API, 30/min auth) — Phase 25/24.
- No daemon, no broker, no paid scheduler (Phase 25).
- No local model runtime exists to limit: LLM-backed execution
  is unavailable (Phase 18 fallback only) and vector retrieval
  is not implemented (Phase 19); both are recorded as absent,
  not as resource-limited.
- Backfills are bounded by the same CLI dry-run/commit discipline
  as every phase runner: a failure rolls back the whole run
  instead of storing a partial result.

## Deliberately NOT built

- No log aggregation service, no paid APM, no external metrics
  endpoint (free-only constraint; stdout JSON is the sink).
- No auto-remediation: drift and SLO breaches are findings to
  explain, never auto-fixed (Phase 26 drift policy).
- No web approval, web incident resolution, or web exception
  lifecycle actions: the dashboard is read-only; lifecycle
  changes are recorded, not clicked (same rule as Phase 22
  report approval and Phase 21 alert lifecycle).
- No index added: see `optimization_report.md` — at current
  scale every probe is sub-millisecond except the ticker lookup
  at 1.557 ms, and the one plausible index
  (`report_figures.report_id`) was evaluated and rejected as
  decoration on a 541-row table.
