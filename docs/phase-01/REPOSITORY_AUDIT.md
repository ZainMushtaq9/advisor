# PSX Intelligence AI — Repository Audit (Phase 1, Team 1)

- **Project:** PSX Intelligence AI
- **Phase:** Phase 1 of 30 — documentation and audit only
- **Team:** Team 1 — Repository Audit + Product Requirements
- **Date:** 2026-11-04
- **Status of this document:** Phase 1 audit record. It describes what exists, what does not exist, and what is still unverified. It does not authorise Phase 2 work.
- **Budget rule (revised brief, absolute):** PKR 0. No paid API, subscription, hosting, database service, storage service, monitoring service, or AI/LLM subscription is assumed, approved, or specified anywhere in Team 1's files. Local hardware, electricity, and internet are EXTERNAL operating expenses — they are disclosed as such and are never described as "free". No permanent free hosting is assumed to exist.
- **Trading rule:** The system must NOT execute real trades initially. This is stated here, in `PROJECT_STATUS.md`, and in `NEXT_ACTIONS.md`. No broker connection, order placement, or trade execution is specified in Phase 1.
- **Stop rule:** STOP AFTER PHASE 1. Do not begin Phase 2 until the Phase 1 audit passes (see `NEXT_ACTIONS.md`).

> **How to read verification labels in this file**
>
> - **VERIFIED (starting condition, 2026-11-04):** stated in the verified starting condition supplied to Team 1 and reused verbatim; Team 1 did not re-run it as a new live claim in this turn.
> - **CHECKED BY TEAM 1 (2026-11-04):** Team 1 directly observed it in this turn (directory listing, `python3 --version`, `node --version`, absence of `docker`/`psql`/`redis-cli`, git check).
> - **UNVERIFIED:** not yet verified by a live, documented run or by an official source read in this phase. Never treat UNVERIFIED as available, covered, or working.
> - **PROPOSED / DEFERRED:** a Phase 2 design question owned by another team, listed here only so the gap is visible. Team 1 does not decide it.

---

## 1. Executive summary

1. **There is no application yet.** As of this audit, PSX Intelligence AI consists of documentation only (this team's files plus sibling teams' Phase 1 documents — see §3). There is no application code, no database, no deployment, no live data pipeline, and no user-facing service.
2. **There is a separate, earlier scaffold to reference — not to claim as this project.** `~/workspace/psx-data-collection/` is a small, stdlib-only collector scaffold with provenance rules. It is reference material for Phase 2 design. It is NOT the PSX Intelligence AI application, it has not been moved into this project, and Team 1 has not modified it.
3. **The local toolchain is minimal.** Python 3.12.3 and Node v24.22.1 are present. Docker, `psql` (PostgreSQL client), and `redis-cli` are NOT installed. No database server, cache server, container runtime, or hosting environment is confirmed.
4. **Data-source coverage is mostly unproven.** Two unofficial, free, MIT-licensed Python libraries (`psx-dps` and `psxdata`) are plausible from their public READMEs for market snapshots / EOD data, but neither has been proven by a live run in this workspace in Phase 1, and Phase 1 explicitly forbids full-scale live data collection (documentation + read-only inspection only). Regulator and statistics sources (SECP, SBP, PBS, Finance Division, World Bank, IMF, FRED) are UNVERIFIED for machine use. Eulerpool is NOT a PSX source and must never be presented as one.
5. **The binding constraints for Phase 2 planning are cost, legality, and honesty about uncertainty.** PKR 0 budget, no assumed redistribution rights for PSX data, undocumented PSX endpoints that can change without notice, and probabilistic — never guaranteed — forecasts and recommendations.

## 2. Starting-condition discrepancy — recorded, not hidden

The original Team 1 brief stated, as a verified starting condition for 2026-11-04, that "no folder `~/workspace/psx-intelligence-ai` exists yet (you will create it)".

**What Team 1 actually found (CHECKED BY TEAM 1, 2026-11-04):**

