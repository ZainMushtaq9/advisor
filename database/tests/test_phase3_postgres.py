"""Phase 3 PostgreSQL-only tests — CHECK constraints, immutability
triggers, and indexed queries on the live database.

Runs inside ONE transaction that is rolled back at the end, so no
TEST ONLY row survives in the production database. Trigger-violation
attempts run inside SAVEPOINTs (begin_nested) so the outer transaction
stays usable after the expected exception.

Skipped (not faked) when DATABASE_URL is unset.
"""

import os
import sys
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from app.models.financial import (  # noqa: E402
    FinancialDocument,
    FinancialDocumentVersion,
    FinancialStatement,
    FinancialStatementLineItem,
)
from app.models.governance import AgentExecution, DataQualityReport, DataSource  # noqa: E402
from app.models.market import Announcement, IndexPrice, LiveQuote, MarketPrice  # noqa: E402
from app.models.reference import Company, Security  # noqa: E402
from app.services.data_quality import values_conflict  # noqa: E402

URL = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="DATABASE_URL not set; PostgreSQL tests skipped, not faked"
)


@pytest.fixture()
def session():
    engine = create_engine(URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    s = Session()
    tx = s.begin()
    yield s
    tx.rollback()
    s.close()


@pytest.fixture()
def fixtures(session):
    session.add(
        DataSource(
            source_key="pg-test-source",
            display_name="PG Test Source",
            source_type="test",
            base_reference="TEST ONLY",
        )
    )
    session.flush()
    src = session.query(DataSource).filter_by(source_key="pg-test-source").one()
    co = Company(legal_name="PG TEST ONLY Company Ltd", status="UNVERIFIED")
    session.add(co)
    session.flush()
    sec = Security(company_id=co.id, ticker="PGTEST", status="UNVERIFIED")
    session.add(sec)
    session.flush()
    return {"security": sec, "source": src}


def test_quality_status_check_constraint(session, fixtures):
    sec, src = fixtures["security"], fixtures["source"]
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                MarketPrice(
                    security_id=sec.id,
                    trading_date=date(2026, 11, 3),
                    bar_type="daily",
                    data_source_id=src.id,
                    close_price=Decimal("100"),
                    quality_status="BOGUS_STATUS",
                )
            )
            session.flush()


def test_immutability_trigger_blocks_update_and_delete(session, fixtures):
    sec, src = fixtures["security"], fixtures["source"]
    row = MarketPrice(
        security_id=sec.id,
        trading_date=date(2026, 11, 3),
        bar_type="daily",
        data_source_id=src.id,
        close_price=Decimal("100"),
        quality_status="UNVERIFIED",
    )
    session.add(row)
    session.flush()
    # Trigger RAISE maps to ProgrammingError (a DBAPIError), not to
    # IntegrityError — the trigger firing IS the pass condition.
    with pytest.raises(DBAPIError):
        with session.begin_nested():
            row.close_price = Decimal("101")
            session.flush()
    session.expire(row)
    with pytest.raises(DBAPIError):
        with session.begin_nested():
            session.delete(row)
            session.flush()


def test_security_date_index_exists_and_query_returns_row(session, fixtures):
    sec, src = fixtures["security"], fixtures["source"]
    session.add(
        MarketPrice(
            security_id=sec.id,
            trading_date=date(2026, 11, 3),
            bar_type="daily",
            data_source_id=src.id,
            close_price=Decimal("100"),
            quality_status="UNVERIFIED",
        )
    )
    session.flush()
    # With one row the planner correctly chooses a sequential scan, so
    # asserting 'Index Scan' would be wrong. What is testable here: the
    # index exists in pg_indexes, and the security+date query returns
    # the row. (Planner use at scale is a performance-report
    # observation, not a unit-test assertion.)
    index_exists = session.execute(
        text(
            "SELECT count(*) FROM pg_indexes "
            "WHERE indexname = 'idx_market_prices_security_date'"
        )
    ).scalar()
    assert index_exists == 1
    row = session.query(MarketPrice).filter_by(
        security_id=sec.id, trading_date=date(2026, 11, 3)
    ).one()
    assert row.close_price == Decimal("100")


def test_market_price_unique_grain(session, fixtures):
    sec, src = fixtures["security"], fixtures["source"]
    session.add(
        MarketPrice(
            security_id=sec.id,
            trading_date=date(2026, 11, 3),
            bar_type="daily",
            data_source_id=src.id,
            close_price=Decimal("105"),
            quality_status="UNVERIFIED",
        )
    )
    session.flush()
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                MarketPrice(
                    security_id=sec.id,
                    trading_date=date(2026, 11, 3),
                    bar_type="daily",
                    data_source_id=src.id,
                    close_price=Decimal("106"),
                    quality_status="UNVERIFIED",
                )
            )
            session.flush()


