"""Phase 26 evaluation dataset registry, model cards, promotion gates.

Every entry states what it points at and what would change it.
Nothing here claims an accuracy, a promotion, or an evaluation
that does not exist: the seed run's honest state is that no
model has out-of-sample evaluated predictions, no recommendation
has a recorded outcome, and no human approval gate has been
granted — so every model card is NOT_PROMOTED and every
promotion gate is NOT_MET. A gate is MET only by positive
evidence, never by the absence of failures.

Split policies (brief: "Results are reproducible and
out-of-sample"):

- Forecast evaluation uses expanding-window walk-forward folds
  (Phase 13's validator): folds are chronological, never
  shuffled. A label counts as matured only after the full
  forecast horizon has elapsed AND an actual observation at or
  after the horizon date exists in stored rows.
- Recommendation evaluation uses the decision date as the
  split: only observations with an as-of date AFTER the
  decision date count as outcomes (Phase 15's rule). Nothing
  is backfilled.
- Agent/RAG evaluation uses fixed golden sets: the same case
  keys, the same expected pages/kinds, every run. A retrieval
  change that breaks a golden case is a regression, not an
  improvement to hide.
- Drift evaluation compares live row counts against the
  Phase 24 baseline in the Phase 25 job registry
  (EXPECTED_COUNTS). A difference is a finding to explain,
  never an error to auto-fix.

Retraining / recalibration criteria (brief: "Set
retraining/recalibration criteria and model retirement rules"):

- Recalibrate a forecasting baseline when a new trading day
  lands that completes a horizon window (new matured labels),
  or when a new statement period loads (new feature snapshot
  origin). Until then there is nothing new to calibrate on.
- Recalibrate decision rules only as a new version (rules v2),
  never by editing v1 in place: v1's decisions must stay
  reconstructable from their evidence snapshots.
- Retire a model version when it is superseded by a version
  that passed every promotion gate, or when its evaluation
  window shows sustained failure across two consecutive
  evaluation runs. No version is retired silently: retirement
  is a recorded status change with a reason.
- No model is promoted solely because it looks good on its
  training data: in this project there is no training/test
  split to game — every stored row is both the training set
  and the evaluation set until new observations arrive, which
  is exactly why promotion requires matured out-of-sample
  labels that do not exist yet.
"""

from __future__ import annotations

