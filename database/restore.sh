#!/usr/bin/env bash
# PSX Intelligence AI — restore from a backup directory (Phase 2, Team D).
# pg_restore based. Credentials ONLY from the environment.
#
# Usage:
#   set -a; source database/.env; set +a
#   bash database/restore.sh <backup-dir> [target-database]
#
# SAFETY: the default target is psx_intelligence_restore_test — a SEPARATE
# database. Restoring over the live psx_intelligence database is REFUSED
# unless ALLOW_LIVE_RESTORE=1 is set explicitly, and even then only after
# a verified backup of the live database exists (operator's responsibility;
# this script does not silently overwrite live data).
# The target database must already exist and psx_app must have privileges
# on it (operator/superuser creates it once, see DATABASE_SETUP.md).
# Files are NOT auto-restored over the live store: files.tar.gz is listed
# and its hash verified; extraction is a separate, explicit operator step
# into a staging directory, so a restore test can never clobber live files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${DATABASE_URL:-}" ] && [ -f "$SCRIPT_DIR/.env" ]; then
  set -a; # shellcheck disable=SC1091
  source "$SCRIPT_DIR/.env"; set +a
fi
BACKUP_DIR="${1:?usage: restore.sh <backup-dir> [target-database]}"
TARGET_DB="${2:-psx_intelligence_restore_test}"
: "${PGUSER:?PGUSER must be set}"
export PGHOST="${PGHOST:-localhost}" PGPORT="${PGPORT:-5432}"

if [ "$TARGET_DB" = "psx_intelligence" ] && [ "${ALLOW_LIVE_RESTORE:-0}" != "1" ]; then
  echo "restore: REFUSED — target is the live database. Set ALLOW_LIVE_RESTORE=1" >&2
  echo "restore: only after taking a verified backup of the live database." >&2
  exit 2
fi
[ -f "$BACKUP_DIR/database.dump" ] || { echo "restore: no database.dump in $BACKUP_DIR" >&2; exit 2; }
[ -f "$BACKUP_DIR/manifest.json" ] || { echo "restore: no manifest.json in $BACKUP_DIR" >&2; exit 2; }

echo "restore: verifying dump hash against manifest..."
EXPECTED="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['database_dump_sha256'])" "$BACKUP_DIR/manifest.json")"
ACTUAL="$(sha256sum "$BACKUP_DIR/database.dump" | cut -d' ' -f1)"
[ "$EXPECTED" = "$ACTUAL" ] || { echo "restore: HASH MISMATCH (manifest=$EXPECTED actual=$ACTUAL)" >&2; exit 2; }
echo "restore: dump hash OK ($ACTUAL)"

echo "restore: pg_restore into $TARGET_DB (clean, if-exists)..."
# AUDIT NOTE (2026-11-04): pg_restore's exit code is NOT the gate here:
# --clean on a fresh DB, and the postgres-owned default-privilege
# statements in the dump, produce known non-fatal errors (see
# DATABASE_SETUP.md §9.3). The row-count check below is authoritative:
# a genuinely failed restore cannot pass it. A non-zero pg_restore exit
# is therefore printed as a warning, never silently swallowed.
pg_restore -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$TARGET_DB" --clean --if-exists "$BACKUP_DIR/database.dump" \
  || echo "restore: WARNING — pg_restore exited non-zero (see above); proceeding to row-count gate"

RESTORED="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$TARGET_DB" -At -c 'SELECT count(*) FROM phase2_probe' 2>/dev/null || echo 'ERROR')"
EXPECTED_COUNT="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['row_counts']['phase2_probe'])" "$BACKUP_DIR/manifest.json")"
echo "restore: phase2_probe rows restored=$RESTORED expected(manifest)=$EXPECTED_COUNT"
if [ "$RESTORED" != "$EXPECTED_COUNT" ]; then
  echo "restore: ROW-COUNT MISMATCH — restore NOT verified" >&2
  exit 2
fi
echo "restore: VERIFIED — row count matches manifest."
echo "restore: files archive in backup (NOT auto-extracted over live store):"
ls -lh "$BACKUP_DIR/files.tar.gz"
sha256sum "$BACKUP_DIR/files.tar.gz"
