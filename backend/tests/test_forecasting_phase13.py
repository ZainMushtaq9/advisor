"""Phase 13 pure tests: baselines, intervals, walk-forward, abstention.

No database, no network. Hand-calculated expectations throughout.
The leakage test is the important one: a walk-forward forecast must
never depend on a value dated after its origin.
"""

from decimal import Decimal

import pytest

from app.services.forecasting import METHODS
from app.services.forecasting.baselines import (
    ar1_fit,
    ar1_forecast,
    empirical_quantile,
    historical_mean,
    moving_average,
    naive_persistence,
    one_step_residuals,
    prediction_interval,
)
from app.services.forecasting.coverage import assess
from app.services.forecasting.validation import (
    calibration_error,
    evaluate_method,
    interval_coverage,
    walk_forward_folds,
)


def test_naive_persistence_is_last_value():
    assert naive_persistence([10, 12, 11]) == Decimal(11)
    # A single observation still yields a naive POINT (interval is separate).
    assert naive_persistence([7]) == Decimal(7)


def test_historical_mean_and_minimum():
    assert historical_mean([10, 12, 11, 13, 14]) == Decimal(12)
    with pytest.raises(ValueError):
        historical_mean([1, 2])


def test_moving_average_windows():
    # Last 5 of 1..10 are 6,7,8,9,10; mean = 40/5 = 8.
    assert moving_average([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5) == Decimal(8)
    with pytest.raises(ValueError):
        moving_average([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 20)


def test_one_step_residuals_never_use_future():
    assert one_step_residuals([10, 12, 11], "naive_persistence") == [
        Decimal(2),
        Decimal(-1),
    ]
    # Expanding mean: t=1 uses mean([10])=10 -> 12-10=2; t=2 uses
    # mean([10,12])=11 -> 11-11=0. Full-sample mean (11) would leak.
    assert one_step_residuals([10, 12, 11], "historical_mean") == [
        Decimal(2),
        Decimal(0),
    ]
    assert one_step_residuals([5], "naive_persistence") == []


def test_empirical_quantile_interpolation():
    assert empirical_quantile([Decimal(0), Decimal(10)], Decimal("0.5")) == Decimal(5)
    assert empirical_quantile([Decimal(4)], Decimal("0.9")) == Decimal(4)


def test_prediction_interval_from_residuals():
    residuals = [Decimal(v) for v in [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4]]
    low, high = prediction_interval(Decimal(100), residuals)
    # q10: pos 0.9 -> -5 + 0.9*(-4+5) = -4.1; q90: pos 8.1 -> 3 + 0.1 = 3.1.
    assert low == Decimal("95.9")
    assert high == Decimal("103.1")
    with pytest.raises(ValueError):
        prediction_interval(Decimal(100), [Decimal(1)] * 9)


def test_ar1_fit_on_arithmetic_series():
    series = list(range(1, 31))  # y = 1 + 1*x exactly.
    intercept, slope = ar1_fit(series)
    assert slope == Decimal(1)
    assert intercept == Decimal(1)
    assert ar1_forecast(series, steps=1) == Decimal(31)
    with pytest.raises(ValueError):
        ar1_fit(list(range(1, 10)))


def test_walk_forward_folds_are_chronological():
    folds = walk_forward_folds([1, 2, 3, 4, 5], min_train=3, horizon_steps=1, step=1)
    assert len(folds) == 2
    assert folds[0][0] == [1, 2, 3] and folds[0][2] == [4]
    assert folds[1][0] == [1, 2, 3, 4] and folds[1][2] == [5]
    origins = [train[-1] for train, _, _ in folds]
    assert origins == sorted(origins)
    with pytest.raises(ValueError):
        walk_forward_folds([1, 2], min_train=2, horizon_steps=1)


def test_evaluate_method_hand_calculated():
    result = evaluate_method([10, 12, 11, 13], "naive_persistence", min_train=2)
    assert result["n_folds"] == 2
    assert result["forecasts"] == [Decimal(12), Decimal(11)]
    assert result["realised"] == [Decimal(11), Decimal(13)]
    assert result["mae"] == Decimal("1.5")
    # RMSE = sqrt((1 + 4) / 2) = sqrt(2.5); check via square, not float.
    assert abs(result["rmse"] * result["rmse"] - Decimal("2.5")) < Decimal("0.000001")
    # Both forecasts equal their origins (persistence), so direction is
    # 0 while realised moves are non-zero: accuracy 0, not "no data".
    assert result["directional_accuracy"] == Decimal(0)


def test_no_leakage_future_value_cannot_change_forecast():
    # The 100 arrives after both origins; persistence forecasts stay 5.
    result = evaluate_method([5, 5, 5, 100], "naive_persistence", min_train=2)
    assert result["forecasts"] == [Decimal(5), Decimal(5)]


def test_interval_coverage_and_calibration():
    assert interval_coverage([(0, 10), (5, 15)], [5, 20]) == Decimal("0.5")
    assert calibration_error(Decimal("0.80"), Decimal("0.50")) == Decimal("0.30")


def test_assess_abstention_rules():
    # Zero observations: nothing, not even a point.
    zero = assess("return", "1d", 0)
    assert zero["computation_status"] == "insufficient_inputs"
    assert zero["per_method"]["naive_persistence"]["status"] == "insufficient_inputs"
    # One observation: naive point exists but interval does not -> abstained.
    one = assess("close_price", "1d", 1)
    assert one["computation_status"] == "insufficient_inputs"
    assert one["per_method"]["naive_persistence"]["status"] == "point_only_abstained"
    assert one["calibration_status"] == "not_calibrated_insufficient_history"
    # Eleven observations: naive interval minimum (11) met -> computed.
    eleven = assess("close_price", "1d", 11)
    assert eleven["computation_status"] == "computed"
    assert eleven["per_method"]["naive_persistence"]["status"] == "ready"
    # Horizon never changes the verdict: 12m from one observation is
    # exactly as unsupported as 1d.
    assert assess("close_price", "12m", 1)["computation_status"] == "insufficient_inputs"


def test_registry_minima_are_sane():
    assert METHODS["naive_persistence"][0] == 1
    assert METHODS["naive_persistence"][1] == 11
    assert METHODS["historical_mean"][0] == 5
    assert METHODS["ar1"][0] == 30
    assert METHODS["ets"][2] is False  # registered candidate, not implemented
