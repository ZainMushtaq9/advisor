"""Deterministic loader: extracted faces -> Phase 3 financial tables.

Rules:
- Every row quality_status = UNVERIFIED (single source, rule H1).
- Dash/blank/nil -> numeric_value NULL, never zero.
- Values are stored as reported AND normalised to base currency
  units (thousands x1000, millions x1e6, billions x1e9). Per-share
  EPS rows are NOT scaled: they are Rupees per share, not thousands.
- Documents are hash-deduplicated per company (Phase 3 unique
  index). A re-run with the same hash writes nothing new.
- Restatements are new versions, never overwrites (none in this run).
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .numbers import normalise_value

PKT = ZoneInfo("Asia/Karachi")
EPS_PREFIX = "eps_"
SCALE = {"rupees": 1, "thousands": 1000, "millions": 1_000_000, "billions": 1_000_000_000}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_or_create_data_source(session, source_key, display_name, base_reference, terms_summary):
    from app.models.governance import DataSource

    row = session.query(DataSource).filter_by(source_key=source_key).one_or_none()
    if row is None:
        row = DataSource(
            source_key=source_key,
            display_name=display_name,
            source_type="issuer_investor_relations",
            base_reference=base_reference,
            verification_status="UNVERIFIED",
            terms_summary=terms_summary,
        )
        session.add(row)
        session.flush()
    return row


def get_company(session, symbol):
    """Resolve a ticker to its company via the securities table."""
    from app.models.reference import Company, Security

    sec = session.query(Security).filter_by(ticker=symbol).one_or_none()
    if sec is None:
        raise ValueError(f"unknown company symbol: {symbol}")
    company = session.query(Company).filter_by(id=sec.company_id).one_or_none()
    if company is None:
        raise ValueError(f"no company row for symbol: {symbol}")
    return company


def get_or_create_document(session, company_id, page_map, content_hash, page_count):
    from app.models.financial import FinancialDocument, FinancialDocumentDownload

    doc = (
        session.query(FinancialDocument)
        .filter_by(company_id=company_id, content_hash=content_hash)
        .one_or_none()
    )
    created = False
    if doc is None:
        doc = FinancialDocument(
            company_id=company_id,
            document_type=page_map.get("document_type", "financial_report"),
            title=page_map.get("title", f"{page_map['company_symbol']} financial statements"),
            source_url=page_map.get("source_url"),
            storage_location=page_map["pdf"],
            content_hash=content_hash,
            mime_type="application/pdf",
            page_count=page_count,
        )
        session.add(doc)
        session.flush()
        # No HTTP download is performed by this loader: the PDF is
        # a sampled local file. Record that truth (http_status
        # NULL), never a fabricated 200.
        session.add(
            FinancialDocumentDownload(
                document_id=doc.id,
                attempted_at=datetime.now(PKT),
                status="success",
                http_status=None,
                error_detail=(
                    "Sampled local file (issuer/RNS PDF stored under "
                    "storage/financial_reports/); no HTTP download "
                    "performed by the loader."
                ),
            )
        )
        created = True
    return doc, created


def load_statement(
    session,
    *,
    company_id,
    data_source,
    document_id,
    page_map,
    column,
    rows,
    col_index,
    method,
    confidence,
    confidence_map=None,
    scope=None,
):
    """Write one statement (one column of a face) + its line items.

    ``confidence_map`` optionally overrides the confidence per
    line-item key (used for pdftotext page-match mismatches, which
    must be NULL at insert time: versioned tables forbid UPDATEs).
    ``scope`` disambiguates matrix faces (changes-in-equity): one
    statement per equity component per movement block, with
    statement_scope = the component key; None for ordinary faces.
    Returns (statement, n_items_written, skipped_existing).
    """
    from app.models.financial import FinancialStatement, FinancialStatementLineItem

    period_start = date.fromisoformat(column["period_start"])
    period_end = date.fromisoformat(column["period_end"])
    existing = (
        session.query(FinancialStatement)
        .filter_by(
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            statement_type=page_map["statement_type"],
            version_number=1,
            data_source_id=data_source.id,
            statement_scope=scope,
        )
        .one_or_none()
    )
    if existing is not None:
        return existing, 0, True
    pub = page_map.get("publication_date")
    stmt = FinancialStatement(
        data_source_id=data_source.id,
        company_id=company_id,
        statement_type=page_map["statement_type"],
        period_start=period_start,
        period_end=period_end,
        publication_date=date.fromisoformat(pub) if pub else None,
        reporting_frequency=column.get("reporting_frequency")
        or page_map.get("reporting_frequency"),
        audited_status=page_map.get("audited_status"),
        consolidated_status=page_map.get("consolidated_status"),
        currency=page_map.get("currency", "PKR"),
        unit_scale=page_map.get("unit_scale"),
        document_id=document_id,
        source_key=data_source.source_key,
        collected_at=datetime.now(PKT),
        quality_status="UNVERIFIED",
        version_number=1,
        is_current=True,
        statement_scope=scope,
    )
    session.add(stmt)
    session.flush()
    unit_scale = page_map.get("unit_scale", "rupees")
    n = 0
    for row in rows:
        value = row["values"][col_index] if col_index < len(row["values"]) else None
        displayed = row["displayed"][col_index] if col_index < len(row["displayed"]) else None
        if row["key"].startswith(EPS_PREFIX):
            normalised = value  # Rupees per share, not scaled
            rule = "per-share value in Rupees; not scaled by unit_scale"
            reported_unit = "rupees"
        else:
            normalised = normalise_value(value, unit_scale) if value is not None else None
            rule = (
                f"reported in {unit_scale}; normalised_value = "
                f"numeric_value x {SCALE.get(unit_scale, 1)}"
            )
            reported_unit = unit_scale
        row_conf = (
            confidence_map.get(row["key"], confidence) if confidence_map is not None else confidence
        )
        session.add(
            FinancialStatementLineItem(
                statement_id=stmt.id,
                line_item_key=row["key"],
                original_label=row["original_label"],
                original_displayed_value=displayed,
                numeric_value=value,
                normalized_value=normalised,
                currency=page_map.get("currency", "PKR"),
                reported_unit=reported_unit,
                normalization_rule=rule,
                page_number=row.get("page"),
                extraction_method=method,
                extraction_confidence=row_conf,
                quality_status="UNVERIFIED",
                is_derived=False,
                version_number=1,
                is_current=True,
            )
        )
        n += 1
    return stmt, n, False
