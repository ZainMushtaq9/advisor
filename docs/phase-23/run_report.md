# Phase 23 — Frontend Product Experience and Complete Dashboard Integration

## Verdict

PARTIALLY COMPLETE (see "Gate judgement" below).

## Entry-check repair (blocking, fixed first)

Live probing found a real API regression from the surrogate-id shift: after
the post-VM-replacement registry import (HUBC 759 / NML 864 / OGDC 873 /
HBL 747), `/fundamentals/ratios` returned `no_configured_period` and
`/valuations` returned `no_inputs` for every company, because Phase 8/9/10
config dicts were keyed by the OLD surrogate ids (289 / 394 / 403 / 277).
Config is now keyed by TICKER in every affected module and live ids are
resolved from the database by ticker at request/run time:

- `fundamental_analysis` (`__init__`, `coverage`, `runner`), `valuation`
  (`__init__`, `coverage`, `runner`), `macro_analysis` (`__init__`,
  `runner`), `news_events` (`__init__`), `rag` (`__init__`, `runner`),
  `backtesting` (`runner`), `scripts/run_fundamental_analysis.py`,
  `scripts/run_valuation.py`, and the Phase 8/9/10 tests.
- No stored row was changed. Dry-runs write 0 rows.
- Verified live after the fix: HUBC ratios assessed (36 metrics, 32
  computed, gross margin 0.417400); HUBC valuations 17 methods (trailing P/E
  5.1552535, book total 258,007,509,000, owners 235,381,655,000 — matching
  Phase 9 exactly); macro exposures HUBC 1 / NML 3 / OGDC 2; HBL pending on
  all three endpoints (correct).
- Backend suite: 348 passed (same count as Phase 22; one test updated for
  the ticker-keyed exposure seeds).

## What was built

- Full product IA in `lib/nav.ts`: Home, Dashboard, Companies, Market,
  Securities, News, Fundamentals, Valuation, Macro, Technical, Forecasts,
  Risk, Portfolio, Screener, Alerts, Reports, Research, Admin.
- Company detail route (`/companies/[key]`, by registry id or ticker) with
  seven tabs: Overview, Fundamentals, Valuation, Macro, Ownership &
  actions, Risk, News & reports.
- Report detail route (`/reports/[id]`) with sections in template order
  plus the figure table (kinds, computation statuses, no value for
  non-computed figures).
- Shared honesty layer: `lib/format.ts` (display-only formatting, missing
  stays missing), `components/data-states.tsx` (PageHeader with banners,
  loading/error/empty notices, quality and computation-status badges,
  source/date/unit/quality lines), `lib/use-api.ts` (GET-only fetch hook
  with loading/ready/error states), `lib/watchlist.ts` (localStorage-only
  watchlist, explicitly labelled "this browser only" — no account system
  exists, so no server watchlist is claimed).
- Every screen states its limits where the data appears: UNVERIFIED badges,
  single trading date, 3/470 statement coverage, HBL pending, 0 calculable
  technical values, 120 abstained forecast assessments, WITHHELD decisions,
  NOT_RUNNABLE backtests, fallback-only agents, vector retrieval not
  implemented, DRAFT-only reports, in-app-only alerts, SIMULATED portfolios.
- No chart is drawn from a single price date (a one-point chart would imply
  a series that does not exist). No decorative data, no fabricated chart
  points, no nonfunctional buttons: lifecycle actions (alert
  acknowledge/mute, report approval) exist only in the CLIs, not in this
  GET-only web UI, and the pages say so.
- GET-only API use throughout (backend CORS allows GET only). No
  credentials anywhere in the frontend.

## What computed vs what did not

Computed (live from APIs): registry 470/470/37; prices 444 on 2026-11-03;
breadth (coverage 94.468085%, median volume 54,631.5, top-10 share
49.249694%); fundamentals 108 values; valuations 51 rows (7 computed);
macro 12 indicators, 1 regime (tightening), 4 events, 6 exposures; risk 81
values (46 computed); decisions 4 (user-facing WITHHELD); portfolios 3
(reconciled); screener 1,418 results (241 MATCH); alerts 89; reports 22
(DRAFT); RAG 943 chunks, benchmark r3 6/6 (page level).

NOT_CALCULABLE / absent (shown as such, never numbered): all technical
values; advances/declines/turnover breadth; share-count and DCF/DDM/peer
valuation methods; all forecasts; series risk metrics; mean-variance;
all backtest metrics; vector retrieval; universe-wide news coverage;
HBL fundamentals/valuation/macro/documents (pending).

## Tests

- Backend suite: 348 passed.
- Frontend unit tests (vitest): 11 passed.
- ESLint on all new/changed frontend files: clean.
- Production build (`next build --webpack`): 23 routes, all pages present,
  dynamic routes as partial prerender. Note: the default Turbopack build
  fails in this worktree because `frontend/node_modules` is a symlink to
  the main worktree's install, which Turbopack refuses to resolve; the
  webpack builder follows the symlink and succeeds. This is a worktree
  artifact, not a code defect.
- Playwright suite (`playwright.phase23.config.ts`, desktop + mobile):
  22 passed (11 specs × 2 projects), 0 failed, in 28.6 s. Coverage: home
  figures + full nav, companies search → detail fundamentals (gross margin
  0.4174 live), HBL pending, market search (HUBC 197.24), screener matches
  (194) + disclaimer, alerts in-app-only, reports DRAFT → detail sections,
  unknown-ticker honest error, keyboard navigation, forecasts abstention,
  portfolio SIMULATED + reconciliation. Issues found by the suite and fixed
  are listed in `docs/phase-23/ux_audit.md` (API prefix, footer text,
  watchlist loop, screener field, unknown-ticker handling, stale-server
  trap).

## UX audit

See `docs/phase-23/ux_audit.md`.

## DB counts before/after

No database writes were made by Phase 23 work (entry-check repair used
dry-runs only; the frontend is read-only). All Phase 22 counts unchanged.

## HBL pending

HBL remains pending: its CY2025 annual report PDF could not be downloaded
(issuer-site bot-management challenge) and the live-browser download runs
separately. The product is designed so a 4th company joins without
redesign: fundamentals/valuation/macro tabs, the ticker selectors and the
company detail page all resolve by ticker and already render HBL's pending
state correctly.

## Gate judgement

PARTIALLY COMPLETE, not COMPLETE, because the acceptance gate's "every
visible control performs its advertised action" and "all displayed
production data comes from APIs" hold, but the underlying production data
itself remains limited exactly as Phases 4–22 recorded it: UNVERIFIED
inputs, 3-company statement coverage, abstained forecasts, WITHHELD
decisions, NOT_RUNNABLE backtests, fallback-only agents, vector retrieval
not implemented, DRAFT-only reports, HBL pending. Forcing COMPLETE would
misrepresent those limits as resolved. No new blocker was introduced by
Phase 23 itself; the entry-check regression it found and fixed is the only
correctness change to earlier-phase code.

## Remaining blockers (with exact unblockers)

- Written PSX permission evidence (user-owned) — unlocks GEM/Non-Compliant
  capture, full-470 verification, and any new PSX collection.
- More trading days (Terms-gated) — unlocks technical values, forecasts,
  backtests, and series risk metrics.
- HBL CY2025 PDF via the live-browser download — unlocks the 4th company
  across fundamentals, valuations, macro, news, risk, decisions,
  portfolios, backtests, RAG, screener, alerts and reports.
- A verified local embedding model — unlocks vector retrieval.
- An internal review decision — unlocks the first APPROVED report (CLI
  transition only; no web approval exists by design).
