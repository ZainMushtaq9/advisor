"""Baseline: no tables (Phase 2 foundation).

Phase 3 schema is explicitly out of scope for this phase, so the
baseline migration is intentionally empty. It exists only so that
``alembic upgrade head`` can be verified end-to-end against a database.
"""

from __future__ import annotations

revision = "0001_baseline_empty"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
