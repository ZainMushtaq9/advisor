# Phase 3 — Backup and Restore

Scripts (Phase 2, unchanged in Phase 3): `database/backup.sh`,
`database/restore.sh`. Credentials only from the environment
(gitignored `database/.env`, mode 0600). Live-restore is refused
without `ALLOW_LIVE_RESTORE=1`, and even then only after a verified
backup exists.

## Phase 3 run (actually executed, 2026-11-04)

- Backup: `storage/backups/2026-11-04T1217-PKT/` — database.dump
  (175K), files.tar.gz, manifest.json.
- Manifest: alembic_revision `20261104_0003`, database dump SHA-256
  `76596f98cd4fa05fe7423ebddae84341e7ba9d439f241c81c14f7c1ee97b5958`
  — re-hashed by the coordinator and MATCHED; files archive SHA
  also MATCHED.
- Restore: to the separate `psx_intelligence_restore_test`
  database (never the live database). Result VERIFIED: phase2_probe
  rows restored 0 = manifest 0, with the 2 known harmless
  pg_restore default-privilege warnings already documented in
  Phase 2. Files archive listed and hash-verified, NOT
  auto-extracted over the live store.

## What restore does NOT prove

Restore verifies the dump is restorable and the row-count gate
works. It does not prove that a future, larger dataset restores
within a time budget, and it does not prove point-in-time recovery
(PITR/WAL archiving is not configured in Phase 3). Both are
Phase 5+ operational decisions, to be measured with real volumes.

## After a reboot

PostgreSQL on this VM does not auto-start (systemd start is blocked
by policy-rc.d, Phase 2 finding). Run `pg_ctlcluster 16 main start`
before any database work. This is a VM limitation, not a schema
limitation, and it is carried forward.
