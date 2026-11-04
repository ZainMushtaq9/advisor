# Phase 26 — Promotion Gates and Drift Policy

## Promotion gates

A model version is promoted only when EVERY gate is MET by
positive, recorded evidence. The gates (full requirement text
in `backend/app/services/evaluation/registry.py`):

| Gate | Applies to | Seed-run status | Exact missing evidence |
|---|---|---|---|
| out_of_sample_evidence | all | NOT_MET | Evaluated predictions with matured labels from observations after the forecast/decision date |
| baselines_and_negatives_included | all | NOT_MET | A baseline-relative comparison over evaluated predictions |
| evidence_governed_promotion | all | NOT_MET | Evaluated out-of-sample performance to govern a promotion |
| no_unsupported_accuracy_claims | all | NOT_MET | At least one evaluated claim to check |
| human_approval_recorded | all | NOT_MET | A recorded human approval for the promotion |

A gate is never MET by the absence of failures, never MET by
rewording, and never MET by training-data performance. No
model is promoted solely because it looks good on its
training data: in this project every stored row is both the
training set and the evaluation set until new observations
arrive, which is exactly why promotion requires matured
out-of-sample labels that do not exist yet.

## Drift policy

**Definition.** Drift = a difference between live row counts
and the Phase 24 baseline (EXPECTED_COUNTS in the Phase 25
job registry). The Phase 26 runner recomputes the comparison
on every run and stores one metric per differing table.

**Response.** A difference is a finding to explain in the run
report, never an error to auto-fix and never a silent baseline
update. A later phase that legitimately changes a count
updates the baseline explicitly with its evidence (Phase 25
registry docstring rule); otherwise the difference stands as
drift.

**Informational counts (not drift).** Tables created after the
baseline are not compared: job tables (Phase 25), auth tables
(Phase 24, 0 by decision), evaluation tables (this phase),
and rag_benchmark_results (6 = r3 only; the r1/r2 divergence
is a recorded recovery outcome, not drift).

## Retraining / recalibration criteria

- **Forecasting baselines:** recalibrate when a new trading
  day lands that completes a horizon window (new matured
  labels), or when a new statement period loads (new feature
  snapshot origin). Until then there is nothing new to
  calibrate on — recalibrating on the same single date would
  be fitting noise.
- **Decision rules:** recalibrate only as a new version
  (rules v2). v1 is never edited in place: its decisions must
  stay reconstructable from their evidence snapshots.
- **RAG retrieval:** re-benchmark (new run id, never rewriting
  r3) when the chunking, scoring, or corpus changes.
- **Screener / risk / QA:** re-evaluate on every evaluation
  run; thresholds change only as new versioned registries.

## Retirement rules

- A version retires when superseded by a version that passed
  every promotion gate.
- A version retires when its evaluation window shows sustained
  failure across two consecutive evaluation runs.
- Retirement is a recorded status change with a reason. No
  version is retired silently, and no retired version's rows
  are deleted: history stays queryable.
- No version is retired in the seed run: no version has an
  evaluation window to fail in yet.
