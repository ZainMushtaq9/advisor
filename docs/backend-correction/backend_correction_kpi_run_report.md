# Backend Correction + KPI Testing — Run Report (2026-11-05)

**Branch:** `backend-correction-kpi` (new; from `news-intelligence`
`57f77ec` + merge of `d05-readiness-g5` `261eab8`, clean, zero
conflicts, tip `d00c6ba` at merge, plus the CORS fix commit below).
**No existing branch tip moved. No merge to main. Main `eb6025b`
untouched. No history rewritten.**
**Task split honored:** backend code correction + KPI testing only.
No host account created, no payment, no Docker, no register file
edited (proposed entry supplied separately in this directory).
No business-row write except the deterministic re-derivation in §2
and run-history appends (each recorded with before/after counts).
No deletion of any business row. No status promotion anywhere
(all re-derived rows UNVERIFIED as before). No live auth account
(auth 0/0/0 throughout).

## 1. Branch-line map and chosen deploy branch

| Branch | Tip | Backend pieces it carries |
|---|---|---|
| `phase-30-release` | `8937338` | Deployed frontend's line. Backend at migration head **0024**. No news engine, no HBL batch code, no blockers fixes. Readiness constant (Phase 27 artifact) `0023` — stale. |
| `phase-hbl-reruns` | `c71469a` | HBL batch code (Phases 8–22 ticker-keyed, D-03/D-04 fixes, `EXPECTED_COUNTS` batch-end baseline). Chain head 0024. |
| `news-intelligence` | `57f77ec` | HBL batch + news engine: migration **0025** (9 tables), 6 GET-only news endpoints, 3 frontend pages, 3 jobs (2 collection PAUSED + 1 digest). Chain head 0025. |
| `d05-readiness-g5` | `261eab8` | HBL batch + blockers: D-05 census fix (389/244/16=649), risk runner `--as-of-date`, readiness retargeted to **0025**, D-12 brief, G5 package (unsigned), portfolio brief. Chain head 0024 — so on that branch alone the 0025 constant tracks the *live* head, not its own chain head (truthful not-ready on a bare checkout). |
| **`backend-correction-kpi`** | **this branch** | **news-intelligence + d05-readiness-g5 merged.** Chain head **0025** and readiness constant **0025** — the constant now matches the branch's *own* chain head, so the old "tracks live head, not chain head" caveat is closed by the merge itself. |

**Deploy branch: `backend-correction-kpi`.** It is the only line that
contains everything: HBL batch code, news engine + migration 0025,
blockers fixes, and the CORS fix in §3. Merges still needed: none.
Merge conflicts: none (the two change sets touch zero common files;
verified with `comm` on the file lists before merging).

## 2. VM-replacement recovery (this session, before any KPI work)

The session started with a fresh PostgreSQL 16 cluster (only
`postgres`/`template` databases; no `psx_app` role, no
`psx_intelligence` database) — a VM replacement since the parent's
last verification. Home persisted, so the repo, venvs, and
`storage/backups/` survived.

1. `pg_ctlcluster 16 main start` (binaries already present; no
   reinstall needed this time).
2. Backup `2026-11-05T0642-PKT` SHA-verified before restore:
   `database.dump` SHA-256 matches manifest `8f72c170…37019`;
   `files.tar.gz` matches `18f659a7…be70c461`. (Two staging-copy
   permission failures first: the backup dir is root-only and
   `/home/hatch` is group-only, so the dump was staged under
   `/var/lib/postgresql/` for the `postgres` user; staging copies
   deleted after the restore. The backup itself was not modified.)
3. Role `psx_app` recreated (LOGIN, NOSUPERUSER, NOCREATEDB,
   NOCREATEROLE; password only from `database/.env`, never printed)
   + database `psx_intelligence` + contract grants. (First attempt
   failed silently because sourcing `.env` leaked `PGUSER`/`PGPASSWORD`
   into the `su postgres` psql invocation; diagnosed from the
   postgres log, then done with a clean environment.)
4. `pg_restore` exit 0. Post-restore counts matched the manifest
   exactly (470 / 444 / 1 price date / 118 / 2,116 / 108 / 51 / 6 /
   7 / 34 / 120 / 4 / 943 / 1,418 / 89 / 22 / 541 / 81 / 8 / 71 /
   1 acceptance run / auth 0/0/0 / head 0024), and the ticker→id
   map matched the parent-verified map (HUBC 759, NML 864, OGDC 873,
   HBL 747). The HBL Phase 7 base was already in the backup
   (30 statements, 1 document) and the HBL PDF was present in
   `storage/financial_reports/`.

