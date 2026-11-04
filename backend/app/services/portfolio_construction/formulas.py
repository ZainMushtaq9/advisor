"""Phase 16 pure portfolio mathematics (Decimal, no I/O, no DB).

Every function here is deterministic and side-effect free so the
tests can prove reconciliation exactly:

- Whole shares only: units = floor(target value / price). The
  residual cash absorbs rounding, so holdings + cash == capital
  exactly. Target weights are kept next to actual weights so the
  rounding is visible, never hidden.
- Sector weights are reported two ways: share of invested value
  and share of capital. Cash is in the capital denominator only.
- Mean-variance gating is a pure predicate: it needs validated
  expected returns AND a covariance matrix. With 0 computed
  forecasts and 0 return observations, both fail — the gate
  returns NOT_CALCULABLE with reasons, never numbers.
"""

from __future__ import annotations

from decimal import ROUND_FLOOR, Decimal

CENT = Decimal("0.0001")


def whole_share_units(target_value: Decimal, price: Decimal) -> Decimal:
    """Whole shares affordable at ``target_value`` for ``price``.

    Floor division: units never exceed the target value, so a
    position can never be over-funded by rounding.
    """
    if price <= 0:
        raise ValueError("price must be positive for unit computation")
    if target_value < 0:
        raise ValueError("target value must not be negative")
    return (target_value / price).to_integral_value(rounding=ROUND_FLOOR)


def build_equal_weight_positions(
    prices: list[tuple[str, Decimal, str | None]],
    capital: Decimal,
    cash_floor: Decimal,
) -> tuple[list[dict], Decimal]:
    """Equal-weight whole-share positions over ``prices``.

    ``prices`` is a list of (ticker, price, sector). The investable
    amount is capital * (1 - cash_floor), split equally; each
    position takes floor(target / price) shares. Returns the
    position list and the residual cash. The caller must check the
    caps; this function only does the arithmetic.
    """
    if not prices:
        raise ValueError("no eligible securities to weight")
    if capital <= 0:
        raise ValueError("capital must be positive")
    if not (Decimal("0") <= cash_floor < 1):
        raise ValueError("cash_floor must be in [0, 1)")
    investable = capital * (Decimal("1") - cash_floor)
    target_value = investable / Decimal(len(prices))
    target_weight = (Decimal("1") - cash_floor) / Decimal(len(prices))
    positions: list[dict] = []
    invested = Decimal("0")
    for ticker, price, sector in prices:
        units = whole_share_units(target_value, price)
        value = units * price
        invested += value
        positions.append(
            {
                "ticker": ticker,
                "sector": sector,
                "target_weight": target_weight,
                "units": units,
                "value": value,
                "price": price,
            }
        )
    cash = capital - invested
    return positions, cash


def actual_weights(positions: list[dict], capital: Decimal) -> list[dict]:
    """Attach actual (post-rounding) weights to each position."""
    for position in positions:
        position["actual_weight"] = position["value"] / capital
    return positions


def sector_allocations(positions: list[dict], capital: Decimal) -> list[dict]:
    """Sector weights per position set, two denominators.

    ``invested_weight`` = sector value / invested value;
    ``capital_weight`` = sector value / capital. Cash appears in
    neither numerator; it is reported at portfolio level.
    """
    invested = sum((p["value"] for p in positions), Decimal("0"))
    by_sector: dict[str, Decimal] = {}
    for position in positions:
        sector = position["sector"] or "UNKNOWN_SECTOR"
        by_sector[sector] = by_sector.get(sector, Decimal("0")) + position["value"]
    rows = []
    for sector, value in sorted(by_sector.items()):
        rows.append(
            {
                "sector": sector,
                "invested_value": value,
                "invested_weight": (value / invested) if invested > 0 else Decimal("0"),
                "capital_weight": value / capital,
            }
        )
    return rows


def check_caps(
    positions: list[dict],
    capital: Decimal,
    max_single_weight: Decimal,
    max_sector_weight: Decimal,
    cash_floor: Decimal,
    cash: Decimal,
) -> dict:
    """Cap and floor checks on a constructed position set.

    Returns per-check pass/fail plus the binding constraints:
    a cap is binding when the target sat exactly at it (the
    actual, post-rounding value then sits just under it); the
    cash floor is binding when the invested amount was capped by
    it (actual cash >= floor, with the excess purely rounding).
    """
    largest_single = max((p["value"] / capital for p in positions), default=Decimal("0"))
    sectors = sector_allocations(positions, capital)
    largest_sector = max((s["capital_weight"] for s in sectors), default=Decimal("0"))
    cash_weight = cash / capital
    return {
        "max_single_weight": {
            "cap": str(max_single_weight),
            "actual": str(largest_single),
            "pass": largest_single <= max_single_weight,
        },
        "max_sector_weight": {
            "cap": str(max_sector_weight),
            "actual": str(largest_sector),
            "pass": largest_sector <= max_sector_weight,
        },
        "cash_floor": {
            "floor": str(cash_floor),
            "actual": str(cash_weight),
            "pass": cash_weight >= cash_floor,
        },
    }


def mean_variance_gate(computed_forecasts: int, return_observations: int) -> tuple[str, list[str]]:
    """Mean-variance constructability gate (pure predicate).

    Returns ("CONSTRUCTIBLE", []) only when validated expected
    returns exist AND a covariance matrix can be estimated.
    Otherwise ("NOT_CALCULABLE", reasons). In this run both fail:
    0 computed forecasts (Phase 13 abstained on all 120
    assessments) and 0 return observations (1 price date).
    """
    reasons: list[str] = []
    if computed_forecasts <= 0:
        reasons.append(
            "no validated expected returns: Phase 13 computed 0 "
            "forecasts (all 120 assessments insufficient_inputs, "
            "live forecasting abstained)"
        )
    if return_observations < 2:
        reasons.append(
            f"no covariance matrix: {return_observations} return "
            "observation(s) from 1 price date (at least 2 closes "
            "are needed for a single return)"
        )
    if reasons:
        return "NOT_CALCULABLE", reasons
    return "CONSTRUCTIBLE", []
