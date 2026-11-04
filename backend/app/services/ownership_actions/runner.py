"""Phase 12 runner: ownership + actions + rules + breadth + liquidity.

--dry-run computes everything and writes nothing; --commit writes and
a second --commit writes 0 new rows. Ownership and dividend actions
come from seed data verified against already-stored documents (HUBC
annual report, Phase 7 statement faces). Breadth and liquidity come
from stored Phase 5 prices only. No HTTP fetch, no DPS download, no
PSX announcement collection anywhere in this module.

Investor flows are intentionally unwritten: no verified published
flow series was loaded, and flows are never derived from price or
volume.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.governance import DataSource
from app.models.market import MarketPrice
from app.models.ownership_actions import (
    AdjustmentRule,
    CorporateActionRecord,
    LiquidityObservation,
    MarketBreadth,
    OwnershipHolding,
)
from app.models.reference import Company, Sector, Security
from app.services.ownership_actions import (
    ADJUSTMENT_RULES,
    CATEGORY_ROWS,
    DATE_EVIDENCE,
    DIVIDEND_ACTIONS,
    KEY_HOLDERS,
    PUBLICATION_DATE,
    PUBLICATION_NOTE,
    REPORTING_DATE,
    SOURCE_EVIDENCE,
    SOURCE_KEY,
)
from app.services.ownership_actions.breadth import compute_breadth, compute_liquidity

PKT = ZoneInfo("Asia/Karachi")
PRICE_SOURCE_KEY = "dps_market_summary_2026-11-03"


def _company_id_by_ticker(session: Session, ticker: str) -> int:
    row = session.query(Security).filter_by(ticker=ticker).one_or_none()
    if row is None:
        raise ValueError(f"unknown ticker {ticker}")
    return row.company_id


def _data_source(session: Session, key: str):
    return session.query(DataSource).filter_by(source_key=key).one_or_none()


def run_ownership(session: Session, commit: bool) -> dict:
    now = datetime.now(PKT)
    hubc_ds = _data_source(session, SOURCE_KEY)
    price_ds = _data_source(session, PRICE_SOURCE_KEY)

    report = {
        "ownership_inserted": 0,
        "ownership_skipped": 0,
        "actions_inserted": 0,
        "actions_skipped": 0,
        "rules_inserted": 0,
        "rules_skipped": 0,
        "breadth_inserted": 0,
        "breadth_skipped": 0,
        "liquidity_inserted": 0,
        "liquidity_skipped": 0,
        "flows_inserted": 0,
        "flows_note": "No flow rows written: no verified published flow series "
        "loaded; flows are never derived from price/volume.",
        "trading_date": None,
        "priced": 0,
        "universe": 0,
    }

    # ---- ownership: HUBC categories + key holders + totals -----------
    hubc_id = _company_id_by_ticker(session, "HUBC")
    source_ts = datetime(REPORTING_DATE.year, REPORTING_DATE.month, REPORTING_DATE.day, tzinfo=PKT)
    ownership_rows = []
    for category, holders, shares, pct in CATEGORY_ROWS:
        ownership_rows.append(
            {
                "company_id": hubc_id,
                "holder_category": category,
                "holder_name": None,
                "folio": None,
                "shareholders_count": holders,
                "shares_held": shares,
                "percentage": Decimal(pct) if pct is not None else None,
                "is_total": False,
            }
        )
    for category, name, folio, shares in KEY_HOLDERS:
        ownership_rows.append(
            {
                "company_id": hubc_id,
                "holder_category": category,
                "holder_name": name,
                "folio": folio,
                "shareholders_count": None,
                "shares_held": shares,
                "percentage": None,
                "is_total": False,
            }
        )
    ownership_rows.append(
        {
            "company_id": hubc_id,
            "holder_category": "TOTAL",
            "holder_name": None,
            "folio": None,
            "shareholders_count": 80377,
            "shares_held": 1297154387,
            "percentage": Decimal("100.00"),
            "is_total": True,
        }
    )
    for row in ownership_rows:
        existing = (
            session.query(OwnershipHolding)
            .filter_by(
                company_id=row["company_id"],
                holder_category=row["holder_category"],
                holder_name=row["holder_name"],
                folio=row["folio"],
                reporting_date=REPORTING_DATE,
            )
            .one_or_none()
        )
        if existing is not None:
            report["ownership_skipped"] += 1
            continue
        report["ownership_inserted"] += 1
        if commit:
            session.add(
                OwnershipHolding(
                    company_id=row["company_id"],
                    holder_category=row["holder_category"],
                    holder_name=row["holder_name"],
                    folio=row["folio"],
                    reporting_date=REPORTING_DATE,
                    publication_date=PUBLICATION_DATE,
                    publication_date_note=PUBLICATION_NOTE,
                    shareholders_count=row["shareholders_count"],
                    shares_held=row["shares_held"],
                    percentage=row["percentage"],
                    is_total=row["is_total"],
                    source_evidence=SOURCE_EVIDENCE,
                    data_source_id=hubc_ds.id if hubc_ds else None,
                    source_key=SOURCE_KEY,
                    source_timestamp=source_ts,
                    collected_at=now,
                    quality_status="UNVERIFIED",
                )
            )

    # ---- corporate actions: dividends ---------------------------------
    for ticker, action_type, fy_label, dps, total_note, evidence in DIVIDEND_ACTIONS:
        company_id = _company_id_by_ticker(session, ticker)
        existing = (
            session.query(CorporateActionRecord)
            .filter_by(
                company_id=company_id,
                action_type=action_type,
                fiscal_year_label=fy_label,
                amount_per_share=Decimal(dps),
            )
            .one_or_none()
        )
        if existing is not None:
            report["actions_skipped"] += 1
            continue
        report["actions_inserted"] += 1
        if commit:
            session.add(
                CorporateActionRecord(
                    company_id=company_id,
                    action_type=action_type,
                    fiscal_year_label=fy_label,
                    amount_per_share=Decimal(dps),
                    currency="PKR",
                    total_amount=None,
                    total_amount_note=total_note,
                    announced_date=None,
                    ex_date=None,
                    record_date=None,
                    effective_date=None,
                    payment_date=None,
                    date_evidence=DATE_EVIDENCE,
                    status="appropriated",
                    source_evidence=evidence,
                    data_source_id=hubc_ds.id if hubc_ds else None,
                    source_key=SOURCE_KEY,
                    source_timestamp=source_ts,
                    collected_at=now,
                    quality_status="UNVERIFIED",
                )
            )

    # ---- adjustment rules ----------------------------------------------
    for rule in ADJUSTMENT_RULES:
        existing = session.query(AdjustmentRule).filter_by(rule_key=rule["rule_key"]).one_or_none()
        if existing is not None:
            report["rules_skipped"] += 1
            continue
        report["rules_inserted"] += 1
        if commit:
            session.add(
                AdjustmentRule(
                    rule_key=rule["rule_key"],
                    action_type=rule["action_type"],
                    formula=rule["formula"],
                    requires=rule["requires"],
                    description=rule["description"],
                    application_status=rule["application_status"],
                )
            )

    # ---- breadth + liquidity from stored prices ------------------------
    trading_dates = [row[0] for row in session.query(MarketPrice.trading_date).distinct().all()]
    if not trading_dates:
        report["breadth_note"] = "No price rows exist; breadth not computed."
        return report
    trading_date: date = max(trading_dates)
    report["trading_date"] = str(trading_date)
    sectors = {row.id: row.name for row in session.query(Sector).all()}
    securities = session.query(Security).all()
    company_sector_id = {row.id: row.sector_id for row in session.query(Company).all()}
    company_sector = {
        sec.company_id: sectors.get(company_sector_id.get(sec.company_id), "UNKNOWN")
        for sec in securities
    }
    universe = [
        {"ticker": sec.ticker, "sector": company_sector.get(sec.company_id, "UNKNOWN")}
        for sec in securities
    ]
    price_rows = (
        session.query(MarketPrice, Security)
        .join(Security, Security.id == MarketPrice.security_id)
        .filter(MarketPrice.trading_date == trading_date)
        .all()
    )
    priced = [
        {
            "ticker": sec.ticker,
            "sector": company_sector.get(sec.company_id, "UNKNOWN"),
            "volume": mp.volume,
        }
        for mp, sec in price_rows
    ]
    report["priced"] = len(priced)
    report["universe"] = len(universe)

    price_ts = datetime(trading_date.year, trading_date.month, trading_date.day, tzinfo=PKT)
    for metric in compute_breadth(priced, universe):
        existing = (
            session.query(MarketBreadth)
            .filter_by(
                trading_date=trading_date, scope=metric["scope"], metric_key=metric["metric_key"]
            )
            .one_or_none()
        )
        if existing is not None:
            report["breadth_skipped"] += 1
            continue
        report["breadth_inserted"] += 1
        if commit:
            session.add(
                MarketBreadth(
                    trading_date=trading_date,
                    scope=metric["scope"],
                    metric_key=metric["metric_key"],
                    metric_value=metric["value"],
                    numerator=metric["numerator"],
                    denominator=metric["denominator"],
                    status=metric["status"],
                    coverage_note=metric["note"],
                    data_source_id=price_ds.id if price_ds else None,
                    source_key=PRICE_SOURCE_KEY,
                    source_timestamp=price_ts,
                    collected_at=now,
                    quality_status="UNVERIFIED",
                )
            )
    sec_ids = {sec.ticker: sec.id for sec in securities}
    for obs in compute_liquidity(priced):
        existing = (
            session.query(LiquidityObservation)
            .filter_by(
                trading_date=trading_date, scope_key=obs["scope_key"], metric_key=obs["metric_key"]
            )
            .one_or_none()
        )
        if existing is not None:
            report["liquidity_skipped"] += 1
            continue
        report["liquidity_inserted"] += 1
        if commit:
            ticker = obs["scope_key"][4:] if obs["scope_key"].startswith("SEC:") else None
            session.add(
                LiquidityObservation(
                    trading_date=trading_date,
                    scope_key=obs["scope_key"],
                    security_id=sec_ids.get(ticker) if ticker else None,
                    metric_key=obs["metric_key"],
                    metric_value=obs["value"],
                    status=obs["status"],
                    coverage_note=obs["note"],
                    data_source_id=price_ds.id if price_ds else None,
                    source_key=PRICE_SOURCE_KEY,
                    source_timestamp=price_ts,
                    collected_at=now,
                    quality_status="UNVERIFIED",
                )
            )
    if commit:
        session.flush()
    return report
