# Blocker-Resolution Run Report — 2026-11-05

**Branch:** `d05-readiness-g5` (from `phase-hbl-reruns` `c71469a`,
unmoved). **Base `phase-30-release`:** `8937338` (unmoved).
**Main:** `eb6025b` (untouched; no merge, no PR).
**Task split honored exactly:** items 1 and 3 executed; items 2, 4,
6 preparation only; item 5 unchanged; item 7 measured.

**Headline:** D-05 is FIXED on measured evidence; the readiness
endpoint is FIXED and retargeted to the live head 0025; the
acceptance gate stands at G1–G4 MET / G5 PARTIAL with zero
recomputation exceptions in force; D-12, G5, and portfolio work are
delivered as briefs/packages only, as ordered. No market data was
fabricated, no permission requirement was bypassed, no verdict was
changed without measured evidence, and no human sign-off is claimed.

## 0. Baseline verification and counts before/after

Guard check at task start matched the batch-end baseline exactly
(fundamentals 144, valuations 68, macro exposures 9, news events 8,
news links 4, ownership 112, corporate actions 9, forecast
assessments 156, decisions 5, RAG chunks 2,020, screen results 1,422,
alerts 89, reports 25, report figures 649, job runs 73, acceptance
runs 3, companies 470, prices 444, statements 118, auth 0/0/0, head
0024 at that moment).

| Table | Before | After | Cause |
|---|---|---|---|
| reports | 25 | 25 | Report 14 deleted, report 26 created (same template/subject) |
| report_figures | 649 | 649 | Figures 339/340 deleted, figures 650/651 created, identical values |
| decisions | 5 | 5 | Re-run wrote 0, skipped 4 (2026-11-04 grain) |
| news_events / links | 8 / 4 | 8 / 4 | News re-run skipped all existing (1,376 aliases, 8 events) |
| risk_metric_values | 95 | 98 | 3 new versioned model rows @ 2026-11-05 (this task) |
| acceptance_runs | 3 | 4 | New run `phase29-acceptance-2026-11-05-blockers` (this task) |
| job_runs | 73 | 73 | No job runs in this task |
| alembic head | 0024 | 0025 | News-intelligence migration 0025 (parallel work, §8) |
| job_definitions | 8 | 11 | News-intelligence Phase B (parallel work, §8) |

## 1. D-05 — RESOLVED (execution)

### 1a. What was actually wrong (measured, not assumed)

There was **no live stale figure at batch end**. Report 14
(`event_brief`, subject `news:HUBC:earning`, DRAFT, 2026-11-04) held
exactly 2 figures — id 339 `event_date` = 2026-09-21 (computed,
sourced_fact, `news_events`) and id 340 `event_type` = earnings
(computed) — matching both the live news event (id 1, earnings,
2026-09-21, pending_review) and the committed Markdown export
(line 41). The census delta was fully explained by the HBL batch's
3 new reports (dossier 56 + earnings 25 + valuation 27 = 108
figures; computed +54, insufficient +45, not_applicable +9;
541 + 108 = 649). What persisted was the stale MEASUREMENT: the
pinned 541 = 335/199/7 claim and recovery #6 method text in
`recompute.py`, plus the matching pin in `defects.py`. The
prescribed clean re-derivation was still executed as proof, and the
measurement was then updated to the measured result.

### 1b. Snapshot, deletion, re-derivation (in order)

- **Snapshot BEFORE any deletion:**
  `~/workspace/d05-snapshots/pre_d05_snapshot.sql` (612,354 bytes,
  SHA-256
  `8285fed82a14739e95387753de234ea2484ac2c8f95f86c63d8aa7524bb42f50`),
  9 tables, outside the repo so it cannot be committed.
- **Concurrency re-check immediately before deletion passed:**
  reports 25, figures 649, and no `news_intelligence%` tables in the
  live DB at that time (see §8 for what the parallel work later
  added — different table names, untouched by this task).
