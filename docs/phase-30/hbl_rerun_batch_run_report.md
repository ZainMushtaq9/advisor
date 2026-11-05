# HBL Re-run Batch — Run Report (2026-11-05)

Branch: `phase-hbl-reruns` (from Phase 30 tip `8937338` + cherry-pick
`cb2eb7e`, the Phase 7 HBL extraction). This report is the batch's own
record; the parent consolidates the three register files separately, and
no register file was edited here.

## Verdict

**PARTIALLY COMPLETE** — every item in batch scope is done and measured,
and the system verdict follows the new acceptance run (below). The
partiality comes only from pre-existing items outside batch scope: G5
human sign-off (user/parent), defect D-05 (measured open), defect D-12
(token-gated approval, needs a covering brief), and the PSX Terms gate
(user-owned). No verdict was upgraded by hand: every gate below is a
measured runner result.

**Headline: gate G1 flipped to MET on measured evidence.** All four
company chains pass, including HBL's full chain.

## What changed

HBL (Habib Bank Limited, company 747, COMMERCIAL BANKS) joined every
downstream phase that excluded it, under the binding banking rule:
Phase 9 uses the bank residual-income model for HBL, never industrial
models; where no banking adaptation exists the metric is
`not_applicable` with the banking reason, never an industrial number.
All HBL rows are UNVERIFIED (single source, rule H1); no row was
promoted to VERIFIED or PARTIALLY_VERIFIED. No new PSX market data was
collected, no broker/order path was touched, no Docker was used, no
merge to main, no existing branch tip moved.

### Per-phase counts (before → after; HBL added)

| Phase | Table | Before | After | HBL |
|---|---|---|---|---|
| 7 (base) | financial_documents / statements / line items / opinions | 4 / 118 / 2,116 / 4 | unchanged | 1 / 30 / 800 / 1 (pre-batch extraction) |
| 8 | fundamental_metric_values | 108 | 144 | 36: 20 computed / 15 insufficient / 1 not_applicable |
| 8 | financial_health_assessments | 24 | 32 | 8 |
| 8 | fundamental_warning_events | 8 | 8 | 0 |
| 9 | valuations | 51 | 68 | 17: 3 computed / 10 insufficient / 4 not_applicable |
| 10 | company_macro_exposures | 6 | 9 | 3 |
| 10 | sector_metric_profiles | 120 | 156 | 36 |
| 11 | news_events / news_event_companies | 7 / 3 | 8 / 4 | 1 earnings event (2026-03-03) |
| 12 | ownership_holdings / corporate_action_records | 34 / 5 | 112 / 9 | 78 holdings / 4 dividends |
| 13 | forecast_assessments | 120 | 156 | 36, all abstained (0 computed) |
| 14 | risk_metric_values / risk_control_checks / stress_results | 81 / 7 / 10 | 95 / 8 / 12 | 14 (3 computed / 11 insufficient) / 1 PASS / 2 insufficient |
| 15 | decisions | 4 | 5 | 1 new row dated 2026-11-05 (see below) |
| 16 | simulated_portfolios | 3 | 3 | unchanged by design (baseline scope) |
| 17 | backtest_runs | 5 | 5 | unchanged (all NOT_RUNNABLE, single price date) |
| 18 | orchestration_tasks / orchestration_runs | 6 / 1 | 7 / 1 | 1 new task `hbl_ticker_resolution` |
| 19 | rag_documents / rag_chunks | 3 / 943 | 4 / 2,020 | 1 document / 1,077 chunks (407 text pages) |
| 19 | rag_benchmark_cases / results | 6 / 6 | 7 / 12 | 1 case / 6 results (new run 6/6 PASS) |
| 19 | rag_access_audits / rag_answers | 9 / 0 | 21 / 1 | 12 audits / 1 stored HBL profit answer |
| 20 | screen_runs / screen_results | 5 / 1,418 | 6 / 1,422 | 1 run (dividend_payers, as-of 2026-11-05) + 4 results |
| 21 | alert_runs / alerts / alert_deliveries | 18 / 89 / 89 | 36 / 89 / 89 | 0 new alerts (see below) |
| 22 | reports / report_figures / sections / exports | 22 / 541 / 188 / 66 | 25 / 649 / 214 / 75 | 3 DRAFT reports / 108 figures / 26 sections / 9 exports |
| 25 | job_definitions / job_runs | 8 / 71 | 8 / 73 | drift_check runs 72 (finding) + 73 (confirm) |
| 26 | evaluation_runs / evaluation_metrics | 1 / 44 | 2 / 105 | 1 run / 61 metrics |
| 27 | observability_runs | 1 | 3 | 2 runs (finding + confirm) |
| 29 | acceptance_runs / scenarios / recomputations / defects | 1 / 15 / 15 / 14 | 3 / 14 / 15 / 14 | see acceptance section |

