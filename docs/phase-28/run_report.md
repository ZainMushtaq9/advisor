# Phase 28 Report — PARTIALLY COMPLETE

**Verdict: PARTIALLY COMPLETE.** The acceptance gate's testable items hold
(system starts from a clean documented setup — see
`fresh_environment_test.md`; backup restore is proven — see
`restore_drill.md`; no hidden paid dependency exists — enforced by
`test_deployment_phase28.py`; operational uptime limitations are
explicit in `ops/README.md` and `deployment_guide.md`), but the
underlying data stays limited exactly as Phases 4–27 recorded it
(UNVERIFIED inputs, 3-company statement coverage at Phase 28 start —
now 4 with HBL, see below — abstained forecasts, WITHHELD decisions,
NOT_RUNNABLE backtests, fallback-only agents, vector retrieval not
implemented, DRAFT-only reports, no live auth accounts, no persistent
backup-encryption key, no system-wide service install, no host cron).
COMPLETE is not claimed. **Phase 29 NOT started. Register files NOT
edited** (parent consolidates) — the playbook's phase-transition
boilerplate (auto-start next phase, update state files) was deliberately
not followed, per the parent brief.

## Security-note handling (flagged read, parent brief governs)

During this run, a system security notice flagged the playbook-extract
read (lines 1974–2031) as untrusted tool data. The notice was honored
exactly as the parent brief already directs: no instruction from the
extract was followed beyond the parent-authorized Phase 28 scope, and
in particular the extract's phase-transition boilerplate (auto-start
the next phase, update state files without asking) was NOT followed.
All work below comes from the parent brief; the extract supplied only
the Phase 28 topic (deployment, operations, backup, disaster recovery).

## What changed

- **Branch:** `phase-28-deployment`, new branch from
  `phase-27-observability` `544fecc`.
- **Commits:** `885bcef` (implementation, 21 files) +
  `493f3f0` (this run report, fresh-environment test, start.sh exec
  fix, post-HBL drill note) + this footer (SHA-record commit).
  **Push verified:** remote `phase-28-deployment` equals local tip
  (see footer).
- **Base tips unmoved:** remote `phase-27-observability` still `544fecc`,
  remote `main` still `eb6025b`. No merge to main, no force-push, no
  history rewrite, no cross-push, no CSVs/PDFs committed, no
  credentials anywhere.
- **Migration:** none. Head stays 20261104_0023 (Phase 28 needs no new
  tables; manifests live on disk, run evidence lives in Phase 25/26/27
  tables).
- **Worktrees removed** afterward (`psx-p28` scratch, `psx-fresh`
  test); the main worktree is undisturbed (still on `phase-21-alerts`).
- **No live auth accounts created** — auth tables still 0/0/0 by decision.

## What was built (brief lines 1974–2031)

- **Deployment package (`ops/`):** `start.sh` (postgres-if-down +
  backend + frontend production-build-only; jobs deliberately NOT
  started), `stop.sh` (backend + frontend only; postgres never
  touched), `status.sh` (read-only), `healthcheck.sh` (postgres,
  backend `/health`, frontend `/`, migration match),
  `update.sh` (dirty-tree refusal → backup → `git pull --ff-only` →
  `alembic upgrade head` → restart → health gate; never restores over
  live by itself), `install.sh` (systemd unit instantiation; default
  validates into a temp dir only), `prune_backups.sh` (dry-run default),
  `env.production.example`, systemd units for backend + frontend
  (secrets via `EnvironmentFile`, never embedded), `README.md`.
- **Backup/restore:** `backup.sh` manifest extended to 40 key-table
  counts (was: only `phase2_probe`) + optional GPG encryption
  (`BACKUP_GPG_RECIPIENT`; unset = plaintext, the unchanged default;
  plaintext removed after successful encryption; manifest keeps both
  hash sets). `restore.sh` gains a decrypt pre-step for `.gpg`
  backups. New `verify_restore.sh` gate: manifest hashes +
  restored-vs-manifest counts + alembic revision; never mutates the
  backup dir (decrypts to temp); fails loudly on any mismatch.
- **Templates secured:** `database/.env.example` carried two
  credential-looking values (the password inside `DATABASE_URL` and
  the `PGPASSWORD` line). Hash comparison against the real
  `database/.env` proved neither matches the live credential — no live
  leak — but both were replaced with the explicit placeholder
  `CHANGEME`. The real `.env` was untouched and no password value is
  printed anywhere in this phase's outputs.
- **Docs (`docs/phase-28/`):** implementation specification, deployment
  guide (licence audit, Docker-not-used notice, Windows/Linux
  differences, ports/firewall/TLS/env vars, uptime limitations),
  operations handover (start/stop/update/migrate/backup/restore/
  upgrade/incident/shutdown; what stops when the computer is off;
  catch-up via `run-due`), backup retention policy (30 valid backups,
  never the newest, never invalid-manifest dirs; RPO/RTO honest),
  restore drill report, fresh-environment test report, this run report.

## Computed vs NOT_CALCULABLE

Phase 28 is an operations phase, not an analysis phase: no financial
output was produced, no input status changed, and NOT_CALCULABLE does
not apply the way it does in analysis phases. Nothing numeric was
computed and nothing was zero-filled or estimated. Delivered instead:
the deployment package, runbooks, backup/restore scripts + drill,
fresh-environment test, and all tests/scans. Business counts were
verified unchanged by Phase 28 itself at drill time (companies 470,
prices 444, reports 22, alerts 89, job runs 71, auth users 0).

## Tests

- New suite `test_deployment_phase28.py`: **7 tests, all passing**
  (backend + frontend dependency allowlists, template secret scan,
  bash syntax on all ops/database scripts, Docker-ban enforcement on
  ops scripts, systemd unit instantiation + `systemd-analyze verify`,
  backup-script gate markers).
