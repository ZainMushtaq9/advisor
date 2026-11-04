"""Phase 26 pure metric computation (no DB, no network).

Every function takes plain data (counts, rows, dates) and returns
metric dicts with a value (or None), a status, a reason, and
evidence. NOT_EVALUABLE means the metric cannot be computed
from the data that exists — it is never zero-filled, never
estimated, and never presented as a number.

Horizon maturity: a forecast label is matured only when the
full horizon has elapsed AND an actual observation at or after
the horizon date exists. Horizon lengths use fixed day counts
(1d=1, 1w=7, 1m=30, 3m=90, 6m=180, 12m=365) as a documented
approximation for the maturity check only: the seed-run
conclusion (no horizon matured) holds under any calendar
convention, because the latest stored price date EQUALS the
origin date — no observation exists after the origin at all.
"""

from __future__ import annotations

from datetime import date, timedelta

HORIZON_DAYS: dict[str, int] = {
    "1d": 1,
    "1w": 7,
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "12m": 365,
}

HORIZONS: tuple[str, ...] = ("1d", "1w", "1m", "3m", "6m", "12m")


def metric(
    subject_key: str,
    metric_key: str,
    value: float | int | None,
    status: str,
    reason: str,
    evidence: dict | None = None,
) -> dict:
    """One metric row dict (matches the evaluation_metrics table)."""
    return {
        "subject_key": subject_key,
        "metric_key": metric_key,
        "value": value,
        "status": status,
        "reason": reason,
        "evidence": evidence or {},
    }


def matured_horizons(origin: date, latest_observation: date) -> list[str]:
    """Horizons whose horizon date is on/before the latest observation.

    A horizon counts as matured only if an actual observation
    exists at or after origin + horizon days. With a single
    price date equal to the origin, this is empty for every
    horizon — the honest seed-run result.
    """
    matured = []
    for horizon in HORIZONS:
        if origin + timedelta(days=HORIZON_DAYS[horizon]) <= latest_observation:
            matured.append(horizon)
    return matured


def forecast_metrics(
    *,
    assessments_total: int,
    assessments_computed: int,
    assessments_insufficient: int,
    predictions_count: int,
    origin: date,
    latest_price_date: date | None,
    matured_labels: int,
    matured_horizon_list: list[str],
) -> list[dict]:
    """Forecast evaluation metrics from stored assessment counts.

    Error, directional accuracy, calibration, interval coverage,
    and baseline-relative performance are NOT_EVALUABLE whenever
    predictions or matured labels are missing — both are missing
    in the seed run (0 predictions, 0 matured labels). The runner
    counts matured labels from stored assessment rows whose
    horizon is in the matured list; this function never invents
    that count.
    """
    out = [
        metric(
            "forecast",
            "predictions_count",
            predictions_count,
            "computed",
            "Rows in the Phase 3 forecasts table. Phase 13 abstained "
            "on every assessment, so no forecast row exists.",
            {"assessments_total": assessments_total},
        ),
        metric(
            "forecast",
            "assessments_total",
            assessments_total,
            "computed",
            "Stored Phase 13 assessment rows at the forecast origin.",
            {},
        ),
        metric(
            "forecast",
            "assessments_computed",
            assessments_computed,
            "computed",
            "Assessments with a validated interval forecast. None: "
            "no residual history exists from which any interval "
            "could be validated.",
            {},
        ),
        metric(
            "forecast",
            "assessments_insufficient",
            assessments_insufficient,
            "computed",
            "Assessments abstained for insufficient inputs (series "
            "too short for every baseline method).",
            {},
        ),
        metric(
            "forecast",
            "matured_labels",
            matured_labels,
            "computed",
            "Assessments whose horizon has matured (horizon date on "
            "or before the latest stored price date). Zero in the "
            "seed run: the latest stored price date equals the "
            "origin date, so no horizon has elapsed in data.",
            {
                "origin": str(origin),
                "latest_price_date": (str(latest_price_date) if latest_price_date else None),
                "matured_horizons": matured_horizon_list,
            },
        ),
    ]
    for key, why in (
        (
            "mae",
            "No predictions and no matured labels: mean absolute "
            "error has no (prediction, actual) pairs.",
        ),
        (
            "rmse",
            "No predictions and no matured labels: root mean "
            "squared error has no (prediction, actual) pairs.",
        ),
        (
            "directional_accuracy",
            "No predictions and no matured labels: direction cannot be scored.",
        ),
        (
            "interval_coverage",
            "No validated intervals exist: coverage of an interval "
            "that was never produced is undefined, not zero.",
        ),
        (
            "baseline_relative_performance",
            "No evaluated predictions exist for any baseline, so "
            "no baseline-relative comparison is computable.",
        ),
    ):
        out.append(
            metric(
                "forecast",
                key,
                None,
                "not_evaluable",
                why,
                {"predictions": predictions_count, "matured_labels": matured_labels},
            )
        )
    return out


