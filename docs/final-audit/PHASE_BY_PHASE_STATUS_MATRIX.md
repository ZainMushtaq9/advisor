# Phase-by-Phase Status Matrix — PSX Intelligence AI (Independent Audit)

**Audit baseline:** branch `phase-30-release`, commit `8937338`
(tag `v0.2.0-handover` peels to `6b1ff9f`, one commit before the
tip). **Audit date:** 2026-11-05 (Asia/Karachi).
**Method:** scratch-database reproduction + fresh-clone test
execution + live runtime checks + GitHub verification, all
performed by this audit (see the companion reports for evidence).
**Status definitions (prompt §14, applied strictly):** COMPLETE
= all mandatory criteria pass with current reproducible evidence;
PARTIALLY COMPLETE = implementation exists but mandatory criteria
remain; BLOCKED = a critical external dependency prevents
passing; FAILED = implementation or mandatory tests fail
materially; UNVERIFIED = insufficient evidence; NOT STARTED = no
meaningful implementation; NOT APPLICABLE = genuinely irrelevant
with a documented reason. No phase is COMPLETE merely because its
branch, documentation, test file, endpoint, migration, or report
exists, or because the application starts.
**Reading note:** the live database was in flux (post-handover
HBL batch), so all database evidence below is from the scratch
reproduction; handover-time live counts are the cross-check
targets, and divergences are flagged (DB-01…DB-09 in the database
audit). The post-handover batch's results are future work, not
evidence for this baseline.

## Summary counts

| Status | Phases | Count |
|---|---|---|
| COMPLETE | 1, 2, 3 | **3** |
| PARTIALLY COMPLETE | 4–30 | **27** |
| BLOCKED | — | 0 |
| FAILED | — | 0 |
| UNVERIFIED | — | 0 |
| NOT STARTED | — | 0 |
| NOT APPLICABLE | — | 0 |
| **Total** | | **30** |

No phase is rated BLOCKED as a whole (each has partial function;
the blocking criteria are named per phase) and none is FAILED
(no implementation materially fails — all suites pass, all
runners work). The project verdict therefore follows §15: the
project is COMPLETE only if all 30 phases are COMPLETE — it is
not, so the verdict is **C: PROJECT PARTIALLY COMPLETE — 3 OF 30
PHASES COMPLETE** (see FINAL_EXECUTIVE_VERDICT.md).

## The 30 rows

| Phase | Name | Code | Data | Tests | Acceptance | GitHub | Final verdict |
|---|---|---|---|---|---|---|---|
| 1 | Specification checkpoint | exists | n/a (spec) | n/a | PASS with forward gates G-01–G-08 | in base history | **COMPLETE** |
| 2 | Repository & environment | exists | probe only | 453 pass (re-run) | COMPLETE under amended criteria; CI-in-CI unverified | 016f3c8 | **COMPLETE** |
| 3 | Database & storage | exists | 54 tables migrated | storage tests pass | PASS WITH LIMITATIONS, all fixed/accepted | b22281a | **COMPLETE** |
| 4 | Company registry | exists, but LEAP loader + universe endpoint absent from tree | 470 UNVERIFIED, 0 identifiers | registry tests pass | universe not verified; no promotions | 0f4342f (+ side branches c078c0b, 9204632, eb2e331 unmerged) | **PARTIALLY COMPLETE** |
| 5 | Market snapshot import | exists | 444/470, 1 day, NULLs | ingestion tests pass | single-day, Terms-gated | ffc9d61 (+ f4b703d, e281c73 unmerged docs) | **PARTIALLY COMPLETE** |
| 6 | Technical analytics | exists | 1 run / 124 errors / 0 values | indicator tests pass | warm-ups unmet | 6efede9 (+ e556806, 85f4a72 unmerged docs) | **PARTIALLY COMPLETE** |
| 7 | Financial statements | exists, but HBL code absent from tree | 118 stmts, 4 companies | extraction tests pass | KSE-100 coverage missing | 366ed32, 59834f1, f53cde8 (+ 42bd8e2 unmerged) | **PARTIALLY COMPLETE** |
| 8 | Fundamental analysis | exists | 108 values, UNVERIFIED inputs | analysis tests pass | 3 companies only | 9969f5a | **PARTIALLY COMPLETE** |
| 9 | Valuation | exists | 51 (7 computed) | valuation tests pass | share counts missing; HBL bank model pending | f9de2cc | **PARTIALLY COMPLETE** |
| 10 | Macro & sector | exists, sector ids hardcoded (D-04) | 12 indicators (6 caveated VERIFIED) | macro tests pass | CPI blocker; sector-id trap | 9df2266 | **PARTIALLY COMPLETE** |
| 11 | News & events | exists, doc ids hardcoded (D-04) | 8 events (scratch) / 7 (handover) | news tests pass | PSX announcements not collected | b6c6026 | **PARTIALLY COMPLETE** |
| 12 | Ownership, actions, breadth | exists | 34 / 5 / 4 / 50 / 889 / 0 flows | ownership tests pass | flows 0; rules defined_not_applied | a58a104 | **PARTIALLY COMPLETE** |
| 13 | Forecasting | exists | 48 / 116 / 120, 0 computed | forecasting tests pass | all abstain (insufficient inputs) | 9eb2f41 | **PARTIALLY COMPLETE** |
| 14 | Risk management | exists | 81 (46 computed) | risk tests pass | VaR/ES warm-ups unmet | 04ad858 | **PARTIALLY COMPLETE** |
| 15 | Decision engine | exists | 4 decisions, all WITHHELD | decision tests pass | completeness ≤ 6/7; 0 outcomes | 9f78fb4 | **PARTIALLY COMPLETE** |
| 16 | Portfolio construction | exists | 3 simulated, reconcile to 1M | portfolio tests pass | no covariance (correctly refused) | cb2a70c | **PARTIALLY COMPLETE** |
| 17 | Backtesting | exists | 5 runs NOT_RUNNABLE, 0 computed | backtest tests pass | not runnable on 1 day | 5bea951 | **PARTIALLY COMPLETE** |
| 18 | Orchestration | exists | 16 agents, 6/6 eval PASS | orchestration tests pass | LLM unavailable (rule fallback) | 6b8ba4d | **PARTIALLY COMPLETE** |
| 19 | RAG knowledge base | exists, retrieval registered not implemented | 3 docs / 943 chunks / 6 bench (r3) | RAG tests pass | no verified model; no vector retrieval | 3cd98e7 | **PARTIALLY COMPLETE** |
| 20 | Screener | exists | 1,418 results (241 MATCH) | screener tests pass | filter only; inputs UNVERIFIED | c91acb1 | **PARTIALLY COMPLETE** |
| 21 | Alerts | exists | 89 alerts, 89 deliveries, in-app only | alert tests pass | external consent False | dbeee4a | **PARTIALLY COMPLETE** |
| 22 | Reports | exists | 22 DRAFT, 541 figures, 66 exports | report tests pass | 0 APPROVED; no publish | 45d08ec | **PARTIALLY COMPLETE** |
| 23 | Dashboard | exists | 27 routes render (Playwright 6/6 via acceptance page) | frontend 11 pass; build 27 routes | universe endpoint missing; company detail id-keyed | 6662d34 (repair a5077e0) | **PARTIALLY COMPLETE** |
| 24 | Security | exists | auth tables 0/0/0 | auth tests pass (24) | 0 accounts; enforcement OFF | f648bd5 | **PARTIALLY COMPLETE** |
| 25 | Automation (jobs) | exists | 8 defs (3 paused), 0 runs in scratch | job tests pass | operator-invoked only; no scheduler | a129614 | **PARTIALLY COMPLETE** |
| 26 | Evaluation | exists | 9 cards NOT_PROMOTED; metrics 50 (scratch) / 44 (handover) | evaluation tests pass | golden 13/14 in scratch (stale HBL case) | b6f007c | **PARTIALLY COMPLETE** |
| 27 | Observability | exists | SLOs 7/6/1 (scratch) / 10/4 (handover) | observability tests pass | monitoring docs only, not operational | 544fecc | **PARTIALLY COMPLETE** |
| 28 | Deployment | exists | ops scripts + units; no prod deployment | deployment tests pass (layout-sensitive) | readiness artifact (0023 vs 0024) | b791b7d | **PARTIALLY COMPLETE** |
| 29 | Acceptance | exists | 15 scenarios (12/0/1/2); 15 recomps (14/1); 14 defects | acceptance tests pass | G1 NOT_MET, G2/G3/G4 MET, G5 PARTIAL | 858e914 | **PARTIALLY COMPLETE** |
| 30 | Release & handover | exists | handover snapshot reproducible | release tests pass (5) | not a production release; no merge; no sign-off | 8937338 (6b1ff9f + consolidation) | **PARTIALLY COMPLETE** |

