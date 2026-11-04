# Phase 13 — Run report (2026-11-04)

## Branch and commit

- Branch: `phase-13-forecasting`, new branch from `a58a104`
  (phase-12-ownership-actions-breadth tip). Base tip unmoved;
  `main` untouched at `eb6025b`.
- Migration head: `20261104_0009` → `20261104_0010`.

## Run evidence

- `--dry-run`: targets 48/0, snapshots 116/0, assessments 120/0,
  computed 0, Phase 3 forecasts 0.
- `--commit`: same counts written (48 targets, 116 snapshots, 120
  assessments, all UNVERIFIED).
- Second `--commit`: 0 new rows (48/116/120 skipped) — idempotency
  proven.
- Per-company snapshots: HUBC 37 (32 fundamentals + 3 valuations +
  close + volume), NML 35 (31 + 2 + 2), OGDC 32 (28 + 2 + 2);
  macro snapshots 12 (all current Phase 10 observations).
- Per-company assessments: 36 each (6 targets x 6 horizons);
  macro assessments 12 (2 targets x 6 horizons).
- Prior-phase rows untouched: statements 88, prices 444,
  valuations 51, indicators 12, news events 7, ownership 34;
  Phase 3 `forecasts` 0, `forecast_evaluations` 0.

## Tests and checks

- Backend suite: 210 passed, 0 failed (197 prior + 13 new pure
  tests: baselines, intervals, walk-forward, leakage, abstention).
- Ruff check: clean on all non-migration Phase 13 files (the
  migration carries the same 5 boilerplate UP035/UP007 findings as
  the Phase 12 migration — established migration style, not fixed).
- Ruff format: clean on all Phase 13 files after formatting.
- Live API (TestClient): `/forecasting/status` 200 (48/116/120/0/0),
  `/forecasting/targets` 200 (48), `/forecasting/assessments?ticker=HUBC`
  200 (36), `/forecasting/assessments/macro` 200 (12),
  `/forecasting/features?ticker=OGDC` 200 (32), HBL 200 with empty
  list + pending note, unknown ticker 404.

## Independent audit notes

- Spot-checked assessment rows against the database: HUBC
  close_price 1d (series 1, naive `point_only_abstained`),
  earnings 1d (series 2, naive `point_only_abstained`), return 1d
  (series 0, `insufficient_inputs`) — all match the runner's
  read-from-DB series lengths.
- No status was promoted: every new row is UNVERIFIED, matching its
  inputs. No CSV/PDF committed. No credentials in code or docs.
- One audit-driven fix during the run: the macro snapshot scope
  was widened from the 2 target indicators to all 12 current macro
  observations (a feature store should hold all usable features,
  not only the forecast targets).

## Remaining blockers

See `abstention_report.md` (trading days, statement periods, macro
vintages, HBL load, VERIFIED promotion). No other Phase 13 work
remains open.
