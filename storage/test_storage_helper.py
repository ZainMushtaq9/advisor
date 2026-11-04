#!/usr/bin/env python3
"""Storage helper test — Phase 2 (Team D). Stdlib only, no pytest needed.

Writes a CLEARLY LABELLED TEST FILE (not PSX data) via storage_helper,
reads it back with hash verification, then proves the integrity check
actually catches tampering and a missing sidecar. Exit 0 only on all PASS.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_helper import (  # noqa: E402
    IntegrityError,
    UnsafePathError,
    name_with_hash,
    read_and_verify,
    sha256_hex,
    validate_rel_path,
    write_text,
)

CONTENT = "PHASE2-STORAGE-TEST — NOT PSX DATA — integrity-check fixture only\n"


def check(name, fn):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — harness reports, not hides
        print(f"FAIL: {name}: {type(exc).__name__}: {exc}")
        return False
    print(f"PASS: {name}")
    return True


def main() -> int:
    ok = True
    with tempfile.TemporaryDirectory(prefix="psx-storage-test-") as tmp:
        root = Path(tmp)
        fname = name_with_hash("phase2-test-file", "txt", sha256_hex(CONTENT.encode()))
        rel = f"processed/phase2-test/{fname}"
        sidecar = write_text(rel, CONTENT, metadata={"payload_type": "test"}, root=root)

        def sidecar_matches():
            assert sidecar["content_sha256"] == sha256_hex(CONTENT.encode()), "hash mismatch"

        def read_matches():
            assert read_and_verify(rel, root=root).decode() == CONTENT, "content mismatch"

        def tamper_fails():
            p = root / rel
            p.write_bytes(b"X" + p.read_bytes()[1:])
            try:
                read_and_verify(rel, root=root)
            except IntegrityError:
                return
            raise AssertionError("tampered file passed verification")

        def missing_sidecar_fails():
            p = root / rel
            p.write_bytes(CONTENT.encode())  # restore good content
            (root / (rel + ".sidecar.json")).unlink()
            try:
                read_and_verify(rel, root=root)
            except IntegrityError:
                return
            raise AssertionError("missing sidecar passed verification")

        def unsafe_rejected():
            for bad in ("../escape.txt", "/abs.txt", "raw/../../x.txt",
                        "secret/file.txt", "raw/Bad Name.txt"):
                try:
                    validate_rel_path(bad)
                except UnsafePathError:
                    continue
                raise AssertionError(f"accepted unsafe path {bad!r}")

        def overwrite_refused():
            write_text(rel, CONTENT, root=root)  # identical content: allowed
            try:
                write_text(rel, "different content\n", root=root)
            except IntegrityError:
                return
            raise AssertionError("overwrite with different bytes allowed")

        ok &= check("write returns sidecar with matching hash", sidecar_matches)
        ok &= check("read back equals written content", read_matches)
        ok &= check("tampered file fails verification", tamper_fails)
        ok &= check("missing sidecar fails verification", missing_sidecar_fails)
        ok &= check("unsafe paths rejected", unsafe_rejected)
        ok &= check("overwrite with different bytes refused", overwrite_refused)
    print("STORAGE TEST: ALL PASS" if ok else "STORAGE TEST: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