```
HBL rows added per phase (count of new rows touching HBL content)
P8  ████████████████████████████████████████ 44 (36 values + 8 health)
P9  █████████████████ 17
P10 ███████████████████████████████████████ 39 (3 exposures + 36 profiles)
P11 █ 1 (+1 link)
P12 ██████████████████████████████████████████████████████████████████████████████████ 82
P13 ████████████████████████████████████ 36
P14 █████████████████ 17 (14 values + 1 check + 2 stress)
P15 █ 1
P18 █ 1
P19 ████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████ 1,096 (1,077 chunks + 19 rows)
P20 █████ 5 (1 run + 4 results)
P21 (0 alerts; 18 runs are run rows, not alerts)
P22 █████████████████████████████████████████████████████████████████████████████████████████████████████████████ 143 (3 + 108 + 26 + 9, minus overlaps)
```

### Computed vs NOT_CALCULABLE (HBL, with banking reasons)

- **Phase 8 (bank-adapted map):** operating margin 0.435367, net
  margin 0.184887, ROA 0.009702, ROE total 0.148461 / owners
  0.148904, ROCE 0.102786, debt/assets 0.936611, debt/equity
  14.7755. Gross / current / quick / cash / receivables /
  inventory / payables margins are insufficient (no bank analogue);
  interest_coverage is not_applicable (markup is a bank's cost of
  funds, not interest on industrial debt).
- **Phase 9:** trailing P/E **6.291996** (close 286.16 on 2026-11-03 /
  EPS 45.48 published 2026-03-03); book value total
  488,614,705,000, owners 486,943,716,000. EV and DCF are
  not_applicable for banks; residual_income:bank APPLIES but is
  insufficient (no source-backed cost of equity or forecasts — never
  invented).
- **Phase 10:** rates_markup_income (income), rates_funding_cost
  (cost), fx_income (income) — all UNVERIFIED, issuer-evidenced.
- **Phase 11:** earnings event 2026-03-03 ("HBL Annual Report 2025",
  summary cites PAT 66,763,916 / EPS 45.48, ≤280 chars).
- **Phase 12:** ownership from Annual Report pp. 397–398 (PDF pp.
  399–400), two extractors agreed; largest holder AGA KHAN FUND
  829,967,872 / 56.58; printed % sum 99.96 vs 100.00 (rounding).
  Dividend CF total 26,610,622,000 vs CE appropriation sum
  26,770,058,000 differ by 159,436,000 (timing) — no single total
  asserted. 4 dividends, all dates NULL (FY2025 final 4.25,
  interims 4.50 / 4.50 / 5.00).
- **Phase 13:** abstained on all 36 (series: close 1, return 0,
  volume 1, earnings 2) — single price date, honestly abstained.
- **Phase 14:** volume tier MEDIUM (525,393 vs median 54,631.5),
  largest_holder 56.58, top3 76.52; 8 series insufficient;
  turnover insufficient; 2 sensitivity insufficient; 0 new flags
  (latest period end 2025-12-31 is 309 days before 2026-11-05,
  under 365; publication known).
- **Phase 15 — new HBL decision dated 2026-11-05** (new grain; the
  2026-11-04 v1 row cannot be overwritten and stays as history):
  **SCREEN_PASS / HOLD_CANDIDATE / WITHHELD / LOW, total 0, 6/7
  dimensions, gates [], 1 conflict** (profitability 73.3333 vs
  earnings_quality 20.0000). Old row preserved:
  SCREEN_NOT_RUNNABLE / INSUFFICIENT_EVIDENCE / WITHHELD / NONE,
  −1, 2 dimensions, gates [no_statements, too_few_dimensions].
