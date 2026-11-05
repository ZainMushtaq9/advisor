# Phase 30 — Run Report

Run: `phase30-release-2026-11-05`. Branch: `phase-30-release`
(from `phase-29-acceptance` `858e914`).
Verdict: **Phase 30 PARTIALLY COMPLETE**. System verdict unchanged:
**PARTIALLY COMPLETE** (Phases 1–3 COMPLETE, Phases 4–30 PARTIALLY
COMPLETE). No verdict upgraded, no human sign-off claimed.

## What changed

Two commits on `phase-30-release` (full SHAs in §Commit record):

1. `e84e92b` — release + handover snapshot: 7 new
   `docs/phase-30/` files (implementation specification, release
   checklist + rollback plan, licence + source inventory,
   documentation index, user guide, developer guide, handover
   report), README Phase 30 status section (+ Docker corrections),
   CHANGELOG `[0.2.0-handover]` entry, and the release test file
   `backend/tests/test_release_phase30.py` (5 tests).
2. This file (`run_report.md`) — second commit, then tag
   `v0.2.0-handover` on the final tip (see §Commit record).

No application code, no migration, no API route, no script
behaviour changed. No business database row was written by this
phase: every live-database interaction below was read-only
(`SELECT`s, `pg_dump`, TestClient `GET`s), and the restore drill
wrote only to a scratch database that was dropped afterwards.

## Database counts before / after (identical — nothing written)

| Group | Before | After | Note |
|---|---|---|---|
| companies / securities / sectors | 470 / 470 / 37 | 470 / 470 / 37 | All UNVERIFIED |
| registry_evidence | 1,001 | 1,001 | 940 DPS + 61 secp_leap |
| company_identifiers | 0 | 0 | CUINs recorded only |
| market_prices | 444 | 444 | One date 2026-11-03, all UNVERIFIED |
| financial_documents / statements / line items / opinions | 4 / 118 / 2,116 / 4 | 4 / 118 / 2,116 / 4 | HUBC 8 / NML 56 / OGDC 24 / HBL 30 |
| technical runs / errors / values | 1 / 124 / 0 | 1 / 124 / 0 | 0 calculable values |
| fundamental values / valuations | 108 / 51 | 108 / 51 | All UNVERIFIED |
| economic_indicators | 12 | 12 | 6 VERIFIED (caveat in handover), 6 UNVERIFIED |
| news_events / event-companies | 7 / 3 | 7 / 3 | Coverage 3/470 |
| forecast_assessments | 120 | 120 | ALL insufficient_inputs |
| risk values / decisions / portfolios / backtest runs | 81 / 4 / 3 / 5 | 81 / 4 / 3 / 5 | Decisions WITHHELD; backtests NOT_RUNNABLE |
| rag_chunks / benchmark results | 943 / 6 | 943 / 6 | r3 only; r1/r2 never re-fabricated |
| screen_results (241 MATCH) / alerts (89) | 1,418 / 89 | 1,418 / 89 | In-app only |
| reports (all DRAFT) / report_figures | 22 / 541 | 22 / 541 | 335 computed / 199 insufficient / 7 not_applicable |
| job_definitions / job_runs | 8 / 71 | 8 / 71 | 3 collection jobs PAUSED |
| model cards (NOT_PROMOTED) / evaluation_metrics | 9 / 44 | 9 / 44 | 32 computed metrics |
| SLO definitions / measurements (10 met, 4 unmet) | 14 / 14 | 14 / 14 | market_prices stale |
| auth_users / tokens / audit_logs | 0 / 0 / 0 | 0 / 0 / 0 | Empty by decision |
| acceptance runs / scenarios / recomputations / defects | 1 / 15 / 15 / 14 | 1 / 15 / 15 / 14 | 12 PASS / 1 BLOCKED / 2 NOT_EVALUABLE; 14 matched / 1 expected drift; 0 critical, 0 high |
| migration head | `20261104_0024` | `20261104_0024` | No migration in this phase |

