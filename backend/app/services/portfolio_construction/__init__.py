"""Phase 16 portfolio construction registries and eligibility rules.

Risk profiles (input schema, not advice): each profile is a set
of constraints, not a suitability claim. A profile never claims
the portfolio suits any particular user — suitability is a
user-side judgement the system does not make.

- conservative: 10% cash floor, 50% single-name cap, 50% sector cap.
- balanced: 0% cash floor, 50% single-name cap, 100% sector cap.
- growth: 0% cash floor, 100% single-name cap, 100% sector cap.
  Growth is defined-not-run in this run: on the 2-name
  rule-based set it collapses to balanced, so constructing it
  would add a duplicate portfolio with no information. The CLI
  --profile flag can still construct it on request.

Eligibility statuses (validated before any units or value):
- ELIGIBLE: security row exists AND a positive price exists on
  the price date.
- NOT_IN_UNIVERSE: no security row for the ticker.
- IN_UNIVERSE_NO_QUOTE: security row exists, no price row on the
  price date.
- INVALID_QUOTE: a price row exists but is null, zero, or
  negative. Never a position.
"""

from __future__ import annotations

from decimal import Decimal

PRICE_DATE = "2026-11-03"
DECISION_DATE = "2026-11-04"
SIMULATION_CAPITAL = Decimal("1000000")
BASE_CURRENCY = "PKR"

# Risk-profile constraint registry: profile -> constraints.
RISK_PROFILES: dict[str, dict] = {
    "conservative": {
        "cash_floor": Decimal("0.10"),
        "max_single_weight": Decimal("0.50"),
        "max_sector_weight": Decimal("0.50"),
        "description": (
            "10% cash floor, 50% single-name cap, 50% sector cap. "
            "A constraint set, not a suitability claim."
        ),
    },
    "balanced": {
        "cash_floor": Decimal("0.00"),
        "max_single_weight": Decimal("0.50"),
        "max_sector_weight": Decimal("1.00"),
        "description": (
            "No cash floor, 50% single-name cap, no sector cap. "
            "A constraint set, not a suitability claim."
        ),
    },
    "growth": {
        "cash_floor": Decimal("0.00"),
        "max_single_weight": Decimal("1.00"),
        "max_sector_weight": Decimal("1.00"),
        "description": (
            "No cash floor, no weight caps. Defined-not-run in "
            "this run: on the 2-name rule-based set it collapses "
            "to balanced, so constructing it adds a duplicate."
        ),
    },
}

# Method registry: method -> constructability in this run.
METHODS: dict[str, dict] = {
    "equal_weight_baseline": {
        "constructible": True,
        "description": (
            "Equal weight over the eligible set, whole shares, "
            "residual cash. The simple baseline every other "
            "method is compared against."
        ),
    },
    "rule_based_screen_pass": {
        "constructible": True,
        "description": (
            "Equal weight over Phase 15 SCREEN_PASS securities "
            "only, under the chosen risk profile's constraints. "
            "SCREEN_FAIL and SCREEN_NOT_RUNNABLE names are "
            "excluded with reasons, never silently dropped."
        ),
    },
    "mean_variance": {
        "constructible": False,
        "description": (
            "Mean-variance optimization. NOT constructed: it "
            "requires validated expected returns and a "
            "covariance matrix, and neither exists (Phase 13 "
            "computed 0 forecasts; 1 price date gives 0 return "
            "observations). See the mean_variance_gate."
        ),
    },
}

# Assumptions block, shown separately per the brief: expected
# returns, historical returns, and forecasts are three distinct
# absences, never merged into one invented return figure.
ASSUMPTIONS_TEMPLATE: dict = {
    "expected_returns": {
        "value": None,
        "reason": (
            "No validated expected-return source exists. Phase 13 "
            "computed 0 forecasts; no expected return is assumed."
        ),
    },
    "historical_returns": {
        "value": None,
        "reason": (
            "1 price date (2026-11-03) gives 0 return observations; "
            "no historical return can be computed."
        ),
    },
    "forecasts": {
        "value": None,
        "reason": (
            "Phase 13 live forecasting abstained on all 120 "
            "assessments (no series meets any method's interval "
            "minimum); point-only values were never stored as "
            "forecasts and contribute nothing here."
        ),
    },
    "transaction_costs": {
        "value": None,
        "reason": (
            "No defensible transaction-cost assumption is stored: "
            "no broker, fee schedule, or spread source is in "
            "scope, so costs are excluded rather than invented."
        ),
    },
    "simulation_note": (
        "Hypothetical simulation capital (PKR 1,000,000), not real "
        "funds. No real trade, order, or custody concept exists."
    ),
}


def validate_eligibility(
    security_exists: bool,
    price: Decimal | None,
) -> tuple[str, str]:
    """Eligibility status for one ticker on the price date.

    Pure function so the four-way distinction is unit-testable
    without a database. The caller passes whether a security row
    exists and the price value (None when no price row exists).
    """
    if not security_exists:
        return "NOT_IN_UNIVERSE", "No security row for this ticker in the central universe."
    if price is None:
        return "IN_UNIVERSE_NO_QUOTE", "Security exists but has no price row on the price date."
    if price <= 0:
        return "INVALID_QUOTE", f"Price row exists but is not positive ({price}); never a position."
    return "ELIGIBLE", "Security exists with a positive price on the price date."
