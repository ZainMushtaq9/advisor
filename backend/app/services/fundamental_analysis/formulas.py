"""Pure Decimal formulas for Phase 8.

Every function returns ``Decimal | None``: ``None`` means the inputs
do not support a value (missing input or zero denominator) and the
caller records NOT_CALCULABLE with a reason. No function ever returns
zero as a substitute, and no function ever raises on bad inputs —
bad inputs are a coverage outcome, not an exception.
"""

from __future__ import annotations

from datetime import date
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


def avg(a, b) -> Decimal | None:
    """Exact two-point average; None when either point is missing."""
    x, y = _dec(a), _dec(b)
    if x is None or y is None:
        return None
    return (x + y) / D(2)


def growth(current, prior) -> Decimal | None:
    """(current - prior) / prior; None when either is missing or prior is 0."""
    c, p = _dec(current), _dec(prior)
    if c is None or p is None or p == 0:
        return None
    return (c - p) / p


def period_days(start: date, end: date) -> int:
    """Inclusive calendar days in [start, end]; the day count used by
    every *_days metric. Computed from the dates, never assumed."""
    return (end - start).days + 1


def days_metric(average_balance, flow, days: int) -> Decimal | None:
    """average_balance / flow x days; None on missing input or zero flow."""
    bal, fl = _dec(average_balance), _dec(flow)
    if bal is None or fl is None or fl == 0:
        return None
    return bal / fl * D(days)


def sign_changed(current, prior) -> bool:
    """True when current and prior have opposite strict signs."""
    c, p = _dec(current), _dec(prior)
    if c is None or p is None:
        return False
    return (c < 0) != (p < 0)
