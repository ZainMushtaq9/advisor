# PSX Intelligence AI — Website Module Specification (Phase 1 of 30)

> **Coordinator audit correction, 2026-11-04 (documentation only, no code changed):** References in this file to an agent registry covering "Agents 1–6 only" (notably §0/§4, the per-module agent dependencies, and the UNVERIFIED list at §5, plus the "Phase 16/Phase 22" phase references for agent registration and API routes) are SUPERSEDED by the canonical sibling specs: `AGENT_REGISTRY.md` registers all 18 agents plus the orchestrator, and the canonical 30-phase list is in `docs/phase-01/MASTER_ROADMAP.md` / `PHASE_BREAKDOWN.md` (Phase 22 is Investment recommendation engine, not API-route fixing; backend/API foundations are Phase 05, frontend integration is Phase 28). Read this file's agent dependencies against that 18-agent registry. Forecasting, valuation, risk, screening, optimisation, alerts, report-narrative, orchestration and news-ingest functions are therefore NOT unregistered — they are registered, with the UNVERIFIED status applying only to their external data feeds, not to their registry entries. No other content in this file was changed by this correction.

> **Team 9 — Website Module Specification + User Workflow. Phase 1 only.**
> This file is a specification. It delivers no application code, no running
> website, no database, and no later-phase implementation. Tiny illustrative
> snippets, if any, are specification illustrations only, not application code.
> This file was written by Team 9 alone; sibling teams' files were not
> modified, and `~/workspace/psx-data-collection/` was used as reference only
> and was not touched.

## File header — stage status (honest record)

The 11-stage workflow required for this work, with the status of each stage
at the time this file was written (2026-11-04):

| # | Stage | Status |
|---|-------|--------|
| 1 | Brainstorm | DONE — 21 website modules derived from the assigned product scope; no module added or dropped. |
| 2 | Research | DONE — public-web / sibling-spec reading only. No sign-up, install, purchase, credential, or API key was used. |
| 3 | Validate | DONE against the verified starting condition below; every claim that could not be verified is marked UNVERIFIED, not asserted. |
| 4 | Data inspection | DONE, READ-ONLY ONLY — directory listings and sibling Phase 1 spec headings were read. No full-scale live data collection was performed in Phase 1, no live polling was performed, and no price, quote, or company record is asserted in this file. |
| 5 | Architecture planning | DONE — modules are aligned to the fixed stack and to the sibling System Architecture / Database Design / Agent Registry specs; where those specs do not yet cover a need, the gap is named as an open dependency. |
| 6 | Implementation specification | DONE — this file. It specifies what later phases must build; it does not build it. |
| 7 | Documentation | DONE — this file, plus the companion `USER_WORKFLOW.md` by the same team. |
| 8 | Testing strategy | DONE — how each module WILL be tested in later phases. No test is claimed to have passed, because no code exists to test in Phase 1. |
| 9 | Independent audit | NOT DONE — reserved for the coordinator / independent audit in Phase 1 close-out (and Phase 23). This file has not been independently audited. |
| 10 | Correction | PENDING — corrections will be applied only after audit findings are issued; none are pre-claimed here. |
| 11 | Checkpoint | PENDING — Phase 1 is complete only when the coordinator audit passes. This file alone does not close Phase 1. |

## 0. Verified starting condition (2026-11-04, reused, not re-claimed)

- Tools verified in the environment: Python 3.12.3, Node v24.22.1.
  Docker, `psql`, and `redis-cli` are NOT installed.
- Fixed stack (no substitution in this spec): Next.js / React / TypeScript /
  Tailwind / shadcn (website), Python / FastAPI / Pydantic (API),
  PostgreSQL / SQLAlchemy / Alembic (database; SQLite for local dev only,
  per sibling stack decisions), local filesystem + Apache Parquet +
  optional self-hosted MinIO, Redis, Ollama local open-weight inference
  only, Pandas / NumPy / scikit-learn / statsmodels / PyTorch where
  justified, PyMuPDF / pypdf / Tesseract, Pytest / Playwright,
  Git / GitHub Free / Docker Engine / local dev.
- Budget: **PKR 0 absolute zero-cost.** No paid API, subscription, hosting,
  database, storage, monitoring, or AI/LLM subscription is specified,
  assumed, or required by any module below. Local hardware, electricity,
  and internet are **external operating expenses** — they are disclosed
  here and are never described as "free". No permanent free hosting is
  assumed to exist; any deployment option in later phases must be
  re-verified at that time and must still meet PKR 0 or be separately
  approved before any spend.
- Verified data sources (the only market-data sources this spec may rely on):
  - **psx-dps** — MIT licence, zero dependencies, no API key, ~496 trading
    symbols vs ~1029 listed, ~5 years of end-of-day (EOD) data, today's
    ticks, 38 sectors, multi-node 404 quirk, and **no official PSX API**.
  - **psxdata** — MIT licence, PyPI, alpha 0.1.0a1, daily OHLCV + live
    snapshots ONLY, **no historical intraday archive**.
  - **Eulerpool: NO PSX coverage** — vendor only; it is not a data source
    for this system and no module below depends on it.
