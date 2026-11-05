# Phase 28 — Backup and Retention Policy

## What is backed up

`database/backup.sh` writes one directory per run,
`storage/backups/<YYYY-MM-DD>T<HHMM>-PKT/` (gitignored operational
output, never committed):

- `database.dump` — `pg_dump` custom format (-Fc) of the live database.
- `files.tar.gz` — file store, EXCLUDING `backups/` (would recurse),
  `tmp/` (scratch, no retention value), `quarantine/` (reviewed
  separately). Included: `raw/`, `processed/`, `financial_reports/`,
  `parquet/`, `research_reports/`, `manifests/`.
- `manifest.json` — timestamp (PKT), PostgreSQL version, alembic
  revision, plaintext SHA-256 of both outputs, full key-table row
  counts (40 tables, Phase 28 extension), inclusion/exclusion lists,
  and the encryption block (below).

A backup without a verified manifest is not a backup: verify with
`database/verify_restore.sh` after every run that matters, and always
before a schema change.

## Retention

- Keep the newest **30** valid backups. Prune with
  `ops/prune_backups.sh` (dry-run default; `--confirm` deletes).
- Never auto-delete: the newest backup, or any directory whose
  `manifest.json` is missing/unreadable (operator review instead —
  a corrupt-manifest directory might be the only copy of something).
- Keep a backup from BEFORE every migration touching existing tables
  (Phase 1 rule): the pre-migration backup is the rollback, and
  pruning must not remove the most recent pre-migration backup
  implicitly — the operator checks `manifest.json`'s `alembic_revision`
  before pruning around a migration.
- Disk grounding (measured 2026-11-05): 144 GB free on the home volume;
  the whole file store is ~27 MB and old (pre-import) backups total
  428 KB. Thirty current-state backups fit comfortably; if the store
  grows past ~1 GB, revisit the count before disk pressure does.

## Integrity check

Every restore is verified on three axes by
`database/verify_restore.sh`: manifest hashes, restored-vs-manifest row
counts (every table the manifest records; null = absent on both sides,
never zero), and alembic revision. `restore.sh`'s own gate (phase2_probe
count) is retained as a smoke check, but the Phase 28 gate is
`verify_restore.sh` — a restore that passes only the probe gate is NOT
verified.

Negative control (proven in the drill): a manifest with a tampered hash
fails verification, and a restore into a database with a different
alembic revision fails the revision check. Both must fail loudly, never
silently.

## Encryption (opt-in, mechanism delivered, no production key yet)

- Mechanism: set `BACKUP_GPG_RECIPIENT` to a GPG key id/email when
  running `backup.sh`. Both outputs are encrypted
  (`gpg --batch --yes --trust-model always`), plaintext is removed
  after successful encryption, and the manifest records both hash sets
  (plaintext hashes for post-decrypt verification, encrypted hashes
  for the stored files).
- Restore of an encrypted backup: `restore.sh` decrypts in place first
  when plaintext is absent (private key required), then the normal
  verification runs. `verify_restore.sh` decrypts COPIES to a temp
  directory instead (never mutates the backup).
- Operator key steps (NOT done by this phase — no key is created here):
  1. `gpg --full-generate-key` (operator identity; note the key id).
  2. Back up the private key OFF this machine (a key kept only next
     to the backups it decrypts is not a backup strategy).
  3. Set `BACKUP_GPG_RECIPIENT=<key id>` for backup runs.
  4. Prove it: restore an encrypted backup into
     `psx_intelligence_restore_test` and run `verify_restore.sh`.
- Until those steps are done, production backups stay plaintext and
  the retention policy records that fact honestly — encryption is a
  delivered mechanism awaiting an operator key, not a claimed state.
- Where supported, filesystem-level protection still applies:
  backup directories inherit the store's restrictive permissions, and
  `database/.env` (mode 0600) is never inside a backup's file archive
  (the archive covers the store, not the repo checkout).

## RPO / RTO (honest, measured where possible)

- **RPO (recovery point objective): time since the last operator
  backup.** Backups are operator-invoked, not scheduled, so there is
  no guaranteed window: RPO = the interval between operator backups.
  Recommended practice: a backup daily, plus one before every
  migration and before every bulk load. A backup taken during a
  concurrent load is a valid point-in-time snapshot of that moment —
  its manifest timestamp says exactly what it contains, and anything
  loaded after it is NOT in it (the HBL extraction landing after a
  backup is the standing example: take a fresh backup after it lands).
- **RTO (recovery time objective): measured by the drill.**
  `restore_drill.md` records the timed restore + verify of a
  current-state backup into the restore-test database. RTO for a live
  restore is that measured time plus operator confirmation time; the
  drill number is the evidence, not an estimate.
- **Off-machine note:** a backup that lives only on the machine it
  backs up does not survive that machine. The operator should copy
  backup directories (or at least the newest verified one) to a second
  location. This phase does not automate that copy: the destination is
  the operator's choice, and an automated copy to an unapproved
  third-party host would violate the project's data rules.

## What backups do NOT contain

- No credentials: `database/.env` is not in the file archive (the
  archive covers the store, not the checkout). The operator must keep
  the `.env` (and any GPG private key) separately — a restore without
  them cannot connect to the database.
- No `backups/` recursion, no `tmp/` scratch, no `quarantine/`.
- No claim of point-in-time recovery finer than the last backup: WAL
  archiving / PITR is NOT configured (it would need a WAL archive
  destination and is out of scope for this local deployment).
