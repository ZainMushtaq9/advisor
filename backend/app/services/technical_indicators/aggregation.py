"""Daily -> weekly / monthly aggregation (Phase 6).

Rules, fixed here so no caller improvises them:

- Weekly bars group ISO year-weeks (Monday-Sunday). Monthly bars
  group calendar months.
- OHLC aggregation is standard: open = first bar's open, high =
  max high, low = min low, close = last bar's close, volume =
  sum of volumes. A missing volume in any constituent bar makes
  the aggregated volume missing (never zero-filled).
- Period status is ALWAYS "partial" in this framework version.
  A period can only be called complete when its observed sessions
  are checked against a validated trading calendar (which would
  list holidays and half-days), and no such calendar is validated
  yet. Labelling a one-day week "complete" would be fabrication.
  The aggregated bar therefore always carries observed_days and
  status="partial", and no indicator is ever computed from a
  partial period without that status travelling with it.
- Intraday aggregation does not exist: no validated intraday data
  exists, so any intraday request is refused, not approximated.
"""

from __future__ import annotations

from datetime import date

from app.services.technical_indicators.formulas import InsufficientData


def _aggregate_group(bars: list[dict]) -> dict:
    """Aggregate one already-grouped, date-ordered list of bars.

    Missing OHLC in any constituent bar is missing data, raised
    cleanly — never a TypeError from max()/min(), never a silent
    None propagating into the aggregated bar.
    """
    ordered = sorted(bars, key=lambda b: b["date"])
    for bar in ordered:
        for field in ("open", "high", "low", "close"):
            if bar.get(field) is None:
                raise InsufficientData(
                    "missing_data",
                    f"Aggregated group has a bar with missing {field}",
                )
    first = ordered[0]
    last = ordered[-1]
    volumes = [b.get("volume") for b in ordered]
    volume = None if any(v is None for v in volumes) else sum(volumes)
    return {
        "date": last["date"],
        "period_start": first["date"],
        "period_end": last["date"],
        "open": first.get("open"),
        "high": max(b["high"] for b in ordered),
        "low": min(b["low"] for b in ordered),
        "close": last.get("close"),
        "volume": volume,
        "previous_close": None,
        "observed_days": len(ordered),
        "status": "partial",
    }


def aggregate(bars: list[dict], timeframe: str) -> list[dict]:
    """Aggregate daily bars to weekly or monthly bars.

    Returns aggregated bars in date order, each with status
    "partial" (see module docstring). Raises InsufficientData for
    an unknown timeframe, and refuses intraday outright.
    """
    if timeframe == "daily":
        ordered = sorted(bars, key=lambda b: b["date"])
        return [dict(b, observed_days=1, status="partial") for b in ordered]
    if timeframe == "intraday":
        raise InsufficientData(
            "missing_data", "No validated intraday data exists; intraday refused"
        )
    if timeframe not in ("weekly", "monthly"):
        raise InsufficientData("missing_data", f"Unknown timeframe: {timeframe}")
    groups: dict[object, list[dict]] = {}
    for bar in bars:
        d: date = bar["date"]
        if timeframe == "weekly":
            key = (d.isocalendar()[0], d.isocalendar()[1])
        else:
            key = (d.year, d.month)
        groups.setdefault(key, []).append(bar)
    return [_aggregate_group(groups[k]) for k in sorted(groups)]