# One entry per evaluation dataset. "row_count" is the count
# verified live at the end of Phase 25 (2026-11-05); the
# runner recomputes it from stored rows and reports any
# difference as a drift finding, never as a silent update.
DATASETS: list[dict] = [
    {
        "dataset_key": "forecast_targets_v1",
        "title": "Forecast target registry (targets x horizons)",
        "kind": "forecast_targets",
        "version": "targets-v1",
        "split_policy": (
            "Expanding-window walk-forward folds, chronological, never "
            "shuffled. A label is matured only after the full horizon "
            "has elapsed AND an actual observation at or after the "
            "horizon date exists in stored rows."
        ),
        "as_of_date": "2026-11-04",
        "row_count": 48,
        "status": "active",
        "evidence": {"targets": 8, "horizons": 6, "source_table": "forecast_targets"},
    },
    {
        "dataset_key": "forecast_assessments_2026_11_04",
        "title": "Forecast assessments at origin 2026-11-03",
        "kind": "forecast_assessments",
        "version": "assessments-2026-11-04",
        "split_policy": (
            "Origin 2026-11-03 (single price date). No horizon has "
            "elapsed in data, so no assessment has a matured label."
        ),
        "as_of_date": "2026-11-04",
        "row_count": 120,
        "status": "active",
        "evidence": {
            "computed": 0,
            "insufficient_inputs": 120,
            "source_table": "forecast_assessments",
        },
    },
    {
        "dataset_key": "decisions_2026_11_04",
        "title": "Investment decisions at decision date 2026-11-04",
        "kind": "decisions",
        "version": "decisions-v1-2026-11-04",
        "split_policy": (
            "Decision date is the split: only observations with an "
            "as-of date AFTER 2026-11-04 count as outcomes. Nothing "
            "is backfilled."
        ),
        "as_of_date": "2026-11-04",
        "row_count": 4,
        "status": "active",
        "evidence": {
            "user_facing_withheld": 4,
            "outcomes_recorded": 0,
            "source_table": "decisions",
        },
    },
    {
        "dataset_key": "rag_benchmark_r3",
        "title": "RAG benchmark run r3 (page-level traceability)",
        "kind": "rag_benchmark",
        "version": "phase19-benchmark-2026-11-04-r3",
        "split_policy": (
            "Fixed golden set: the same 6 case keys and expected "
            "pages/kinds every run. Page-level traceability is the "
            "brief's acceptance criterion; snippet-level precision "
            "is reported separately, not hidden."
        ),
        "as_of_date": "2026-11-04",
        "row_count": 6,
        "status": "active",
        "evidence": {
            "cases": 6,
            "passed": 6,
            "recall_at_5": 1.0,
            "source_table": "rag_benchmark_results",
            "note": (
                "r1/r2 historical rows (1/6, 2/6) were runs of "
                "superseded retrieval code and were NOT reproduced "
                "after VM replacement #6; they were not fabricated. "
                "Live count is 6 (r3 only)."
            ),
        },
    },
    {
        "dataset_key": "agent_evaluations_demo",
        "title": "Agent evaluations from the Phase 18 demo graph",
        "kind": "agent_evaluations",
        "version": "phase18-demo-graph",
        "split_policy": (
            "Fixed evaluation cases: prompt injection, tool failure, "
            "loop termination, duplicate action, hallucinated value, "
            "deterministic authority. Same case names every run."
        ),
        "as_of_date": "2026-11-04",
        "row_count": 6,
        "status": "active",
        "evidence": {
            "passed": 6,
            "source_table": "agent_evaluations",
        },
    },
    {
        "dataset_key": "backtest_metrics_2026_11_04",
        "title": "Backtest metrics (all NOT_RUNNABLE)",
        "kind": "backtest_metrics",
        "version": "backtests-2026-11-04",
        "split_policy": (
            "Window 2026-11-03 to 2026-11-03 holds a single price "
            "observation and zero return intervals; no metric is "
            "computable. A single-day snapshot is never presented "
            "as a backtest result."
        ),
        "as_of_date": "2026-11-04",
        "row_count": 55,
        "status": "active",
        "evidence": {
            "computed": 0,
            "insufficient_inputs": 50,
            "not_applicable": 5,
            "source_table": "backtest_metrics",
        },
    },
    {
        "dataset_key": "report_qa_2026_11_04",
        "title": "Report QA audit (Phase 22 seed run)",
        "kind": "report_figures",
        "version": "reports-2026-11-04",
        "split_policy": (
            "Every figure carries a kind and a computation status; "
            "non-computed figures carry no value. QA runs on every "
            "draft; approval is a CLI transition only."
        ),
        "as_of_date": "2026-11-04",
        "row_count": 541,
        "status": "active",
        "evidence": {
            "reports": 22,
            "computed_figures": 335,
            "published_externally": 0,
            "source_table": "report_figures",
        },
    },
    {
        "dataset_key": "golden_cases_v1",
        "title": "Phase 26 golden test suite",
        "kind": "golden_cases",
        "version": "golden-v1",
        "split_policy": (
            "Fixed case keys with expected outcomes. Pure-function "
            "cases run against current code; stored-evidence cases "
            "read stored evaluation rows. A failed case blocks "
            "promotion of every model it touches."
        ),
        "as_of_date": "2026-11-05",
        "row_count": 14,
        "status": "active",
        "evidence": {"source_table": "golden_test_cases"},
    },
]

