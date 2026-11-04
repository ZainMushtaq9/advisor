"""Phase 24 auth administration CLI (local operator only).

Account management happens HERE, never over HTTP: there is no
login, registration, password-change, or token-issue route in
the API, so the admin surface does not exist on the network.

Commands (DATABASE_URL must be set, e.g. from database/.env):
  python scripts/manage_auth.py create-user --username alice --role analyst
      (password read via getpass, never a CLI argument, never logged)
  python scripts/manage_auth.py list-users
  python scripts/manage_auth.py disable-user --username alice
  python scripts/manage_auth.py enable-user --username alice
  python scripts/manage_auth.py set-role --username alice --role administrator
  python scripts/manage_auth.py login --username alice
      (verifies credentials, prints a bearer token ONCE; the token
      itself is never stored — only its hash. Save it now: it
      cannot be shown again. Revoke by prefix if lost.)
  python scripts/manage_auth.py issue-service-token --username svc-job
      (service tokens only for service_process / administrator roles)
  python scripts/manage_auth.py revoke-token --prefix psx_ab12
  python scripts/manage_auth.py audit-log [--limit 50]

Role enforcement at this layer: create-user, disable/enable,
set-role, and revoke-token require the OPERATOR to be an
administrator. The operator proves it with --operator-token
(a valid administrator bearer token) or --operator-user when
bootstrapping the FIRST administrator (allowed only when no
administrator account exists yet; every bootstrap is audited).
Login itself needs no operator token — it IS the authentication.

Exit codes: 0 ok; 1 operational failure (unknown user, bad
role, bad password, lockout, denied); 2 bad arguments /
missing DATABASE_URL. Human-readable lines go to stderr; the
bearer token (login / issue-service-token) is the only stdout
output, so it can be captured without mixing with logs.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import get_settings
from app.database import build_engine
from app.models.auth import AuthAuditLog, AuthUser
from app.services.auth import ROLES
from app.services.auth.service import (
    audit,
    authenticate,
    create_user,
    issue_token,
    public_user,
    revoke_token,
    set_user_active,
    set_user_role,
    validate_token,
)
from sqlalchemy.orm import sessionmaker


def _session():  # type: ignore[no-untyped-def]
    settings = get_settings()
    engine = build_engine(settings.DATABASE_URL)
    if engine is None:
        print("DATABASE_URL is not set; cannot manage auth.", file=sys.stderr)
        return None
    # Ensure the three auth tables exist. Idempotent: create_all
    # only creates missing tables and never alters existing ones,
    # so this is a no-op on a migrated live database and makes
    # the CLI usable against a fresh scratch database.
    from app.database import Base

    auth_tables = [
        t
        for name, t in Base.metadata.tables.items()
        if name in ("auth_users", "auth_tokens", "auth_audit_logs")
    ]
    Base.metadata.create_all(engine, tables=auth_tables)
    return sessionmaker(bind=engine)()


def _operator_is_admin(session, args) -> tuple[bool, str]:  # type: ignore[no-untyped-def]
    """Prove the operator is an administrator.

    Preferred: --operator-token (a valid administrator token).
    Bootstrap: --operator-user, allowed ONLY when no administrator
    account exists yet. Anything else is denied.
    """
    if args.operator_token:
        user, _ = validate_token(session, args.operator_token)
        if user is not None and user.role == "administrator":
            return True, "token"
        return False, "operator token is not a valid administrator token"
    admins = (
        session.query(AuthUser).filter_by(role="administrator", is_active=True).count()
    )
    if admins == 0 and getattr(args, "operator_user", None):
        return True, "bootstrap"
    return False, (
        "administrator proof required: pass --operator-token, or "
        "--operator-user when bootstrapping the first administrator"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create-user")
    p.add_argument("--username", required=True)
    p.add_argument("--role", required=True, choices=list(ROLES))
    p.add_argument("--operator-token")
    p.add_argument("--operator-user")

    p = sub.add_parser("list-users")

    for cmd in ("disable-user", "enable-user"):
        p = sub.add_parser(cmd)
        p.add_argument("--username", required=True)
        p.add_argument("--operator-token")

    p = sub.add_parser("set-role")
    p.add_argument("--username", required=True)
    p.add_argument("--role", required=True, choices=list(ROLES))
    p.add_argument("--operator-token")

    p = sub.add_parser("login")
    p.add_argument("--username", required=True)

    p = sub.add_parser("issue-service-token")
    p.add_argument("--username", required=True)
    p.add_argument("--operator-token")

    p = sub.add_parser("revoke-token")
    p.add_argument("--prefix", required=True)
    p.add_argument("--operator-token")

    p = sub.add_parser("audit-log")
    p.add_argument("--limit", type=int, default=50)

    args = parser.parse_args()
    session = _session()
    if session is None:
        return 2
    settings = get_settings()

    try:
        if args.command == "list-users":
            for user in session.query(AuthUser).order_by(AuthUser.username):
                print(json.dumps(public_user(user)), file=sys.stderr)
            return 0

        if args.command == "audit-log":
            rows = (
                session.query(AuthAuditLog)
                .order_by(AuthAuditLog.id.desc())
                .limit(args.limit)
            )
            for row in rows:
                print(
                    json.dumps(
                        {
                            "id": row.id,
                            "actor": row.actor,
                            "action": row.action,
                            "target": row.target,
                            "outcome": row.outcome,
                            "created_at": row.created_at.isoformat()
                            if row.created_at
                            else None,
                        }
                    ),
                    file=sys.stderr,
                )
            return 0

        if args.command == "login":
            try:
                password = getpass.getpass("Password: ")
            except EOFError:
                print("no password supplied (stdin closed)", file=sys.stderr)
                return 1
            user, reason = authenticate(
                session,
                args.username,
                password,
                max_failed=settings.AUTH_MAX_FAILED_LOGINS,
                lockout_minutes=settings.AUTH_LOCKOUT_MINUTES,
            )
            if user is None:
                print(f"login denied: {reason}", file=sys.stderr)
                return 1
            token, treason = issue_token(
                session,
                actor=args.username,
                user=user,
                token_type="user",
                user_ttl_hours=settings.AUTH_TOKEN_TTL_HOURS,
                service_ttl_days=settings.AUTH_SERVICE_TOKEN_TTL_DAYS,
            )
            if token is None:
                print(f"token issue failed: {treason}", file=sys.stderr)
                return 1
            print(token)
            print(
                "Token shown once: save it now; it cannot be shown again.",
                file=sys.stderr,
            )
            return 0

        ok, proof = _operator_is_admin(session, args)
        if not ok:
            print(f"denied: {proof}", file=sys.stderr)
            audit(
                session,
                getattr(args, "operator_user", None) or "cli",
                "access_denied",
                "denied",
                target=args.command,
                detail={"reason": proof},
            )
            session.commit()
            return 1
        actor = getattr(args, "operator_user", None) or "cli-admin-token"

        if args.command == "create-user":
            try:
                password = getpass.getpass("New password: ")
                confirm = getpass.getpass("Confirm password: ")
            except EOFError:
                print("no password supplied (stdin closed)", file=sys.stderr)
                return 1
            if password != confirm:
                print("passwords do not match", file=sys.stderr)
                return 1
            _, errors = create_user(session, actor, args.username, password, args.role)
            if errors:
                print("; ".join(errors), file=sys.stderr)
                return 1
            print(f"user {args.username} created ({args.role})", file=sys.stderr)
            return 0

        if args.command in ("disable-user", "enable-user"):
            active = args.command == "enable-user"
            done, reason = set_user_active(session, actor, args.username, active)
            if not done:
                print(reason, file=sys.stderr)
                return 1
            print(
                f"user {args.username} {'enabled' if active else 'disabled'}",
                file=sys.stderr,
            )
            return 0

        if args.command == "set-role":
            done, reason = set_user_role(session, actor, args.username, args.role)
            if not done:
                print(reason, file=sys.stderr)
                return 1
            print(f"user {args.username} role -> {args.role}", file=sys.stderr)
            return 0

        if args.command == "issue-service-token":
            user = session.query(AuthUser).filter_by(username=args.username).first()
            if user is None:
                print("unknown_user", file=sys.stderr)
                return 1
            token, reason = issue_token(
                session,
                actor=actor,
                user=user,
                token_type="service",
                user_ttl_hours=settings.AUTH_TOKEN_TTL_HOURS,
                service_ttl_days=settings.AUTH_SERVICE_TOKEN_TTL_DAYS,
            )
            if token is None:
                print(f"token issue failed: {reason}", file=sys.stderr)
                return 1
            print(token)
            print(
                "Service token shown once: save it now.",
                file=sys.stderr,
            )
            return 0

        if args.command == "revoke-token":
            if revoke_token(session, actor, args.prefix):
                print(f"tokens with prefix {args.prefix} revoked", file=sys.stderr)
                return 0
            print(f"no live tokens with prefix {args.prefix}", file=sys.stderr)
            return 1

        return 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
