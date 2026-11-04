"""Phase 13 walk-forward validation: chronological only, never shuffled.

A fold trains on observations strictly before its forecast origin
and evaluates on observations strictly after it. Any function here
that received a shuffled series would still produce chronological
folds — but the runner never shuffles: series are read ordered by
date, and the fold builder asserts origins are increasing.

Metrics: MAE, RMSE, directional accuracy (forecast direction vs
realised direction, both measured against the origin value),
interval coverage (fraction of realised values inside the forecast
interval, PICP), and a simple calibration error (mean absolute gap
between nominal and empirical coverage across the intervals
evaluated — with one interval level, the 80% level, this reduces to
|0.80 - PICP|; it is reported as such, never dressed up as a curve).
"""

from __future__ import annotations

from decimal import Decimal

from .baselines import historical_mean, naive_persistence


def walk_forward_folds(series: list, min_train: int, horizon_steps: int = 1, step: int = 1) -> list:
    """Expanding-window folds: (train_series, origin_value, test_values).

    ``series`` is oldest-first. Fold k trains on series[:origin] with
    origin >= min_train and evaluates on the next ``horizon_steps``
    values. Origins increase by ``step``. Raises ValueError when the
    series cannot yield even one fold — an empty fold list is never
    silently returned as "no evidence".
    """
    if min_train < 1:
        raise ValueError("min_train must be at least 1")
    if horizon_steps < 1:
        raise ValueError("horizon_steps must be at least 1")
    folds = []
    origin = min_train
    while origin + horizon_steps <= len(series):
        folds.append(
            (
                list(series[:origin]),
                series[origin - 1],
                list(series[origin : origin + horizon_steps]),
            )
        )
        origin += step
    if not folds:
        raise ValueError(
            f"series of length {len(series)} yields no walk-forward fold "
            f"(min_train={min_train}, horizon_steps={horizon_steps})"
        )
    return folds


def _forecast(train: list, method: str) -> Decimal:
    if method == "naive_persistence":
        return naive_persistence(train)
    if method == "historical_mean":
        return historical_mean(train)
    raise ValueError(f"walk-forward not defined for method: {method}")


def evaluate_method(
    series: list, method: str, min_train: int, horizon_steps: int = 1, step: int = 1
) -> dict:
    """Walk-forward metrics for one method on one series.

    Returns MAE, RMSE, directional_accuracy (None when no fold has a
    non-zero realised move), n_folds, and the per-fold forecasts and
    realised values so an auditor can recompute every metric.
    """
    values = [Decimal(v) for v in series]
    folds = walk_forward_folds(values, min_train, horizon_steps, step)
    forecasts = []
    realised = []
    origins = []
    for train, origin_value, test_values in folds:
        forecasts.append(_forecast(train, method))
        realised.append(test_values[0])
        origins.append(origin_value)
    errors = [f - r for f, r in zip(forecasts, realised)]
    abs_errors = [abs(e) for e in errors]
    mae = sum(abs_errors, Decimal(0)) / Decimal(len(abs_errors))
    rmse = (sum(e * e for e in errors) / Decimal(len(errors))).sqrt()
    direction_hits = 0
    direction_total = 0
    for forecast, real, origin_value in zip(forecasts, realised, origins):
        forecast_dir = (forecast > origin_value) - (forecast < origin_value)
        real_dir = (real > origin_value) - (real < origin_value)
        if real_dir != 0:
            direction_total += 1
            if forecast_dir == real_dir:
                direction_hits += 1
    directional_accuracy = (
        Decimal(direction_hits) / Decimal(direction_total) if direction_total else None
    )
    return {
        "method": method,
        "n_folds": len(folds),
        "mae": mae,
        "rmse": rmse,
        "directional_accuracy": directional_accuracy,
        "forecasts": forecasts,
        "realised": realised,
    }


def interval_coverage(intervals: list, realised: list) -> Decimal:
    """PICP: fraction of realised values inside their intervals."""
    if not intervals or len(intervals) != len(realised):
        raise ValueError("intervals and realised must be non-empty and equal-length")
    hits = sum(
        1
        for (low, high), real in zip(intervals, realised)
        if Decimal(low) <= Decimal(real) <= Decimal(high)
    )
    return Decimal(hits) / Decimal(len(realised))


def calibration_error(nominal_coverage: Decimal, empirical_coverage: Decimal) -> Decimal:
    """|nominal - empirical| coverage gap for a single interval level."""
    return abs(Decimal(nominal_coverage) - Decimal(empirical_coverage))
