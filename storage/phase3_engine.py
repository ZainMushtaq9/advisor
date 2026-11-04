#!/usr/bin/env python3
"""Phase 3 storage engine — dataset registry, manifests, integrity
sweeps, quarantine and retention, built on the Phase 2 storage_helper
(write-once, SHA-256 sidecars, slug paths).

Rules (Phase 1 STORAGE_ARCHITECTURE + DATA_RETENTION_POLICY):
- raw/ is immutable: never overwritten, never deleted by the engine.
  A correction is a new file with a new hash.
- processed/ and parquet/ are regenerable from raw/ + code version;
  they may be rebuilt, never edited in place as if they were source.
- research_reports/ and financial_reports/ are versioned outputs;
  a new version is a new file, old versions stay.
- backups/ hold pg_dump files + manifests (see database/backup.sh).
- manifests/ hold dataset manifests: one JSON per dataset, listing
  every file, its SHA-256, byte size and provenance.
- quarantine/ holds files that failed integrity checks, with a
  reason file — quarantined files are never silently deleted.
- tmp/ is the only directory the engine will ever prune, and only
  files older than TMP_MAX_AGE_DAYS, and only when explicitly asked
  (prune_tmp defaults to dry-run).

Parquet: written only through pyarrow when it is actually installed.
If pyarrow is absent, write_parquet_dataset raises a clear error
instead of writing a fake '.parquet' file. No Parquet dataset is
claimed to exist unless this function wrote it and its manifest
records it.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PKT = ZoneInfo("Asia/Karachi")
TMP_MAX_AGE_DAYS = 7

DATASET_DIRS = {
    "raw_psx_dps": "raw/psx-dps",
    "raw_psxdata": "raw/psxdata",
    "raw_pdf": "raw/pdf",
    "processed": "processed",
    "parquet": "parquet",
    "research_reports": "research_reports",
    "financial_reports": "financial_reports",
    "backups": "backups",
    "manifests": "manifests",
    "quarantine": "quarantine",
    "tmp": "tmp",
}

# Retention: 'never' = engine never deletes; 'regenerable' = may be
# rebuilt from raw + code; 'prunable' = tmp only, age-gated.
RETENTION = {
    "raw": "never",
    "processed": "regenerable",
    "parquet": "regenerable",
    "research_reports": "never",
    "financial_reports": "never",
    "backups": "never",
    "manifests": "never",
    "quarantine": "never",
    "tmp": "prunable",
}


def _load_helper():
    spec = importlib.util.spec_from_file_location(
        "storage_helper", Path(__file__).resolve().parent / "storage_helper.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_helper = _load_helper()
sha256_hex = _helper.sha256_hex


def storage_root(root=None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parent


def now_pkt_iso() -> str:
    return datetime.now(PKT).isoformat()


def retention_for(top_dir: str) -> str:
    """Look up the retention policy for a top-level directory. This
    function exists so the policy is consulted, not just declared:
    prune_tmp refuses to touch any directory whose policy is not
    'prunable' (audit L5 fix)."""
    return RETENTION.get(top_dir, "never")


def register_dataset(
    root, dataset_key: str, file_rel_paths, provenance: dict | None = None
) -> dict:
    """Write a manifest for a dataset. Every listed file must exist
    under root; its SHA-256 and size are recorded. Returns the manifest.
    The manifest itself lives in manifests/<dataset_key>.manifest.json
    and is NOT listed inside itself (that would be self-referential).
    Audit L5 fix: registering a key whose manifest already exists
    raises instead of silently overwriting it — a new dataset version
    gets a new key."""
    base = storage_root(root)
    manifest_path = base / "manifests" / f"{dataset_key}.manifest.json"
    if manifest_path.exists():
        raise ValueError(
            f"manifest for dataset {dataset_key!r} already exists; "
            "use a new dataset key for a new version, never overwrite"
        )
    entries = []
    for rel in file_rel_paths:
        full = base / rel
        if not full.is_file():
            raise FileNotFoundError(f"dataset file missing: {rel}")
        data = full.read_bytes()
        entries.append({"rel_path": str(rel), "sha256": sha256_hex(data), "byte_size": len(data)})
    manifest = {
        "manifest_version": "phase3-dataset-v1",
        "dataset_key": dataset_key,
        "created_at_pkt": now_pkt_iso(),
        "provenance": provenance or {},
        "files": entries,
    }
    manifest_dir = base / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / f"{dataset_key}.manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def verify_dataset(root, dataset_key: str) -> list:
    """Re-hash every file in a manifest. Returns a list of mismatch
    dicts (empty = verified). A missing file, a hash mismatch, or a
    size mismatch (audit L5 fix: byte_size was recorded but ignored)
    is a finding, never a silent pass."""
    base = storage_root(root)
    manifest_path = base / "manifests" / f"{dataset_key}.manifest.json"
    manifest = json.loads(manifest_path.read_text())
    mismatches = []
    for entry in manifest["files"]:
        full = base / entry["rel_path"]
        if not full.is_file():
            mismatches.append({"rel_path": entry["rel_path"], "problem": "missing"})
            continue
        data = full.read_bytes()
        if sha256_hex(data) != entry["sha256"]:
            mismatches.append({"rel_path": entry["rel_path"], "problem": "hash_mismatch"})
        elif len(data) != entry["byte_size"]:
            mismatches.append({"rel_path": entry["rel_path"], "problem": "size_mismatch"})
    return mismatches


def quarantine_file(root, rel_path: str, reason: str) -> dict:
    """Move a failed-integrity file (and its sidecar, if present) into
    quarantine/ with a reason file. Returns the quarantine record.
    Nothing is deleted."""
    base = storage_root(root)
    src = base / rel_path
    if not src.is_file():
        raise FileNotFoundError(f"cannot quarantine missing file: {rel_path}")
    dest_dir = base / "quarantine"
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Audit L5 fix: two same-named files from different directories
    # must not overwrite each other in quarantine. Append a hash
    # suffix when the destination name is taken.
    dest = dest_dir / src.name
    if dest.exists():
        stem, suffix = src.stem, src.suffix
        dest = dest_dir / f"{stem}_{sha256_hex(src.read_bytes())[:8]}{suffix}"
    shutil.move(str(src), str(dest))
    sidecar = src.with_name(src.name + ".sidecar.json")
    if sidecar.is_file():
        # Follow the (possibly hash-suffixed) destination name, or a
        # second same-named quarantine would overwrite the first
        # file's sidecar — the same bug class as the file itself.
        shutil.move(str(sidecar), str(dest_dir / (dest.name + ".sidecar.json")))
    record = {
        "original_rel_path": rel_path,
        "quarantined_as": f"quarantine/{dest.name}",
        "reason": reason,
        "quarantined_at_pkt": now_pkt_iso(),
    }
    (dest_dir / f"{dest.name}.reason.json").write_text(json.dumps(record, indent=2))
    return record


def prune_tmp(root, dry_run: bool = True) -> list:
    """List (dry_run, default) or delete (dry_run=False) tmp/ files
    older than TMP_MAX_AGE_DAYS. This is the ONLY deletion the engine
    ever performs, and it is age-gated and opt-in."""
    base = storage_root(root)
    if retention_for("tmp") != "prunable":
        raise ValueError("tmp/ is not marked prunable in RETENTION; refusing to prune")
    tmp_dir = base / "tmp"
    if not tmp_dir.is_dir():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=TMP_MAX_AGE_DAYS)
    candidates = []
    for path in tmp_dir.rglob("*"):
        if path.is_file():
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                candidates.append(str(path.relative_to(base)))
                if not dry_run:
                    path.unlink()
    return candidates


def write_parquet_dataset(root, dataset_key: str, rows: list, columns: list) -> dict:
    """Write a real Parquet file via pyarrow, or fail loudly. rows are
    dicts; columns define the schema order. Returns manifest info."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "pyarrow is not installed; refusing to write a fake .parquet file"
        ) from exc
    base = storage_root(root)
    table = pa.table({col: [row.get(col) for row in rows] for col in columns})
    out_dir = base / "parquet"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{dataset_key}.parquet"
    if out_path.exists():
        raise ValueError("parquet dataset already exists; write a new version, never overwrite")
    pq.write_table(table, out_path)
    data = out_path.read_bytes()
    return {
        "dataset_key": dataset_key,
        "rel_path": f"parquet/{out_path.name}",
        "sha256": sha256_hex(data),
        "byte_size": len(data),
        "rows": len(rows),
    }
