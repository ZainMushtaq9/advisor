# Phase 27 — Run Report

## Verdict: PARTIALLY COMPLETE

The acceptance gate's testable items hold: major failures are
diagnosable from logs and metrics (correlation ids, redacted
structured logs, readiness endpoint, exception queue, incident
reports); data-quality SLOs are measurable (14 definitions, all
measured, none hidden); recovery tests pass (corrupted rows
rejected, DB disconnect reported, idempotent re-runs, rollback
and recovery procedures documented and previously proven);
no sensitive values are logged (redaction unit-tested and
formatter-tested). COMPLETE is not claimed: the underlying data
stays limited exactly as Phases 4–26 recorded it (UNVERIFIED
inputs, 3-company coverage, abstained forecasts, WITHHELD
decisions, NOT_RUNNABLE backtests, fallback-only agents, vector
retrieval not implemented, DRAFT-only reports, HBL pending),
and 4 of 14 SLOs are unmet. Forcing COMPLETE would misrepresent
those limits.

## What changed

- Branch: `phase-27-observability`, new branch from
  `phase-26-evaluation` `b6f007c` (base unmoved; main untouched
  at `eb6025b`; no merge, no force-push, no history rewrite,
  no cross-push, no register files edited — parent consolidates).
- Migration: `20261104_0022` → `20261104_0023` (7 tables),
  applied to the live DB; `alembic current` = `20261104_0023 (head)`.
- Worktree removed afterward; the main worktree is undisturbed
  (still on `phase-21-alerts`).

## Seed run (live, committed)

Run `phase27-observability-2026-11-05`, run date 2026-11-05:

- SLOs: 14 total — 10 met, 4 unmet, 0 not_evaluable.
  Unmet: price_coverage_latest_day (0.944681 < 0.95),
  price_session_gap_weekdays (2 > 0), previous_close_completeness
  (0 < 1.0), news_company_coverage (0.006383 < 0.10).
- Source health: 9 rows — 1 stale (market_prices), 0 unknown.
- Exceptions: 6, all open (4 SLO breaches + HBL pending +
  paused collection jobs).
- Incidents: 3, all resolved (VM replacements #5 and #6, Phase 26
  push disconnect).
- Performance: 13 probes (5 COUNT(*) timings, 1 ticker lookup,
  7 storage sizes).
- Idempotency: second `--commit` wrote nothing
  (`skipped_existing`).

## Independent audit (hand-checked vs live DB)

- Price coverage 444/470 = 0.944681 ✓ matches stored SLO value.
- Previous close NULL on 444/444 rows → 0 ✓.
- OHLC-invalid stored rows 0 → validity 1.0 ✓.
- Registry companies with evidence 470 ✓.
- News companies 3 ✓; latest observed event 2026-11-02 ✓.
- HUBC close re-read 197.2400 after the run ✓ (no business row
  changed: companies 470, prices 444, statements 88, reports 22,
  alerts 89, job runs 71, auth users 0).

## Tests

- New suite: 11 tests, all passing (redaction, formatter,
  SLO measurement on seeded rows, dry-run/commit/idempotency,
  exception queue contents, corrupted-row rejection, DB
  disconnect probe, no-execution scan, correlation-id headers,
  readiness honesty, full API shape incl. bad-status 400 and
  bad-pagination 400).
- Full backend suite: 419 passed, 0 failed (408 + 11 new).
  Ruff check + format clean on all new/changed files.
- Frontend vitest: 11 passed. ESLint clean on new/changed files.
- Production build (`next build --webpack`): 26 routes
  (25 + `/admin/observability`). The Phase 23
  Turbopack-on-symlinked-node_modules note still applies
  (worktree artifact, not a code defect).
- Playwright phase27 suite: 6 passed, 0 failed (3 specs ×
  desktop + mobile).
- Live API smoke (uvicorn, live DB): `/health` 200 with
  `X-Correlation-ID`; readiness `ready: true`, migration match
  true; summary 14/10/4; slos 14 definitions, 4 unmet;
  incidents 3 resolved; unknown route 404; bad pagination 400.

## Corrections made during this run (not hidden)

1. RegistryEvidence has no `company_id` column — evidence is
   keyed by entity_type/entity_id. The SLO and source-health
   modules were fixed to count entity_type 'company' before
   any run.
2. News freshness first used the maximum event date, which is
   a scheduled future event (SBP meeting 2026-12-14), reporting
   -39 days as "fresh". Fixed before commit: freshness uses
   the latest event on or before the run date (2026-11-02);
   scheduled future events are noted, not dated.
3. The readiness endpoint crashed (500) when no database
   existed, because the session factory was None. Fixed: it
   now reports `reachable: false, ready: false` instead.
4. SQLAlchemy `distinct()` misuse warning fixed (proper
   `.distinct()` on the query).

## HBL note — status changed during this run

At brief time, the HBL CY2025 PDF download was still running
with no result. During Phase 27, the parent confirmed the PDF
was OBTAINED (2026-11-05, live-browser visit, 6,437,243 bytes,
411 pages, gitignored at
`storage/financial_reports/HBL_Annual_Report_2025.pdf`) and a
separate extraction coordinator was spawned. Verified live
during this run: the PDF file exists at that size, but the
database still holds 3 documents / 88 statements — extraction
has not loaded yet. Phase 27 therefore keeps the HBL exception
open with updated evidence ("PDF obtained, extraction in
progress") and touches no HBL data. When extraction lands, the
next observability run will show drift vs the Phase 24 baseline
(new documents/statements) — that is the drift SLO working as
designed, and the baseline update must be recorded with its
evidence per the Phase 25 rule, not hidden.

## Remaining blockers with exact unblockers

- Written PSX permission evidence (user-owned) → collection
  jobs unpause, full-470 verification, new PSX collection, and
  with them the price-coverage, session-gap, and
  previous-close SLOs.
- More trading days (Terms-gated) → technical values, forecasts,
  backtests, series risk, evaluated predictions.
- HBL extraction (parent-owned, separate coordinator) → 4th
  company everywhere, including a 4th decision and dossier;
  then Phase 8+ HBL re-runs.
- Verified local embedding model → vector retrieval (then the
  RAG card and vector metric become evaluable).
- Internal review decision → first APPROVED report (CLI
  transition only, no web approval by design).
- Parent/user decision → first live auth account (auth tables
  intentionally 0/0/0).
- Real deployment decision → enforced-mode production proof,
  backup encryption, dependency audit, frontend token support,
  multi-instance rate limiting.
- Follow-ups (not Phase 27 changes, still open from Phase 25):
  permanent name-based sector resolution; permanent
  ticker-based news publication-date mapping (the same
  surrogate-id trap will recur on the next recovery otherwise).
- Phase 24 candidate (a) token-gated report approval: still open
  (belongs to no phase brief so far; candidate for a later phase).
- Parent consolidation still owed: append Phases 8–27 outcomes
  to the three registers, and update the consolidated MEMORY.md
  PSX bullet (Phase 27 coordinators cannot edit memory files).

**STOP — Phase 28 not started; awaiting parent verification and
the next brief.**
