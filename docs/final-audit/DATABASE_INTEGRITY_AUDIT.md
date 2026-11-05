# Database Integrity Audit — PSX Intelligence AI (Independent Audit)

**Audit baseline:** branch `phase-30-release`, commit `8937338`.
**Audit date:** 2026-11-05 (Asia/Karachi).
**Method and scoping (read first):** the live database was in flux
during this audit because the post-handover HBL re-run batch was
actively writing HBL rows to Phases 8–22. Live counts were therefore
NOT used as audit evidence and nothing was written to the live
database. All counts below come from a SCRATCH database
(`psx_intelligence_audit`) reproduced from the documented recovery
recipe: backup `2026-11-04T1230-PKT` restored (dump SHA-256 verified,
row-count gate passed), migrated to head `20261104_0024`, then the
full phase chain re-run in order (registry → LEAP → prices → Phase 6
→ Phase 7 → HBL extraction → Phases 8–22 → Phases 25–27 → Phase 29).
The handover-time live counts (Phase 30 run report, parent-verified)
are the cross-check targets. Where scratch differs from the target,
the difference is recorded exactly with its mechanism — never
smoothed over.

## 1. Headline reproduction result

**29 of 33 headline count groups reproduce exactly.** The 4
divergences are all explained by one mechanism: the scratch run
executes the phases in order WITH HBL statements already loaded,
while the handover snapshot's Phase 8–27 runs predate HBL downstream
rows (HBL statements were a later Phase 7 follow-up; Phases 8–22
were never re-run against them before handover). The scratch state
is therefore the HBL-inclusive pipeline state, not a failure to
reproduce — and every divergence below names the HBL-affected
tables. A second, smaller mechanism explains the job-run and
data-source differences (operational history and the LEAP provenance
row — see §3).

## 2. Per-table counts: scratch vs handover target