- **UNVERIFIED — never treated as available:** machine-use of SECP, SBP,
  PBS, Finance Division, World Bank, IMF, and FRED. No endpoint, feed,
  field, or coverage claim for any of them appears in this spec. Any module
  that would need them lists the need as UNVERIFIED and degrades
  gracefully (see §2 and each module's "UNVERIFIED" note).
- **No official PSX API is verified.** `psx-dps` / `psxdata` are
  third-party libraries, not an official PSX API, and must never be
  described as one.

## 1. System-wide rules every website module must obey

1. **No real trades, ever, in Phase 1 scope and in the initial system.**
   The system must NOT execute real trades initially, must NOT connect to
   a broker, and must NOT place, amend, or cancel any order. Every
   BUY / HOLD / SELL / WATCHLIST label is a **probabilistic recommendation
   with uncertainty shown**, for information only. Every screen that could
   suggest a trade-like action must carry that restriction in the UI
   (see also `USER_WORKFLOW.md`, which repeats it at each such step).
   There is no "Buy", "Sell", "Place order", or "Execute" control anywhere
   in this specification.
2. **Forecasts are probabilistic, never guaranteed.** No module may show a
   point forecast, target, or return without its uncertainty interval /
   confidence band, its model name and version, its input-data date range,
   and its limitations. Past performance is never presented as a promise
   of future results.
3. **Deterministic numbers only from deterministic code.** All financial
   calculations (ratios, indicators, valuations, scores, portfolio maths)
   are deterministic Python functions over stored, validated records.
   **LLMs never invent numbers.** An LLM / Ollama narrative may only cite
   numbers already computed and stored, with the source record identified;
   if a number is not stored, the narrative must say it is unavailable,
   not fill it in. Narrative text and computed numbers must be stored
   separately so a reviewer can check one against the other.
4. **Provenance and freshness on every data display.** Every market,
   financial, news, or macro value shown must be accompanied (on the
   screen, or one click away in a provenance panel) by: source library /
   source name, retrieval / as-of date and time (PKT), data vintage
   (EOD date, snapshot time), and a freshness label — current, stale,
   or missing. Stale or missing data must never be silently displayed
   as current.
5. **No live polling.** The website does not poll a market feed
   continuously. "Today's" data means the latest snapshot / tick batch
   obtained by the scheduled collector (Phases 5–6), labelled with its
   capture time. Any module described as "live" in ordinary language
   means "latest stored snapshot", and its UI must say so.
6. **No invented API, endpoint, price, or capability.** Internal API
   needs below are described by the data they must return, not by
   invented routes. Exact internal routes are fixed in Phase 22
   (Internal API Layer); this spec invents none. No price, index level,
   exchange rate, or company figure is stated anywhere in this file.
7. **Zero-cost enforcement.** A module feature that would require a paid
   service (paid market feed, paid news feed, SMS gateway, push provider,
   hosted database, paid monitoring, paid LLM API) is specified as
   **in-app only, or deferred as UNVERIFIED**, never as a paid
   integration. Ollama inference is local open-weight only; no
   cloud LLM subscription is specified.
8. **Accessibility, language, and honesty.** UI text must be plain and
   checkable. Any value that is an estimate, a model output, or from an
   unverified source must be labelled as such. No dark pattern may steer
   a user toward a recommendation; recommendations always show the
   reasons and the uncertainty alongside the label.
9. **Security by default (specification level).** Authentication, roles,
   audit logging, and input validation are specified per module below;
   they are implemented in Phases 20–21 and 27, not claimed as done here.
   No credential, secret, API key, or personal datum is included in
   this file.

## 2. Cross-module data and freshness model

All 21 modules read **validated, stored data only** — never a live
third-party call from the browser. The read path, in specification terms,
is: website (Next.js) → internal API (FastAPI, Phase 22) → validated
store (PostgreSQL / Parquet / local filesystem, Phases 2–4) → collector
provenance (Phases 2, 5, 6). If the validated store has no row, the
module shows an empty / unavailable state (see §3), never a fabricated
value and never a direct browser call to an external site.

| Data class | Verified source in Phase 1 | Freshness rule for the UI |
|---|---|---|
| Listed / trading symbols, sectors | psx-dps (~496 trading vs ~1029 listed, 38 sectors) | Labelled with collector run date; trading vs listed distinction always shown |
| Daily OHLCV, ~5y EOD | psx-dps; psxdata (daily OHLCV) | EOD date shown; "latest EOD" is a date, not "now" |
| Today's ticks / snapshots | psx-dps today's ticks; psxdata live snapshots ONLY | Snapshot capture time (PKT) shown; never called "real-time" without that timestamp |
| Historical intraday | NONE verified | Module must show "not available" — never synthesised from daily data |
| Financial statements (structured) | NONE verified as a machine source in Phase 1 | UNVERIFIED — see Module 6; PDF/manual-ingest path only if separately verified in Phase 7 |
| News / announcements (machine feed) | NONE verified as a machine feed in Phase 1 | UNVERIFIED — see Module 10; no feed is assumed |
| Macro / regulator data (SECP, SBP, PBS, Finance Division, World Bank, IMF, FRED) | NONE verified for machine use | UNVERIFIED — see Modules 6, 9, 11; fields gated, never populated by guesswork |
| User-entered data (watchlists, manual portfolios, journals, alerts, screens) | User input, stored locally | Shown as user-entered, with entry date; never mixed with market data without a label |

The psx-dps multi-node 404 quirk is a collector concern (Phases 2, 5, 6):
the website must surface its consequence — a symbol / date that failed
to fetch — as "data unavailable for this date (collector note)", not as
a zero price and not as a gap silently interpolated.

## 3. Shared UI patterns (specified once, reused by all modules)

- **Provenance panel:** source, as-of timestamp, vintage, freshness label,
  and collector / validation status, on every data-bearing screen.
- **Empty / stale / missing states (mandatory, not optional polish):**
  no data → "No validated data available for this selection yet" +
  what the user can do (change date range, check back after the next
  scheduled refresh); stale data → amber banner with the last-good date
  and "figures may be out of date"; UNVERIFIED source → "This field
  depends on a source not yet verified for machine use and is not shown
  as fact" — the field is hidden or greyed, never filled with a guess.
- **Uncertainty display:** forecasts and recommendations always show a
  band / range and a "What this does / does not mean" note.
- **No-trade banner:** any screen showing a BUY / HOLD / SELL /
  WATCHLIST label carries: "Probabilistic recommendation for information
  only. This system does not execute trades and is not connected to a
  broker."
- **Export / report honesty:** any export or generated report carries the
  same provenance, as-of date, and uncertainty notes as the screen it
  came from; an export is a snapshot, not a live document.
- **Error handling:** a failed internal read shows a retry action and a
  plain-language error; it never shows a partial chart as if complete,
  and never falls back to invented data.

## 4. Module specifications

Each module below follows the same structure: Objective; Features;
User interactions; Required data / APIs; DB dependencies; AI agent
dependencies; Security; Testing strategy (later phases — nothing is
claimed as passed); Acceptance criteria.

Agent-dependency note that applies to all modules: the sibling
Phase 1 Agent Registry currently registers Agents 1–6 only
(Market Data; Company Discovery; Historical Research; Financial
Statement; Fundamental Analysis; Technical Analysis). A module that
needs an agent function beyond those six names the function as
**required but not yet registered** — an open dependency for Phase 16
(Multi-Agent Orchestration), not an assumed capability. No agent number,
tool, or behaviour beyond the registry is invented here.

---

### Module 1 — Landing Page

- **Objective:** Explain, in plain language, what PSX Intelligence AI is
  and is not, who it is for, and what data it actually covers — before
  any registration — so a first visitor is not misled about coverage,
  freshness, or trading.
- **Features:** Product summary; coverage statement (~496 trading vs
  ~1029 listed, 38 sectors, ~5y EOD — as verified, with the caveat that
  coverage is as supplied by the verified libraries, not an official PSX
  guarantee); no-trade and probabilistic-forecast disclosures; feature
  tour of the 21 modules; data-source and licence attributions
  (psx-dps MIT, psxdata MIT); sign-in / register entry points; no price
  ticker that implies real-time trading data (any market snapshot shown
  here must carry its snapshot timestamp and freshness label).
- **User interactions:** Read disclosures; navigate to registration /
  sign-in; browse the feature tour. No data entry except navigation.
- **Required data / APIs:** Static marketing copy (stored content, not
  a feed); optional latest-stored market snapshot via the internal read
  path, with timestamp. UNVERIFIED: any live index ticker, any
  "market now" claim — not specified.
- **DB dependencies:** None for the core page (static content). Optional
  snapshot read only, from the validated market store; no write.
- **AI agent dependencies:** None. No agent-generated claim may appear
  on the landing page without a stored, checkable source.
- **Security:** No authenticated data on a public page; no tracking
  beyond what a later, separately approved privacy decision allows
  (none is specified here); links to sign-in must use the auth module's
  flow, not a bespoke login form.
- **Testing strategy (later phases):** Playwright checks that disclosures
  (no-trade, probabilistic, coverage, timestamp) are present and visible
  without scrolling past them; content test that no invented price or
  guarantee wording appears; accessibility check (keyboard navigation,
  headings); link test for register / sign-in routes. No test has been
  run in Phase 1.
- **Acceptance criteria:** (a) A visitor can state, from the page alone,
  that the system does not trade and forecasts are probabilistic.
  (b) Coverage figures match the verified starting condition or the page
  shows no coverage figure. (c) Any snapshot shown carries a timestamp.
  (d) No broker, order, or "buy now" control exists.

### Module 2 — Registration / Authentication

- **Objective:** Let a user create and use a local-first account, with
  roles, so personal data (watchlists, portfolios, alerts, reports)
  belongs to that user and admin functions are separated from ordinary
  use.
- **Features:** Registration, sign-in, sign-out, password change /
  reset (local-first flow, Phases 21 and 27 — exact reset mechanism is
  fixed there, not invented here); session handling; role assignment
  (ordinary user vs administrator, at minimum); profile basics; audit
  record of sign-in / role change. No social-login, broker-login, or
  paid identity provider is specified (PKR 0).
- **User interactions:** Register with the fields the Phase 21 spec
  fixes; sign in; sign out; change password; request a reset. Every
  failure message must not reveal whether an account exists (to be
  fixed in Phase 27 hardening).
- **Required data / APIs:** Internal auth APIs only (routes fixed in
  Phase 22). UNVERIFIED: any external identity provider, email-delivery
  provider for reset messages, or SMS provider — none is assumed; if
  email delivery cannot be provided at zero cost, the reset flow must be
  specified in Phase 21 as an in-app / administrator-assisted path, not
  silently assumed to work.
- **DB dependencies:** User account, credential hash (never plaintext),
  session, role, and audit-log records (schema per sibling Database
  Design; exact tables fixed in Phase 3). No market-data write.
- **AI agent dependencies:** None.
- **Security:** Passwords hashed with a current, approved algorithm
  (fixed in Phase 27); sessions expire; failed-sign-in handling and
  rate limiting specified in Phase 21/27; admin role required for
  Module 21; every role change logged with actor and timestamp.
  No credential is stored in, or readable from, this spec.
- **Testing strategy (later phases):** Pytest unit tests for auth logic;
  Playwright flows for register / sign-in / sign-out / wrong-password /
  expired-session; negative tests (privilege escalation attempt to an
  admin route as an ordinary user must fail); audit-log test that role
  changes are recorded. No test has been run in Phase 1.
- **Acceptance criteria:** (a) An ordinary user cannot reach any admin
  function. (b) No password or session token is ever displayed or
  logged in plaintext. (c) Sign-in failure does not leak account
  existence. (d) Every role change has an audit entry.

### Module 3 — Market Dashboard

- **Objective:** Give a signed-in user a single, honest overview of the
  market as last validated: breadth, sector shape, and latest EOD /
  snapshot state — with freshness visible, not implied.
- **Features:** Latest-EOD summary (date shown); market breadth
  (advancers / decliners / unchanged, computed from validated EOD rows
  only); sector overview across the 38 sectors; top movers by a stated,
  deterministic rule (e.g. largest percentage change on the latest EOD
  date — exact rule fixed by the analytics spec, never a hidden ranking);
  data-health strip (last successful collector run, symbols missing for
  the latest date, stale-data warning if the latest EOD is older than
  the expected refresh); links into explorer, sector, and company pages.
- **User interactions:** View overview; change the reference EOD date
  (within validated range); click through to a sector or company;
  dismiss (not hide permanently) a stale-data banner after reading it.
- **Required data / APIs:** Internal reads for latest validated EOD
  aggregate, sector aggregates, breadth, and collector health. Sources:
  psx-dps / psxdata via Phases 5–6. UNVERIFIED: any intraday breadth,
  any live index level, any macro overlay (SECP / SBP / PBS / Finance
  Division / World Bank / IMF / FRED) — none is shown.
- **DB dependencies:** Validated EOD store; sector mapping; collector-run
  / freshness records. No user write except navigation state, if any.
- **AI agent dependencies:** Agent 1 — Market Data (registered) for the
  validated market picture. Narrative summary, if any, is a Phase 12
  function: it may only restate stored aggregates and must carry the
  as-of date; it must not add a new number.
- **Security:** Signed-in read only; no user data exposed to another
  user; aggregates contain no personal data.
- **Testing strategy (later phases):** Fixture-based tests with a small
  synthetic validated EOD set: breadth arithmetic recomputed by hand
  and compared; stale-date test (old latest EOD → banner appears);
  missing-date test (no rows for the chosen date → empty state, not
  zeros); Playwright screenshot / content checks for timestamp and
  banner presence. No test has been run in Phase 1.
- **Acceptance criteria:** (a) Every figure shows its EOD date.
  (b) Breadth numbers reconcile to the underlying validated rows.
  (c) A stale latest EOD produces a visible warning. (d) No figure is
  presented as "live" without a snapshot timestamp.

### Module 4 — Company Explorer

- **Objective:** Let a user find companies by symbol, name, or sector,
  understand trading vs listed status, and move to a company page —
  without ever implying that an unlisted or suspended symbol is
  tradeable or covered.
- **Features:** Search by symbol / name substring; filter by sector
  (38 sectors); filter by trading vs listed-only status; sort by
  symbol, name, or sector (deterministic, stated sort); result list
  showing symbol, name, sector, trading status, and latest validated
  EOD date for that symbol (or "no validated EOD yet"); pagination for
  the full ~1029-listed set; empty-result state with a suggestion to
  broaden the filter.
- **User interactions:** Type a search; apply / clear filters; sort;
  page through results; click a company to open Module 5.
- **Required data / APIs:** Internal reads for company directory and
  per-symbol latest-EOD availability, from psx-dps-derived directory
  data (Phases 2, 5). UNVERIFIED: any official PSX company directory
  API, any fundamentals field from an unverified source — not used.
- **DB dependencies:** Company directory (symbol, name, sector, status,
  symbol-history handling per sibling Database Design §7); latest-EOD
  pointer per symbol. Read only from the website.
- **AI agent dependencies:** Agent 2 — Company Discovery (registered)
  for directory completeness and symbol-history notes. No agent may add
  a company not present in the validated directory.
- **Security:** Public directory data only; no personal data; search
  input validated and escaped (no query-string injection into any
  later query — fixed in Phase 27).
- **Testing strategy (later phases):** Fixture tests for search
  (substring, case handling as specified in Phase 22), sector filter
  counts reconciled to fixtures, trading-vs-listed filter, pagination
  boundary tests, and empty-result UI test. Playwright test that a
  listed-only symbol is visibly distinguished from a trading symbol.
  No test has been run in Phase 1.
- **Acceptance criteria:** (a) Every listed company in the validated
  directory is findable; no company outside it is shown. (b) Trading
  vs listed-only status is visible on every row. (c) A symbol with no
  validated EOD shows that fact, not a blank price. (d) Search never
  returns a fabricated company.

### Module 5 — Individual Company Intelligence

- **Objective:** Be the single company page that gathers everything
  validated about one symbol — profile, price history, statements,
  analysis, news (if verified), forecast, recommendation, and risk —
  with each section labelled by source and freshness, so the user never
  has to guess which number came from where.
- **Features:** Company header (symbol, name, sector, trading status);
  price chart over validated EOD data (date range selectable within
  the ~5y validated range); key facts panel (each fact sourced);
  section links / embedded summaries for Modules 6–14 (statements,
  fundamentals, technicals, valuation, forecast, recommendation, risk);
  watchlist add / remove (user data only); notes / journal link
  (Phase 14); provenance panel for the whole page; "data unavailable"
  placeholders for any section whose source is UNVERIFIED or empty.
- **User interactions:** Open from explorer / dashboard / screener;
  change chart date range; expand a section; add to / remove from a
  watchlist; open the provenance panel; export the page snapshot as a
  report input (Module 19) — export carries the as-of date.
- **Required data / APIs:** Internal reads aggregating company,
  EOD, statement, fundamental, technical, valuation, forecast,
  recommendation, and risk stores. UNVERIFIED: any field whose source
  is SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED,
  any intraday chart, any official PSX company feed — none is rendered
  as fact.
- **DB dependencies:** Company directory; validated EOD; statement,
  fundamental, technical, valuation, forecast, recommendation, and
  risk result stores; user watchlist. Reads dominate; only the
  watchlist action writes, and only to the signed-in user's records.
- **AI agent dependencies:** Agents 1–6 (registered) for market,
  discovery, history, statements, fundamentals, and technicals;
  forecast / recommendation / risk narrative functions are required
  but not yet registered (Phase 16 dependency). No agent output may
  appear on this page without its underlying stored numbers.
- **Security:** Watchlist actions require sign-in and are scoped to
  the acting user; company data itself is non-personal.
- **Testing strategy (later phases):** Fixture company page tests:
  every section renders with source + date or with an unavailable
  placeholder; chart test with a known EOD fixture (points match the
  fixture exactly); watchlist add/remove round-trip test per user;
  cross-user isolation test (one user's watchlist never appears for
  another). No test has been run in Phase 1.
- **Acceptance criteria:** (a) No section shows a number without a
  source and date. (b) UNVERIFIED sections are placeholders, not
  guesses. (c) Watchlist changes affect only the acting user.
  (d) The no-trade banner is present wherever a recommendation appears.

### Module 6 — Financial Statements

- **Objective:** Present a company's financial statements exactly as
  validated and stored — with period, filing source, and any restatement
  note — and refuse to present a statement that has not been validated.
- **Features:** Statement selector (balance sheet / income / cash flow,
  as the Phase 7 data model fixes — statement types are not expanded
  here by assumption); period selector (annual / interim, only periods
  actually stored); line-item table with units and period labels;
  year-on-year / period-on-period comparison computed deterministically
  from stored rows; restatement / correction notes where the source
  records them; download of the stored statement table (snapshot, with
  provenance); prominent "not available" state when no validated
  statement exists for the company / period.
- **User interactions:** Choose company (via Module 5), statement type,
  and period; expand line items; compare periods; download the table.
- **Required data / APIs:** Internal reads for stored statement rows.
  **UNVERIFIED (blocking): no structured financial-statement machine
  source is verified in Phase 1.** Possible paths — regulator filings,
  company-published PDFs parsed with PyMuPDF / pypdf / Tesseract —
  are Phase 7 verification work, not assumed feeds. Until a source is
  verified, this module's data area is an unavailable state, and the
  module must not be described as populated. Manual, sourced entry is
  only permitted if Phase 7 specifies its validation and provenance
  rules; it is not specified here as a shortcut.
- **DB dependencies:** Statement header + line-item store with full
  provenance block (source document, period, retrieval date, validator
  status) per sibling Database Design §5; company link; no computed
  figure stored without its input row ids.
- **AI agent dependencies:** Agent 4 — Financial Statement
  (registered) for statement extraction / validation logic, within the
  verified-source limit above. An agent must never "complete" a missing
  statement line by estimation without labelling it as an estimate —
  and in Phase 1 scope, missing lines stay missing.
- **Security:** Statement data is company-public data as stored; no
  personal data. Downloads must carry provenance and must not strip
  the unavailable / estimate labels (estimates, if ever allowed in a
  later phase, must travel with the download).
- **Testing strategy (later phases):** Fixture statement tests:
  totals recomputed from fixture line items; period-mismatch test
  (comparing different period types is blocked or clearly labelled);
  unavailable-company test (placeholder, not zeros); provenance test
  (every row traces to a stored source document id). No test has been
  run in Phase 1.
- **Acceptance criteria:** (a) No statement is shown without period,
  source, and validation status. (b) No missing line is filled by
  guesswork. (c) Comparisons use only like-for-like periods or say so.
  (d) The module is honestly empty until Phase 7 verifies a source.

### Module 7 — Fundamental Analysis

- **Objective:** Turn validated statements and market data into
  transparent, reproducible fundamental ratios and commentary — every
  ratio showing its formula, inputs, and period, so a user can recompute
  it.
- **Features:** Ratio set as fixed by the sibling Financial Formulas
  spec (this spec does not invent new ratios here); ratio table per
  company and period; peer / sector comparison using only companies
  with validated data for the same period; trend view across stored
  periods; plain-language interpretation that cites the stored ratios
  (Phase 12 narrative rules apply); "insufficient data" state when
  inputs are missing.
- **User interactions:** Choose company and period; choose a peer set
  (sector peers with data, or a manually chosen set); view a ratio's
  formula and inputs; compare across periods.
- **Required data / APIs:** Internal reads for statement rows
  (Module 6) and EOD market data (for market-based ratios). UNVERIFIED:
  any ratio input from SECP / SBP / PBS / Finance Division / World
  Bank / IMF / FRED, and any statement input whose source is itself
  UNVERIFIED — such ratios are not computed and are shown as
  unavailable, not computed from substitutes.
- **DB dependencies:** Statement store; EOD store; computed-ratio
  store recording formula version and input row ids (so a ratio can be
  audited, not just displayed).
- **AI agent dependencies:** Agent 5 — Fundamental Analysis
  (registered). Narrative interpretation is a Phase 12 function and
  must cite stored ratios only.
- **Security:** No personal data; ratio computation must not expose
  another user's private notes or portfolios.
- **Testing strategy (later phases):** Pytest tests recomputing each
  ratio from fixture inputs by hand and comparing; missing-input test
  (ratio → unavailable, not zero or infinity silently rendered);
  peer-comparison test (only same-period, validated peers included);
  formula-display test (displayed formula matches the computed one).
  No test has been run in Phase 1.
- **Acceptance criteria:** (a) Every displayed ratio is recomputable
  from displayed inputs. (b) Missing inputs yield "unavailable", never
  a silent default. (c) Peer sets state their inclusion rule.
  (d) No interpretation states a number that is not in the ratio table.

### Module 8 — Technical Analysis

- **Objective:** Provide deterministic technical indicators and chart
  overlays over validated EOD data only, with each indicator's
  parameters and data window stated, so a chart is a computation, not
  an impression.
- **Features:** EOD price chart with selectable indicators as fixed by
  the Phase 9 engine spec (this spec invents no indicator list);
  parameter controls within validated ranges; indicator values table
  for the latest validated date; signal notes that are explicitly
  descriptive ("indicator X crossed Y on [date]") rather than
  prescriptive trade instructions; date-range selection within the
  validated range; handling of gaps / missing EOD dates (gap shown,
  not interpolated silently).
- **User interactions:** Choose company, date range, and indicators;
  adjust parameters; hover / inspect a dated value; read the signal
  note and its date.
- **Required data / APIs:** Internal reads for validated EOD series
  and computed indicator series. UNVERIFIED: any intraday indicator
  (no historical intraday archive exists — see §2); any indicator
  computed from unverified data.
- **DB dependencies:** Validated EOD store; computed-indicator store
  (indicator name, parameters, function version, input row ids).
- **AI agent dependencies:** Agent 6 — Technical Analysis (registered).
  Agent narrative, if any, must describe stored indicator values only.
- **Security:** Read-only market data; parameter inputs validated to
  the ranges the Phase 9 spec allows (no arbitrary code or query input).
- **Testing strategy (later phases):** Pytest recomputation of each
  indicator from a small hand-computed EOD fixture; gap test (missing
  date → indicator correctly marked unavailable / restarted per the
  Phase 9 rule, never silently bridged); parameter-boundary tests;
  Playwright chart test that the plotted points match fixture values.
  No test has been run in Phase 1.
- **Acceptance criteria:** (a) Every indicator shows name, parameters,
  and window. (b) Indicator values match deterministic recomputation.
  (c) Gaps are visible. (d) No signal note is worded as an instruction
  to trade.

### Module 9 — Sector Analysis

- **Objective:** Show how each of the 38 sectors is doing on validated
  EOD data — aggregates, breadth within the sector, and leaders /
  laggards by a stated rule — without importing any unverified macro
  story to explain the movement.
- **Features:** Sector list (38, as verified); per-sector aggregate
  (constituent count, trading vs listed-only count, breadth, aggregate
  movement computed by the Phase 8 analytics rule); sector comparison
  table and chart; constituent list linking to Module 5; sector
  history over validated EOD dates; "sector has too few validated
  constituents for a reliable aggregate" warning where the Phase 8
  rule requires it.
- **User interactions:** Choose a sector; compare sectors; choose a
  reference EOD date; drill into a constituent company.
- **Required data / APIs:** Internal reads for sector aggregates and
  constituents from psx-dps-derived sector mapping. UNVERIFIED: any
  sector classification beyond the verified 38-sector mapping, any
  macro / industry data from SECP / SBP / PBS / Finance Division /
  World Bank / IMF / FRED — sector commentary must not cite them.
- **DB dependencies:** Sector mapping; validated EOD; sector-aggregate
  store with constituent list and computation rule version.
- **AI agent dependencies:** Agent 1 — Market Data (registered) for
  aggregates; a dedicated sector-narrative function, if wanted, is
  required but not yet registered (Phase 16 dependency) and must cite
  stored aggregates only.
- **Security:** Aggregates only; no personal data.
- **Testing strategy (later phases):** Fixture tests recomputing a
  sector aggregate from constituent fixtures; constituent-change test
  (a symbol moving sector, per symbol-history rules, changes the
  aggregate only from the effective date); small-constituent warning
  test; Playwright test that the 38-sector list renders completely.
  No test has been run in Phase 1.
- **Acceptance criteria:** (a) Sector aggregates reconcile to
  constituents. (b) The sector list matches the verified mapping or
  states its deviation. (c) No macro claim appears without a verified
  source. (d) Thin sectors carry a reliability warning.

### Module 10 — News / Announcements

- **Objective:** Collect, in one place, only the news and announcements
  that have actually been obtained from a verified source, each with
  its source, publication date, and link to the underlying record —
  and be explicit when there is nothing verified to show.
- **Features:** News / announcement list filtered by company, sector,
  and date; detail view showing headline, source, publication date,
  and a stored summary that does not add facts beyond the source text;
  company linkage only where the source itself names the company;
  "no verified items for this selection" empty state.
- **User interactions:** Browse, filter by company / sector / date,
  open a detail view, follow the source reference (external link, if
  the source record provides one — the website does not re-host
  copyrighted text beyond what the source licence allows; licence
  handling is a Phase 27 matter).
- **Required data / APIs:** Internal reads for stored news /
  announcement records. **UNVERIFIED (blocking): no machine news /
  announcements feed is verified in Phase 1** — no PSX announcements
  API, no press feed, and no scraping target is specified here.
  Until a source is verified (Phase 7 / later data work), this module
  shows the empty state and must not be presented as populated.
  Manual curation, if ever adopted, requires its own provenance and
  approval spec and is not assumed here.
- **DB dependencies:** News / announcement store with full provenance
  (source name, source date, retrieval date, source reference, company
  link basis). No record without provenance may be displayed.
- **AI agent dependencies:** Agent 3 — Historical Research (registered)
  is the closest registered function, but a news-ingest agent is
  required but not yet registered (Phase 16 dependency). Summarisation,
  if any, is a Phase 12 function: it must not add, infer, or restate
  as fact anything absent from the source text, and any AI summary
  must be labelled as a summary of the cited source.
- **Security:** External links open as external references; no user
  data is sent to a news source; stored summaries must not contain
  personal data.
- **Testing strategy (later phases):** Fixture tests that every item
  renders source + date or is rejected from display; empty-state test
  for an unverified / empty feed; summary-fidelity check (summary
  claims checked against fixture source text — manual review in the
  test plan, not an automated truth claim); filter tests by company /
  sector / date. No test has been run in Phase 1.
- **Acceptance criteria:** (a) No news item appears without source and
  date. (b) With no verified feed, the module honestly shows no items.
  (c) No summary adds a fact absent from its source. (d) No feed is
  described as official unless verified as such.

### Module 11 — Valuation

- **Objective:** Show valuation outputs that are fully traceable to
  their inputs, method, and assumptions — and refuse to show a
  valuation whose inputs are missing or unverified.
- **Features:** Valuation method selector limited to methods whose
  inputs are validated and whose formulas are fixed in the sibling
  Financial Formulas spec (no method is invented here); input panel
  showing every input value, source, and date; output with a range /
  sensitivity view where the method supports one; assumption list
  stated in plain language; "cannot be valued from available data"
  state when inputs fail.
- **User interactions:** Choose company and method; inspect / adjust
  only the assumptions the method explicitly allows the user to vary
  (any user-varied assumption is labelled as user-supplied and the
  output is re-labelled accordingly); view sensitivity.
- **Required data / APIs:** Internal reads for statement rows, EOD
  market data, and computed fundamentals. UNVERIFIED: any discount
  rate, growth rate, or macro input from SECP / SBP / PBS / Finance
  Division / World Bank / IMF / FRED; any peer multiple from an
  unverified peer set — such inputs are not defaulted; the user must
  either supply them (labelled user-supplied) or the valuation is
  unavailable.
- **DB dependencies:** Statement store; EOD store; valuation-result
  store recording method, version, inputs (row ids or user-supplied
  flags), and output range.
- **AI agent dependencies:** Agent 5 — Fundamental Analysis
  (registered) for input preparation; a dedicated valuation function
  is required but not yet registered (Phase 16 dependency).
  Narrative must cite the stored output range, never a single
  "true value".
- **Security:** User-supplied assumptions are per-user data and must
  not leak to other users; valuation outputs are information only and
  carry the no-trade banner.
- **Testing strategy (later phases):** Pytest recomputation of each
  method from fixture inputs; missing-input test (→ unavailable);
  user-assumption test (output re-labels as user-assumption-based);
  sensitivity test (changing one stated assumption moves the output
  in the stated direction). No test has been run in Phase 1.
- **Acceptance criteria:** (a) Every valuation shows method, inputs,
  and assumptions. (b) No valuation is shown as a single true value
  without a range or a stated reason why the method gives a point
  output (and its uncertainty note). (c) Unverified inputs are never
  silently defaulted. (d) The output carries the no-trade banner.

### Module 12 — Forecasting

- **Objective:** Show probabilistic forecasts over validated EOD data,
  with uncertainty bands, model identity, training window, and
  out-of-sample limitations visible — never a bare point prediction.
- **Features:** Forecast chart with uncertainty band (interval, not a
  line alone); horizon selector limited to horizons the Phase 11
  baselines spec actually evaluates; model selector limited to
  evaluated models (name + version shown); training-window and
  evaluation summary (out-of-sample error as measured in Phase 11,
  stated in the model's own terms); "forecast unavailable" state when
  the symbol has too little validated history; limitations panel
  (EOD-only, no intraday, no guarantee).
- **User interactions:** Choose company, model, and horizon (within
  evaluated limits); inspect the band at a date; read the evaluation
  summary; compare models only where both were evaluated on the same
  window (otherwise the comparison is blocked or labelled
  non-comparable).
- **Required data / APIs:** Internal reads for validated EOD series
  and stored forecast outputs. UNVERIFIED: any forecast that depends
  on intraday data, unverified macro data, or a model not evaluated in
  Phase 11 — none is offered.
- **DB dependencies:** Validated EOD; forecast-result store (model,
  version, training window, horizon, point + interval, evaluation
  reference, input row ids).
- **AI agent dependencies:** Forecasting-model function required but
  not yet registered (Phase 16 dependency); Agents 1 and 3
  (registered) supply the validated history. LLM narrative, if any,
  is Phase 12 only and must cite the stored band, never narrow it.
- **Security:** Forecast outputs are information only; no personal
  data; model artefacts are not exposed for download unless Phase 27
  explicitly allows it (not specified here).
- **Testing strategy (later phases):** Pytest tests that stored
  forecast intervals contain the stated point and widen (or are
  explained) with horizon per the model spec; backtest-reproduction
  test on a fixture (evaluation numbers recomputed, not copied);
  insufficient-history test (→ unavailable); Playwright test that the
  band, model name, and limitations panel are all visible together.
  No test has been run in Phase 1.
- **Acceptance criteria:** (a) No forecast is shown without its band,
  model, version, and training window. (b) No forecast wording implies
  a guarantee. (c) Unevaluated models / horizons are not offered.
  (d) Short-history symbols show "unavailable", not a forecast.

### Module 13 — Recommendations

- **Objective:** Present BUY / HOLD / SELL / WATCHLIST as transparent,
  probabilistic, scored recommendations — with every contributing
  factor, its weight or rule, and its uncertainty — for information
  only, with no execution path.
- **Features:** Recommendation label + confidence / score + uncertainty
  note; factor breakdown (fundamental, technical, valuation, forecast,
  risk — each only if its module actually produced a stored output for
  this company; missing factors are shown as missing, not zero);
  recommendation history (how the label changed over stored runs, with
  dates); "why this label" plain-language explanation citing stored
  factors; prominent no-trade banner; watchlist action (the only
  action: save to the user's watchlist for monitoring).
- **User interactions:** View a company's recommendation; expand the
  factor breakdown; view history; add to watchlist. There is
  deliberately no "act on this", "buy", "sell", or order control.
- **Required data / APIs:** Internal reads aggregating Modules 7, 8,
  11, 12, and 14 outputs. UNVERIFIED: any factor whose source module
  is itself UNVERIFIED or empty — such a factor is excluded and the
  exclusion is shown.
- **DB dependencies:** Recommendation-result store (label, score,
  factor values + weights / rules, model / rule version, run date,
  input result ids); watchlist store.
- **AI agent dependencies:** Decision-support function required but
  not yet registered (Phase 16 dependency; Phase 13 in the roadmap).
  Narrative must cite stored factors only.
- **Security:** Recommendation logic and weights are the same for all
  users (no per-user hidden personalisation unless Phase 13 specifies
  it); watchlist writes are per-user scoped.
- **Testing strategy (later phases):** Pytest tests recomputing the
  score from fixture factor values; missing-factor test (label still
  produced only if the Phase 13 rule allows it, with the missing factor
  shown, otherwise → "insufficient data"); history test (label changes
  trace to dated runs); Playwright test that no order control exists
  on the page and the no-trade banner is present. No test has been
  run in Phase 1.
- **Acceptance criteria:** (a) Every label shows score, factors, and
  uncertainty. (b) Missing factors are visible, not hidden.
  (c) No execution control exists anywhere in the module.
  (d) Recommendation history is dated and auditable.

### Module 14 — Risk Analysis

- **Objective:** Show a company's and a user's manual portfolio's risk
  in stated, recomputable terms — volatility, drawdown, and other
  measures fixed by the Financial Formulas spec — with the data window
  and limitations stated, so risk is never a single reassuring number.
- **Features:** Risk measures table per company (window stated);
  risk chart (e.g. rolling measure over validated EOD, as the Phase 9 /
  formulas spec fixes); portfolio risk view for manually entered
  holdings (Module 15 inputs, clearly labelled user-entered); stress /
  scenario note limited to scenarios the spec defines (no invented
  crash scenario); "insufficient history" state.
- **User interactions:** Choose company or manual portfolio; choose
  the measurement window within validated history; inspect a measure's
  definition and inputs.
- **Required data / APIs:** Internal reads for validated EOD and
  user-entered holdings. UNVERIFIED: any risk input from intraday
  data or unverified macro data — excluded, with the exclusion shown.
- **DB dependencies:** Validated EOD; computed-risk store (measure,
  version, window, input row ids); user portfolio store (Module 15).
- **AI agent dependencies:** Risk-computation function required but
  not yet registered (Phase 16 dependency); Agent 6 (registered) for
  the underlying EOD series. Narrative must cite stored measures only.
- **Security:** A user's manual portfolio is private to that user;
  company risk measures are non-personal.
- **Testing strategy (later phases):** Pytest recomputation of each
  risk measure from fixture EOD; window test (shorter window changes
  the measure and the window label changes with it);
  insufficient-history test; portfolio isolation test (one user's
  holdings never affect another's risk view). No test has been run
  in Phase 1.
- **Acceptance criteria:** (a) Every measure shows definition, window,
  and inputs. (b) Risk is never presented as a guarantee of safety.
  (c) User portfolios are isolated per user. (d) Short-history cases
  show "insufficient data", not a low-risk label.

### Module 15 — Portfolio Optimization

- **Objective:** Let a user explore optimised allocations over
  **manually entered holdings and watchlist symbols only**, using
  validated EOD data and stated optimisation rules — as analysis, not
  as an instruction to trade, and never as an executed portfolio.
- **Features:** Manual holding entry (symbol, quantity, entry price /
  date — all labelled user-entered, with entry date); optimisation
  view (efficient-frontier-style output only as the Phase 14 / formulas
  spec defines it; the exact optimiser and constraints are fixed there,
  not invented here); constraint controls within stated bounds
  (e.g. per-symbol weight limits, if the spec provides them);
  current-manual-portfolio vs optimised-allocation comparison, both
  labelled with their data dates; explicit statement that the
  optimised allocation is hypothetical and has not been traded.
  **No-trade restriction restated here:** there is no control that
  applies the allocation, rebalances a real account, or connects to a
  broker.
- **User interactions:** Enter / edit / delete manual holdings;
  run an optimisation over a chosen validated window; adjust stated
  constraints; compare allocations; save the analysis as a personal
  note / report input (Module 19).
- **Required data / APIs:** Internal reads for validated EOD and the
  user's manual holdings. UNVERIFIED: any live holding / brokerage
  import, any intraday optimisation input — neither is offered.
- **DB dependencies:** User manual-portfolio store (holdings with
  user-entered flags); optimisation-result store (inputs, constraints,
  optimiser version, window, output weights) so a result can be
  reproduced.
- **AI agent dependencies:** Optimisation function required but not
  yet registered (Phase 16 dependency). Narrative must cite stored
  weights and window only.
- **Security:** Holdings are strictly per-user; optimisation runs
  must not read another user's holdings; deletion of a holding
  removes it from that user's future optimisations (retention of past
  result snapshots follows the Phase 14 / audit rule, not silent
  rewriting of history).
- **Testing strategy (later phases):** Pytest tests with a small
  fixture return matrix recomputed by hand (weights sum to the stated
  total, constraints respected); user-holding isolation test;
  insufficient-history test (symbol with too little EOD → excluded
  with a note, not optimised on invented data); Playwright test that
  no "apply / trade this allocation" control exists. No test has been
  run in Phase 1.
- **Acceptance criteria:** (a) Optimisation uses only manual holdings
  + validated EOD, and says so. (b) Weights, constraints, and window
  are all displayed. (c) No execution or broker control exists.
  (d) The result is labelled hypothetical.

### Module 16 — Investment Screener

- **Objective:** Let a user build, save, and re-run a composable screen
  over validated data — with the screen definition stored so the same
  screen on the same data vintage gives the same result — and make
  clear which companies were excluded for missing data rather than
  for failing a criterion.
- **Features:** Criteria builder (fundamental, technical, valuation,
  sector, market, and risk criteria — each criterion only offered when
  its source module actually has stored data); AND / OR composition
  as the Phase 10 engine spec fixes it; saved screens per user;
  result table (symbol, sector, values for each criterion, latest EOD
  date); excluded-for-missing-data list; screen re-run on a chosen
  data vintage; export of results as a snapshot with provenance.
- **User interactions:** Build a screen; add / remove / edit criteria;
  run, save, rename, delete a screen; inspect why a company was
  excluded; click through to Module 5.
- **Required data / APIs:** Internal reads for screening engine
  inputs (EOD, fundamentals, technicals, valuation, risk, sector).
  UNVERIFIED: any criterion whose input is UNVERIFIED — such a
  criterion is not offered, not offered with a substitute.
- **DB dependencies:** Saved-screen store (owner, definition version,
  criteria, creation / edit dates); screen-run store (screen id, data
  vintage, result ids, excluded-for-missing list) for reproducibility.
- **AI agent dependencies:** Screening-engine function required but
  not yet registered (Phase 16 dependency); Agents 1, 5, 6
  (registered) supply input data. No agent may silently widen or
  narrow a user's criteria.
- **Security:** Saved screens are per-user; a shared / public screen,
  if ever offered, requires a separate Phase 10 / 21 decision and is
  not specified here. Criterion inputs validated (no arbitrary
  expressions executed — the engine's allowed operators are fixed in
  Phase 10).
- **Testing strategy (later phases):** Pytest tests with fixtures:
  a screen's result set recomputed by hand; missing-data exclusion
  test (company missing a criterion input appears in the excluded
  list, not silently dropped without note); reproducibility test
  (same screen + same vintage → same results); saved-screen isolation
  test per user. No test has been run in Phase 1.
- **Acceptance criteria:** (a) Every result row shows the criterion
  values that passed it. (b) Missing-data exclusions are listed.
  (c) A saved screen re-runs reproducibly on a stated vintage.
  (d) No criterion is offered without validated input data.

### Module 17 — AI Research Centre

- **Objective:** Be the single place where a user asks a research
  question about validated PSX data and receives an answer that cites
  stored numbers, states its limits, and never invents a figure —
  powered locally (Ollama open-weight only), not by a paid LLM API.
- **Features:** Question input; answer panel with inline citations to
  stored records (company, EOD date, statement period, ratio, forecast
  band — each citation checkable); "I don't have validated data for
  that" answer when the data is absent or UNVERIFIED; question /
  answer history per user; disclaimer panel (probabilistic, not
  advice, no trade execution); suggested questions limited to topics
  the validated store can actually answer (no suggested question
  about an UNVERIFIED source).
- **User interactions:** Type a question; read the cited answer;
  follow a citation to its source screen; save an answer as a report
  input (Module 19); flag an answer as unhelpful (feedback stored
  per user, used only for later quality review — no automatic
  retraining is specified).
- **Required data / APIs:** Internal reads for all validated stores
  the question may cite; local Ollama inference (Phase 12). UNVERIFIED:
  any external LLM API, any web-search answer source, any macro /
  news answer whose source is UNVERIFIED — the centre must answer
  "not available from validated data" for those, not browse or guess.
- **DB dependencies:** Q&A history store (user, question, answer text,
  citation record ids, model name + version, answer date); citation
  integrity rule: an answer row without at least one stored citation
  (or an explicit "no data" statement) must not be displayed as a
  researched answer.
- **AI agent dependencies:** Phase 12 interpretation function and
  Phase 16 orchestration, both required but not yet registered beyond
  Agents 1–6; Agents 1–6 supply the citable data. The LLM is a
  narrator of stored numbers, never a calculator and never a source.
- **Security:** Questions and history are per-user private; answers
  must not reveal another user's data; prompt-injection handling
  (a question that asks the system to reveal system instructions,
  ignore its citation rule, or invent data) is a Phase 27 hardening
  item — the specified behaviour is to refuse the injected instruction
  and answer only from validated data or not at all.
- **Testing strategy (later phases):** Citation tests on fixtures:
  every number in a sample answer traces to a stored record id;
  no-data test (question about an UNVERIFIED source → "not available"
  answer, not a fabricated answer); hallucination-spot-check
  procedure (manual review of a sampled answer set against citations,
  recorded in the Phase 23 test plan); per-user history isolation test.
  No test has been run in Phase 1.
- **Acceptance criteria:** (a) Every numeric claim in an answer has a
  checkable citation or the answer says the data is unavailable.
  (b) No paid LLM API is used. (c) History is per-user only.
  (d) The disclaimer (probabilistic, not advice, no execution) is
  always visible with the answer.

### Module 18 — Alerts Centre

- **Objective:** Let a user define alerts that fire from **stored,
  scheduled-refresh data** (not from live polling), see a complete
  alert history, and control alert volume — with every firing traceable
  to the data vintage that caused it.
- **Features:** Alert creation (company, condition type limited to
  conditions computable from stored EOD / computed outputs — e.g.
  price crossing a user-set level on the latest EOD, indicator
  crossing, recommendation-label change; exact condition catalogue
  fixed in Phase 15); alert list with enable / disable / delete;
  firing history (alert, condition, triggering value, data vintage,
  firing timestamp); in-app notification display (the only delivery
  channel specified at PKR 0); rate-limit / digest rule as fixed in
  Phase 15 (no alert spam: repeated identical firings on unchanged
  data must not re-fire).
  **No-trade restriction restated here:** an alert is a notification
  to look at information. It never places, suggests executing, or
  links to any order.
- **User interactions:** Create / edit / enable / disable / delete an
  alert; view firing history; acknowledge / dismiss a notification;
  set a digest preference if Phase 15 provides one.
- **Required data / APIs:** Internal reads for latest validated EOD /
  computed outputs and the user's alert definitions; internal write
  for alert definitions and firing history. UNVERIFIED: SMS, email,
  or push delivery providers; any intraday trigger (no intraday
  archive) — triggers fire only when a new validated batch lands, and
  the UI must say which batch caused the firing.
- **DB dependencies:** Alert-definition store (owner, company,
  condition, threshold, enabled flag); alert-firing store (alert id,
  triggering value, vintage, timestamp, acknowledged flag).
- **AI agent dependencies:** Alert-evaluation function required but
  not yet registered (Phase 16 dependency); Agents 1 and 6
  (registered) supply trigger data. No agent may create an alert for a
  user or change a user's threshold.
- **Security:** Alerts are strictly per-user; thresholds and firing
  history never leak across users; alert creation inputs validated.
- **Testing strategy (later phases):** Pytest tests with fixture
  EOD batches: a crossing on a new batch fires once; the same batch
  re-evaluated does not re-fire; a disabled alert never fires; a
  deleted alert's history handling follows the Phase 15 rule;
  per-user isolation test. Playwright test for create → fire (on
  fixture batch) → history row. No test has been run in Phase 1.
- **Acceptance criteria:** (a) Every firing shows its triggering value
  and data vintage. (b) No alert fires twice on the same unchanged
  data. (c) Delivery is in-app only unless a zero-cost channel is
  separately verified. (d) No alert links to any trading action.

### Module 19 — Research Report Generation

- **Objective:** Turn a user's selected, validated analysis into a
  single, dated, citable report snapshot — with provenance, uncertainty,
  and limitations carried into the document — that the user can save,
  re-open, and share as a snapshot, not as live advice.
- **Features:** Report builder (choose company / sector / screen /
  portfolio analysis already produced by Modules 5–16; choose sections
  to include); generated document (sections in the order the user
  chose, each section carrying its source, as-of date, and uncertainty
  note); cover block (title, subject, generation date (PKT), data
  vintage, "snapshot — not live" label, no-trade disclaimer);
  saved-report list per user; download / print of the snapshot;
  "regenerate on newer data" action that creates a **new** dated
  report rather than silently rewriting the old one.
- **User interactions:** Select subject and sections; generate;
  preview; save; download / print; open a saved report; regenerate
  on newer data (new version).
- **Required data / APIs:** Internal reads for the selected analysis
  outputs and their provenance. UNVERIFIED: any section whose source
  is UNVERIFIED — such a section is omitted from the report with a
  note ("section omitted: source not verified"), never filled.
- **DB dependencies:** Saved-report store (owner, subject, section
  list, generation date, data vintage, content snapshot or content
  record ids, version); report content must be reproducible from its
  stored record ids + vintage, or stored as an immutable snapshot —
  the choice is fixed in Phase 24 documentation, not here.
- **AI agent dependencies:** Phase 12 narrative function (required,
  not yet registered beyond Agents 1–6) for section prose, citing
  stored outputs only; Agents 1–6 supply underlying data. Generated
  prose must not introduce a number absent from the cited section.
- **Security:** Reports are per-user; a report about a user's manual
  portfolio contains that user's private data and must never be
  visible to another user; downloads carry the same disclaimers as
  the on-screen report.
- **Testing strategy (later phases):** Fixture report tests: every
  number in a generated report traces to a cited record; omitted-
  section test (UNVERIFIED section → omission note, not content);
  version test (regenerate creates a new version, old version
  unchanged); per-user isolation test; Playwright test that the
  cover block (date, vintage, disclaimer) renders on every report.
  No test has been run in Phase 1.
- **Acceptance criteria:** (a) A report is a dated snapshot, never
  presented as live. (b) Every section carries source + as-of date.
  (c) Regeneration never rewrites history. (d) The no-trade
  disclaimer is on the cover and in the download.

### Module 20 — Agent Monitoring

- **Objective:** Let a user (and, for system health, an administrator)
  see what the system's agents actually did — runs, inputs, outputs,
  approvals, and failures — so agent behaviour is auditable rather
  than mysterious, and so a wrong agent output can be traced.
- **Features:** Agent run list (agent function, run date, input
  vintage, status: completed / failed / awaiting approval where
  Phase 16 provides approval gates); run detail (inputs, outputs,
  citations, errors, duration as recorded); failure / quarantine view
  (runs that failed validation, with the reason); approval queue view
  if Phase 16 gates apply (approve / reject actions are administrator
  or owner actions as Phase 16 fixes them — no agent action executes
  a trade or a send without its gate, and in Phase 1 scope there is
  no trade or external send for a gate to release); read-only-first
  posture: monitoring never re-runs an agent with different inputs
  silently — any re-run is a new, logged run.
- **User interactions:** Browse runs; filter by agent function, date,
  status; open a run detail; view failures; act on an approval item
  only if the user's role permits it (Phase 16 / 21).
- **Required data / APIs:** Internal reads for agent-run logs and
  approval records. UNVERIFIED: any agent capability beyond the
  registered / specified functions — monitoring must not display a
  capability the system does not have.
- **DB dependencies:** Agent-run log store (agent function, run id,
  input ids / vintage, output ids, status, error, timestamps);
  approval store if Phase 16 provides gates. Logs are append-only
  in specification: a log row is never edited to hide a failure.
- **AI agent dependencies:** This module monitors the agents; it is
  not itself an analysis agent. Its data source is the Phase 16
  orchestration log (required, not yet built).
- **Security:** Ordinary users see runs relevant to their own data
  (e.g. a forecast run for a company they viewed) as Phase 16 / 21
  fixes visibility; system-wide run detail, including any prompt or
  internal configuration, is administrator-only. No secret, key, or
  credential may appear in any run log display.
- **Testing strategy (later phases):** Fixture log tests: a completed
  run, a failed run, and an awaiting-approval run each render with
  the correct status; append-only test (an attempt to edit a log row
  is rejected); visibility test (ordinary user cannot open an
  admin-only run detail); approval-action test (only a permitted role
  can approve). No test has been run in Phase 1.
- **Acceptance criteria:** (a) Every agent output visible elsewhere
  in the product has a traceable run here (or the gap is logged as a
  known Phase 16 dependency). (b) Failures are visible, not hidden.
  (c) Logs are append-only. (d) No secret appears in monitoring.

### Module 21 — Administrative Dashboard

- **Objective:** Give administrators — and only administrators — a
  single surface to see system health, data freshness, source status,
  user administration, and configuration, without giving any admin
  control a trading, broker, or external-send capability.
- **Features:** System health overview (collector run status, last
  successful refresh, symbols missing, validation / quarantine counts,
  storage state — local filesystem / Parquet / MinIO as configured);
  source-status panel (verified sources with status; UNVERIFIED
  sources listed as "not verified — not in use", never as active);
  user administration (list users, roles, disable / enable accounts,
  role changes with audit — per Phase 21); configuration view
  (refresh schedule, retention, feature flags for modules whose data
  is unavailable — e.g. hiding Module 10's data area until a feed is
  verified); audit-log viewer (sign-ins, role changes, admin actions,
  agent approvals); data-management entry points (quarantine review,
  re-validation trigger — as Phases 4 and 20 specify; triggers are
  logged and never silent).
  **No-trade restriction restated here:** the admin dashboard has no
  broker, order, payment, or external-send control. An administrator
  cannot use it to trade, to send on a user's behalf, or to connect a
  paid service without separate approval.
- **User interactions:** View health and source status; manage users
  and roles; view audit logs; adjust configuration within the bounds
  Phase 20 fixes; review quarantine items.
- **Required data / APIs:** Internal admin reads for health, source
  status, users, audit logs, and configuration; internal admin writes
  for user / role / configuration changes (all logged). UNVERIFIED:
  any hosted monitoring / alerting SaaS, any paid admin tooling —
  health is from local logs and local checks only in this spec.
- **DB dependencies:** User / role / audit stores (Module 2);
  collector-run / validation / quarantine stores (Phases 2–4);
  configuration store. Admin writes must create audit rows in the
  same transaction conceptually (exact mechanism fixed in Phase 3).
- **AI agent dependencies:** None for administration itself; agent
  health is viewed via Module 20, linked from here, not duplicated
  with different numbers.
- **Security:** Administrator role required for every route and
  action in this module; every admin action logged with actor,
  action, target, and timestamp; admin sessions subject to the same
  expiry and hardening as Module 2 (Phase 27); no admin action may
  bypass the provenance, no-trade, or per-user privacy rules.
- **Testing strategy (later phases):** Role tests (ordinary user →
  every admin route denied, including direct URL access); audit tests
  (each admin action creates exactly one audit row with actor and
  timestamp); health-display tests on fixture collector runs
  (failed run → visible failure, not a green status); configuration
  tests (a flag change takes effect only for its stated scope).
  No test has been run in Phase 1.
- **Acceptance criteria:** (a) No non-admin can reach any admin
  function, including by direct URL. (b) Every admin action is
  audited. (c) UNVERIFIED sources are shown as not in use, never as
  active. (d) The dashboard contains no trading, broker, payment,
  or external-send control.

## 5. Module coverage checklist (21 of 21)

| # | Module | Specified in |
|---|---|---|
| 1 | Landing page | §4 Module 1 |
| 2 | Registration / auth | §4 Module 2 |
| 3 | Market dashboard | §4 Module 3 |
| 4 | Company explorer | §4 Module 4 |
| 5 | Individual company intelligence | §4 Module 5 |
| 6 | Financial statements | §4 Module 6 |
| 7 | Fundamental analysis | §4 Module 7 |
| 8 | Technical analysis | §4 Module 8 |
| 9 | Sector analysis | §4 Module 9 |
| 10 | News / announcements | §4 Module 10 |
| 11 | Valuation | §4 Module 11 |
| 12 | Forecasting | §4 Module 12 |
| 13 | Recommendations | §4 Module 13 |
| 14 | Risk analysis | §4 Module 14 |
| 15 | Portfolio optimization | §4 Module 15 |
| 16 | Investment screener | §4 Module 16 |
| 17 | AI research centre | §4 Module 17 |
| 18 | Alerts centre | §4 Module 18 |
| 19 | Research report generation | §4 Module 19 |
| 20 | Agent monitoring | §4 Module 20 |
| 21 | Administrative dashboard | §4 Module 21 |

## 6. UNVERIFIED register (complete for this file)

Every item below is UNVERIFIED for machine use in Phase 1. Nothing in
this spec depends on any of them as if it were available. Verification,
where required, is later-phase work with its own blocker status; it is
not assumed here.

1. SECP — machine-use endpoint / feed: UNVERIFIED.
2. SBP (State Bank of Pakistan) — machine-use endpoint / feed: UNVERIFIED.
3. PBS (Pakistan Bureau of Statistics) — machine-use endpoint / feed: UNVERIFIED.
4. Finance Division — machine-use endpoint / feed: UNVERIFIED.
5. World Bank — machine-use endpoint / feed for this system's use: UNVERIFIED.
6. IMF — machine-use endpoint / feed for this system's use: UNVERIFIED.
7. FRED — machine-use endpoint / feed for this system's use: UNVERIFIED.
8. Official PSX API — none verified; psx-dps / psxdata are third-party libraries, not an official API: UNVERIFIED / NOT EXISTENT as verified.
9. Historical intraday archive for PSX — none verified (psxdata explicitly has none): UNVERIFIED.
10. Guaranteed real-time / continuous market feed — none verified; only today's ticks / snapshots via the verified libraries, with capture timestamps: UNVERIFIED as a guaranteed feed.
11. Structured financial-statement machine source — none verified (blocks Module 6 data): UNVERIFIED.
12. News / announcements machine feed — none verified (blocks Module 10 data): UNVERIFIED.
13. Email / SMS / push delivery provider at PKR 0 — none verified (blocks any external alert delivery; in-app only in this spec): UNVERIFIED.
14. Permanent free hosting, free hosted database, free hosted monitoring, or any paid-service equivalent at PKR 0 — none verified or assumed: UNVERIFIED.
15. Any price, index level, exchange rate, company figure, ratio value, forecast value, or benchmark stated as fact — none is stated in this file, and none may be added without a verified stored source: NOT STATED (by design).
16. Agent functions beyond Agents 1–6 in the sibling registry (forecasting, decision support, valuation, risk, screening, optimisation, alerts, report narrative, orchestration, news ingest) — required functions, but their registration, tools, and behaviours are NOT YET REGISTERED: open dependency for Phase 16.
17. Exact internal API routes — not invented here; fixed in Phase 22: NOT YET FIXED (by design, not a gap in this spec's data needs).
18. Exact statement types, indicator lists, ratio sets, valuation methods, forecast models, risk measures, alert conditions, and optimiser constraints — fixed by their owning phase specs (Phases 7–15), not invented here: NOT YET FIXED in this file (referenced, not assumed).

## 7. What this specification deliberately does NOT do

- It does not start Phase 2 or any later phase, and it does not deliver
  application code, a database, a deployment, or a test run.
- It does not claim any test has passed, any module works, or any data
  has been collected at scale.
- It does not invent an API, endpoint, price, capability, or source.
- It does not authorise any spend, sign-up, install, credential,
  broker connection, live polling, trading, or posting.
- It does not describe local hardware, electricity, or internet as
  free — they are external operating expenses (see §0).

## 8. Open items for the coordinator audit (Phase 1 close-out)

1. Independent audit (stage 9) has not been performed — see file header.
2. Agent functions beyond Agents 1–6 need registration in Phase 16
   before Modules 11–20 can be implemented as specified.
3. Modules 6 and 10 are honestly empty until their sources are verified
   (Phase 7 / later data work); the audit should confirm that this
   emptiness is accepted as the Phase 1 position, not papered over.
4. Internal API routes (Phase 22) and owning-phase formula / model /
   condition catalogues (Phases 7–15) must be fixed before
   implementation; this spec references them without inventing them.
5. No delivery time is promised in this file. Later-phase timing is
   for the coordinator's plan, not this specification.

---

*End of Team 9 Website Module Specification — Phase 1 of 30. STOP AFTER PHASE 1.*