- **Deleted report 14 and ONLY its dependents, with RETURNING:**
  figures 339/340, sections 111–118 (8 rows), export rows 40
  (markdown), 41 (html), 42 (pdf), report 14 itself. Counts after
  delete: reports 24, figures 647. No HBL batch row, no news-engine
  row, and no other report was touched.
- **News re-run** (`scripts/run_news_events.py`, dry-run then
  `--commit`): aliases skipped_existing 1,376; events
  skipped_existing 8; duplicates 0. News data is final.
- **Decisions re-run** (`scripts/run_decision_engine.py`, dry-run
  then `--commit`, default date 2026-11-04): rules written 0 /
  skipped 1; decisions written 0 / skipped 4. Deliberately NOT
  re-run with date 2026-11-05 without `--company HBL`: a full
  2026-11-05 run would write 3 extra rows (HUBC/OGDC/NML) and break
  the batch's design (only HBL got a 2026-11-05 row).
- **Reports re-run** (`scripts/run_reports.py --template event_brief
  --subject "news:HUBC:earning"`, dry-run then `--commit`):
  created report 26 with 2 figures, 8 sections. Figures 650
  (`event_date` = 2026-09-21, computed) and 651 (`event_type` =
  earnings, computed) are identical to deleted figures 339/340.
  Export hashes md/html are byte-identical to pre-deletion
  (verified by sha256sum; `docs/phase-22/reports/` git-clean).
  The PDF regenerated with a new hash (expected: PDFs embed
  timestamps; the PDF is gitignored).
- **Census after re-derivation, measured: 389 computed / 244
  insufficient_inputs / 16 not_applicable = 649; reports 25.**
  This measured census — not an advance assertion — is the new
  approved claim.

### 1c. Measurement code updates

