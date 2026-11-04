# Phase 25 — Run report

**Verdict: PARTIALLY COMPLETE** (see gate judgement below).
Phase 26 NOT started. Register files NOT edited (parent
consolidates).

## What changed

- **Branch:** `phase-25-automation`, new branch from
  `phase-24-security` (`f648bd5`).
- **Commit:** (filled at push time — see parent
  verification note).
- **Bases untouched:** remote `phase-24-security` still
  `f648bd5`, remote `main` still `eb6025b`. No merge to
  main, no force-push, no history rewrite, no cross-push,
  no register files edited, no CSVs/PDFs committed, no
  credentials anywhere.
- **Migration:** `20261104_0020` → `20261104_0021`
  (4 job tables), applied to the live DB.
- **Worktree:** `~/workspace/psx-p25` (linked worktree;
  removed after push, main worktree undisturbed).

## What was built (brief lines 1801–1857)

Job registry + scheduler (DB-backed, single-pass,
operator-invoked, no daemon, no paid service, no
Celery/Redis), queue/retry/checkpoint implementation
(atomic lease claims, exponential backoff, dead
letters, dependency blocking, bounded catch-up),
operations dashboard (GET-only API + `/admin/jobs`
page), and recovery playbooks. Full design in
`implementation_specification.md`; registry in
`job_registry.md`; cadence in
`scheduling_cadence.md`; dashboard in
`operations_dashboard.md`; recovery in
`recovery_playbook.md`; test evidence in
`restart_test_evidence.md`.