"Before" is the parent-verified Phase 29 census, re-read live in
this run (backup manifest 40 counts, drill verification, and the
recomputations below all agree with it). "After" is the same live
database after all Phase 30 work.

## Computed vs NOT_CALCULABLE (this phase)

Phase 30 has no computable financial output: it is descriptive /
analytical only, by design. Nothing computed, nothing
NOT_CALCULABLE added — the standing NOT_CALCULABLE surface is
unchanged (technical values 0, forecasts 0 computed, backtests
NOT_RUNNABLE, mean-variance NOT_CALCULABLE, false-positive rate
NOT_MEASURABLE, P/B / P/S / market cap / EV / dividend yield
blocked on share counts).

## Independent recomputations (live DB rows, this run — all matched)

| Check | Recomputed | Stored / recorded | Result |
|---|---|---|---|
| Company ids by ticker | HUBC 759, NML 864, OGDC 873, HBL 747 | Parent-verified ids | MATCH |
| Breadth coverage | 444 / 470 = 0.944681 | 0.944681 | MATCH |
| Screen outcomes | MATCH 241, NO_MATCH 680, INSUFFICIENT_DATA 497 (total 1,418) | 241 MATCH, 1,418 total | MATCH |
| Alerts by severity | INFO 82, WARNING 6, CRITICAL 1 (total 89) | 82 / 6 / 1 = 89 | MATCH |
| Report figures | computed 335, insufficient_inputs 199, not_applicable 7 (total 541) | 335 / 199 / 7 = 541 | MATCH |
| Portfolios (holdings + cash = capital) | 999,473.03 + 526.97; 999,581.14 + 418.86; 899,884.10 + 100,115.90 | 1,000,000 each (Phase 16 run report) | MATCH |
| Volume median / top-10 share | 54,631.5 / 49.249694% | 54,631.5 / 49.249694% | MATCH |
| Closes 2026-11-03 | HUBC 197.24, OGDC 303.63, HBL 286.16 | Same | MATCH |
| HUBC trailing P/E | 197.24 / 38.26 = 5.155254 | 5.155254 | MATCH |
| OGDC trailing P/E | 303.63 / 16.98 = 17.881625 | 17.881625 | MATCH |
| HUBC gross margin | 29,688,160,000 / 71,126,352,000 = 0.41740029… | 0.417400 | MATCH |
| HBL PAT / EPS (FY2025) | 66,763,916,000 Rs / 45.48 | 66,763,916 (Rs '000s) / 45.48 | MATCH |
| HBL SFP identity 2025 | 7,219,529,515,000 + 488,614,705,000 = 7,708,144,220,000 | total_assets same | MATCH |
| HBL SFP identity 2024 | 5,644,314,783,000 + 410,798,094,000 = 6,055,112,877,000 | total_assets same | MATCH |

Method notes: identity resolved by ticker via `securities` (the
`companies` table has no ticker column — the first recomputation
query failed on that assumption and was corrected). Screen
`result` is stored as `outcome`; statement types are
`balance_sheet` / `income` / `cash_flow` / `changes_in_equity`
(not SFP/PL). Portfolio reconciliation is holdings + residual cash
(Phase 16 rule: whole shares, residual cash absorbs rounding;
portfolio 3's 100,115.90 cash is the 90% conservative cap, not an
error).

## Test results

| Suite | Result | Notes |
|---|---|---|
| Backend pytest (`~/workspace/psx-p30`) | **453 passed**, 5 warnings | 448 Phase 29 tests + 5 new Phase 30 tests. First run: 2 new-test failures (substring mismatches from a table pipe and a README line break) — fixed in the docs, not by weakening the tests; re-run green. Ruff check on `app`, `services`, and the new test file: clean. New test file ruff-format clean. |
| Frontend vitest (`~/workspace/psx-p30`) | **11 passed** (3 files) | Unchanged from Phase 29. |
| Frontend production build, webpack (`~/workspace/psx-p30`) | **Compiled, 27 routes** | `app-path-routes-manifest` = 27 entries, matching Phase 29. |
| Fresh-clone reproducibility | **PASS** (see below) | Backend 453 passed, vitest 11 passed, webpack build 27/27 pages, 27 routes — identical to the worktree run. |
| Playwright | **Not re-run** | No frontend code changed in this phase; Phase 29's 6-passed suite stands and is NOT re-claimed as a Phase 30 run. |
| Phase 30 release test (5 tests) | **5 passed** | Handover six-way separation (IMPLEMENTED / VERIFIED / PARTIALLY VERIFIED / UNAVAILABLE / BLOCKED / PLANNED), Phase 29 gate verbatim (G1 NOT_MET, G5 PARTIAL, no sign-off claimed), system verdict PARTIALLY COMPLETE with HBL noted, CHANGELOG `[0.2.0-handover]` entry, README Phase 30 status section ("NOT a production release"). |

## Fresh-clone reproducibility test

- Clone: `git clone --branch phase-30-release --single-branch`
  from origin → tip `e84e92b`, clean status, no extra files.
- First attempt in `/tmp` FAILED on environment, not on code:
  `/tmp` is a 512 MB tmpfs with 163 MB free; `pip install` hit
  "No space left on device" (Errno 28) while building the fresh
  venv. Root disk has 6.7 GB free. The test was therefore run in
  `~/workspace/psx-fresh30` (deleted after the run) — an
  environment constraint to note for future fresh-environment
  tests, not a release defect.
- Fresh venv: created in 4 s, `pip install -r
  backend/requirements.txt` in 38 s, imports OK.
- Fresh backend suite: 453 passed in 34 s.
- Fresh frontend: `npm install` in 20 s, vitest 11 passed,
  webpack build compiled in 17 s, 27/27 pages generated, 27 routes.
- Conclusion: a fresh checkout of the pushed branch reproduces
  the worktree results exactly.

## Backup / restore drill

- Backup: `2026-11-05T0642-PKT` in the normal location
  (`storage/backups/`), taken with the Phase 30 branch's
  `database/backup.sh` (40-count manifest) against the live store.
  Dump 1.1 MB, files archive 24 MB, manifest SHA-256 verified.
  Manifest counts match the live census exactly (470 / 444 / 4 /
  118 / 2,116 / 89 / 22 / 541 / 943 / 1,418, alembic
  `20261104_0024`).
- Two drill-setup failures, both operator-side, both recorded
  honestly:
  1. Pointing `PSX_STORAGE_ROOT` at an empty drill directory made
     `tar` fail (the script correctly fails loudly since Phase
     28's fix — it no longer masks tar failures). The correct use
     is pointing it at the real store root; the worktree checkout
     alone lacks the gitignored file-store classes.
  2. The first restore attempt failed (1,362 pg_restore errors,
     tables absent) because the `USAGE, CREATE ON SCHEMA public`
     grant was issued while connected to the default database
     instead of the drill database. After granting on the drill
     database itself, the restore passed.
- Restore: `database/restore.sh` into scratch database
  `psx_intelligence_p30_drill` → "VERIFIED — row count matches
  manifest", files-archive hash OK (archive NOT auto-extracted
  over the live store, by design).
- Verification: `database/verify_restore.sh` → "VERIFIED —
  hashes, counts and revision all match manifest" (all 40 counts,
  alembic `20261104_0024`).
