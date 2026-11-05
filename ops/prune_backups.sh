#!/usr/bin/env bash
# PSX Intelligence AI — backup retention pruning (Phase 28).
# Policy (docs/phase-28/backup_retention_policy.md): keep the newest 30
# valid backups; never delete the newest backup; never delete a directory
# whose manifest.json is missing or unreadable (operator review instead).
# Dry-run by default: lists what WOULD be deleted and deletes nothing.
# Delete for real only with --confirm. Backups live in storage/backups/
# (gitignored operational output, never committed).
# Usage: ops/prune_backups.sh [--confirm] [--keep N]  (default keep 30)
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="${PSX_BACKUP_ROOT:-$ROOT/storage/backups}"
KEEP=30
CONFIRM=0
for arg in "$@"; do
  case "$arg" in
    --confirm) CONFIRM=1 ;;
    --keep) echo "usage: $0 [--confirm] [--keep N]" >&2; exit 2 ;;
    --keep=*) KEEP="${arg#--keep=}" ;;
    *) echo "usage: $0 [--confirm] [--keep N]" >&2; exit 2 ;;
  esac
done
[ "$KEEP" -ge 1 ] 2>/dev/null || { echo "prune: --keep must be >= 1" >&2; exit 2; }

VALID=()
INVALID=()
for d in "$BACKUP_ROOT"/202*-PKT; do
  [ -d "$d" ] || continue
  if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$d/manifest.json" 2>/dev/null; then
    VALID+=("$d")
  else
    INVALID+=("$d")
  fi
done
# Newest first (directory names sort chronologically: YYYY-MM-DDTHHMM-PKT).
IFS=$'\n' SORTED=($(printf '%s\n' "${VALID[@]}" | sort -r)); unset IFS
TOTAL="${#SORTED[@]}"
echo "prune: $TOTAL valid backups, keep newest $KEEP, ${#INVALID[@]} invalid (never auto-deleted)"
for d in "${INVALID[@]}"; do echo "prune: REVIEW (invalid manifest, kept): $d"; done
if [ "$TOTAL" -le "$KEEP" ]; then
  echo "prune: nothing to delete"
  exit 0
fi
DELETE=("${SORTED[@]:$KEEP}")
for d in "${DELETE[@]}"; do
  if [ "$CONFIRM" -eq 1 ]; then
    rm -rf "$d" && echo "prune: DELETED $d"
  else
    echo "prune: would delete (dry-run, use --confirm): $d"
  fi
done
[ "$CONFIRM" -eq 1 ] || echo "prune: dry-run only — nothing deleted"