### Deterministic re-derivation (restored DB → parent-verified live state)

Every runner was dry-run first, then `--commit`, in phase order.
No deletion was needed: the D-05 re-derivation proof in the
blockers task is reproduced by the HBL figures themselves
(541 + 108 = 649), and the approved census below matches exactly.

| Step | Command (scoped) | Before → After (verified) |
|---|---|---|
| P8 fundamentals | `run_fundamental_analysis.py --company HBL --commit` | values 108→144 (HBL 20/15/1), health 24→32, profiles 120→156 |
| P9 valuation | `run_valuation.py --company HBL --commit` | valuations 51→68 (HBL 3/10/4; P/E 6.291996) |
| P10 macro | `run_macro_analysis.py --commit` | exposures 6→9 |
| P11 news | `run_news_events.py --commit` | events 7→8, links 3→4 |
| P12 ownership | `run_ownership_actions.py --commit` | holdings 34→112, actions 5→9 |
| P13 forecasting | `run_forecasting.py --company HBL --commit` | assessments 120→156, all abstained |
| P14 risk | `run_risk_analytics.py --company HBL --commit` | risk 81→95, checks 7→8, stress 10→12 |
| P15 decisions | `run_decision_engine.py --company HBL --decision-date 2026-11-05 --commit` | decisions 4→5; new HBL row SCREEN_PASS/HOLD_CANDIDATE/WITHHELD/LOW/0/6 dims; 2026-11-04 row preserved |
| P16 portfolio | dry-run only | 0 writes (unchanged by design); portfolios 3 |
| P17 backtesting | dry-run only | 0 writes (all NOT_RUNNABLE); runs 5 |
| P18 orchestration | `run_orchestration.py --commit` | tasks 6→7 (`hbl_ticker_resolution`), runs 1 |
| P19 RAG | `--index --benchmark --query --access-audit --commit` | docs 3→4, chunks 943→2,020, bench cases 6→7, results 6→12, answers 0→1, audits 9→21 |
| P20 screener | `run_screener.py --screen dividend_payers --as-of 2026-11-05 --commit` | runs 5→6, results 1,418→1,422 (MATCH 3) |
| P21 alerts | `run_alerts.py --commit` (2 passes; see note) | runs 18→36, alerts 89 (0 new), latest STALE 2 / NO_EVENT_DATE 9 |
| P22 reports | `run_reports.py --commit` | reports 22→25, figures 541→649, sections 188→214, exports 66→75 |
| Migration | `alembic upgrade head` (from `database/`) | head 0024→0025, 9 news tables created |
| Jobs register | `run_jobs.py register` | job_definitions 8→11 (2 collection PAUSED + 1 digest) |
| News enforce | `run_news_intelligence.py enforce --commit` | collection_runs 0→8, all refused, no fetch |
| News reactions | `run_news_intelligence.py reactions --commit` | market_reactions 0→8, all INSUFFICIENT_DATA; articles 0 by design |
| Risk as-of | `run_risk_analytics.py --as-of-date 2026-11-05 --commit` | risk 95→98 (exactly 3 would-write rows in dry-run, 3 written) |
| Evaluation | `run_evaluation.py --run-id phase26-evaluation-2026-11-05-backend-correction --commit` | runs 1→2, metrics 44→89 (new run 45; see §5) |
| Observability | `run_observability.py --run-id phase27-observability-2026-11-05-backend-correction --commit` | runs 1→2, SLO measurements 14→28 (see §5) |
| Jobs drift | `run_jobs.py run-one drift_check --run-tag backend-correction-2026-11-05` | job_runs 71→72, drift_count 1 (risk only; see §5) |
| Acceptance | `run_acceptance.py --run-id phase29-acceptance-2026-11-05-backend-correction --commit` | acceptance_runs 1→2 (see §6) |

Note on P21 (2 passes): one alerts pass writes 9 run rows (one per
rule). The batch-end count is 36 (4 passes: 2 pre-batch + 2 batch
passes across the original batch and its recovery re-run). This
task ran 2 passes to reproduce 36 exactly; both passes created
0 alerts. The count is run history, not business data.

