"""Phase 16 portfolio construction tests (pure: no DB, no network).

Covers: whole-share reconciliation (holdings + cash == capital
exactly), floor rounding never over-funding, the four-way
eligibility distinction (including zero/negative INVALID_QUOTE),
mean-variance gating on the real pipeline state (0 forecasts, 0
returns), sector weights summing to 1 over invested value, the
risk-profile registry, and the no-execution-path scan (the same
guarantee Phase 15 proved: no broker/order concept anywhere in
application source, and the portfolios endpoint is GET-only).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.services.portfolio_construction import RISK_PROFILES, validate_eligibility
from app.services.portfolio_construction.formulas import (
    actual_weights,
    build_equal_weight_positions,
    check_caps,
    mean_variance_gate,
    sector_allocations,
    whole_share_units,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = BACKEND_ROOT / "app"
SCRIPTS_ROOT = BACKEND_ROOT.parent / "scripts"

# Code identifiers only (the Phase 15 scan's token set): prose mentions
# of "broker" in docstrings are not execution paths and are not matched.
EXECUTION_IDENTIFIERS = (
    "place_order",
    "execute_order",
    "submit_order",
    "execute_trade",
    "place_trade",
    "class Broker",
    "BrokerClient",
    "broker_client",
    "broker_api",
    "/orders",
    "orders_router",
)


def test_whole_share_units_never_overfund() -> None:
    assert whole_share_units(Decimal("500000"), Decimal("197.24")) == 2534
    assert Decimal("2534") * Decimal("197.24") <= Decimal("500000")
    assert Decimal("2535") * Decimal("197.24") > Decimal("500000")


def test_whole_share_units_reject_nonpositive_price() -> None:
    for bad in (Decimal("0"), Decimal("-5")):
        try:
            whole_share_units(Decimal("1000"), bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"price {bad} should have raised")


def test_equal_weight_reconciles_exactly() -> None:
    prices = [
        ("HUBC", Decimal("197.24"), "POWER GENERATION & DISTRIBUTION"),
        ("NML", Decimal("123.61"), "TEXTILE COMPOSITE"),
        ("OGDC", Decimal("303.63"), "OIL & GAS EXPLORATION COMPANIES"),
    ]
    capital = Decimal("1000000")
    positions, cash = build_equal_weight_positions(prices, capital, Decimal("0"))
    actual_weights(positions, capital)
    invested = sum((p["value"] for p in positions), Decimal("0"))
    assert invested + cash == capital
    # Hand-checked values (floor units on 2026-11-03 closes).
    by_ticker = {p["ticker"]: p for p in positions}
    assert by_ticker["HUBC"]["units"] == 1689
    assert by_ticker["HUBC"]["value"] == Decimal("333138.36")
    assert by_ticker["NML"]["units"] == 2696
    assert by_ticker["NML"]["value"] == Decimal("333252.56")
    assert by_ticker["OGDC"]["units"] == 1097
    assert by_ticker["OGDC"]["value"] == Decimal("333082.11")
    assert cash == Decimal("526.97")
    assert all(p["value"] <= capital / 3 for p in positions)


def test_equal_weight_with_cash_floor() -> None:
    prices = [("HUBC", Decimal("197.24"), "POWER"), ("OGDC", Decimal("303.63"), "OIL")]
    capital = Decimal("1000000")
    positions, cash = build_equal_weight_positions(prices, capital, Decimal("0.10"))
    invested = sum((p["value"] for p in positions), Decimal("0"))
    assert invested + cash == capital
    assert cash >= Decimal("100000")  # floor respected (excess is rounding only)
    by_ticker = {p["ticker"]: p for p in positions}
    assert by_ticker["HUBC"]["units"] == 2281
    assert by_ticker["OGDC"]["units"] == 1482
    assert cash == Decimal("100115.90")


def test_sector_weights_sum_to_one_over_invested() -> None:
    prices = [
        ("HUBC", Decimal("197.24"), "POWER"),
        ("NML", Decimal("123.61"), "TEXTILE"),
        ("OGDC", Decimal("303.63"), "OIL"),
    ]
    positions, cash = build_equal_weight_positions(prices, Decimal("1000000"), Decimal("0"))
    rows = sector_allocations(positions, Decimal("1000000"))
    assert sum((r["invested_weight"] for r in rows), Decimal("0")) == 1
    invested = sum((p["value"] for p in positions), Decimal("0"))
    assert sum((r["invested_value"] for r in rows), Decimal("0")) == invested
    assert sum((r["capital_weight"] for r in rows), Decimal("0")) == invested / Decimal("1000000")


def test_caps_pass_for_baseline_and_rule_portfolios() -> None:
    prices = [
        ("HUBC", Decimal("197.24"), "POWER"),
        ("NML", Decimal("123.61"), "TEXTILE"),
        ("OGDC", Decimal("303.63"), "OIL"),
    ]
    capital = Decimal("1000000")
    positions, cash = build_equal_weight_positions(prices, capital, Decimal("0"))
    checks = check_caps(positions, capital, Decimal("0.50"), Decimal("1.00"), Decimal("0"), cash)
    assert checks["max_single_weight"]["pass"] is True
    assert checks["max_sector_weight"]["pass"] is True
    assert checks["cash_floor"]["pass"] is True
    # A cap that must fail: 30% single-name cap vs 33.3% targets.
    failing = check_caps(positions, capital, Decimal("0.30"), Decimal("1.00"), Decimal("0"), cash)
    assert failing["max_single_weight"]["pass"] is False


def test_eligibility_four_way_distinction() -> None:
    assert validate_eligibility(False, None)[0] == "NOT_IN_UNIVERSE"
    assert validate_eligibility(True, None)[0] == "IN_UNIVERSE_NO_QUOTE"
    assert validate_eligibility(True, Decimal("0"))[0] == "INVALID_QUOTE"
    assert validate_eligibility(True, Decimal("-1"))[0] == "INVALID_QUOTE"
    assert validate_eligibility(True, Decimal("197.24"))[0] == "ELIGIBLE"
    # NOT_IN_UNIVERSE and IN_UNIVERSE_NO_QUOTE are distinct strings,
    # so a caller can never confuse a missing security with a
    # missing quote.
    assert validate_eligibility(False, None)[0] != validate_eligibility(True, None)[0]


def test_mean_variance_gate_blocks_on_pipeline_state() -> None:
    status, reasons = mean_variance_gate(computed_forecasts=0, return_observations=0)
    assert status == "NOT_CALCULABLE"
    assert len(reasons) == 2
    assert any("expected returns" in r for r in reasons)
    assert any("covariance" in r for r in reasons)
    # Gate opens only when both inputs exist (hypothetical state).
    assert mean_variance_gate(5, 60)[0] == "CONSTRUCTIBLE"


def test_risk_profile_registry() -> None:
    assert RISK_PROFILES["conservative"]["cash_floor"] == Decimal("0.10")
    assert RISK_PROFILES["conservative"]["max_single_weight"] == Decimal("0.50")
    assert RISK_PROFILES["balanced"]["cash_floor"] == Decimal("0.00")
    assert RISK_PROFILES["balanced"]["max_single_weight"] == Decimal("0.50")
    assert RISK_PROFILES["growth"]["max_single_weight"] == Decimal("1.00")
    assert set(RISK_PROFILES) == {"conservative", "balanced", "growth"}


def test_no_execution_path_in_application_source() -> None:
    """No broker/order/execution concept anywhere in app or scripts."""
    hits: list[str] = []
    for root in (APP_ROOT, SCRIPTS_ROOT):
        for path in root.rglob("*.py"):
            if "test" in path.name:
                continue
            # Phase 29 allowlist: the acceptance auditor holds these
            # identifiers as SEARCH patterns for its own scan; it
            # contains no execution code and never calls them.
            if "acceptance" in path.parts and path.name == "audits.py":
                continue
            text = path.read_text(encoding="utf-8")
            for identifier in EXECUTION_IDENTIFIERS:
                if identifier in text:
                    hits.append(f"{path}:{identifier}")
    assert hits == [], f"execution identifiers found: {hits}"


def test_portfolios_endpoint_is_get_only() -> None:
    endpoint = APP_ROOT / "api" / "v1" / "endpoints" / "portfolios.py"
    text = endpoint.read_text(encoding="utf-8")
    assert "@router.get" in text
    assert "@router.post" not in text
    assert "@router.put" not in text
    assert "@router.delete" not in text
    assert "@router.patch" not in text