| Table / group | Scratch | Handover target | Match? |
|---|---|---|---|
| companies | 470, all UNVERIFIED | 470, all UNVERIFIED | ✓ |
| securities | 470 | 470 | ✓ |
| sectors | 37 | 37 | ✓ |
| registry_evidence (DPS + secp_leap) | 1,001 (940 + 61) | 1,001 (940 + 61) | ✓ |
| company_identifiers | 0 | 0 | ✓ |
| market_prices (one date 2026-11-03) | 444, all UNVERIFIED | 444, all UNVERIFIED | ✓ |
| market_prices previous_close NULL | 444 | 444 | ✓ |
| market_prices turnover NULL | 444 | 444 | ✓ |
| market_prices source_timestamp NULL | 444 | 444 | ✓ |
| trading_sessions / index_prices | 0 / 0 | 0 / 0 | ✓ |
| financial_documents | 4 | 4 | ✓ |
| financial_statements | 118 | 118 | ✓ |
| financial_statement_line_items | 2,116 | 2,116 | ✓ |
| auditor_opinions | 4 | 4 | ✓ |
| HBL split (doc/stmts/items/opinion) | 1 / 30 / 800 / 1, UNVERIFIED | 1 / 30 / 800 / 1, UNVERIFIED | ✓ |
| technical_calculation_runs / errors / values / signals | 1 / 124 / 0 / 0 | 1 / 124 / 0 / 0 | ✓ |
| technical errors: insufficient_warmup / missing_data | 61 / 63 | 61 / 63 | ✓ |
| fundamental_metric_definitions / values | 36 / 108 | 36 / 108 | ✓ |
| financial_health_assessments / warnings | 24 / 8 | 24 / 8 | ✓ |
| sector_metric_profiles (fundamental + macro) | 120 (108 + 12) | 108 + 12 | ✓ |
| valuations (computed / insufficient / not_applicable) | 51 (7 / 41 / 3), all UNVERIFIED | 51 (7 / 41 / 3), all UNVERIFIED | ✓ |
| economic_indicators (VERIFIED / UNVERIFIED) | 12 (6 / 6) | 12 (6 / 6) | ✓ |
| company_macro_exposures / macro_regimes / macro_events | 6 / 1 (tightening) / 4 | 6 / 1 (tightening) / 4 | ✓ |
| news_sources / company_aliases | 8 / 1,376 | 8 / 1,376 | ✓ |
| news_events | **8** (4 earnings + 4 macro) | 7 | ✗ — see D-DB-01 |
| news_event_companies | **4** (HUBC/NML/OGDC/HBL) | 3 | ✗ — see D-DB-01 |
| ownership_holdings / action_records / adjustment_rules | 34 / 5 / 4 (defined_not_applied) | 34 / 5 / 4 (defined_not_applied) | ✓ |
| market_breadth / liquidity_observations / investor_flows | 50 / 889 / 0 | 50 / 889 / 0 | ✓ |
| forecast_targets / snapshots / assessments | 48 / 116 / 120 (all insufficient) | 48 / 116 / 120 (all insufficient) | ✓ |
| forecasts (computed rows) | 0 | 0 | ✓ |
| risk_metric_definitions / values (computed / insufficient) | 22 / 81 (46 / 35) | 22 / 81 (46 / 35) | ✓ |
| risk_flags / controls / checks / stress scenarios / results | 17 / 5 / 7 / 5 / 10 | 17 / 5 / 7 / 5 / 10 | ✓ |
| decision_rules / decisions (all WITHHELD) / outcomes | 1 / 4 / 0 | 1 / 4 / 0 | ✓ |
| decision completeness HUBC / OGDC | 6/7 / 6/7 | 6/7 / 6/7 | ✓ |
| simulated_portfolios / holdings / exclusions / sector_allocs / comparisons | 3 / 7 / 5 / 7 / 3 | 3 / 7 / 5 / 7 / 3 | ✓ |
| backtest_strategies / runs (all NOT_RUNNABLE) / metrics (0 computed) / ledger / bias / paper_orders | 5 / 5 / 55 / 13 / 7 / 0 | 5 / 5 / 55 / 13 / 7 / 0 | ✓ |
| agent_definitions / orchestration_runs / tasks / audit_logs / evaluations (6/6 PASS) | 16 / 1 / 6 / 6 / 6 | 16 / 1 / 6 / 6 / 6 | ✓ |
| rag_documents / chunks / benchmark cases / results | 3 / 943 / 6 / 6 (single run) | 3 / 943 / 6 / 6 (r3 only) | ✓ |
| screen_definitions / runs / results (MATCH) | 5 / 5 / 1,418 (241) | 5 / 5 / 1,418 (241) | ✓ |
| alert_rules / alerts (INFO/WARNING/CRITICAL) / deliveries / runs | 9 / 89 (82/6/1) / 89 / **9** | 9 / 89 (82/6/1) / 89 / 18 | △ — see D-DB-02 |
| report_templates / reports (DRAFT) / figures (computed/insufficient/n-a) / sections / exports (md/html/pdf) | 8 / 22 / 541 (335/199/7) / 188 / 66 (22/22/22) | 8 / 22 / 541 (335/199/7) / 188 / 66 (22/22/22) | ✓ |
| job_definitions (active / paused) / job_runs | 8 (5 / 3) / **0** | 8 / 71 | ✗ — see D-DB-03 |
| model_cards (all NOT_PROMOTED) | 9 | 9 | ✓ |
| evaluation_metrics (computed / not_evaluable / not_applicable) | **50 (38 / 11 / 1)** | 44 (32 / 11 / 1) | ✗ — see D-DB-04 |
| golden_test_cases / results | 14 / 14 (13 pass, 1 fail) | 14 / 14 pass (Phase 26) | ✗ — see D-DB-05 |
| slo_definitions / measurements (met / unmet / not_evaluable) | 14 / **7 / 6 / 1** | 14 / 10 / 4 / 0 | ✗ — see D-DB-06 |
| observability_source_health / exceptions / incidents (resolved) | 9 / **8** / 3 | 9 / 6 / 3 | ✗ — see D-DB-07 |
| performance_probes | 13 | 13 | ✓ |
| auth_users / auth_tokens / auth_audit_logs | 0 / 0 / 0 | 0 / 0 / 0 | ✓ |
| acceptance_runs / scenarios (pass/blocked/not_evaluable) / recomputations (matched/mismatched) / defects | 1 / 15 (12/1/2) / 15 (14/1) / 14 | 1 / 15 (12/1/2) / 15 (14/1) / 14 | ✓ |
| data_sources | **20** | 19 | ✗ — see D-DB-08 |
| Phase 3 tables: forecasts / recommendations / portfolios / corporate_actions | 0 / 0 / 0 / 0 | 0 (deliberately not reused) | ✓ |
| financial_document_versions (restatement) | 0 | 0 (NOT_EVALUABLE) | ✓ |
| migration head | 20261104_0024 | 20261104_0024 | ✓ |

## 3. Divergences, with mechanisms (all findings, none smoothed over)

