"""Phase 29 independent recomputations: direct queries + Decimal
arithmetic, never the phase service code that produced the values.

Each check returns a dict with check_key, claimed_value,
recomputed_value, matches, tolerance, and method. A mismatch row is
kept, not deleted: it is the audit finding. Two checks are EXPECTED
to mismatch (the recovery #6 intermediate-state artifacts, defect
D-05); the runner records them as findings, and the verdict follows
from the gate evaluation, not from hiding them.

Tolerances: exact for counts and integer money values; 1e-6 for
ratios and multiples stored at 6 decimal places; 0.01 for portfolio
money values (stored at 2 decimal places in the Phase 16 report).
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text

PRICE_DATE = "2026-11-03"


def _dec(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _one(session, sql: str, **params):
    row = session.execute(text(sql), params).first()
    return row[0] if row is not None else None


def _company_id(session, ticker: str):
    return _one(
        session,
        "SELECT c.id FROM companies c JOIN securities s ON s.company_id = c.id "
        "WHERE s.ticker = :ticker",
        ticker=ticker,
    )


def _security_id(session, ticker: str):
    return _one(
        session,
        "SELECT id FROM securities WHERE ticker = :ticker",
        ticker=ticker,
    )


def _line_item(
    session,
    ticker: str,
    statement_type: str,
    period_end: str,
    key: str,
    period_start: str | None = None,
):
    sql = (
        "SELECT li.numeric_value FROM financial_statement_line_items li "
        "JOIN financial_statements fs ON fs.id = li.statement_id "
        "JOIN companies c ON c.id = fs.company_id "
        "JOIN securities s ON s.company_id = c.id "
        "WHERE s.ticker = :ticker AND fs.statement_type = :stype "
        "AND fs.period_end = :pend AND li.line_item_key = :key"
    )
    params: dict = {
        "ticker": ticker,
        "stype": statement_type,
        "pend": period_end,
        "key": key,
    }
    if period_start is not None:
        # Disambiguates cumulative interim columns from standalone
        # quarter columns stored as separate rows (OGDC: six months
        # 2025-07-01→2025-12-31 vs quarter 2025-10-01→2025-12-31).
        sql += " AND fs.period_start = :pstart"
        params["pstart"] = period_start
    return _dec(_one(session, sql, **params))


def _close(session, ticker: str):
    return _dec(
        _one(
            session,
            "SELECT mp.close_price FROM market_prices mp "
            "JOIN securities s ON s.id = mp.security_id "
            "WHERE s.ticker = :ticker AND mp.trading_date = :d",
            ticker=ticker,
            d=PRICE_DATE,
        )
    )


def _stored_valuation(session, ticker: str, method: str):
    return _dec(
        _one(
            session,
            "SELECT v.estimated_value FROM valuations v "
            "JOIN securities s ON s.id = v.security_id "
            "WHERE s.ticker = :ticker AND v.method = :method",
            ticker=ticker,
            method=method,
        )
    )


def _stored_fundamental(session, ticker: str, metric_key: str):
    return _dec(
        _one(
            session,
            "SELECT fmv.value FROM fundamental_metric_values fmv "
            "JOIN fundamental_metric_definitions fmd "
            "ON fmd.id = fmv.metric_definition_id "
            "JOIN companies c ON c.id = fmv.company_id "
            "JOIN securities s ON s.company_id = c.id "
            "WHERE s.ticker = :ticker AND fmd.metric_key = :key",
            ticker=ticker,
            key=metric_key,
        )
    )


def _ratio_match(claimed, recomputed, tol=Decimal("0.000001")) -> bool:
    if claimed is None or recomputed is None:
        return False
    return abs(claimed - recomputed) <= tol


def check_hubc_gross_margin(session):
    claimed = _stored_fundamental(session, "HUBC", "gross_margin")
    gross = _line_item(session, "HUBC", "income", "2026-06-30", "gross_profit")
    revenue = _line_item(session, "HUBC", "income", "2026-06-30", "revenue")
    recomputed = gross / revenue if gross is not None and revenue else None
    return {
        "check_key": "hubc_gross_margin",
        "claimed_value": str(claimed),
        "recomputed_value": str(recomputed),
        "matches": _ratio_match(claimed, recomputed),
        "tolerance": "1e-6 (stored at 6 decimal places)",
        "method": "gross_profit 29,688,160 / revenue 71,126,352 from HUBC "
        "income statement line items (FY2026, period_end 2026-06-30), "
        "compared with the stored fundamental_metric_values row.",
    }


def check_hubc_trailing_pe(session):
    claimed = _stored_valuation(session, "HUBC", "multiples:pe_trailing")
    close = _close(session, "HUBC")
    # Phase 9's own assumptions JSON names eps_key eps_total.
    eps = _line_item(session, "HUBC", "income", "2026-06-30", "eps_total")
    recomputed = close / eps if close is not None and eps else None
    return {
        "check_key": "hubc_trailing_pe",
        "claimed_value": str(claimed),
        "recomputed_value": str(recomputed),
        "matches": _ratio_match(claimed, recomputed),
        "tolerance": "1e-6 (stored at 6 decimal places)",
        "method": "HUBC close 197.24 (2026-11-03) / FY2026 eps_total 38.26 "
        "from the income statement line items, compared with the "
        "stored valuations row (multiples:pe_trailing).",
    }


def check_ogdc_trailing_pe(session):
    claimed = _stored_valuation(session, "OGDC", "multiples:pe_trailing")
    close = _close(session, "OGDC")
    # Six-month cumulative EPS only: period_start 2025-07-01, not
    # the standalone quarter (2025-10-01, 8.07).
    eps = _line_item(session, "OGDC", "income", "2025-12-31", "eps_basic", "2025-07-01")
    recomputed = close / eps if close is not None and eps else None
    return {
        "check_key": "ogdc_trailing_pe",
        "claimed_value": str(claimed),
        "recomputed_value": str(recomputed),
        "matches": _ratio_match(claimed, recomputed),
        "tolerance": "1e-6 (stored at 6 decimal places)",
        "method": "OGDC close 303.63 (2026-11-03) / 6M eps_basic 16.98 "
        "from the income statement line items (period "
        "2025-07-01→2025-12-31), compared with the stored "
        "valuations row. Labelled an interim-period multiple, not a "
        "full-year trailing P/E.",
    }


def check_portfolio_reconciliation(session):
    rows = session.execute(
        text(
            "SELECT p.name, p.capital, h.ticker, h.units, h.value "
            "FROM simulated_portfolio_holdings h "
            "JOIN simulated_portfolios p ON p.id = h.portfolio_id"
        )
    ).fetchall()
    by_portfolio: dict[str, dict] = {}
    for name, capital, ticker, units, value in rows:
        entry = by_portfolio.setdefault(
            name, {"capital": _dec(capital), "stored": Decimal("0"), "recomputed": Decimal("0")}
        )
        entry["stored"] += _dec(value)
        close = _close(session, ticker)
        entry["recomputed"] += _dec(units) * close
    pairs = []
    all_match = True
    for name in sorted(by_portfolio):
        entry = by_portfolio[name]
        cash = entry["capital"] - entry["stored"]
        pairs.append(
            f"{name}: stored {entry['stored']} + cash {cash} = "
            f"{entry['capital']}; recomputed holdings {entry['recomputed']}"
        )
        if abs(entry["stored"] - entry["recomputed"]) > Decimal("0.01"):
            all_match = False
    claimed = (
        "ew_statements_3_balanced 999,473.03 + 526.97; "
        "rule_screen_pass_balanced 999,581.14 + 418.86; "
        "rule_screen_pass_conservative 899,884.10 + 100,115.90; "
        "each = capital 1,000,000 (Phase 16 report)"
    )
    return {
        "check_key": "portfolio_reconciliation",
        "claimed_value": claimed,
        "recomputed_value": "; ".join(pairs),
        "matches": all_match,
        "tolerance": "0.01 (money at 2 decimal places)",
        "method": "Each holding value recomputed as units x 2026-11-03 "
        "close from market_prices, summed per portfolio, and "
        "compared with the stored holding values; residual cash = "
        "capital minus stored invested.",
    }


def check_breadth_coverage(session):
    priced = (
        _one(
            session,
            "SELECT COUNT(DISTINCT security_id) FROM market_prices WHERE trading_date = :d",
            d=PRICE_DATE,
        )
        or 0
    )
    companies = _one(session, "SELECT COUNT(*) FROM companies") or 0
    claimed = "444/470 = 0.944681 (Phase 12 report)"
    recomputed = f"{priced}/{companies} = {priced / companies:.6f}" if companies else "0/0"
    return {
        "check_key": "breadth_coverage",
        "claimed_value": claimed,
        "recomputed_value": recomputed,
        "matches": priced == 444 and companies == 470,
        "tolerance": "exact counts",
        "method": "Distinct priced securities on 2026-11-03 divided by "
        "registry companies, counted directly.",
    }


def check_volume_median(session):
    volumes = [
        _dec(v)
        for (v,) in session.execute(
            text(
                "SELECT volume FROM market_prices WHERE trading_date = :d "
                "AND volume IS NOT NULL ORDER BY volume"
            ),
            {"d": PRICE_DATE},
        ).fetchall()
    ]
    n = len(volumes)
    if n % 2 == 0:
        median = (volumes[n // 2 - 1] + volumes[n // 2]) / 2
    else:
        median = volumes[n // 2]
    return {
        "check_key": "volume_median",
        "claimed_value": "54,631.5 (Phase 12 report)",
        "recomputed_value": f"{median} over {n} volumes",
        "matches": median == Decimal("54631.5") and n == 444,
        "tolerance": "exact",
        "method": "Median of all 444 non-null volumes on 2026-11-03, "
        "computed in Python from the ordered rows.",
    }


def check_top10_volume_share(session):
    rows = session.execute(
        text(
            "SELECT volume FROM market_prices WHERE trading_date = :d "
            "AND volume IS NOT NULL ORDER BY volume DESC"
        ),
        {"d": PRICE_DATE},
    ).fetchall()
    volumes = [_dec(v) for (v,) in rows]
    total = sum(volumes)
    top10 = sum(volumes[:10])
    share = (top10 / total * 100) if total else None
    return {
        "check_key": "top10_volume_share",
        "claimed_value": "49.249694% (Phase 12 report)",
        "recomputed_value": f"{share:.6f}% (top-10 {top10} / total {total})"
        if share is not None
        else "no volumes",
        "matches": share is not None and abs(share - Decimal("49.249694")) <= Decimal("0.000001"),
        "tolerance": "1e-6 percentage points",
        "method": "Top-10 volumes divided by total volume on 2026-11-03, "
        "computed in Python from the ordered rows.",
    }


def _hbl_identity(session, period_end: str):
    assets = _line_item(session, "HBL", "balance_sheet", period_end, "total_assets")
    liabilities = _line_item(session, "HBL", "balance_sheet", period_end, "total_liabilities")
    equity = _line_item(session, "HBL", "balance_sheet", period_end, "total_equity")
    total = (liabilities + equity) if liabilities is not None and equity else None
    return assets, liabilities, equity, total


def check_hbl_sfp_identity_2025(session):
    assets, liabilities, equity, total = _hbl_identity(session, "2025-12-31")
    return {
        "check_key": "hbl_sfp_identity_2025",
        "claimed_value": "assets 7,708,144,220 = liabilities 7,219,529,515 + equity 488,614,705",
        "recomputed_value": f"assets {assets} vs liabilities + equity {total} "
        f"(liabilities {liabilities} + equity {equity})",
        "matches": assets is not None and assets == total,
        "tolerance": "exact (Rs '000s)",
        "method": "HBL balance-sheet total lines for period_end "
        "2025-12-31, read directly from line items.",
    }


def check_hbl_sfp_identity_2024(session):
    assets, liabilities, equity, total = _hbl_identity(session, "2024-12-31")
    return {
        "check_key": "hbl_sfp_identity_2024",
        "claimed_value": "assets 6,055,112,877 = liabilities 5,644,314,783 + equity 410,798,094",
        "recomputed_value": f"assets {assets} vs liabilities + equity {total} "
        f"(liabilities {liabilities} + equity {equity})",
        "matches": assets is not None and assets == total,
        "tolerance": "exact (Rs '000s)",
        "method": "HBL balance-sheet total lines for period_end "
        "2024-12-31, read directly from line items.",
    }


def check_hbl_pat_eps_2025(session):
    pat = _line_item(session, "HBL", "income", "2025-12-31", "profit_after_taxation")
    eps = _line_item(session, "HBL", "income", "2025-12-31", "eps_basic_diluted")
    return {
        "check_key": "hbl_pat_eps_2025",
        "claimed_value": "PAT 66,763,916; EPS 45.48",
        "recomputed_value": f"PAT {pat}; EPS {eps}",
        "matches": pat == Decimal("66763916") and eps == Decimal("45.48"),
        "tolerance": "exact",
        "method": "HBL income statement line items for period_end "
        "2025-12-31, read directly (independent cross-read with "
        "pdfplumber confirmed the same figures at extraction).",
    }


def check_screen_matched_counts(session):
    rows = session.execute(
        text(
            "SELECT sd.name, sr.matched_count, "
            "(SELECT COUNT(*) FROM screen_results r "
            "WHERE r.screen_run_id = sr.id AND r.outcome = 'MATCH') "
            "FROM screen_runs sr "
            "JOIN screen_definitions sd ON sd.id = sr.screen_definition_id "
            "ORDER BY sd.name"
        )
    ).fetchall()
    parts = []
    all_match = True
    for name, claimed, recount in rows:
        parts.append(f"{name}: stored {claimed}, recount {recount}")
        if claimed != recount:
            all_match = False
    return {
        "check_key": "screen_matched_counts",
        "claimed_value": "liquid_leaders 194; volume_top_decile 44; "
        "cheap_profitable 1; dividend_payers 2; technical_momentum 0 "
        "(Phase 20 report)",
        "recomputed_value": "; ".join(parts),
        "matches": all_match,
        "tolerance": "exact counts",
        "method": "screen_runs.matched_count compared with a recount "
        "of screen_results rows with outcome MATCH per run.",
    }


def check_alert_totals(session):
    rows = session.execute(
        text("SELECT severity, COUNT(*) FROM alerts GROUP BY severity ORDER BY severity")
    ).fetchall()
    by_severity = {severity: count for severity, count in rows}
    total = sum(by_severity.values())
    recomputed = (
        f"{total} = {by_severity.get('INFO', 0)} INFO + "
        f"{by_severity.get('WARNING', 0)} WARNING + "
        f"{by_severity.get('CRITICAL', 0)} CRITICAL"
    )
    return {
        "check_key": "alert_totals",
        "claimed_value": "89 = 82 INFO + 6 WARNING + 1 CRITICAL (Phase 21 report)",
        "recomputed_value": recomputed,
        "matches": total == 89
        and by_severity.get("INFO") == 82
        and by_severity.get("WARNING") == 6
        and by_severity.get("CRITICAL") == 1,
        "tolerance": "exact counts",
        "method": "alerts grouped by severity, counted directly.",
    }


def check_report_figure_census(session):
    rows = session.execute(
        text(
            "SELECT computation_status, COUNT(*) FROM report_figures "
            "GROUP BY computation_status ORDER BY computation_status"
        )
    ).fetchall()
    by_status = {status: count for status, count in rows}
    total = sum(by_status.values())
    recomputed = (
        f"{total} = {by_status.get('computed', 0)} computed + "
        f"{by_status.get('insufficient_inputs', 0)} insufficient_inputs + "
        f"{by_status.get('not_applicable', 0)} not_applicable"
    )
    return {
        "check_key": "report_figure_census",
        "claimed_value": "541 = 335 computed + 199 insufficient_inputs + 7 "
        "not_applicable (Phase 22 report)",
        "recomputed_value": recomputed,
        "matches": total == 541
        and by_status.get("computed") == 335
        and by_status.get("insufficient_inputs") == 199
        and by_status.get("not_applicable") == 7,
        "tolerance": "exact counts",
        "method": "report_figures grouped by computation_status, counted "
        "directly. EXPECTED MISMATCH (defect D-05): the live census "
        "is 334/200/7 — one figure (event_brief news:HUBC:earning, "
        "event_date) is stale from the recovery #6 intermediate news "
        "state, while its committed Markdown export shows computed.",
    }


def check_decision_completeness(session):
    rows = session.execute(
        text(
            "SELECT s.ticker, d.scored_dimensions, d.completeness "
            "FROM decisions d JOIN securities s ON s.id = d.security_id "
            "ORDER BY s.ticker"
        )
    ).fetchall()
    parts = [
        f"{ticker}: scored {scored} (completeness {completeness})"
        for ticker, scored, completeness in rows
    ]
    hubc = next((r for r in rows if r[0] == "HUBC"), None)
    ogdc = next((r for r in rows if r[0] == "OGDC"), None)
    return {
        "check_key": "decision_completeness",
        "claimed_value": "HUBC 6/7, OGDC 6/7 (original Phase 15 report)",
        "recomputed_value": "; ".join(parts),
        "matches": hubc is not None and hubc[1] == 6 and ogdc is not None and ogdc[1] == 6,
        "tolerance": "exact",
        "method": "decisions.scored_dimensions read directly. EXPECTED "
        "MISMATCH (defect D-05): the live rows are 5/7 for HUBC and "
        "OGDC — the decision engine ran during recovery #6 before "
        "the corrected news links landed, so their news dimension "
        "is ABSENT instead of neutral 0. Totals, conclusions, "
        "confidence, and user-facing values are unaffected.",
    }


def check_drift_vs_phase24_baseline(session):
    documents = _one(session, "SELECT COUNT(*) FROM financial_documents") or 0
    statements = _one(session, "SELECT COUNT(*) FROM financial_statements") or 0
    line_items = _one(session, "SELECT COUNT(*) FROM financial_statement_line_items") or 0
    return {
        "check_key": "drift_vs_phase24_baseline",
        "claimed_value": "Phase 24 baseline: documents 3, statements 88, "
        "line items 1,316 (Phase 26 drift check: 0 differences)",
        "recomputed_value": f"documents {documents}, statements {statements}, "
        f"line items {line_items}",
        "matches": documents == 3 and statements == 88 and line_items == 1316,
        "tolerance": "exact counts",
        "method": "Live counts compared with the Phase 24 baseline. "
        "EXPECTED DIFFERENCE, not a failure: +1 document, +30 "
        "statements, +800 line items is exactly the HBL extraction. "
        "The drift SLO is working as designed; the baseline update "
        "must be recorded with this evidence per the Phase 25 rule.",
    }


CHECKS = [
    check_hubc_gross_margin,
    check_hubc_trailing_pe,
    check_ogdc_trailing_pe,
    check_portfolio_reconciliation,
    check_breadth_coverage,
    check_volume_median,
    check_top10_volume_share,
    check_hbl_sfp_identity_2025,
    check_hbl_sfp_identity_2024,
    check_hbl_pat_eps_2025,
    check_screen_matched_counts,
    check_alert_totals,
    check_report_figure_census,
    check_decision_completeness,
    check_drift_vs_phase24_baseline,
]


def run_recomputations(session):
    """Run every recomputation; returns a list of result dicts."""
    results = []
    for fn in CHECKS:
        try:
            results.append(fn(session))
        except Exception as exc:  # noqa: BLE001 - reported, not hidden
            results.append(
                {
                    "check_key": getattr(fn, "__name__", "unknown"),
                    "claimed_value": "unknown",
                    "recomputed_value": f"error: {exc}",
                    "matches": False,
                    "tolerance": "n/a",
                    "method": f"Check raised: {exc}",
                }
            )
    return results
