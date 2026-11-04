"""Safe catch-up helpers — Phase 5. Pure functions over stored rows.

Catch-up never invents a price: given a requested date range it computes
which dates have NO stored observation for a security (for one source),
and ingestion then fills only those dates from a supplied file. A date
with no stored row is reported as a missing session; it is never
zero-filled, and absence of a row is NOT a claim that the market was
open or closed that day (no trading calendar is consulted here).

"Stored" means stored for the same source: a date observed from source
A is still missing for source B, because the grain includes
data_source_id.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.market import MarketPrice


def compute_missing_dates(
    stored_dates: set[date], start: date, end: date
) -> list[date]:
    """Sorted dates in [start, end] absent from ``stored_dates``."""
    if end < start:
        raise ValueError("end date must not be before start date")
    missing: list[date] = []
    current = start
    while current <= end:
        if current not in stored_dates:
            missing.append(current)
        current += timedelta(days=1)
    return missing


def missing_sessions_by_security(
    stored_by_ticker: dict[str, set[date]],
    tickers: list[str],
    start: date,
    end: date,
) -> dict[str, list[str]]:
    """Missing dates per ticker, as ISO strings, for a requested range.

    Tickers with no missing dates map to an empty list; tickers absent
    from ``stored_by_ticker`` are treated as having no stored dates.
    """
    return {
        ticker: [
            day.isoformat()
            for day in compute_missing_dates(
                stored_by_ticker.get(ticker, set()), start, end
            )
        ]
        for ticker in tickers
    }


def stored_dates_for_source(
    session: Session, data_source_id: int, security_ids: list[int]
) -> dict[int, set[date]]:
    """Stored trading dates per security id, for one source only."""
    if not security_ids:
        return {}
    rows = (
        session.query(MarketPrice.trading_date, MarketPrice.security_id)
        .filter(
            MarketPrice.data_source_id == data_source_id,
            MarketPrice.bar_type == "daily",
            MarketPrice.security_id.in_(security_ids),
        )
        .all()
    )
    stored: dict[int, set[date]] = {security_id: set() for security_id in security_ids}
    for trading_date, security_id in rows:
        stored.setdefault(security_id, set()).add(trading_date)
    return stored


def filter_rows_to_missing(
    validated_rows: list,
    stored_by_security_id: dict[int, set[date]],
    security_id_by_ticker: dict[str, int],
) -> tuple[list, int]:
    """Keep only validated rows whose (security, date) is not stored.

    Returns (kept_rows, filtered_out_count). Pure over the supplied
    stored sets; it performs no database access itself.
    """
    kept: list = []
    filtered_out = 0
    for row in validated_rows:
        security_id = security_id_by_ticker.get(row.ticker)
        stored = stored_by_security_id.get(security_id, set()) if security_id else set()
        if row.trading_date in stored:
            filtered_out += 1
        else:
            kept.append(row)
    return kept, filtered_out
