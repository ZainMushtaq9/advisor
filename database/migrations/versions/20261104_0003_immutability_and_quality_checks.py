"""Phase 3 immutability triggers + quality-status CHECK constraints.

Immutability: BEFORE UPDATE OR DELETE triggers on append-only /
versioned tables. A correction is a NEW row (new version, new
observation), never an edit to an existing row. Tables whose rows
legitimately change state (live_quotes.is_latest, portfolios,
holdings, securities/company status, calculation runs) are
deliberately NOT trigger-protected — their mutability is documented
in docs/phase-03/integrity_rules.md.

Quality checks: the shared quality_status vocabulary (VERIFIED,
PARTIALLY_VERIFIED, UNVERIFIED, CONFLICTED, MISSING, REJECTED,
STALE, PENDING_REVIEW) is enforced by database CHECK constraints on
every provenance-carrying table, so a bad status cannot be written
even by a caller that bypasses the application helpers.
"""

from alembic import op

revision = "20261104_0003"
down_revision = "645bcd200539"
branch_labels = None
depends_on = None

IMMUTABLE_TABLES = (
    "audit_logs",
    "market_prices",
    "raw_payloads",
    "data_quality_reports",
    "market_snapshots",
    "announcements",
    "news",
)

# Versioned tables: figures must never be edited, but the is_current
# pointer MUST be able to flip when a new version arrives — otherwise
# 'current' could never be maintained. The trigger below allows ONLY
# is_current to change (compared via jsonb with that key removed) and
# rejects every other column change.
VERSIONED_TABLES = (
    "financial_statements",
    "financial_statement_line_items",
    "economic_indicators",
    "valuations",
    "forecasts",
    "recommendations",
    "financial_health_assessments",
)

QUALITY_TABLES = (
    "market_prices",
    "live_quotes",
    "market_snapshots",
    "index_prices",
    "corporate_actions",
    "announcements",
    "news",
    "financial_statement_line_items",
    "fundamental_metric_values",
    "technical_indicator_values",
    "quantitative_market_features",
    "market_regime_observations",
    "technical_signal_events",
    "economic_indicators",
    "valuations",
    "forecasts",
    "recommendations",
    "fundamental_trend_observations",
    "earnings_quality_observations",
    "financial_health_assessments",
    "fundamental_warning_events",
)

QUALITY_VALUES = (
    "VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "CONFLICTED",
    "MISSING", "REJECTED", "STALE", "PENDING_REVIEW",
)


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION psx_prevent_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'table % is append-only/versioned: corrections must be new rows, never edits', TG_TABLE_NAME;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table in IMMUTABLE_TABLES:
        op.execute(
            f"CREATE TRIGGER trg_{table}_immutable "
            f"BEFORE UPDATE OR DELETE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION psx_prevent_mutation();"
        )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION psx_allow_only_current_flag()
        RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'table % is versioned: rows must never be deleted', TG_TABLE_NAME;
            END IF;
            IF (to_jsonb(OLD) - 'is_current') IS DISTINCT FROM (to_jsonb(NEW) - 'is_current') THEN
                RAISE EXCEPTION 'table % is versioned: only is_current may change; figures require a new version row', TG_TABLE_NAME;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table in VERSIONED_TABLES:
        op.execute(
            f"CREATE TRIGGER trg_{table}_versioned "
            f"BEFORE UPDATE OR DELETE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION psx_allow_only_current_flag();"
        )
    for table in QUALITY_TABLES:
        values = ", ".join(f"'{v}'" for v in QUALITY_VALUES)
        op.create_check_constraint(
            f"ck_{table}_quality_status", table,
            f"quality_status IN ({values})",
        )


def downgrade() -> None:
    for table in QUALITY_TABLES:
        op.drop_constraint(f"ck_{table}_quality_status", table, type_="check")
    for table in VERSIONED_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_versioned ON {table};")
    op.execute("DROP FUNCTION IF EXISTS psx_allow_only_current_flag();")
    # Legacy: financial_statements / financial_statement_line_items were
    # immutable triggers in the first version of this migration, before
    # they moved to the versioned-trigger set. Their triggers must be
    # dropped too, or dropping psx_prevent_mutation() fails with
    # DependentObjectsStillExist (found by the coordinator's downgrade
    # re-run, 2026-11-04).
    for table in tuple(IMMUTABLE_TABLES) + ("financial_statements", "financial_statement_line_items"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON {table};")
    op.execute("DROP FUNCTION IF EXISTS psx_prevent_mutation();")
