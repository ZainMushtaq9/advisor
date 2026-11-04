"""Phase 13 forecasting registries.

Targets, horizons and baseline-method data requirements. The minima
are design decisions, documented here so an assessment row can cite
the exact shortfall:

- A POINT estimate needs ``point_min`` observations of the target's
  own series. naive_persistence needs 1 (the last value IS the
  forecast); historical_mean and moving_average_5 need 5 (fewer
  makes the "average" a single observation in disguise);
  moving_average_20 needs 20; ar1 needs 30 (an OLS slope on fewer
  points is noise presented as signal).
- An INTERVAL needs ``interval_min`` = point_min + 10: ten in-sample
  one-step residuals from which an empirical interval can be built.
  Fewer residuals make the interval a guess, and the Phase 3
  ``forecasts`` table rightly refuses a row without one.
- ets and arima are REGISTERED candidates, not implemented methods:
  no statsmodels dependency is added for a pipeline that owns one
  price date, and neither may run until a validated statistical fit
  plus residual history exists. Their method_requirements say so.
- Tree/ML models are likewise registered-but-gated: the brief allows
  them "only where out-of-sample evidence shows incremental value",
  and no out-of-sample evidence can exist on one observation.

Horizons are the brief's six: 1d, 1w, 1m, 3m, 6m, 12m. A horizon
does not change the minima — a 12m forecast from one observation
is exactly as unsupported as a 1d one — so assessments are
identical across horizons in this run, and the assessment rows say
so rather than pretending longer horizons are "more" computable.
"""

from __future__ import annotations

HORIZONS = ("1d", "1w", "1m", "3m", "6m", "12m")

# target_key -> (target_type, scope, series description)
TARGETS = {
    "close_price": ("price", "company", "daily close_price series"),
    "return": ("return", "company", "daily simple-return series derived from closes"),
    "direction": ("direction", "company", "daily up/down series derived from closes"),
    "volatility": ("volatility", "company", "daily realised-volatility series derived from closes"),
    "volume": ("volume", "company", "daily volume series"),
    "earnings": ("earnings", "company", "per-period earnings series from statements"),
    "macro_policy_rate": ("macro", "macro", "SBP policy-rate observation series"),
    "macro_cpi_yoy": ("macro", "macro", "CPI year-on-year observation series"),
}

# method -> (point_min_observations, interval_min_observations, implemented)
METHODS = {
    "naive_persistence": (1, 11, True),
    "historical_mean": (5, 15, True),
    "moving_average_5": (5, 15, True),
    "moving_average_20": (20, 30, True),
    "ar1": (30, 40, True),
    "ets": (30, 40, False),
    "arima": (50, 60, False),
    "ml_tree": (100, 110, False),
}


def method_requirements() -> dict:
    """JSON-able method requirements for the target registry rows."""
    return {
        name: {
            "point_min_observations": point_min,
            "interval_min_observations": interval_min,
            "implemented": implemented,
            "not_implemented_reason": (
                None
                if implemented
                else "Candidate method only: no validated statistical fit and "
                "no residual history exists on the current data; never run "
                "on a series shorter than its minimum."
            ),
        }
        for name, (point_min, interval_min, implemented) in METHODS.items()
    }


def target_min_observations() -> int:
    """Smallest point_min across implemented methods: naive needs 1."""
    return min(point_min for point_min, _, implemented in METHODS.values() if implemented)


__all__ = ["HORIZONS", "TARGETS", "METHODS", "method_requirements", "target_min_observations"]