def test_conflicting_sources_kept_side_by_side(session, fixtures):
    sec = fixtures["security"]
    src2 = DataSource(
        source_key="pg-test-source-2",
        display_name="Second PG Test Source",
        source_type="test",
        base_reference="TEST ONLY",
    )
    session.add(src2)
    session.flush()
    src1 = fixtures["source"]
    for src, close in ((src1, Decimal("105")), (src2, Decimal("107"))):
        session.add(
            MarketPrice(
                security_id=sec.id,
                trading_date=date(2026, 11, 3),
                bar_type="daily",
                data_source_id=src.id,
                close_price=close,
                quality_status="CONFLICTED",
            )
        )
    session.flush()
    rows = session.query(MarketPrice).filter_by(trading_date=date(2026, 11, 3)).all()
    assert len(rows) == 2
    assert values_conflict([r.close_price for r in rows])


def test_missing_is_never_zero(session, fixtures):
    sec, src = fixtures["security"], fixtures["source"]
    session.add(
        MarketPrice(
            security_id=sec.id,
            trading_date=date(2026, 11, 4),
            bar_type="daily",
            data_source_id=src.id,
            close_price=None,
            volume=None,
            quality_status="MISSING",
        )
    )
    session.flush()
    row = session.query(MarketPrice).filter_by(trading_date=date(2026, 11, 4)).one()
    assert row.close_price is None and row.volume is None


def test_versioned_statement_never_overwritten(session, fixtures):
    co = fixtures["security"].company_id
    src = fixtures["source"]
    v1 = FinancialStatement(
        company_id=co,
        statement_type="income",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 12, 31),
        version_number=1,
        is_current=True,
        quality_status="UNVERIFIED",
        data_source_id=src.id,
    )
    session.add(v1)
    session.flush()
    # Writer order (audit M2 partial-unique index): flip the old
    # current flag FIRST, then insert the new current version — the
    # reverse order violates the one-current-per-grain index at flush.
    v1.is_current = False
    session.flush()
    v2 = FinancialStatement(
        company_id=co,
        statement_type="income",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 12, 31),
        version_number=2,
        supersedes_id=v1.id,
        is_current=True,
        quality_status="UNVERIFIED",
        data_source_id=src.id,
    )
    session.add(v2)
    session.flush()
    # The is_current pointer MAY flip (it is the only mutable column on
    # versioned tables); every other column change must be rejected.
    with pytest.raises(DBAPIError):
        with session.begin_nested():
            v1.statement_type = "balance_sheet"
            session.flush()
    session.expire(v1)
    assert session.query(FinancialStatement).count() == 2
    assert session.get(FinancialStatement, v1.id).version_number == 1
    assert session.get(FinancialStatement, v1.id).is_current is False


def test_line_item_keeps_original_label_and_unit(session, fixtures):
    co = fixtures["security"].company_id
    stmt = FinancialStatement(
        company_id=co,
        statement_type="income",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 12, 31),
        quality_status="UNVERIFIED",
        data_source_id=fixtures["source"].id,
    )
    session.add(stmt)
    session.flush()
    session.add(
        FinancialStatementLineItem(
            statement_id=stmt.id,
            line_item_key="revenue",
            original_label="Net sales (Rs in 000)",
            original_displayed_value="1,234,567",
            numeric_value=Decimal("1234567"),
            normalized_value=Decimal("1234567000"),
            reported_unit="thousands",
            normalization_rule="multiply by 1000 to base rupees",
            quality_status="UNVERIFIED",
        )
    )
    session.flush()
    item = session.query(FinancialStatementLineItem).one()
    assert item.original_label == "Net sales (Rs in 000)"
    assert item.normalized_value == Decimal("1234567000")


def test_performance_bulk_10000_rows(session, fixtures):
    import time
    from datetime import timedelta

    sec, src = fixtures["security"], fixtures["source"]
    base_date = date(2000, 1, 1)
    rows = [
        MarketPrice(
            security_id=sec.id,
            trading_date=base_date + timedelta(days=i),
            bar_type="daily",
            data_source_id=src.id,
            close_price=Decimal("100"),
            quality_status="UNVERIFIED",
        )
        for i in range(10000)
    ]
    start = time.perf_counter()
    session.bulk_save_objects(rows)
    session.flush()
    elapsed = time.perf_counter() - start
    assert session.query(MarketPrice).count() == 10000
    assert elapsed < 60  # generous bound; actual elapsed is recorded in the test report


