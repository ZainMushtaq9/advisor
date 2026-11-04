"""phase_6_technical_immutability

Revision ID: 20261104_0005
Revises: a909e8449cdd
Create Date: 2026-11-04

Phase 6: apply the existing psx_prevent_mutation() trigger function
(Phase 3, migration 20261104_0003) to the Phase 6 output tables, so
"version history never overwritten" is enforced by the database,
not just by service-layer discipline:

- technical_indicator_values
- technical_signal_events
- quantitative_market_features
- market_regime_observations

UPDATE or DELETE on any of these raises an exception. Corrections
therefore require new rows: for indicator values, a NEW
configuration version (config_version bump) whose rows carry the
corrected figures, with old rows retained. Calculation runs and
error logs are NOT locked here: a run row legitimately changes
status (running -> completed), and error rows are append-only logs
whose correction is a new run, not an edit.

"""

from typing import Sequence, Union

from alembic import op

revision: str = '20261104_0005'
down_revision: Union[str, None] = 'a909e8449cdd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "technical_indicator_values",
    "technical_signal_events",
    "quantitative_market_features",
    "market_regime_observations",
)


def upgrade() -> None:
    for table in TABLES:
        op.execute(
            f"CREATE TRIGGER trg_{table}_immutable "
            f"BEFORE UPDATE OR DELETE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION psx_prevent_mutation();"
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON {table};")
