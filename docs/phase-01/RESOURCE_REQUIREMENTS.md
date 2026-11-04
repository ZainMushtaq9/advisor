# PSX Intelligence AI — Resource Requirements

> Every figure is labelled VERIFIED (with source), ESTIMATE (with basis
> and range), or UNVERIFIED (with the check needed). Estimates here are
> planning arithmetic to be replaced by measured actuals in Phase 06/07
> reports and Phase 30's handover — they are not measured results.
> Budget context: PKR 0 absolute (see `COST_ESTIMATION.md`); resources
> below are therefore local-machine resources unless Scenario 3 verifies
> a free online service at deployment time.

## EOD volume arithmetic (ESTIMATE — shown in full, not asserted as measured)

**Basis (stated, so the arithmetic can be checked):**
- Trading universe: ~496 symbols (VERIFIED, 2026-11-04).
- Listed universe: ~1029 symbols (VERIFIED, 2026-11-04).
- EOD history span: ~5 years (VERIFIED as a `psx-dps` source property).
- Trading days per year: ~250 (ESTIMATE — approximate trading calendar;
  actual trading days vary by year and holidays, which is why the totals
  below are ranges, and why Phase 06's backfill report is the authority
  over this estimate).
- Trading days in ~5 years: 5 × ~250 = **~1,250 days (ESTIMATE)**.

**Row counts (ESTIMATE arithmetic):**
- Trading universe: 496 × 1,250 = **620,000 EOD rows (ESTIMATE)**.
- Full listed universe (if every listed symbol had a full 5-year history,
  which it does not — listed-only symbols lack trading history, so this
  is an upper-bound illustration, not an expected row count):
  1,029 × 1,250 = **1,286,250 EOD rows (ESTIMATE upper bound)**.
- Realistic expected store: close to the trading-universe figure, plus
  partial histories for symbols that listed/delisted within the window.
  Phase 06's report replaces this with actuals per symbol.

**Storage per row (ESTIMATE):**
- Assumed stored row content: symbol reference, date, open/high/low/close,
  volume, source reference, provenance link. Assumed size:
  **~150–300 bytes per row (ESTIMATE)** — a planning assumption, not a
  measured SQLite page calculation; actual size depends on schema, types,
  and page layout chosen in Phase 03.
- Trading-universe EOD data alone: 620,000 × 150–300 bytes =
  **~93–186 MB (ESTIMATE)**.
- With indexes (ESTIMATE multiplier 1.5×–2.5× on data size, for
  symbol+date, sector, and screen-filter indexes):
  **~140–465 MB total for the trading-universe EOD store (ESTIMATE)**.
- Listed-universe upper bound, same method: 1,286,250 × 150–300 bytes =
  ~193–386 MB data, **~290–965 MB with indexes (ESTIMATE upper bound)** —
  again, not expected, because listed-only symbols do not all have full
  histories.

**Daily volumes (ESTIMATE):**
- New EOD rows per trading day: **~496 rows/day (ESTIMATE)** — one per
  trading symbol, before quarantine exclusions.
- New EOD rows per trading year: 496 × ~250 = **~124,000 rows/year (ESTIMATE)**.
- Snapshot rows per refresh: **UNVERIFIED count** — depends on how many
  symbols the verified snapshot source returns on a given day; Phase 07's
  refresh reports are the authority. Snapshot storage is short-retention
  (Phase 03 policy), so it does not accumulate like EOD history.
- Statement / announcement / news / macro rows: **UNVERIFIED** — zero
  until Phases 08, 09, 10, 14 verify a source; no volume is estimated for
  data that may not arrive.

## Compute, memory, and scaling (ESTIMATE unless noted)

| Resource | Local development (Phases 01–05) | Full local operation (Phases 06–30, Scenario 2) | Label / basis |
|---|---|---|---|
| CPU | Any current developer machine; no special CPU required | Same machine class; backfill and full-universe screen/forecast runs are batch jobs, not interactive loads | ESTIMATE — no benchmark is claimed; Phase 27 measures actual runtimes and replaces this with measured figures |
| RAM | Within a normal developer-machine allocation; SQLite + Python stdlib workloads for fixtures | Same, with headroom for full-universe in-memory operations (screens, sector aggregates) — batch in chunks if memory pressure is observed, rather than assuming a larger machine | ESTIMATE — no RAM benchmark is claimed; chunking is the documented fallback, not a purchase |
| Disk | < 1 GB for code + fixtures + early DB | **~0.5–1 GB (ESTIMATE)** for the full trading-universe EOD store with indexes, plus logs, dossiers, and snapshots (short retention) — see arithmetic above; allow growth of ~124,000 rows/year (~19–37 MB/year data, ~28–93 MB/year with indexes, ESTIMATE) | ESTIMATE arithmetic above |
| Network | None for offline work; free-source fetches only for collectors | Periodic fetches for daily refresh + snapshots; no continuous connection required | ESTIMATE volume — request counts UNVERIFIED (see below) |
| AI inference | None in development (Phase 01 defines, does not run, AI) | Free/local AI only; token counts are ESTIMATE ranges below; no paid inference | ESTIMATE (counts); price UNVERIFIED and not used |

