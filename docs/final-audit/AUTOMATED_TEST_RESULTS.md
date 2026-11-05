# Automated Test Results — PSX Intelligence AI (Independent Audit)

**Audit baseline:** branch `phase-30-release`, commit
`8937338` (tag `v0.2.0-handover` peels to `6b1ff9f`, one commit
before the tip; the tip itself is the parent consolidation #2 docs
commit, which changes no code).
**Audit date:** 2026-11-05 (Asia/Karachi).
**Environment:** fresh clone of `phase-30-release` at `8937338`
into `~/workspace/psx-audit-fresh` (deleted after the audit only if
the parent so directs; left in place at report time for re-checks),
fresh Python venv, fresh `npm install`. Python 3.12.3, Ubuntu
24.04.5 LTS, Next.js 16.4.5, React 19.3.0.
**Rule applied:** counts below are from test runs executed BY THIS
AUDIT on the audited commit. No prior-branch count is reused without
re-execution. No test was weakened, skipped by edit, or re-run with
reduced assertions to force a pass.

## 1. Backend pytest (fresh clone, fresh venv)

Command (from `psx-audit-fresh/backend`, venv `.venv`):

```
.venv/bin/python -m pytest tests/ -q
```

| Run | Result |
|---|---|
| First run (venv named `.venv-fresh`, no `node_modules`) | **452 passed, 1 failed, 5 warnings** in 25.82 s |
| Second run (standard layout: `.venv` + `node_modules` installed) | **453 passed, 5 warnings** in 22.84 s |

**The single first-run failure, investigated (not smoothed over):**

- Test: `tests/test_deployment_phase28.py::
  test_systemd_units_instantiate_and_validate`.
- Failure: `ops/install.sh` runs `systemd-analyze verify` on the
  generated units, which checks that `ExecStart` binaries exist.
  The fresh clone used a non-standard venv name (`.venv-fresh`)
  and had no `frontend/node_modules`, so verify failed with
  "`backend/.venv/bin/uvicorn` is not executable: No such file or
  directory" and the same for `frontend/node_modules/.bin/next`.
- After creating the standard layout (real `.venv` + `npm install`),
  the same test passed (1 passed, 0.14 s) and the full suite
  reached **453 passed**.
- **Conclusion: the Phase 30 claim of "453 passed" is REPRODUCED.**
  The first-run failure is a test-environment coupling finding
  (LOW): the deployment test fails in any checkout that does not
  use the exact `.venv` / `node_modules` layout. It is not a code
  defect, but it makes the suite layout-sensitive. The timer
  warnings in `systemd-analyze` output (`motd-news.timer`,
  `apt-daily.timer` "lacks value setting") are host noise, as Phase
  28 already documented; they do not fail the test once the
  binaries exist.

**Warnings (5, unchanged from Phase 30):** SQLAlchemy SQLite
`DeprecationWarning` (default datetime adapter), `fitz` API
`FutureWarning` (use `import pymupdf`), Starlette/httpx
deprecation in TestClient, plus two of the same class. None is a
failure; the `fitz` warning corroborates that PyMuPDF 2.1 is the
installed version (see licensing audit).

**Ruff:** `ruff check app services` → **All checks passed** (fresh
clone, standard venv).

**Test isolation note (verified in `backend/tests/conftest.py`):**
"No test ever touches a real PostgreSQL instance or any network
service." Fixtures build a fresh app with `DATABASE_URL` unset or
fake. The backend suite therefore does NOT prove live-database
behavior; that is covered separately by the scratch-database
reproduction and the runtime audit.

**Suite composition (31 test files):** acceptance (Phase 29),
alerts (21), auth (24), backtesting (17), decision engine (15),
deployment (28), endpoints, errors/config, evaluation (26),
financial statements (07), forecasting (13), fundamental analysis
(08), indicators API, jobs (25), macro (10), market API, market
data, news events (11), observability (27), orchestration (18),
ownership actions (12), portfolio construction (16), RAG (19),
registry, release (30), reports (22), risk analytics (14),
screener (20), technical indicators, valuation (09).

## 2. Frontend vitest (fresh clone, fresh `npm install`)

Command (from `psx-audit-fresh/frontend`):

```
npx vitest run
```

Result: **Tests 11 passed (11)**, 3 files, 3.34 s. Matches the
Phase 30 claim (11 passed).

## 3. Frontend production build (fresh clone)

Command:

```
npx next build --webpack
```

Result: **27/27 pages generated** in 2.3 s. The route manifest
(`.next/app-path-routes-manifest.json`) contains exactly **27
entries**, including the dynamic routes `/companies/[key]/page`
and `/reports/[id]/page` (which is why the human-readable route
table shows 23 static rows). Matches the Phase 30 claim
(27 routes).

