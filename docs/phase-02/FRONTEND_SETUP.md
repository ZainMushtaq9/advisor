# PSX Intelligence AI — Frontend Setup (Phase 2, Team B)

> Scope: frontend foundation only. No market data, forecasting, AI agents,
> or Phase 3 functionality is included. Every route is a clearly labelled
> foundation shell. PKR 0: every dependency below is free/open-source, no
> purchase, sign-up, credential, or secret is involved.

## 1. What was built

A real Next.js App Router application in `frontend/`, following the Phase 1
stack (`docs/phase-01/TECH_STACK_DECISIONS.md`, `SYSTEM_ARCHITECTURE.md`):
Next.js + React + TypeScript (strict) + Tailwind CSS v4 + a shadcn/ui-style
component pattern (components copied into the repo; no shadcn runtime
dependency was added in this phase) + TradingView Lightweight Charts as a
renderer only.

- **Routes (all foundation shells, no market data):** `/`, `/dashboard`,
  `/companies`, `/research`, `/portfolio`, `/alerts`, `/admin`, plus a
  global error page (`app/error.tsx`) and 404 page (`app/not-found.tsx`).
  Each route renders through `components/foundation-shell.tsx`, whose
  banner states the page is structure only and shows no prices, indices,
  company financials, forecasts, or recommendations.
- **Reusable components:** `site-header` / `site-footer` (navigation from
  the single source of truth in `lib/nav.ts`), `theme-provider` /
  `theme-toggle` (dark navy/neutral theme, default dark, stored locally),
  `ui.tsx` (Card, Badge, LoadingState, EmptyState, ErrorState),
  `data-table.tsx` (generic accessible table with an explicit empty state),
  `chart-container.tsx` (Lightweight Charts line renderer; renders an
  empty state when no series is supplied — Phase 2 pages pass `null`),
  `error-boundary.tsx`, `api-status.tsx` (one-shot `/health` probe that
  reports "Backend not connected yet" when nothing answers).
- **API service layer:** `lib/api.ts` — typed `ApiClient` (fetch, timeout,
  typed errors, `health()` returning `null` when unreachable). It points
  at `NEXT_PUBLIC_API_URL` via `lib/env.ts` and sends no credentials.
- **No fabricated data:** no prices, index values, tickers with values, or
  company financials appear anywhere in the frontend source. Tables and
  charts render empty states only. The one test chart point type
  (`ChartPoint`) is market-neutral and is never populated on any page.
- **Chart licence duty (Phase 1):** the TradingView attribution logo is
  left enabled (it is not disabled in `chart-container.tsx`), and pages
  using the chart link to tradingview.com.

## 2. How to run it