- **Phase 16:** UNCHANGED by design — the baseline is defined over
  the 3 original statement companies (`ew_statements_3_balanced`);
  HBL quote ELIGIBLE at 286.16 proven by the runner. Expanding the
  portfolio universe needs a new portfolio brief (new names +
  Phase 17 ledger re-derivation) — follow-up, not done.
- **Phase 17:** UNCHANGED — 5 runs NOT_RUNNABLE (single price date).
- **Phase 18:** new task `hbl_ticker_resolution` (depends on
  discover; resolves HBL by ticker: close 286.16, 30 statements,
  36 values, latest decision 2026-11-05 SCREEN_PASS); run
  checkpoint updated to completed 6; HUBC close re-verified
  197.2400 after. Old task checkpoints keep pre-batch counts
  (3/88/108) as history.
- **Phase 19:** HBL indexed (seed + face pages 74 auditor / 75 SFP
  / 76 P&L / 78 CE / 79 CF; publication proxy 2026-03-03); **NUL-byte
  strip fix** in `index_document_pages` (HBL text layer carries
  NULs, found p.93 — PostgreSQL rejects NUL, so the first commit
  failed and rolled back cleanly). Benchmark case
  `hbl_missing_document` RETIRED (premise ended; row + r3 results
  preserved, new runs evaluate only current code cases and report
  retired ones as skipped); replacement `hbl_profit_cy2025`
  direct_evidence p.76 fragment "66,763,916" PASSED rank 2; new run
  `phase19-benchmark-2026-11-05-hbl` 6/6, recall 1.0. HBL query now
  returns direct_evidence (5 HBL citations, snippets ≤500 chars +
  ellipsis, no body served).
- **Phase 20:** only dividend_payers changed — new snapshot as-of
  2026-11-05 (1 run + 4 results), MATCH 2→3 (HBL MATCH 1/1, max DPS
  5.00, dates unknown; old NO_MATCH row preserved). Other screens'
  HBL outcomes verified unchanged (liquid MATCH, volume NO_MATCH
  at percentile 76.13, cheap_profitable INSUFFICIENT_DATA with
  SECTOR_NOT_APPLICABLE — the bank rule honored by the filter
  itself, P/E 6.29 NOT forced into a match, technical
  INSUFFICIENT_DATA).
- **Phase 21:** ZERO new alerts (verified: pre-existing HBL alert
  rows = 0, contradicting the brief's "one high-volume alert"
  claim — HBL volume 525,393 < 1,000,000 threshold). HBL earnings
  suppressed STALE (2026-03-03, 247 days), HBL dividends
  suppressed NO_EVENT_DATE (now 9 total, was 5); latest run rows
  record STALE 2 / NO_EVENT_DATE 9.
- **Phase 22:** 3 new HBL reports, all DRAFT, QA passed: dossier 56
  figs / 1 warn / 10 sections, earnings 25/1/8, valuation 27/1/8
  (ids 23/24/25); dossier cites the 2026-11-05 decision and P/E
  6.291996; exports md/html committed under
  `docs/phase-22/reports/`, PDFs gitignored under
  `storage/research_reports/`. NOT added (spec enumerates company
  reports only): a COMMERCIAL BANKS sector outlook — follow-up.

### Code mechanisms added (all default-preserving)

- Decision `--decision-date` (runner + CLI); screener `--as-of`
  (runner + CLI, incl. a `would_write` fix and a reused-branch
  NameError fix found by the second commit).
- Portfolio `mean_variance_gate` now takes the live assessment
  count (was hardcoded "120", now 156).
- Orchestration `DEMO_TASKS` +1 with checkpoint-count refresh on
  re-run; RAG retired-case filter in `run_benchmark`; news API
  scope note "4 companies" (was 3).
- Evaluation golden suite: `golden_refusal_hbl_missing` RETIRED,
  replaced by `golden_hbl_indexed_evidence` (exactly one HBL
  document); `golden_extraction_chunk_counts` updated 3/943 →
  4/2020 with a batch note. Old case row + Phase 26 result stay
  as history.
