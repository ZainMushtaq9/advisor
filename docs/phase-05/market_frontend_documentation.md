# Phase 5 — Market Frontend Documentation

## Pages

- `/market` (`frontend/app/market/page.tsx` +
  `frontend/app/market/loading.tsx`): read-only market page
  mirroring the companies page pattern exactly — same
  `ApiClient`, `FoundationShell`, `DataTable`, and `Badge`
  components, no new pattern invented. It renders only API
  rows from `GET /api/v1/market/status` and
  `GET /api/v1/market/prices`, with truthful empty states
  (no observations ingested yet) and unavailable states (API
  unreachable / DB unconfigured). No fabricated prices,
  charts, or ratings are rendered.
- Navigation: `/market` is registered in
  `frontend/lib/nav.ts` ("Market — Daily OHLCV for snapshot
  securities, from validated observations only."), added by
  the Phase 5 coordinator after the implementer's page (the
  implementer left nav.ts untouched as outside its owned
  files). The page is reachable at `/market` with or without
  the nav entry.

## Verification (this phase)

- Frontend typecheck clean, lint clean, `next build`
  succeeds with `/market` in the route list (implementer run).
- Coordinator re-ran typecheck + lint after the nav edit:
  clean, exit 0.
- No frontend change was made to the Gemini agent, Shariah /
  scenario modules, or deployment files (none exist in the
  frontend scope touched here); dashboard/research/portfolio/
  alerts/admin shells are untouched.

## Limits

- The page shows stored observations only. With production
  `market_prices` at 0, it shows the empty state — that is
  correct behaviour, not a missing feature.
- No charting, forecasting, or recommendation UI is included
  in Phase 5; those belong to later phases and must not be
  built on an empty observation set.