Note on files: `storage/research_reports/` HBL report PDFs from the
batch are not in this workspace (gitignored, lost in the VM
replacement); the committed md/html exports under
`docs/phase-22/reports/` are intact, and the PDFs regenerate from
the reports runner. No DB count depends on them.

Final live counts after re-derivation (all parent-verified values
reproduced): companies 470, prices 444 (1 date 2026-11-03),
statements 118, line items 2,116, fundamentals 144, valuations 68,
macro exposures 9, news events 8, ownership 112, assessments 156,
decisions 5, RAG chunks 2,020, screens 1,422, alerts 89, reports 25,
figures 649, risk 98, job definitions 11, auth 0/0/0, head 0025.
Run-history rows added by this task (by design, not batch
reproduction): evaluation run 2, observability run 2, job run 72,
acceptance run 2.

## 3. Backend correction #1 (the only code fix needed): CORS_ORIGINS from env crashed boot

**Defect:** `backend/app/config.py` — `CORS_ORIGINS` is a tuple
field. pydantic-settings 2.16.2 JSON-decodes complex fields from
env *before* field validators run, so the documented env format
(`backend/.env.example`: comma-separated
`CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`) raised
`SettingsError` at import/boot. The deployed origin could therefore
*not* be configured via environment — the exact host path the
deployment needs. Earlier tests never caught it: they only passed
tuples at init time, never env strings.

**Before:**
```python
CORS_ORIGINS: tuple[str, ...] = DEFAULT_CORS_ORIGINS
```
Init with a string worked (before-validator splits); env string
crashed boot.

**After (`backend/app/config.py`):**
```python
CORS_ORIGINS: Annotated[tuple[str, ...], NoDecode] = DEFAULT_CORS_ORIGINS
```
plus a hardened before-validator that accepts comma-separated
strings *and* a JSON list string. `NoDecode` delivers the raw env
string to the validator. (First attempt used `NoDecode[...]` as a
subscript; that type is not subscriptable in 2.16.2 — corrected to
`Annotated[..., NoDecode]`.)

**Regression tests:** new `backend/tests/test_cors_env_origins.py`
(7 tests: env single origin, env comma-separated + stripping, env
JSON list, env wildcard still rejected in production, defaults
unchanged, TestClient allows the configured origin incl. OPTIONS
preflight, TestClient does not allow an unconfigured origin).
All 7 pass; existing `test_errors_and_config.py` still passes.

**What was NOT changed:** CORS behavior itself — origins still come
from env only, wildcard still rejected in production, methods still
GET-only, credentials still off. No wildcard, no hardcoded origin.
The deployed origin `https://gentle-sopapillas-f33c78.netlify.app`
is allowed purely by setting the env var (verified in §4).

## 4. CORS + boot matrix (measured, TestClient + live uvicorn)

| Case | Result |
|---|---|
| Deploy config (development, auth off, `CORS_ORIGINS` = Netlify origin): GET `/api/v1/health` with Netlify `Origin` | 200, `access-control-allow-origin` = Netlify URL |
| Same config: OPTIONS preflight (`Access-Control-Request-Method: GET`) | 200, allow-origin = Netlify URL |
| Same config: GET `/api/v1/observability/readiness` | 200, head 0025, expected 0025, matches true, ready true |
| Default CORS (no env): GET with Netlify `Origin` | 200 but **no** allow-origin header (proves the env var is required) |
| Production + auth off | Boot **refused** with `ValueError` (Phase 24 safety rule intact — not a defect) |
| Production + auth on: GET `/api/v1/registry/statistics` with 0 accounts | **401** `authentication required` (fail-closed, as specified) |
| Production + auth on: GET `/health` (public path) | 200 |

**Deploy configuration for the future host (exact):**
```
ENVIRONMENT=development
AUTH_ENFORCEMENT=off
CORS_ORIGINS=https://gentle-sopapillas-f33c78.netlify.app
DATABASE_URL=<hosted Postgres URL>
```
Start command (from `backend/`, venv active):
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
Why not production yet: production boot *requires*
`AUTH_ENFORCEMENT=on`, and enforced mode is fail-closed with
0 accounts (401 on every data route). The production flip is a
separate future step gated on first-admin-account creation, which
this task must not do. Note: with `ENVIRONMENT=development` the
interactive docs (`/docs`, `/openapi.json`) are enabled; that
exposure ends at the production flip.