## Per-phase detail

### Phase 1 — Specification checkpoint — COMPLETE
- Branch/SHA: in base history (no separate phase branch; files
  present on every later branch including `8937338`).
- Implementation files: `docs/phase-01/` — 59 files on `8937338`
  (the Phase 1 claim of 47 in that directory was its count at
  Phase 1 time; 59 + 8 root trackers = 67 documents total,
  matching the 67-file claim) — including `DATABASE_DESIGN.md`,
  `AGENT_REGISTRY.md`, `FINANCIAL_FORMULAS.md`,
  `DATA_LICENSING_POLICY.md`, `PHASE_1_ACCEPTANCE_REPORT.md`,
  `PHASE_1_AUDIT_REPORT.md`.
- Evidence: 21 modules, 18 agents + orchestrator, 33 entities, 30
  phases specified; acceptance "PASS with gates".
- Test output: n/a (specification; no code tests).
- Database/runtime evidence: n/a.
- Defects: none open against Phase 1 itself.
- Blockers: none for Phase 1. Its gates G-01–G-08 are FORWARD
  gates (they block later phases' ingestion until sources verify
  — e.g., G-01 gates Phases 08/09/10/14, G-02 licence detail) —
  not Phase 1 acceptance failures. The acceptance report states
  explicitly that Phase 1 is NOT a claim that external sources are
  verified.
- Missing criteria: none for the checkpoint itself.
- Remediation: none. The gates are carried as blockers on the
  phases they gate (see roadmap A1/B2/B3).

### Phase 2 — Repository & environment — COMPLETE (under amended criteria)
- Branch/SHA: `phase-02-repository-foundation` `016f3c8`
  (verified via ls-remote; ancestor of `8937338`).
- Implementation files: `backend/` (FastAPI), `frontend/`
  (Next.js 16.4.5 + React 19.3.0, verified in `package.json`),
  `database/` (PostgreSQL contract, migrations, backup/restore
  scripts), `ops/` scripts, `.github/workflows/ci.yml`.
- Evidence: fresh-clone reproducibility reproduced by this audit
  (venv install, imports, 453 backend tests, 11 vitest, 27-route
  build); backup `2026-11-04T1230-PKT` restore gate VERIFIED in
  scratch (including catching an auditor grant error); Redis
  7.0.15 + Celery live proof carried from the Phase 2 report
  (not re-run — no Redis-dependent test exists in the suite).
- Test output: backend 453 passed (fresh clone, standard layout;
  452+1 layout-sensitive failure on a non-standard layout,
  resolved without editing any test); frontend vitest 11 passed.
- Database/runtime evidence: PostgreSQL probe 0 rows at backup
  time; alembic migrated 0004 → 0024 in scratch.
