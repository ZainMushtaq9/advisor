# Phase 6 — Aggregation and timeframes

## Supported timeframes: daily, weekly, monthly only

- Daily is the native grain of the stored data (bar_type daily).
- Weekly groups ISO year-weeks (Monday–Sunday); monthly groups
  calendar months.
- Aggregation: open = first open, high = max high, low = min
  low, close = last close, volume = sum of constituent volumes.
- Intraday is REFUSED outright: no validated intraday data
  exists, and the aggregator raises for any intraday request
  instead of inventing bars.

## Partial vs completed periods — the honest distinction

Every aggregated period is labelled "partial" in this version.
A period can only be called complete against a validated
trading calendar listing holidays and half-days, and no such
calendar is validated yet. A 5-bar week is therefore NOT
called complete: calling it complete would assert that no
trading day was missed, which the data cannot prove. The
status travels with the aggregated bar (observed_days +
status), so no consumer can mistake a partial period for a
complete one.

Consequence for indicators: no indicator is computed from a
partial period without that status travelling with it, and
today no aggregated indicator is computed at all — the runner
never calls the aggregator, and aggregated warm-ups (e.g. 20
weekly bars) are far beyond reach. (Correction to an earlier
draft: a single stored day DOES form exactly one partial weekly
bar and one partial monthly bar; what it cannot form is a
complete period or an aggregated indicator.) Aggregated
indicators unblock only after many trading days AND a validated
trading calendar.

## Missing sessions inside a period

A missing constituent bar is absent, never zero-filled. If a
constituent volume is missing, the aggregated volume is
missing (never zero-filled). If a constituent bar is missing,
the period's observed_days reflects it, and downstream
indicators see fewer bars, not a fabricated price.

## Timezone

Market timestamps are Asia/Karachi. Aggregation groups by
trading_date (a date, not a timestamp), so no timezone
conversion is performed inside the aggregator; the date column
is the authority.
