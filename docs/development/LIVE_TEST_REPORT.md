# PSX Intelligence AI — Live Test Report (Phase 2, interim)

## Live preview: UNVERIFIED

- Supplied URL checked by the parent: https://cuddly-system-jj7j95xv97x7fjv7.github.dev/
- Result: returns only a GitHub sign-in page via text fetch.
- Conclusion: it is NOT an operational terminal/filesystem accessible to us, NOT the application preview URL, and NOT the runtime. The zero-cost local environment for Phase 2 remains this VM (~/workspace/psx-intelligence-ai/).
- No GitHub password was asked for or entered for that URL, and none must be asked for in chat for it.
- This report must NOT be read as a live-preview pass. Any future live-preview claim requires an actual inspection of a running local frontend/backend (with URL, time, and observed screens) recorded here.

## Local live checks already reported by teams (coordinator re-verification pending)
- Backend (Team C): uvicorn run + curl of all four /api/v1 endpoints — PASS as reported (health ok, system status with database unavailable when DATABASE_URL unset, version 0.1.0, config status redacted by name only). No uvicorn processes left running by Team C. Coordinator re-run: PENDING.
- Frontend: dev-server/browser inspection — PENDING Team B final report and coordinator re-verification. Do not treat scaffold presence as a live pass.
- Database/Redis: server liveness observed (PostgreSQL 16.15 accepting connections, Redis 7.0.15 PONG) during Team A's window. Project database, migration, backup/restore, and Celery task live evidence — PENDING Teams D and E final reports.

## Tests not claimed here
- No browser test (Playwright) result is asserted in this interim report.
- No frontend route render result is asserted until Team B's report and the coordinator's re-run.
- No Docker container run is asserted (Docker was absent at first check; Team E's evidence is pending).

## Phase 3 live checks (2026-11-04, coordinator)

- Backend on port 8002 (DATABASE_URL unset): /api/v1/health ok; /api/v1/system/version app 0.1.0, API v1, Python 3.12.3.
- PostgreSQL: head 20261104_0004, 56 tables, 23 triggers, 22 quality CHECKs, 0 business rows (verified by query and by independent verifiers).
- Backup 2026-11-04T1230-PKT: both SHAs MATCHED (coordinator + 2 verifiers); restore VERIFIED to psx_intelligence_restore_test, gate 0=0 (2 ignored pg_restore default-privilege warnings).
- Migration cycle: downgrade base exit 0, upgrade head exit 0 (coordinator + second independent verifier).
- Live preview URL: UNVERIFIED (github.dev returns sign-in page only).
