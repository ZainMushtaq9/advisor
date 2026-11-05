"""Actual market-reaction / event-study calculations.

Uses ACTUAL available trading observations only, with Decimal
arithmetic (the project's financial-computation rule). Nothing is
manufactured: a missing observation yields INSUFFICIENT_DATA for
that window, with the exact missing piece named.

Date-granularity rule (documented, because sessions have no
intraday timestamps in this dataset): for an event dated D,
pre = last observation with trading_date < D, event_day = the
observation on D itself (if any), post = first observation with
trading_date > D. A same-day publication cannot be split into
pre/post intraday — that limitation is stated, not hidden.
Returns are simple returns on closes: (post - pre) / pre.
Volume change compares the post-session volume to the pre
volume. Benchmark/sector excess return = company return minus
benchmark/sector return, computed only when both series have the
matching window observations.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

WINDOWS = (1, 5, 10, 20)


def _dec(value: object) -> Decimal | None:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result


def _simple_return(later: Decimal, earlier: Decimal) -> Decimal | None:
    if earlier == 0:
        return None
    return (later - earlier) / earlier


def compute_reaction(
    event_date: date,
    prices: list[dict],
    benchmark_prices: list[dict] | None = None,
    sector_prices: list[dict] | None = None,
) -> dict:
    """Compute the market reaction for one event.

    ``prices``: [{trading_date: date, close: Decimal-compatible,
    volume: int-compatible}] sorted or unsorted (sorted here).
    Benchmark/sector series use the same shape. Returns a dict
    with pre/post/event-day observations, per-window returns,
    volume change, benchmark/sector returns and excess returns,
    plus ``status`` ("computed" or "INSUFFICIENT_DATA") and a
    ``missing`` list naming every window that could not be
    computed and why.
    """
    ordered = sorted(prices, key=lambda p: p["trading_date"])
    pre = None
    event_day = None
    post = None
    for row in ordered:
        day = row["trading_date"]
        if day < event_date:
            pre = row
        elif day == event_date:
            event_day = row
        elif day > event_date and post is None:
            post = row
    missing: list[str] = []
    if pre is None:
        missing.append("no price observation before the event date")
    if post is None:
        missing.append("no price observation after the event date")

    def _window_returns(series: list[dict], anchor: dict | None) -> dict:
        """Returns at 1/5/10/20 sessions after the anchor row."""
        result: dict[str, Decimal | None] = {}
        if anchor is None:
            return {f"return_{w}d": None for w in WINDOWS}
        ordered_series = sorted(series, key=lambda p: p["trading_date"])
        try:
            anchor_idx = next(
                i for i, row in enumerate(ordered_series)
                if row["trading_date"] == anchor["trading_date"]
            )
        except StopIteration:
            return {f"return_{w}d": None for w in WINDOWS}
        base = _dec(anchor["close"])
        for window in WINDOWS:
            idx = anchor_idx + window
            if base is None or idx >= len(ordered_series):
                result[f"return_{window}d"] = None
                continue
            later = _dec(ordered_series[idx]["close"])
            result[f"return_{window}d"] = (
                _simple_return(later, base) if later is not None else None
            )
        return result

    company_returns = _window_returns(ordered, post)
    for window in WINDOWS:
        if company_returns[f"return_{window}d"] is None:
            missing.append(f"{window}-day window: no observation {window} sessions after the post-event session")

    volume_change = None
    if pre is not None and post is not None:
        pre_vol = _dec(pre.get("volume"))
        post_vol = _dec(post.get("volume"))
        if pre_vol is not None and post_vol is not None and pre_vol != 0:
            volume_change = (post_vol - pre_vol) / pre_vol

    def _series_windows(series: list[dict] | None) -> dict:
        if not series:
            return {}
        ordered_series = sorted(series, key=lambda p: p["trading_date"])
        anchor = next(
            (row for row in ordered_series if row["trading_date"] > event_date),
            None,
        )
        return _window_returns(ordered_series, anchor)

    benchmark_returns = _series_windows(benchmark_prices)
    sector_returns = _series_windows(sector_prices)

    def _excess(company: dict, other: dict) -> dict:
        out = {}
        for window in WINDOWS:
            key = f"return_{window}d"
            c, o = company.get(key), other.get(key)
            out[f"excess_{window}d"] = (c - o) if (c is not None and o is not None) else None
        return out

    status = "INSUFFICIENT_DATA" if missing else "computed"
    return {
        "status": status,
        "missing": missing,
        "pre_price": str(pre["close"]) if pre else None,
        "pre_date": pre["trading_date"].isoformat() if pre else None,
        "post_price": str(post["close"]) if post else None,
        "post_date": post["trading_date"].isoformat() if post else None,
        "event_day_price": str(event_day["close"]) if event_day else None,
        "event_day_date": event_day["trading_date"].isoformat() if event_day else None,
        "company_returns": {
            k: (str(v) if v is not None else None) for k, v in company_returns.items()
        },
        "volume_change": str(volume_change) if volume_change is not None else None,
        "benchmark_returns": {
            k: (str(v) if v is not None else None) for k, v in benchmark_returns.items()
        },
        "sector_returns": {
            k: (str(v) if v is not None else None) for k, v in sector_returns.items()
        },
        "excess_vs_benchmark": {
            k: (str(v) if v is not None else None)
            for k, v in _excess(company_returns, benchmark_returns).items()
        },
        "excess_vs_sector": {
            k: (str(v) if v is not None else None)
            for k, v in _excess(company_returns, sector_returns).items()
        },
        "note": (
            "Returns are simple returns on actual closes. No causality "
            "is claimed: correlation between news and movement is not "
            "evidence that the news caused the movement."
        ),
    }
