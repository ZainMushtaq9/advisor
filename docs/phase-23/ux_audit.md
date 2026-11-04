# Phase 23 — UX audit (first-time-user review)

## Method

- Playwright suite (`frontend/e2e/phase23/product.spec.ts`): 11 specs ×
  desktop (Desktop Chrome) + mobile (Pixel 7) = 22 tests, all passing.
- Manual first-time-user walkthrough of every route against the production
  build with the live backend.
- Performance measured in-browser (navigation timing + goto-to-networkidle).

## Performance (measured, production build, local backend)

| Page | goto-to-networkidle | domContentLoaded | load |
| --- | --- | --- | --- |
| / | 1644 ms | 299 ms | 299 ms |
| /dashboard | 1259 ms | 51 ms | 53 ms |
| /companies | 1105 ms | 29 ms | 30 ms |
| /market | 1000 ms | 28 ms | 29 ms |
| /companies/HUBC | 990 ms | 52 ms | 52 ms |
| /screener | 1084 ms | 52 ms | 52 ms |
| /reports | 1030 ms | 33 ms | 33 ms |

Reading: rendering is fast (DOM ready in under 300 ms everywhere); the
~1 s to networkidle is API round-trips, not rendering. The first page's
1644 ms includes server warm-up. No high-impact performance issue found;
no fix needed.

## First-time-user findings

- **Orientation is immediate.** The home page states the product's limits
  before any figure: one trading date, three statement companies, abstained
  forecasts, withheld decisions, draft reports. A user with no domain
  knowledge is never shown a number without its caveat.
- **Navigation is complete but dense.** 18 items wrap to two rows on
  desktop and stack on mobile; every item resolves to a real page (verified
  by the suite's nav check). No dead links were found.
- **Search behaves as labelled.** Company search matches legal names only
  (the registry API's actual field) and the page says so; ticker search
  works on Market and Securities pages, where the API supports it.
- **Empty/error/stale states are correct.** Unknown ticker → a single
  banner ("could not be resolved") with no tab panels and no guessed
  company. HBL → "pending" on fundamentals/valuation/macro. Backend down →
  per-panel error notices plus the admin health card; nothing is estimated.
- **No decorative data.** No chart is drawn from a single price date. No
  button promises an action the GET-only UI cannot perform: alert
  lifecycle and report approval exist only in the CLIs, and the pages say
  so. The watchlist is labelled "this browser only" everywhere it appears.
- **Keyboard and accessibility.** Skip link, tab order through nav/search/
  tabs/selects, labelled inputs, `tablist`/`tab` roles with `aria-selected`,
  `aria-pressed` watch buttons, sr-only table captions, `alert`/`note`
  roles on notices, and a working theme toggle. Keyboard flow is covered
  by a suite test.
- **Honesty labels hold.** SIMULATED on portfolios, DRAFT on reports,
  WITHHELD on decisions, abstained on forecasts, UNVERIFIED badges on
  values, in-app-only on alerts — all present in the rendered UI, not just
  in docs.

## Issues found during this audit and fixed

1. **API prefix missing (product bug).** The frontend called product paths
   without `/api/v1`, so every data panel 404'd while `/health` worked.
   Fixed centrally in `ApiClient.get()`; `/health` stays unprefixed.
2. **Stale footer (product text bug).** The site footer still claimed "no
   market data is shown on this site yet" on every page. Rewritten to the
   honest disclaimer.
3. **Watchlist infinite loop (product bug).** `useSyncExternalStore`'s
   snapshot returned a fresh array on every call → React error #185 on the
   companies page. Fixed with a raw-string-keyed snapshot cache.
4. **Screener run field (product bug).** The page read `run.*`; the API
   returns `latest_run.*`. Matched/universe columns showed "—". Fixed.
5. **Unknown ticker guessed a page (product bug).** Any non-numeric key was
   treated as a ticker. Now a ticker must exist in the registry, else the
   page shows only the unresolvable banner.
6. **Stale-server trap (run note, not a product bug).** Playwright's
   `reuseExistingServer` silently reused a manually started `next start`
   serving an older build, which masked fixes across runs. Before running
   the suite, kill any process on port 3000 so the suite starts a fresh
   server from the current build.

## Remaining UX limitations (by design, stated in the UI)

- No charts: one price date is not a series.
- No alert lifecycle or report approval actions in the web UI (CLI only).
- Watchlist is local to the browser; no account system exists.
- Company search is by legal name only; ticker lookup goes through the
  Securities page or direct detail URLs.
- Backend CORS allows only ports 3000 (localhost and 127.0.0.1); serving
  the frontend on any other port blocks API calls with a CORS error. This
  bit once during debugging (port 3001) and is worth knowing for any
  future deployment: the allowed origins live in the backend config, not
  in the frontend.
