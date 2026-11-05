# PSX Intelligence AI — Developer Guide (Phase 30)

## Layout

```text
frontend/    Next.js 16.4.5 app (App Router) — 27 routes in the production build
backend/     FastAPI app — 24 endpoint files under app/api/v1/endpoints/, services per phase
database/    PostgreSQL 16 infrastructure — migrations/, backup.sh, restore.sh, verify_restore.sh
scripts/     One CLI per phase (dry-run default, --commit) + ops helpers
ops/         start/stop/status/healthcheck/update/install/prune_backups + systemd units
docs/        phase-01 … phase-30 run reports, specs, evidence; development/ registers
storage/     gitignored file store (backups/, financial_reports/, manifests/)
```

## Branch and commit discipline (non-negotiable)

- One branch per phase work; base branch tips are NEVER moved.
- No merge to `main` without a separate user approval. Remote `main`
  (`eb6025b`, README-only) and local `main` (`214a701`) have unrelated
  histories; no PR exists. Never force-push, never rewrite history.
- Push only verified content; verify the remote SHA equals the local
  tip and record old vs new SHAs in the run report.
- Coordinators stop after their report. Register files
  (`docs/development/PHASE_COMPLETION_REGISTER.md`,
  `PROJECT_EXECUTION_STATE.md`, `MASTER_EXECUTION_LOG.md`) are
  consolidated by the parent only — never edited by a phase coordinator.
- Tags are never moved: a corrected release gets a new tag name.

## Database contract (docs/phase-02/DATABASE_SETUP.md)

- Database `psx_intelligence`, OWNER postgres; app role `psx_app`
  (LOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE).
- The role password lives ONLY in `database/.env` (gitignored, mode
  0600). Never print it, log it, or commit it. Create the role via a
  SQL file built from `.env` without printing the password, then delete
  the file.
- After `set -a; source database/.env`, superuser commands must clear
  env: `env -u PGUSER -u PGPASSWORD -u PGDATABASE sudo -u postgres psql`.
- Migrations live in `database/migrations/`; run alembic from
  `database/` with `database/.venv/bin/alembic`. Migration files live
  PER BRANCH — always verify migration state from the LATEST branch
  checkout, not an older one (an older checkout reports "Can't locate
  revision" for newer heads; that is a checkout artifact, not a DB
  problem). Current head: `20261104_0024`.
- Cluster start after a VM reboot: `pg_ctlcluster 16 main start`
  (policy-rc.d denies auto-start).

## The surrogate-id rule (read this before touching any seed)

Company ids are SURROGATE and SHIFT across fresh imports. Original
import: HUBC 289, NML 394, OGDC 403, HBL 277. Current live DB: HUBC 759,
NML 864, OGDC 873, HBL 747. Resolve ALL company identity BY TICKER,
never by hardcoded company id. The same trap applies to sector ids
(macro sector ids shifted 16/8/36/4 → 53/45/73/41) and news document
ids (13/14/15 → 7/8/9 in recovery #6, → 4/5/6 in recovery #7).
Permanent fixes (name-based sector resolution, ticker-based news
publication-date mapping) are defect D-04, still open. If you re-run an
earlier phase seed, check its id constants against the live DB first,
patch temporarily in your worktree only, and revert before committing
— no committed code may change on that account.

## Testing

```bash
cd backend && .venv/bin/python -m pytest        # full backend suite (448 at Phase 29 + Phase 30 release tests)
cd backend && .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
cd frontend && npm run test                     # vitest (11)
cd frontend && npm run build -- --webpack       # production build (27 routes; Turbopack fails on the
                                                # symlinked node_modules worktree artifact — pre-existing,
                                                # not a code defect)
```

- Playwright suites live per phase (`frontend/playwright.phaseNN.config.ts`;
  the Phase 2 smoke config is untracked by design and deliberately NOT
  committed). Kill port-3000 servers before suite runs: Playwright's
  `reuseExistingServer` silently reuses a stale manually started
  `next start` and masks fixes.
- Backend CORS allows only port-3000 origins; serving the frontend on
  any other port blocks API calls.
- Every phase CLI is dry-run by default with `--commit`; every
  `--commit` run must prove idempotency with a second `--commit`
  writing 0 new rows.
- Never zero-fill, never estimate, never present a NOT_CALCULABLE
  output as a number, never use a future observation or a statement
  published after the analysis date (no look-ahead).
- Never promote a quality status without a recorded human approval
  gate (none granted). New outputs carry their inputs' status, never
  higher.

## Adding a new phase (checklist)

1. New branch from the latest tip; base tip unmoved.
2. Read the playbook brief lines for that phase; ignore
   phase-transition boilerplate (no auto-start, no register edits).
3. Services + CLI + GET-only API following the Phase 8–29 patterns;
   hand-calculated test cases for every computable output; tests
   proving NOT_CALCULABLE outputs stay empty with reasons.
4. Dry-run, then `--commit`, then second `--commit` (0 new rows).
5. Independent audit: hand-recompute headline figures from live DB
   rows, never from prior reports.
6. Docs: implementation specification + run report under
   `docs/phase-NN/`; record defects with exact unblockers.
7. Commit (explicit `git add` only; no CSVs/PDFs/`.env`/venv/
   test-results), push, verify remote SHA = local tip, report old vs
   new SHAs, base tips unmoved, main untouched, DB counts
   before/after. Stop after the report.

## Recovery recipe (proven 7 times; full detail in phase run reports)

Restart cluster → recreate role + database → restore backup
`2026-11-04T1230-PKT` (manifest SHA verified) → migrate to head →
deterministically re-run, in order: registry import → 444-row price
commit (with `--source-key dps_market_summary_2026-11-03`; a bare run
rejects the 444 as missing_field) → Phase 6 coverage → Phase 7 run-1 +
remainders → HBL extraction (gitignored HBL PDF + committed page maps
on `phase-07-hbl-extraction`) → Phase 8 → 9 → 10 → 11 → 12 → 13 → 14 →
15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 commits. Do NOT re-fabricate the
12 superseded RAG benchmark rows (r1/r2) — the live count is 6 (r3
only). After recovery, re-verify every recorded count before new work.

## Hard stops (violating any fails the run)

No new PSX collection without written permission evidence; no
VERIFIED/PARTIALLY_VERIFIED promotion; no broker/order/execution path;
no Docker; no merge to main; no force-push; no CSV/PDF commits; no
credentials printed, logged, or committed; no live auth accounts
without a parent/user decision; no DPS downloads (discovery only); no
PSX financials portal use; no paid dependency; no misrepresentation.