**Fresh-checkout deploy test:** cloned branch to scratch, created a
fresh venv, `pip install -r backend/requirements.txt` (fastapi
0.162.0), booted uvicorn with the deploy env — `/health` 200,
readiness ready true (0025/0025). Scratch checkout removed after
verification; the procedure above is what a host (e.g. Render
native Python) needs, plus `alembic upgrade head` from `database/`
against the hosted database URL before first boot.

## 5. KPI tables (all re-measured on this branch)

### 5a. Observability SLOs — run `phase27-observability-2026-11-05-backend-correction`: 9 met / 5 unmet / 14

| SLO | Measured | Target | Result | Reason |
|---|---|---|---|---|
| registry_evidence_coverage | 1.000000 | ≥ 1 | MET | — |
| price_coverage_latest_day | 0.944681 | ≥ 0.95 | UNMET | 444/470 priced; pre-existing |
| price_session_gap_weekdays | 2 | ≤ 0 | UNMET | Single trading day; pre-existing |
| previous_close_completeness | 0.000000 | ≥ 1 | UNMET | No previous close; single price date; pre-existing |
| ohlc_validity_rate | 1.000000 | ≥ 1 | MET | — |
| duplicate_ticker_rate | 0.000000 | ≤ 0 | MET | — |
| statement_document_lineage | 1.000000 | ≥ 1 | MET | — |
| statement_freshness_days | 128 | ≤ 180 | MET | Latest period end 2025-12-31 |
| news_company_coverage | 0.008511 | ≥ 0.10 | UNMET | 4/470; seed scope; pre-existing |
| reports_published_externally | 0 | ≤ 0 | MET | — |
| alert_delivery_rate | 1.000000 | ≥ 1 | MET | — |
| job_success_rate | 1.000000 | ≥ 0.95 | MET | — |
| golden_pass_rate | 1.000000 | ≥ 1 | MET | 14/14 golden (see §5b) |
| drift_difference_count | 1 | ≤ 0 | UNMET | **Risk only: expected 95, actual 98** — the 3 documented blockers as-of rows. All other 32 drift tables match. Explained, not hidden; the baseline update for risk is a parent decision (see §8). |

Current-run exceptions: 6 open (5 SLO-unmet incl. drift +
`known_collection_jobs_paused`, the documented Terms-gate pause).
Legacy run-1 rows stay as history, including `known_hbl_pending`
(open): the runner no longer seeds it and never edits run-scoped
rows by design, so the stale row persists until a parent-authorized
cleanup or a runner change — flagged, not silently fixed.

### 5b. Evaluation — run `phase26-evaluation-2026-11-05-backend-correction`: 45 metrics (33 computed / 11 not_evaluable / 1 not_applicable); golden 14/14 PASS; promotion gates 5, all NOT_MET; promoted models 0

The batch run reported 61 metrics. That is **not** a regression:
`drift_metrics` emits one metric per *differing* table
(`backend/app/services/evaluation/metrics.py`). Base metrics are
44; the batch run predated the `EXPECTED_COUNTS` baseline update,
so 17 tables differed (44 + 17 = 61). This run postdates the
baseline update, so only risk differs (44 + 1 = 45). Golden cases:
all 14 current cases pass (the retired `golden_refusal_hbl_missing`
is not evaluated; `golden_hbl_indexed_evidence` passes). Datasets
8, model cards 9, gates 5 NOT_MET, promoted 0 — no promotion, as
before.

### 5c. Jobs drift check — run 72: succeeded, 33 tables checked, drift_count 1

Drift: `risk_metric_values` expected 95, actual 98 only. All other
tables match the batch-end baseline (companies 470, securities 470,
evidence 1,001, prices 444, documents 4, statements 118, line items
2,116, opinions 4, technical runs 1 / errors 124 / values 0,
fundamentals 144, profiles 156, valuations 68, indicators 12, news
8, ownership 112, assessments 156, decisions 5, portfolios 3,
backtests 5, orchestration runs 1, chunks 2,020, screens 1,422,
alerts 89, deliveries 89, reports 25, figures 649, sources 20,
auth 0/0/0).

