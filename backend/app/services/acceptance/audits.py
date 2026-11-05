"""Phase 29 security, licensing, and privacy audits.

All scans run against the worktree checkout (source scans) and the
live database (PII-column scan). A scan hit is reported with its
file and line, never summarized away. Two boundaries are stated
honestly:

- The tracked-dataset scan covers branch TIPS, not every historical
  commit. The .gitignore rules (financial reports, Phase 5 CSVs,
  .env) plus the tip scans are the evidence; a full-history scan is
  not claimed.
- A branch tip whose objects are not present locally is reported as
  unscanned, never as clean.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# parents[4] from backend/app/services/acceptance/audits.py:
# acceptance -> services -> app -> backend -> repo root. (Four
# chained .parent calls would stop at backend/ — that bug cost one
# dry-run round: the scans then covered backend/ only.)
REPO_ROOT = Path(__file__).resolve().parents[4]

EXECUTION_PATTERNS = [
    re.compile(r"place_order"),
    re.compile(r"execute_order"),
    re.compile(r"submit_order"),
    re.compile(r"execute_trade"),
    re.compile(r"place_trade"),
    re.compile(r"class\s+\w*Broker"),
    re.compile(r'"/orders"'),
    re.compile(r"'/orders'"),
]

DANGEROUS_PATTERNS = [
    re.compile(r"\beval\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"pickle\.load"),
    re.compile(r"os\.system\s*\("),
    re.compile(r"shell\s*=\s*True"),
]

WRITE_ROUTE_PATTERN = re.compile(r"@router\.(post|put|patch|delete)\b")
UPLOAD_PATTERN = re.compile(r"UploadFile")
# The trailing \b matters: "docker psql" in a tool-availability list
# (scripts/check_env.sh) is not `docker ps`; without \b the "ps"
# alternative would false-positive on it.
DOCKER_PATTERN = re.compile(r"docker\s+(run|build|exec|compose|ps|pull|push)\b|docker-compose")
SECRET_PATTERN = re.compile(
    r"(password|passwd|secret|api_key|token)\s*=\s*[\"'][^\"']{8,}[\"']",
    re.IGNORECASE,
)

CODE_DIRS = ["backend/app", "ops", "scripts", "database"]


def _grep_files(root: Path, patterns, dirs, suffixes=(".py", ".sh")):
    hits = []
    for rel in dirs:
        base = root / rel
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if "test" in path.name:
                continue
            # The scanner itself holds the search patterns as data;
            # scanning it would report its own patterns as hits.
            # Same allowlist rationale as the Phase 15-22 guard
            # tests (which skip this file for the same reason).
            if "acceptance" in path.parts and path.name == "audits.py":
                continue
            try:
                lines = path.read_text(errors="ignore").splitlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, start=1):
                for pattern in patterns:
                    if pattern.search(line):
                        hits.append(f"{path.relative_to(root)}:{lineno}: {line.strip()[:120]}")
                        break
    return hits


def _tracked_files(root: Path):
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.splitlines()


def audit_execution_identifiers(root: Path = REPO_ROOT):
    hits = _grep_files(root, EXECUTION_PATTERNS, ["backend/app"])
    return {
        "name": "execution_identifiers",
        "expected": 0,
        "found": len(hits),
        "hits": hits,
        "status": "pass" if not hits else "fail",
    }


def audit_dangerous_constructs(root: Path = REPO_ROOT):
    hits = _grep_files(root, DANGEROUS_PATTERNS, ["backend/app"])
    # The tesseract OCR call in financial_statements/extract.py uses a
    # fixed argv list with no shell=True; it matches none of the
    # patterns above and is therefore not a hit. (Confirmed safe in
    # Phase 24; re-verified here by the absence of any hit.)
    return {
        "name": "dangerous_constructs",
        "expected": 0,
        "found": len(hits),
        "hits": hits,
        "status": "pass" if not hits else "fail",
    }


def audit_write_routes(root: Path = REPO_ROOT):
    hits = _grep_files(root, [WRITE_ROUTE_PATTERN], ["backend/app"])
    return {
        "name": "write_routes",
        "expected": 0,
        "found": len(hits),
        "hits": hits,
        "status": "pass" if not hits else "fail",
    }


def audit_upload_endpoints(root: Path = REPO_ROOT):
    hits = _grep_files(root, [UPLOAD_PATTERN], ["backend/app"])
    return {
        "name": "upload_endpoints",
        "expected": 0,
        "found": len(hits),
        "hits": hits,
        "status": "pass" if not hits else "fail",
    }


def audit_docker_invocations(root: Path = REPO_ROOT):
    hits = _grep_files(root, [DOCKER_PATTERN], CODE_DIRS)
    return {
        "name": "docker_invocations",
        "expected": 0,
        "found": len(hits),
        "hits": hits,
        "status": "pass" if not hits else "fail",
    }


def audit_tracked_datasets(root: Path = REPO_ROOT):
    files = _tracked_files(root)
    if files is None:
        return {
            "name": "tracked_datasets",
            "expected": 0,
            "found": None,
            "hits": ["git ls-files failed"],
            "status": "fail",
        }
    hits = [
        f
        for f in files
        if f.endswith(".csv") or f.endswith(".pdf") or f.rsplit("/", 1)[-1] == ".env"
    ]
    return {
        "name": "tracked_datasets",
        "expected": 0,
        "found": len(hits),
        "hits": hits,
        "status": "pass" if not hits else "fail",
    }


def audit_tracked_secrets(root: Path = REPO_ROOT):
    files = _tracked_files(root)
    if files is None:
        return {
            "name": "tracked_secrets",
            "expected": 0,
            "found": None,
            "hits": ["git ls-files failed"],
            "status": "fail",
        }
    hits = []
    test_hits = []
    for rel in files:
        path = root / rel
        if not path.is_file():
            continue
        if path.suffix in (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz"):
            continue
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, start=1):
            if SECRET_PATTERN.search(line):
                entry = f"{rel}:{lineno}: {line.strip()[:120]}"
                if "test" in path.name:
                    # Test fixtures carry synthetic values, never live
                    # credentials; reported separately, not counted
                    # as secrets.
                    test_hits.append(entry)
                else:
                    hits.append(entry)
    return {
        "name": "tracked_secrets",
        "expected": 0,
        "found": len(hits),
        "hits": hits,
        "test_fixture_hits": test_hits,
        "status": "pass" if not hits else "fail",
    }


def audit_branch_tip_datasets(root: Path = REPO_ROOT):
    """Scan every remote branch tip for tracked .csv/.pdf/.env files.

    Tips whose objects are not present locally are reported as
    unscanned, never as clean.
    """
    proc = subprocess.run(
        ["git", "ls-remote", "--heads", "origin"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "name": "branch_tip_datasets",
            "expected": 0,
            "found": None,
            "hits": ["git ls-remote failed"],
            "unscanned": [],
            "status": "fail",
        }
    tips = {}
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            tips[parts[1].removeprefix("refs/heads/")] = parts[0]
    hits: list[str] = []
    unscanned: list[str] = []
    for branch, sha in sorted(tips.items()):
        proc = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", sha],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            unscanned.append(branch)
            continue
        for f in proc.stdout.splitlines():
            if f.endswith(".csv") or f.endswith(".pdf") or f.rsplit("/", 1)[-1] == ".env":
                hits.append(f"{branch}: {f}")
    return {
        "name": "branch_tip_datasets",
        "expected": 0,
        "found": len(hits),
        "hits": hits,
        "unscanned": unscanned,
        "tips_scanned": len(tips) - len(unscanned),
        "status": "pass" if not hits and not unscanned else "fail",
    }


def audit_pii_columns(session):
    """PII-like columns in the live database (auth hashes excepted).

    Implemented with the SQLAlchemy inspector so the same code runs
    on PostgreSQL (live) and SQLite (tests) — information_schema
    exists only on PostgreSQL.
    """
    from sqlalchemy import inspect, text

    hits = []
    inspector = inspect(session.bind)
    for table in sorted(inspector.get_table_names()):
        for column in inspector.get_columns(table):
            name = column["name"].lower()
            if any(key in name for key in ("email", "phone", "ssn", "passport")):
                hits.append(f"{table}.{column['name']}")
    auth_users = session.execute(text("SELECT COUNT(*) FROM auth_users")).scalar() or 0
    auth_tokens = session.execute(text("SELECT COUNT(*) FROM auth_tokens")).scalar() or 0
    auth_audit = session.execute(text("SELECT COUNT(*) FROM auth_audit_logs")).scalar() or 0
    return {
        "name": "pii_columns",
        "expected": 0,
        "found": len(hits),
        "hits": hits,
        "auth_tables": {
            "auth_users": auth_users,
            "auth_tokens": auth_tokens,
            "auth_audit_logs": auth_audit,
        },
        "status": "pass" if not hits else "fail",
    }


def run_audits(session, root: Path = REPO_ROOT):
    """Run every audit; returns a list of result dicts."""
    return [
        audit_execution_identifiers(root),
        audit_dangerous_constructs(root),
        audit_write_routes(root),
        audit_upload_endpoints(root),
        audit_docker_invocations(root),
        audit_tracked_datasets(root),
        audit_tracked_secrets(root),
        audit_branch_tip_datasets(root),
        audit_pii_columns(session),
    ]