- `backend/app/services/acceptance/defects.py`
  `resolve_d05_status()`: census target 335/199/7 → 389/244/16,
  with docstring recording the supersession (Phase 22 claim 541 →
  HBL batch +108 → 649; recovery #6 staleness resolved by recovery
  #7 and confirmed by this re-derivation). HUBC/OGDC scored 6/6
  check kept. (Latent note, not changed: its scored query builds a
  dict keyed by ticker, so HBL's two rows — scored 2 on 2026-11-04
  and scored 6 on 2026-11-05 — collide on one key. The check only
  uses HUBC/OGDC (single-row each), so it is unaffected; noted here
  for a future robustness pass.)
- `backend/app/services/acceptance/recompute.py`:
  `check_report_figure_census()` claim → 649 = 389/244/16 with
  history in the method text; `check_decision_completeness()`
  method text corrected (live rows are 6/6, not the recovery #6
  5/7); logic unchanged.
- `check_drift_vs_phase24_baseline()`: claim and matching logic →
  the Phase 25-rule approved baseline (documents 4, statements 118,
  line items 2,116), with the Phase 24 baseline (3/88/1,316) kept in
  text as history and the drift finding/confirm evidence recorded
  (drift 17 in jobs run 72 + observability finding run; drift 0 in
  jobs run 73 + confirm run). The check key is unchanged for run
  history; it now fails only on NEW drift.
- `backend/app/services/acceptance/gate.py`:
  `KNOWN_RECOMPUTATION_EXCEPTIONS` emptied (all three former entries
  resolved). Any future recomputation mismatch now fails G3 by
  design; re-adding an entry requires a recorded defect + evidence.
  The G3 met-evidence wording was corrected accordingly (no more
  "D-05 omissions / HBL drift" text).
- Tests: `test_d05_fixed_when_census_and_scored_match` now seeds
  (389, 244, 16); `test_d05_open_when_stale` kept (334/200/7 + 5/5 →
  open); new `test_d05_open_when_old_census` proves the superseded
  335/199/7 census now returns open; new
  `test_gate_g3_met_evidence_claims_no_exceptions`; and
  `test_gate_g1_not_met_when_hbl_blocked` updated (a census mismatch
  now correctly yields G3 not_met under the stricter gate — this
  was the one failure in the first full-suite run, and updating the
  expectation is the correct response to the intended behavior
  change, documented in the test).

### 1d. Carried stale-evidence item: forecast_abstention_rate — FIXED

- Problem: the stored MARKET row (id 79, as_of 2026-11-04) cited
  120/120 while the true count was 156/156 (rate still 100%),
  because the runner skips existing grains and the table's unique
  constraint forbids a second row for the same grain. No stored row
  was hand-edited (forbidden by the task).
- Fix (surgical, versioned): `run_risk(..., model_as_of)` threads an
  override into the model-risk section only
  (`forecast_abstention_rate`, `technical_coverage_rate`,
  `input_drift`); CLI gains `--as-of-date` (ISO-validated, exit 2
  on a bad date). Default behavior is unchanged (ANALYSIS_D
  2026-11-04).
- Live result: dry-run with `--as-of-date 2026-11-05` showed exactly
  3 would-write rows; `--commit` wrote exactly 3 (values 3/92);
  new 2026-11-05 MARKET `forecast_abstention_rate` = 100.000000 with
  evidence {assessments: 156, insufficient: 156}; the 2026-11-04 row
  (120/120) is preserved; risk values 95 → 98; a repeat commit
  wrote 0 (values 0/95), total stays 98.
- Regression tests: new `backend/tests/test_risk_runner_asof.py`
  (5 tests: default keeps 2026-11-04; new as-of writes exactly the 3
  model rows and preserves the old vintage; repeat writes nothing;
  CLI threads the date; CLI rejects a bad date). SQLite note: the
  fixture assigns ids in a session-scoped before_flush listener
  because SQLite does not auto-generate BigInteger IDENTITY keys —
  a test-only dialect workaround, scoped to that fixture's session.

### 1e. D-05 status

**D-05: fixed.** The new acceptance run (§7) records it as fixed on
the updated measurement. Nothing in this section was asserted in
advance: every number above was measured before it was claimed.

## 2. D-12 covering brief — DELIVERED (preparation only)

- Document: `docs/blocker-resolution/d12_token_gated_approval_brief.md`.
- Contents: current state (CLI-only `approve()`/`reject()` in
  `reports/runner.py`, DRAFT-only guard, no actor/audit row;
  APPROVED = internally reviewed only; GET-only read paths;
  existing Bearer/`validate_token`/role-gated machinery;
  auth tables 0/0/0 by decision); scope (both write transitions,
  the four read paths, same-transaction audit rows; publishing
  explicitly out of scope); threat model (local/loopback only —
  accidental approval, local-process API calls, token leakage,
  replay on superseded versions; remote attackers explicitly out);
  design (reuse Bearer tokens, new `report_approver` role,
  always-gated writes recommended, CLI token via env var or 0600
  credential file with NO bypass flag, optional API routes, audit
  fields, backward compatibility with loud failure when no token is
  presented); D-10 interaction (dashboard cannot use a gated route
  until frontend token support lands — CLI-only gating is the
  smallest complete step); five decisions needed before
  implementation; tests; acceptance criteria; risks (bootstrap
  chicken-and-egg, operator friction, scope creep into publishing,
  D-10 dependency); rollout steps.
- **NOT implemented in this task, by order.** D-12 remains OPEN
  (low). Its unblocker is now this brief + the §5 decisions, not
  "a phase brief" anymore — the implementing item should record
  that refinement when it updates the register.

## 3. Readiness endpoint — FIXED, retargeted to live head 0025

- The Phase 27 artifact: `EXPECTED_MIGRATION_HEAD` hardcoded
  `20261104_0023` in exactly one place
  (`backend/app/api/v1/endpoints/observability.py:51`), reporting
  `migration_matches` False / `ready` False against any newer head.
- Arc of this task: the brief first said 0023 → 0024 (the branch
  chain head). During this task the live head moved to 0025 (see
  §8), and the parent retargeted the fix to the CURRENT head. The
  constant now reads `20261104_0025`, with a comment explaining the
  full history and the key distinction: **the constant tracks the
  LIVE head, not this branch's migration chain head (0024)** — this
  branch does not carry the 0025 migration file, so a checkout of
  this branch alone truthfully reports not-ready until the news
  migration is merged into its chain. A future migration requires
  updating the constant AND the tests together.
- Hardcode sweep (repo-wide, `20261104_0023|0024|0025` over
  `backend/app`, `backend/tests`, `scripts`, `frontend/*`,
  `ops`, `database`): only the endpoint constant + this task's
  tests hardcode a head. `ops/healthcheck.sh:44` mentions
  `20261104_0023` only as a comment example — its logic parses the
  head dynamically (`alembic heads`), so no change was needed.
  Note: `ops/healthcheck.sh` on this branch reports a migration
  mismatch (live 0025 ≠ branch head 0024) until the news migration
  is merged — truthful behavior, same cause as above.
- Regression tests (updated to the 0025 target):
  `test_readiness_matches_current_head` (head 0025 → matches true,
  ready true, reachable true), `test_readiness_detects_stale_head`
  (head 0024 → matches false, ready false), plus the preserved
  `test_readiness_reports_unavailable_db_truthfully`.
- Live verification (GET-only): first smoke (before the retarget)
  showed head 0025 vs expected 0024 → matches false / ready false
  — which is how the 0025 move was independently discovered in this
  task. After the retarget, a second smoke (uvicorn on 127.0.0.1:8001,
  stopped afterwards) showed head 0025, expected 0025, matches true,
  ready true. A third confirmation came from the stack backend on
  port 8000 during Playwright (§7): same result.

## 4. G5 evidence package — DELIVERED (preparation only, UNSIGNED)

- Document:
  `docs/blocker-resolution/g5_signoff_evidence_package.md`.
- Contents: gate table with verbatim measured evidence (G1–G4 MET,
  G5 PARTIAL); run history for all 4 runs (pre-batch PARTIALLY
  COMPLETE; mid-batch FAILED with 4 failed scenarios and D-04/D-05/
  D-12 open — superseded; batch-end PARTIALLY COMPLETE via
  exceptions; this run PARTIALLY COMPLETE with zero exceptions);
  new-run detail (14 scenarios: 12 pass, 2 not_evaluable, 0 fail;
  15/15 recomputations; 14 defects; 9/9 repo audits); defect status
  (D-05 fixed, D-12 open, Terms BLOCKED, remainder accepted);
  test evidence; known limitations (HBL rows UNVERIFIED, prices
  UNVERIFIED, readiness-vs-chain-head distinction, parallel
  news-engine tables outside acceptance coverage, remaining frontend
  stale copy, auth 0/0/0, audit D1 recommendation for a fresh
  post-batch audit); sign-off block left UNSIGNED.
- **No signature is claimed by this package, by any code, or by any
  run.** G5 stays PARTIAL until a human completes §7 of that
  document.

## 5. PSX Terms gate — BLOCKED (no change)

- Status: **BLOCKED, unchanged.** No written permission evidence
  exists. The permission request was sent 2026-11-04 from 5439 to
  marketdatarequest@psx.com.pk (Gmail message/thread
  `1a1a66ca3ef85eeb`); the user-reported reply was permanently
  deleted including from trash, so its wording is unverifiable and
  does NOT clear the gate; no resend was sent (user declined
  2026-11-04).
- In this task: no PSX email, no DPS systematic collection, no
  VERIFIED promotion, no bypass of any kind. HBL extraction used
  HBL's own investor-relations page (issuer IR, sampled only,
  internal analysis only, no republication) — unchanged from the
  batch. The news-intelligence work's DPS collection stays BLOCKED
  on the same gate.
