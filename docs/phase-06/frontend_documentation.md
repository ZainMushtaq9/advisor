# Phase 6 — Frontend documentation

## Route: /indicators

Added to the primary nav (`frontend/lib/nav.ts`) after Market.
The page mirrors the Market page's structure exactly (client
component, FoundationShell, DataTable, ApiClient, Badge), so it
inherits the same loading / unavailable / empty-state behaviour.

## What it shows

1. A summary badge: securities assessed, indicators registered,
   securities with any calculable indicator (today: 470, 62, 0).
2. A coverage table: one row per registered indicator with
   category, warm-up bars, calculable count, not-calculable
   count, and the NOT_CALCULABLE reasons with counts (e.g.
   "insufficient_warmup (444), missing_data (26)").
3. A ticker lookup (prefilled OGDC): per-indicator verdicts for
   that ticker, including the exact unblocker per row (e.g.
   "Needs 5 bars, only 1 available; 4 more bars required.").
   An unknown ticker shows "Unknown ticker or backend
   unavailable" — it never invents a ticker.
4. Stored totals fetched from the API (values total, signals
   total, the API's signal observation note, and the scope
   note) — never static "none yet" text, so the day a value or
   event exists the page says so. Today both totals are 0:
   nothing is calculable on one day, and no rule is activated.
   A one-point chart would imply a trend; the page refuses
   that implication by not drawing one.

## What it deliberately does not do

- No chart component is rendered: there is no series to chart.
- No value is rounded, coloured as "good/bad", or labelled
  buy/sell. Signal events, when they exist, will be shown as
  observations with their condition text, never as
  recommendations. (The "observations only, never buy/sell
  recommendations" note itself is rendered from the signals
  API response, not hardcoded.)
- The ticker lookup distinguishes "Unknown ticker" (API 404)
  from "Backend unavailable" instead of conflating them.
- No data is fetched from anywhere except the backend
  indicators API; no price is ever fabricated client-side.

## Verification

TypeScript typecheck passes, ESLint passes, `next build`
passes (12 routes including /indicators), Vitest 11 passed
(pre-existing suite; no dedicated page unit test was added —
the page is a thin rendering layer over the tested API, and
the build + typecheck + lint cover it; this is stated here
rather than padded with a mock-heavy test).
