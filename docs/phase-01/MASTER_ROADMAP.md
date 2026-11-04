# PSX Intelligence AI — Master Roadmap (Canonical)

> **Canonical version.** This file, `docs/phase-01/MASTER_ROADMAP.md`, is the
> canonical roadmap. The project-root `MASTER_ROADMAP.md` is a summary only
> and must not introduce different phase numbers, titles, or objectives.
> If the two ever disagree, this file governs and the root file must be
> corrected.
>
> **Exact named phase list.** The 30 phases below are used verbatim, in
> this order, in this file, in the root summary, in `PHASE_BREAKDOWN.md`,
> in `PHASE_DEPENDENCY_MAP.md`, and in `TASK_ACCEPTANCE_MATRIX.md`. No
> phase is renamed, reordered, merged, or split.

## Phase 1 status and stop rule

**Phase 1 is IN PROGRESS — Requirements and architecture only.**
Phase 1 is complete only when the coordinator audit passes, followed by
correction and a checkpoint (stages 10–11 of the Phase 1 workflow below).
**STOP AFTER PHASE 1 — do not begin Phase 2.** Phases 2–30 are documented
here and in `PHASE_BREAKDOWN.md` only; no Phase 2+ code, collector run,
or deployment is started by this roadmap.

**Starting condition (verified 2026-11-04, reused verbatim in substance):**
Project folder `~/workspace/psx-intelligence-ai/` is new. A separate
scaffold to REFERENCE but NEVER overwrite or touch is
`~/workspace/psx-data-collection/` (stdlib collector, provenance / PKT /
stale / conflict rules, offline tests passing, coverage template).
Tools verified: Python 3.12.3, Node v24.22.1. Docker, `psql`, `redis-cli`
are NOT installed — plans must reflect local-dev reality and must not
assume paid hosting exists.

**Verified sources (reuse, do not extend beyond this):** `psx-dps` (MIT,
zero dependencies, no API key, ~496 trading vs ~1029 listed symbols,
~5 years EOD, today's ticks, 38 sectors, multi-node 404 quirk, no official
PSX API); `psxdata` (MIT, PyPI, alpha 0.1.0a1, daily OHLCV + live snapshots
ONLY, no historical intraday archive); Eulerpool: NO PSX coverage, vendor
only, no paid API approved, never purchase anything.

**UNVERIFIED — never assume:** machine-use of SECP / SBP / PBS / Finance
Division / World Bank / IMF / FRED feeds is UNVERIFIED. Any phase depending
on them lists verification as a dependency / blocker, never as an assumed
feed. Likewise, no verified machine-readable source is asserted in this
roadmap for financial statements (Phase 08), corporate announcements
(Phase 09), or news (Phase 14) — those phases are designed and gated on
verification; they do not ship data from an unverified source.

## Budget rule (PKR 0 absolute — governs all 30 phases)

**BUDGET IS PKR 0 ABSOLUTE.** No paid APIs, subscriptions, hosting,
databases, storage, monitoring, or AI services in any phase. Nothing in
this roadmap introduces a paid alternative: if a free solution cannot
satisfy a requirement, the limitation is documented, scope is reduced or
deferred, and the requirement stays open — it is never solved by
proposing a purchase. See `COST_ESTIMATION.md` for the three scenarios
and `FREE_VS_PAID_COMPARISON.md` for the free-coverage / gap analysis.

**Local hardware, electricity, and internet are EXTERNAL operating
expenses.** They are disclosed as such in the cost documents and are
never called "free". Zero-budget in this roadmap means zero project
spend on software, data, hosting, and services — not zero cost of
running a computer.

**Zero-cost online deployment (Phase 30 / Phase 28–29 context) is
conditional, not promised:** it is used ONLY where a legitimate free
service is verified as available at deployment time, and it carries the
permanent-free-hosting caveat — no free tier is guaranteed permanent;
terms can change or be withdrawn, so the system must always remain
runnable locally (Scenario 2) if an online free service disappears.
If no legitimate free service covers a component, that component stays
local and the limitation is documented.

## Trading rule (governs every trading-adjacent phase)

