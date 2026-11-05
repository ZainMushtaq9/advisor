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

# PHASE 28 EXTENSION — full key-table counts for the restore gate.
# A backup whose only count is phase2_probe cannot prove a real restore:
# database/verify_restore.sh compares every count below against the
# restored database. A table missing from this database is recorded as
# null (never zero — missing is not empty). The list is the system's
# authoritative state, not every table: audit/log tables are excluded
# on purpose (they grow on every run and would false-fail the gate).
COUNT_TABLES="companies securities sectors registry_evidence company_identifiers market_prices trading_sessions financial_documents financial_statements financial_statement_line_items auditor_opinions technical_calculation_runs technical_calculation_errors technical_indicator_values fundamental_metric_values valuations economic_indicators news_events ownership_holdings market_breadth liquidity_observations forecast_assessments risk_metric_values decisions simulated_portfolios backtest_runs rag_chunks rag_benchmark_results screen_results alerts alert_runs reports report_figures job_runs job_definitions evaluation_metrics observability_slo_measurements auth_users data_sources phase2_probe"
COUNTS_JSON=""
for t in $COUNT_TABLES; do
  c="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -At -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='$t'" 2>/dev/null || echo 0)"
  if [ "$c" = "1" ]; then
    v="$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -At -c "SELECT count(*) FROM \"$t\"" 2>/dev/null || echo 'null')"
  else
    v="null"
  fi
  [ -n "$COUNTS_JSON" ] && COUNTS_JSON="$COUNTS_JSON, "
  COUNTS_JSON="$COUNTS_JSON\"$t\": $v"
done

cat > "$OUT/manifest.json" <<EOF
{
  "schema_version": "backup-manifest-v1",
  "backup_timestamp_pkt": "$STAMP",
  "database": "$PGDATABASE",
  "postgres_version": "$PG_VERSION",
  "alembic_revision": "$ALEMBIC_REV",
  "database_dump_sha256": "$DUMP_SHA",
  "files_archive_sha256": "$FILES_SHA",
  "row_counts": {$COUNTS_JSON},
  "included": ["database.dump", "raw/", "processed/", "financial_reports/", "parquet/", "research_reports/", "manifests/"],
  "excluded": ["backups/", "tmp/", "quarantine/"],
  "encryption": {"enabled": false, "recipient": null, "database_dump_sha256_encrypted": null, "files_archive_sha256_encrypted": null}
}
EOF

# PHASE 28 EXTENSION — optional GPG encryption (opt-in, off by default).
# Set BACKUP_GPG_RECIPIENT to a GPG key id/email to encrypt both outputs.
# No key is created by this project: the operator creates one first
# (gpg --full-generate-key) and keeps the private key OFF the backups.
# When encryption is on, the PLAINTEXT files are REMOVED after successful
# encryption (keeping them would defeat the purpose); the manifest keeps
# the plaintext hashes (for post-decrypt verification) plus the encrypted
# hashes. database/restore.sh decrypts first when plaintext is absent.
if [ -n "${BACKUP_GPG_RECIPIENT:-}" ]; then
  command -v gpg >/dev/null 2>&1 || { echo "backup: FAIL — BACKUP_GPG_RECIPIENT set but gpg not installed" >&2; exit 2; }
  echo "backup: encrypting to recipient $BACKUP_GPG_RECIPIENT"
  gpg --batch --yes --trust-model always --recipient "$BACKUP_GPG_RECIPIENT" \
    --output "$OUT/database.dump.gpg" --encrypt "$OUT/database.dump" \
    || { echo "backup: FAIL — database.dump encryption failed" >&2; exit 2; }
  gpg --batch --yes --trust-model always --recipient "$BACKUP_GPG_RECIPIENT" \
    --output "$OUT/files.tar.gz.gpg" --encrypt "$OUT/files.tar.gz" \
    || { echo "backup: FAIL — files.tar.gz encryption failed" >&2; exit 2; }
  ENC_DUMP_SHA="$(sha256sum "$OUT/database.dump.gpg" | cut -d' ' -f1)"
  ENC_FILES_SHA="$(sha256sum "$OUT/files.tar.gz.gpg" | cut -d' ' -f1)"
  python3 - "$OUT/manifest.json" "$BACKUP_GPG_RECIPIENT" "$ENC_DUMP_SHA" "$ENC_FILES_SHA" <<'PYEOF'
import json, sys
path, recipient, dump_sha, files_sha = sys.argv[1:5]
m = json.load(open(path))
m["encryption"] = {"enabled": True, "recipient": recipient,
                   "database_dump_sha256_encrypted": dump_sha,
                   "files_archive_sha256_encrypted": files_sha}
json.dump(m, open(path, "w"), indent=2)
PYEOF
  rm -f "$OUT/database.dump" "$OUT/files.tar.gz"
  echo "backup: encrypted (plaintext removed); manifest records both hash sets"
fi
echo "backup: done. manifest=$OUT/manifest.json"
echo "backup: database.dump sha256=$DUMP_SHA"
ls -lh "$OUT"
