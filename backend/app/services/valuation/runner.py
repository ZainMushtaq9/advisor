"""Phase 9 run orchestration (mirrors Phase 8 runner.py).

Reads ONLY already-committed Phase 7 statement rows, Phase 8
period configuration, and Phase 5 price rows. Writes nothing in
dry-run mode. In commit mode it writes, idempotently, one Valuation
row per (security, valuation_date, method): estimated_value, or NULL
with computation_status 'insufficient_inputs' / 'not_applicable' in
the assumptions JSON plus the exact reason. A second --commit writes
0 new rows (skipped_existing) — the idempotency guard. All written
rows are UNVERIFIED: calculation never upgrades input quality. No
row is ever updated or deleted; a correction is a new method version.

Valuation dates: PRICE_DATE (2026-11-03) for price-based and
assumption-gated methods; the balance-sheet date for statement-date
methods (book value, sum-of-parts). HBL gets no rows (pending).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.analysis import Valuation
from app.models.financial import FinancialStatement
from app.models.market import MarketPrice
from app.models.reference import Company, Sector, Security
from app.services.fundamental_analysis import (
    KEY_MAPS,
    PERIODS,
)
from app.services.fundamental_analysis.runner import load_period_inputs
from app.services.valuation import (
    PENDING_COMPANIES,
    PRICE_DATE,
    STATEMENT_DATE_METHODS,
    VALUATION_VERSION,
    coverage,
)
from app.services.valuation import peers as peer_engine

SOURCE_KEY = "phase09-valuation-v1.0"


def _parse(d: str) -> date:
    return date.fromisoformat(d)


def _security_for(session: Session, company_id: int) -> Security | None:
    return (
        session.query(Security)
        .filter(Security.company_id == company_id)
        .order_by(Security.id)
        .first()
    )


def _sector_name(session: Session, company_id: int) -> str | None:
    company = session.query(Company).filter(Company.id == company_id).first()
    if company is None or company.sector_id is None:
        return None
    sector = session.query(Sector).filter(Sector.id == company.sector_id).first()
    return sector.name if sector else None


def _income_publication_date(
    session: Session, company_id: int, period_start: str, period_end: str, frequency: str
) -> date | None:
    row = (
        session.query(FinancialStatement)
        .filter(
            FinancialStatement.company_id == company_id,
            FinancialStatement.statement_type == "income",
            FinancialStatement.period_start == _parse(period_start),
            FinancialStatement.period_end == _parse(period_end),
            FinancialStatement.reporting_frequency == frequency,
            FinancialStatement.statement_scope.is_(None),
            FinancialStatement.is_current.is_(True),
        )
        .first()
    )
    return row.publication_date if row else None


def load_valuation_inputs(session: Session, company_id: int) -> dict:
    """Build the canonical input dict for one company.

    Reuses Phase 8's load_period_inputs for statement faces (same
    period discipline, same key maps), then adds the price row, the
    income statement's publication date, the sector, and the peer
    set. Raises ValueError when the company has no configured period
    (it is then reported as pending/unknown, never fabricated).
    """
    if company_id not in PERIODS:
        raise ValueError(f"no configured company-period for company {company_id}")
    cfg = PERIODS[company_id]
    keymap = KEY_MAPS[company_id]
    inputs, stmt_ids, notes = load_period_inputs(session, company_id)

    (fs, fe, freq) = cfg["flow_current"]
    eps = inputs.get("eps_cur")
    total_equity = inputs.get("te_cur")
    owners_equity = inputs.get("oe_cur")
    bs_date = _parse(cfg["bs_current"])

    security = _security_for(session, company_id)
    price = None
    price_id = None
    if security is not None:
        prow = (
            session.query(MarketPrice)
            .filter(
                MarketPrice.security_id == security.id,
                MarketPrice.trading_date == PRICE_DATE,
            )
            .first()
        )
        if prow is not None:
            price = Decimal(str(prow.close_price)) if prow.close_price is not None else None
            price_id = prow.id

    publication = _income_publication_date(session, company_id, fs, fe, freq)

    # Peer candidates: the other configured statement companies.
    sector = _sector_name(session, company_id)
    target = {
        "ticker": security.ticker if security else None,
        "sector": sector,
        "reporting_frequency": freq,
        "period_end": _parse(fe),
    }
    candidates = []
    for other_id, other_cfg in PERIODS.items():
        if other_id == company_id:
            continue
        other_sec = _security_for(session, other_id)
        (ofs, ofe, ofreq) = other_cfg["flow_current"]
        candidates.append(
            {
                "ticker": other_sec.ticker if other_sec else None,
                "sector": _sector_name(session, other_id),
                "reporting_frequency": ofreq,
                "period_end": _parse(ofe),
            }
        )
    peer_list = peer_engine.select_peers(target, candidates)

    return {
        "company_id": company_id,
        "ticker": security.ticker if security else None,
        "security_id": security.id if security else None,
        "sector": sector,
        "flow_frequency": freq,
        "period_end": _parse(fe),
        "bs_date": bs_date,
        "price": price,
        "price_id": price_id,
        "price_date": PRICE_DATE,
        "eps": eps,
        "eps_period_label": cfg["label"],
        "publication_date": publication,
        "total_equity": total_equity,
        "owners_equity": owners_equity,
        "peers": peer_list,
        "statement_ids": stmt_ids,
        "price_ids": [price_id] if price_id is not None else [],
        "notes": notes,
        "keymap_eps_key": keymap.get("eps"),
    }


def run_valuation(
    session: Session,
    company_ids: list[int] | None = None,
    dry_run: bool = True,
) -> dict:
    """Assess every method for each company; commit unless dry-run."""
    ids = company_ids if company_ids is not None else sorted(PERIODS)
    companies: dict[str, dict] = {}
    totals = {"rows": 0, "computed": 0, "insufficient": 0, "not_applicable": 0}
    written = 0
    skipped = 0
    for company_id in ids:
        if company_id in PENDING_COMPANIES:
            companies[str(company_id)] = {
                "status": "pending",
                "reason": PENDING_COMPANIES[company_id],
                "methods": [],
            }
            continue
        inputs = load_valuation_inputs(session, company_id)
        verdicts = coverage.assess(company_id, inputs)
        entries = []
        for verdict in verdicts:
            method_key = verdict["method_key"]
            status = verdict["status"]
            totals["rows"] += 1
            if status == "computed":
                totals["computed"] += 1
            elif status == "not_applicable":
                totals["not_applicable"] += 1
            else:
                totals["insufficient"] += 1
            if method_key in STATEMENT_DATE_METHODS:
                valuation_date = inputs["bs_date"]
            else:
                valuation_date = PRICE_DATE
            entry = {
                "method": method_key,
                "status": status,
                "value": verdict["value"],
                "reason": verdict["reason"],
                "flags": verdict["flags"],
                "sensitivity": verdict["sensitivity"],
                "valuation_date": valuation_date,
            }
            entries.append(entry)
            if dry_run or inputs["security_id"] is None:
                continue
            existing = (
                session.query(Valuation)
                .filter(
                    Valuation.security_id == inputs["security_id"],
                    Valuation.valuation_date == valuation_date,
                    Valuation.method == method_key,
                )
                .first()
            )
            if existing is not None:
                skipped += 1
                continue
            sensitivity = verdict["sensitivity"] or {}
            row = Valuation(
                security_id=inputs["security_id"],
                valuation_date=valuation_date,
                method=method_key,
                estimated_value=verdict["value"],
                value_low=sensitivity.get("price_minus_10pct"),
                value_high=sensitivity.get("price_plus_10pct"),
                assumptions={
                    "method_version": VALUATION_VERSION,
                    "computation_status": status,
                    "reason": verdict["reason"],
                    "flags": verdict["flags"],
                    "sensitivity": {
                        k: (str(v) if v is not None else None) for k, v in sensitivity.items()
                    }
                    if sensitivity
                    else None,
                    "inputs": {
                        "price": str(inputs["price"]) if inputs["price"] is not None else None,
                        "price_date": str(PRICE_DATE),
                        "eps": str(inputs["eps"]) if inputs["eps"] is not None else None,
                        "eps_key": inputs["keymap_eps_key"],
                        "publication_date": str(inputs["publication_date"])
                        if inputs["publication_date"] is not None
                        else None,
                        "bs_date": str(inputs["bs_date"]),
                        "sector": inputs["sector"],
                        "peers": [p.get("ticker") for p in inputs["peers"]],
                    },
                },
                input_statement_ids=inputs["statement_ids"],
                input_price_ids=inputs["price_ids"],
                source_key=SOURCE_KEY,
                quality_status="UNVERIFIED",
            )
            session.add(row)
            written += 1
        companies[inputs["ticker"] or str(company_id)] = {
            "status": "assessed",
            "company_id": company_id,
            "ticker": inputs["ticker"],
            "methods": entries,
        }
    if not dry_run:
        session.commit()
    return {
        "valuation_version": VALUATION_VERSION,
        "price_date": str(PRICE_DATE),
        "dry_run": dry_run,
        "totals": totals,
        "written": written,
        "skipped_existing": skipped,
        "companies": companies,
    }