def test_audit_h1_statement_quality_check(session, fixtures):
    """Audit H1 regression: financial_statements was the 22nd
    quality_status table, missing from migration 0003. A bogus
    status must now be rejected by the CHECK constraint."""
    co, src = fixtures["security"].company_id, fixtures["source"]
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                FinancialStatement(
                    company_id=co,
                    statement_type="income",
                    period_start=date(2026, 1, 1),
                    period_end=date(2026, 12, 31),
                    quality_status="BOGUS_STATUS",
                    data_source_id=src.id,
                )
            )
            session.flush()


def test_audit_h2_quality_report_resolution(session, fixtures):
    """Audit H2 regression: resolution_status/resolved_at may change;
    every other column change on data_quality_reports is rejected."""
    report = DataQualityReport(
        issue_type="missing_session",
        severity="LOW",
        affected_entity="market_prices",
        detail="TEST ONLY missing session",
    )
    session.add(report)
    session.flush()
    report.resolution_status = "resolved"
    from datetime import datetime, timezone

    report.resolved_at = datetime.now(timezone.utc)
    session.flush()
    assert report.resolution_status == "resolved"
    with pytest.raises(DBAPIError):
        with session.begin_nested():
            report.detail = "edited detail"
            session.flush()


def test_audit_h3_null_source_grain_rejected(session, fixtures):
    """Audit H3 regression: a NULL grain source no longer allows
    duplicate market prices — the column itself is NOT NULL."""
    sec = fixtures["security"]
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                MarketPrice(
                    security_id=sec.id,
                    trading_date=date(2026, 11, 3),
                    bar_type="daily",
                    data_source_id=None,
                    close_price=Decimal("100"),
                    quality_status="UNVERIFIED",
                )
            )
            session.flush()


def test_audit_m3_document_version_trigger(session, fixtures):
    """Audit M3 regression: document versions carry is_current and
    the versioned trigger (only that flag may change)."""
    co = fixtures["security"].company_id
    doc = FinancialDocument(company_id=co, document_type="annual_report", title="TEST ONLY")
    session.add(doc)
    session.flush()
    ver = FinancialDocumentVersion(document_id=doc.id, version_number=1, is_current=True)
    session.add(ver)
    session.flush()
    ver.is_current = False
    session.flush()
    with pytest.raises(DBAPIError):
        with session.begin_nested():
            ver.content_hash = "b" * 64
            session.flush()


def test_audit_m4_marker_and_immutable_triggers(session, fixtures):
    """Audit M4 regression: index_prices is immutable; live_quotes
    allows only is_latest flips; agent_executions allows only
    status/ended_at progress."""
    sec, src = fixtures["security"], fixtures["source"]
    idx = IndexPrice(
        index_code="TEST-INDEX",
        trading_date=date(2026, 11, 3),
        data_source_id=src.id,
        close_value=Decimal("100"),
        quality_status="UNVERIFIED",
    )
    session.add(idx)
    session.flush()
    with pytest.raises(DBAPIError):
        with session.begin_nested():
            idx.close_value = Decimal("101")
            session.flush()
    session.expire(idx)
    from datetime import datetime, timezone

    quote = LiveQuote(
        security_id=sec.id,
        data_source_id=src.id,
        quote_instant=datetime.now(timezone.utc),
        price=Decimal("100"),
        is_latest=True,
        quality_status="UNVERIFIED",
    )
    session.add(quote)
    session.flush()
    quote.is_latest = False
    session.flush()
    with pytest.raises(DBAPIError):
        with session.begin_nested():
            quote.price = Decimal("101")
            session.flush()
    session.expire(quote)
    run = AgentExecution(agent_name="TEST ONLY agent", trigger="manual", status="running")
    session.add(run)
    session.flush()
    run.status = "completed"
    session.flush()
    with pytest.raises(DBAPIError):
        with session.begin_nested():
            run.agent_name = "renamed agent"
            session.flush()


def test_audit_m6_announcement_hash_unique(session, fixtures):
    """Audit M6 regression: same company + same document hash is a
    duplicate; NULL hashes are excluded (review path)."""
    co = fixtures["security"].company_id
    session.add(
        Announcement(
            company_id=co,
            announcement_date=date(2026, 11, 3),
            title="TEST ONLY announcement",
            document_hash="c" * 64,
            quality_status="UNVERIFIED",
            data_source_id=fixtures["source"].id,
        )
    )
    session.flush()
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                Announcement(
                    company_id=co,
                    announcement_date=date(2026, 11, 3),
                    title="TEST ONLY duplicate",
                    document_hash="c" * 64,
                    quality_status="UNVERIFIED",
                    data_source_id=fixtures["source"].id,
                )
            )
            session.flush()


def test_head_revision_is_phase3(session):
    engine = create_engine(URL, pool_pre_ping=True)
    with engine.connect() as conn:
        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert rev == "20261104_0004"