- `~/workspace/psx-intelligence-ai/` already existed when Team 1 began work, containing an empty `docs/` directory structure and, by the time Team 1 listed it, sibling-team Phase 1 documents (see §3.3). Team 1 did not create the folder from nothing and does not claim to have done so.
- Team 1's own contribution is strictly the files listed in §3.2. Team 1 has not created, edited, moved, or deleted any sibling-team file, any file in `~/workspace/psx-data-collection/`, or any `~/workspace/*.md` file.
- The discrepancy does not change any substantive conclusion: before Team 1's files, this project still had no application code, no database, and no deployment. The folder's pre-existence is a scaffolding fact, not a delivery.

Any later document that repeats "no folder exists" without this correction is out of date. The coordinator audit (see `NEXT_ACTIONS.md`) should reconcile the starting-condition wording against this section.

## 3. Repository status

### 3.1 Git / version control

| Item | Status |
|---|---|
| `~/workspace` as a git repository | **No.** CHECKED BY TEAM 1: `git rev-parse` reports "not a git repository". `~/workspace` is NOT a git repository. |
| `~/workspace/psx-intelligence-ai` as a git repository | **No.** No `.git` directory was observed for this project. |
| Remote, branch, commit history, tags | **None.** Nothing to audit. Do not invent a remote URL, branch name, or commit. |
| Implication for Phase 2 | Version control, branching, review, and release process are all still to be specified and set up. Until then, files in this folder are unversioned working documents. The coordinator must decide (in Phase 2 planning only) where the canonical repository will live, under the PKR 0 constraint — i.e. without assuming a paid hosting plan. Local git (no remote) is a zero-cost option; any remote/hosting choice needs its own cost and terms check. |

### 3.2 Files created by Team 1 (this team, Phase 1 only)

All paths are under `~/workspace/psx-intelligence-ai/`. These are the ONLY files Team 1 wrote.

| # | File | Purpose |
|---|---|---|
| 1 | `docs/phase-01/REPOSITORY_AUDIT.md` | This file. |
| 2 | `docs/phase-01/PRODUCT_REQUIREMENTS.md` | Complete functional specification for all 21 product modules (see §6 and that file). No application code. |
| 3 | `PROJECT_STATUS.md` | Phase 1 status: docs only; what does not exist; blockers / UNVERIFIED items; no real trades; stop after Phase 1. |
| 4 | `DEVELOPMENT_LOG.md` | Dated 2026-11-04 Phase 1 log: starting condition, decisions in this document set, files created, work deferred to other teams without claiming it. |
| 5 | `NEXT_ACTIONS.md` | Immediate next actions after Phase 1 docs: coordinator audit, fix loop, then Phase 2 planning only; do NOT start Phase 2 until Phase 1 audit passes; per-UNVERIFIED-item verification checks. |
| 6 | `MASTER_WORKFLOW.md` | The mandatory 11-stage workflow every task must follow. |
| 7 | `WORKFLOW_STAGE_TRACKER.md` | Honest per-stage status for Phase 1 work. |
| 8 | `TASK_TRACKER.md` | Phase 1 tasks with status. |

No other file in this project was written by Team 1. In particular, Team 1 did not write any `.py`, `.js`, `.ts`, `.sql`, configuration, Dockerfile, CI, or deployment file. Tiny illustrative snippets may appear inside specifications only where they clarify a data shape or rule; they are not runnable application code and must not be treated as an implementation.

### 3.3 Sibling-team files observed in this project (REFERENCE ONLY — do not edit)