- Observability: `_drift_reason()` caps the drift SLO reason for
  VARCHAR(1000) (full pairs stay in evidence JSON); the stale
  `known_hbl_pending` exception is resolved and no longer seeded
  (Phase 27 run row stays as history).
- Jobs: `EXPECTED_COUNTS` updated to batch-end live counts (see
  baseline section).
- Acceptance: `chain_hbl_partial` replaced by `chain_hbl_full`
  (core links gate; risk_flags / portfolio_holdings / alerts
  informational for HBL by design); `missing_source` RETIRED
  (premise ended); `model_failure`, `corporate_action`, and
  `provenance_warnings` now assert invariants instead of pinned
  Phase 29 counts (120 assessments, 5 actions, 22 reports); gate
  chain key updated and the stale D-03 else-text made generic.
- Defects: D-03 MEASURED at run time (`resolve_d03_status`,
  mirroring D-05); D-04 marked fixed (see below).

## Refreshes (in order)

### Dashboard verification

API smoke all 200 for HBL by ticker (securities, fundamentals
FY2025 annual audited consolidated, valuations 17 methods, macro,
ownership, risk, news, decisions showing the 2026-11-05 row,
reports, market latest 286.16 on 2026-11-03, screener dividend
latest 2026-11-05 / 3 MATCH). Frontend webpack production build
succeeded; vitest 11 passed; Playwright phase23 suite **22/22
passed** (35.6s) with the phase23 config. First Playwright
attempt without the config failed on missing baseURL (relative
`page.goto`) — a harness invocation error, not a product failure;
re-run with `--config=playwright.phase23.config.ts` passed.
Servers stopped after verification (uvicorn :8000, next :3000).

### Evaluation re-run — `phase26-evaluation-2026-11-05-hbl`

| | Before (Phase 26) | After |
|---|---|---|
| Metrics | 44 (32 computed / 11 not_evaluable / 1 not_applicable) | **61 (49 / 11 / 1)** |
| Golden cases | 14 / 14 PASS | **14 / 14 PASS** (1 retired case row + 1 new case = 15 rows) |
| Drift differences | 0 | **17** (the HBL additions; see below) |
| Promotion gates | 5 | 5, all NOT_MET |
| Promoted models | 0 | **0** (no promotion; model cards unchanged at 9) |

The 2 initially failing golden cases were the retired-premise
cases (`golden_refusal_hbl_missing`, `golden_extraction_chunk_counts`),
not regressions — investigated before committing, then updated
with batch notes (above). Second `--commit` wrote 0 (idempotent).

### Observability re-runs

| Run | SLOs met / unmet / total | Exceptions open / total | Drift SLO |
|---|---|---|---|
| Phase 27 (pre-batch) | 10 / 4 / 14 | 6 / 6 | met (0) |
| `phase27-observability-2026-11-05-hbl` | 9 / 5 / 14 | 6 / 6 | **unmet (17)** |
| `phase27-observability-2026-11-05-hbl-confirm` | 10 / 4 / 14 | 5 / 5 | **met (0)** |

The 5th unmet SLO in the finding run is `drift_difference_count`
(17) — the drift SLO working as designed. The 4 other unmet SLOs
are pre-existing (price coverage, session gap, previous close,
news coverage). The drift SLO reason is now capped at 381 chars
(full pairs in evidence). Second `--commit` of the finding run
was skipped_existing.

### Jobs — drift_check

- Run 72 (`drift_check`, 2026-11-05): **succeeded, drift_count 17**
  with the full expected/live table list as evidence — a finding,
  never auto-fixed.
- After the baseline update, run 73 (manual, no date key — a dated
  re-run replays run 72 by idempotency design): **succeeded,
  drift_count 0**.

### Baseline update (WITH evidence, per the Phase 25 rule)

`EXPECTED_COUNTS` in `backend/app/services/jobs/registry.py`
updated to batch-end live counts (documents 4, statements 118,
line items 2,116, opinions 4, fundamentals 144, profiles 156,
valuations 68, news 8, ownership 112, assessments 156, risk 95,
decisions 5, chunks 2,020, screen results 1,422, reports 25,
figures 649, data_sources 20; all other keys unchanged), with a
doc note citing the HBL evidence. **data_sources 19 → 20 is NOT
a batch change:** the pre-batch backup `2026-11-05T0642-PKT`
manifest already lists 20 — the Phase 24 baseline undercounted
by one and is corrected here with that manifest as evidence.
Confirmed by the observability confirm run (drift 0) and job
run 73 (drift 0).