**Turbopack note:** the default `next build` (Turbopack) fails in
a worktree whose `node_modules` is a symlink — a worktree artifact,
not a code defect (Phase 23 note, re-confirmed by the audit's own
worktree layout). The webpack build is the supported path and
passes. No Turbopack failure was observed in the fresh clone with
a real `node_modules` install, because the audit used `--webpack`
throughout, as Phase 30 did.

**Other frontend checks (from `package.json`):** `lint` (eslint),
`typecheck` (`tsc --noEmit`), `format:check` (prettier) scripts
exist. Phase 23/24/25/26/27 reports record eslint clean and a
pre-existing `tsc` LayoutProps error in untouched `app/layout.tsx`
that does not fail the build; this audit did not re-run `tsc`
because the build result (which is the acceptance-relevant
artifact) already passed, and the LayoutProps note is carried as
an open LOW item from the phase reports, not re-verified here.

## 4. Playwright E2E (Phase 29 acceptance suite)

**Status: RUN BY THIS AUDIT — 6 passed, 0 failed.**

Command (from `psx-audit-fresh/frontend`, backend on scratch
database at `http://127.0.0.1:8000`, production build present):

```
npx playwright test --config=playwright.phase29.config.ts
```

Result: **6 passed (14.9 s)**, 2 workers:

- acceptance page shows run, verdict and counts (desktop + mobile)
- scenario table shows HBL blocked and no failures (desktop + mobile)
- defect register shows no critical/high defects (desktop + mobile)

This reproduces the Phase 29 claim (6 passed) against the audit's
own scratch backend and fresh-clone production build, and it
independently proves the frontend acceptance page renders the
scratch gate (verdict PARTIALLY COMPLETE, HBL chain blocked, no
failures, no critical/high defects). The suite's webServer started
its own `next start` on port 3000 and exited after the run; the
audit backend on port 8000 was stopped afterwards and both ports
were verified clear.

**Phase 2 smoke suite:** `frontend/playwright.config.ts` +
`frontend/e2e/smoke.spec.ts` remain untracked and deliberately NOT
committed (Phase 2 decision). Their 2/2 pass is a prior claim,
not re-verified here (the files are not in the audited tree).

## 5. Migration / backup / restore / startup tests

- **Alembic:** scratch database migrated `20261104_0004 →
  20261104_0024` with `database/.venv/bin/alembic upgrade head`
  from `database/`; `alembic current` = `20261104_0024 (head)`.
  PASS.
- **Backup/restore:** backup `2026-11-04T1230-PKT` restored into
  scratch database `psx_intelligence_audit` with
  `database/restore.sh`: dump SHA-256 verified
  (`98f7bc2e…d75ccd`, matches manifest and the prior claim), only
  the 2 documented non-fatal `pg_restore` errors (postgres-owned
  default-privilege statements), row-count gate
  `phase2_probe 0 = 0` → **VERIFIED**. A first restore attempt by
  this audit FAILED the gate (`phase2_probe` ERROR) because the
  schema grant had been issued against the wrong database — the
  gate correctly refused the bad restore, and the retry after the
  corrected grant passed. This corroborates that the restore gate
  works as designed (and that the grant mistake is an easy
  operator trap — the same mistake appears in the Phase 30 drill
  report).
- **Startup/shutdown/health/job-recovery:** exercised against the
  scratch backend in the runtime audit (see
  APPLICATION_RUNTIME_AUDIT.md); the Phase 28 `ops/` scripts were
  statically reviewed here (exec-in-subshell fix present,
  production-build-only frontend, postgres deliberately left
  running by `stop.sh`, dirty-tree refusal + ff-only pull +
  health gate in `update.sh`).

## 6. Totals (audit-executed only)

| Suite | Run | Passed | Failed | Skipped |
|---|---|---|---|---|
| Backend pytest (fresh clone, standard layout) | 453 | 453 | 0 | 0 |
| Backend pytest (fresh clone, non-standard layout) | 453 | 452 | 1 (layout artifact, resolved) | 0 |
| Frontend vitest | 11 | 11 | 0 | 0 |
| Webpack production build | 27 pages | 27 | 0 | 0 |
| Ruff | — | clean | 0 | 0 |
| Playwright Phase 29 suite | 6 | 6 | 0 | 0 |
| Alembic migration to head | 1 | 1 | 0 | 0 |
| Backup/restore gate | 1 (after 1 failed attempt on auditor error) | 1 | 0 | 0 |

**No test was weakened.** The one failure observed was resolved
by correcting the test environment to the layout the test
documents, not by editing the test.
