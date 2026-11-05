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

## 7. Post-HBL backup (closes the §3 gap during this run)

While this phase ran, the separate HBL extraction coordinator completed
and the live database gained HBL statements (documents 3→4, statements
88→118, line items 1316→2116, opinions 3→4). A new backup was therefore
taken after the load:

- Backup `2026-11-05T0537-PKT`: 7 s, 25 MB. Manifest: alembic
  20261104_0023, encryption off, documents 4, statements 118, line
  items 2116, opinions 4.
- Restore into the restore-test DB + `verify_restore.sh` full gate:
  PASSED in 6 s combined.
- Consistency note: the files archive hash is identical to the
  0529 backup's (`18f659…`) — expected, because the file store did
  not change (the HBL PDF was already in it before 0529); only
  database rows changed. The dump hash differs, as it must.
- The §3 limitation is now closed: a verified recovery point
  containing HBL statements exists. (Future HBL re-runs in Phases 8+
  will change derived rows again; take a fresh backup after those land
  too — that is routine, not a gap.)

## Conclusion for the acceptance gate

"Backup restore is proven" holds for: plaintext backups (old, new,
and post-HBL manifests), encrypted backups (ephemeral-key round-trip
+ restore + full gate), and the negative controls. What is NOT proven:
restore of an encrypted backup with a persistent operator key (no
such key exists yet — operator step).
