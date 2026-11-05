# Phase 30 — Release Checklist and Rollback Plan

## Release identity

- Release: `v0.2.0-handover` (annotated tag on the `phase-30-release`
  branch tip). Handover snapshot, NOT a production release.
- Base: `phase-29-acceptance` `858e914`. Main untouched (`eb6025b`).
- Migration head: `20261104_0024`. No migration in this phase.
- Date: 2026-11-05 (Asia/Karachi).

## Release checklist

### Releasable as-is (this snapshot)

- [x] All 30 phase folders exist under `docs/` with run reports, specs,
      and evidence; every phase status in the handover report carries an
      exact branch + commit reference.
- [x] Backend suite passes (see `run_report.md` for the measured count);
      frontend vitest passes; production build succeeds (webpack).
- [x] Fresh-clone reproducibility proven from origin (see `run_report.md`).
- [x] Backup/restore drill proven (see `run_report.md`): backup manifest
      hashes verified, restore into a scratch database verified on all
      three axes (hashes, row counts, alembic revision).
- [x] Final audit scans pass (execution identifiers 0, write routes 0,
      upload endpoints 0, docker invocations 0, tracked datasets 0,
      tracked secrets 0, PII columns 0 — branch-tip boundary).
- [x] Licence + source inventory reviewed (see
      `licence_and_source_inventory.md`); no paid dependency; no hidden
      cost. Hardware, electricity, and internet are external operating
      expenses, disclosed, never called free.
- [x] README corrected to the true current state (Phase 30 status section
      at the top; Docker wording corrected to the no-Docker decision).
- [x] Operations documented: `ops/README.md`, Phase 28 deployment guide
      and operations handover, Phase 27 incident playbooks, Phase 25 job
      framework docs.
- [x] Rollback plan below is documented and uses only already-proven
      mechanisms (git branch tips, backup/restore scripts).

### Explicitly NOT released (do not treat as done)

- [ ] Merge to `main`. Blocked on: separate user approval + an
      unrelated-histories decision (remote `main` `eb6025b` is README-only
      and shares no history with the phase branches; local `main`
      `214a701` was never pushed). No PR exists.
- [ ] External deployment. Blocked on: a real deployment decision
      (enforced-mode production proof, backup-encryption key management,
      dependency audit with network, frontend token support,
      multi-instance rate limiting). `main` branch is UNPROTECTED
      (verified via GitHub API, 404 "Branch not protected"); enabling
      protection is a recommended owner action before any public-release
      use — not done by this phase.
- [ ] Live auth accounts. Auth tables intentionally 0/0/0; enforced mode
      is fail-closed (401) until the first admin account is created with
      the CLI-only tool — a parent/user decision.
- [ ] Approved or published reports. All 22 reports are DRAFT, 0
      approved, 0 published externally. Approval is a CLI transition
      only, and requires an internal review decision that has not been
      made. Report approval is not token-gated (defect D-12, open).
- [ ] External notifications. No path exists; Phase 21 external consent
      is False. Alerts are in-app only.
- [ ] CI-in-CI. `.github/workflows/ci.yml` triggers only on push/PR to
      `main`/`development`; no Actions runs exist. Unverified.
- [ ] Any quality-status promotion. No permission name exists for it;
      none invented. All inputs keep their recorded status.
- [ ] Any live PSX collection. The 3 collection jobs are PAUSED
      (Terms gate); their handlers are stubs that dead-letter if ever
      dispatched.
- [ ] The HBL Phases 8+ re-runs. Sequenced after Phase 30 (see handover
      report); they need a parent-approved branch strategy (merge or
      cherry-pick of `phase-07-hbl-extraction` code into the phase
      lineage).

## Pre-release verification (all performed this phase; evidence in `run_report.md`)

1. Backend suite + ruff on new/changed files.
2. Frontend vitest + webpack production build.
3. Fresh clone from origin → fresh venv install → backend suite →
   frontend build.
4. Backup (live DB, read-only) → restore into scratch DB →
   three-axis verification → scratch DB dropped, drill dir deleted.
5. Final audit scans over the branch tip.
6. Independent recomputations from live DB rows.
7. Live API smoke (`/health`, registry statistics, acceptance summary,
   observability readiness).
8. Business-count census before/after (unchanged by this phase).

## Rollback plan

This release is a branch snapshot, so rollback is branch-level, never
destructive. No history rewrite, no force-push, no merge is involved.

1. **Code rollback:** check out the previous branch tip
   (`phase-29-acceptance` `858e914`) or delete the `phase-30-release`
   branch and its tag if the snapshot is rejected. Nothing on `main` is
   affected (it was never touched).
2. **Database rollback:** this phase runs no migration and writes no
   business rows, so there is nothing to roll back in the live DB. If a
   later phase's migration must be undone, use `alembic downgrade` to
   the recorded revision, then restore from a verified backup with
   `database/restore.sh` into a scratch database first and
   `verify_restore.sh` before any live decision. Restoring over live is
   refused by `restore.sh` unless `ALLOW_LIVE_RESTORE=1` is set
   explicitly, and only after a verified backup of live exists.
3. **Tag rollback:** delete the tag locally and remotely
   (`git tag -d v0.2.0-handover && git push origin :v0.2.0-handover`)
   if the snapshot is rejected. Tags are never moved: a corrected
   release gets a new tag name.
4. **VM-replacement recovery (proven 7 times):** restart the cluster
   (`pg_ctlcluster 16 main start`; policy-rc.d denies auto-start),
   recreate role + database per `docs/phase-02/DATABASE_SETUP.md`,
   restore backup `2026-11-04T1230-PKT` (manifest SHA verified), migrate
   to head `20261104_0024`, then deterministically re-run, in order:
   registry import → 444-row price commit (with
   `--source-key dps_market_summary_2026-11-03`) → Phase 6 coverage →
   Phase 7 run-1 + remainders → HBL extraction (from the gitignored HBL
   PDF + committed page maps on `phase-07-hbl-extraction`) → Phase 8 →
   9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 →
   22 commits. Resolve all company identity BY TICKER (surrogate ids
   shift across fresh imports; current HUBC 759, NML 864, OGDC 873,
   HBL 747). Temporary id remaps (sector ids, news document ids) must
   be reverted after each use. Do NOT re-fabricate the 12 superseded
   RAG benchmark rows (r1/r2) — the live count is 6 (r3 only).
5. **Incident procedure:** Phase 27 incident playbooks
   (`docs/phase-27/incident_playbooks.md`) + `ops/README.md`. There is
   no external incident contact: the operator is the user. Log via the
   structured logging + correlation-ID system (Phase 27); never log a
   secret (redaction is enforced and tested).

## Known post-release work (not part of this release)

- HBL Phases 8+ re-runs (banking rule: Phase 9 uses the bank
  residual-income model for HBL).
- Permanent surrogate-id fixes (D-04): name-based sector resolution +
  ticker-based news publication-date mapping with fixture tests.
- Token-gated report approval (D-12).
- First live admin account + internal review for the first APPROVED
  report (both are decisions, not code).
- Written PSX permission evidence (user-owned; the single largest
  blocker — see handover report).
- More trading days (Terms-gated) → technical values, forecasts,
  backtests, series risk, evaluated predictions.
- Verified local embedding model → vector retrieval; verified
  local/open-weight LLM → LLM-backed orchestration.
- Share-count data → P/B, P/S, market cap, EV multiples, dividend yield.
- KSE-100 / wider-company expansion (per-company source verification).
