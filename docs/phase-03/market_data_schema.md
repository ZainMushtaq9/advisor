# Phase 3 — Market Data Schema

## Tables

market_prices, live_quotes, market_snapshots, index_prices,
corporate_actions, dividends, announcements, news,
trading_sessions, trading_calendars. See schema_reference.md for
grains.

## Rules that matter for Phase 5 (the consumer)

1. **Unadjusted only.** market_prices stores official unadjusted
   prices. Adjustment factors live in corporate_actions;
   adjusted series are derived views. Never present unadjusted
   prices as total-return/adjusted prices.
2. **Source is part of the grain.** Two sources disagreeing is
   two rows with quality CONFLICTED, not one row with a chosen
   value. Phase 5 reconciliation must preserve both.
3. **No historical intraday promise.** The schema allows
   bar_type='intraday_tick', but Phase 1/5 evidence says only
   today's ticks are available (psx-dps) and no historical
   intraday archive exists via psxdata. A bar_type value is not
   evidence that the data exists.
4. **Missing sessions are data.** trading_sessions.status =
   'missing' plus a data_quality_reports row is the correct
   representation of a missing session. A missing price row is
   not a zero, not an interpolated value, not a carried-forward
   close.
5. **Live quotes are a log, not a current value.** live_quotes
   rows are append-only with is_latest marking the newest per
   (security, source). A 'current quote' is a view over
   is_latest rows, and its staleness must be computed from
   quote_instant + source freshness, never assumed live.
6. **Snapshots are as-of views.** market_snapshots rows are never
   overwritten; an as-of query takes the latest snapshot at or
   before a PKT instant.
7. **Announcements vs news.** Announcements are issuer/exchange
   publications (with PDF URL + hash where the source provides
   them); news is third-party reporting. Neither is a live feed
   until verified. Duplicate detection key: content_hash first,
   source URL second, else flagged for review (no key = no
   duplicate check, not a pass).
