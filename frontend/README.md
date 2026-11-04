# PSX Intelligence AI — Frontend (Phase 2 Foundation)

Next.js (App Router) + React + TypeScript + Tailwind CSS foundation shell.
**No market data is shown yet.** Every route is a clearly labelled foundation
shell; real data arrives only in later phases, from verified sources.

## Run

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # production build
npm run start      # serve the production build
npm run typecheck  # tsc --noEmit
npm run lint       # eslint
npm run test       # vitest run
npm run format     # prettier --write .
```

## Environment

Copy `.env.example` to `.env.local` to override. Public values only — never
put keys, tokens, or passwords in frontend env vars.

| Variable               | Default                 | Purpose                                                                                     |
| ---------------------- | ----------------------- | ------------------------------------------------------------------------------------------- |
| `NEXT_PUBLIC_API_URL`  | `http://localhost:8000` | FastAPI backend base URL (Phase 2 default: local dev server; backend built by another team) |
| `NEXT_PUBLIC_APP_NAME` | `PSX Intelligence AI`   | Public display name                                                                         |

## Routes (all foundation shells, no market data)

| Route        | Purpose                   |
| ------------ | ------------------------- |
| `/`          | Home / overview           |
| `/dashboard` | Market overview shell     |
| `/companies` | Company directory shell   |
| `/research`  | Research workspace shell  |
| `/portfolio` | Portfolio workspace shell |
| `/alerts`    | Alerts workspace shell    |
| `/admin`     | Operator workspace shell  |

## Structure

- `app/` — App Router routes, layout, global error / 404, loading states
- `components/` — `site-header`, `site-footer`, `theme-provider`, `theme-toggle`,
  `foundation-shell`, `ui` (Card, Badge, LoadingState, EmptyState, ErrorState),
  `data-table`, `chart-container`, `error-boundary`, `api-status`
- `lib/` — `env` (safe API URL resolution), `api` (typed fetch client),
  `types` (shared API shapes), `nav`, `utils` (`cn`)
- `tests/` — Vitest + Testing Library (env, API client, components)

## Design

Dark navy / neutral financial theme (Tailwind v4, class-based dark mode,
default dark). Charts use TradingView Lightweight Charts as a renderer only,
with its attribution logo left enabled; it supplies no market data.

Full setup record: `../docs/phase-02/FRONTEND_SETUP.md`.
