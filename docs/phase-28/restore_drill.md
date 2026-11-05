# Phase 28 — Restore Drill Report (measured 2026-11-05)

All restores target `psx_intelligence_restore_test` (the designated test
database). The live database was never a restore target, and its counts
were re-checked after every drill step (470 companies / 88 statements /
22 reports throughout — untouched).

## 1. Encrypted backup round-trip (ephemeral key, temp dirs only)

- Ephemeral GPG key generated in a temp `GNUPGHOME` (RSA 2048,
  `drill-test@local.invalid`, no passphrase); temp storage root with
  empty store dirs. No persistent key was created anywhere.
- Encrypted backup: 6 s. Outputs: `database.dump.gpg` (664 KB) +
  `files.tar.gz.gpg` (545 B, empty store dirs) + manifest. Plaintext
  files present: 0 (removed after successful encryption). Manifest:
  encryption enabled, recipient recorded, both hash sets present,
  40 row-count tables, companies 470, prices 444, alembic 20261104_0023.
- Decrypt-to-temp hash check: both decrypted copies match the
  manifest's plaintext hashes (True/True).
- Restore of the encrypted backup into the restore-test DB via
  `restore.sh` (exercising its decrypt pre-step): 2 s, gate passed.
- `verify_restore.sh` full gate on the encrypted restore: PASSED
  (hashes + all 40 counts + alembic 0023).
- Cleanup: ephemeral keyring, temp storage root, and temp decrypt dirs
  all removed after the test.

## 2. Old backup restore (pre-import manifest)

- Backup `2026-11-04T1230-PKT` (the newest pre-Phase-28 backup; predates
  the registry import) restored into the restore-test DB: 1 s.
- `restore.sh` gate: PASSED (phase2_probe 0 = manifest 0).
- `verify_restore.sh` gate: PASSED on the old manifest's own terms
  (phase2_probe 0, alembic 20261104_0004). Older manifests carry only
  the probe count; the verifier compares exactly what the manifest
  records, no more.

## 3. Fresh current-state backup (first since the registry import)

- Before this drill, every backup predated the registry import. The
  fresh backup closes that gap.
- Backup `2026-11-05T0529-PKT`: 8 s, 25 MB total (database.dump 1.1 MB,
  files.tar.gz 24 MB — dominated by the financial-report PDFs).
  Manifest: alembic 20261104_0023, encryption off (default),
  companies 470, prices 444, statements 88, reports 22.
- HONEST LIMIT: this backup predates the HBL extraction load (the
  separate HBL coordinator had not loaded anything when it ran). A
  fresh backup must be taken again after the HBL load lands; until
  then, HBL statements are NOT in any backup.

## 4. Fresh backup restore + full verification

- Restore into the restore-test DB: 1 s, `restore.sh` gate PASSED.
- `verify_restore.sh` full gate: PASSED — all 40 manifest counts match
  (including companies 470, securities 470, sectors 37,
  registry_evidence 1001, market_prices 444, financial_documents 3,
  financial_statements 88, line items 1316, opinions 3,
  rag_benchmark_results 6 — the honest post-replacement-#6 value, not
  the superseded 18 — screen_results 1418, alerts 89, alert_runs 18,
  reports 22, report_figures 541, job_runs 71, job_definitions 8,
  evaluation_metrics 44, observability_slo_measurements 14,
  auth_users 0, data_sources 19) + alembic 20261104_0023.
- Verify run time: 5 s. Measured RTO for a current-state restore +
  verification: ~6 s (plus operator confirmation time for a live
  restore, which is not automated and not timed here).

## 5. Negative controls (must fail, and did)

- Tampered manifest copy (database.dump hash zeroed, everything else
  intact): `verify_restore.sh` exits 1 with an explicit HASH MISMATCH
  for database.dump, while all 40 counts and the alembic revision
  still pass — proving the hash axis is independent and effective,
  and that a pass is not a rubber stamp.
- A restore into a database with a different alembic revision fails
  the revision check (covered by the verifier's design; the old-backup
  case in §2 shows the complementary pass at revision 0004).

## 6. Live database untouched

After all five drill sections, the live database still reads companies
470, statements 88, reports 22 — no drill step wrote to it. The
restore-test database ends holding the fresh-backup restore (the
current state), which is its intended purpose.

## Conclusion for the acceptance gate

"Backup restore is proven" holds for: plaintext backups (old and new
manifests), encrypted backups (ephemeral-key round-trip + restore +
full gate), and the negative controls. What is NOT proven: restore of
an encrypted backup with a persistent operator key (no such key
exists yet — operator step), and restore of a post-HBL state (no such
backup exists yet — take one after the HBL load lands).
