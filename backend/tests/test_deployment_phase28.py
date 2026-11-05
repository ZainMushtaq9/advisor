"""Phase 28 deployment gates: no hidden paid dependency, no secret in any
env template, no Docker invocation in ops scripts, systemd units validate.

These tests run against the CHECKOUT (repo root = parents[2] of this file).
They use only the standard library plus subprocess; they never touch the
live database, never print a secret, and never install anything.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Known-free backend pins (licences verified in backend/LICENCES.md for the
# Phase 2 set; fpdf2 added by Phase 22 for report PDFs, BSD-3-Clause).
# Any NEW backend dependency fails this test until its licence is reviewed
# and it is added here deliberately — that is the gate, not an accident.
ALLOWED_BACKEND_DEPS = {
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic-settings",
    "sqlalchemy",
    "alembic",
    "psycopg",
    "httpx",
    "pytest",
    "ruff",
    "fpdf2",
}

# Known-free frontend packages (all MIT/ISC/Apache-2.0/BSD as published).
ALLOWED_FRONTEND_DEPS = {
    "clsx",
    "lightweight-charts",
    "next",
    "react",
    "react-dom",
    "tailwind-merge",
    "@playwright/test",
    "@tailwindcss/turbopack",
    "@testing-library/jest-dom",
    "@testing-library/react",
    "@types/node",
    "@types/react",
    "@types/react-dom",
    "eslint",
    "eslint-config-next",
    "jsdom",
    "prettier",
    "tailwindcss",
    "typescript",
    "vitest",
}

# Placeholder values allowed for secret-bearing template keys. Anything else
# in a template is treated as a possibly-real secret and fails the test.
SECRET_PLACEHOLDERS = {"", "<redacted>", "changeme", "example"}


def _dep_name(spec: str) -> str:
    """Strip version specifiers and extras: 'psycopg[binary]==3.3.7' -> 'psycopg'."""
    name = re.split(r"[<>=!~\s;\[]", spec.strip(), maxsplit=1)[0]
    return name.lower()


def test_backend_dependencies_are_all_known_free() -> None:
    req = ROOT / "backend" / "requirements.txt"
    assert req.is_file(), "backend/requirements.txt missing"
    found = set()
    for line in req.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        found.add(_dep_name(line))
    unknown = found - ALLOWED_BACKEND_DEPS
    assert not unknown, f"unreviewed backend dependencies (licence gate): {sorted(unknown)}"
    assert found, "no backend dependencies parsed — test is vacuous"


def test_frontend_dependencies_are_all_known_free() -> None:
    pkg = json.loads((ROOT / "frontend" / "package.json").read_text())
    found = set(pkg.get("dependencies", {})) | set(pkg.get("devDependencies", {}))
    unknown = found - ALLOWED_FRONTEND_DEPS
    assert not unknown, f"unreviewed frontend dependencies (licence gate): {sorted(unknown)}"
    assert found, "no frontend dependencies parsed — test is vacuous"


def _template_entries(path: Path) -> list[tuple[str, str]]:
    entries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        entries.append((key.strip(), value.strip().strip('"').strip("'")))
    return entries


def test_env_templates_contain_no_real_secrets() -> None:
    templates = sorted(ROOT.rglob(".env.example"))
    assert templates, "no .env.example templates found — test is vacuous"
    for path in templates:
        for key, value in _template_entries(path):
            upper = key.upper()
            if "PASSWORD" in upper or "SECRET" in upper or "TOKEN" in upper:
                ok = (
                    value in SECRET_PLACEHOLDERS
                    or "placeholder" in value.lower()
                    or "example" in value.lower()
                    or "changeme" in value.lower()
                )
                assert ok, f"{path.relative_to(ROOT)}: {key} has a non-placeholder value"
            if upper == "DATABASE_URL":
                # Empty is legitimate here: unset DATABASE_URL means the API
                # truthfully reports db: unavailable (backend config.py).
                ok = (
                    value == ""
                    or "user:password" in value
                    or "<redacted>" in value
                    or "placeholder" in value.lower()
                    or "changeme" in value.lower()
                    or "sqlite" in value.lower()
                )
                assert ok, f"{path.relative_to(ROOT)}: DATABASE_URL is not a placeholder"
            assert "gmail" not in value.lower(), f"{path.relative_to(ROOT)}: {key} leaks a mailbox"
            assert "5439" not in value, f"{path.relative_to(ROOT)}: {key} leaks a user identifier"


def test_ops_and_database_scripts_pass_bash_syntax_check() -> None:
    scripts = sorted((ROOT / "ops").glob("*.sh")) + sorted((ROOT / "database").glob("*.sh"))
    assert scripts, "no ops/database scripts found — test is vacuous"
    for script in scripts:
        proc = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert proc.returncode == 0, f"{script.relative_to(ROOT)} fails bash -n: {proc.stderr}"


def test_ops_scripts_never_invoke_docker() -> None:
    """Docker ban (user decision 2026-11-04): no ops script may run Docker.
    Comments may mention Docker (e.g. 'WITHOUT Docker'); command invocations
    may not. Only non-comment code lines are checked."""
    docker_commands = (
        "docker run",
        "docker compose",
        "docker-compose",
        "docker build",
        "docker ps",
        "docker exec",
        "docker pull",
    )
    for script in sorted((ROOT / "ops").glob("*.sh")):
        for lineno, line in enumerate(script.read_text().splitlines(), start=1):
            code = line.split("#", 1)[0]
            for cmd in docker_commands:
                assert cmd not in code, (
                    f"{script.relative_to(ROOT)}:{lineno} invokes Docker ({cmd})"
                )


def test_systemd_units_instantiate_and_validate(tmp_path: Path) -> None:
    """ops/install.sh must write both units into a temp dir; when
    systemd-analyze exists it must also validate them (install.sh fails
    otherwise). No system-wide install happens here."""
    dest = tmp_path / "units"
    # Invoked via bash so the test does not depend on the executable bit
    # surviving a checkout (the scripts are chmod +x in the repo).
    proc = subprocess.run(
        ["bash", str(ROOT / "ops" / "install.sh"), "--dest", str(dest)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, f"ops/install.sh failed: {proc.stdout}\n{proc.stderr}"
    for unit in ("psx-backend.service", "psx-frontend.service"):
        text = (dest / unit).read_text()
        assert "@INSTALL_PATH@" not in text, f"{unit} still has an unsubstituted placeholder"
        assert "@SERVICE_USER@" not in text, f"{unit} still has an unsubstituted placeholder"
        assert "127.0.0.1" in text, f"{unit} does not bind loopback only"


def test_backup_scripts_carry_phase28_gates() -> None:
    backup = (ROOT / "database" / "backup.sh").read_text()
    assert "COUNT_TABLES" in backup, "backup.sh lost the Phase 28 full-counts extension"
    assert "BACKUP_GPG_RECIPIENT" in backup, "backup.sh lost the Phase 28 encryption option"
    assert (ROOT / "database" / "verify_restore.sh").is_file(), "verify_restore.sh missing"
    restore = (ROOT / "database" / "restore.sh").read_text()
    assert "database.dump.gpg" in restore, "restore.sh lost the Phase 28 decrypt pre-step"
