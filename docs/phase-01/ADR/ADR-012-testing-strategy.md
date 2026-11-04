# ADR-012 — Testing strategy: pytest + Playwright, defined not claimed passed

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04

## Context

The fixed stack names pytest and Playwright. The scaffold this project
references already demonstrates the right pattern: offline tests with a fake
client, no network, no PSX call. Phase 1 defines the strategy; it does not
claim a passing suite for an application that does not exist yet.

## Decision

- **Backend:** pytest. Unit tests for deterministic calculation functions
  (ADR-010), adapter tests with fake clients (never live PSX calls), API tests
  against the FastAPI app with a test database, Celery job tests with jobs run
  eagerly or against a test broker — never against production data.
- **Frontend E2E:** Playwright, against local dev only. Tests cover rendering
  of computed series, chart attribution presence (ADR-001), and stale-data
  flagging in the UI — never live market data.
- **Offline-first rule:** the default test run needs no network, no PSX call,
  no Ollama model, and no paid service. Any test needing a network is marked
  and excluded from the default run.
- **CI gate:** GitHub Actions (within Free-tier limits) runs pytest +
  Playwright on every change; a failing gate blocks merge. Local runs
  (`pytest`, `playwright test`) are the fallback if CI limits are hit.

## Consequences

- Positive: deterministic functions are exactly the code that is easiest to
  test (same inputs → same outputs); fake-client adapter tests protect
  against psx-dps/psxdata changes without live calls; PKR 0.
- Negative: Playwright browser tests are slower than unit tests and need
  browser binaries (licence UNVERIFIED — confirm at install, including
  downloaded browsers); E2E scope must stay small or CI slows down.
- Constraint: **no passing tests are claimed in Phase 1 for this application.**
  The scaffold's own offline tests passing is a property of the scaffold
  (`~/workspace/psx-data-collection/`), not of this project. Any later claim
  of "tests pass" must name the suite, the run, and the date.

## Alternatives considered

- Backend tests only, no E2E — rejected: chart rendering and stale-flag
  display are user-visible correctness properties that unit tests cannot see.
- E2E against live data — rejected: live data changes, is rate-limited, and
  would make tests flaky and non-reproducible.
- A paid test-cloud / hosted browser service — **excluded**: paid, violates
  PKR 0.

## Verification / open checks

- [ ] At Phase 2 setup: pin pytest/Playwright; read their LICENSE files
  (UNVERIFIED in Phase 1); record the first real test run (suite, date,
  result) before any "tests pass" claim is made.
