# Phase 4 — Frontend Documentation

## Page: /companies

`frontend/app/companies/page.tsx` (client component, following
the existing `ApiStatus` pattern with `ApiClient` + `getApiBaseUrl`).

- Fetches `/companies?limit=50` and `/registry/statistics` from
  the backend. Renders ONLY the rows returned.
- States, shown explicitly with a Badge:
  - "Checking registry…" while loading.
  - "Registry unavailable" when the backend cannot be reached
    (description changes to say so; no data is shown).
  - "Registry connected — N companies, M securities, K sectors"
    when up. (Audit LOW finding fixed: the page previously
    fetched statistics and discarded them; the counts are now
    displayed.)
- Table columns: Company (legal name), Sector (source taxonomy,
  shown as "name (source)" or "Unavailable"), Status, Securities
  (count). Empty table: "No registry records yet" with the
  explanation that nothing is shown rather than placeholder
  companies, prices, or ratings.
- No price chart is shown on this page in Phase 4 (the Phase 2
  foundation chart container with `series={null}` was removed
  from this page because it implied a price view the registry
  does not provide; price charts belong to Phase 5/6).

## Verified behaviour

- `npm run typecheck`, `npm run lint`, and `npm run build` all
  pass. The /companies route builds and renders.
- Live preview URL: UNVERIFIED (the supplied github.dev URL
  returns only a GitHub sign-in page, as in Phases 2–3; no
  GitHub password was asked for or entered). The live route
  evidence is the backend API check plus the successful build;
  a browser-rendered screenshot was not obtained by a generic
  subagent (no live browser) and is recorded as a parent check
  if a visual confirmation is required.

## What is NOT on the frontend

- No company descriptions, prices, ratings, or recommendations
  (none exist in the registry).
- No search/filter UI beyond the API's query parameters in
  this phase; the API supports search/filter, the page lists
  the first 50 companies. Search UI is a later-phase addition,
  not a Phase 4 claim.