Seed run (live, before VM replacement #6): 8
definitions registered (3 paused with exact reasons,
5 active); 70 runs executed across 5 `run-due`
passes, ALL succeeded, 0 stuck, 0 dead letters;
pass 6 steady state (0 created, 0 executed).
Watermarks: system_health 2026-11-05, alert_digest
2026-11-05 (+digest watermark 2026-11-05 PKT after
the fix run), drift_check 2026-11-02, report_qa_audit
2026-11-01. One manual digest run (id 71) verified
the PKT fix live: 89 alerts (82 INFO / 6 WARNING /
1 CRITICAL, all NEW), drift 0 on the latest
drift_check run.

## Tests

- New suite: 26 tests, all passing (pure calendar +
  SQLite runner/handler tests + API tests + scans).
- Full backend suite: 394 passed, 0 failed (368 + 26).
- Ruff check + format clean on all new/changed files.
- Frontend vitest: 11 passed (unchanged).
- ESLint on new/changed frontend files: clean.
- Production build (`next build --webpack`): 24 routes
  (23 + `/admin/jobs`). Pre-existing `tsc --noEmit`
  `LayoutProps` error in untouched `app/layout.tsx`
  does NOT fail the Next build (build typecheck
  passes); left untouched as out of scope.
- Playwright (`playwright.phase25.config.ts`,
  post-recovery run): 6 passed, 0 failed (3 specs ×
  desktop + mobile, 10.7 s, live backend on port 8000
  + `next start` on port 3000 started by the suite
  itself; no stale port-3000 server was running).

## Corrections made during this run (not hidden)

1. **Digest watermark UTC → PKT.** The alert digest
   first used `datetime.now(timezone.utc).date()` for
   its watermark. This project runs on PKT: a digest
   at 01:00 PKT would mislabel same-day alerts. Fixed
   to Asia/Karachi dates for both the watermark and
   the processing-time comparison, with a regression
   test (22:30 UTC = 03:30 PKT next day counts as new).
   Verified live by manual digest run 71.
2. **SQLite `text()` datetime strings.** Raw SQL
   queries on SQLite return datetimes as ISO strings,
   which broke `_as_aware` in the digest handler.
   Fixed to parse ISO strings (PostgreSQL returns real
   datetimes and never takes that branch).
3. **Test setup: catch-up interference.** Two tests
   called `run-due` without a watermark, so the
   30-day lookback materialised extra occurrences.
   Fixed by setting a prior-day watermark in those
   tests (the runner behaved correctly; the tests did
   not account for bounded catch-up).
4. **Drift test baseline math.** Four EXPECTED_COUNTS
   entries are legitimately 0, so an all-empty database
   drifts on 29 tables, not 33. Test fixed to compute
   the nonzero expectation count.

## VM replacement #6 (during this run)

At ~22:53 PKT on 2026-11-05, during Playwright setup,
the VM was replaced: PostgreSQL binaries, cluster and
logs vanished (uptime reset to minutes); home survived
(worktree, venvs, `.env`, backups intact). Recovery
followed `recovery_playbook.md` §1: waited out the
runtime's apt replay lock, reinstalled PostgreSQL,
restarted the cluster, recreated the contract role/DB,
restored backup 2026-11-04T1230-PKT (manifest
verified), migrated to 0021, re-ran all deterministic
phase commits in order (registry, 444 prices, Phase 6
coverage, Phase 7 run-1 + remainders, Phase 8–22
commits), re-registered Phase 25, re-ran `run-due`
to steady state. Re-verified counts below replace the
pre-replacement seed numbers as the authoritative
Phase 25 live state.

Recovery corrections during the re-runs (not hidden;
all temporary patches reverted before committing, no
committed code changed on their account):

1. **Price ingestion needs `--source-key`.** The
   mapped CSV carries empty `source_key` columns, so
   a bare dry-run rejects 444 rows as
   `missing_field`. The recorded Phase 5 command
   (untracked `phase_05_commit_2026-11-04.md`) uses
   `--source-key dps_market_summary_2026-11-03
   --from-date 2026-11-03 --to-date 2026-11-03`;
   with it, dry-run and commit both reproduce 444
   ingested / 13 rejected exactly.
2. **Macro sector ids shifted.** `SECTOR_POWER /
   TEXTILE / EP / BANKS` were hardcoded to the old
   id space (16/8/36/4); the fresh import assigns
   53/45/73/41. The macro commit failed FK-clean
   (nothing written) until a temporary remap; the
   patch was reverted after the run (12/6/1/4/120
   exact). Permanent name-based sector resolution
   is a follow-up, not a Phase 25 change.
3. **News publication-date map still id-keyed.**
   Phase 23's ticker-keying fixed RAG seed documents
   but NOT `PUBLICATION_DATES` / `SEED_SUMMARIES`
   (keys 13/14/15 vs live document ids 7/8/9). The
   first news re-run seeded 3 earnings events with
   NULL dates, which then suppressed the HUBC
   earnings alert as UNKNOWN_DATE (88 alerts, not
   89). Fixed per the Phase 22 precedent: deleted
   the 3 wrong earnings events + 3 links, temporarily
   remapped 13/14/15 → 7/8/9, re-ran news (HUBC
   2026-09-21 known, NML unknown, OGDC 2026-02-23
   known; review 5 pending + 2 scheduled), reverted
   the patch, re-ran alerts (HUBC earnings alert
   created; suppressions STALE 1, UNKNOWN_DATE 1,
   FUTURE_SCHEDULED 2, NO_EVENT_DATE 5, NO_SERIES 3
   all match the record). The third alerts commit
   (idempotency proof, 0 new alerts) added a 9-row
   run group; those 9 redundant run rows were
   deleted to restore the recorded 18 runs (alerts
   stayed 89).
4. **Phase 22 report files regenerated mid-recovery.**
   The reports re-run overwrote 12 committed report
   files with intermediate-state content (3 alerts,
   unknown earnings dates) because it ran before the
   news/alerts fixes. The files were reverted to the
   committed Phase 22 versions, which match the
   fixed DB (HUBC alerts = 4, verified by query).
5. **RAG benchmark history (see counts table).**
   Only the r3 benchmark run was re-created (6/6);
   r1/r2 historical rows were not fabricated.

## Database counts — before → after (live, re-verified)

Before = post-replacement-#6 partial state (backup
restored, migrated to 0021, registry + LEAP re-run,
all later phases still empty). After = full recovery
+ Phase 25 re-seed, re-verified by direct psql counts
and the live jobs API (8 definitions, 71 runs, 0 dead
letters).

