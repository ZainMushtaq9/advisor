# Phase 6 — API documentation

Base: `/api/v1`. All endpoints are GET only. No endpoint writes
anything. When DATABASE_URL is not set, every endpoint answers
503 with a truthful reason, never a fake empty market.

## GET /api/v1/indicators/coverage

Live coverage summary computed deterministically from
market_prices (no stored verdicts are trusted blindly).

Query: `as_of` (optional ISO date; defaults to the latest price
date; bars after it are excluded — no-look-ahead).

Response: `as_of`, `securities_assessed`, `indicators_registered`,
`securities_with_any_calculable`, `per_indicator` (per key:
category, warmup_bars, calculable, not_calculable, reasons with
counts), `scope_note`.

Live result (2026-11-04): 470 assessed, 62 registered, 0 with
any calculable indicator.

## GET /api/v1/indicators/coverage/{ticker}

Per-ticker verdicts for all 62 indicators: indicator_key,
category, status (CALCULABLE / NOT_CALCULABLE), value (string
Decimal or null), reason, detail (including the exact unblocker,
e.g. "Needs 5 bars, only 1 available; 4 more bars required."),
warmup_bars, formula_version, parameters, plus bars_available,
first/last dates, input_quality, and the scope note.

Errors: 404 for an unknown ticker; 422 for a bad as_of date.
A known ticker with no observations returns 200 with all
verdicts NOT_CALCULABLE (missing_data) — never 404 for an empty
series.

## GET /api/v1/indicators/values

Stored technical_indicator_values rows only, newest first.
Query: `ticker`, `indicator_key`, `skip`, `limit` (1–200).
Response: `total`, `items` (ticker, indicator_key,
indicator_configuration_id, config_version, parameters,
observation_date, timeframe, value, calculation_version,
last_input_observation_date, quality_status, source_key),
`scope_note`. Rows are ordered by observation_date desc,
ticker, indicator_key.

Live result: total 0. That is the truthful empty state: nothing
is calculable on one trading day, so nothing is stored.

Errors: 404 for an unknown ticker; 422 for an unknown
indicator_key or an out-of-range limit.

## GET /api/v1/indicators/signals

Stored technical_signal_events rows only, newest first.
Query: `ticker`, `skip`, `limit` (1–200). Response: `total`,
`items` (ticker, event_date, indicator_key, event_condition,
observed_value, parameter_configuration, calculation_version),
a `note` stating events are observations only and no rule is
activated, and the scope note.

Live result: total 0.

## Scope note (attached to every response)

Main Board / Normal Counter registry view only (470
securities); GEM and Non-Compliant not captured. All committed
prices are UNVERIFIED single-source observations for one trading
day (2026-11-03). No KSE-100, full-market, or VERIFIED claim is
made. Signal events, if any ever exist, are observations only,
never buy/sell recommendations.

## Transparency contract

Every value row carries its formula version, parameters (via
its configuration), last input date, quality status and source
key. Every NOT_CALCULABLE verdict carries its reason and the
data that would unblock it. Nothing in these endpoints is
rounded for display beyond the stored Decimal string.