**The system must NOT execute real trades initially.** This applies in
particular to Phase 19 (Price target engine), Phase 22 (Investment
recommendation engine), and Phase 23 (Portfolio optimization), and to
any agent or scheduling work that touches recommendations (Phases 25–27).
Recommendations, price targets, and portfolio suggestions are
information and analysis only, probabilistic with uncertainty stated,
never guaranteed, and never connected to a broker or order system.
No phase in this roadmap adds trade execution; adding it would require
a separate, explicit authorisation outside Phase 1, which this roadmap
does not grant.

## Hard rules (all phases)

No sign-ups, installs, purchases, credentials, API keys, broker
connections, live polling, trading, or posting without separate explicit
authorisation. **No full-scale live data collection in Phase 1** —
Phase 1 data work is read-only inspection only (see workflow stage 4).
Never invent a price, benchmark, API, endpoint, or capability. Every cost
figure is labelled VERIFIED (with source), ESTIMATE (with basis and range),
or UNVERIFIED (with the check needed). Forecasts and recommendations are
probabilistic, never guaranteed. No unauthorised trading.

## Phase 1 workflow — 11 stages (followed by Phase 1, not skipped)

1. **Brainstorm** — scope, problems, and candidate approaches, recorded
   with open questions, not decided by assumption.
2. **Research** — check verified sources, tools, and prior scaffold;
   record what is verified vs unverified.
3. **Validate** — test claims against sources; reject or label anything
   that cannot be verified.
4. **Data inspection (read-only only)** — inspect existing data, samples,
   and the referenced scaffold read-only. **NO full-scale live data
   collection in Phase 1.**
5. **Architecture planning** — architecture, modules, dependencies, and
   the 30-phase sequence in this roadmap.
6. **Implementation specification** — per-phase tasks, inputs, outputs,
   files, DB / API / agent requirements, free resources, and test cases
   in `PHASE_BREAKDOWN.md`, detailed enough to implement without guessing.
7. **Documentation** — this roadmap set, written as the Phase 1 record.
8. **Testing strategy (defined, not claimed passed)** — test cases and
   acceptance criteria are defined per phase; no test is claimed passed
   in Phase 1, and Phase 1 acceptance rows stay PENDING-AUDIT.
9. **Independent audit** — coordinator audit of the Phase 1 spec against
   the acceptance matrix; the authoring team does not mark its own work
   passed.
10. **Correction** — fix audit findings; re-check consistency across all
    Phase 1 documents (same phase list everywhere).
11. **Checkpoint** — frozen Phase 1 checkpoint: what is specified, what
    is open / UNVERIFIED, and what Phase 2 may start from. Only after
    this checkpoint may a separately authorised Phase 2 begin — and this
    roadmap does not authorise it.

## The 30 phases — exact named list

