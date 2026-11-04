"""Phase 13 baseline models: pure Decimal, no database, no network.

Every function takes an explicit chronological series (oldest first)
and refuses — by returning None or raising ValueError — when the
series is shorter than the method's minimum. Nothing here fills,
interpolates or invents a missing observation: a series of length 1
has no mean worth the name, no moving average and no AR(1) slope,
and these functions say so instead of computing one.

Hand-calculated expectations live in backend/tests/test_forecasting_phase13.py.
"""

from __future__ import annotations

from decimal import Decimal

from . import METHODS


def _require(series: list, method: str) -> None:
    point_min, _, _ = METHODS[method]
    if len(series) < point_min:
        raise ValueError(f"{method} needs at least {point_min} observations, got {len(series)}")


def naive_persistence(series: list) -> Decimal:
    """Random-walk baseline: the next value equals the last value."""
    _require(series, "naive_persistence")
    return Decimal(series[-1])


def historical_mean(series: list) -> Decimal:
    """Mean of the whole series as the forecast for every horizon."""
    _require(series, "historical_mean")
    total = sum((Decimal(v) for v in series), Decimal(0))
    return total / Decimal(len(series))


def moving_average(series: list, window: int) -> Decimal:
    """Mean of the last ``window`` observations."""
    method = f"moving_average_{window}"
    if method not in METHODS:
        raise ValueError(f"unknown moving-average window: {window}")
    _require(series, method)
    window_values = series[-window:]
    total = sum((Decimal(v) for v in window_values), Decimal(0))
    return total / Decimal(len(window_values))


def one_step_residuals(series: list, method: str) -> list:
    """In-sample one-step errors of a baseline, oldest first.

    For naive_persistence: error[t] = value[t] - value[t-1].
    For historical_mean: error[t] = value[t] - mean(value[..t-1]),
    i.e. the expanding mean available BEFORE t — never the full-sample
    mean, which would leak t's own value into its "forecast".
    Returns [] when fewer than 2 observations exist.
    """
    values = [Decimal(v) for v in series]
    if len(values) < 2:
        return []
    if method == "naive_persistence":
        return [values[i] - values[i - 1] for i in range(1, len(values))]
    if method == "historical_mean":
        out = []
        for i in range(1, len(values)):
            mean_prior = sum(values[:i], Decimal(0)) / Decimal(i)
            out.append(values[i] - mean_prior)
        return out
    raise ValueError(f"residuals not defined for method: {method}")


def empirical_quantile(sorted_values: list, q: Decimal) -> Decimal:
    """Linear-interpolation quantile on an already-sorted list."""
    if not sorted_values:
        raise ValueError("quantile of an empty list is undefined")
    if len(sorted_values) == 1:
        return Decimal(sorted_values[0])
    pos = q * Decimal(len(sorted_values) - 1)
    lower = int(pos)
    upper = min(lower + 1, len(sorted_values) - 1)
    frac = pos - Decimal(lower)
    low = Decimal(sorted_values[lower])
    high = Decimal(sorted_values[upper])
    return low + (high - low) * frac


def prediction_interval(
    point: Decimal, residuals: list, lower_q: str = "0.10", upper_q: str = "0.90"
) -> tuple:
    """80% empirical interval: point + residual quantiles.

    Needs at least 10 residuals (see METHODS interval minima); fewer
    makes the interval a guess. The interval is symmetric only if
    the residuals are — no normality is assumed.
    """
    if len(residuals) < 10:
        raise ValueError(f"prediction interval needs at least 10 residuals, got {len(residuals)}")
    ordered = sorted(Decimal(r) for r in residuals)
    low = Decimal(point) + empirical_quantile(ordered, Decimal(lower_q))
    high = Decimal(point) + empirical_quantile(ordered, Decimal(upper_q))
    return (low, high)


def ar1_fit(series: list) -> tuple:
    """OLS AR(1): value[t] = intercept + slope * value[t-1].

    Returns (intercept, slope) as Decimals. Needs 30 observations
    (METHODS minimum): a slope fitted on fewer points is noise
    presented as signal, so the function refuses instead.
    """
    _require(series, "ar1")
    values = [Decimal(v) for v in series]
    xs = values[:-1]
    ys = values[1:]
    n = Decimal(len(xs))
    mean_x = sum(xs, Decimal(0)) / n
    mean_y = sum(ys, Decimal(0)) / n
    sxx = sum((x - mean_x) * (x - mean_x) for x in xs)
    if sxx == 0:
        raise ValueError("ar1 undefined: regressor has zero variance")
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    return (intercept, slope)


def ar1_forecast(series: list, steps: int = 1) -> Decimal:
    """Iterated AR(1) forecast ``steps`` ahead from the last value."""
    intercept, slope = ar1_fit(series)
    value = Decimal(series[-1])
    for _ in range(steps):
        value = intercept + slope * value
    return value
