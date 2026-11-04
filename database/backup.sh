#!/usr/bin/env bash
# PSX Intelligence AI — database + file-store backup (Phase 2, Team D).
# pg_dump/pg_restore based. Credentials ONLY from the environment.
#
# Usage:
#   set -a; source database/.env; set +a   # .env is gitignored, mode 0600
#   bash database/backup.sh
#   # or, without .env: DATABASE_URL=... PGPASSWORD=... bash database/backup.sh
#
# Output: storage/backups/<YYYY-MM-DD>T<HHMM>-PKT/
#   database.dump   (pg_dump custom format, -Fc)
#   files.tar.gz    (file store, EXCLUDING backups/ itself, tmp/, quarantine/)
#   manifest.json   (timestamp PKT, pg version, hashes, row counts, alembic revision)
#
# BACKUP INCLUSION RULES (Phase 1 retention policy):
#   INCLUDED: the database dump, raw/, processed/, financial_reports/,
#     parquet/, research_reports/, manifests/ (file-store classes that are
#     system-of-record or derived evidence).
#   EXCLUDED: storage/backups/ (would recurse), storage/tmp/ (scratch, no
#     retention value, deletable freely), storage/quarantine/ (reviewed
#     separately; a quarantined file is a quality issue, not backup data).
#   A backup MUST exist (and verify) BEFORE any major schema change
#   (new migration touching existing tables, partition changes, restores).
#   A backup without a verified manifest is not a backup — verify with
#   the hash check in docs/phase-02/DATABASE_SETUP.md after every run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
STORAGE_DIR="${PSX_STORAGE_ROOT:-$PROJECT_DIR/storage}"
if [ -z "${DATABASE_URL:-}" ] && [ -f "$SCRIPT_DIR/.env" ]; then
  set -a; # shellcheck disable=SC1091
  source "$SCRIPT_DIR/.env"; set +a
fi
: "${PGDATABASE:?PGDATABASE (or DATABASE_URL via .env) must be set}"
: "${PGUSER:?PGUSER must be set}"
export PGHOST="${PGHOST:-localhost}" PGPORT="${PGPORT:-5432}"

STAMP="$(TZ=Asia/Karachi date +%Y-%m-%dT%H%M-PKT)"
OUT="$STORAGE_DIR/backups/$STAMP"
mkdir -p "$OUT"

echo "backup: database=$PGDATABASE host=$PGHOST:$PGPORT -> $OUT"
pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -Fc -f "$OUT/database.dump"

# File-store copy (excluding backups/tmp/quarantine — see header rules).
# AUDIT FIX (2026-11-04): this step used to end with "|| true" and
# "2>/dev/null", which masked a tar failure and could have produced a
# "successful" backup with a bad/empty files.tar.gz. It now fails loudly
# (set -e) and the archive is checked non-empty below before the manifest
# is written, so a bad file-store copy can never be reported as done.
tar --exclude='backups' --exclude='tmp' --exclude='quarantine' \
  -czf "$OUT/files.tar.gz" -C "$STORAGE_DIR" \
  raw processed financial_reports parquet research_reports manifests
[ -s "$OUT/files.tar.gz" ] || { echo "backup: FAIL — files.tar.gz is empty" >&2; exit 2; }

DUMP_SHA="$(sha256sum "$OUT/database.dump" | cut -d' ' -f1)"
FILES_SHA="$(sha256sum "$OUT/files.tar.gz" | cut -d' ' -f1)"
PG_VERSION="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -At -c 'SHOW server_version')"
PROBE_COUNT="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -At -c 'SELECT count(*) FROM phase2_probe' 2>/dev/null || echo 'null')"
ALEMBIC_REV="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -At -c 'SELECT version_num FROM alembic_version' 2>/dev/null || echo 'null')"

cat > "$OUT/manifest.json" <<EOF
{
  "schema_version": "backup-manifest-v1",
  "backup_timestamp_pkt": "$STAMP",
  "database": "$PGDATABASE",
  "postgres_version": "$PG_VERSION",
  "alembic_revision": "$ALEMBIC_REV",
  "database_dump_sha256": "$DUMP_SHA",
  "files_archive_sha256": "$FILES_SHA",
  "row_counts": {"phase2_probe": $PROBE_COUNT},
  "included": ["database.dump", "raw/", "processed/", "financial_reports/", "parquet/", "research_reports/", "manifests/"],
  "excluded": ["backups/", "tmp/", "quarantine/"]
}
EOF
echo "backup: done. manifest=$OUT/manifest.json"
echo "backup: database.dump sha256=$DUMP_SHA"
ls -lh "$OUT"