**D-DB-01 — news_events 8 vs 7; event_companies 4 vs 3 (LOW,
expected, HBL mechanism).** Scratch Phase 11 ran with HBL statements
loaded, so it seeded a 4th earnings event (HBL, NULL publication
date — no seed summary exists for HBL) and a 4th event-company row.
The handover's Phase 11 ran before HBL downstream rows existed
(3 earnings + 4 macro = 7; HUBC/NML/OGDC only). The HBL event did
NOT generate an alert (alerts remain exactly 89), because the alert
rules do not fire on the undated HBL event. Coverage moves 3/470 →
4/470. This divergence is evidence the pipeline handles the
HBL-inclusive state without inflating alerts — it is not a
reproduction failure.

**D-DB-02 — alert_runs 9 vs 18 (LOW, operational history).** The
analytical outputs match exactly (89 alerts, 89 deliveries, same
severity split, HUBC alerts = 4). The run count differs because the
live database accumulated a second execution's runs (Phase 21 run +
a later verification re-run); a fresh scratch register + single
execution produces 9 (one per rule). Run counts are operational
logs, not analytical evidence; the audit does not treat this as a
data defect.

**D-DB-03 — job_runs 0 vs 71 (LOW, operational history, same
reason).** A fresh `run_jobs.py register` seeds 8 definitions
(5 active, 3 paused — the paused three are exactly the Terms-gated
collection jobs: `market_post_close`, `filing_check`,
`macro_release_check`) and 0 runs. The 71 live runs are the
accumulated record of operator invocations across the pipeline's
life (run-due passes, run-one calls, retries). They cannot be
reproduced by re-running the pipeline, and their individual
contents were not re-verified. Consequence: the
`job_success_rate` SLO is NOT_EVALUABLE in scratch (0 terminal
runs), vs MET at Phase 27 (71/71) — see D-DB-06.

**D-DB-04 — evaluation_metrics 50 vs 44 (LOW, HBL mechanism).**
Computed 38 vs 32 (+6); not_evaluable 11 and not_applicable 1
identical. The +6 computed metrics coincide with HBL downstream
rows now present (drift metrics detecting the differing tables;
recommendation metrics covering the HBL decision). The Phase 26
report's 44 was measured on the pre-HBL-downstream state.

**D-DB-05 — golden case `golden_refusal_hbl_missing` FAILS in
scratch (LOW, stale expectation, not a regression).** 13/14 pass.
The failing case's own evidence is `{"hbl_documents": 1}`: the case
asserts the system must REFUSE HBL work because HBL was missing at
Phase 26 time. In scratch HBL documents = 1 (present), so the
refusal assertion correctly fails — the case is stale relative to
the HBL-inclusive state. This is the mechanism behind the SLO flip
in D-DB-06, and it is a positive signal (the pipeline no longer
needs to refuse HBL), not a defect in the code.

**D-DB-06 — SLO measurements 7 met / 6 unmet / 1 not_evaluable vs
10 / 4 / 0 (MEDIUM as a measurement, LOW as a defect — fully
reconciled).** The three flips from Phase 27's own SLO table are:
(1) `job_success_rate` met → not_evaluable (D-DB-03, 0 runs);
(2) `golden_pass_rate` met (14/14) → unmet (13/14, D-DB-05);
(3) `drift_difference_count` met (live matched Phase 24 baseline)
→ unmet (6 tables differ: financial_documents 3→4, statements
88→118, line_items 1316→2116, opinions 3→4, news_events 7→8,
data_sources 19→20 — every one an HBL/LEAP table). The four
Phase 27 unmet SLOs remain unmet (news coverage, previous_close
completeness 0/444, price coverage 444/470 = 0.944681, session gap
2 weekdays). Arithmetic closes exactly: 10−3=7 met, 4+2=6 unmet,
0+1=1 not_evaluable. SLOs are time- and state-sensitive
measurements, not stable counts; the audit records the scratch
measurement as the current evidence.

**D-DB-07 — observability_exceptions 8 vs 6 (LOW, unexamined
delta).** By severity in scratch: 1 high, 1 info, 2 low, 4 medium.
The +2 vs the handover count were not individually traced to a
mechanism in this audit (the exception rows' keys were not
compared row-by-row to the Phase 27 list). Recorded as an open
minor divergence, not attributed to HBL without evidence.

