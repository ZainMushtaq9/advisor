# Phase 25 — Restart / interruption test evidence

## Automated tests (backend suite, SQLite, no network)

File: `backend/tests/test_jobs_phase25.py` — 26 tests,
all passing; full backend suite 394 passed (368 + 26).
Ruff check + format clean on all new/changed files.

| Evidence | Test |
|---|---|
| Idempotency: same occurrence key replays stored result, handler called once | test_idempotent_replay_calls_handler_once |
| Overlap prevention: second claim of a claimed run loses | test_claim_overlap_second_runner_loses |
| Retry with exponential backoff (60s after attempt 1), then dead-letter | test_retry_backoff_then_dead_letter |
| Backoff respected: run-due does not retry before next_attempt_at | test_retry_backoff_then_dead_letter |
| Collection stubs dead-letter immediately, no retries spent | test_non_retryable_collection_stub_dead_letters_immediately |
| Unknown handler dead-letters | test_unknown_handler_dead_letters |
| Lease reclaim after simulated crash; live lease untouched | test_lease_reclaim_after_crash_and_live_lease_untouched |
| Checkpoint resume: steps 1–2 not redone after mid-run failure | test_checkpoint_resume_after_mid_run_failure |
| Cancel queued → cancelled + watermark advances; running cannot be cancelled | test_cancel_rules_and_watermark |
| Dependency gate: downstream blocked, then unblocked after upstream succeeds | test_dependency_gate_blocks_then_unblocks |
| Dependency dead keeps dependent blocked | test_dependency_dead_keeps_dependent_blocked |
| Paused job refused without creating a run | test_paused_job_refused_without_creating_a_run |
| Dead-letter retry creates fresh run with `:retry-N` key, letter resolved | test_retry_dead_letter_creates_fresh_run |
| Bounded catch-up: 7 oldest occurrences per pass; watermark advances | test_run_due_materialises_bounded_catchup_and_executes |
| Schedule evaluator: weekday post-close, weekly, monthly, quarterly, annual | test_daily_weekdays_only, test_weekly_monthly_quarterly_annual |
| Nonexistent days skipped, never moved (31 Feb, 29 Feb non-leap) | test_nonexistent_day_is_skipped_never_moved |
| Manual jobs never due; new-job lookback 30 days | test_manual_never_due_and_catchup_capped |
| Drift check reports differences but succeeds (finding, not failure) | test_drift_check_reports_differences_but_succeeds |
| Alert digest baseline + watermark + PKT boundary case | test_alert_digest_baseline_and_watermark |
| Retention purge dry-run then confirm (only old rows deleted) | test_retention_purge_dry_run_then_confirm |
| Report QA audit asserts no publish column, published_externally 0 | test_report_qa_audit_asserts_no_publish_path |
| Jobs API is GET-only | test_jobs_router_is_get_only |
| Jobs API endpoints (definitions/runs/detail/checkpoints/dead-letters/status) | test_jobs_api_endpoints |
| No execution identifiers in new code | test_no_execution_identifiers_in_new_code |

## Live restart evidence (this run)

- Pre-replacement live seed run: 70 runs, all
  succeeded, 0 stuck, 0 dead letters, pass 6 steady
  state (0 created, 0 executed). Paused definitions
  exactly the 3 collection jobs with reasons.
- VM replacement #6 (2026-11-05, ~22:53 PKT) destroyed
  the PostgreSQL installation mid-run (during the
  Playwright setup). Recovery followed
  recovery_playbook.md §1 exactly: reinstall,
  restore backup 2026-11-04T1230-PKT, migrate to
  0021, re-run all deterministic phase commits in
  order, re-register Phase 25, re-run run-due to
  steady state. Final re-verified counts are in
  run_report.md.
- Live interruption proof from the seed run itself:
  the 70-run catch-up executed across 5 passes with
  no duplicate runs (idempotency keys unique) and no
  lost occurrences (watermarks advanced exactly to
  the latest processed date per job).
