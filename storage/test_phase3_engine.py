"""Phase 3 storage-engine tests — stdlib only, temp directory roots.
No test file ever lands in the real storage/ tree."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase3_engine as eng  # noqa: E402
from storage_helper import write_bytes  # noqa: E402


def test_register_and_verify_dataset(tmp_path):
    root = tmp_path / "store"
    write_bytes("raw/psx-dps/test-file.json", b'{"TEST ONLY": true}', root=root)
    manifest = eng.register_dataset(
        root, "test-dataset", ["raw/psx-dps/test-file.json"], provenance={"source": "TEST ONLY"}
    )
    assert len(manifest["files"]) == 1
    assert eng.verify_dataset(root, "test-dataset") == []


def test_tamper_detected_by_verify(tmp_path):
    root = tmp_path / "store"
    write_bytes("raw/psx-dps/test-file.json", b"original", root=root)
    eng.register_dataset(root, "test-dataset", ["raw/psx-dps/test-file.json"])
    (root / "raw/psx-dps/test-file.json").write_bytes(b"tampered")
    mismatches = eng.verify_dataset(root, "test-dataset")
    assert mismatches and mismatches[0]["problem"] == "hash_mismatch"


def test_quarantine_moves_file_and_keeps_reason(tmp_path):
    root = tmp_path / "store"
    write_bytes("raw/psx-dps/bad-file.json", b"bad", root=root)
    record = eng.quarantine_file(root, "raw/psx-dps/bad-file.json", "hash mismatch in sweep")
    assert not (root / "raw/psx-dps/bad-file.json").exists()
    assert (root / "quarantine/bad-file.json").exists()
    assert record["reason"] == "hash mismatch in sweep"


def test_quarantine_same_basename_twice(tmp_path):
    """Audit L5 regression: two same-named files from different
    directories must both survive quarantine, not overwrite."""
    root = tmp_path / "store"
    write_bytes("raw/psx-dps/same-name.json", b"first", root=root)
    write_bytes("raw/psxdata/same-name.json", b"second", root=root)
    eng.quarantine_file(root, "raw/psx-dps/same-name.json", "first failure")
    eng.quarantine_file(root, "raw/psxdata/same-name.json", "second failure")
    data_files = [
        p
        for p in (root / "quarantine").glob("same-name*.json")
        if "reason" not in p.name and "sidecar" not in p.name
    ]
    assert len(data_files) == 2
    assert sorted(p.read_bytes() for p in data_files) == [b"first", b"second"]


def test_register_duplicate_key_raises(tmp_path):
    """Audit L5 regression: re-registering a dataset key overwrites
    nothing — it raises."""
    root = tmp_path / "store"
    write_bytes("raw/psx-dps/test-file.json", b"data", root=root)
    eng.register_dataset(root, "dup-key", ["raw/psx-dps/test-file.json"])
    with pytest.raises(ValueError, match="already exists"):
        eng.register_dataset(root, "dup-key", ["raw/psx-dps/test-file.json"])


def test_verify_checks_byte_size(tmp_path):
    """Audit L5 regression: verify_dataset checks byte_size, not
    only the hash. (A size edit in the manifest with an unchanged
    hash must be reported.)"""
    root = tmp_path / "store"
    write_bytes("raw/psx-dps/test-file.json", b"data", root=root)
    eng.register_dataset(root, "size-key", ["raw/psx-dps/test-file.json"])
    manifest_path = root / "manifests" / "size-key.manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][0]["byte_size"] = 99999
    manifest_path.write_text(json.dumps(manifest))
    mismatches = eng.verify_dataset(root, "size-key")
    assert mismatches and mismatches[0]["problem"] == "size_mismatch"


def test_prune_tmp_is_dry_run_by_default(tmp_path):
    import os
    import time

    root = tmp_path / "store"
    tmp_dir = root / "tmp"
    tmp_dir.mkdir(parents=True)
    old = tmp_dir / "old-file.txt"
    old.write_text("old")
    old_time = time.time() - (8 * 24 * 3600)
    os.utime(old, (old_time, old_time))
    candidates = eng.prune_tmp(root, dry_run=True)
    assert "tmp/old-file.txt" in candidates
    assert old.exists()  # dry run deletes nothing
    eng.prune_tmp(root, dry_run=False)
    assert not old.exists()


def test_retention_policy_never_deletes_raw():
    assert eng.RETENTION["raw"] == "never"
    assert eng.RETENTION["research_reports"] == "never"
    assert eng.RETENTION["tmp"] == "prunable"


def test_parquet_guard_or_real_write(tmp_path):
    try:
        import pyarrow  # noqa: F401

        has_pyarrow = True
    except ImportError:
        has_pyarrow = False
    if not has_pyarrow:
        # The guard is the behaviour under test on this VM: no fake
        # '.parquet' file may ever be written.
        with pytest.raises(RuntimeError, match="refusing to write a fake"):
            eng.write_parquet_dataset(tmp_path, "test-parquet", [{"a": 1}], ["a"])
    else:
        out = eng.write_parquet_dataset(tmp_path, "test-parquet", [{"a": 1}, {"a": 2}], ["a"])
        assert out["rows"] == 2
        assert (tmp_path / out["rel_path"]).exists()
