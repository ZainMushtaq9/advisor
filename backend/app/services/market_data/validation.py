"""Pure, deterministic validation for daily OHLCV rows — Phase 5.

No database access, no network, no LLM. A rejected row is NEVER stored
as a price: the caller keeps the raw values in the ingestion report
together with the rejection reason, and nothing is written for that row.

Rejection reasons (stable codes, also used in ingestion reports):
  missing_field       a required field is missing or blank
  unknown_ticker      ticker is not in the securities table
  unparseable_date    trading_date is not an ISO date (YYYY-MM-DD)
  unparseable_number  a numeric field is not a finite number
  unparseable_timestamp  source_timestamp is not an ISO datetime
  non_positive_price  open/high/low/close (or previous_close, when
                      present) is zero or negative
  negative_volume     volume is negative
  negative_turnover   turnover is negative
  ohlc_inconsistency  high < max(open, close), or low > min(open, close),
                      or high < low
  future_trading_date trading_date is after today in Asia/Karachi

Required fields: ticker, trading_date, open, high, low, close, volume.
Optional fields (blank means "absent", never zero): turnover,
previous_close, source_key, source_timestamp. A blank optional price is
absent, not a zero price; a present optional price must still be
positive, because a zero previous close would be a fabricated value.

Ticker matching is exact after stripping surrounding whitespace and
upper-casing, matching how securities.ticker is stored. Scope is the
securities table itself: a ticker outside the 470-snapshot scope cannot
occur except as an unknown ticker, which is rejected, never widened.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

KARACHI = ZoneInfo("Asia/Karachi")

EXPECTED_HEADER = (
    "ticker",
    "trading_date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "turnover",
    "previous_close",
    "source_key",
    "source_timestamp",
)

REQUIRED_FIELDS = ("ticker", "trading_date", "open", "high", "low", "close", "volume")

REJECTION_MISSING_FIELD = "missing_field"
REJECTION_UNKNOWN_TICKER = "unknown_ticker"
REJECTION_UNPARSEABLE_DATE = "unparseable_date"
REJECTION_UNPARSEABLE_NUMBER = "unparseable_number"
REJECTION_UNPARSEABLE_TIMESTAMP = "unparseable_timestamp"
REJECTION_NON_POSITIVE_PRICE = "non_positive_price"
REJECTION_NEGATIVE_VOLUME = "negative_volume"
REJECTION_NEGATIVE_TURNOVER = "negative_turnover"
REJECTION_OHLC_INCONSISTENCY = "ohlc_inconsistency"
REJECTION_FUTURE_TRADING_DATE = "future_trading_date"


@dataclass(frozen=True)
class ValidatedRow:
    """One validated daily bar. All prices are official UNADJUSTED values
    (is_adjusted=False when stored); adjustment is never applied here."""

    ticker: str
    trading_date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    turnover: Decimal | None
    previous_close: Decimal | None
    source_key: str | None
    source_timestamp: datetime | None

    def ohlcv(self) -> tuple[Decimal, Decimal, Decimal, Decimal, int]:
        return (
            self.open_price,
            self.high_price,
            self.low_price,
            self.close_price,
            self.volume,
        )


def karachi_today() -> date:
    return datetime.now(KARACHI).date()


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def _blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _parse_decimal(value: str) -> Decimal | None:
    try:
        parsed = Decimal(value.strip())
    except (InvalidOperation, ValueError, AttributeError):
        return None
    if not parsed.is_finite():
        return None
    return parsed


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def _parse_timestamp(value: str) -> datetime | None:
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        # A naive source timestamp is read as Asia/Karachi local time;
        # it is never silently relabelled as UTC.
        parsed = parsed.replace(tzinfo=KARACHI)
    return parsed


def validate_row(
    raw: dict,
    known_tickers: set[str],
    today: date | None = None,
) -> tuple[ValidatedRow | None, str | None]:
    """Validate one raw CSV row.

    Returns (ValidatedRow, None) on success, or (None, reason-code) on
    rejection. ``raw`` is never mutated and its values are never stored
    by this function; the caller preserves them in the report.
    """
    if today is None:
        today = karachi_today()

    for field in REQUIRED_FIELDS:
        if _blank(raw.get(field)):
            return None, REJECTION_MISSING_FIELD

    ticker = normalize_ticker(str(raw["ticker"]))
    # Unknown-ticker is checked before any numeric parsing so that the
    # CLI fail-fast (abort on any unknown ticker) fires even when the
    # same row is malformed in other ways.
    if ticker not in known_tickers:
        return None, REJECTION_UNKNOWN_TICKER

    trading_date = _parse_date(str(raw["trading_date"]))
    if trading_date is None:
        return None, REJECTION_UNPARSEABLE_DATE

    prices: dict[str, Decimal] = {}
    for field in ("open", "high", "low", "close"):
        parsed = _parse_decimal(str(raw[field]))
        if parsed is None:
            return None, REJECTION_UNPARSEABLE_NUMBER
        prices[field] = parsed

    volume_decimal = _parse_decimal(str(raw["volume"]))
    if volume_decimal is None or volume_decimal != volume_decimal.to_integral_value():
        return None, REJECTION_UNPARSEABLE_NUMBER
    volume = int(volume_decimal)

    turnover: Decimal | None = None
    if not _blank(raw.get("turnover")):
        turnover = _parse_decimal(str(raw["turnover"]))
        if turnover is None:
            return None, REJECTION_UNPARSEABLE_NUMBER

    previous_close: Decimal | None = None
    if not _blank(raw.get("previous_close")):
        previous_close = _parse_decimal(str(raw["previous_close"]))
        if previous_close is None:
            return None, REJECTION_UNPARSEABLE_NUMBER

    source_timestamp: datetime | None = None
    if not _blank(raw.get("source_timestamp")):
        source_timestamp = _parse_timestamp(str(raw["source_timestamp"]))
        if source_timestamp is None:
            return None, REJECTION_UNPARSEABLE_TIMESTAMP

    for field in ("open", "high", "low", "close"):
        if prices[field] <= 0:
            return None, REJECTION_NON_POSITIVE_PRICE
    if previous_close is not None and previous_close <= 0:
        return None, REJECTION_NON_POSITIVE_PRICE
    if volume < 0:
        return None, REJECTION_NEGATIVE_VOLUME
    if turnover is not None and turnover < 0:
        return None, REJECTION_NEGATIVE_TURNOVER

    open_price = prices["open"]
    high_price = prices["high"]
    low_price = prices["low"]
    close_price = prices["close"]
    if (
        high_price < max(open_price, close_price)
        or low_price > min(open_price, close_price)
        or high_price < low_price
    ):
        return None, REJECTION_OHLC_INCONSISTENCY

    if trading_date > today:
        return None, REJECTION_FUTURE_TRADING_DATE

    source_key = raw.get("source_key")
    source_key = source_key.strip() if isinstance(source_key, str) else None
    return ValidatedRow(
        ticker=ticker,
        trading_date=trading_date,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        volume=volume,
        turnover=turnover,
        previous_close=previous_close,
        source_key=source_key or None,
        source_timestamp=source_timestamp,
    ), None
