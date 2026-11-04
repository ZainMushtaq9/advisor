"""phase_24_auth

Revision ID: 20261104_0020
Revises: 20261104_0019
Create Date: 2026-11-05

Phase 24 (authentication, authorization, security and governance)
tables: auth_users (local accounts, PBKDF2 hashes only — never
plaintext passwords), auth_tokens (SHA-256 hashes of opaque
bearer tokens only — the token itself is never stored), and
auth_audit_logs (append-only audit trail for account, token,
and access events; detail JSON never carries a secret).

Precedent note (Phases 11-22): Phase 24 stores its own tables
rather than retrofitting Phase 3 tables. These tables carry no
quality_status: they are access-control records, not business
data, and no quality-status promotion ever applies to them.
No order, execution, external-send, or publication concept
exists in these tables. No credentials are stored anywhere:
password_hash is PBKDF2-HMAC-SHA256 with a per-user salt and
token_hash is SHA-256 of an opaque token.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0020"
down_revision: str | None = "20261104_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_users",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=200), nullable=False),
        sa.Column("password_salt", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failed_logins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("username", name="uq_auth_users_username"),
        sa.CheckConstraint(
            "role IN ('user', 'analyst', 'administrator', 'read_only_agent', "
            "'service_process')",
            name="ck_auth_users_role",
        ),
    )
    op.create_table(
        "auth_tokens",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("token_type", sa.String(length=20), nullable=False),
        sa.Column("prefix", sa.String(length=12), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"]),
        sa.UniqueConstraint("token_hash", name="uq_auth_tokens_token_hash"),
        sa.CheckConstraint(
            "token_type IN ('user', 'service')",
            name="ck_auth_tokens_type",
        ),
    )
    op.create_table(
        "auth_audit_logs",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("target", sa.String(length=200), nullable=True),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "outcome IN ('success', 'failure', 'denied')",
            name="ck_auth_audit_logs_outcome",
        ),
    )


def downgrade() -> None:
    op.drop_table("auth_audit_logs")
    op.drop_table("auth_tokens")
    op.drop_table("auth_users")
