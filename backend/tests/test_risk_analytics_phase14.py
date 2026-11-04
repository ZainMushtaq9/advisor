"""Phase 14 risk formula tests — pure, no DB, no network.

Hand-calculated cases only. Every gating rule is tested: a series
shorter than the minimum returns None, never a number.
"""

from decimal import Decimal

import pytest

from app.services.risk_analytics import (
    CONTROLS_V1,
    METRIC_DEFINITIONS,
    SENSITIVITY_ROWS,
    SERIES_METRICS,
    STRESS_SCENARIOS,
)
from app.services.risk_analytics.formulas import (
    beta,
    correlation,
    downside_deviation,
    es95_hist,
    gap_pct,
    hhi,
    log_returns,
    max_drawdown,
    portfolio_shock_impact,
    top_n_share,
    var95_hist,
    volatility,
    volume_tier,
)

D = Decimal


def test_log_returns_two_closes():
    assert len(log_returns([D(100), D(110)])) == 1
    assert log_returns([D(100)]) == []


def test_volatility_gating_and_constant_series():
    assert volatility([D("0.01")] * 29) is None
    # 30 identical returns -> stdev 0 -> volatility 0.
    assert volatility([D("0.01")] * 30) == D(0)


def _varying_series():
    # 30 varying returns: 0.01, 0.02, ..., 0.30.
    return [D(i) / D(100) for i in range(1, 31)]


def test_beta_identical_series_is_one():
    series = _varying_series()
    assert beta(series, series) == D(1)
    assert beta(series, [s * 2 for s in series]) == D("0.5")
    assert beta(series[:29], series[:29]) is None


def test_correlation_identical_series_is_one():
    series = _varying_series()
    # Float sqrt rounding keeps this within 1e-9 of 1, not exactly 1.
    assert abs(correlation(series, series) - D(1)) < D("0.000000001")
    assert correlation(series[:29], series[:29]) is None


def test_beta_correlation_undefined_on_constant_series():
    # Zero variance -> undefined, not zero: the guard must hold.
    assert beta([D("0.02")] * 30, [D("0.02")] * 30) is None
    assert correlation([D("0.03")] * 30, [D("0.03")] * 30) is None


def test_max_drawdown_hand_calculated():
    # Peak 120, trough 90 -> (90/120 - 1) * 100 = -25.
    assert max_drawdown([D(100), D(120), D(90), D(100)]) == D(-25)
    assert max_drawdown([D(100)]) is None


def test_downside_deviation_gating_and_all_positive():
    assert downside_deviation([D("0.01")] * 29) is None
    assert downside_deviation([D("0.01")] * 30) == D(0)


def test_var_es_gating_and_constant_tail():
    assert var95_hist([D("-0.01")] * 250) is None
    assert es95_hist([D("-0.01")] * 250) is None
    assert var95_hist([D("-0.01")] * 251) == D("-1")
    assert es95_hist([D("-0.01")] * 251) == D("-1")


def test_gap_pct():
    assert gap_pct(D(110), D(100)) == D(10)
    assert gap_pct(D(110), None) is None
    assert gap_pct(None, D(100)) is None


def test_volume_tier_boundaries():
    assert volume_tier(1_000_000, D("54631.5")) == "HIGH"
    assert volume_tier(60000, D("54631.5")) == "MEDIUM"
    assert volume_tier(1000, D("54631.5")) == "LOW"


def test_top_n_share_hubc_categories():
    pcts = [D("38.27"), D("20.36"), D("10.82"), D("5.95")]
    assert top_n_share(pcts, 1) == D("38.27")
    assert top_n_share(pcts, 3) == D("69.45")


def test_hhi_two_equal_shares():
    assert hhi([D(50), D(50)]) == D(5000)


def test_portfolio_shock_impacts():
    w = [D(100) / D(3)] * 3
    assert portfolio_shock_impact(w, [D(-10)] * 3) == D(-10)
    impact = portfolio_shock_impact(w, [D(-20), D(0), D(0)])
    assert abs(impact - D("-6.666667")) < D("0.000001")


def test_registries_complete():
    assert len(METRIC_DEFINITIONS) == 22
    assert len(SERIES_METRICS) == 8
    assert len(SENSITIVITY_ROWS) == 6
    assert len(CONTROLS_V1) == 5
    assert len(STRESS_SCENARIOS) == 5
    keys = [m[0] for m in METRIC_DEFINITIONS]
    assert len(set(keys)) == len(keys)
    for key, category, formula, min_obs, window, unit, scope in METRIC_DEFINITIONS:
        assert min_obs >= 1
        assert scope in ("security", "sector", "market")
        assert category in ("market", "liquidity", "concentration", "sensitivity", "model")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