- Exact unblocker: written permission evidence (user-owned).
  Reply-watch cron `psx-permission-reply-watch` remains active
  every 6h (checks 5439 for `from:psx.com.pk`; silent if none; on a
  reply, delivers full text + assessment, then removes the
  schedule).

## 6. HBL portfolio expansion brief — DELIVERED (preparation only)

- Document:
  `docs/blocker-resolution/hbl_portfolio_expansion_brief.md`.
- Contents: current baseline (3 simulated portfolios, PKR
  1,000,000, price_date 2026-11-03; ledger 13 rows; comparisons 3);
  the three STALE HBL `SCREEN_NOT_RUNNABLE` exclusion rows quoted
  verbatim, to be superseded by versioning (never overwritten);
  eligibility evidence (HBL quote ELIGIBLE at 286.16; 2026-11-05
  SCREEN_PASS decision 6/7; fundamentals/valuations present;
  forecasts abstained — no expected return assumed); three proposed
  new versions (`ew_statements_4_balanced`,
  `rule_screen_pass_balanced_v2`, `rule_screen_pass_conservative_v2`,
  same capital/price date/method/caps); Phase 17 ledger
  re-derivation plan (snapshot → construct → ledger → supersede
  exclusions → comparisons → acceptance reconciliation check →
  reports only if the implementing brief says so, in news-first
  order); cash reconciliation identity (capital = holdings + cash,
  whole-share rounding, residual cash, > PKR 0.01 failure rule);
  comparison methodology (v2 vs predecessor only, banking sector
  shown separately, returns NOT_CALCULABLE on one price date);
  tests; acceptance criteria; risks (sector concentration at 25%
  single-bank weight, banking-model gaps → `not_applicable`,
  single-date depth limits, stale-exclusion confusion, no trading
  scope creep).