| # | Phase (exact name) | One-paragraph objective |
|---|--------------------|-------------------------|
| 01 | Requirements and architecture | Produce the complete, auditable Phase 1 specification — scope, non-goals, architecture, source status, provenance rules, cost/resource model — with no application code and no later phase started. Its completion condition is audit pass + correction + checkpoint (workflow stages 9–11). |
| 02 | Repository and development environment | Set up the version-controlled repository, local development environment (Python 3.12.3 / Node v24.22.1 baseline), dependency policy (free / stdlib-first), and contributor workflow, so every later phase builds reproducibly on a developer machine with no paid tooling. |
| 03 | Database architecture | Design the database (local-first; SQLite for local development with a PostgreSQL-compatible schema design) covering registry, market data, statements, announcements, macro data, analysis, and provenance, with migrations, indexes, and backup/restore defined before any collector writes to it. |
| 04 | PSX company registry | Build the authoritative company registry for the PSX universe (~496 trading vs ~1029 listed, 38 sectors — verified counts), with symbol identity, listing status, and sector membership, kept distinct from price data so a symbol is never confused with its history. |
| 05 | Backend foundation | Build the shared backend foundation — configuration, logging, provenance recording, error handling, and internal module boundaries — on free, local tooling, so collectors and engines share one set of conventions instead of each inventing its own. |
| 06 | Historical market data collector | Implement the resumable, idempotent collector for ~5 years of EOD history from verified sources, handling the `psx-dps` multi-node 404 quirk, with provenance per fetch and no historical intraday claim (no verified source provides a historical intraday archive). |
| 07 | Market snapshot collector | Implement today's snapshot / tick-view collection from verified sources only, labelled as snapshots (not history), with freshness timestamps and stale marking, and no live polling or guaranteed real-time claim. |
| 08 | Financial statement collector | Design and, only after source verification, implement collection of financial-statement data; until a machine-readable source with a checkable licence is verified, this phase ships the collector framework, field model, and verification checklist — not statement data from an assumed source. |
| 09 | Corporate announcement collector | Design and, only after source verification, implement collection of corporate announcements; until a verified machine-readable announcement source is established, this phase ships the framework, announcement model, and verification checklist — not announcement data from an assumed source. |
| 10 | Macroeconomic data collector | Design and, only after verification, implement collection of macroeconomic series; SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use is UNVERIFIED, so this phase is gated: framework and verification checklist first, data ingestion only on a verified source. |
| 11 | Fundamental analysis | Compute fundamental analysis from verified, stored data (registry + statements once available + market data), with every figure traceable to a stored source and as-of date, and missing inputs shown as missing — never zero-filled or estimated silently. |
| 12 | Technical analysis | Implement a deterministic technical-analysis engine over validated EOD data, documented per indicator (formula, window, minimum history), with insufficient history reported as insufficient data and no indicator presented as a standalone buy/sell signal. |
| 13 | Sector intelligence | Compute sector intelligence across the 38 verified sectors and market breadth from validated data, with denominators and coverage stated, so sector claims are recomputable from their constituents. |
| 14 | News intelligence | Design and, only after source verification, implement news collection and classification; until a verified, lawfully usable news source is established, this phase ships the framework, taxonomy, and verification checklist — not news content from an assumed source. |
| 15 | Financial health scoring | Compute transparent financial-health scores from verified fundamentals and market data, with the scoring formula, inputs, and limitations published alongside every score, and no score presented as a guarantee of future health or performance. |
| 16 | Valuation engine | Implement valuation calculations from verified inputs with methods, assumptions, and sensitivity ranges stated per output; where a required input is UNVERIFIED or missing, the valuation is withheld or range-bounded and labelled as such, never completed with an invented input. |
| 17 | Statistical forecasting | Implement transparent statistical forecasting baselines over EOD history, evaluated out-of-sample with error bands, reported as probabilistic forecasts with limitations — never as guaranteed future prices. |
| 18 | AI forecasting | Add AI-assisted forecasting and interpretation that cites stored numbers, states uncertainty, and never invents figures, papers, or sources; AI output is an explanation layer over Phases 11–17, not a replacement for them, and its token usage is logged under the PKR 0 rule (free/local options only). |
| 19 | Price target engine | Compute price targets as probabilistic, range-based analysis outputs with method, inputs, horizon, and uncertainty shown; price targets are information only — the system must NOT execute real trades, and no target is a buy/sell instruction or a guaranteed outcome. |
| 20 | Backtesting | Run honest backtests of screens, rules, and forecasts over historical EOD data with survivorship, look-ahead, and cost/slippage limitations stated; EOD only, since no verified historical intraday archive exists, and backtest results are never presented as future guarantees. |
| 21 | Risk management | Implement risk measurement and risk reporting (volatility, drawdown, concentration, and scenario views over validated history) as analysis and disclosure, not as a trading control — no position is opened, closed, or sized into a live order by this system. |
| 22 | Investment recommendation engine | Combine analysis, scores, valuations, forecasts, targets, backtests, and risk views into a transparent recommendation record showing inputs, reasoning, uncertainty, and limitations; recommendations are information only — the system must NOT execute real trades and no recommendation is a guaranteed outcome. |
| 23 | Portfolio optimization | Implement portfolio analysis and optimisation suggestions over user-entered (manual) holdings and validated market data, as analysis only; no live portfolio is managed, rebalanced by order, or connected to a broker, and suggested allocations are probabilistic analysis, not instructions to trade. |
| 24 | Independent audit | Run an independent audit of data, calculations, provenance, and outputs against the acceptance matrix — by a party other than the implementing team — reporting pass / fail / UNVERIFIED per item, with findings corrected before rollout. |
| 25 | Multi-agent orchestration | Introduce orchestrated agents (researcher, validator, analyst, reporter roles as specified in `PHASE_BREAKDOWN.md`) with explicit task boundaries, read-only defaults, human-approval gates for any outward action, and complete execution logs; agents never trade, post, or send on their own authority. |
| 26 | Autonomous company research | Build autonomous, scheduled company-research runs that assemble a research dossier per company from verified stored data only, with every claim cited to a stored figure and every gap labelled; autonomy here means scheduled assembly and reporting, not autonomous trading, posting, or external action. |
| 27 | Scheduling and monitoring | Implement scheduling (daily refresh, research runs, reports) and monitoring (freshness, failures, health) on free/local tooling, so a stale feed or failed job is visible before any user acts on old data, with alerting limited to channels the user has explicitly approved. |
| 28 | Frontend and dashboard integration | Build the frontend and dashboard integrating registry, market, fundamental, technical, sector, forecast, target, recommendation, and portfolio views, with source, as-of date, uncertainty, and limitations visible on the same screen as any figure or recommendation. |
| 29 | Security and production hardening | Harden the system for production: input validation, credential handling (no credential in code or chat), access control, licence/attribution compliance, backup/restore, and a security review — on the PKR 0 constraint, using free/local controls only. |
| 30 | Full PSX rollout and final verification | Roll out across the full PSX universe covered by verified data, run final verification (data completeness, calculation audit, UI checks, limitation disclosures), publish the handover pack and open-items register (including every UNVERIFIED item still open), and freeze the release; any zero-cost online deployment is used only where a legitimate free service is verified, with the permanent-free-hosting caveat. |