- Direct drill-DB counts: 470 / 444 / 118 / 2,116 / 89 / 22 / 541
  — matching live. Live DB re-checked unchanged (470 companies).
- Cleanup: scratch database dropped. The `2026-11-05T0642-PKT`
  backup remains in the normal backups location as a valid
  backup (retention: 30 valid backups).
- Minor script quirk observed: two `backup.sh` runs inside the
  same minute share one timestamped directory, so the second run
  overwrote the first run's manifest (content identical except
  the manifest format — the first run used the stale
  phase-21-era script from the main worktree checkout, the second
  the Phase 30 script). No data loss; minute-granularity stamps
  are a known limitation, not a defect introduced here.

## Final audit scans (authoritative scanner, this run)

`backend/app/services/acceptance/audits.py::run_audits` against
the Phase 30 worktree (= tip `e84e92b`) and the live database.
All 9 checks PASS, 0 hits each:

| Check | Result |
|---|---|
| execution_identifiers | PASS, 0 |
| dangerous_constructs | PASS, 0 |
| write_routes | PASS, 0 |
| upload_endpoints | PASS, 0 |
| docker_invocations | PASS, 0 |
| tracked_datasets | PASS, 0 |
| tracked_secrets | PASS, 0 |
| branch_tip_datasets (all pushed branch tips, incl. `phase-30-release`) | PASS, 0 |
| pii_columns (email/phone/ssn/passport pattern) | PASS, 0; auth tables 0 / 0 / 0 |