# One card per model/version. "training_data" is "stored rows
# only" for every card: no external training corpus exists in
# this project, and claiming one would be fabrication.
MODEL_CARDS: list[dict] = [
    {
        "model_key": "forecasting_baselines",
        "version": "baselines-v1",
        "purpose": (
            "Point + interval baselines for 8 targets x 6 horizons: "
            "naive persistence, historical mean, moving average 5, "
            "moving average 20, AR(1)."
        ),
        "training_data": (
            "Stored rows only (single price date 2026-11-03, "
            "single-period statements). No production prediction "
            "exists: every assessment abstained."
        ),
        "evaluation_status": (
            "Not evaluable: 0 predictions, 0 matured labels. "
            "Fixture-tested only (minima: naive 1/11, mean 5/15, "
            "MA5 5/15, MA20 20/30, AR1 30/40 observations)."
        ),
        "limitations": (
            "No interval can be validated without residual history; "
            "naive point-only outputs are recorded as abstained, "
            "never stored as forecasts."
        ),
        "promotion_status": "NOT_PROMOTED",
        "evidence": {"assessments": 120, "computed": 0},
    },
    {
        "model_key": "forecasting_candidates",
        "version": "candidates-registered-only",
        "purpose": "ETS / ARIMA / ML-tree forecast candidates.",
        "training_data": "None: registered as candidates only, not implemented.",
        "evaluation_status": "Not implemented; nothing to evaluate.",
        "limitations": "Must not be presented as available methods.",
        "promotion_status": "NOT_PROMOTED",
        "evidence": {"implemented": False},
    },
    {
        "model_key": "decision_rules",
        "version": "decision-rules-v1",
        "purpose": (
            "Seven-dimension scoring producing screening, research, "
            "and user-facing levels for HUBC, NML, OGDC, HBL."
        ),
        "training_data": (
            "Stored Phase 8/9/10/12/13/14 rows as of 2026-11-04. "
            "Forecasts contribute nothing by design (abstained)."
        ),
        "evaluation_status": (
            "Abstention measurable (user-facing WITHHELD 4/4); "
            "subsequent performance not evaluable (0 outcomes, no "
            "later price, no benchmark, no costs)."
        ),
        "limitations": (
            "Confidence caps at LOW while all inputs are "
            "UNVERIFIED; calibration NOT_ESTABLISHED; conflicts "
            "preserved, never averaged."
        ),
        "promotion_status": "NOT_PROMOTED",
        "evidence": {"decisions": 4, "outcomes": 0},
    },
    {
        "model_key": "screener_score",
        "version": "screener-score-v1",
        "purpose": "Rank filter results as passed/scored over 18 filters.",
        "training_data": "Stored rows only (screens run 2026-11-04).",
        "evaluation_status": (
            "Match counts reproducible (1,418 results, 241 MATCH); "
            "predictive quality not evaluable (no outcomes)."
        ),
        "limitations": (
            "Screen matches are filter results, not opportunities, "
            "not recommendations, not forecasts."
        ),
        "promotion_status": "NOT_PROMOTED",
        "evidence": {"results": 1418, "matches": 241},
    },
    {
        "model_key": "risk_controls",
        "version": "controls-v1",
        "purpose": "Five portfolio controls with pass/breach/blocked checks.",
        "training_data": "Stored rows only (simulated portfolios, 2026-11-03 closes).",
        "evaluation_status": (
            "Checks reproducible (5 pass, 1 breach on the SIMULATED "
            "portfolio only, 1 blocked); breach is a finding, not "
            "a real holding violation."
        ),
        "limitations": "Series risk metrics NOT_CALCULABLE (no return series).",
        "promotion_status": "NOT_PROMOTED",
        "evidence": {"checks": 7, "breaches": 1},
    },
    {
        "model_key": "rag_retrieval",
        "version": "retrieval-token-v1",
        "purpose": (
            "Deterministic full-text + metadata + exact-identifier "
            "retrieval over 943 chunks from 3 issuer reports."
        ),
        "training_data": (
            "3 issuer-hosted reports (HUBC 423 pp., NML 72 pp., "
            "OGDC 12 pp.). DPS-hosted filings NOT seeded."
        ),
        "evaluation_status": (
            "Benchmark r3: 6/6 passed, recall@5 1.0 at page level; "
            "mean citation precision 0.4667 reported, not hidden. "
            "Vector retrieval NOT_IMPLEMENTED."
        ),
        "limitations": (
            "Token heuristics outscore figure rows with header "
            "windows; snippet-level precision not achievable "
            "without row-label-aware table parsing. No embedding "
            "model verified, so no vector retrieval exists."
        ),
        "promotion_status": "NOT_PROMOTED",
        "evidence": {"chunks": 943, "benchmark_cases": 6},
    },
    {
        "model_key": "orchestration_fallback",
        "version": "fallback-v1",
        "purpose": "Rule-based 16-agent orchestration without an LLM.",
        "training_data": "Stored rows only (demo graph, 2026-11-04).",
        "evaluation_status": (
            "6/6 evaluations PASS (injection, tool failure, loop, "
            "duplicate, hallucination, deterministic authority). "
            "LLM-backed execution unavailable."
        ),
        "limitations": (
            "No verified local model; consequential actions "
            "(publish, promotion, external send) denied to all; "
            "preemptive timeouts unavailable (checkpoint checks "
            "only)."
        ),
        "promotion_status": "NOT_PROMOTED",
        "evidence": {"evaluations": 6, "passed": 6},
    },
    {
        "model_key": "technical_indicators",
        "version": "registry-v1.0",
        "purpose": "62-indicator registry with warm-ups and coverage.",
        "training_data": "Single price date 2026-11-03 (444 rows).",
        "evaluation_status": (
            "0 calculable values (470 assessed, 124 error rows). "
            "Nothing to evaluate until more trading days land."
        ),
        "limitations": (
            "Daily return missing_data(470): previous_close NULL. "
            "More trading days alone do not unblock it without a "
            "validated calendar and adjustment methodology."
        ),
        "promotion_status": "NOT_PROMOTED",
        "evidence": {"definitions": 62, "values": 0},
    },
    {
        "model_key": "reports_qa_gate",
        "version": "qa-v1",
        "purpose": (
            "QA gate on every report draft: cut-off/date present, "
            "exact section list, DISCLAIMER present, forbidden "
            "wording rejected, every figure validated, every "
            "non-disclosures section cited or marked unavailable."
        ),
        "training_data": "Stored Phase 5/8/9/10/12/14/15/16/20/21 rows.",
        "evaluation_status": (
            "22 drafts pass QA; 0 approved (nothing internally "
            "reviewed yet); 0 published externally (no publish "
            "step exists)."
        ),
        "limitations": (
            "QA proves internal consistency, not truth: every "
            "input is UNVERIFIED, so a passing draft is still a "
            "DRAFT."
        ),
        "promotion_status": "NOT_PROMOTED",
        "evidence": {"reports": 22, "figures": 541, "approved": 0},
    },
]