## Ordering principles

1. **Foundations before collectors, collectors before analysis.**
   Repository / environment (02) and database (03) precede the registry
   (04), backend (05), and collectors (06–10); analysis (11–13) consumes
   stored, validated data only.
2. **Deterministic before probabilistic.** Fundamentals, technicals, and
   sector intelligence (11–13) and statistical baselines (17) precede AI
   forecasting (18), price targets (19), and recommendations (22), so
   every probabilistic output has numbers to cite.
3. **Gated phases stay gated.** Phases 08, 09, 10, and 14 ship framework
   + verification checklist first; data ingestion starts only on a
   verified source. Downstream phases (11, 15, 16, 26) must work on
   verified data alone if verification fails.
4. **Audit before agents and rollout.** Independent audit (24) precedes
   multi-agent orchestration (25) and autonomous research (26); security
   hardening (29) precedes full rollout (30).
5. **No trading at any point in this roadmap.** Recommendation-adjacent
   phases (19, 22, 23) and agent phases (25, 26) are analysis and
   reporting only.

## Explicit non-goals (all phases)

- No broker integration, order placement, auto-trading, or real-trade execution.
- No guaranteed real-time feed, forecast, price target, or return.
- No historical intraday archive unless a future verified source provides one.
- No purchase, licence fee, subscription, or paid API — PKR 0 absolute;
  a requirement free solutions cannot satisfy is documented as a
  limitation, with scope reduced or deferred, never solved by buying.
- No redistribution of licensed data beyond the actual licence terms —
  licence text must be checked, not assumed.
- No Phase 2 work inside Phase 1, and no later-phase work inside an
  earlier phase's acceptance criteria.

## Companion documents (Phase 1, Team 8)

- `PHASE_BREAKDOWN.md` — full detail per phase (exact list above).
- `PHASE_DEPENDENCY_MAP.md` — dependency table, Mermaid diagram, critical path.
- `TASK_ACCEPTANCE_MATRIX.md` — task × acceptance matrix; Phase 1 rows PENDING-AUDIT.
- `COST_ESTIMATION.md` — three PKR 0 scenarios (see budget rule above).
- `RESOURCE_REQUIREMENTS.md` — compute / storage / volume per phase and scenario.
- `FREE_VS_PAID_COMPARISON.md` — free coverage, free gaps, and the no-purchase decision rule.