- **NOT executed in this task, by order.** No portfolio, ledger,
  comparison, or exclusion row was created, changed, or deleted.

## 7. Regression + acceptance (item 7)

### 7a. New acceptance run (committed)

- Run id: `phase29-acceptance-2026-11-05-blockers`, verdict
  PARTIALLY COMPLETE, committed (dry-run first, then `--commit`;
  a post-retarget dry-run with a fresh id confirmed the identical
  gate table and wrote nothing — acceptance runs stay 4).
- Gate table: G1 MET (all four company chains pass), G2 MET (0
  critical, 0 high open), G3 MET (15/15 recomputations match, no
  exceptions in force), G4 MET (9/9 audits pass; boundary: branch
  tips, not every historical commit), G5 PARTIAL (human sign-off
  pending). The verdict is PARTIALLY COMPLETE for one reason only:
  G5 itself, by design.
- Scenarios: 14 (12 pass, 2 not_evaluable — restatement,
  suspended_security — 0 fail, 0 blocked).
- Recomputations: 15/15 match, including `report_figure_census`
  (649 = 389/244/16) and `drift_vs_phase24_baseline` (4/118/2,116).
- Defects: 14 (D-03/D-04/D-05/D-13 fixed; D-12 open; remainder
  accepted). No new failures appeared; had any appeared they would
  have been reported exactly, not reworded.

### 7b. Regression test evidence

| Suite | Command | Result |
|---|---|---|
| Backend pytest (full) | `backend/.venv/bin/python -m pytest tests/ -q` | **477 passed** (batch baseline 468 + 9 new/changed tests in this task) |
| Frontend vitest | `frontend/node_modules/.bin/vitest run` | **11 passed** (3 files, baseline unchanged) |
| Webpack production build | `frontend/node_modules/.bin/next build --webpack` | **exit 0, 27/27 pages, 27 routes** (incl. corrected news page) |
| Playwright phase23 | `playwright test --config playwright.phase23.config.ts` (stack up) | **22 passed** (baseline 22/22) |
| Playwright phase29 | `playwright test --config playwright.phase29.config.ts` (stack up) | **6 passed** (baseline count 6, specs updated — see §7c) |
| Live readiness smoke | GET `/api/v1/observability/readiness` (ports 8001, then 8000) | head 0025, expected 0025, matches true, ready true |

