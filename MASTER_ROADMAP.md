# PSX Intelligence AI — Master Roadmap (Summary)

> **Phase 2 update (2026-11-04):** Phase 1 accepted as a specification checkpoint; Phase 2 implemented and independently audited (see docs/phase-02/PHASE_2_ACCEPTANCE_REPORT.md). Phases 3–30 remain as specified in the canonical Phase 1 roadmap; Phase 3 is NOT started by this update. Phase 2 branch for push: phase-02-repository-foundation; merge to main: NOT MERGED pending separate approval.

> **Canonical version:** `docs/phase-01/MASTER_ROADMAP.md` is canonical.
> This root file is a summary only. If the two ever disagree, the docs
> version governs and this file must be corrected. Phase numbers, titles,
> and objectives here are copied from the canonical version — no different
> phase numbers or objectives are introduced here.

## Phase 1 status and stop rule

**IN PROGRESS — Requirements and architecture only.** Phase 1 is complete
only when the coordinator audit passes, followed by correction and a
checkpoint (Phase 1 workflow stages 9–11). **STOP AFTER PHASE 1 — do not
begin Phase 2.** Phases 2–30 are documented only.

**Starting condition (verified 2026-11-04):** Project folder is new;
`~/workspace/psx-data-collection/` is a separate scaffold to reference but
never overwrite. Python 3.12.3, Node v24.22.1 verified. Docker, `psql`,
`redis-cli` NOT installed. Verified: `psx-dps` (MIT, zero deps, no API key,
~496 trading vs ~1029 listed, ~5y EOD, today's ticks, 38 sectors,
multi-node 404 quirk, no official PSX API); `psxdata` (MIT, PyPI, alpha
0.1.0a1, daily OHLCV + live snapshots ONLY, no historical intraday archive);
Eulerpool: NO PSX coverage, vendor only, no paid API approved.
**UNVERIFIED:** machine-use of SECP / SBP / PBS / Finance Division /
World Bank / IMF / FRED, and machine-readable sources for financial
statements, corporate announcements, and news — gated phases list
verification as a blocker, never assume the feed.

**Budget: PKR 0 absolute.** No paid APIs, subscriptions, hosting, DB,
storage, monitoring, or AI services in any phase. If a free solution
cannot satisfy a requirement, document the limitation; do not introduce
a paid alternative. Local hardware / electricity / internet are EXTERNAL
operating expenses, disclosed as such, never called free. Zero-cost online
deployment only where a legitimate free service is verified at deployment
time, with the permanent-free-hosting caveat (free terms can change or be
withdrawn; the system must always remain runnable locally).

**Trading rule:** The system must NOT execute real trades initially.
Phases 19, 22, 23, 25, and 26 are analysis and reporting only, probabilistic
with uncertainty stated, never guaranteed, never connected to a broker.

**Phase 1 workflow (11 stages):** brainstorm → research → validate →
data inspection read-only only (NO full-scale live data collection in
Phase 1) → architecture planning → implementation specification →
documentation → testing strategy defined not claimed passed → independent
audit → correction → checkpoint.

## 30-phase table (exact named list, in order)

