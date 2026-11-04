# Phase 26 — Implementation Specification

## Brief

Playbook Phase 26 (lines 1858–1916): model evaluation, forecast
monitoring, and research quality benchmarking. Deliverables:
evaluation dataset registry, forecast/recommendation performance
dashboards, agent/RAG benchmark suite, model cards, promotion
gates, drift policy.

## What this phase builds

| Piece | Location |
|---|---|
| 7 tables (migration 0022) | `backend/app/models/evaluation.py`, `database/migrations/versions/20261104_0022_phase_26_evaluation.py` |
| Dataset registry, model cards, promotion gates | `backend/app/services/evaluation/registry.py` |
| Pure metric computation | `backend/app/services/evaluation/metrics.py` |
| Golden suite (14 cases) | `backend/app/services/evaluation/golden.py` |
| Runner (dry-run default, --commit, idempotent) | `backend/app/services/evaluation/runner.py` |
| GET-only API (9 routes) | `backend/app/api/v1/endpoints/evaluation.py` |
| CLI | `scripts/run_evaluation.py` |
| Dashboard | `frontend/app/admin/evaluation/page.tsx` (+ nav entry) |
| Tests | `backend/tests/test_evaluation_phase26.py`, `frontend/e2e/phase26/evaluation.spec.ts` |

## Design rules (inherited, not reinvented)

- **No zero-fill, no estimation.** A metric that cannot be
  computed from stored rows is NOT_EVALUABLE with a NULL value
  and an exact reason — the same discipline as Phase 13
  assessments.
- **Matured labels only.** A forecast label counts as matured
  only after the full horizon has elapsed AND an actual
  observation at or after the horizon date exists in stored
  rows. Horizon day counts (1d=1, 1w=7, 1m=30, 3m=90, 6m=180,
  12m=365) are a documented approximation for the maturity
  check only; the seed-run conclusion (0 matured) holds under
  any calendar convention because the latest stored price date
  equals the origin date.
- **Decision date is the split.** Only observations with an
  as-of date after 2026-11-04 count as recommendation outcomes.
  Nothing is backfilled.
- **Fixed golden sets.** The same case keys and expected
  outcomes every run. A retrieval change that breaks a golden
  case is a regression, not an improvement to hide.
- **Promotion requires positive evidence.** Every model card is
  NOT_PROMOTED and every gate is NOT_MET in the seed run. A
  gate flips to MET only when its missing evidence is
  recorded, never by rewording and never by the absence of
  failures.
- **Stored-evidence golden checks never re-emit adversarial
  text.** The injection and hallucination cases read stored
  evaluation rows by case name only (result + quarantine flag /
  verdict). No probe input text appears in Phase 26 code.
- **Ticker-keyed identity.** Company identity is resolved by
  ticker everywhere (surrogate ids shift across fresh imports;
  Phase 23 repair). The runner resolves HUBC/HBL by ticker.
- **No new capabilities.** No order, execution, publication,
  external-send, or quality-promotion concept exists in this
  phase. The API is GET-only; runs execute through the CLI.

## What the seed run evaluates (and what it cannot)

| Subject | Computed | NOT_EVALUABLE / NOT_APPLICABLE |
|---|---|---|
| Forecast | predictions 0, assessments 120 (0 computed, 120 insufficient), matured labels 0 | MAE, RMSE, directional accuracy, interval coverage, baseline-relative performance |
| Recommendation | decisions 4, abstention rate 1.0, outcomes 0, adverse observed 0 (among 0 recorded) | subsequent return, benchmark-relative return, precision, recall, calibration |
| Agent | pass rate 6/6 = 1.0, per-category rates | — |
| RAG | recall@5 1.0, pass rate 6/6, mean citation precision 0.4667 | vector retrieval (not implemented) |
| Backtest | runs 5, runnable 0, metrics computed 0 | Sharpe (no return series, no validated risk-free series) |
| Reports QA | reports 22, approved 0, published 0, figures 541 (335 computed) | — |
| Drift | differences vs Phase 24 baseline (see run report) | — |

## Golden suite (14 cases)

source_matching (4: trailing LIMITED, &/and, no abbreviation
expansion, D.G. tokens), entity_resolution (1: shared-alias cap
0.50 + forced review), tool_selection (1: deterministic
authority + unchanged HUBC close), citation (1: QA citation
rule), extraction (1: 3 documents → 943 chunks), summarization
(1: stored summaries ≤ 280 chars), refusal_abstention (2: HBL
missing documents, all decisions WITHHELD),
injection_resistance (1: stored injection evaluation PASS +
quarantine), hallucination (1: stored hallucination evaluation
PASS + quarantine verdict), conflicting_sources (1: 470
UNVERIFIED despite 61 LEAP rows).

## Drift policy (summary; full text in promotion_gates_and_drift_policy.md)

Drift = live row counts vs the Phase 24 baseline in the Phase
25 job registry (EXPECTED_COUNTS). A difference is a finding
to explain, never an error to auto-fix. Retraining triggers:
new trading day completing a horizon window, or a new
statement period loading. Recalibration of decision rules
happens only as a new version (v1 is never edited in place).
Retirement: supersession by a fully gated version, or
sustained failure across two consecutive evaluation runs.
No model is promoted solely on training-data performance —
in this project every stored row is both training and
evaluation data until new observations arrive, which is
exactly why promotion requires matured out-of-sample labels
that do not exist yet.

## Corrections made during this run

1. `matured_labels` was first drafted as a hardcoded zero;
   corrected so the runner counts assessments whose horizon
   actually matured (0 in the seed run, for the right reason).
2. The alias-collision golden check first used tickers present
   in the resolved text; the resolver rightly preferred the
   ticker match at 1.0. Corrected to tickers absent from the
   text, so the shared stripped alias is the only match.
3. `predictions_count` was first hardcoded 0; corrected to count
   the Phase 3 forecasts table (0 rows, now read, not assumed).
4. A nonsense `rag_chunks` expression in an early runner draft
   was replaced with a real RagChunk count before any run.