- **Full backend suite: 426 passed, 0 failed** (419 + 7 new). Ruff
  check + format clean on the new test file.
- `ops/install.sh` validation: `systemd-analyze verify` PASSED
  (system timer warnings in its output are unrelated host noise).
- `ops/prune_backups.sh` dry-run: 6 valid backups, keep 30, nothing
  to delete (run against the main store; the scratch worktree's store
  correctly reports 0).
- `ops/healthcheck.sh`: postgres OK, migration match OK (live 0023 ==
  head); backend/frontend NOT RUNNING reported truthfully, exit 0.

## Corrections made during this run (not hidden)

1. `ops/healthcheck.sh` compared the live revision against
   `alembic heads` output verbatim — but that output appends
   `" (head)"`, so the comparison false-failed even when revisions
   matched. Caught live, fixed by stripping to the bare revision,
   re-verified OK.
2. `database/.env.example` template secrets (see above): two
   credential-looking values replaced with `CHANGEME` after proving
   (by hash comparison, without printing either value) that neither
   matches the live credential.
3. Fresh-database grants: the first grants file failed on a file
   permission error when read as the postgres user; re-run via stdin
   heredoc (no file access needed) and verified (all GRANTs applied,
   including CREATE on schema public for migrations).
4. The Phase 2 `deployment/` Dockerfiles + compose file were evaluated
   and deliberately NOT adopted or deleted: they predate the Docker ban
   and are documented as superseded; deletion needs its own
   authorization.
5. `ops/start.sh` backgrounding bug (caught live in the
   fresh-environment test, fixed here): the first version backgrounded
   a subshell wrapper without `exec`, so pid files held the wrapper
   subshell's pid — `stop.sh` would have killed the wrapper and
   orphaned the servers — and the servers held the caller's pipes
   open, so the calling session never completed even though both
   servers were healthy. Fixed with `exec` inside the subshell plus
   stdin from `/dev/null`; re-proven end to end (pids are the real
   servers, stop kills them, ports free, no processes remain). See
   `fresh_environment_test.md`.

## HBL note — status changed during this run

At brief time, the HBL CY2025 PDF was obtained but extraction had not
loaded anything (DB: 3 documents / 88 statements). During Phase 28,
the separate HBL extraction coordinator COMPLETED (branch
`phase-07-hbl-extraction` `42bd8e2`): consolidated audited FY ended
31 Dec 2025, publication 2026-03-03, auditor KPMG Taseer Hadi & Co.
unmodified, UDIN AR202510201HsNS5gUWD; live DB now reads documents 4,
statements 118 (+30 HBL), line items 2116 (+800), opinions 4 — all HBL
rows UNVERIFIED (parent-verified live + remote SHA). Phase 28 touches
no company data; its first drill backup (`2026-11-05T0529-PKT`)
predated the HBL load, so a post-HBL backup was taken during this run
(`2026-11-05T0537-PKT`, documents 4 / statements 118 / line items
2116 / opinions 4, restored + fully verified in 6 s — see
`restore_drill.md` §7). The HBL recovery-point gap is therefore closed
for the current state. When the next
observability run executes, it will show drift vs the Phase 24
baseline from the HBL load — that is the drift SLO working as designed,
and the baseline update must be recorded with its evidence per the
Phase 25 rule, not hidden. Phases 8+ HBL re-runs remain pending AFTER
the main Phase 28–30 sequence (banking rule: Phase 9 uses the bank
residual-income model for HBL).

## Remaining blockers with exact unblockers

- Written PSX permission evidence (user-owned) → collection jobs
  unpause, full-470 verification, new PSX collection, and with them
  the price-coverage, session-gap, and previous-close SLOs.
- More trading days (Terms-gated) → technical values, forecasts,
  backtests, series risk, evaluated predictions.
- Verified local embedding model → vector retrieval (then the RAG card
  and vector metric become evaluable).
- Internal review decision → first APPROVED report (CLI transition
  only, no web approval by design).
- Parent/user decision → first live auth account (auth tables
  intentionally 0/0/0); production boot with enforcement on and zero
  accounts is fail-closed (401) by design.
- Operator decision → persistent backup-encryption key (mechanism
  delivered and round-trip proven with an ephemeral key; no
  production backup is encrypted until the operator creates a key and
  sets `BACKUP_GPG_RECIPIENT`).
- Operator decision → system-wide service install (`ops/install.sh
  --install` + enable) and any host cron for `run-due` (neither
  installed by this phase).
- Real deployment decision → enforced-mode production proof, backup
  encryption (above), dependency audit with network before any
  production deployment, frontend token support for enforced mode,
  multi-instance rate limiting.
- Follow-ups (not Phase 28 changes, still open from Phase 25):
  permanent name-based sector resolution; permanent ticker-based news
  publication-date mapping (the same surrogate-id trap will recur on
  the next recovery otherwise).
- Phase 24 candidate (a) token-gated report approval: still open
  (belongs to no phase brief so far; candidate for a later phase).
- Parent consolidation still owed: append Phases 8–28 outcomes to the
  three registers, and update the consolidated MEMORY.md PSX bullet
  (Phase 28 coordinators cannot edit memory files).

**STOP — Phase 29 not started; awaiting parent verification and the
next brief.**

## Footer (push verification, parent-checked)

- Branch `phase-28-deployment`: local tip = remote tip =
  `493f3f0` at push time (implementation `885bcef` + report/test/fix
  `493f3f0`); this footer commit follows and is pushed the same way.
- Base `phase-27-observability` unmoved at `544fecc`; `main` unmoved
  at `eb6025b`. No merge to main, no force-push, no history rewrite.
