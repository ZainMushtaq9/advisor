# Phase 15 Implementation Specification

## Data model (migration 20261104_0012)

- `decision_rules`: one row per rule version. v1 stores
  dimensions, weights (equal), thresholds, gates, precedence and
  confidence rules as JSON, so the rule set itself is auditable.
- `decisions`: one row per (company, decision_date, rules_version).
  Columns: screening_outcome, research_conclusion, user_facing,
  confidence, total_score, scored_dimensions, completeness,
  evidence_snapshot (JSON), conflicts (JSON), gate_reasons
  (JSON), plus the standard provenance block (UNVERIFIED).
- `decision_outcomes`: one row per (decision, outcome_type,
  outcome_date). Holds 0 rows until a later observation arrives
  with an as-of date after the decision date; nothing is
  backfilled or estimated.

Precedent (Phases 11–14): Phase 15 stores its own tables rather
than retrofitting the Phase 3 `recommendations` table, which has
no screening/research/user-facing split, no rule version, no
evidence snapshot, no conflicts, and no gate reasons.

## Services

- `backend/app/services/decision_engine/__init__.py`: rules v1,
  constants (decision date 2026-11-04, price date 2026-11-03,
  stale threshold 365 days, universe HUBC/NML/OGDC/HBL).
- `backend/app/services/decision_engine/scoring.py`: pure
  functions only (no database access) — dimension scores,
  aggregation, conclusion mapping, completeness, agreement,
  confidence, user-facing mapping. ABSENT (None) is never
  zero-filled.
- `backend/app/services/decision_engine/runner.py`: reads stored
  rows, evaluates gates before any conclusion, builds evidence
  snapshots, derives conflicts by generic rules, asserts
  no-look-ahead (any evidence dated after the decision date
  aborts the run), writes idempotently (a second --commit writes
  0 new rows).

## CLI and API

- `scripts/run_decision_engine.py`: --dry-run (default) /
  --commit, optional --company filter. JSON report on stdout,
  summary on stderr. Exit codes: 0 ok, 1 operational failure,
  2 missing DATABASE_URL / bad arguments.
- `backend/app/api/v1/endpoints/decisions.py`: GET-only —
  /decisions/rules, /decisions?ticker=, /decisions/status.
  Unknown ticker 404; known ticker with no rows 200 with a note.
  No POST/PUT/PATCH/DELETE route exists on this router, and no
  execution identifier exists anywhere in application source (a
  test scans for it).

## No-look-ahead enforcement

- Evidence with a publication, event, or observation date after
  2026-11-04 is excluded by assertion in the runner (the run
  fails rather than silently dropping it).
- A NULL publication date on valuation inputs is a blocking gate
  (NML), because the valuation cannot be placed in time.
- Decision outcomes may only be recorded with outcome dates
  after the decision date (enforced by the outcome-recording
  rule, documented; the table is empty in this run).

## Acceptance gate — status

- Every recommendation reconstructable from dated evidence: YES
  — evidence_snapshot + rules_version + conflicts + gates per
  decision.
- Abstention works: YES — NML (stale + publication unknown)
  and HBL (no statements) are INSUFFICIENT_EVIDENCE, and all
  user-facing values are WITHHELD.
- No unsupported certainty or fabricated score: YES — confidence
  is categorical from measured factors; ABSENT is never scored.
- Risk and conflicts visible: YES — flags, warnings and 6
  preserved conflicts served with every decision.
- No brokerage order path present: YES — proven by a codebase
  scan test (execution identifiers + write routes).

Verdict: PARTIALLY COMPLETE. The engine, rules, audit model and
APIs are complete; the pipeline's evidence limits (UNVERIFIED
inputs, abstained forecasts, absent technicals, 3-company
coverage, HBL pending) keep every user-facing value WITHHELD
and two of four companies abstained. That is the honest gate
outcome, not a defect in the engine.
