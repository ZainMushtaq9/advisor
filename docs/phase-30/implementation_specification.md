# Phase 30 — Implementation Specification

## Scope (playbook lines 2094–2157 + final handover section)

Phase 30 is release, documentation, governance and operations handover. It
produces a versioned, documented, auditable release snapshot and hands over
a maintainable system with clear limitations and operating procedures. It is
NOT a production launch: nothing in this phase merges to `main`, deploys
externally, creates live accounts, approves a report, publishes a report, or
sends an external notification. Those remain separate decisions (see
`handover_report.md`, section "Pending decisions").

The playbook's phase-transition boilerplate ("update all state files, then
start the next phase automatically") is deliberately NOT followed: the parent
brief governs, this phase stops after its report, and the parent consolidates
the three register files (`PHASE_COMPLETION_REGISTER.md`,
`PROJECT_EXECUTION_STATE.md`, `MASTER_EXECUTION_LOG.md`). There is no
Phase 31.

## What this phase builds

| Item | Location | Notes |
|---|---|---|
| Final system acceptance + handover report | `docs/phase-30/handover_report.md` | Six-way separation: IMPLEMENTED / VERIFIED / PARTIALLY VERIFIED / UNAVAILABLE / BLOCKED / PLANNED. Carries the Phase 29 gate table verbatim; upgrades no verdict; claims no human sign-off. |
| Release checklist + rollback plan | `docs/phase-30/release_checklist.md` | What is releasable as-is, what is explicitly NOT released, rollback steps. |
| Licence + source inventory | `docs/phase-30/licence_and_source_inventory.md` | Software licences (backend pins + frontend deps) and data-source verdicts. |
| Documentation index | `docs/phase-30/documentation_index.md` | Maps architecture, API, schema, methodology, data sources, operations, troubleshooting, security, backup/restore, user guide, developer guide to existing docs; names the gaps. |
| Run report (this phase's evidence) | `docs/phase-30/run_report.md` | Fresh-clone reproducibility test, backup/restore drill, final audit scans, independent recomputations, live API smoke, gate judgement. |
| Release test | `backend/tests/test_release_phase30.py` | Guards the handover doc's required sections, the changelog entry, and the README status section. |
| README status correction | `README.md` (top section) | The Phase 2-era framing ("Phase 2 (this foundation)… No data ingestion…") was stale; a Phase 30 status section now states the true current state. Docker wording corrected to the user decision: Docker is NOT used anywhere. |
| Changelog entry | `CHANGELOG.md` | `[0.2.0-handover]` entry dated 2026-11-05. |
| Version tag | `v0.2.0-handover` (annotated) | Points at the Phase 30 branch tip. A handover snapshot, NOT a production release; annotated as such. First tag on this repository (no prior tags existed). |

## What this phase does NOT build

- No new migration (head stays `20261104_0024`). No new API routes, no new
  tables, no new business rows. Phase 30 writes no financial, registry,
  price, statement, decision, portfolio, backtest, RAG, screen, alert,
  report, job, evaluation, observability, acceptance, or auth row.
- No merge to `main` (remote `main` stays `eb6025b`, README-only, unrelated
  history; local `main` `214a701` never pushed). No PR exists.
- No live auth accounts (auth tables stay 0/0/0 by decision).
- No HBL re-runs (Phases 8+ HBL batch is sequenced AFTER Phase 30; see
  handover report). HBL statements stay as loaded by
  `phase-07-hbl-extraction` (`42bd8e2`).
- No fix for the open follow-ups D-04 (permanent surrogate-id resolution)
  or D-12 (token-gated report approval): neither belongs to the Phase 30
  brief; both stay open and are recorded in the handover.
- No branch-protection change: `main` is verified UNPROTECTED (GitHub API
  returns 404 "Branch not protected") and protection is recorded as a
  recommended owner action before any public-release use — changing repo
  settings is outside this phase's authority.

## Design rules carried forward

- Identity by ticker, never by hardcoded company id (surrogate ids shift
  across fresh imports: current HUBC 759, NML 864, OGDC 873, HBL 747).
- No VERIFIED/PARTIALLY_VERIFIED promotion of any row (H1: VERIFIED needs
  ≥2 distinct agreeing sources incl. one official; the Phase 10 macro
  VERIFIED rows rest on documented cross-publisher SBP/PBS agreement, not
  on second evidence rows in the DB — see handover report).
- No broker/order/execution path of any kind; no real trades, ever.
- No Docker anywhere (user decision); enforced by test scan.
- CSVs and downloaded PDFs are NEVER committed (gitignored:
  `storage/financial_reports/*`, price/registry CSVs). Credentials are
  NEVER printed, logged, or committed; the role password lives only in
  `database/.env` (gitignored, mode 0600).
- Push only verified content; verify remote SHA equals local tip.
- Examples in docs use stored/derived values with provenance; no PSX
  snapshot or private disclosure is published in the repository.

## Verification plan (all measured, none assumed)

1. Backend suite in the Phase 30 worktree (448 Phase 29 tests + new
   release tests); ruff check + format clean on new/changed files.
2. Frontend vitest + production build (webpack; Turbopack fails on the
   symlinked `node_modules` worktree artifact — pre-existing, not a code
   defect, same note as Phases 23–29).
3. Fresh-clone reproducibility: `git clone --branch phase-30-release`
   from origin into a scratch directory, fresh backend venv,
   `pip install -r backend/requirements.txt`, full backend suite, fresh
   frontend install + webpack build.
4. Backup/restore drill: `database/backup.sh` (live DB, read-only) into a
   scratch store, manifest hash check, `database/restore.sh` into a
   scratch database (never live), `database/verify_restore.sh` three-axis
   gate (hashes, all manifest row counts, alembic revision). Scratch
   database dropped and drill directory deleted afterwards.
5. Final audit scans over the branch tip: execution identifiers 0,
   dangerous constructs 0, write routes 0, upload endpoints 0, docker
   invocations 0, tracked datasets 0, tracked secrets 0, PII columns 0
   (same boundary as Phase 29: branch tips, not every historical commit).
6. Independent recomputations from live DB rows (not from prior reports):
   HUBC gross margin, HUBC trailing P/E, OGDC trailing P/E, breadth
   coverage, volume median, top-10 share, HBL SFP identity both years,
   report census, alert totals, decision completeness.
7. Live API smoke (uvicorn, live DB): `/health`, registry statistics,
   acceptance summary, observability readiness.
8. Live count census across all phase tables (before/after: Phase 30
   writes no business rows, so every business count must be unchanged).

## Release identity

- Branch: `phase-30-release`, from `phase-29-acceptance` `858e914`.
- Tag: `v0.2.0-handover` (annotated; first tag on the repository).
- Migration head: `20261104_0024` (unchanged by this phase).
- System verdict: PARTIALLY COMPLETE (Phases 1–3 COMPLETE, Phases 4–29
  PARTIALLY COMPLETE, Phase 30 per its own gate judgement in
  `run_report.md`). The playbook rule is honoured literally: COMPLETE is
  claimed only for features that passed.
