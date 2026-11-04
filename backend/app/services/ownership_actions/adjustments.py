"""Pure price-adjustment formulas (Phase 12).

All functions are pure Decimal arithmetic on a single raw price.
Nothing here reads the database, writes anything, or touches a raw
row: applying a rule produces a NEW derived value, and the caller is
responsible for never storing it over a raw observation.

A rule may only be applied when its required inputs exist. The
``can_apply`` helpers return False (never raise, never guess) when an
input is missing — in this run every stored action lacks an ex-date,
so no rule is applied to any series.
"""

from __future__ import annotations

from decimal import Decimal

ZERO = Decimal("0")


def dividend_adjusted_close(raw_close: Decimal, dps: Decimal) -> Decimal:
    """Cash dividend: adjusted = raw - DPS. DPS must be >= 0."""
    if dps < ZERO:
        raise ValueError("dividend per share must not be negative")
    return raw_close - dps


def bonus_factor(existing: Decimal, bonus: Decimal) -> Decimal:
    """Bonus factor: (existing + bonus) / existing."""
    if existing <= ZERO or bonus < ZERO:
        raise ValueError("bonus inputs must be positive / non-negative")
    return (existing + bonus) / existing


def split_factor(old: Decimal, new: Decimal) -> Decimal:
    """Split factor: new shares per old share."""
    if old <= ZERO or new <= ZERO:
        raise ValueError("split inputs must be positive")
    return new / old


def apply_factor(raw_close: Decimal, raw_volume: int, factor: Decimal) -> tuple[Decimal, Decimal]:
    """Split/bonus application: price divides, volume multiplies."""
    if factor <= ZERO:
        raise ValueError("adjustment factor must be positive")
    return raw_close / factor, Decimal(raw_volume) * factor


def theoretical_ex_rights_price(
    old_shares: Decimal,
    cum_rights_price: Decimal,
    new_shares: Decimal,
    subscription_price: Decimal,
) -> Decimal:
    """TERP = (old * cum_price + new * subscription) / (old + new)."""
    if (
        old_shares <= ZERO
        or new_shares < ZERO
        or cum_rights_price < ZERO
        or subscription_price < ZERO
    ):
        raise ValueError("rights inputs must be non-negative and old shares positive")
    return (old_shares * cum_rights_price + new_shares * subscription_price) / (
        old_shares + new_shares
    )


def can_apply_dividend(ex_date, dps) -> bool:
    """A dividend rule applies only with both an ex-date and a DPS."""
    return ex_date is not None and dps is not None
