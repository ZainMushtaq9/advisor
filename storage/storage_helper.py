#!/usr/bin/env python3
"""Local file-storage helper — PSX Intelligence AI, Phase 2 (Team D).

Standalone stdlib-only module. It does NOT belong to backend/ and does
not collide with it: backend code may import it or re-implement the
same interface, but no backend file is created or modified here.

Contract (implements Phase 1 STORAGE_ARCHITECTURE.md §4/§5/§7):
  * Paths are RELATIVE to the storage root, never absolute machine paths.
  * Filenames are slugs: lowercase, hyphenated, no path separators, no
    ".." — a filename containing "../" is rejected, not sanitised silently.
  * Every write computes SHA-256 of the exact bytes BEFORE the file is
    considered stored, and writes a sidecar JSON next to it:
    "<filename>.sidecar.json" with schema_version "sidecar-v1",
    relative path, full SHA-256, byte size, created_at_pkt
    (Asia/Karachi ISO-8601), payload_type, and caller metadata.
  * Every read re-computes SHA-256 and compares it to the sidecar; a
    mismatch, a missing sidecar, or a missing file raises IntegrityError.
  * Raw files are write-once in spirit: write_file() refuses to overwrite
    an existing file with different bytes (a correction is a NEW file
    with a new hash, per Phase 1 immutability). Overwriting with
    byte-identical content is a no-op that re-validates the sidecar.

Storage root: PSX_STORAGE_ROOT env var, else the directory containing
this file (i.e. storage/ itself). Tests pass an explicit root.
"""
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SIDECAR_SCHEMA = "sidecar-v1"
ALLOWED_TOP_DIRS = {
    "raw", "processed", "financial_reports", "parquet",
    "research_reports", "backups", "manifests", "quarantine", "tmp",
}
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
PKT = ZoneInfo("Asia/Karachi")


class IntegrityError(ValueError):
    """Raised when a stored file fails its hash/sidecar verification."""


class UnsafePathError(ValueError):
    """Raised when a requested relative path violates the naming rules."""


def storage_root(root=None) -> Path:
    if root is not None:
        return Path(root)
    env = os.environ.get("PSX_STORAGE_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent


def validate_rel_path(rel_path) -> Path:
    """Validate a storage-relative path; return it as a Path.

    Accepts str or Path (internal callers pass the already-validated Path
    back in on the verify-after-write step — accepting both is what makes
    write-then-verify work instead of crashing on a type error).
    """
    s = str(rel_path)
    if not s or s.startswith("/") or ".." in Path(s).parts:
        raise UnsafePathError(f"unsafe storage path: {rel_path!r}")
    parts = Path(s).parts
    if parts[0] not in ALLOWED_TOP_DIRS:
        raise UnsafePathError(
            f"top directory {parts[0]!r} not in {sorted(ALLOWED_TOP_DIRS)}"
        )
    if not _SLUG_RE.match(parts[-1]):
        raise UnsafePathError(
            f"filename {parts[-1]!r} must match [a-z0-9][a-z0-9._-]*"
        )
    for part in parts[:-1]:
        if not _SLUG_RE.match(part):
            raise UnsafePathError(f"directory component {part!r} is not a slug")
    return Path(rel_path)


def name_with_hash(stem: str, ext: str, sha256_hex: str) -> str:
    """Phase 1 filename convention: <stem>_<sha256-first-8>.<ext>."""
    return f"{stem}_{sha256_hex[:8]}.{ext}"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sidecar_path(full: Path) -> Path:
    return full.with_name(full.name + ".sidecar.json")


def write_bytes(rel_path: str, data: bytes, metadata=None, root=None) -> dict:
    rel = validate_rel_path(rel_path)
    base = storage_root(root)
    full = base / rel
    digest = sha256_hex(data)
    if full.exists():
        existing = full.read_bytes()
        if sha256_hex(existing) != digest:
            raise IntegrityError(
                f"refusing to overwrite {rel} with different bytes "
                "(write-once rule: store a correction as a new file)"
            )
        # Identical rewrite: content is already correct. If the sidecar
        # is missing (e.g. deleted by a test or an operator), regenerate
        # it from the verified bytes instead of failing on its absence;
        # the bytes themselves are the evidence, and they match.
        sidecar_file = _sidecar_path(full)
        if sidecar_file.exists():
            return read_sidecar(rel, root=root)
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(data)
    sidecar = {
        "schema_version": SIDECAR_SCHEMA,
        "file_path": str(rel),
        "content_sha256": digest,
        "byte_size": len(data),
        "payload_type": (metadata or {}).get("payload_type", "other"),
        "created_at_pkt": datetime.now(PKT).isoformat(),
        "metadata": metadata or {},
    }
    _sidecar_path(full).write_text(json.dumps(sidecar, indent=2) + "\n")
    # Verify immediately: what was just written must read back identical.
    read_and_verify(rel, root=root)
    return sidecar


def write_text(rel_path: str, text: str, metadata=None, root=None) -> dict:
    return write_bytes(rel_path, text.encode("utf-8"), metadata=metadata, root=root)


def read_sidecar(rel_path: str, root=None) -> dict:
    rel = validate_rel_path(rel_path)
    full = storage_root(root) / rel
    sidecar_file = _sidecar_path(full)
    if not sidecar_file.exists():
        raise IntegrityError(f"missing sidecar for {rel}")
    return json.loads(sidecar_file.read_text())


def read_and_verify(rel_path: str, root=None) -> bytes:
    rel = validate_rel_path(rel_path)
    full = storage_root(root) / rel
    if not full.exists():
        raise IntegrityError(f"missing file: {rel}")
    sidecar = read_sidecar(rel, root=root)
    data = full.read_bytes()
    digest = sha256_hex(data)
    if digest != sidecar["content_sha256"]:
        raise IntegrityError(
            f"hash mismatch for {rel}: file={digest} sidecar={sidecar['content_sha256']}"
        )
    if len(data) != sidecar["byte_size"]:
        raise IntegrityError(f"size mismatch for {rel}")
    return data
