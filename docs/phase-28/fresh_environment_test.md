# Phase 28 — Fresh-Environment Deployment Test (measured 2026-11-05)

Acceptance gate item: "system starts from clean documented setup."
This test follows `deployment_guide.md`'s clean-setup procedure
verbatim, except where noted, against a scratch checkout and a scratch
database. Nothing in it touches the live database or the live file
store (the live store was only READ by the backup drill, never written
by this test — the fresh backup in `restore_drill.md` is the separate
operational artifact).

## Procedure and measurements

1. **Scratch checkout:** `git worktree add --detach ~/workspace/psx-fresh
   885bcef` (the Phase 28 implementation commit). Detached on purpose:
   the test proves the committed content, not uncommitted edits.
2. **Scratch database:** `psx_intelligence_fresh_test`, created by the
   superuser, `psx_app` granted CONNECT + USAGE/CREATE on schema public
   + table/sequence privileges + default privileges (the
   `DATABASE_SETUP.md` contract). One correction during setup: the
   first grants file failed on a file-permission error when read as
   the postgres user; re-run via stdin heredoc, all GRANTs applied.
3. **Scratch environment file:** `database/.env` built programmatically
   from the live `.env`'s password (never printed) with `PGDATABASE`
   rewritten to the fresh database. Mode 0600. Deleted with the
   worktree afterward.
4. **Fresh installs (real, not symlinked):** backend venv + pip install
   from `requirements.txt`: 45 s. Database venv + pip install: included
   in the same 45 s. Frontend `npm install`: 15 s (488 packages).
5. **Migration:** `alembic upgrade head` from the fresh checkout: 2 s,
   ending at `20261104_0023 (head)` (the 0020→0021→0022→0023 tail shown
   in the log; the full chain from base ran clean).
6. **Frontend production build:** `npm run build` (plain, Turbopack —
   this checkout has a real `node_modules`, not a symlinked one, so
   the worktree Turbopack caveat does not apply): 24 s, `.next` produced.
7. **Start:** `ops/start.sh` on production ports (8000/3000, verified
   free first): backend + frontend up, health summary all OK,
   migrations OK (live fresh revision == head). First attempt: 7 s to
   healthy after the fix below (see §Bug found).
8. **Smoke on the EMPTY database (truthful zeros, never faked):**
   - `GET /health` → `{"status":"ok","service":"psx-intelligence-ai"}`.
   - `GET /api/v1/registry/statistics` → companies 0, securities 0,
     sectors 0, evidence_rows 0, with the note "Counts are live
     database counts. Zero means the registry is empty, not that the
     market is empty."
   - `GET /api/v1/observability/readiness` → database available,
     reachable true, migration_head 20261104_0023, migration_expected
     20261104_0023, migration_matches true, ready true,
     auth_enforcement off (fresh env has no enforcement set — correct
     default for a fresh setup; production requires `on`).
   - `GET /` (frontend) → HTTP 200.
   - `ops/healthcheck.sh` from the fresh checkout → postgres OK,
     backend OK, frontend OK, migrations OK, exit 0.
9. **Stop:** `ops/stop.sh` → both servers stopped by pid, ports free,
   no server processes remain. PostgreSQL left running on purpose
   (shared system service).
10. **Cleanup:** fresh worktree removed, fresh database dropped, temp
    run dirs removed. No trace of the test remains except this report.

## Bug found by this test (fixed, not hidden)

The first `start.sh` backgrounded a subshell wrapper without `exec`:
pid files held the wrapper subshell's pid (so `stop.sh` would have
killed the wrapper and orphaned the servers), and the servers held the
caller's pipes open, so the calling session never completed even
though both servers were healthy (diagnosed from the service logs +
`ps`: servers up, `/health` 200, yet the session hung). Fixed with
`exec` inside the subshell plus stdin from `/dev/null`; the full
start → smoke → healthcheck → stop cycle was then re-proven in 7 s
with pids verified as the real servers (`uvicorn`, `next-server`) and
a clean stop. The fix is committed in this phase (same branch, second
commit); the fresh worktree tested the fixed script copied from this
file, and the file has not changed since that copy.

## Result for the acceptance gate

"System starts from clean documented setup" — PROVEN for the
documented Linux path (fresh checkout + fresh database + fresh
installs + migrate + build + start + smoke + stop + cleanup). What
this test does NOT prove: Windows setup (documented, not implemented —
Windows is dev-only for this project), systemd installation (validated
into a temp dir only — installing is an operator decision), and any
host cron for `run-due` (not installed by this phase).