### Acceptance — NEW runs

| Run | Verdict | Scenarios | Recomputations | Defects open |
|---|---|---|---|---|
| Phase 29 (`phase29-acceptance-2026-11-05`) | PARTIALLY COMPLETE | 15 (12 pass / 0 fail / 1 blocked / 2 not_evaluable) | 14 matched / 1 expected mismatch | D-04, D-12 |
| HBL interim (`...-hbl`) | FAILED | 14 evaluated + retired rows (8 pass / 4 fail / 1 blocked / 2 not_evaluable) | 13 / 2 (both known exceptions) | D-04, D-05, D-12 |
| **HBL rerun (`...-hbl-rerun`)** | **PARTIALLY COMPLETE** | **14 (12 pass / 0 fail / 0 blocked / 2 not_evaluable)** | **13 / 2 (both known exceptions)** | **D-05, D-12** |

The interim FAILED run is kept as history: its 4 scenario fails
were stale pinned Phase 29 counts (assessments 120, actions 5,
reports 22) and the by-construction `chain_hbl_partial` blocked
outcome — investigated, then fixed by measuring invariants
instead of pinned counts (above), never by rewording a verdict.

**New gate table (measured, `...-hbl-rerun`):**

| Gate | Result | Evidence |
|---|---|---|
| G1 critical workflows | **MET** | All four company chains pass (HBL core chain full) |
| G2 defects resolved | MET | 0 critical, 0 high defects open |
| G3 no fabrication | **MET** | Point-in-time pass; forecasts abstain honestly; recomputations match except documented D-05 omissions and the expected HBL drift |
| G4 repo clean | MET | All security/licensing/privacy scans pass (branch-tip boundary noted) |
| G5 auditor sign-off | PARTIAL | Evidence complete; human sign-off belongs to the user/parent and is pending |

**G1 flipped to MET on measured evidence.** Verdict is
PARTIALLY COMPLETE (not COMPLETE) only because G5 stays partial.
Recomputation mismatches (2) are both in the documented known
exceptions: `report_figure_census` (D-05) and
`drift_vs_phase24_baseline` (expected HBL drift).
Defects: D-03 **fixed** (measured live: HBL fundamentals,
valuations, decision, reports all present), D-04 **fixed**
(name/ticker keying + fixture tests), D-13 fixed, D-05 open
(measured — census moved with HBL figures; the stale
`event_brief news:HUBC:earning` figure persists), D-12 open,
remainder accepted. 0 critical, 0 high, 6 medium, 8 low overall
(D-05 medium open; D-12 low open).

## Tests

| Suite | Result |
|---|---|
| Backend pytest (full) | **468 passed** (Phase 30: 453; batch added 15) |
| Frontend vitest | **11 passed** |
| Playwright phase23 | **22 / 22 passed** |
| Per-phase suites re-run in the batch | P8 +1, P9 +1, P10 17, P11 10, P12 9, P14 16, P15 13, P16+P17 24, P18 13, P19 23, P20 20, P21 14, P22 22, P26 14, P27 12, P29 22 — all pass |

## VM-replacement recovery (this session, after the batch phases)

Mid-batch the VM was replaced (uptime 1 min, no PostgreSQL, no
`postgres` user, `/tmp` fresh). Home persisted: the worktree and
all uncommitted batch edits survived intact.

1. **PostgreSQL 16 reinstalled without apt:** the VM ships no
   Ubuntu archive sources except a boot-time `ubuntu.sources`
   (azure + cogent mirrors); apt's proxy config uses the
   unauthenticated egress URL while direct HTTPS (authenticated
   env proxy) works, so `apt-get update` fetched no Ubuntu lists.
   Fix used: `Packages.xz` fetched via curl (env proxy) and the
   8 required `.deb`s installed with `dpkg` (postgresql-16
   16.15, client, common, libpq5, libllvm17t64, libjson-perl,
   ssl-cert). Cluster `16/main` created and started; role
   `psx_app` + database `psx_intelligence` recreated per
   `docs/phase-02/DATABASE_SETUP.md` (password only from
   `database/.env`, never printed).