- Defects: deployment test layout sensitivity (LOW, see test
  report); CI-in-CI unverified (A-03, LOW).
- Blockers: Docker gap closed by user decision (NOT verified,
  removed from requirements — a decision, not a gap to fill).
- Missing criteria: CI-in-CI (no Actions runs; workflow triggers
  only on main/development, neither of which has activity).
- Remediation: roadmap C2 (CI run under separate approval).

### Phase 3 — Database & storage — COMPLETE
- Branch/SHA: `phase-03-database-storage` `b22281a` (ancestor of
  `8937338`).
- Implementation files: `backend/app/models/` (54 model tables),
  storage engine (manifests, SHA-256, quarantine),
  `database/migrations/` (chain 0001 → 0024).
- Evidence: migration chain runs cleanly in scratch (0004 →
  0024); Phase 3 audit PASS WITH LIMITATIONS (0 CRITICAL, 3 HIGH,
  9 MEDIUM, 10 LOW, all fixed/accepted per the Phase 3 report).
- Test output: model/storage tests pass within the 453 suite.
- Database/runtime evidence: 56 tables at backup time; Phase 3
  tables (`forecasts`, `recommendations`, `portfolios`,
  `corporate_actions`) deliberately 0 rows in scratch (not reused
  — verified); `financial_document_versions` 0 rows.
- Defects: none open.
- Blockers: none. PyArrow NOT installed and no Parquet dataset
  claimed — not a missing criterion (no Parquet deliverable was
  promised in the completion claim).
- Missing criteria: none.
- Remediation: none.

### Phase 4 — Company registry — PARTIALLY COMPLETE
- Branch/SHA: `phase-04-company-registry` `0f4342f` (ancestor);
  side branches `phase-04-completion` `c078c0b`,
  `phase-04-sampled-verification` `9204632`,
  `phase-04-leap-load` `eb2e331` — all three NOT ancestors of
  `8937338` (integration gap A-02).
- Implementation files: `scripts/import_dps_snapshot.py`,
  registry service; ABSENT from `8937338`:
  `scripts/load_leap_evidence.py`,
  `backend/app/services/registry/leap_evidence.py`,
  `backend/tests/test_leap_evidence.py`, LEAP reports/procedure,
  `backend/app/api/v1/endpoints/universe.py`.
- Evidence: scratch registry import committed 470 companies /
  470 securities / 37 sectors, all UNVERIFIED; LEAP load from
  `eb2e331` validated 61/61 and committed 61 rows (evidence
  940 → 1,001); loader never changes statuses, never writes
  identifiers (verified in its help text and in scratch: 0
  identifiers, statuses unchanged).
- Test output: registry tests pass within the 453 suite
  (LEAP tests exist only on `eb2e331`, not in the release tree).
- Database/runtime evidence: companies 470 UNVERIFIED; evidence
  1,001; identifiers 0; no VERIFIED/PARTIALLY_VERIFIED company.
- Defects: A-02 (integration gap, MEDIUM); D-04 (surrogate ids,
  MEDIUM, latent).
- Blockers: H1 verification (second agreeing source incl. one
  official per company); field-scoped LEAP promotion executed
  (not just documented); universe endpoint.
- Missing criteria: a verified universe; identifier coverage;
  the universe API endpoint.
- Remediation: roadmap A2 (integration), A3 (surrogate fix),
  B2 (verified universe).

### Phase 5 — Market snapshot import — PARTIALLY COMPLETE
- Branch/SHA: `phase-05-snapshot-import` `ffc9d61` (ancestor);
  `phase-05-completion` `f4b703d`, `phase-05-revisit` `e281c73`
  NOT ancestors (completion/rejudgment docs only).
- Implementation files: `scripts/run_market_ingestion.py`,
  `scripts/import_dps_snapshot.py` (registry side); mapped CSV
  gitignored, never committed.
- Evidence: scratch price commit 444 rows with
  `--source-key dps_market_summary_2026-11-03` (a bare run
  rejects the 444 as missing_field — verified behaviour, not
  worked around); 13 rejected (12 OHLC + 1 non-positive) + 13
  absent = 26 unpriced, matching missing_securities 26/470.
- Test output: market ingestion tests pass within the 453 suite.
- Database/runtime evidence: 444 rows, 1 date (2026-11-03), all
  UNVERIFIED; previous_close/turnover/source_timestamp NULL on
  444/444; OHLC validity 444/444; 0 duplicates; 0 non-positive.
- Defects: none new (the single-day limitation is a blocker,
  not a defect).
- Blockers: written PSX permission (A1); more trading dates (B1).
- Missing criteria: multi-day series; previous_close/turnover/
  source_timestamp populated; 26 unpriced securities resolved.
- Remediation: roadmap A1, B1.

### Phase 6 — Technical analytics — PARTIALLY COMPLETE
- Branch/SHA: `phase-06-technical-analytics` `6efede9`
  (ancestor); `phase-06-completion` `e556806`,
  `phase-06-revisit` `85f4a72` NOT ancestors (docs only).
- Implementation files: `scripts/run_technical_indicators.py`,
  technical service (62 indicators).
- Evidence: scratch coverage commit 1 run / 124 errors (61
  insufficient_warmup + 63 missing_data) / 0 values / 0 signals.
- Test output: indicator tests pass within the 453 suite.
- Database/runtime evidence: all 124 error rows are run-level
  (security_id NULL) — see D-DB-09: the prior
  "daily_return missing_data(470)" phrasing is interpretive, not
  a stored count (daily_return has 2 run-level error rows).
- Defects: none new.
- Blockers: multi-day price series (warm-ups need 251
  observations for VaR/ES; even 2 days would enable returns).
- Missing criteria: any computed indicator value; any signal.
- Remediation: roadmap B1.

