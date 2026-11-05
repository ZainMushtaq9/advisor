#!/usr/bin/env bash
# PSX Intelligence AI — restore verification gate (Phase 28).
# Stronger than restore.sh's own phase2_probe gate: this script verifies a
# restored database against the backup manifest on THREE axes, and fails
# loudly on any mismatch:
#   1. Manifest hashes: database.dump + files.tar.gz SHA-256 vs manifest.
#      (For encrypted backups with plaintext absent, decrypts COPIES to a
#      temp directory and verifies those — the backup directory itself is
#      never mutated by this script.)
#   2. Row counts: every table in the manifest's row_counts (Phase 28
#      manifests carry ~44 tables; older manifests carry only
#      phase2_probe, and only those are compared) vs the target database.
#      A null manifest count (table absent at backup time) requires the
#      table to be absent in the target too — missing is not zero.
#   3. Alembic revision: target's alembic_version vs manifest (when both
#      are present and non-null).
# This script writes nothing to the target database (read-only queries)
# and never touches the live database unless the operator names it as the
# target — the normal target is psx_intelligence_restore_test.
# Usage: database/verify_restore.sh <backup-dir> [target-database]
#   (DATABASE_URL/PGUSER from the environment or database/.env)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${DATABASE_URL:-}" ]; then
  set -a; # shellcheck disable=SC1091
  source "$SCRIPT_DIR/.env"; set +a
fi
BACKUP_DIR="${1:?usage: verify_restore.sh <backup-dir> [target-database]}"
TARGET_DB="${2:-psx_intelligence_restore_test}"
: "${PGUSER:?PGUSER must be set}"
export PGHOST="${PGHOST:-localhost}" PGPORT="${PGPORT:-5432}"

[ -f "$BACKUP_DIR/manifest.json" ] || { echo "verify: no manifest.json in $BACKUP_DIR" >&2; exit 2; }
FAIL=0

# --- Axis 1: hashes (decrypt to temp when needed, never mutate backup) ---
VERIFY_DIR="$BACKUP_DIR"
TMPDIR=""
if [ ! -f "$BACKUP_DIR/database.dump" ] && [ -f "$BACKUP_DIR/database.dump.gpg" ]; then
  command -v gpg >/dev/null 2>&1 || { echo "verify: FAIL — encrypted backup but gpg not installed" >&2; exit 2; }
  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT
  echo "verify: decrypting copies to temp dir (backup untouched)..."
  gpg --batch --yes --quiet --output "$TMPDIR/database.dump" --decrypt "$BACKUP_DIR/database.dump.gpg" \
    || { echo "verify: FAIL — database.dump decryption failed" >&2; exit 2; }
  if [ -f "$BACKUP_DIR/files.tar.gz.gpg" ]; then
    gpg --batch --yes --quiet --output "$TMPDIR/files.tar.gz" --decrypt "$BACKUP_DIR/files.tar.gz.gpg" \
      || { echo "verify: FAIL — files.tar.gz decryption failed" >&2; exit 2; }
  fi
  VERIFY_DIR="$TMPDIR"
fi
check_hash() { # $1=file $2=expected
  if [ ! -f "$VERIFY_DIR/$1" ]; then echo "verify: MISSING $1" >&2; FAIL=1; return; fi
  actual="$(sha256sum "$VERIFY_DIR/$1" | cut -d' ' -f1)"
  if [ "$actual" = "$2" ]; then echo "verify: hash OK $1"; else echo "verify: HASH MISMATCH $1 (manifest=$2 actual=$actual)" >&2; FAIL=1; fi
}
EXP_DUMP="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['database_dump_sha256'])" "$BACKUP_DIR/manifest.json")"
EXP_FILES="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['files_archive_sha256'])" "$BACKUP_DIR/manifest.json")"
check_hash database.dump "$EXP_DUMP"
check_hash files.tar.gz "$EXP_FILES"

# --- Axis 2: row counts vs manifest ---
echo "verify: comparing row counts (manifest vs $TARGET_DB)..."
python3 - "$BACKUP_DIR/manifest.json" <<'PYEOF' > /tmp/psx-verify-counts.txt || echo "verify: manifest row_counts unreadable" >&2
import json, sys
m = json.load(open(sys.argv[1]))
for table, count in (m.get("row_counts") or {}).items():
    print(f"{table}\t{count}")
PYEOF
while IFS=$'\t' read -r table expected; do
  [ -n "$table" ] || continue
  exists="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$TARGET_DB" -At -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='$table'" 2>/dev/null || echo 0)"
  if [ "$expected" = "null" ] || [ "$expected" = "None" ]; then
    if [ "$exists" = "0" ]; then echo "verify: count OK $table (absent both sides)"
    else echo "verify: COUNT MISMATCH $table (manifest absent, target present)" >&2; FAIL=1; fi
  elif [ "$exists" = "1" ]; then
    actual="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$TARGET_DB" -At -c "SELECT count(*) FROM \"$table\"" 2>/dev/null || echo 'ERROR')"
    if [ "$actual" = "$expected" ]; then echo "verify: count OK $table ($actual)"
    else echo "verify: COUNT MISMATCH $table (manifest=$expected target=$actual)" >&2; FAIL=1; fi
  else
    echo "verify: COUNT MISMATCH $table (manifest=$expected, table absent in target)" >&2; FAIL=1
  fi
done < /tmp/psx-verify-counts.txt
rm -f /tmp/psx-verify-counts.txt

# --- Axis 3: alembic revision ---
EXP_REV="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('alembic_revision'))" "$BACKUP_DIR/manifest.json")"
LIVE_REV="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$TARGET_DB" -At -c 'SELECT version_num FROM alembic_version' 2>/dev/null || echo 'ERROR')"
if [ "$EXP_REV" != "null" ] && [ "$EXP_REV" != "None" ] && [ -n "$EXP_REV" ]; then
  if [ "$LIVE_REV" = "$EXP_REV" ]; then echo "verify: alembic OK ($LIVE_REV)"
  else echo "verify: ALEMBIC MISMATCH (manifest=$EXP_REV target=$LIVE_REV)" >&2; FAIL=1; fi
else
  echo "verify: alembic skipped (manifest has no revision)"
fi

if [ "$FAIL" -eq 0 ]; then echo "verify: VERIFIED — hashes, counts and revision all match manifest."
else echo "verify: FAILED — restore does NOT match manifest (see mismatches above)" >&2; exit 1; fi