2. **Restore shortcut (verified, not improvised):** instead of
   the 1230 base + full re-run chain, the verified Phase 30
   backup `2026-11-05T0642-PKT` was restored (manifest SHA
   verified by `restore.sh`; manifest counts match the pre-batch
   verified state exactly: documents 4, statements 118, line
   items 2,116, fundamentals 108, valuations 51, decisions 4,
   chunks 943, metrics 44). Migration head already 0024.
3. **Phases 8–22 re-run in order** on the restored DB with the
   batch branch code; every post-phase count reproduced the
   original batch exactly (table above).
4. **Two mid-recovery corrections** (my own over-broad re-runs,
   fixed before proceeding, both verified to exact batch counts):
   - Decision runner without `--company HBL` wrote 4 rows dated
     2026-11-05 (one per company); the 3 non-HBL rows (ids 5–7)
     were deleted, keeping the HBL row (id 8, SCREEN_PASS /
     HOLD_CANDIDATE / WITHHELD). Decisions back to exactly 5.
   - Screener runner without `--screen dividend_payers` wrote 5
     runs + 1,418 results as-of 2026-11-05; the 4 non-dividend
     runs (ids 6–8, 10) + 1,414 results were deleted, keeping
     run 9 (dividend_payers, MATCH 3). Runs back to exactly 6,
     results to exactly 1,422.
5. Refreshes (evaluation, observability, jobs, baseline,
   acceptance, dashboard, full tests) then re-ran on the
   recovered DB and reproduced every batch number above.

## Stale-evidence items carried honestly (history, not errors)

- MARKET `forecast_abstention_rate` row still cites 120/120
  evidence (grain exists, runner cannot update by design; true
  count now 156/156, rate still 100%).
- Stored HBL portfolio-exclusion reasons cite the pre-batch
  decision; old decision / screen / RAG-case rows preserved as
  above; the retired golden case, benchmark case, observability
  exception, and acceptance scenario rows stay in the database
  as history, unevaluated in new runs.
- Readiness endpoint still hardcodes
  `EXPECTED_MIGRATION_HEAD = "20261104_0023"` vs correct
  `20261104_0024` (pre-existing Phase 27 artifact, needs its own
  brief — NOT batch scope).
- D-12 token-gated report approval still open (needs a covering
  brief).

## Remaining blockers (with exact unblockers)

| Blocker | Unblocker |
|---|---|
| PSX Terms gate (permission) | Written PSX permission evidence (user-owned). The claimed reply was deleted by the user; no PSX email without a new user instruction. Reply-watch cron `psx-permission-reply-watch` still active. |
| G5 human sign-off | User/parent sign-off on this acceptance evidence. No signature claimed. |
| D-05 (medium, open) | Clean re-derivation in the correct order (news fixed before decisions and reports) that removes the stale `event_brief news:HUBC:earning` figure, or an accepted-census update with evidence. |
| D-12 (low, open) | A covering brief for token-gated report approval. |
| Readiness endpoint head | Its own brief to correct `0023` → `0024`. |
| Portfolio universe expansion (HBL in portfolios) | A new portfolio brief (new names + Phase 17 ledger re-derivation). |
| COMMERCIAL BANKS sector outlook | A brief enumerating it (Phase 22 spec enumerates company reports only). |
| More trading days / technical values / forecasts / backtests | More price days (Terms-gated). |
| KSE-100 expansion | Per-company source verification (Phase 7 blocker, unchanged). |

## Hard stops honored

No new market-data collection; no VERIFIED/PARTIALLY_VERIFIED
promotion; no Docker; no merge to main; no force-push or history
rewrite; no existing branch tip moved; advisor repo only; no
CSVs or PDFs committed (HBL PDF gitignored, never committed);
no credentials printed, logged, or committed (role password only
in `database/.env`, mode 0600); no live auth accounts (auth
0/0/0); no register file edited
(`PHASE_COMPLETION_REGISTER.md`, `PROJECT_EXECUTION_STATE.md`,
`MASTER_EXECUTION_LOG.md` untouched — parent consolidates).
