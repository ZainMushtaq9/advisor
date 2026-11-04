"""Phase 3 model-metadata and pure-logic tests — no database needed.

Why no SQLite here: the Phase 3 models use PostgreSQL Identity
columns on BIGINT primary keys, which SQLite cannot generate (a
NOT NULL id failure on insert). Pretending SQLite proves the schema
would be dishonest. All behaviour that needs a database runs in
test_phase3_postgres.py against PostgreSQL inside a rolled-back
transaction. This file proves only what needs no database: model
metadata, column sets, and the deterministic validation helpers.
"""

import os
import sys
from decimal import Decimal

from sqlalchemy import inspect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

import pytest  # noqa: E402

from app.models import Base  # noqa: E402
from app.models.analysis import Forecast  # noqa: E402
from app.models.financial import FinancialStatementLineItem  # noqa: E402
from app.models.market import Announcement  # noqa: E402
from app.services.data_quality import (  # noqa: E402
    check_balance_sheet,
    check_cash_flow,
    duplicate_key_for_document,
    upgrade_quality_status,
    validate_ohlc,
    values_conflict,
)


def test_schema_has_54_tables():
    assert len(Base.metadata.tables) == 54


def test_no_broker_or_secret_columns():
    # Audit L4 fix: scan ALL 54 tables, not just Portfolio/Company.
    # (JSON payload/evidence columns cannot be constrained by column
    # names — keeping secrets out of them remains a convention, and
    # is recorded as such in the completion report.)
    forbidden = {
        "broker_account",
        "brokerage_id",
        "api_key",
        "password",
        "secret",
        "token",
        "credential",
    }
    for table_name, table in Base.metadata.tables.items():
        hits = set(table.columns.keys()) & forbidden
        assert not hits, f"{table_name} has secret-named columns: {hits}"


def test_ohlc_validation():
    assert validate_ohlc(Decimal("100"), Decimal("110"), Decimal("99"), Decimal("105")) == []
    assert "high_below_open_or_close" in validate_ohlc(
        Decimal("100"), Decimal("90"), Decimal("99"), Decimal("105")
    )
    assert "missing_close" in validate_ohlc(Decimal("100"), Decimal("110"), Decimal("99"), None)
    assert "negative_open" in validate_ohlc(
        Decimal("-1"), Decimal("110"), Decimal("99"), Decimal("105")
    )


def test_balance_sheet_and_cash_flow_identities():
    ok, diff = check_balance_sheet(Decimal("1000"), Decimal("600"), Decimal("400"))
    assert ok and diff == 0
    ok, _ = check_balance_sheet(Decimal("1000"), Decimal("600"), Decimal("300"))
    assert not ok
    ok, _ = check_cash_flow(Decimal("100"), Decimal("50"), Decimal("150"))
    assert ok
    assert check_balance_sheet(None, Decimal("600"), Decimal("400")) == (False, None)


def test_quality_upgrade_requires_evidence():
    with pytest.raises(ValueError):
        upgrade_quality_status("UNVERIFIED", "VERIFIED", "")
    # Audit M1 regression: the bypass states must also require evidence.
    for state in ("REJECTED", "CONFLICTED", "MISSING", "STALE", "PENDING_REVIEW"):
        with pytest.raises(ValueError):
            upgrade_quality_status(state, "VERIFIED", "")
        assert upgrade_quality_status(state, "VERIFIED", "re-checked") == "VERIFIED"
    assert (
        upgrade_quality_status("UNVERIFIED", "VERIFIED", "checked against source PDF p.12")
        == "VERIFIED"
    )
    assert (
        upgrade_quality_status("VERIFIED", "CONFLICTED", "") == "CONFLICTED"
    )  # downgrades always allowed
    assert upgrade_quality_status("VERIFIED", "VERIFIED", "") == "VERIFIED"  # re-affirmation


def test_duplicate_detection_key():
    assert (
        duplicate_key_for_document("a" * 64, "https://example.test/doc.pdf") == "sha256:" + "a" * 64
    )
    assert (
        duplicate_key_for_document(None, "https://example.test/doc.pdf")
        == "url:https://example.test/doc.pdf"
    )
    assert duplicate_key_for_document(None, None) is None


def test_forecast_requires_uncertainty_columns():
    cols = inspect(Forecast).columns
    assert not cols["interval_low"].nullable
    assert not cols["interval_high"].nullable
    assert not cols["uncertainty"].nullable
    for col in ("bear_value", "base_value", "bull_value"):
        assert col in cols


def test_announcement_hash_stored_not_pdf_bytes():
    cols = set(inspect(Announcement).columns.keys())
    assert "document_hash" in cols and "pdf_bytes" not in cols and "content" not in cols


def test_line_item_columns_keep_provenance():
    cols = set(inspect(FinancialStatementLineItem).columns.keys())
    for col in (
        "original_label",
        "original_displayed_value",
        "numeric_value",
        "normalized_value",
        "currency",
        "reported_unit",
        "normalization_rule",
        "page_number",
        "extraction_method",
        "quality_status",
        "is_derived",
    ):
        assert col in cols


def test_conflict_detection_helper():
    assert values_conflict([Decimal("105"), Decimal("107")])
    assert not values_conflict([Decimal("105"), Decimal("105"), None])