Method correction recorded: an ad-hoc `grep` across docs and
tests first reported 69 / 1 / 38 hits and 10 PII-like columns.
Those were false positives from the methodology, not the code:
the authoritative scanner covers `.py`/`.sh` in `backend/app`
(execution/dangerous/write/upload) and `CODE_DIRS`
(`backend/app`, `ops`, `scripts`, `database`) for docker, skips
test files and itself, and uses the email/phone/ssn/passport
pattern for PII (the broader pattern matched auth-table hash
columns). The authoritative run above is the reported result.
Scan boundary (unchanged from Phase 29): dataset/secret scans
cover branch tips, not every historical commit.

## Live API smoke (TestClient, GET-only, live DB)

| Route | Status | Payload note |
|---|---|---|
| `/health` | 200 | `{'status': 'ok', 'service': 'psx-intelligence-ai'}` |
| `/api/v1/registry/statistics` | 200 | 470 / 470 / 37, all UNVERIFIED, evidence 1,001 |
| `/api/v1/acceptance/summary` | 200 | verdict PARTIALLY COMPLETE; scenarios 15 (12 / 0 / 1 / 2); recomputations 15 (14 / 1); defects 14 (0 critical, 0 high, 6 medium, 8 low; 2 open, 2 fixed, 10 accepted) |
| `/api/v1/acceptance/gate` | 200 | gate table as carried in the handover |
| `/api/v1/acceptance/scenarios` | 200 | — |
| `/api/v1/acceptance/recomputations` | 200 | — |
| `/api/v1/acceptance/runs` | 200 | — |
| `/api/v1/acceptance/defects` | 200 | — |
| `/api/v1/observability/readiness` | 200 | database available; migration_head `20261104_0024`; **ready `False`** (see observation below) |

Observation (pre-existing, NOT caused by Phase 30, NOT fixed
here): the readiness endpoint hardcodes
`EXPECTED_MIGRATION_HEAD = "20261104_0023"` (Phase 27 artifact,
`observability.py` line 51), so it reports
`migration_matches: False` and `ready: False` against the
correct current head `20261104_0024`. Fixing it needs its own
brief (update the expected revision + a regression test); no
Phase 30 brief covers it, and Phase 30 changed no code.

## HBL note

Statements loaded (4 documents, 118 statements, 2,116 items;
HBL: 30 statements, 800 items, all UNVERIFIED) — unchanged by
this phase. Phases 8+ HBL re-runs remain PENDING after Phase 30
(banking rule: Phase 9 must use the bank residual-income model
for HBL). The HBL decision still predates the statements
(SCREEN_NOT_RUNNABLE/no_statements) and will change in that
batch. The next observability run will show drift vs the Phase
24 baseline from the HBL additions — that is the drift SLO
working as designed, and the baseline update must be recorded
with evidence per the Phase 25 rule. Full batch spec: handover
report, "HBL Phases 8+ re-run batch" section.