# Promotion gates. Every gate is NOT_MET in the seed run.
# "reason" names the exact missing evidence; a gate flips to
# MET only when that evidence is recorded, never by rewording.
PROMOTION_GATES: list[dict] = [
    {
        "gate_key": "out_of_sample_evidence",
        "applies_to": "all",
        "requirement": (
            "Results are reproducible and out-of-sample: evaluated "
            "predictions with matured labels from observations "
            "after the forecast/decision date."
        ),
        "status": "NOT_MET",
        "reason": (
            "0 predictions exist (Phase 13 abstained on all 120 "
            "assessments) and 0 outcomes exist (Phase 15 outcomes "
            "table empty; no price after 2026-11-03)."
        ),
        "evidence": {"predictions": 0, "matured_labels": 0, "outcomes": 0},
    },
    {
        "gate_key": "baselines_and_negatives_included",
        "applies_to": "all",
        "requirement": (
            "Baselines and negative outcomes are included: every "
            "evaluation reports baseline-relative performance and "
            "every abstention, WITHHELD value, NOT_RUNNABLE run, "
            "and failed prediction, not only successes."
        ),
        "status": "NOT_MET",
        "reason": (
            "The framework records negatives (abstention 100%, "
            "WITHHELD 4/4, backtests NOT_RUNNABLE), but no "
            "baseline-relative comparison is computable without "
            "evaluated predictions."
        ),
        "evidence": {
            "abstention_rate": 1.0,
            "withheld": 4,
            "baseline_comparisons": 0,
        },
    },
    {
        "gate_key": "evidence_governed_promotion",
        "applies_to": "all",
        "requirement": (
            "Model promotion is governed by evidence: a versioned "
            "evaluation run, a model card, and a gate record exist "
            "before any promotion, and training-data performance "
            "alone never promotes a model."
        ),
        "status": "NOT_MET",
        "reason": (
            "Evaluation runs, model cards, and gate records now "
            "exist (this phase), but no model has any evaluated "
            "out-of-sample performance to govern a promotion."
        ),
        "evidence": {"promoted_models": 0},
    },
    {
        "gate_key": "no_unsupported_accuracy_claims",
        "applies_to": "all",
        "requirement": (
            "No unsupported accuracy claims are made: every "
            "accuracy, precision, recall, or coverage figure cites "
            "its evaluated rows, and unevaluated claims are "
            "labelled NOT_EVALUABLE, never numbered."
        ),
        "status": "NOT_MET",
        "reason": (
            "The framework enforces this (NOT_EVALUABLE metrics "
            "carry NULL values), but the gate cannot be MET until "
            "at least one evaluated claim exists to check."
        ),
        "evidence": {"evaluated_claims": 0, "not_evaluable_metrics": 5},
    },
    {
        "gate_key": "human_approval_recorded",
        "applies_to": "all",
        "requirement": (
            "A recorded human approval exists for the promotion "
            "(quality-status promotion, first APPROVED report, "
            "first live auth account, or any production release)."
        ),
        "status": "NOT_MET",
        "reason": (
            "No human approval gate has been granted for any "
            "promotion, report approval, live account, or release."
        ),
        "evidence": {"approvals_recorded": 0},
    },
]