CHECKED BY TEAM 1 (2026-11-04 directory listing at the start of Team 1's turn): the following files already existed in `~/workspace/psx-intelligence-ai/` when Team 1 first listed the folder. Team 1 has not read them as its own work, has not verified their contents, and has not modified them. They are listed here only so the audit does not under-count what sits in the folder, and so a reader does not mistake them for Team 1 deliverables.

**Snapshot warning (added at the end of Team 1's turn):** sibling teams were writing concurrently during Team 1's turn — by the end of the turn the folder contained additional sibling files beyond the list below (including, as observed in the final listing, further agent/database/data-source/deployment/forecasting documents and a root `ZERO_COST_REGISTER.md`). This list is therefore a start-of-turn snapshot, NOT an exhaustive end-of-turn inventory. The coordinator audit must take a fresh listing. Nothing in this warning changes Team 1's boundary: Team 1 wrote only its 8 files and touched no sibling file.

- `MASTER_ROADMAP.md` (project root)
- `docs/phase-01/AGENT_ARCHITECTURE.md`
- `docs/phase-01/AGENT_REGISTRY.md`
- `docs/phase-01/DATABASE_DESIGN.md`
- `docs/phase-01/FINANCIAL_FORMULAS.md`
- `docs/phase-01/MASTER_ROADMAP.md`
- `docs/phase-01/PHASE_BREAKDOWN.md`
- `docs/phase-01/SYSTEM_ARCHITECTURE.md`
- `docs/phase-01/SYSTEM_ARCHITECTURE_DIAGRAM.md`
- `docs/phase-01/TECH_STACK_DECISIONS.md`
- `docs/phase-01/ADR/` (directory; contents not audited by Team 1)

**Audit caution:** the presence of sibling documents (architecture, database, formulas, agents, roadmap) does NOT mean those designs are approved, implemented, costed, or consistent with each other or with Team 1's requirements. Cross-document consistency is a coordinator-audit task (see `NEXT_ACTIONS.md`), not something Team 1 certifies here. If any sibling document assumes a paid service, a live database, or a Phase 2 start, that assumption conflicts with the PKR 0 / stop-after-Phase-1 rules in Team 1's files and must be flagged in the fix loop — Team 1 does not silently resolve it by editing the sibling file.

### 3.4 Reference scaffold — `~/workspace/psx-data-collection/` (NEVER overwrite or touch)

This is a SEPARATE folder, not part of PSX Intelligence AI. Team 1 references it; Team 1 does not own, move, copy, or modify it.

CHECKED BY TEAM 1 (2026-11-04 directory listing + file reads for reference purposes only):

| File | What it is (as stated in its own README) |
|---|---|
| `README.md` | Scaffold status: "SCAFFOLD ONLY, not a live collector run yet." Documents the primary/backup design, the multi-node 404 quirk, the licensing warning, and next steps requiring user confirmation before any live run. |
| `DATA_SOURCE_REGISTRY.md` | Source registry. Last reviewed 2026-11-04, from public READMEs / portal landing page only. "Verified" there means the README/portal page itself states it — not that a live run in the workspace confirmed it. |
| `psx_collector.py` | Stdlib-only collector core (~5.5 KB as listed): provenance on every record, PKT (Asia/Karachi) timestamps, stale/missing detection, conflict handling (both prices kept, never silently merged), raw vs processed separation, configurable polling/cache/backoff/retry/recovery. Live fetching is delegated to an injected client, so the module itself makes no live PSX call. |
| `test_collector_offline.py` | Offline tests using a fake client (no network, no PSX call): PKT conversion, stale detection, missing-session detection, conflicting-price handling. |
| `coverage.json` | Coverage tracker template. Every company is `unknown` until a real, verified run documents it. Template includes an OGDC entry with all fields `unknown` except `intraday_history: not_available_via_psxdata`, and economic-indicator entries for SECP/SBP/PBS/Finance Division all `unknown`. Company master registry status: `not_built`. |
| `__pycache__/` | Python bytecode cache directory. Not a deliverable; ignore for audit purposes. |

**Starting-condition reuse (verbatim substance):** the scaffold's offline tests are stated in the starting condition as passing. Team 1 did NOT re-run those tests in this turn and therefore does NOT present a fresh test-pass claim of its own. The scaffold's own claim remains the scaffold's claim. Any Phase 2 testing strategy must re-run them under its own record (see `PRODUCT_REQUIREMENTS.md` §2, testing rules).

**What the scaffold does NOT prove:** full-market coverage, live quote/EOD correctness, financial-statement availability, announcement completeness, or economic-indicator availability. Its README and registry are explicit that those remain unproven. Team 1 repeats that position; it does not upgrade it.

### 3.5 `~/workspace` root context (REFERENCE ONLY — not project files)

CHECKED BY TEAM 1: `~/workspace/` contains many unrelated user folders and, at its root, several `*.md` files from other work (including, as listed on 2026-11-04, `AGENT_PROGRESS.md`, `API_SPECIFICATION.md`, `DATABASE_DESIGN.md`, `DEVELOPMENT_ROADMAP.md`, `PROJECT_AUDIT.md`, `SECURITY_DESIGN.md`, `SYSTEM_ARCHITECTURE.md`, `TEST_AND_DEPLOYMENT_PLAN.md`).

Team 1's hard rule, honoured in this turn: **do NOT touch `~/workspace/*.md` files.** Those root files are NOT PSX Intelligence AI project files, are NOT listed as this project's deliverables, and must not be cited as evidence for this project's status. They are mentioned here only to prevent a future reader from mistaking a same-named root file (e.g. root `DATABASE_DESIGN.md`) for this project's `docs/phase-01/DATABASE_DESIGN.md` (a sibling-team file) or for any Team 1 file. If a root file's content ever appears relevant, it must be re-verified and explicitly imported by the coordinator — never silently assumed to apply.

## 4. Existing dependencies

### 4.1 Toolchain actually present (CHECKED BY TEAM 1)

| Tool | Version / result | Notes |
|---|---|---|
| Python | **3.12.3** | `python3 --version` output in this turn. Compatible in principle with the scaffold's stdlib-only code and, per the scaffold registry, with `psxdata`'s stated Python 3.11+ requirement — but compatibility is NOT installation, and no package was installed in Phase 1. |
| Node.js | **v24.22.1** | `node --version` output in this turn. No Node project, `package.json`, or frontend code exists yet in this project, so Node is available toolchain, not an existing dependency of the product. |
| Docker | **NOT installed** | `which docker` returned nothing. Do not assume containers. |
| PostgreSQL client (`psql`) | **NOT installed** | `which psql` returned nothing. Do not assume a PostgreSQL server exists. |
| Redis client (`redis-cli`) | **NOT installed** | `which redis-cli` returned nothing. Do not assume a Redis server exists. |
| Git | Present as a command, but **no repository** (see §3.1) | Availability of the `git` binary is not a repository. |

### 4.2 Language / library dependencies of the product

**None exist yet for PSX Intelligence AI.** There is no `requirements.txt`, `pyproject.toml`, `package.json`, lockfile, or vendor directory in this project (CHECKED BY TEAM 1 — none listed).

Dependencies that Phase 2 planning may *consider* — and only consider, subject to the PKR 0 rule, licence check, and coordinator approval — include:

- `psx-dps` (MIT, zero dependencies, no API key) — primary market-snapshot candidate, per scaffold registry. Not installed, not vendored, not imported by this project.
- `psxdata` (MIT, PyPI, alpha 0.1.0a1) — backup market/EOD candidate. Not installed. Alpha status means its APIs may change before 1.0.
- Python standard library only (as demonstrated by the reference scaffold) — the zero-cost, zero-install baseline for any early collector work.

**Forbidden assumptions:** no paid SDK, no proprietary data vendor, no LLM API client, no broker API client, and no cloud SDK may be added to a dependency list in Phase 1 on the basis that "it will probably be free" or "a free tier probably covers it". A free tier is not PKR 0 unless its limits, expiry, and terms are documented and the design works inside them without payment — and even then the coordinator must record that check. See `NEXT_ACTIONS.md` for the per-item verification checks.

### 4.3 What "free/open-source first" means here (binding interpretation)

1. Prefer free, openly licensed components and public, machine-readable sources.
2. A paid API may be *discussed* only after a written record shows why free sources are insufficient for a specific, named requirement — and even then it is NOT approved by that discussion. Purchase requires separate, explicit approval, which Phase 1 does not grant.
3. "Free to view" on a website is not "free to redistribute", "free for commercial use", or "free to republish as a feed". Each use needs its own licence/terms check (see §7).
4. No component may be specified in a way that silently requires payment later (e.g. a database, hosting, or monitoring choice whose free option expires, caps out, or requires a card). If a Phase 2 design cannot be built at PKR 0, that must be stated as a blocker, not hidden behind a "free tier" label.

## 5. Existing infrastructure

**None confirmed.** This is the complete, honest position:

| Infrastructure | Status |
|---|---|
| Application / web server | None. No server process, no framework, no deployed URL. |
| Database server | None confirmed. No PostgreSQL (or any other) server was found. No schema has been applied anywhere. Sibling `DATABASE_DESIGN.md` is a document, not a running database. |
| Cache / queue (Redis or equivalent) | None confirmed. `redis-cli` absent; no cache server observed. |
| Container runtime / orchestration | None. Docker absent. |
| CI/CD pipeline | None observed. |
| Hosting / domain / TLS | None. No hosting account, domain, or certificate is claimed. Do not assume permanent free hosting exists. |
| Monitoring / logging service | None. No paid or free monitoring service is assumed. Local log files are the only zero-cost baseline, and even their retention/storage cost must be treated as local operating expense, not "free". |
| Backup / disaster recovery | None. No backup job, snapshot, or restore procedure exists. |
| Secrets / credentials store | None for this project. No API key, broker credential, or password is stored, requested, or assumed. Phase 1 forbids sign-ups, credentials, and API keys. |
| AI/LLM service | None. No LLM subscription, model endpoint, or API key exists or is assumed. Any future AI feature must be specified against a PKR 0 route first (local / free-tier-with-documented-limits / user-supplied-and-optional), and must degrade gracefully without it. Do not specify a feature that only works with a paid model. |

**External operating expenses (disclose, never call free):** the machine this work runs on, its electricity, and its internet connection are real costs borne outside the project budget. Team 1's PKR 0 statement covers project spend (APIs, subscriptions, hosting, services) — it does not claim that running a computer costs nothing. Any Phase 2 cost document must keep that distinction explicit.

## 6. Missing components — complete checklist

Nothing in this section exists as a working component. "Missing" means: no code, no running service, no verified data, no deployment. Sibling Phase 1 *documents* about a component do not make the component exist.

### 6.1 All 21 product modules (see PRODUCT_REQUIREMENTS.md for the full spec)

Missing as working software (all 21):

1. Landing page — 2. Registration / authentication — 3. Market dashboard — 4. Company explorer — 5. Individual company intelligence — 6. Financial statements — 7. Fundamental analysis — 8. Technical analysis — 9. Sector analysis — 10. News / announcements — 11. Valuation — 12. Forecasting — 13. Recommendations — 14. Risk analysis — 15. Portfolio optimization — 16. Investment screener — 17. AI research centre — 18. Alerts centre — 19. Research report generation — 20. Agent monitoring — 21. Administrative dashboard.

The original 8-group framing (A–H) from the first Team 1 brief maps onto these 21 modules and is preserved as a cross-reference inside `PRODUCT_REQUIREMENTS.md` §1.3, so no earlier scope is lost in the expansion. The 21-module list is authoritative for Phase 2 planning.

### 6.2 Architecture layers (PROPOSED checklist only — architecture is deferred)

The first Team 1 brief referred to "all 8 architecture layers" without naming them in Team 1's assignment. Team 1 does **not** invent an authoritative 8-layer architecture here. The following is a *checklist of layer-shaped gaps* for the architecture team / coordinator to confirm, rename, merge, or replace — every row is currently missing as a working layer:

| # (checklist only) | Layer-shaped gap | Current state |
|---|---|---|
| L1 | Presentation / user interface (public site + authenticated app) | Missing — no UI code. |
| L2 | API / gateway / request handling | Missing — no API code. |
| L3 | Application / business services (modules 1–21 logic) | Missing — no service code. |
| L4 | AI agent layer (research, analysis, monitoring agents) | Missing — no agents running. Sibling agent documents are documents only. |
| L5 | Data collection / ingestion (incl. provenance, stale/conflict rules) | Missing as a project component. Reference scaffold only (separate folder, stdlib core, no live run claimed as project delivery). |
| L6 | Processing / analytics / modelling (ratios, technicals, valuation, forecasting, risk) | Missing — formulas documents are not running calculations. |
| L7 | Storage (database, raw-payload store, file/object store) | Missing — no database, no store. |
| L8 | Infrastructure / operations (deployment, jobs, logging, monitoring, backup) | Missing — no deployment, jobs, or monitoring. |

If the architecture team defines a different layer count or names, that definition supersedes this checklist — but it must still account for every row above (no layer may disappear without a written reason), and it must still respect PKR 0.

### 6.3 Other missing components

- **Database:** no database, no schema applied, no migrations, no seed data, no backup. All database dependencies in `PRODUCT_REQUIREMENTS.md` are *required-for-Phase-2* statements, not descriptions of existing tables.
- **Agents:** no agent is running, scheduled, or monitored. Agent names in the requirements are roles to be specified/built, not live processes.
- **Background jobs / scheduling:** no collector job, no refresh job, no alert job, no report job exists or is scheduled.
- **Authentication / user accounts:** no user store, no login flow, no session handling exists.
- **External integrations:** no integration is connected — no PSX feed connection, no broker, no email/SMS/push provider, no payment provider (and none is to be added for payments under PKR 0).
- **Deployment:** no environment (dev/staging/production), no release, no rollback plan has been executed.
- **Tests for this project:** no project test suite exists. The reference scaffold's offline tests belong to the separate scaffold folder (see §3.4) and are not this project's suite. Phase 1 testing work is strategy definition only (see §8).
- **Legal / licence clearances:** no PSX redistribution licence, no data-terms clearance, no privacy/legal review has been completed or documented for this project. See §7.

## 7. Technical constraints (binding for Phase 2 planning)

1. **PKR 0 absolute.** No paid API, subscription, hosting, database, storage, monitoring, or AI/LLM subscription anywhere in the design unless a separate, explicit approval and a written "free insufficient" record exist. Until then, the design must work — or explicitly degrade — at zero project spend.
2. **Free/open-source first, with proof.** See §4.3. A claim of "free" needs a source (licence + terms + limits), not an assumption.
3. **Undocumented PSX endpoints are unstable.** PSX publishes no official public API/documentation for the portal's data endpoints (per `psx-dps` FAQ as cited in the scaffold registry). Endpoints can change without notice. Any design that depends on a single undocumented endpoint without a fallback, a failure mode, and a stale-data display is non-compliant.
4. **Multi-node quirk is a design input, not trivia.** The DPS portal is served by several nodes; some return 404 for data routes while serving the website (per `psx-dps` README as cited in the scaffold). A collector must probe/pin/re-probe rather than treat a 404 as "no data". Phase 2 must carry this rule forward; Phase 1 does not implement it here.
5. **No commercial redistribution rights assumed.** PSX market data is PSX's to license. "Free to view" ≠ "free to republish/resell". No feature in `PRODUCT_REQUIREMENTS.md` may be read as authorising redistribution, resale, or republication of a live PSX feed. Commercial use requires a prior licence/terms check, recorded in writing.
6. **No bypassing of controls.** Do not bypass authentication, access controls, or rate limits; do not scrape in a way that violates a site's terms; respect `429` / backoff / cooldown behaviour. The scaffold's stated rules (cross-process 1 req/s limit for `psx-dps`, 429 stops) are design constraints to carry forward, not numbers to "optimise away".
7. **Provenance, PKT time, stale/missing/conflict rules are non-negotiable.** Every record carries `source`, `source_timestamp`, `collected_at_pkt`, and freshness (Asia/Karachi). Stale data is flagged, never silently presented as live. Missing sessions are recorded, never filled with estimates. Conflicting prices are kept side-by-side, never silently merged. Raw payloads are stored separately from processed records. A quote is never called "real-time" merely because it was fetched recently — its source timestamp is shown.
8. **No historical intraday archive is assumed.** `psxdata`'s README states daily OHLCV + live snapshots only; `psx-dps` offers today's ticks only. Any feature requiring historical intraday bars is UNVERIFIED and must be flagged as such in its module spec, not designed as if the archive exists.
9. **Symbol/coverage reconciliation is mandatory before any completeness claim.** ~496 trading symbols (psx-dps market watch) vs ~1,029 listed instruments (psx-dps claim) vs 1000+ tickers (psxdata claim) vs 38 sectors (psx-dps) vs 37 sectors (psxdata) — these numbers disagree because they count different things. No module may claim "all PSX companies" until a reconciled company master registry exists (status in `coverage.json`: `not_built`).
10. **Forecasts and recommendations are probabilistic, never guaranteed.** All forecasts show uncertainty (range/scenarios, not a single guaranteed price). BUY / HOLD / SELL / WATCHLIST are probabilistic recommendations with uncertainty shown, not guarantees, not investment advice, and not trade instructions. The system must NOT execute real trades initially — and recommendations must never be wired to execution in Phase 1 or Phase 2 planning without a separate, explicit decision.
11. **No invented APIs, endpoints, prices, or capabilities.** If a requirement needs an endpoint, field, price, or capability that is not verified in a cited public source, the requirement must say UNVERIFIED and state what check would verify it. Phase 2 must not build on an invented endpoint.
12. **Phase 1 data discipline.** Phase 1 is documentation + read-only inspection only. No full-scale live data collection was performed or authorised in Phase 1. Any "live" number appearing in a Phase 1 document must be traceable to a cited public page/ README read, with its date, or be labelled as an example (clearly marked illustrative, not a real quote).
13. **11-stage workflow discipline.** Every task follows brainstorm → research → validate → data inspection → architecture planning → implementation specification → documentation → testing strategy → independent audit → correction → checkpoint, with no stage skipped (see `MASTER_WORKFLOW.md`). Testing strategy means defining how future components WILL be tested — it does not mean claiming future tests have passed.

## 8. Data sources — verified vs UNVERIFIED (summary; full registry is deferred)

This table reuses the verified starting condition and the scaffold registry. It does not upgrade any UNVERIFIED item. Full per-source verification is deferred to the data-sources team and to the checks in `NEXT_ACTIONS.md`.

| Source | Position at end of Phase 1 (Team 1) |
|---|---|
| PSX Data Portal — `dps.psx.com.pk` | Portal exists (VERIFIED starting condition: portal landing page read 2026-11-04). Machine-use coverage, endpoint stability, and licence terms: UNVERIFIED beyond the portal page itself. |
| `psx-dps` (MIT, zero deps, no API key) | README claims VERIFIED as README statements only (see §3.4): ~496 trading symbols, ~5y EOD, today's ticks, 38 sectors, 224k+ announcements, multi-node 404 quirk, no official PSX API. Live-run proof in this workspace: NOT DONE in Phase 1 — UNVERIFIED as a working integration. |
| `psxdata` (MIT, PyPI, alpha 0.1.0a1) | README claims VERIFIED as README statements only: daily OHLCV + live snapshots ONLY, no historical intraday archive, tickers 1000+, sectors 37, fundamentals claimed. Live-run proof: NOT DONE in Phase 1 — UNVERIFIED as a working integration. Fundamentals claim in particular needs a live sample check before any reliance. |
| Eulerpool Financial Data API | Vendor to evaluate ONLY. States NO PSX-specific coverage on the page read (VERIFIED starting condition). Never a PSX source. No paid API approved. Any future mention must carry that warning. |
| SECP (`secp.gov.pk`) | UNVERIFIED for machine use (coverage, format, licence not yet checked). |
| SBP (`sbp.org.pk`) | UNVERIFIED for machine use. |
| PBS (`pbs.gov.pk`) | UNVERIFIED for machine use. |
| Finance Division (`finance.gov.pk`) | UNVERIFIED for machine use. |
| World Bank | UNVERIFIED for machine use in this project (not yet checked for the specific indicators this product would need). |
| IMF | UNVERIFIED for machine use in this project. |
| FRED | UNVERIFIED for machine use in this project. |
| Listed-company investor-relations sites | UNVERIFIED per company (formats vary; needs a per-company registry). |
| Any broker, exchange feed vendor, or paid data vendor | NOT approved, NOT connected, NOT assumed. |

## 9. Initial recommendations (Phase 1 only — none authorises Phase 2 build)

1. **Coordinator audit first.** Reconcile this audit against sibling Phase 1 documents (architecture, database, agents, formulas, roadmap, tech stack). Flag any paid-service assumption, any "implemented" wording for a document-only design, and any inconsistency with PKR 0 / no-trades / stop-after-Phase-1. Fix loop before any Phase 2 planning (see `NEXT_ACTIONS.md`).
2. **Freeze the scope language.** Adopt the 21-module list in `PRODUCT_REQUIREMENTS.md` as the single scope vocabulary. Retire loose phrases like "the dashboard" or "the AI" unless they name a numbered module.
3. **Treat the scaffold as a pattern, not a product.** Carry forward its provenance / PKT / stale / missing / conflict / raw-vs-processed rules into every Phase 2 data design. Do not copy its code into this project without a Phase 2 decision, a licence check (stdlib + MIT libraries), and a test record.
4. **Verify data sources in the order the product needs them.** Market snapshot/EOD first (psx-dps vs psxdata sample comparison on a small, named symbol set — e.g. OGDC as in the scaffold example — under Phase 2 planning, not Phase 1 collection), then announcements/fundamentals, then economic indicators. Do not start with the hardest source (per-company financials) before the market-data fallback is proven.
5. **Decide storage at PKR 0 before designing features that assume it.** Local file/SQLite-style storage on local hardware is the only zero-cost baseline that needs no subscription; any server database, hosted storage, or managed service needs a cost/terms record first. Do not let module specs silently assume a server database exists.
6. **Keep AI features degradable.** Every AI-dependent module in `PRODUCT_REQUIREMENTS.md` states what it shows when no model is available (cached analysis, rules-based summary, or an explicit "unavailable" state). Phase 2 must not make core market/company data depend on a paid model.
7. **Keep legal review on the critical path.** PSX redistribution/commercial-use terms, website terms for every scraped/queried source, and the investment-advice disclaimer for every recommendation/forecast surface must be checked and recorded before any public launch planning — not after a build.
8. **Do not start Phase 2 on the strength of this audit alone.** This audit documents absence and constraints. Phase 2 planning begins only after the coordinator audit passes and the fix loop closes (see `NEXT_ACTIONS.md` and `WORKFLOW_STAGE_TRACKER.md`).

## 10. Acceptance check for this document

- [x] Current environment/state documented accurately: no git repo, no application, no database, no deployment; Python 3.12.3 / Node v24.22.1 present; Docker / psql / redis-cli absent.
- [x] Existing files listed: Team 1 files (§3.2), sibling files observed (§3.3, reference only), scaffold files (§3.4, reference only), workspace-root context (§3.5, reference only, untouched).
- [x] Existing dependencies listed: none for the product; toolchain only (§4).
- [x] Existing infrastructure listed: none confirmed (§5).
- [x] Missing components listed: all 21 modules, all 8 layer-shaped gaps, DB, agents, jobs, auth, integrations, deployment, tests, legal clearances (§6).
- [x] Technical constraints listed: PKR 0, free/open-source first with proof, undocumented-endpoint instability, no redistribution rights assumed, provenance/PKT/stale/missing/conflict rules, probabilistic-only forecasts/recommendations, no invented capabilities (§7).
- [x] Initial recommendations given without authorising a build (§9).
- [x] UNVERIFIED items labelled, not upgraded (§8 and throughout).
- [x] PKR 0, no-real-trades, and stop-after-Phase-1 rules stated explicitly (§1, §7, §9).

---

*Team 1 — Repository Audit + Product Requirements — Phase 1 only. This file creates no code, no database, no deployment, and no Phase 2 commitment.*