**No benchmark is claimed.** No "queries per second", "forecast latency",
or "dashboard load time" figure appears in this document, because none
has been measured. Phase 27's performance baseline and Phase 29's
re-measurement are where measured figures first appear.

## API requests, agent executions, AI token usage (ESTIMATE / UNVERIFIED)

| Quantity | Figure | Label / basis |
|---|---|---|
| Backfill requests (Phase 06) | Not stated as a single figure | **UNVERIFIED** — depends on the verified sources' request granularity (per symbol? per symbol-year? per batch?), which Phase 1 does not measure (no full-scale live collection in Phase 1). Illustrative arithmetic only: *if* 1 request per symbol, ~496 requests (ESTIMATE conditional); *if* 1 per symbol-year, ~2,480 requests (ESTIMATE conditional). Neither is the plan until Phase 06 measures it. |
| Daily refresh requests (Phase 07) | Same granularity caveat as backfill | **UNVERIFIED** — measured by Phase 07 refresh reports |
| Snapshot requests | Per refresh cycle, source-dependent | **UNVERIFIED** — measured by Phase 07 reports |
| Agent executions (Phases 25–26) | 1 dossier run per company per scheduled cycle is the design unit; full-universe dossier cycles therefore scale with the covered universe (~496 companies, ESTIMATE count from the verified trading universe) | ESTIMATE (count) — frequency (daily/weekly) is set in Phase 27, not assumed here |
| AI token usage per dossier (Phase 26) | **~2,000–8,000 tokens per dossier (ESTIMATE range)** — basis: a dossier summarising stored figures across ~10 sections, each section tens to low hundreds of tokens of cited output plus input context; the range is wide because section coverage depends on gated inputs (08/10/14) | ESTIMATE (counts only) — no token price is stated; only free/local AI is permitted, so token counts are a local-resource planning figure, not a bill |
| AI token usage, full-universe dossier cycle | ~496 dossiers × 2,000–8,000 tokens = **~1–4 million tokens per full cycle (ESTIMATE)** | ESTIMATE arithmetic from the per-dossier range; actuals logged per run in Phase 18/25 |
| AI token usage, single-company explanation (Phase 18) | **~500–2,000 tokens per explanation (ESTIMATE)** — basis: one forecast/target/recommendation explained with cited figures | ESTIMATE (counts only) |

## Per-phase resource profile