### 7c. Playwright: what failed first, and why it is not a product regression

1. **Missing backend (harness setup, not product failure).** The
   first runs executed with no backend on port 8000 (the suites
   render pages that fetch from the API), so content locators were
   not visible: phase23 18 failed / 4 passed, phase29 6 failed.
   Starting the backend (uvicorn from this worktree, port 8000,
   stopped afterwards) fixed phase23 completely: 22 passed.
2. **Stale phase29 assertions (superseded state, updated on
   measured evidence).** With the stack up, phase29 still showed 4
   failures — two assertions per project that encoded states this
   task was ordered to end: "14 matched / 1 mismatched (the
   expected HBL drift)" and the retired `chain_hbl_partial` /
   "blocked" scenario. The live API confirms the current state:
   latest run = blockers run, scenarios 14 total / 12 pass / 0 fail
   / 0 blocked / 2 not_evaluable, recomputations 15 matched /
   0 mismatched, scenario keys `chain_*_full` all passing. The spec
   was updated to exactly those measured values (same discipline as
   the backend census updates — values moved forward, assertions
   not weakened: counts stay exact, "no failures" intent kept, the
   retired key's absence is now asserted via `chain_hbl_full` +
   "0 blocked"). Re-run: **6 passed, exit 0.**
3. **Turbopack build note (environment artifact, not a code
   failure).** Plain `next build` (Turbopack) fails in this worktree
   only: "Could not find the Next.js package" because the
   worktree's `node_modules` is a symlink to the main worktree's
   install, which falls outside Turbopack's workspace root. The
   webpack build — the baseline's method — succeeds (27 routes).
   No project config was changed to work around the worktree
   layout; the frontend `AGENTS.md` Next.js rules were read and the
   change made was display-string-only (no API/structure change).

### 7d. Frontend copy fix (authorized optional item)

- The Phase 11 news page said "three company earnings events and
  four macro events" with a "Coverage is 3 of 470 companies"
  banner. Verified live: earnings 4, macro_release 4, distinct
  companies with news links 4. Both strings on that page were
  corrected ("four company earnings events and four macro events";
  "Coverage is 4 of 470 companies") — display strings only, no data
  change, no test asserted the old strings, vitest + build green
  after.
- Remaining stale copy on OTHER pages (not fixed — outside the
  authorized one-line scope, noted as follow-ups): company detail
  page "Seed coverage is 3 of 470 companies"; home page statements
  line "3 of 470 companies (HUBC, NML, OGDC)" (statements now cover
  4 companies including HBL).

## 8. Concurrency and parallel-work notes

- **Live head 0024 → 0025 during this task (EXPECTED, not
  interference).** The news-intelligence coordinator applied
  migration 0025 as gated Phase B work (branch `news-intelligence`,
  tip `57f77ec` per the parent; the migration commit is visible
  locally as `66b58c8`). The live DB gained 9 news-intelligence
  tables; measured here: news_sources 8, news_collection_runs 8,
  news_articles 0 (by design), news_summaries/sentiment/impact 0;
  job_definitions 8 → 11 (two new collection jobs PAUSED, one
  read-only digest job active); 8 refused collection runs;
  8 INSUFFICIENT_DATA market-reaction rows. All D-05-table counts
  (news_events 8, decisions 5, reports 25, figures 649) are
  unchanged by that work, and this task's deletion touched only
  report 14 + dependents — no news-engine row was deleted or
  overwritten. The parent's updated brief explicitly clears the head
  and job-definition deltas as expected; the stop rule for D-05
  tables was never triggered.
