# Phase 5 — Market-Data Validation Rules

All rules are deterministic Python in
`backend/app/services/market_data/validation.py`. No LLM validates
or computes any value. A rejected row is never stored as a price;
its raw values and rejection code are preserved in the ingestion
report.

## 1. Input contract

CSV header must be exactly:
`ticker,trading_date,open,high,low,close,volume,turnover,previous_close,source_key,source_timestamp`
A wrong header or an empty file raises ValueError before any
database work. Blank `turnover`, `previous_close`, and
`source_timestamp` mean "absent", never zero.

## 2. Rejection codes (stable, in check order)

| Code | Rule |
|---|---|
| `missing_field` | A required field is blank (ticker, trading_date, open, high, low, close, volume, source_key). |
| `unknown_ticker` | Ticker is not in the securities table. Checked before numeric parsing, so the CLI fail-fast fires even on otherwise-malformed rows. Unknown tickers abort the whole CLI run (exit 2) before any write. |
| `unparseable_date` | `trading_date` is not an ISO date. |
| `unparseable_number` | A numeric field is not a number, is NaN, or volume is non-integral. |
| `unparseable_timestamp` | `source_timestamp`, when present, is not parseable. |
| `non_positive_price` | Any present price (open/high/low/close, and present previous_close) is ≤ 0. |
| `negative_volume` | Volume < 0. |
| `negative_turnover` | Turnover < 0. |
| `ohlc_inconsistency` | high < max(open, close), or low > min(open, close), or high < low. |
| `future_trading_date` | trading_date is after today in Asia/Karachi. |

## 3. Quality assignment (`quality.py`)

| Situation | quality_status |
|---|---|
| Single source | UNVERIFIED (never VERIFIED alone, even for an official source) |
| Two sources agreeing exactly on OHLCV for the grain | PARTIALLY_VERIFIED |
| Agreeing sources include an official source (`psx_official`, `secp`) | VERIFIED |
| Sources disagreeing on the grain | CONFLICTED (both rows stored side-by-side) |

## 4. Freshness — v1 rule (the ONLY freshness rule in v1)

An observation collected more than 30 days after its
trading_date is labelled `freshness: STALE`, in addition to its
quality_status. `quality_status` is a single column, so STALE
does not overwrite UNVERIFIED / PARTIALLY_VERIFIED / VERIFIED /
CONFLICTED; it is carried as a separate `freshness` label
(STALE / CURRENT / UNKNOWN) on API rows and as a `stale` count
in ingestion reports. No other freshness inference exists in v1:
nothing infers freshness from a source, a delay, or a market
session. A fresh-looking row with no collected_at is UNKNOWN,
never a claim of freshness.

## 5. Scope rule

Scope is the securities table: the 470 Main Board / Normal
Counter snapshot securities. Any ticker outside it is
`unknown_ticker`. This scope is never described as KSE-100 or
full-market.
