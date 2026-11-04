"""Phase 8 run orchestration (mirrors Phase 6 runner.py).

Reads ONLY already-committed Phase 7 statement rows. Writes nothing
in dry-run mode. In commit mode it writes, idempotently:
  * one FundamentalMetricValue row per (company, metric, period_end,
    calculation_version 1.0) — value, or NULL with
    computation_status 'insufficient_inputs' / 'not_applicable';
  * one FinancialHealthAssessment row per (company, period_end,
    category, health-v1) — score, or NULL for insufficient data;
  * one FundamentalWarningEvent row per (company, event_date,
    warning_type);
  * one SectorMetricProfile row per (sector, metric_key) for the
    three computed sectors (HBL's COMMERCIAL BANKS gets no profile
    until its statements exist).
A second --commit writes 0 new rows (skipped_existing) — the
idempotency guard. All written rows are UNVERIFIED: calculation
never upgrades input quality. No row is ever updated or deleted;
a correction is a new calculation_version.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.analysis import (
    FinancialHealthAssessment,
    FundamentalWarningEvent,
    SectorMetricProfile,
)
from app.models.financial import (
    FinancialStatement,
    FinancialStatementLineItem,
    FundamentalMetricDefinition,
    FundamentalMetricValue,
)
from app.models.reference import Company, Sector, Security
from app.services.fundamental_analysis import (
    CALCULATION_VERSION,
    HEALTH_METHOD_VERSION,
    KEY_MAPS,
    METRICS,
    PENDING_COMPANIES,
    PERIODS,
    coverage,
    formulas,
    health,
    warnings,
)

RUN_KEY_PREFIX = "phase08-fundamental"


def _parse(d: str) -> date:
    return date.fromisoformat(d)


def _load_face(
    session: Session,
    company_id: int,
    statement_type: str,
    period_end: str,
    period_start: str | None = None,
    frequency: str | None = None,
):
    """Load one face: (values dict key -> Decimal, statement id).

    Balance-sheet faces match by period_end only (their period_start
    is the fiscal-year start of the comparative column, not the flow
    window). Flow faces match by (period_start, period_end, frequency).
    Ordinary faces have statement_scope NULL. Returns (values, stmt_id)
    or ({}, None) when the face does not exist.
    """
    q = session.query(FinancialStatement).filter(
        FinancialStatement.company_id == company_id,
        FinancialStatement.statement_type == statement_type,
        FinancialStatement.period_end == _parse(period_end),
        FinancialStatement.statement_scope.is_(None),
        FinancialStatement.is_current.is_(True),
    )
    if period_start is not None:
        q = q.filter(FinancialStatement.period_start == _parse(period_start))
    if frequency is not None:
        q = q.filter(FinancialStatement.reporting_frequency == frequency)
    rows = q.all()
    if not rows:
        return {}, None
    if len(rows) > 1:
        raise ValueError(
            f"multiple current {statement_type} faces for company {company_id} "
            f"period_end={period_end} (data grain violation)"
        )
    stmt = rows[0]
    items = (
        session.query(FinancialStatementLineItem)
        .filter(FinancialStatementLineItem.statement_id == stmt.id)
        .all()
    )
    values = {}
    for li in items:
        if li.normalized_value is not None:
            values[li.line_item_key] = Decimal(str(li.normalized_value))
    return values, stmt.id


def _sum_keys(face: dict, keys: tuple[str, ...]) -> tuple[Decimal | None, bool]:
    """Sum present keys; (None, False) when none present; partial flag
    when some but not all present."""
    present = [face[k] for k in keys if face.get(k) is not None]
    if not present:
        return None, False
    total = present[0]
    for v in present[1:]:
        total += v
    return total, len(present) < len(keys)


def load_period_inputs(session: Session, company_id: int) -> tuple[dict, list[int], list[str]]:
    """Build the canonical input dict for one company-period."""
    cfg = PERIODS[company_id]
    keymap = KEY_MAPS[company_id]
    (fs, fe, freq) = cfg["flow_current"]
    (ps, pe, pfreq) = cfg["flow_prior"]
    inc_cur, id1 = _load_face(session, company_id, "income", fe, fs, freq)
    inc_prior, id2 = _load_face(session, company_id, "income", pe, ps, pfreq)
    cf_cur, id3 = _load_face(session, company_id, "cash_flow", fe, fs, freq)
    cf_prior, id4 = _load_face(session, company_id, "cash_flow", pe, ps, pfreq)
    bs_cur, id5 = _load_face(session, company_id, "balance_sheet", cfg["bs_current"])
    bs_prior, id6 = _load_face(session, company_id, "balance_sheet", cfg["bs_prior"])
    eq_cur, id7 = _load_face(session, company_id, "changes_in_equity", fe, fs, freq)
    stmt_ids = [i for i in (id1, id2, id3, id4, id5, id6, id7) if i is not None]
    notes: list[str] = []

    def pick(face: dict, spec) -> Decimal | None:
        if spec is None:
            return None
        if isinstance(spec, tuple):
            total, partial = _sum_keys(face, spec)
            if partial:
                notes.append(f"partial sum for {spec}: only some keys present")
            return total
        return face.get(spec)

    inputs: dict = {}
    # Flow values.
    inputs["revenue_cur"] = pick(inc_cur, keymap["revenue"])
    inputs["revenue_prior"] = pick(inc_prior, keymap["revenue"])
    inputs["gross_cur"] = pick(inc_cur, keymap["gross_profit"])
    inputs["gross_prior"] = pick(inc_prior, keymap["gross_profit"])
    inputs["op_cur"] = pick(inc_cur, keymap["operating_profit"])
    inputs["op_prior"] = pick(inc_prior, keymap["operating_profit"])
    inputs["fin_cur"] = pick(inc_cur, keymap["finance_cost"])
    inputs["fin_prior"] = pick(inc_prior, keymap["finance_cost"])
    inputs["pat_cur"] = pick(inc_cur, keymap["pat"])
    inputs["pat_prior"] = pick(inc_prior, keymap["pat"])
    inputs["owners_profit_cur"] = pick(eq_cur, keymap["owners_profit"])
    inputs["eps_cur"] = pick(inc_cur, keymap["eps"])
    inputs["eps_prior"] = pick(inc_prior, keymap["eps"])
    inputs["ocf_cur"] = pick(cf_cur, keymap["ocf"])
    inputs["ocf_prior"] = pick(cf_prior, keymap["ocf"])
    inputs["capex_cur"] = pick(cf_cur, keymap["capex"])
    div = pick(cf_cur, keymap["dividends"])
    inputs["div_cur"] = div
    # Cost: printed line, or OGDC's exact derivation.
    cost_cur = pick(inc_cur, keymap["cost"])
    if cost_cur is None and keymap["cost"] is None:
        rev, gross = inputs["revenue_cur"], inputs["gross_cur"]
        if rev is not None and gross is not None:
            cost_cur = rev - gross
            inputs["cost_derived"] = True
            notes.append("cost derived exactly as sales_net - gross_profit (no printed cost line)")
    inputs["cost_cur"] = cost_cur
    cost_prior = pick(inc_prior, keymap["cost"])
    if cost_prior is None and keymap["cost"] is None:
        rev, gross = inputs["revenue_prior"], inputs["gross_prior"]
        if rev is not None and gross is not None:
            cost_prior = rev - gross
    inputs["cost_prior"] = cost_prior
    # Balance-sheet points.
    inputs["ca_cur"] = pick(bs_cur, keymap["current_assets"])
    inputs["cl_cur"] = pick(bs_cur, keymap["current_liabilities"])
    inputs["cash_cur"] = pick(bs_cur, keymap["cash"])
    inputs["inv_cur"] = pick(bs_cur, keymap["inventory"])
    inputs["inv_prior"] = pick(bs_prior, keymap["inventory"])
    inputs["td_cur"] = pick(bs_cur, keymap["trade_debts"])
    inputs["td_prior"] = pick(bs_prior, keymap["trade_debts"])
    inputs["pay_cur"] = pick(bs_cur, keymap["payables"])
    inputs["pay_prior"] = pick(bs_prior, keymap["payables"])
    inputs["ta_cur"] = pick(bs_cur, keymap["total_assets"])
    inputs["ta_prior"] = pick(bs_prior, keymap["total_assets"])
    inputs["te_cur"] = pick(bs_cur, keymap["total_equity"])
    inputs["te_prior"] = pick(bs_prior, keymap["total_equity"])
    inputs["oe_cur"] = pick(bs_cur, keymap["owners_equity"])
    inputs["oe_prior"] = pick(bs_prior, keymap["owners_equity"])
    inputs["ib_cur"] = pick(bs_cur, keymap["ib_debt"])
    inputs["ib_prior"] = pick(bs_prior, keymap["ib_debt"])
    # Total liabilities: printed, or HUBC's exact derivation.
    tl_cur = pick(bs_cur, keymap["total_liabilities"])
    if tl_cur is None and keymap["total_liabilities"] is None:
        if inputs["ta_cur"] is not None and inputs["te_cur"] is not None:
            tl_cur = inputs["ta_cur"] - inputs["te_cur"]
            notes.append("total_liabilities derived exactly as total_assets - total_equity")
    inputs["tl_cur"] = tl_cur
    tl_prior = pick(bs_prior, keymap["total_liabilities"])
    if tl_prior is None and keymap["total_liabilities"] is None:
        if inputs["ta_prior"] is not None and inputs["te_prior"] is not None:
            tl_prior = inputs["ta_prior"] - inputs["te_prior"]
    inputs["tl_prior"] = tl_prior
    inputs["period_days"] = formulas.period_days(_parse(fs), _parse(fe))
    inputs["period_end"] = fe
    return inputs, stmt_ids, notes


def _sector_applicability(sector_name: str, metric_key: str) -> str:
    """Short per-sector applicability note (see sector_profiles.md)."""
    if sector_name == "OIL & GAS EXPLORATION COMPANIES":
        if metric_key == "interest_coverage":
            return "NOT APPLICABLE by structure: no finance-cost line, lease-only debt."
        if metric_key in ("operating_margin", "roce"):
            return "NOT AVAILABLE: no operating-profit line in extracted statements."
        if metric_key == "ib_debt_to_equity":
            return "Lease liabilities only — not comparable to loan-funded peers."
        if metric_key == "receivables_days":
            return "Includes settlement receivables; interpret with sector context."
    if sector_name == "POWER GENERATION & DISTRIBUTION":
        if metric_key == "receivables_days":
            return "Settlement receivables (offtaker); interpret as settlement lag."
        if metric_key == "inventory_days":
            return "Low relevance: fuel and stores only, no finished-goods stock."
    if sector_name == "TEXTILE COMPOSITE":
        if metric_key == "inventory_days":
            return "Primary working-capital metric: large raw/cotton stock."
    return "Applicable."


def run_analysis(
    session: Session, company_ids: list[int] | None = None, dry_run: bool = True
) -> dict:
    """Assess every configured company-period; write only when committed."""
    targets = company_ids or sorted(PERIODS)
    report: dict = {
        "run_key": f"{RUN_KEY_PREFIX}-{CALCULATION_VERSION}",
        "dry_run": dry_run,
        "companies": {},
        "pending_companies": {str(cid): reason for cid, reason in PENDING_COMPANIES.items()},
        "values_written": 0,
        "values_skipped_existing": 0,
        "health_written": 0,
        "health_skipped_existing": 0,
        "warnings_written": 0,
        "warnings_skipped_existing": 0,
        "profiles_written": 0,
        "profiles_skipped_existing": 0,
    }
    # Seed metric definitions (idempotent by metric_key).
    defs: dict[str, FundamentalMetricDefinition] = {}
    for key, (category, formula_text, unit) in METRICS.items():
        row = session.query(FundamentalMetricDefinition).filter_by(metric_key=key).one_or_none()
        if row is None:
            row = FundamentalMetricDefinition(
                metric_key=key,
                category=category,
                formula_text=formula_text,
                formula_version=CALCULATION_VERSION,
                unit=unit,
            )
            session.add(row)
            session.flush()
        defs[key] = row
    if not dry_run:
        session.flush()

    for cid in targets:
        cfg = PERIODS[cid]
        company = session.query(Company).filter_by(id=cid).one_or_none()
        # Securities carry the ticker (companies are issuers, not tickers).
        sec = (
            session.query(Security).filter(Security.company_id == cid).order_by(Security.id).first()
        )
        ticker = sec.ticker if sec is not None else str(cid)
        try:
            inputs, stmt_ids, notes = load_period_inputs(session, cid)
        except ValueError as exc:
            report["companies"][ticker] = {"status": "error", "error": str(exc)}
            continue
        if not stmt_ids:
            report["companies"][ticker] = {
                "status": "no_inputs",
                "error": "no current statements found",
            }
            continue
        results = coverage.assess(cid, inputs)
        values = {r["metric_key"]: r["value"] for r in results}
        flags = {r["metric_key"]: r.get("flags", []) for r in results}
        health_scores = health.score_dimensions(values, flags)
        warn_inputs = dict(values)
        warn_inputs["_pat_cur"] = inputs.get("pat_cur")
        warn_inputs["_ocf_cur"] = inputs.get("ocf_cur")
        warn_list = warnings.build_warnings(warn_inputs, results)
        period_end = _parse(cfg["flow_current"][1])
        entry = {
            "status": "assessed",
            "period_label": cfg["label"],
            "period_end": str(period_end),
            "period_days": inputs["period_days"],
            "statement_ids": stmt_ids,
            "loader_notes": notes,
            "computed": sum(1 for r in results if r["status"] == "computed"),
            "insufficient_inputs": sum(1 for r in results if r["status"] == "insufficient_inputs"),
            "not_applicable": sum(1 for r in results if r["status"] == "not_applicable"),
            "metrics": [
                {
                    "metric_key": r["metric_key"],
                    "status": r["status"],
                    "value": str(r["value"]) if r["value"] is not None else None,
                    "reason": r["reason"],
                    "flags": r["flags"],
                }
                for r in results
            ],
            "health": {
                cat: {
                    "score": str(v["score"]) if v["score"] is not None else None,
                    "evidence": v["evidence"],
                }
                for cat, v in health_scores.items()
            },
            "warnings": warn_list,
        }
        if not dry_run:
            for r in results:
                existing = (
                    session.query(FundamentalMetricValue)
                    .filter_by(
                        company_id=cid,
                        metric_definition_id=defs[r["metric_key"]].id,
                        period_end=period_end,
                        calculation_version=CALCULATION_VERSION,
                    )
                    .one_or_none()
                )
                if existing is not None:
                    report["values_skipped_existing"] += 1
                    continue
                session.add(
                    FundamentalMetricValue(
                        company_id=cid,
                        metric_definition_id=defs[r["metric_key"]].id,
                        period_end=period_end,
                        value=r["value"],
                        calculation_version=CALCULATION_VERSION,
                        input_statement_ids=stmt_ids,
                        computation_status=(
                            "computed" if r["status"] == "computed" else r["status"]
                        ),
                        quality_status="UNVERIFIED",
                    )
                )
                report["values_written"] += 1
            for cat, v in health_scores.items():
                existing = (
                    session.query(FinancialHealthAssessment)
                    .filter_by(
                        company_id=cid,
                        period_end=period_end,
                        category=cat,
                        scoring_method_version=HEALTH_METHOD_VERSION,
                    )
                    .one_or_none()
                )
                if existing is not None:
                    report["health_skipped_existing"] += 1
                    continue
                session.add(
                    FinancialHealthAssessment(
                        company_id=cid,
                        period_end=period_end,
                        category=cat,
                        score=v["score"],
                        scoring_method_version=HEALTH_METHOD_VERSION,
                        evidence=v["evidence"],
                        quality_status="UNVERIFIED",
                    )
                )
                report["health_written"] += 1
            for w in warn_list:
                existing = (
                    session.query(FundamentalWarningEvent)
                    .filter_by(
                        company_id=cid,
                        event_date=period_end,
                        warning_type=w["warning_type"],
                    )
                    .one_or_none()
                )
                if existing is not None:
                    report["warnings_skipped_existing"] += 1
                    continue
                session.add(
                    FundamentalWarningEvent(
                        company_id=cid,
                        event_date=period_end,
                        warning_type=w["warning_type"],
                        severity=w["severity"],
                        evidence=w["evidence"],
                        quality_status="UNVERIFIED",
                    )
                )
                report["warnings_written"] += 1
            # Sector profiles for this company's sector.
            if company is not None and getattr(company, "sector_id", None):
                sector = session.query(Sector).filter_by(id=company.sector_id).one_or_none()
                sector_name = sector.name if sector is not None else ""
                for key in METRICS:
                    existing = (
                        session.query(SectorMetricProfile)
                        .filter_by(sector_id=company.sector_id, metric_key=key)
                        .one_or_none()
                    )
                    if existing is not None:
                        report["profiles_skipped_existing"] += 1
                        continue
                    session.add(
                        SectorMetricProfile(
                            sector_id=company.sector_id,
                            metric_key=key,
                            applicability=_sector_applicability(sector_name, key),
                            source_requirements=(
                                "Phase 7 statements for a company in this sector "
                                "plus the Phase 4 registry sector"
                            ),
                            is_active=True,
                        )
                    )
                    report["profiles_written"] += 1
        report["companies"][ticker] = entry
    if not dry_run:
        session.commit()
    return report