From `frontend/`:

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # production build (also runs TypeScript checks)
npm run start      # serve the production build
npm run typecheck  # tsc --noEmit
npm run lint       # eslint
npm run test       # vitest run (unit + component tests)
npm run test:watch # vitest in watch mode
npm run format     # prettier --write .
npm run format:check
```

## 3. Environment variables

Copy `.env.example` to `.env.local` to override. Public values only — never
put keys, tokens, or passwords in frontend env vars, and no backend secret
is hard-coded anywhere.

| Variable | Default | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI backend base URL. Invalid or non-http(s) values fall back to this local default (`lib/env.ts`). |
| `NEXT_PUBLIC_APP_NAME` | `PSX Intelligence AI` | Public display name. |

The backend is built by another team; until it serves `/health`, the home
page badge correctly reads "Backend not connected yet".

## 4. Versions pinned (Phase 1 gate G-04, frontend deps)

Installed with npm on 2026-11-04; exact installed versions below (licences
read from each package's own `package.json` in `node_modules/`).
`package.json` uses caret ranges for most entries; `package-lock.json`
(9,184 lines) is the exact pin record. Runtimes verified on this machine:
Node v24.22.1, npm 10.9.4, Python 3.12.3 (not used by the frontend).

| Package | Installed version | Licence (as shipped) |
| --- | --- | --- |
| next | 16.4.5 | MIT |
| react | 19.3.0 | MIT |
| react-dom | 19.3.0 | MIT |
| typescript | 5.9.3 | Apache-2.0 |
| tailwindcss | 4.3.4 | MIT |
| eslint | 9.39.5 | MIT |
| eslint-config-next | 16.4.5 | MIT |
| lightweight-charts | 5.2.1 | Apache-2.0 |
| clsx | 2.1.1 | MIT |
| tailwind-merge | 3.7.0 | MIT |
| prettier | 3.9.10 | MIT |
| vitest | 3.2.4 | MIT |
| @testing-library/react | 16.3.0 | MIT |
| @testing-library/jest-dom | 6.9.1 | MIT |
| jsdom | 27.2.0 | MIT |
| @types/node | 20.19.43 | MIT |
| @types/react | 19.3.0 | MIT |

Notes on choices:

- Scaffolding: official `create-next-app` (template `app-tw`), run
  non-interactively with `--typescript --tailwind --eslint --app
  --import-alias "@/*" --use-npm`.
- Tailwind v4 is CSS-first: the theme lives in `app/globals.css`
  (`@theme` navy scale + `@custom-variant dark` for class-based dark mode).
  There is no `tailwind.config.js` in v4, by design.
- shadcn/ui primitive caution (Phase 1 §2.2): no shadcn CLI was run in
  this phase, so no primitive choice had to be recorded; the `cn()`
  helper (`clsx` + `tailwind-merge`) and the component layout follow the
  shadcn/ui pattern and are ready for copied-in components later.
- Playwright (Phase 1 E2E choice) was **not** installed in this phase:
  the frontend test setup is Vitest + Testing Library, which covers the
  foundation scope. Adding Playwright E2E against local dev is a
  follow-up, not a gap in the unit/component setup.
- One dependency-resolution note: `vitest@latest` (5.x) conflicted with
  the scaffold's `@types/node@^20` peer range, so Vitest was pinned to
  3.2.4 and `@testing-library/jest-dom` to 6.9.1, which resolve cleanly
  without `--force` / `--legacy-peer-deps`.

## 5. Verification performed (2026-11-04)

| Command | Result |
| --- | --- |
| `npm run typecheck` (`tsc --noEmit`, strict) | PASS, no errors |
| `npm run lint` (`eslint`) | PASS after one fix: the theme provider's one-time localStorage read initially tripped `react-hooks/set-state-in-effect`; it now carries a justified `eslint-disable` comment (browser-only hydration read, default matches the server render) |
| `npm test` (`vitest run`) | PASS — 3 files, 11 tests (env URL resolution, API client success/failure/unreachable, component empty states + shell notice) |
| `npx prettier --check app components lib tests` | PASS |
| `npm run build` | PASS — compiled in ~17s, TypeScript clean, 10 static pages. Route list: `/`, `/_not-found`, `/admin`, `/alerts`, `/companies`, `/dashboard`, `/portfolio`, `/research` (all prerendered static) |
| Dev-server smoke check (`next dev -p 3100`, curl) | PASS — `/`, `/dashboard`, `/companies`, `/research`, `/portfolio`, `/alerts`, `/admin` all HTTP 200 and each contains the "Foundation shell" banner; `/no-such-route` correctly HTTP 404. Server stopped afterwards. |

## 6. Structure

```text
frontend/
├── app/                  # routes, layout, globals.css, error.tsx, not-found.tsx
│   ├── page.tsx          # / (home)
│   ├── dashboard/ companies/ research/ portfolio/ alerts/ admin/
│   │   └── page.tsx + loading.tsx
├── components/           # header, footer, theme, foundation-shell, ui,
│                         # data-table, chart-container, error-boundary, api-status
├── lib/                  # env.ts, api.ts, types.ts, nav.ts, utils.ts
├── tests/                # env, api-client, components tests
├── .env.example          # public vars only
├── vitest.config.ts      # jsdom, @/ alias, tests/ only
├── .prettierrc.json      # printWidth 80, 2-space, trailing commas
└── README.md             # frontend run guide
```

## 7. Explicitly NOT done (out of scope, for later phases)

- No backend, database, deployment, or root README/`.gitignore` changes
  (other teams own those; they were only read, not touched).
- No data fetching beyond the `/health` probe shape, no charts with real
  series, no forecasting, no AI agents, no trading/execution path, no
  authentication, no sign-ups, no purchases.
- Nothing was committed to git.