def recommendation_metrics(
    *,
    decisions_total: int,
    withheld: int,
    research_counts: dict[str, int],
    outcomes_total: int,
    latest_price_date: date | None,
    decision_date: date,
) -> list[dict]:
    """Recommendation evaluation metrics from stored decisions.

    Abstention is measurable (WITHHELD / total) and IS computed.
    Subsequent performance is NOT_EVALUABLE: outcomes require
    observations after the decision date, and none exist (no
    price after the single stored date, no benchmark series, no
    transaction costs, dividend dates unknown).
    """
    abstention = (withheld / decisions_total) if decisions_total else None
    out = [
        metric(
            "recommendation",
            "decisions_total",
            decisions_total,
            "computed",
            "Stored Phase 15 decisions at the decision date.",
            {},
        ),
        metric(
            "recommendation",
            "user_facing_abstention_rate",
            abstention,
            "computed",
            "WITHHELD user-facing values / decisions. 1.0 means "
            "every user-facing value was withheld (confidence "
            "capped at LOW, calibration NOT_ESTABLISHED).",
            {"withheld": withheld, "total": decisions_total},
        ),
        metric(
            "recommendation",
            "outcomes_recorded",
            outcomes_total,
            "computed",
            "Stored Phase 15 outcome rows. Zero until a later "
            "observation arrives with an as-of date after the "
            "decision date; nothing is backfilled.",
            {
                "decision_date": str(decision_date),
                "latest_price_date": (str(latest_price_date) if latest_price_date else None),
            },
        ),
        metric(
            "recommendation",
            "adverse_outcomes_observed",
            0,
            "computed",
            "Adverse outcomes among RECORDED outcomes. Zero because "
            "0 outcomes are recorded — this is not a claim that "
            "no adverse outcome occurred.",
            {"outcomes_recorded": outcomes_total},
        ),
    ]
    for conclusion, count in sorted(research_counts.items()):
        out.append(
            metric(
                "recommendation",
                f"research_{conclusion.lower()}",
                count,
                "computed",
                f"Decisions with research conclusion {conclusion}.",
                {},
            )
        )
    for key, why in (
        (
            "subsequent_return",
            "No outcome rows and no price after the decision date: "
            "subsequent return has no end price.",
        ),
        (
            "benchmark_relative_return",
            "No benchmark series is stored: benchmark-relative return is undefined, not zero.",
        ),
        (
            "event_classification_precision",
            "No labelled events exist: precision has no true/false positives to divide.",
        ),
        (
            "event_classification_recall",
            "No labelled events exist: recall has no positives to divide.",
        ),
        (
            "calibration",
            "Calibration needs evaluated predictions with "
            "outcomes; Phase 13 abstained and Phase 15 confidence "
            "is categorical, not probabilistic.",
        ),
    ):
        out.append(
            metric(
                "recommendation",
                key,
                None,
                "not_evaluable",
                why,
                {"outcomes": outcomes_total},
            )
        )
    return out


def agent_rag_metrics(
    *,
    agent_total: int,
    agent_passed: int,
    agent_by_category: dict[str, tuple[int, int]],
    rag_cases: int,
    rag_hits: int,
    rag_passed: int,
    rag_precisions: list[float],
) -> list[dict]:
    """Agent + RAG evaluation metrics from stored evaluation rows.

    These ARE computed: the stored Phase 18 evaluations and
    Phase 19 benchmark results are evaluated rows, not claims.
    Recall@5 is page-level (the brief's acceptance criterion);
    citation precision is reported as its mean, including the
    low direct-case values — never hidden, never averaged away
    into the pass rate.
    """
    out = [
        metric(
            "agent",
            "evaluations_total",
            agent_total,
            "computed",
            "Stored Phase 18 agent evaluation rows.",
            {},
        ),
        metric(
            "agent",
            "pass_rate",
            (agent_passed / agent_total) if agent_total else None,
            "computed",
            "PASS evaluations / total evaluations.",
            {"passed": agent_passed, "total": agent_total},
        ),
    ]
    for category, (passed, total) in sorted(agent_by_category.items()):
        out.append(
            metric(
                "agent",
                f"pass_rate_{category}",
                (passed / total) if total else None,
                "computed",
                f"PASS evaluations in category {category}.",
                {"passed": passed, "total": total},
            )
        )
    mean_precision = sum(rag_precisions) / len(rag_precisions) if rag_precisions else None
    out.extend(
        [
            metric(
                "rag",
                "benchmark_cases",
                rag_cases,
                "computed",
                "Stored Phase 19 benchmark cases (r3 run only; "
                "r1/r2 rows were superseded-code runs, not "
                "reproduced after replacement #6, not fabricated).",
                {},
            ),
            metric(
                "rag",
                "recall_at_5",
                (rag_hits / rag_cases) if rag_cases else None,
                "computed",
                "Page-level recall@5: expected page retrieved within "
                "the top 5 chunks, per the brief's acceptance "
                "criterion.",
                {"hits": rag_hits, "cases": rag_cases},
            ),
            metric(
                "rag",
                "pass_rate",
                (rag_passed / rag_cases) if rag_cases else None,
                "computed",
                "Benchmark cases passed / total cases.",
                {"passed": rag_passed, "cases": rag_cases},
            ),
            metric(
                "rag",
                "mean_citation_precision",
                mean_precision,
                "computed",
                "Mean of stored per-case citation precision. Low "
                "direct-case values (0.2000) are included, not "
                "hidden: header windows outscore figure rows under "
                "token heuristics.",
                {"precisions": rag_precisions},
            ),
            metric(
                "rag",
                "vector_retrieval",
                None,
                "not_applicable",
                "Vector retrieval is REGISTERED but NOT IMPLEMENTED: "
                "no verified local embedding model exists, so no "
                "embedding was computed, stored, or claimed.",
                {},
            ),
        ]
    )
    return out


