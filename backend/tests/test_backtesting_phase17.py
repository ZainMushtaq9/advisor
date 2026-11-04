"""Phase 17 pure tests: metrics, gating, paper simulator, bias, safety.

No database, no network. Fixtures only.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

from app.api.v1.endpoints import backtesting as backtesting_api
from app.services.backtesting import METRIC_NAMES, STRATEGIES
from app.services.backtesting.bias import CHECKS
from app.services.backtesting.metrics import (
    assess_metric,
    cagr,
    max_drawdown,
    sharpe_ratio,
    simple_returns,
    sortino_ratio,
    tail_loss,
    total_return,
    volatility,
    win_rate,
)
from app.services.backtesting.paper import (
    accept_order,
    apply_costs,
    derive_ledger,
    fill_order,
    next_eligible_price_date,
)

D = Decimal


def test_total_return_and_cagr_fixtures():
    closes = [D("100"), D("110"), D("121")]
    assert total_return(closes) == D("0.21")
    # 2 years: (1.21)^(1/2) - 1 = 0.10 exactly.
    assert cagr(closes, D("2")) == D("0.10")
    assert total_return([D("100")]) is None
    assert cagr([D("100")], D("1")) is None
    assert cagr(closes, D("0")) is None


def test_simple_returns_and_win_rate():
    closes = [D("100"), D("110"), D("99")]
    returns = simple_returns(closes)
    assert returns[0] == D("0.1")
    assert win_rate(returns) == D("0.5")
    assert simple_returns([D("100")]) == []
    assert win_rate([]) is None


def test_volatility_sharpe_sortino_need_series_and_risk_free():
    returns = [D("0.01")] * 30
    assert volatility(returns) == D("0")
    # Zero stdev -> Sharpe undefined, never infinite.
    assert sharpe_ratio(returns, D("0.0002")) is None
    assert sortino_ratio(returns, D("0.0002")) is None
    # No risk-free rate -> never computed against an invented one.
    assert sharpe_ratio([D("0.02"), D("-0.01")] * 15, None) is None
    assert sortino_ratio([D("0.02"), D("-0.01")] * 15, None) is None


def test_max_drawdown_and_tail_loss():
    closes = [D("100"), D("120"), D("90"), D("108")]
    assert max_drawdown(closes) == D("0.25")
    assert max_drawdown([D("100")]) is None
    returns = [D("-0.05"), D("0.02"), D("-0.03")] + [D("0.01")] * 17
    assert tail_loss(returns) == D("-0.05")
    assert tail_loss([]) is None


def test_assess_metric_gating_single_observation():
    # Production shape: one close, zero returns, one snapshot.
    for metric in METRIC_NAMES:
        value, status, reason = assess_metric(
            metric,
            closes=[D("197.24")],
            returns=[],
            snapshots=1,
            benchmark_return=None,
            years=D("0"),
            daily_risk_free=None,
        )
        assert value is None
        if metric == "benchmark_relative_return":
            assert status == "not_applicable"
        else:
            assert status == "insufficient_inputs"
        assert reason


def test_assess_metric_computes_when_minima_met():
    closes = [D("100")] + [D("100") * (D("1.01") ** i) for i in range(1, 31)]
    returns = simple_returns(closes)
    assert len(returns) == 30
    value, status, _ = assess_metric("total_return", closes, returns, 31, None, D("1"), None)
    assert status == "computed" and value is not None
    value, status, _ = assess_metric("volatility", closes, returns, 31, None, D("1"), None)
    assert status == "computed"


def test_next_eligible_price_never_looks_ahead():
    observed = [date(2026, 11, 3)]
    # Signal at the close of the only price date: no later price.
    assert next_eligible_price_date(observed, date(2026, 11, 3)) is None
    # Signal before the price date: the next close is eligible.
    assert next_eligible_price_date(observed, date(2026, 11, 2)) == date(2026, 11, 3)
    # A future value cannot change a past fill decision: the
    # eligible date depends only on dates strictly after signal.
    assert next_eligible_price_date(
        [date(2026, 11, 3), date(2026, 11, 10)], date(2026, 11, 3)
    ) == date(2026, 11, 10)


def test_order_lifecycle_accept_fill_reject():
    assert accept_order(True, D("197.24"))[0] == "accepted"
    assert accept_order(False, D("197.24"))[0] == "rejected"
    assert accept_order(True, None)[0] == "rejected"
    assert accept_order(True, D("0"))[0] == "rejected"
    # No next eligible price -> stays accepted, never filled.
    status, _, fill_date, _ = fill_order("accepted", None, D("200"))
    assert status == "accepted" and fill_date is None
    status, _, fill_date, fill_price = fill_order("accepted", date(2026, 11, 10), D("200"))
    assert status == "filled" and fill_date == date(2026, 11, 10)
    assert fill_price == D("200")
    # Non-accepted orders never fill.
    assert fill_order("proposed", date(2026, 11, 10), D("200"))[0] == "proposed"


def test_ledger_reconciles_exactly():
    entries = derive_ledger(
        "test_portfolio",
        D("1000000"),
        [
            {"ticker": "HUBC", "units": D("1689"), "price": D("197.24")},
            {"ticker": "OGDC", "units": D("1097"), "price": D("303.63")},
        ],
        date(2026, 11, 3),
    )
    positions = [e for e in entries if e["entry_type"] == "opening_position"]
    cash = [e for e in entries if e["entry_type"] == "opening_cash"][0]
    total = [e for e in entries if e["entry_type"] == "valuation_snapshot"][0]
    assert positions[0]["value"] == D("1689") * D("197.24")
    assert positions[1]["value"] == D("1097") * D("303.63")
    assert cash["value"] + sum(p["value"] for p in positions) == D("1000000")
    assert total["value"] == D("1000000")


def test_costs_need_validated_rates():
    assert apply_costs(D("1000000"), None, None, None) is None
    assert apply_costs(D("1000000"), D("10"), D("15"), D("5")) == D("3000")


def test_bias_checks_disclose_and_do_not_hide():
    result, _ = CHECKS["selection"]({"covered_companies": 3, "universe_companies": 470})
    assert result == "bias_disclosed"
    result, _ = CHECKS["cost_sensitivity"]({"production_trades": 0})
    assert result == "not_applicable"
    result, _ = CHECKS["missing_data"]({"missing_tickers": ["AGLNCPS"]})
    assert result == "bias_disclosed"
    result, _ = CHECKS["point_in_time"](
        {
            "inputs": [{"after_decision_date": False}],
            "handled_exceptions": ["NML publication NULL; gated out"],
        }
    )
    assert result == "no_bias_detected"


def test_strategy_registry_covers_phase16_portfolios():
    assert set(STRATEGIES) == {
        "equal_weight_statements_3",
        "rule_screen_pass_balanced",
        "rule_screen_pass_conservative",
        "buy_and_hold_hubc",
        "buy_and_hold_ogdc",
    }
    for spec in STRATEGIES.values():
        assert spec["version"] == "backtest-v1"
        assert spec["rule_reference"]


def test_no_execution_path_and_get_only_endpoints():
    root = Path(__file__).resolve().parents[1] / "app"
    forbidden = (
        "place_order",
        "execute_order",
        "submit_order",
        "execute_trade",
        "place_trade",
    )
    hits = []
    for path in root.rglob("*.py"):
        if "test" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                hits.append(f"{path}:{token}")
    assert hits == []
    for route in backtesting_api.router.routes:
        methods = getattr(route, "methods", set()) or set()
        assert methods <= {"GET"}, f"Non-GET route: {route.path} {methods}"