### Phase 7 — Financial statements — PARTIALLY COMPLETE
- Branch/SHA: `phase-07-financial-statements` `366ed32`,
  `phase-07-remainders` `59834f1`,
  `phase-07-hbl-followup` `f53cde8` (all ancestors);
  `phase-07-hbl-extraction` `42bd8e2` NOT an ancestor
  (integration gap A-02).
- Implementation files: `scripts/run_financial_extraction.py`,
  page maps for hubc/nml/ogdc (12, in tree); ABSENT from
  `8937338`: HBL page maps, HBL run report, and the HBL
  extractor options (`skip_values`, `blank_columns`,
  `label_parts` — zero matches in the tree's `extract.py`).
- Evidence: scratch audit-tree extraction (dry-run then commit)
  3 documents / 88 statements / 1,316 items / 3 opinions; then
  HBL extraction from `42bd8e2` → 4 / 118 / 2,116 / 4, with HBL
  split 1 / 30 / 800 / 1, all UNVERIFIED; HBL SFP identities
  exact both years (see financial accuracy audit).
- Test output: extraction tests pass within the 453 suite.
- Database/runtime evidence: all 118 statements UNVERIFIED;
  `financial_document_versions` 0 (restatement NOT_EVALUABLE).
- Defects: A-02 (MEDIUM); recorded HBL source defects handled
  without invented labels (CF unlabeled row, CE 2024 blank NCI
  cell, CF label split, dual-currency ordering).
- Blockers: KSE-100 coverage (466 companies without statements);
  DPS-download terms for LUCK (parked, correctly).
- Missing criteria: statements for more than 4 companies;
  restatement evaluation data.
- Remediation: roadmap A2, B3.

### Phase 8 — Fundamental analysis — PARTIALLY COMPLETE
- Branch/SHA: `phase-08-fundamental-analysis` `9969f5a`
  (ancestor).
- Implementation files: `scripts/run_fundamental_analysis.py`,
  fundamental service (formulae verified: gross margin =
  gross_profit / revenue).
- Evidence: scratch commit values_written 108, health 24,
  warnings 8, profiles 108; per-company (computed, insufficient,
  n/a): HUBC (32,4,0), NML (31,5,0), OGDC (28,7,1).
- Test output: fundamental tests pass within the 453 suite.
- Database/runtime evidence: defs 36, values 108, health 24,
  warnings 8, sector profiles 108 (→ 120 after Phase 10);
  HUBC gross margin recomputed 0.41740029… vs stored 0.417400 ✓.
- Defects: none new.
- Blockers: statement coverage (3 companies); UNVERIFIED inputs.
- Missing criteria: fundamentals for more companies; verified
  inputs.
- Remediation: roadmap B3, B2.

### Phase 9 — Valuation — PARTIALLY COMPLETE
- Branch/SHA: `phase-09-valuation` `f9de2cc` (ancestor).
- Implementation files: `scripts/run_valuation.py`,
  `valuation/formulas.py` (P/E = price / EPS, None for
  missing/zero/negative EPS), keymaps (HUBC `eps_total`, OGDC
  `eps_basic`).
- Evidence: scratch commit 51 valuations (7 computed / 41
  insufficient / 3 not_applicable, dry-run confirms the split),
  all UNVERIFIED; P/Es recomputed exactly (HUBC 5.155254, OGDC
  17.881625); OGDC uses the H1 EPS 16.98, not the standalone
  quarter 8.07.
- Test output: valuation tests pass within the 453 suite.
- Database/runtime evidence: 51 rows, all UNVERIFIED; no
  market-cap / enterprise-value multiples computed (share
  counts missing).
- Defects: none new. Note: the HBL bank residual-income model is
  post-handover batch work (banking rule), not baseline scope.
- Blockers: share counts; statement coverage; verified inputs.
- Missing criteria: computed multiples beyond the 7; HBL bank
  model in the baseline lineage.
- Remediation: roadmap B3, D1 (follow-up audit of the batch
  lineage, which reports HBL P/E 6.292).

### Phase 10 — Macro & sector — PARTIALLY COMPLETE
- Branch/SHA: `phase-10-macro-sector` `9df2266` (ancestor).
- Implementation files: `scripts/run_macro_analysis.py`,
  macro service (sector ids hardcoded — D-04).
- Evidence: scratch commit 12 indicators (6 VERIFIED under the
  SBP/PBS cross-publisher caveat, 6 UNVERIFIED), 6 exposures,
  sector profiles 108 → 120 (+12 macro), 1 regime (tightening,
  2026-11-04), 4 events. Scratch sector ids 16/8/36/4 coincide
  with the hardcoded constants (sequence-state luck) — no remap
  was needed in scratch, but D-04 remains open.
- Test output: macro tests pass within the 453 suite.
- Database/runtime evidence: as above; regime observations 0
  (regime row only).
- Defects: D-04 (MEDIUM); A-06 (macro VERIFIED caveat not
  surfaced, LOW).
- Blockers: October CPI YoY official read (live-browser PBS PDF
  fetch, Phase 10 blocker 1); verified macro sources beyond the
  caveat.
- Missing criteria: CPI official read; H1-grade macro
  verification; sector-id fix.
- Remediation: roadmap A3, B4.

### Phase 11 — News & events — PARTIALLY COMPLETE
- Branch/SHA: `phase-11-news-events` `b6c6026` (ancestor).
- Implementation files: `scripts/run_news_events.py`, news
  service (publication-date and seed-summary maps keyed by
  document ids — D-04; PSX collector gated stub, registered not
  implemented; NOT_COLLECTED list with exact unblockers).
- Evidence: scratch commit with the temporary document-id remap
  (13/14/15 → 4/5/6, reverted immediately after): 8 sources,
  1,376 aliases, 8 events (4 earnings + 4 macro), 4
  event-companies (HUBC/NML/OGDC/HBL); HUBC event date 2026-09-21
  (the remap worked — without it the date is NULL, the recovery
  #6 failure mode). Handover target was 7 events / 3 companies
  (pre-HBL-downstream) — divergence D-DB-01, mechanism explained.
- Test output: news tests pass within the 453 suite.
- Database/runtime evidence: as above; HBL event has NULL date
  (no seed summary for HBL) and generated no alert.
- Defects: D-04 (MEDIUM).
- Blockers: written PSX permission (announcements); per-outlet
  terms review (reputable news); SECP announcements route.
- Missing criteria: PSX/SECP/reputable-news collection; HBL
  event dating; coverage beyond 4/470.
- Remediation: roadmap A1, A3.

### Phase 12 — Ownership, actions, breadth — PARTIALLY COMPLETE
- Branch/SHA: `phase-12-ownership-actions-breadth` `a58a104`
  (ancestor).
- Implementation files: `scripts/run_ownership_actions.py`.
- Evidence: scratch commit ownership 34, action records 5
  (`corporate_actions` table itself 0 — the 5 live in
  `corporate_action_records`; the handover's "corporate actions
  5" maps to records), adjustment rules 4 (all
  defined_not_applied), breadth 50, liquidity 889, investor
  flows 0; priced 444, universe 470 in the runner report.
- Test output: ownership tests pass within the 453 suite.
- Database/runtime evidence: median_volume 54,631.5 ✓;
  missing_securities 26/470; advances/declines empty (no prior
  day); breadth coverage 444/470 = 0.944681.
- Defects: none new.
- Blockers: multi-day data (advances/declines, flows); Terms
  (filing-based actions).
- Missing criteria: applied adjustments (rules are defined, not
  applied); investor flows; multi-day breadth.
- Remediation: roadmap A1, B1.

### Phase 13 — Forecasting — PARTIALLY COMPLETE
- Branch/SHA: `phase-13-forecasting` `9eb2f41` (ancestor).
- Implementation files: `scripts/run_forecasting.py`
  (runner notes `hbl_pending: true` in scratch output).
- Evidence: scratch commit 48 targets, 116 snapshots, 120
  assessments, all insufficient_inputs, 0 computed forecast rows.
- Test output: forecasting tests pass within the 453 suite.
- Database/runtime evidence: `forecasts` table 0 rows.
- Defects: none new — abstention is correct behaviour, not a
  defect.
- Blockers: multi-day return series; sufficient inputs (B1).
- Missing criteria: any computed forecast (1d/1w/1m/3/6/12m
  horizons all abstain).
- Remediation: roadmap B1.

### Phase 14 — Risk management — PARTIALLY COMPLETE
- Branch/SHA: `phase-14-risk-management` `04ad858` (ancestor).
- Implementation files: `scripts/run_risk_analytics.py`
  (warm-ups 251 observations for VaR95/ES95).
- Evidence: scratch commit defs 22, values 81 (46 computed + 35
  insufficient), flags 17, controls 5, checks 7, stress scenarios
  5, results 10.
- Test output: risk tests pass within the 453 suite.
- Database/runtime evidence: as above; simulated portfolio is
  equal-weight HUBC/NML/OGDC (simulation only).
- Defects: none new.
- Blockers: return series for VaR/ES (251 observations).
- Missing criteria: VaR95/ES95 computed values; the 35
  insufficient metrics.
- Remediation: roadmap B1.

### Phase 15 — Decision engine — PARTIALLY COMPLETE
- Branch/SHA: `phase-15-decision-engine` `9f78fb4` (ancestor).
- Implementation files: `scripts/run_decision_engine.py`.
- Evidence: scratch commit rules 1, decisions 4, outcomes 0;
  all WITHHELD; completeness HUBC 6/7, OGDC 6/7, NML 4/7,
  HBL 2/7; outcomes_existing 0.
- Test output: decision tests pass within the 453 suite.
- Database/runtime evidence: as above; screening outcomes
  HUBC/NML/OGDC/HBL = PASS/FAIL/PASS/PASS with user_facing
  WITHHELD throughout.
- Defects: none new.
- Blockers: input completeness (statements, prices, forecasts).
- Missing criteria: any user-facing (non-WITHHELD) decision;
  any outcome tracking.
- Remediation: roadmap B1, B2, B3.

### Phase 16 — Portfolio construction — PARTIALLY COMPLETE
- Branch/SHA: `phase-16-portfolio-construction` `cb2a70c`
  (ancestor).
- Implementation files: `scripts/run_portfolio_construction.py`.
- Evidence: scratch commit 3 simulated portfolios, 7 holdings,
  5 exclusions, 7 sector allocations, 3 comparisons; all three
  reconcile exactly to PKR 1,000,000 (see financial accuracy
  audit); runner honestly reports "no covariance matrix: 0
  return observations from 1 price date".
- Test output: portfolio tests pass within the 453 suite.
- Database/runtime evidence: as above; `portfolios` (Phase 3
  table) 0 rows — simulated portfolios live in their own tables.
- Defects: none new.
- Blockers: return series for covariance/optimisation.
- Missing criteria: optimised (non-rule) portfolios; real
  covariance.
- Remediation: roadmap B1.

### Phase 17 — Backtesting — PARTIALLY COMPLETE
- Branch/SHA: `phase-17-backtesting` `5bea951` (ancestor).
- Implementation files: `scripts/run_backtesting.py`.
- Evidence: scratch commit 5 strategies, 5 runs all
  NOT_RUNNABLE, 55 metrics 0 computed, 13 ledger entries, 7 bias
  reports, 0 paper orders.
- Test output: backtest tests pass within the 453 suite.
- Database/runtime evidence: as above.
- Defects: none new — NOT_RUNNABLE is honest, not a defect.
- Blockers: multi-day price series (B1).
- Missing criteria: any runnable backtest; any computed metric.
- Remediation: roadmap B1.

### Phase 18 — Orchestration — PARTIALLY COMPLETE
- Branch/SHA: `phase-18-orchestration` `6b8ba4d` (ancestor).
- Implementation files: `scripts/run_orchestration.py`,
  agent definitions (16).
- Evidence: scratch commit 1 run, 6 tasks, 6 audit logs, 6
  evaluations 6/6 PASS; runner notes "LLM execution unavailable:
  all agents ran in rule-based fallback mode" and "Jobs do not
  run when the host is off: the runtime is in-process with a
  persistent ledger."
- Test output: orchestration tests pass within the 453 suite.
- Database/runtime evidence: as above; agent_executions 0.
- Defects: none new.
- Blockers: verified local LLM/embedding model (C1).
- Missing criteria: LLM execution (vs rule fallback); any agent
  execution row.
- Remediation: roadmap C1.

### Phase 19 — RAG knowledge base — PARTIALLY COMPLETE
- Branch/SHA: `phase-19-rag-knowledge-base` `3cd98e7`
  (ancestor).
- Implementation files: `scripts/run_rag.py` (`--index`,
  `--benchmark`, `--query`, `--access-audit` subcommands).
- Evidence: scratch `--index` + `--benchmark` commits: 3
  documents, 943 chunks, 6 cases, 6 results in a single run
  (`phase19-benchmark-2026-11-04`); index output notes
  `empty_pages_gap: 16`, `hash_mismatches: []`.
- Test output: RAG tests pass within the 453 suite.
- Database/runtime evidence: as above. The r1/r2 benchmark runs
  were runs of superseded retrieval code and were NOT
  re-fabricated — only the r3-equivalent run exists in scratch,
  consistent with the claim.
- Defects: none new.
- Blockers: verified embedding model; vector retrieval
  implementation (C1).
- Missing criteria: vector retrieval; a benchmark from
  implemented (not keyword) retrieval.
- Remediation: roadmap C1.

### Phase 20 — Screener — PARTIALLY COMPLETE
- Branch/SHA: `phase-20-screener` `c91acb1` (ancestor).
- Implementation files: `scripts/run_screener.py`,
  `screener/ranking.py` (score = passed / scored; MATCH iff
  scored ≥ 1 and passed == scored; INSUFFICIENT_DATA iff
  scored == 0).
- Evidence: scratch commit 5 runs, 1,418 rows; outcomes 241 MATCH
  / 680 NO_MATCH / 497 INSUFFICIENT_DATA; per-screen MATCH
  counts sum to 241 (194+44+1+2+0 as claimed).
- Test output: screener tests pass within the 453 suite.
- Database/runtime evidence: as above; the "filter result, not
  opportunity" disclaimer is attached by API/CLI.
- Defects: none new.
- Blockers: verified inputs (all screened values UNVERIFIED).
- Missing criteria: screens on verified data; any
  recommendation-grade output (screens are filters by design).
- Remediation: roadmap B2.

### Phase 21 — Alerts — PARTIALLY COMPLETE
- Branch/SHA: `phase-21-alerts` `dbeee4a` (ancestor).
- Implementation files: `scripts/run_alerts.py`,
  `alerts/evaluation.py` (dedup key
  `rule_key|source_ref|event_date`).
- Evidence: scratch commit 9 rules, 89 alerts (82 INFO / 6
  WARNING / 1 CRITICAL), 89 deliveries, 9 runs in scratch (vs
  18 claimed — operational-history delta D-DB-02, analytical
  outputs exact); HUBC alerts = 4 (the Phase 22 file-match
  condition ✓); no HBL alert (the undated HBL event does not
  fire); 1 alert preference, in-app only, external consent False.
- Test output: alert tests pass within the 453 suite (21 tests).
- Database/runtime evidence: as above; 8 alerts carry no company
  (sector/macro alerts) — reconciling the 81 company alerts +
  8 non-company = 89 total.
- Defects: none new.
- Blockers: external delivery consent (a decision + a channel);
  verified inputs.
- Missing criteria: any external delivery; alerts on verified
  events.
- Remediation: external-consent decision (parent/user); B2.

### Phase 22 — Reports — PARTIALLY COMPLETE
- Branch/SHA: `phase-22-reports` `45d08ec` (ancestor).
- Implementation files: `scripts/run_reports.py` (approval
  CLI-only: `--approve`/`--reject`; APPROVED means internally
  reviewed only, no publish step, no external send).
- Evidence: scratch commit 8 templates, 22 DRAFT, 541 figures
  (335 computed / 199 insufficient / 7 not_applicable), 188
  sections, 66 exports (22 Markdown + 22 HTML + 22 PDF).
- Test output: report tests pass within the 453 suite.
- Database/runtime evidence: 0 APPROVED reports; report files
  match the fixed database (HUBC alerts = 4) as the recipe
  requires. Side-effect observed: the scratch `--commit` run
  regenerated 4 tracked portfolio-review files, changing the
  HBL exclusion from SCREEN_NOT_RUNNABLE (`no_statements`) to
  SCREEN_PASS (`too_few_dimensions` only) — HBL-inclusive state
  flowing into report content; the 4 files were reverted and
  are not part of this audit's commit.
- Defects: D-12 (token-gated approval belongs to no brief, LOW).
- Blockers: internal review decision for the first APPROVED
  report; any publication path (none exists by design).
- Missing criteria: an APPROVED report; a published report.
- Remediation: roadmap C4 (decision); publication path only on
  a separate brief (and, for market data, permission A1).

### Phase 23 — Dashboard — PARTIALLY COMPLETE
- Branch/SHA: `phase-23-dashboard` `6662d34` (repair commit
  `a5077e0`; ancestor).
- Implementation files: `frontend/app/` (18 nav sections,
  company detail `app/companies/[key]`, report detail
  `app/reports/[id]`), admin pages (acceptance, evaluation,
  jobs, observability), `frontend/lib/api.ts` (prefix `/api/v1`,
  the Phase 23 fix), default API URL `http://localhost:8000`.
- Evidence: webpack production build 27/27 pages (fresh clone);
  Playwright Phase 29 suite 6/6 against scratch backend +
  production build (acceptance page renders run/verdict/counts,
  HBL blocked, no failures, no critical/high defects).
- Test output: frontend vitest 11 passed; Playwright 6 passed.
- Database/runtime evidence: live pages served from scratch
  data; no console errors in the Playwright runs.
- Defects: universe endpoint missing from the API (A-02,
  MEDIUM as a deliverable gap — breaks no runtime caller);
  company detail is id-keyed, not ticker-keyed (LOW contract
  observation).
- Blockers: universe endpoint (A2); any production host.
- Missing criteria: the universe page/endpoint; a deployed
  frontend.
- Remediation: roadmap A2, C3.

### Phase 24 — Security — PARTIALLY COMPLETE
- Branch/SHA: `phase-24-security` `f648bd5` (ancestor).
- Implementation files: `backend/app/services/auth/tokens.py`
  (force-added despite `.gitignore` `*token*`; no literal secret
  — prefix + runtime generation + SHA-256 only),
  PBKDF2-HMAC-SHA256 600k + per-user salt, 5 roles / closed
  5-permission list, append-only `auth_audit_logs`, rate limits
  (300/min API, 30/min auth, in-memory single-process).
- Evidence: auth tables 0/0/0 in scratch (empty by decision);
  readiness `auth_enforcement: "off"` (live); acceptance scans
  9/9 pass incl. `pii_columns` (0 hits) and `tracked_secrets`
  (0 hits); auditor's own greps corroborate (0 dangerous
  constructs, 0 write routes, 0 TODO/FIXME).
- Test output: auth tests pass (24) within the 453 suite.
- Database/runtime evidence: as above; migration 0020 (auth
  tables) applied in scratch, tables empty.
- Defects: none new. Note: `pip-audit` (run by this audit) finds
  no known vulnerabilities — closing the Phase 24 offline gap;
  `npm audit` not run (recorded).
- Blockers: first live auth account decision (A6); enforced-mode
  live test; historical secret scan (tip scans only).
- Missing criteria: operational authentication (accounts +
  enforced mode exercised); production hardening.
- Remediation: roadmap A6.

### Phase 25 — Automation (jobs) — PARTIALLY COMPLETE
- Branch/SHA: `phase-25-automation` `a129614` (ancestor).
- Implementation files: `scripts/run_jobs.py` (subcommands
  register/list/due/run-due/run-one/cancel/retry-dead/status/
  purge); registry with exact Terms pause reasons; runner skips
  paused (`skipped_paused`) and run-one refuses paused;
  re-seeding preserves operator status.
- Evidence: scratch `register` → 8 definitions (5 active, 3
  paused: `market_post_close`, `filing_check`,
  `macro_release_check`); `status` shows pause reasons; job
  runs 0 in scratch vs 71 claimed (operational-history delta
  D-DB-03 — the 71 are accumulated operator invocations, not
  reproducible pipeline output).
- Test output: job tests pass within the 453 suite.
- Database/runtime evidence: as above; dead letters 0,
  watermarks empty in scratch.
- Defects: none new.
- Blockers: Terms clearance for automated polling (A1);
  scheduler decision (host cron vs daemon).
- Missing criteria: any job run history in a fresh deployment;
  any continuously running scheduler (none claimed — jobs are
  operator-invoked by design).
- Remediation: roadmap A1; scheduler decision (parent/user).

### Phase 26 — Evaluation — PARTIALLY COMPLETE
- Branch/SHA: `phase-26-evaluation` `b6f007c` (ancestor).
- Implementation files: `scripts/run_evaluation.py`
  (promotion gates 5, promoted 0 in scratch).
- Evidence: scratch commit 9 model cards, all NOT_PROMOTED;
  evaluation metrics 50 (38 computed / 11 not_evaluable / 1
  not_applicable) vs handover 44 (32 / 11 / 1) — divergence
  D-DB-04 (HBL mechanism, +6 computed); golden cases 14, 13
  pass / 1 fail in scratch vs 14/14 at Phase 26 — divergence
  D-DB-05 (the failing case `golden_refusal_hbl_missing` carries
  evidence `{"hbl_documents": 1}`: a stale pre-HBL expectation,
  not a regression).
- Test output: evaluation tests pass within the 453 suite.
- Database/runtime evidence: as above; by-subject computed:
  agent 8, backtest 3, drift 7, forecast 5, rag 4,
  recommendation 6, reports_qa 5.
- Defects: none new (the golden-case staleness is a test-data
  update need, not a code defect — recorded under D-DB-05).
- Blockers: HBL-inclusive golden-case update (refresh the
  refusal case now that HBL exists); verified inputs for
  meaningful evaluation.
- Missing criteria: a promoted model; 14/14 golden on the
  current state.
- Remediation: refresh the stale golden case under a brief;
  roadmap B2 (verified inputs).

### Phase 27 — Observability — PARTIALLY COMPLETE
- Branch/SHA: `phase-27-observability` `544fecc` (ancestor).
- Implementation files: `scripts/run_observability.py`,
  SLO definitions (14), source health (9), exceptions,
  incidents, performance probes (13).
- Evidence: scratch commit SLO measurements 14 (7 met / 6
  unmet / 1 not_evaluable) vs handover 10 / 4 / 0 — divergence
  D-DB-06, fully reconciled (job_success_rate → not_evaluable
  on 0 runs; golden_pass_rate → unmet on 13/14; drift → unmet on
  the 6 HBL/LEAP tables; the 4 Phase 27 unmet SLOs remain unmet);
  source health 9 (1 stale: market_prices); exceptions 8 vs 6
  (D-DB-07, untraced +2); incidents 3, all resolved; probes 13.
- Test output: observability tests pass within the 453 suite.
- Database/runtime evidence: as above; the readiness artifact
  (A-01) originates in this phase's endpoint code.
- Defects: A-01 (LOW, readiness constant).
- Blockers: operational monitoring (docs + SLOs only, not a
  running monitor); the drift baseline predates HBL (needs a
  re-baseline decision, not a code fix).
- Missing criteria: operational (vs documentary) monitoring;
  a current baseline; met SLOs for freshness/coverage.
- Remediation: roadmap A4; re-baseline decision (parent).

### Phase 28 — Deployment — PARTIALLY COMPLETE
- Branch/SHA: `phase-28-deployment` `b791b7d` (ancestor).
- Implementation files: `ops/start.sh` (exec-in-subshell,
  production-build-only frontend, postgres left running by
  `stop.sh`), `ops/update.sh` (dirty-tree refusal, ff-only pull,
  alembic upgrade, health gate, backup-based rollback),
  `ops/healthcheck.sh` (strips the " (head)" suffix),
  `ops/install.sh` (systemd units + `systemd-analyze verify`),
  backup manifest (40 tables, counted list matches the claim).
- Evidence: statically reviewed by this audit (fixes present);
  deployment test passes in the standard layout, fails in a
  non-standard layout (missing `.venv`/`node_modules` binaries
  — test-environment coupling, LOW, not a code defect);
  backup/restore drill re-verified in scratch (see test report).
- Test output: deployment tests pass within the 453 suite
  (standard layout).
- Database/runtime evidence: no production deployment exists
  to probe; scratch backend started/stopped cleanly via the
  documented launch form.
- Defects: A-01 (readiness constant, LOW); layout-sensitive
  deployment test (LOW).
- Blockers: deployment target + approval (C3); PyMuPDF licence
  decision (pre-deployment gate).
- Missing criteria: a deployed service; a production health
  check; a production backup schedule.
- Remediation: roadmap A4, C3.

### Phase 29 — Acceptance — PARTIALLY COMPLETE
- Branch/SHA: `phase-29-acceptance` `858e914` (ancestor;
  unmoved base for the audit).
- Implementation files: `scripts/run_acceptance.py`,
  `backend/app/services/acceptance/gate.py` (honest-by-
  construction gate logic, verified in code),
  `backend/app/services/acceptance/audits.py` (9 scans),
  `docs/phase-29/defect_register.md` (14 defects).
- Evidence: scratch acceptance run `phase29-acceptance-
  2026-11-05`, verdict PARTIALLY COMPLETE; 15 scenarios (12
  pass / 0 fail / 1 blocked / 2 not_evaluable); 15 recomputations
  (14 matched / 1 expected HBL-drift mismatch); 14 defects
  (0/0/6/8; 2 open D-04/D-12, 2 fixed D-05/D-13, 10 accepted);
  9/9 scans pass; gate G1 NOT_MET / G2 MET / G3 MET / G4 MET /
  G5 PARTIAL — re-derived from scratch, identical to the claim.
- Test output: acceptance tests pass within the 453 suite;
  Playwright acceptance suite 6/6 against scratch backend.
- Database/runtime evidence: gate served live by
  `GET /api/v1/acceptance/gate` with identical content.
- Defects: D-04 (MEDIUM, open), D-12 (LOW, open) — see defects
  report.
- Blockers: HBL chain (baseline predates HBL downstream; the
  batch lineage is the follow-up — D1); human sign-off (G5).
- Missing criteria: G1 met; G5 met (a recorded human signature).
- Remediation: roadmap D1 (follow-up audit of the batch
  lineage); sign-off decision (user/parent).

### Phase 30 — Release & handover — PARTIALLY COMPLETE
- Branch/SHA: `phase-30-release` `8937338` (handover `6b1ff9f` +
  parent consolidation #2 `8937338`; tag `v0.2.0-handover`
  `3dcae17` peels to `6b1ff9f`, not to the tip — A-05).
- Implementation files: `docs/phase-30/handover_report.md` (672
  lines), `run_report.md` (308 lines), `release_checklist.md`
  (145 lines), `implementation_specification.md`,
  `licence_and_source_inventory.md`, `documentation_index.md`,
  `user_guide.md`, `developer_guide.md`,
  `backend/tests/test_release_phase30.py` (5 tests), README
  Phase 30 section, CHANGELOG `[0.2.0-handover]`.
- Evidence: handover structure verified (six-way separation
  IMPLEMENTED / VERIFIED / PARTIALLY VERIFIED / UNAVAILABLE /
  BLOCKED / PLANNED; ten acceptance workflows mapped; explicit
  NOT-claimed list); fresh-clone reproducibility reproduced by
  this audit; backup/restore drill re-verified in scratch;
  release checklist explicitly lists as NOT released: merge to
  main, external deployment, live auth accounts, approved/
  published reports, external notifications, CI-in-CI, quality
  promotions, live PSX collection, HBL re-runs.
- Test output: release tests pass within the 453 suite.
- Database/runtime evidence: the handover's live census is the
  cross-check target for the scratch reproduction (29 of 33
  headline groups exact; divergences reconciled in the database
  audit).
- Defects: A-02 (integration gap, MEDIUM — the consolidation is
  documentary, not a code merge); A-05 (tag/tip, LOW).
- Blockers: everything in §4 of the defects report (the handover
  is a snapshot of a partial system, not a release).
- Missing criteria: a production release; a merge to main; a
  human sign-off; a release tag covering the tip.
- Remediation: roadmap A2, A5, C3, D1. The handover's own verdict
  (PARTIALLY COMPLETE) is confirmed by this audit.
