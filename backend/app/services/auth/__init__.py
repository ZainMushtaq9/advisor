"""Phase 24 roles and least-privilege permission matrix.

Roles (brief: user, analyst, administrator, read-only agent,
service process). Permissions are capability names; a route or
CLI action names the permission it needs, and enforcement checks
membership — never a role-name string comparison at the call site.

Least-privilege notes:
- ``user`` reads public material only. No internal material, no
  audit trail, no account management.
- ``read_only_agent`` reads public material only, like ``user``,
  but exists as a separate role so its tokens can be scoped,
  rate-limited, and revoked independently of human users.
- ``analyst`` additionally reads internal material and the audit
  trail (read-only). Analysts never manage accounts or tokens.
- ``service_process`` reads public + internal material for
  scheduled jobs (the Phase 21 alert runs, Phase 22 report runs).
  It never manages accounts and never reads the audit trail.
- ``administrator`` manages accounts and tokens and reads the
  audit trail. Administration happens through the local CLI
  (``scripts/manage_auth.py``) — no account-management route
  exists over HTTP, so there is no admin endpoint to attack.
- Nothing in this matrix grants an order, a publication, an
  external send, or a quality-status promotion. Those actions
  have no permission name on purpose: no role can ever hold them.

Unknown roles hold no permissions (fail closed). The Phase 19
RAG caller roles (internal / external / auditor) are a separate,
document-level scheme; the mapping is documented in
``docs/phase-24/rbac_model.md`` and is NOT merged into this matrix.
"""

from __future__ import annotations

ROLES = (
    "user",
    "analyst",
    "administrator",
    "read_only_agent",
    "service_process",
)

# Permission names. Keep this list closed: adding a permission is a
# deliberate design decision, recorded in docs/phase-24/rbac_model.md.
PERMISSIONS = (
    "read:public",
    "read:internal",
    "read:audit",
    "manage:users",
    "manage:tokens",
)

ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "user": ("read:public",),
    "analyst": ("read:public", "read:internal", "read:audit"),
    "administrator": (
        "read:public",
        "read:internal",
        "read:audit",
        "manage:users",
        "manage:tokens",
    ),
    "read_only_agent": ("read:public",),
    "service_process": ("read:public", "read:internal"),
}


def permissions_for(role: str) -> tuple[str, ...]:
    """Permissions held by a role; unknown roles hold none (fail closed)."""
    return ROLE_PERMISSIONS.get(role, ())


def has_permission(role: str, permission: str) -> bool:
    """True only when the role's matrix entry contains the permission."""
    return permission in permissions_for(role)