| Phase | Main resources | Scaling note |
|---|---|---|
| 01 Requirements and architecture | Documents only; negligible compute/storage | None |
| 02 Repository and development environment | Local repo + toolchain; < 1 GB (ESTIMATE) | Grows with code only |
| 03 Database architecture | Schema + fixtures; negligible | Fixture size only until Phase 06 |
| 04 PSX company registry | ~496–1,029 registry rows (VERIFIED counts); negligible storage | Row count is the universe, not a scaling risk |
| 05 Backend foundation | Code + logs; log growth is the only scaling item (rotate/archive per Phase 27) | Log retention policy caps growth |
| 06 Historical market data collector | Batch fetch + EOD store (~140–465 MB ESTIMATE, trading universe) | One-off backfill; re-runs are idempotent, not additive |
| 07 Market snapshot collector | Snapshot store (short retention) + daily refresh (~496 rows/day ESTIMATE) | Daily growth ~496 rows/day; snapshots do not accumulate (retention-capped) |
| 08 Financial statement collector | Framework only until verified; then statement tables (volume UNVERIFIED) | Gated — no volume assumed |
| 09 Corporate announcement collector | Framework only until verified; then announcement tables (volume UNVERIFIED) | Gated — no volume assumed |
| 10 Macroeconomic data collector | Framework only until verified; then series tables (volume UNVERIFIED) | Gated — series are few, revisions are versioned, not overwritten |
| 11 Fundamental analysis | Computed metrics over stored data; storage proportional to symbols × periods | Recomputable; store or compute-on-demand per Phase 27 measurement |
| 12 Technical analysis | Compute-on-demand by default; cache only if measured need | Indicator windows are bounded; no unbounded storage |
| 13 Sector intelligence | 38 sectors × dates aggregates (small vs EOD store) | Negligible vs EOD store |
| 14 News intelligence | Framework only until verified; then news tables (volume UNVERIFIED) | Gated — no volume assumed |
| 15 Financial health scoring | Scores per symbol per date (small vs EOD store) | Versioned; old versions retained per policy |
| 16 Valuation engine | Valuations per symbol per method per date (small) | Sensitivity ranges add columns, not rows at EOD scale |
| 17 Statistical forecasting | Forecasts per symbol per horizon per method (small vs EOD store) | Training is batch; history window is bounded |
| 18 AI forecasting | Free/local AI compute; token counts per table above | Local compute is the constraint, not a bill; log usage |
| 19 Price target engine | Targets per symbol per horizon (small) | History retained; past targets immutable |
| 20 Backtesting | Backtest runs over history (compute-bound, batch) | Batch jobs; results stored per run, not per day at EOD scale |
| 21 Risk management | Risk measures per entity per date (small) | Windows bounded |
| 22 Investment recommendation engine | Recommendations per symbol per date (small) | History retained; reasoning traces add text, not EOD-scale rows |
| 23 Portfolio optimization | Manual holdings (user-entered, small) + computed views | User-scale, not market-scale |
| 24 Independent audit | Audit work; negligible system resources | Human process, not a scaling item |
| 25 Multi-agent orchestration | Agent runs + logs; log growth capped by retention policy | Execution logs are the scaling item — rotate/archive |
| 26 Autonomous company research | Dossiers (~496 per full cycle ESTIMATE) + AI tokens (~1–4M per cycle ESTIMATE) | Cycle frequency (Phase 27) controls load |
| 27 Scheduling and monitoring | Job logs + freshness state; small, retention-capped | Log rotation caps growth |
| 28 Frontend and dashboard integration | Dashboard code + preferences (local, small) | Full-universe views must paginate/filter — enforced by Phase 29 checks |
| 29 Security and production hardening | Review + hardening changes; backup storage (one full DB copy per backup, ~140–465 MB ESTIMATE per copy) | Backup count × DB size is the storage item — retention policy caps it |
| 30 Full PSX rollout and final verification | Full-universe verification runs (batch) + handover pack | One-off verification load; local fallback always available |

## Scaling triggers (when to act, and how — without purchasing)

| Trigger (measured, not assumed) | Action (PKR 0) |
|---|---|
| EOD store growth exceeds local disk headroom | Archive old snapshots/logs first; then prune non-essential history only under a documented retention change — never silently delete EOD history |
| A batch job (backfill, screen, forecast, dossier cycle) exceeds its scheduled window | Chunk the job, run it in parts, or reduce its frequency (Phase 27) — not a larger machine purchase |
| Dashboard view slow on full-universe tables | Paginate/filter, add an index, or cache a computed aggregate (Phase 29, only where measurement proves the need) |
| Free/local AI too slow for a full dossier cycle | Reduce cycle frequency or dossier scope (Phase 27) — not a paid AI service |
| A verified free online service (Scenario 3) changes/withdraws | Revert that component to local operation (Scenario 2) under the permanent-free-hosting caveat |
| Log growth dominates disk use | Enforce log rotation/archival (Phase 27 policy) |

## Resource requirements per scenario

- **Scenario 1 (zero-budget local development):** one developer machine,
  local disk for code + fixtures + early DB (< 1 GB ESTIMATE), no network
  except free-source fetches during collector development.
- **Scenario 2 (zero-subscription local operation):** same machine (or
  any machine meeting the local profile above), disk ~0.5–1 GB ESTIMATE
  for the full trading-universe store plus backups/logs, periodic network
  for refresh/snapshots, machine on at scheduled times (operational
  limitation, disclosed in `COST_ESTIMATION.md`).
- **Scenario 3 (conditional zero-cost online deployment):** only components
  covered by a verified free service move online; all other components
  keep their Scenario 2 local profile. No resource figure is asserted for
  a free service until Phase 30 verifies its terms and limits.