- **Independent 30-phase audit is COMPLETE** (branch
  `final-30-phase-verification-audit`, verdict C — 3 of 30 phases
  COMPLETE, 0 failed; its G1 NOT_MET predates the HBL batch and it
  makes no claim about the batch). It recommends a fresh audit of
  the post-batch lineage (item D1) — not part of this task, noted
  here for the parent. Its branch and evidence were not touched.
- **No VM restart occurred during this task**; no recovery was
  needed. PostgreSQL cluster 16/main stayed online throughout.

## 9. Files changed (this branch only)

Modified: `backend/app/api/v1/endpoints/observability.py`,
`backend/app/services/acceptance/defects.py`,
`backend/app/services/acceptance/gate.py`,
`backend/app/services/acceptance/recompute.py`,
`backend/app/services/risk_analytics/runner.py`,
`backend/tests/test_acceptance_phase29.py`,
`backend/tests/test_observability_phase27.py`,
`frontend/app/news/page.tsx`,
`frontend/e2e/phase29/acceptance.spec.ts`,
`scripts/run_risk_analytics.py`.
New: `backend/tests/test_risk_runner_asof.py`,
`docs/blocker-resolution/` (this report, D-12 brief, G5 package,
portfolio brief, proposed register entry).
NOT committed (untracked by design): `backend/.venv`,
`database/.venv` (symlinks), `frontend/test-results/`
(Playwright output), the regenerated PDF (gitignored), the D-05
snapshot (outside the repo). The three consolidated register files
were NOT edited (parent consolidates; proposed entry supplied).
No CSVs, PDFs, `.env` files, or credentials were committed; no
credential value appears in any file, log, or report here.

## 10. Remaining blockers with exact unblockers

| Blocker | Status | Exact unblocker |
|---|---|---|
| D-12 token-gated approval | OPEN (low) | Brief's approval + the §5 decisions (route scope, gating mode, token bootstrap, D-10 sequencing) — then a separate implementing work item. No live auth accounts exist (0/0/0 by decision), so token bootstrap needs its own authorization. |
| G5 human sign-off | PARTIAL | A human completing §7 of the G5 evidence package. No code or run can supply this. |
| PSX Terms gate | BLOCKED | Written permission evidence (user-owned); reply-watch cron still active. |
| Readiness vs branch chain head | KNOWN LIMIT | Merging migration 0025 into this branch's chain (or the branch that owns the endpoint) so the branch head and the live head agree; until then the endpoint truthfully reports not-ready on a bare checkout of this branch. Same cause makes `ops/healthcheck.sh` report a migration mismatch on this branch. |
| HBL portfolio expansion | NOT STARTED (brief only) | Approval of the portfolio brief + a separate implementing work item (snapshot → construct → ledger → comparisons → reconciliation check). |
| Frontend stale copy (2 pages) | OPEN (trivial) | A copy pass on the company detail page and home page statements line (see §7d). |
| Fresh post-batch audit (D1) | RECOMMENDED, not tasked | Parent decision to commission a fresh audit of the post-batch lineage, per the completed 30-phase audit's recommendation. |
| HBL rows / prices verification | UNVERIFIED (by design) | A second agreeing source including an official source (PSX/SECP) — which itself needs the Terms gate cleared for systematic PSX collection. HBL rows stay UNVERIFIED until then; nothing here promotes them. |

## 11. What was NOT done (explicitly, per the brief)

- No re-running of Phases 1–30; no re-doing of the HBL batch.
- No D-12 implementation; no G5 signature; no portfolio expansion
  execution; no PSX email; no DPS collection; no VERIFIED promotion.
- No merge to main; no force-push; no history rewrite; no branch-tip
  moves; no deletions of branches, reports, or evidence (except the
  single snapshotted report-14 re-derivation, recreated as report
  26); no overwrites of previous reports (all new evidence is new
  rows/files).
- No live auth accounts created; no money spent (PKR 0); no Docker
  used anywhere.