## Remaining blockers (exact unblockers)

1. **Written PSX permission evidence** (user-owned) — unlocks
   GEM/Non-Compliant capture, more trading days, PSX announcement
   collection, free-float data, and any VERIFIED promotion.
   The Terms gate is the single largest blocker.
2. **More trading days of price data** (Terms-gated) — 2 closes
   unlock returns, 5 unlock SMA(5), 11 unlock naive forecast
   intervals, 30 unlock volatility/beta/Sharpe/AR(1), 251 unlock
   VaR/ES.
3. **Share-count data** (authoritative shares outstanding + par
   value) — unlocks P/B, P/S, market cap, EV multiples, dividend
   yield, mean-variance.
4. **HBL Phases 8+ re-runs** — parent approval of branch strategy
   (merge or cherry-pick of `phase-07-hbl-extraction` code into
   the phase lineage).
5. **VERIFIED promotion** — H1 second agreeing source including
   one official source, plus (for Phase 18/21 contexts) a recorded
   human approval gate — none granted.
6. **Verified local models** — a verified local/open-weight LLM
   unlocks Phase 18 LLM-backed execution; a verified local
   embedding model unlocks Phase 19 vector retrieval.
7. **First live auth account** — parent/user decision (CLI-only
   creation); auth tables intentionally 0/0/0 until then.
8. **First APPROVED report** — internal review decision (CLI
   transition only, no web approval by design); D-12 token-gating
   belongs to no brief so far.
9. **Real deployment** — operator decisions: enforced-mode
   production proof, backup-encryption key management, dependency
   audit with network, frontend token support (D-10), multi-
   instance rate limiting, readiness expected-revision update
   (see observation above).
10. **Merge to main** — separate approval + an unrelated-histories
    decision (local main `214a701` never pushed, remote main
    `eb6025b` README-only, unrelated histories, no PR exists).
11. **CI-in-CI** — main/development push or PR (separate
    approval).
12. **Register consolidation #2** — parent task, overdue since
    branch tip `59834f1` (this phase did NOT edit the register,
    state, or log files, per the governing brief).
13. **Surrogate-id traps (D-04, OPEN)** — permanent name-based
    sector resolution + ticker-based news publication-date
    mapping with fixture tests; temporary-patch + revert remains
    the documented workaround.
14. **PyMuPDF AGPL review (D-14, accepted)** — trigger: public
    hosted distribution or redistribution; no current violation.

## Worktree / scratch cleanup (post-tag step)

After tagging, the coordinator removes the scratch worktrees
`~/workspace/psx-p30`, `~/workspace/psx-fresh30`,
`~/workspace/psx-leap-load`, `~/workspace/psx-hbl` (all branches
already pushed; removal is safe) and confirms the main worktree
checkout is untouched. The `backend/.venv` symlink in the Phase
30 worktree shows as untracked in `git status` because gitignore
directory patterns (`.venv/`) do not match symlinks — it was
never staged (explicit `git add` only) and was never committed.

## Commit record

- Base: `phase-29-acceptance` `858e914` (unmoved; verified
  before branching).
- Commit 1: `e84e92b` — release + handover snapshot (10 files,
  +1,497 / −5). Pushed to `origin phase-30-release`; remote SHA
  verified equal to local tip.
- Commit 2: this file — SHAs recorded in the coordinator's final
  report after push (this file cannot cite its own commit SHA
  before it exists).
- Tag: `v0.2.0-handover` (annotated) on the final tip, pushed,
  verified via `ls-remote` — recorded in the coordinator's final
  report.
- Main `eb6025b` untouched. No CSV, PDF, or `.env` committed. No
  force-push, no history rewrite, no existing branch tip moved.