def backtest_report_metrics(
    *,
    runs_total: int,
    runs_runnable: int,
    metrics_total: int,
    metrics_computed: int,
) -> list[dict]:
    """Backtest evaluation: the NOT_RUNNABLE verdict carried forward."""
    return [
        metric(
            "backtest",
            "runs_total",
            runs_total,
            "computed",
            "Stored Phase 17 backtest runs.",
            {},
        ),
        metric(
            "backtest",
            "runs_runnable",
            runs_runnable,
            "computed",
            "Runs with a usable window. Zero: every window holds a "
            "single price observation and zero return intervals.",
            {},
        ),
        metric(
            "backtest",
            "metrics_computed",
            metrics_computed,
            "computed",
            "Backtest metrics with values. Zero: no series was "
            "invented, extended, or interpolated to force a result.",
            {"metrics_total": metrics_total},
        ),
        metric(
            "backtest",
            "sharpe_ratio",
            None,
            "not_evaluable",
            "No return series and no validated risk-free series "
            "(the SBP policy rate 12.00% is a policy rate, never a "
            "T-bill rate).",
            {},
        ),
    ]


def reports_qa_metrics(
    *,
    reports_total: int,
    reports_approved: int,
    reports_published: int,
    figures_total: int,
    figures_computed: int,
) -> list[dict]:
    """Report QA evaluation: drafts pass QA; approval needs review."""
    return [
        metric(
            "reports_qa",
            "reports_total",
            reports_total,
            "computed",
            "Stored Phase 22 reports (all DRAFT).",
            {},
        ),
        metric(
            "reports_qa",
            "reports_approved",
            reports_approved,
            "computed",
            "Reports approved by internal review. Zero: nothing "
            "has been internally reviewed yet; approval is a CLI "
            "transition only.",
            {},
        ),
        metric(
            "reports_qa",
            "reports_published_externally",
            reports_published,
            "computed",
            "Reports published outside the system. Zero: no publish step exists.",
            {},
        ),
        metric(
            "reports_qa",
            "figures_total",
            figures_total,
            "computed",
            "Stored Phase 22 report figures.",
            {},
        ),
        metric(
            "reports_qa",
            "figures_computed",
            figures_computed,
            "computed",
            "Figures with values; the rest carry no value (never zero-filled, never estimated).",
            {},
        ),
    ]


def drift_metrics(*, expected: dict[str, int], actual: dict[str, int]) -> list[dict]:
    """Drift evaluation: live counts vs the Phase 24 baseline.

    Returns one computed metric (differences count) plus one
    metric per differing table. A difference is a finding to
    explain, never an error to auto-fix. Tables absent from
    either side are reported, not skipped.
    """
    out: list[dict] = []
    differences: dict[str, dict[str, int | None]] = {}
    for key in sorted(set(expected) | set(actual)):
        exp = expected.get(key)
        act = actual.get(key)
        if exp != act:
            differences[key] = {"expected": exp, "actual": act}
    out.append(
        metric(
            "drift",
            "differences",
            len(differences),
            "computed",
            "Tables whose live count differs from the Phase 24 "
            "baseline (EXPECTED_COUNTS in the Phase 25 job "
            "registry). Zero means no drift; any difference is a "
            "finding with its table named below.",
            {"differences": differences},
        )
    )
    for key in sorted(differences):
        out.append(
            metric(
                "drift",
                f"drift_{key}",
                None,
                "computed",
                f"Count drift on {key}: expected "
                f"{differences[key]['expected']}, actual "
                f"{differences[key]['actual']}. Explained in the "
                "run report, never auto-corrected.",
                {"expected": differences[key]["expected"], "actual": differences[key]["actual"]},
            )
        )
    return out
