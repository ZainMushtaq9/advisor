"""Phase 19 access control for the knowledge base.

Roles (see services/rag __init__ ROLE_ACCESS):
- internal: official_public + issuer_internal + platform_internal.
- external: official_public only. An external caller asking for
  an issuer report is DENIED, and the denial is audited.
- auditor: official_public + platform_internal (never
  issuer_internal: audit scope covers public and platform
  material, not issuer-held reports).

check_access() is pure (no DB writes); the caller (runner / API)
records the decision in rag_access_audits. An unknown role is
denied by default — fail closed, never fail open.
"""

from __future__ import annotations

from app.services.rag import ROLE_ACCESS


def allowed_levels(caller_role: str) -> tuple[str, ...]:
    return ROLE_ACCESS.get(caller_role, ())


def check_access(caller_role: str, access_level: str) -> tuple[bool, str]:
    """Return (allowed, reason). Unknown roles are denied."""
    levels = allowed_levels(caller_role)
    if not levels:
        return False, f"Unknown caller role {caller_role!r}; denied by default."
    if access_level in levels:
        return True, (f"Role {caller_role!r} may access level {access_level!r}.")
    return False, (
        f"Role {caller_role!r} may access {sorted(levels)}; "
        f"level {access_level!r} is outside that scope."
    )


def filter_documents_for_role(
    documents: list[dict], caller_role: str
) -> tuple[list[dict], list[dict]]:
    """Split document dicts (each with id + access_level) into
    (allowed, denied) lists, with a reason per denied document."""
    allowed: list[dict] = []
    denied: list[dict] = []
    for doc in documents:
        ok, reason = check_access(caller_role, doc["access_level"])
        if ok:
            allowed.append(doc)
        else:
            denied.append({**doc, "denial_reason": reason})
    return allowed, denied
