# Phase 6 — Implementation specification

## What was built (and what was deliberately not built)

Built:

- `backend/app/services/technical_indicators/` — a pure,
  dependency-free calculation package:
  - `conventions.py` — the registry: 62 indicator outputs with
    category, formula text, version (1.0), default parameters
    and warm-up bars. The single source of truth.
  - `formulas.py` — Decimal implementations of every registered
    indicator, raising InsufficientData (insufficient_warmup /
    missing_data / degenerate_input) instead of fabricating.
  - `aggregation.py` — daily -> weekly / monthly aggregation
    with always-partial period status (no validated calendar).
  - `coverage.py` — per-security, per-indicator CALCULABLE /
    NOT_CALCULABLE assessment with reasons and unblockers, with
    as-of slicing for no-look-ahead and conflicted-input
    exclusion.
  - `runner.py` — production assessment runner: seeds the 62
    definitions and configurations idempotently, assesses all
    470 securities, writes one run row, aggregate error rows,
    and value rows only for CALCULABLE verdicts on new grains.
  - `signals.py` — the SEPARATE signal-event engine with an
    empty activated-rule set (see signal_engine_separation.md).
- `backend/app/api/v1/endpoints/indicators.py` — GET-only
  endpoints (coverage, per-ticker coverage, stored values,
  stored signals), registered in the v1 router.
- `scripts/run_technical_indicators.py` — CLI with --dry-run
  (default) and --commit, mirroring the Phase 5 CLI's exit-code
  and JSON-report conventions.
- `frontend/app/indicators/page.tsx` + nav entry — coverage
  tables and a per-ticker verdict lookup with truthful empty
  states; no chart is drawn from a single point.
- `database/migrations/versions/20261104_0005_phase_6_technical_immutability.py`
  — applies the existing psx_prevent_mutation() trigger to the
  four Phase 6 output tables (values, signal events, features,
  regime observations). Alembic head is now 20261104_0005.

Reused, not duplicated (Phase 3 already defined them):
technical_indicator_definitions, _configurations, _values,
technical_signal_events, quantitative_market_features,
market_regime_observations, technical_calculation_runs,
technical_calculation_errors. No new tables were created.

NOT built (honestly out of scope on this data):

- No indicator VALUE rows (0 written — nothing is calculable).
- No signal events (0 written — no rule is activated).
- No regime/feature rows (0 written — no inputs to classify).
- No adjusted series (no validated corporate-action method).
- No intraday anything (no validated intraday data).
- No charts (a one-point chart would imply a trend).

## Storage and versioning design

- A value row's grain is (security, configuration, observation
  date, timeframe) — the Phase 3 unique constraint. Values carry
  calculation_version, last_input_observation_date, quality
  status, source_key and collected_at (provenance), per spec.
- Version history is never overwritten: the 0005 migration makes
  UPDATE/DELETE on output tables raise. A correction therefore
  uses a NEW configuration version: get_active_config()
  deactivates the superseded active configuration and creates
  one with a bumped config_version (audit H3, implemented —
  not merely documented); old rows stay under their old
  configuration. The values API exposes indicator_key,
  configuration id, config_version and parameters per row, so
  a consumer can identify which version a row belongs to
  (audit M1); filtering by configuration id is not yet
  implemented — filtering by indicator_key is. The trigger was
  proven to fire on UPDATE and DELETE in a rolled-back
  transaction with zero residue.
- Value quality inherits the lowest input quality. Today's
  inputs are all UNVERIFIED, so any future value is UNVERIFIED
  until a second agreeing source exists. Calculation never
  upgrades quality.
- Run records: one row per assessment run (run_key
  phase06-coverage-<as_of>, status, securities processed,
  records written). Error rows are aggregates per
  (indicator_key, reason, bars_available) with security_id NULL
  — per-security verdicts are recomputed deterministically by
  the live coverage API, so storing ~29,000 per-security error
  rows (470 x 62) would be noise, not information. This choice
  is documented here, not hidden.

## Incremental recalculation and correction propagation

- A re-run writes only grains that do not already exist;
  existing value rows are never rewritten (and the trigger
  would refuse anyway). A second --commit for the same as-of
  writes nothing at all: if a completed run row already exists
  for that run_key, the runner reports already_recorded and
  returns without duplicating run or error rows (audit H4).
  Late-arriving rows for an already-run as-of date need
  operator handling with a distinct run_key; that path is not
  automated here.
- New trading days extend every series; warm-ups are then met
  progressively (SMA(5) first, then SMA(10), and so on). The
  runner's as-of defaults to the latest price date; passing an
  earlier --as-of reproduces the earlier assessment verdicts
  exactly (no-look-ahead slice), which the tests prove — the
  DB writes for a repeated as-of are guarded by the re-run
  rule above, not duplicated.
- If stored inputs for an existing grain ever changed (they
  cannot — market_prices is immutable), the documented path is
  a new configuration version, never an edit.

## No-look-ahead rule (tested, not just stated)

Every computation receives only bars dated on or before the
as-of date. The test suite proves it: assessing a 5-bar series
as of its 3rd bar yields the 3-bar verdicts, and computing on
the 3-bar prefix directly gives identical values. Weekly and
monthly aggregation never pulls a bar from a later period into
an earlier one, and Ichimoku Senkou values are stored at their
computation date, never at their plotted date (see
formula_conventions.md).