**D-DB-08 — data_sources 20 vs 19 (LOW, LEAP provenance row).**
The LEAP loader inserts a `secp_leap` provenance row on commit
("data_sources: inserted secp_leap provenance row" in its output).
The Phase 24 baseline and the handover census both show 19; the
drift SLO itself reports expected 19 / live 20. The 20th row is the
LEAP provenance row, present in scratch because the audit re-ran
the LEAP load; the handover snapshot's 19 predates that row (or
counts without it). Not a data defect.

**D-DB-09 — technical-error model is run-level, not per-security
(LOW, claim correction).** All 124 error rows carry NULL
security_id; the model is 62 indicators × error types at run
level. The prior claim's phrasing "daily_return is
missing_data(470)" does not correspond to a stored row count
(daily_return has exactly 2 run-level error rows in scratch).
The figure 470 is interpretive (all 470 securities lack the prior
day needed for a return), not a stored count. Headline counts
(1 run / 124 errors / 0 values / 0 signals) reproduce exactly.

## 4. Quality status, date coverage, missing values, duplicates, referential integrity

- **Quality status:** every company (470), security-linked price
  (444), statement (118), valuation (51), and decision input is
  UNVERIFIED, except the 6 macro indicators carrying VERIFIED under
  the documented SBP/PBS cross-publisher caveat (NOT H1-verified in
  the registry sense — no official-source pair in the registry
  supports them; see the licensing audit). Zero rows were promoted
  by this audit, and no promotion path was exercised.
- **Date coverage:** prices cover exactly one trading date
  (2026-11-03). No trading_sessions rows exist, so the 2-weekday
  session gap SLO is unmet by construction. Statement period ends
  reach 2026-06-30 (128 days old at measurement) — the
  statement_freshness SLO is met only because its threshold is
  generous, not because statements are current.
- **Missing values (honest NULLs, never zero-filled):** prices:
  previous_close NULL on 444/444, turnover NULL on 444/444,
  source_timestamp NULL on 444/444. Breadth: advances/declines
  empty (no prior day). Forecasts: 0 computed rows; 120 assessments
  all insufficient_inputs. Backtests: 0 computed metrics.
  Investor flows: 0 rows. These gaps are labelled in the data,
  not hidden — that honesty is a strength, and it is also why the
  phases cannot be COMPLETE.
- **Duplicates:** 0 duplicate (security, trading_date) price rows;
  0 duplicate ticker assignments across 470 securities (SLO
  duplicate_ticker_rate met, 0.0). OHLC validity 444/444 pass;
  0 non-positive prices. No duplicate evidence rows (LEAP dry-run:
  0 identical skips; commit inserted exactly 61 new rows).
- **Referential integrity:** 118/118 statements trace to a document
  (SLO statement_document_lineage met, 1.0). All 444 priced
  securities resolve to registry companies by ticker. No orphaned
  valuation, decision, or report rows were found in the audited
  queries. Surrogate ids shift across imports by design (scratch
  HUBC id 289 = the original import's id, vs live 759 at handover
  time) — every audit query resolved companies BY TICKER, never by
  hardcoded id, and the one place code hardcodes ids (macro sector
  ids, news document ids — defect D-04) is called out in the
  defects register, not hidden.

## 5. Scratch reproduction provenance

- Backup restored: `2026-11-04T1230-PKT`, dump SHA-256
  `98f7bc2e…d75ccd` verified, 2 documented non-fatal pg_restore
  errors, row-count gate `phase2_probe 0 = 0` VERIFIED.
- Migration: `20261104_0004 → 20261104_0024` via
  `database/.venv/bin/alembic upgrade head` from `database/`.
- One auditor error during setup (schema grant issued against the
  wrong database) was caught by the restore gate, corrected, and
  re-run successfully — evidence the gate works.
- Temporary worktree-only remap applied for Phase 11 (news document
  ids 13/14/15 → scratch 4/5/6, both maps) and reverted immediately
  after the commit (`git checkout --`, verified clean). The macro
  sector-id remap was NOT needed in scratch (scratch sector ids
  16/8/36/4 coincide with the hardcoded constants because the
  sequence state matches the original import) — the D-04 trap
  remains open for any import with different sequence state, as
  recoveries #5–#7 proved.
- LEAP load ran from detached worktree `psx-audit-leap` (`eb2e331`
  loader + committed observations JSON); HBL extraction from
  detached worktree `psx-audit-hbl` (`42bd8e2` code + page maps).
  Neither worktree's code is committed to the audit branch.
- Interruption recorded: VM replacement #8 destroyed the first
  scratch cluster mid-audit; the scratch environment was rebuilt
  on the recovered cluster per the recipe and the reproduction
  restarted cleanly. No live-database write occurred at any point.
