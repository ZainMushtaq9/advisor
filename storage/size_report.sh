#!/usr/bin/env bash
# Size monitoring for the local file store (Phase 2, Team D).
# Usage: bash storage/size_report.sh [storage-root]
# Prints per-class disk usage + file counts + overall disk free space.
# No data is modified. Review cadence: weekly in Phase 2; a class growing
# unexpectedly (e.g. tmp/ non-empty, quarantine/ backlog) is a quality
# signal, not just a disk signal (see retention policy §4.7/§8).
set -euo pipefail
ROOT="${1:-$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")/storage}"
[ -d "$ROOT" ] || { echo "size_report: no such directory: $ROOT" >&2; exit 2; }
echo "storage root: $ROOT"
echo "--- per-class usage ---"
du -sh "$ROOT"/*/ 2>/dev/null || true
echo "--- file counts (excluding sidecars) ---"
for d in "$ROOT"/*/; do
  n=$(find "$d" -type f ! -name '*.sidecar.json' 2>/dev/null | wc -l)
  echo "$(basename "$d"): $n files"
done
echo "--- disk ---"
df -h "$ROOT" | tail -1