| Table | Before | After |
| --- | ---: | ---: |
| companies / securities / sectors | 470 / 470 / 37 | 470 / 470 / 37 |
| registry_evidence (940 DPS + 61 secp_leap) | 1001 | 1001 |
| company_identifiers | 0 | 0 |
| market_prices (one date 2026-11-03, UNVERIFIED) | 0 | 444 |
| financial_documents / statements / line items / opinions | 0 | 3 / 88 / 1316 / 3 |
| technical_calculation_runs / errors / values | 0 | 1 / 124 / 0 |
| fundamental_metric_values / definitions / health / warnings | 0 | 108 / 36 / 24 / 8 |
| sector_metric_profiles (108 + 12 macro) | 108 | 120 |
| valuations | 0 | 51 |
| economic_indicators / exposures / regimes / macro events | 0 | 12 / 6 / 1 / 4 |
| news_sources / aliases / events / event_companies | 0 | 8 / 1376 / 7 / 3 |
| ownership_holdings / actions / adjustment_rules / breadth / liquidity / investor_flows | 0 | 34 / 5 / 4 / 50 / 889 / 0 |
| forecast_targets / snapshots / assessments (all insufficient) | 0 | 48 / 116 / 120 |
| risk definitions / values / flags / controls / checks / stress scenarios / results | 0 | 22 / 81 / 17 / 5 / 7 / 5 / 10 |
| decision_rules / decisions / outcomes | 0 | 1 / 4 / 0 |
| simulated_portfolios / holdings / exclusions / sector allocations / comparisons | 0 | 3 / 7 / 5 / 7 / 3 |
| backtest_strategies / runs (NOT_RUNNABLE) / metrics / ledger / bias / paper_orders | 0 | 5 / 5 / 55 / 13 / 7 / 0 |
| agent_definitions / orchestration runs / tasks / audit logs / evaluations | 0 | 16 / 1 / 6 / 6 / 6 |
| rag_documents / chunks / benchmark cases / benchmark results / access audits | 0 | 3 / 943 / 6 / 6* / 9 |
| screen_definitions / runs / results (241 MATCH) | 0 | 5 / 5 / 1418 |
| alert_rules / preferences / alerts (82 INFO / 6 WARNING / 1 CRITICAL) / deliveries / runs | 0 | 9 / 1 / 89 / 89 / 18 |
| reports (all DRAFT) / figures / sections / exports | 0 | 22 / 541 / 188 / 66 |
| data_sources | 2 | 19 |
| auth_users / auth_tokens / auth_audit_logs (empty by decision) | 0 / 0 / 0 | 0 / 0 / 0 |
| job_definitions (3 paused) / job_runs (all succeeded) / job_checkpoints / job_dead_letters | 0 | 8 / 71 / 5 / 0 |

\* Benchmark results 6, not the recorded 18: the
recorded 18 were 6 each for r1/r2/r3, and r1 (1/6)
and r2 (2/6) were runs of superseded retrieval code.
Re-running current code cannot reproduce those
scores, so only the r3 run was re-created
(`phase19-benchmark-2026-11-04-r3`, 6/6, recall@5
1.0). The 12 historical rows were NOT fabricated.
Every other count above matches the recorded
pre-replacement state exactly.

## Computed vs NOT_CALCULABLE

Phase 25 is an automation phase, not an analysis phase:
no financial output was produced, no input status
changed, and NOT_CALCULABLE does not apply the way it
does in analysis phases. Delivered instead: the job
framework, registry, scheduler, runner, CLI, API,
dashboard, docs, and all tests/scans. Collection jobs
produce nothing by design (paused + stub handlers).

## HBL-pending note (unchanged)

HBL remains pending (CY2025 PDF blocked at the
issuer-site challenge; live-browser download runs
separately, no result yet). Phase 25 touches no
company data; a 4th company later needs no Phase 25
redesign (jobs are company-agnostic; the dashboard
already resolves by ticker).

## Gate judgement + remaining blockers

**PARTIALLY COMPLETE, not COMPLETE:** the acceptance
gate's testable items hold (jobs idempotent and
recoverable — proven by tests AND by the live
replacement recovery; schedules match source cadence;
no paid services or unbounded polling; offline
limitations accurately represented), but the underlying
data remains limited exactly as Phases 4–24 recorded
it (UNVERIFIED inputs, 3-company coverage, abstained
forecasts, WITHHELD decisions, NOT_RUNNABLE backtests,
fallback-only agents, vector retrieval not implemented,
DRAFT-only reports, HBL pending), and the collection
jobs that would widen coverage are paused on the Terms
gate. Forcing COMPLETE would misrepresent those limits.
No new blocker was introduced by Phase 25.

Remaining blockers with unblockers: written PSX
permission evidence (user-owned) → collection jobs
unpause + full-470 verification + new PSX collection;
more trading days (Terms-gated) → technical values,
forecasts, backtests, series risk; HBL PDF via browser
download → 4th company everywhere; verified local
embedding model → vector retrieval; an internal review
decision → first APPROVED report (CLI transition only,
no web approval by design); a parent/user decision →
first live auth account (auth tables intentionally
empty); a real deployment decision → enforced-mode
production proof, backup encryption, dependency audit,
frontend token support, multi-instance rate limiting.
Phase 24 candidate (a) — token-gated report approval —
stays open: it does not belong to the scheduling brief
and was not adopted here.