| # | Phase | One-line objective |
|---|-------|--------------------|
| 01 | Requirements and architecture | Complete, auditable Phase 1 spec; no code, no later phase started; audit + correction + checkpoint. |
| 02 | Repository and development environment | Version-controlled repo + reproducible local dev environment on free tooling. |
| 03 | Database architecture | Local-first DB design (SQLite dev; PostgreSQL-compatible schema), migrations, backup/restore. |
| 04 | PSX company registry | Authoritative registry: ~496 trading vs ~1029 listed, 38 sectors, listing status, sector membership. |
| 05 | Backend foundation | Shared backend: config, logging, provenance, errors, module boundaries, free/local only. |
| 06 | Historical market data collector | Resumable, idempotent ~5y EOD backfill from verified sources; 404-quirk handling; no intraday claim. |
| 07 | Market snapshot collector | Today's snapshots from verified sources, freshness-labelled, no live polling / real-time guarantee. |
| 08 | Financial statement collector | Framework + field model + verification checklist first; statement data only on a verified source. |
| 09 | Corporate announcement collector | Framework + announcement model + verification checklist first; data only on a verified source. |
| 10 | Macroeconomic data collector | Framework + verification checklist first; SECP/SBP/PBS/Finance/WB/IMF/FRED ingestion gated on verification. |
| 11 | Fundamental analysis | Traceable fundamental analysis from verified stored data; missing inputs shown as missing. |
| 12 | Technical analysis | Deterministic technical engine over validated EOD; no indicator as a standalone buy/sell signal. |
| 13 | Sector intelligence | 38-sector aggregates + market breadth, recomputable, denominators and coverage stated. |
| 14 | News intelligence | Framework + taxonomy + verification checklist first; news data only on a verified, lawfully usable source. |
| 15 | Financial health scoring | Transparent health scores with formula, inputs, limitations published alongside every score. |
| 16 | Valuation engine | Valuation with methods, assumptions, sensitivity ranges; withheld/range-bounded if inputs missing. |
| 17 | Statistical forecasting | Transparent statistical baselines, out-of-sample evaluated, probabilistic with error bands. |
| 18 | AI forecasting | AI explanation/forecast layer citing stored numbers, uncertainty stated, no invented figures; free/local only. |
| 19 | Price target engine | Probabilistic, range-based price targets as information only; must NOT execute real trades. |
| 20 | Backtesting | Honest EOD-only backtests with survivorship, look-ahead, cost/slippage limitations stated. |
| 21 | Risk management | Risk measurement/reporting as analysis and disclosure; no position opened/closed by the system. |
| 22 | Investment recommendation engine | Transparent recommendation records (inputs, reasoning, uncertainty, limits); information only, no trading. |
| 23 | Portfolio optimization | Portfolio analysis/optimisation suggestions over manual holdings; analysis only, no broker, no live rebalancing. |
| 24 | Independent audit | Independent audit (not the implementing team) of data, calculations, provenance, outputs. |
| 25 | Multi-agent orchestration | Orchestrated agents, read-only defaults, approval gates, execution logs; never trade/post/send alone. |
| 26 | Autonomous company research | Scheduled research dossiers from verified stored data only, cited, gaps labelled; no autonomous trading/posting. |
| 27 | Scheduling and monitoring | Scheduling + monitoring on free/local tooling; stale/failed jobs visible; approved channels only. |
| 28 | Frontend and dashboard integration | Dashboard integrating all views, with source, as-of date, uncertainty, limitations on-screen. |
| 29 | Security and production hardening | Hardening: validation, credentials, access control, licence compliance, backup/restore, security review. |
| 30 | Full PSX rollout and final verification | Full-universe rollout, final verification, handover pack, open-items register; online only via verified free service, with permanent-free-hosting caveat. |

Full objectives, outputs, and dependencies: canonical
`docs/phase-01/MASTER_ROADMAP.md`. Full task-level detail:
`docs/phase-01/PHASE_BREAKDOWN.md`. Dependencies and critical path:
`docs/phase-01/PHASE_DEPENDENCY_MAP.md`. Acceptance:
`docs/phase-01/TASK_ACCEPTANCE_MATRIX.md`. Costs and resources:
`docs/phase-01/COST_ESTIMATION.md` and
`docs/phase-01/RESOURCE_REQUIREMENTS.md`. Free coverage and gaps:
`docs/phase-01/FREE_VS_PAID_COMPARISON.md`.

## Non-goals (all phases)

No broker integration or auto-trading; no guaranteed real-time feed,
forecast, target, or return; no historical intraday archive unless a future
verified source provides one; no purchase or paid service (PKR 0 absolute);
no licensed-data redistribution beyond actual licence terms.
