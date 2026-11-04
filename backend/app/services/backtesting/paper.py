"""Paper-trading simulator primitives for Phase 17.

Pure functions only: no database, no network, no clock.

- Next eligible price rule: a signal dated D may only fill at
  the first observed close strictly after D. A signal with no
  later observed price can never fill; it stays proposed. This
  is the no-look-ahead rule for fills.
- Order lifecycle: proposed -> accepted -> filled /
  partially_filled / cancelled / rejected. Acceptance requires
  the ticker to exist in the universe and a reference price to
  exist; anything else is rejected with a reason. A fill
  requires a next eligible price; without one the order stays
  proposed (it is never filled at a signal-date price, which
  would be look-ahead only if the signal came after the close —
  and signal_time is "close", so same-day fills are not assumed).
- Ledger derivation: opening positions, opening cash, and a
  valuation snapshot re-derived from a simulated portfolio's
  holdings. Cash is capital minus the recomputed sum of holding
  values (units x price, recomputed here, never copied from a
  stored value without recomputation). The ledger is a
  SIMULATION dated to the price date.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

ORDER_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "proposed": ("accepted", "cancelled", "rejected"),
    "accepted": ("filled", "partially_filled", "cancelled", "rejected"),
    "filled": (),
    "partially_filled": ("filled", "cancelled"),
    "cancelled": (),
    "rejected": (),
}


def next_eligible_price_date(observed_dates: list[date], signal_date: date) -> date | None:
    """First observed price date strictly after the signal date.

    Returns None when no later observed price exists. Same-day
    fills are not assumed: signal_time is "close", so the signal
    is only known at the close and the next eligible price is a
    later close.
    """
    later = [d for d in observed_dates if d > signal_date]
    return min(later) if later else None


def accept_order(ticker_in_universe: bool, reference_price: Decimal | None) -> tuple[str, str]:
    """Decide acceptance of a proposed simulated order."""
    if not ticker_in_universe:
        return "rejected", "Ticker is not in the central universe."
    if reference_price is None or reference_price <= 0:
        return "rejected", "No valid reference price exists for the ticker."
    return "accepted", "Ticker in universe with a valid reference price."


def fill_order(
    status: str, eligible_date: date | None, fill_price: Decimal | None
) -> tuple[str, str, date | None, Decimal | None]:
    """Advance an accepted order toward a fill.

    Only an accepted order with a next eligible price and a
    positive fill price fills. Anything else keeps its status
    with a reason; nothing is filled at an invented price.
    """
    if status != "accepted":
        return status, "Only an accepted order can fill.", None, None
    if eligible_date is None:
        return (
            "accepted",
            "No next eligible price exists; order stays accepted, unfilled.",
            None,
            None,
        )
    if fill_price is None or fill_price <= 0:
        return (
            "accepted",
            "No valid fill price exists at the next eligible date.",
            None,
            None,
        )
    return "filled", "Filled at the next eligible observed close.", eligible_date, fill_price


def derive_ledger(
    portfolio_name: str,
    capital: Decimal,
    holdings: list[dict],
    entry_date: date,
) -> list[dict]:
    """Re-derive a paper ledger from a simulated portfolio.

    ``holdings`` is a list of dicts with ticker, units, price.
    Returns opening_position entries (one per holding, value
    recomputed as units x price), one opening_cash entry
    (capital minus recomputed holdings total), and one
    valuation_snapshot entry (total = holdings + cash, which
    reconciles to capital exactly). Every entry is a SIMULATION.
    """
    entries: list[dict] = []
    holdings_total = Decimal(0)
    for holding in holdings:
        value = Decimal(holding["units"]) * Decimal(holding["price"])
        holdings_total += value
        entries.append(
            {
                "portfolio_name": portfolio_name,
                "entry_type": "opening_position",
                "ticker_key": holding["ticker"],
                "ticker": holding["ticker"],
                "units": Decimal(holding["units"]),
                "price": Decimal(holding["price"]),
                "value": value,
                "cash_after": capital - holdings_total,
                "entry_date": entry_date,
                "source": {"kind": "phase16_holding", "ticker": holding["ticker"]},
            }
        )
    cash = capital - holdings_total
    entries.append(
        {
            "portfolio_name": portfolio_name,
            "entry_type": "opening_cash",
            "ticker_key": "__CASH__",
            "ticker": None,
            "units": None,
            "price": None,
            "value": cash,
            "cash_after": cash,
            "entry_date": entry_date,
            "source": {"kind": "phase16_portfolio_cash", "capital": str(capital)},
        }
    )
    entries.append(
        {
            "portfolio_name": portfolio_name,
            "entry_type": "valuation_snapshot",
            "ticker_key": "__TOTAL__",
            "ticker": None,
            "units": None,
            "price": None,
            "value": holdings_total + cash,
            "cash_after": cash,
            "entry_date": entry_date,
            "source": {"kind": "phase16_portfolio_total", "capital": str(capital)},
        }
    )
    return entries


def apply_costs(
    traded_value: Decimal,
    fees_bps: Decimal | None,
    taxes_bps: Decimal | None,
    slippage_bps: Decimal | None,
) -> Decimal | None:
    """Total transaction cost for a traded value, or None.

    Returns None when any cost input is None (UNVALIDATED): costs
    are never computed from invented rates. Sensitivity analysis
    varies the bps inputs on fixtures only.
    """
    if fees_bps is None or taxes_bps is None or slippage_bps is None:
        return None
    total_bps = fees_bps + taxes_bps + slippage_bps
    return traded_value * total_bps / Decimal(10000)
