"""Pure Decimal valuation formulas for Phase 9.

Every function returns ``Decimal | None``: ``None`` means the inputs
do not support a value (missing input, zero denominator, negative
EPS for a multiple, terminal growth at or above the discount rate,
or a required return at or below growth) and the caller records
NOT_CALCULABLE with a reason. No function ever returns zero as a
substitute, and no function ever raises on bad inputs — bad inputs
are a coverage outcome, not an exception. No function invents a
discount rate, growth rate, or forecast: callers pass assumptions
explicitly, and production runs pass none, so DCF/DDM/RI return None
there by construction.
"""

from __future__ import annotations

from decimal import Decimal

D = Decimal


def _dec(value) -> Decimal | None:
    """Coerce an int/float/str/Decimal to Decimal; None stays None."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def div(numerator, denominator) -> Decimal | None:
    """Safe division: None when either side is missing or denominator is 0."""
    n, d = _dec(numerator), _dec(denominator)
    if n is None or d is None or d == 0:
        return None
    return n / d


def trailing_pe(price, eps) -> Decimal | None:
    """Price / EPS. None when EPS is missing, zero, or negative: a
    multiple on non-positive earnings is non-meaningful, not zero."""
    p, e = _dec(price), _dec(eps)
    if p is None or e is None or e <= 0:
        return None
    return p / e


def price_sensitivity(price, eps, pct) -> Decimal | None:
    """Mechanical P/E at price moved by ``pct`` (e.g. -0.10 / +0.10),
    EPS held at its printed value. A sensitivity, not a forecast."""
    p, e, q = _dec(price), _dec(eps), _dec(pct)
    if p is None or e is None or q is None or e <= 0:
        return None
    return (p * (D(1) + q)) / e


def dcf_value(free_cash_flows, discount_rate, terminal_growth) -> Decimal | None:
    """PV of an explicit forecast list plus a Gordon terminal value
    on the final forecast flow: TV = FCF_last x (1+g) / (r - g).

    Rejected (None) when: no flows, any flow missing, r missing or
    <= 0, g missing, or g >= r (a perpetual-growth model with
    terminal growth at or above WACC is impossible — brief rule).
    """
    if not free_cash_flows:
        return None
    flows = [_dec(f) for f in free_cash_flows]
    if any(f is None for f in flows):
        return None
    r, g = _dec(discount_rate), _dec(terminal_growth)
    if r is None or g is None or r <= 0 or g >= r:
        return None
    pv = D(0)
    for i, f in enumerate(flows, start=1):
        pv += f / ((D(1) + r) ** i)
    terminal = flows[-1] * (D(1) + g) / (r - g)
    pv += terminal / ((D(1) + r) ** len(flows))
    return pv


def gordon_ddm(dividend_per_share, growth, required_return) -> Decimal | None:
    """Gordon dividend model: DPS x (1+g) / (r - g). None when any
    input is missing or r <= g."""
    d, g, r = _dec(dividend_per_share), _dec(growth), _dec(required_return)
    if d is None or g is None or r is None or r <= g:
        return None
    return d * (D(1) + g) / (r - g)


def residual_income_value(book_value, residual_incomes, required_return) -> Decimal | None:
    """Bank residual-income model: BV + PV of residual incomes.
    None when any input is missing or the required return is <= 0."""
    bv = _dec(book_value)
    r = _dec(required_return)
    if bv is None or r is None or r <= 0 or not residual_incomes:
        return None
    ris = [_dec(x) for x in residual_incomes]
    if any(x is None for x in ris):
        return None
    pv = D(0)
    for i, x in enumerate(ris, start=1):
        pv += x / ((D(1) + r) ** i)
    return bv + pv


def book_value(equity) -> Decimal | None:
    """Asset-based book value: the equity figure as printed. Identity
    by design — the method's content is the labelling (statement-date
    book value, not a market fair value, not per-share), not a
    transformation."""
    return _dec(equity)


def peer_median(multiples) -> Decimal | None:
    """Median peer multiple. Requires at least 3 peers: with fewer,
    a 'median' is not a robust comparable and outlier treatment
    cannot be applied. Returns None below 3 peers."""
    vals = sorted(_dec(m) for m in multiples if _dec(m) is not None)
    if len(vals) < 3:
        return None
    n = len(vals)
    mid = n // 2
    if n % 2 == 1:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / D(2)