### 5d. Dashboard coverage KPIs

| KPI | Measured | Reason for the gap |
|---|---|---|
| Prices | 444/470 (94.5%) | DPS snapshot covers 444 securities on the single date 2026-11-03; 26 securities have no observation in the snapshot. No new collection without the Terms gate. |
| Companies with statements | 4/470 | Phase 7 sampled extraction only (HUBC, NML, OGDC, HBL). KSE-100 expansion needs per-company source verification (Phase 7 blocker). |
| News coverage | 4/470 | Seed scope: 4 earnings events + 4 macro events, 4 companies linked. DPS collection blocked on the Terms gate. |
| Forecast abstention rate | 156/156 = 100% | Single price date → no validatable return intervals; every assessment honestly abstains. |
| Decisions WITHHELD rate | 5/5 = 100% | All user-facing values WITHHELD by design (research conclusions exist for HUBC/OGDC/HBL but are not user-facing recommendations). |
| Technical values | 0/470 | 1 calculation run, 124 errors, 0 values: indicators need price series; one trading day cannot form a series. |

## 6. Acceptance — NEW run `phase29-acceptance-2026-11-05-backend-correction`: PARTIALLY COMPLETE

| Gate | Result | Evidence |
|---|---|---|
| G1 critical workflows | MET | All four company chains pass |
| G2 defects resolved | MET | 0 critical, 0 high defects open |
| G3 no fabrication | MET | Point-in-time checks pass; forecasts abstain honestly; **15/15 recomputations match**, no exceptions in force (former D-05/HBL-drift exceptions resolved 2026-11-05 and removed) |
| G4 repo clean | MET | All security/licensing/privacy scans pass (boundary: branch tips, not every historical commit) |
| G5 auditor sign-off | PARTIAL | Human sign-off pending — **no signature claimed** |

Scenarios: 14 (12 pass, 2 not_evaluable — restatement,
suspended_security — 0 fail, 0 blocked). Recomputations: 15/15
match, including `report_figure_census` (649 = 389/244/16) and
`drift_vs_phase24_baseline` (4/118/2,116). Defects: 14 (D-03/D-04/
D-05/D-13 fixed; D-12 open; remainder accepted). Verdict is
PARTIALLY COMPLETE for one reason only: G5 itself, by design.
(The one defect-key note: `resolve_d05_status` builds a dict keyed
by ticker, so HBL's two decision rows collide on one key; the check
uses HUBC/OGDC only and is unaffected — carried from the blockers
report as a future robustness note.)

## 7. Per-endpoint API smoke (TestClient, live local DB, deploy env)

134 GET routes found (FastAPI 0.162 lazy `_IncludedRouter` entries
expanded recursively). 130 hit in pass 1 (4 docs routes skipped):
103×200, 20×422 (missing query params), 6×404 (wrong id
substitutions), 1×401 (`/auth/me` without a token — correct).
Pass 2/3 with correct params resolved every 422/404:
ticker-scoped routes (`/valuations`, `/fundamentals/*`,
`/forecasting/*`, `/macro/exposures`, `/ownership`, `/actions`,
`/risk/profile`, `/news/aliases`) all 200 with HBL data;
`/evaluation/metrics` and `/golden-results` 200 for the new run;
`/backtesting/metrics?run_id=1` and `/ledger?portfolio=ew_statements_3_balanced`
200 (NOT_RUNNABLE scope note, honest); `/macro/point-in-time?indicator=cpi_yoy`
200; `/companies/747` and `/securities/747` 200 (HBL);
`/jobs/runs/72` 200 (drift_check succeeded);
`/orchestration/runs/<uuid>` 200; `/portfolios/ew_statements_3_balanced`
200; `/news-intelligence/assistant` 200 `missing_data` (0 articles,
honest); `/rag/answer` 200 `direct_evidence` (HBL p.75).
**Final: 129/130 routes return 200 with correct params; the only
non-200 is `/auth/me` 401 without a token (correct). Zero 500s.**
CORS smoke for the Netlify origin is part of §4 (GET + preflight
200 with allow-origin).

## 8. Regression counts

| Suite | Command | Result |
|---|---|---|
| Backend pytest (full) | `backend/.venv/bin/python -m pytest tests/ -q` | **542 passed** (468 HBL batch + 58 news + 9 blockers + 7 new CORS; 0 failed) |
| Frontend vitest | `frontend/node_modules/.bin/vitest run` | **11 passed** (3 files) |
| Webpack production build | `frontend/node_modules/.bin/next build --webpack` | **exit 0, 30/30 pages** (27 baseline + 3 news-intelligence) |
| Playwright phase23 | `playwright test --config playwright.phase23.config.ts` (stack up: uvicorn :8000 + `next start` :3000, both stopped after) | **22 passed** (desktop + mobile) |
| Playwright phase29 | `playwright test --config playwright.phase29.config.ts` (same stack) | **6 passed** (spec asserts blockers-run values; this run's identical values pass it) |

No suite was weakened. The one test-expectation update in this
line's history (blockers: `test_gate_g1_not_met_when_hbl_blocked`)
predates this task and documents an intended behavior change.

## 9. Remaining blockers with exact unblockers

| Blocker | Status | Exact unblocker |
|---|---|---|
| Host choice | PENDING | User picks the backend + database host (Render + Neon recommended by the parent track). No account created in this task. |
| Hosted data seeding | NOT STARTED | Fresh hosted Postgres → `alembic upgrade head` (0025) → deterministic Phases 4–22 seed chain (registry import → price ingestion → Phase 7 extraction → Phases 8–22 re-runs as in §2) → news jobs/enforce/reactions → risk as-of → refreshes. The local re-derivation in §2 is the proven recipe. |
| Netlify API URL + redeploy | NOT STARTED | Set `NEXT_PUBLIC_API_URL` to the hosted backend URL in Netlify env, rebuild/redeploy. Frontend code needs no change; error display stays honest (see §10). |
| G5 human sign-off | PARTIAL | A human completing §7 of `docs/blocker-resolution/g5_signoff_evidence_package.md`. No code or run can supply this. |
| D-12 token-gated approval | OPEN (low) | Brief's approval + its §5 decisions, then a separate implementing item. No live auth accounts exist, so token bootstrap needs its own authorization. |
| PSX Terms gate | BLOCKED | Written permission evidence (user-owned); reply-watch cron still active. No PSX email, no DPS collection, no VERIFIED promotion in this task. |
| Drift baseline (risk 95→98) | OPEN (measurement) | Parent decision: update `EXPECTED_COUNTS` risk 95→98 with the blockers as-of evidence (Phase 25 rule), or leave drift SLO unmet as the honest signal. This task reports the drift; it does not move the baseline to hide it. |
| Stale `known_hbl_pending` exception row | OPEN (cosmetic) | Runner never edits run-scoped rows by design; the row is history. Needs a parent-authorized one-time update or a runner change to resolve superseded known exceptions. |
| HBL portfolio expansion | NOT STARTED (brief only) | Approval of the portfolio brief + separate implementing item. |
| Frontend stale copy (2 pages) | OPEN (trivial) | Copy pass: company detail "Seed coverage is 3 of 470" and home statements line "3 of 470 (HUBC, NML, OGDC)" — both now 4 with HBL. (News page already corrected in the blockers line.) |
| Fresh post-batch audit (D1) | RECOMMENDED, not tasked | Parent decision to commission a fresh audit of the post-batch lineage. |
| HBL report PDFs in workspace | GAP (minor) | Regenerate via the reports runner or re-extract; md/html exports are committed and intact. |

## 10. What was NOT done (explicitly)

- No host account, no payment, no card, no trial.
- No hiding or softening of any backend error: the deployed site's
  "Backend not connected yet" / "Failed to fetch" is an
  infrastructure gap (no backend host, no API URL), not a frontend
  bug, and this task does not touch frontend error display. The
  honesty layer (missing stays missing, never estimated) is intact
  in every smoked response.
- No deletion of any business row; no overwrite of any observation
  or published statement (all refreshes are new versioned rows).
- No VERIFIED/PARTIALLY_VERIFIED promotion; no new market-data
  collection; no PSX email; no DPS collection; no broker/order path.
- No Docker anywhere. No merge to main. No force-push. No history
  rewrite. No existing branch tip moved. Advisor repo only.
- No CSVs, PDFs, `.env` files, or credentials committed. No live
  auth account. All test servers stopped at task end.
- The three consolidated register files were NOT edited (parent
  consolidates; proposed entry supplied in this directory).
