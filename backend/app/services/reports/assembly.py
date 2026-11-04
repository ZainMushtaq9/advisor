"""Draft builders for Phase 22 reports (DB reads only, no
writes). A draft is a dict: header, sections (in template
order), figures, warnings. The runner QAs it and persists it;
renderers format it. Nothing here estimates, fills, or
invents: a missing input yields an insufficient_inputs
figure with its reason, and a missing section fact yields a
"not available" statement, never a number.

Schema notes (verified against the live models, not assumed):
- risk_flags keys on company_id with flag_type/severity/
  evidence (no flag_key, no message column, no security_id).
- news_event_companies links via event_id (not
  news_event_id).
- risk_controls carry rule/rationale; risk_control_checks
  carry control_key/scope_key/outcome/observed/threshold/
  reason; stress_results carry scenario_key/scope_key/
  impact_pct/computation_status/reason.
- market risk rows have scope_key 'MARKET' and NULL
  security_id; company risk rows carry the security id.
- fundamental value quality/computation live on the value
  row (computation_status column); valuation computation
  status and reason live in assumptions JSON.
- decisions carry research_conclusion, user_facing,
  confidence, and gate_reasons (JSON).
"""

from __future__ import annotations

import re

from sqlalchemy import text

from app.services.reports import (
    DATA_CUTOFF_DATE,
    DISCLAIMER,
    PRICE_DATE,
    REPORT_DATE,
    TEMPLATES,
)
from app.services.reports.evidence import (
    figure,
    stale_warning,
)


def slug(text_value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text_value).strip("_").lower()


def breadth_status(status: str) -> str:
    """Map a Phase 12 breadth status to a figure computation
    status. Breadth rows carry 'computed' / 'insufficient' /
    'partial'; figures carry 'computed' / 'insufficient_inputs'
    / 'not_applicable'. A partial breadth row is not a computed
    figure: it maps to insufficient_inputs with the original
    status preserved in the figure note."""
    if status == "computed":
        return "computed"
    return "insufficient_inputs"


DOSSIER_RATIOS = [
    "gross_margin",
    "operating_margin",
    "net_margin",
    "roa",
    "roe_total",
    "roe_owners",
    "roce",
    "roic",
    "current_ratio",
    "quick_ratio",
    "interest_coverage",
    "receivables_days",
    "inventory_days",
    "payables_days",
    "ocf",
    "fcf",
    "cash_conversion",
    "debt_to_equity",
    "revenue_growth",
    "pat_growth",
    "eps_growth",
]

INCOME_KEYS = [
    "revenue",
    "revenue_net",
    "cost_of_revenue",
    "gross_profit",
    "operating_profit",
    "profit_before_tax",
    "profit_after_tax",
    "net_profit",
    "pat",
    "eps_total",
    "eps_continuing",
    "share_of_profit_associates",
    "finance_costs",
    "interest_income",
    "interest_expense",
]


def q(session, sql: str, params: dict | None = None) -> list[dict]:
    rows = session.execute(text(sql), params or {}).mappings().all()
    return [dict(r) for r in rows]


def q1(session, sql: str, params: dict | None = None) -> dict | None:
    rows = q(session, sql, params)
    return rows[0] if rows else None


# ----------------------------------------------------------------
# Loaders (read-only)
# ----------------------------------------------------------------


def resolve_company(session, ticker: str) -> dict | None:
    return q1(
        session,
        """
        SELECT c.id AS company_id, c.legal_name, c.short_name,
               s.id AS security_id, s.ticker,
               sec.name AS sector_name, sec.id AS sector_id
        FROM companies c
        JOIN securities s ON s.company_id = c.id
        LEFT JOIN sectors sec ON sec.id = c.sector_id
        WHERE s.ticker = :ticker
        """,
        {"ticker": ticker},
    )


def company_price(session, security_id: int) -> dict | None:
    return q1(
        session,
        """
        SELECT id, trading_date, open_price, high_price, low_price, close_price, volume,
               turnover, previous_close, quality_status
        FROM market_prices
        WHERE security_id = :sid AND trading_date = :pdate
        """,
        {"sid": security_id, "pdate": PRICE_DATE},
    )


def company_statements(session, company_id: int) -> list[dict]:
    return q(
        session,
        """
        SELECT id, statement_type, period_start, period_end,
               publication_date, audited_status,
               consolidated_status, statement_scope, document_id,
               quality_status, is_current
        FROM financial_statements
        WHERE company_id = :cid AND is_current
        ORDER BY period_end, statement_type
        """,
        {"cid": company_id},
    )


def latest_period_end(session, company_id: int):
    row = q1(
        session,
        """
        SELECT MAX(period_end) AS period_end
        FROM financial_statements
        WHERE company_id = :cid AND is_current
        """,
        {"cid": company_id},
    )
    return row["period_end"] if row else None


def company_fundamentals(session, company_id: int, period_end) -> list[dict]:
    if period_end is None:
        return []
    return q(
        session,
        """
        SELECT v.id, d.metric_key, d.category, d.unit,
               v.value, v.computation_status, v.quality_status,
               v.input_statement_ids, v.input_price_ids
        FROM fundamental_metric_values v
        JOIN fundamental_metric_definitions d
          ON d.id = v.metric_definition_id
        WHERE v.company_id = :cid AND v.period_end = :pend
        ORDER BY d.metric_key
        """,
        {"cid": company_id, "pend": period_end},
    )


def company_health(session, company_id: int, period_end) -> list[dict]:
    if period_end is None:
        return []
    return q(
        session,
        """
        SELECT id, category, score, evidence, quality_status
        FROM financial_health_assessments
        WHERE company_id = :cid
          AND period_end = :pend AND is_current
        ORDER BY category
        """,
        {"cid": company_id, "pend": period_end},
    )


def company_valuations(session, security_id: int) -> list[dict]:
    return q(
        session,
        """
        SELECT id, method, estimated_value, value_low,
               value_high, assumptions, quality_status
        FROM valuations
        WHERE security_id = :sid AND is_current
        ORDER BY method
        """,
        {"sid": security_id},
    )


def company_decision(session, company_id: int) -> dict | None:
    return q1(
        session,
        """
        SELECT id, decision_date, screening_outcome,
               research_conclusion, user_facing, confidence,
               total_score, scored_dimensions, gate_reasons,
               conflicts, quality_status
        FROM decisions
        WHERE company_id = :cid AND is_current
        ORDER BY decision_date DESC LIMIT 1
        """,
        {"cid": company_id},
    )


def company_risk(session, security_id: int) -> list[dict]:
    return q(
        session,
        """
        SELECT id, metric_key, scope_key, value,
               computation_status, reason, quality_status
        FROM risk_metric_values
        WHERE security_id = :sid
        ORDER BY metric_key
        """,
        {"sid": security_id},
    )


def company_flags(session, company_id: int) -> list[dict]:
    return q(
        session,
        """
        SELECT id, flag_type, severity, evidence, as_of_date,
               quality_status
        FROM risk_flags
        WHERE company_id = :cid
        ORDER BY flag_type
        """,
        {"cid": company_id},
    )


def flag_message(flag: dict) -> str:
    """Human message for a risk flag row: type plus the stored
    evidence note. Flags are review-only by design."""
    evidence = flag.get("evidence") or {}
    note = evidence.get("note") or "Review-only flag."
    return f"{flag['flag_type']} ({flag['severity']}): {note}"


def company_ownership(session, company_id: int) -> list[dict]:
    return q(
        session,
        """
        SELECT id, holder_name, holder_category, shares_held AS shares,
               percentage, reporting_date AS as_of_date, quality_status
        FROM ownership_holdings
        WHERE company_id = :cid
        ORDER BY holder_category, holder_name
        """,
        {"cid": company_id},
    )


def company_actions(session, company_id: int) -> list[dict]:
    return q(
        session,
        """
        SELECT id, action_type, amount_per_share,
               announced_date, ex_date, record_date,
               payment_date, quality_status
        FROM corporate_action_records
        WHERE company_id = :cid
        ORDER BY action_type
        """,
        {"cid": company_id},
    )


def company_events(session, company_id: int) -> list[dict]:
    return q(
        session,
        """
        SELECT ne.id, ne.event_date, ne.date_status, ne.event_type,
               ne.headline, ne.summary, ne.publisher, ne.source_type,
               ne.review_status, ne.quality_status
        FROM news_events ne
        JOIN news_event_companies nec ON nec.event_id = ne.id
        WHERE nec.company_id = :cid
          AND (ne.event_date IS NULL OR ne.event_date <= :cutoff)
        ORDER BY ne.event_date NULLS LAST, ne.id
        """,
        {"cid": company_id, "cutoff": DATA_CUTOFF_DATE},
    )


def company_alerts(session, company_id: int) -> list[dict]:
    return q(
        session,
        """
        SELECT a.id, ar.rule_key, a.severity, a.ticker,
               a.as_of_date, a.status, a.title,
               a.quality_status
        FROM alerts a
        JOIN alert_rules ar ON ar.id = a.rule_id
        WHERE a.company_id = :cid
        ORDER BY a.as_of_date DESC NULLS LAST, a.id
        """,
        {"cid": company_id},
    )


def company_income_lines(session, company_id: int, period_end) -> list[dict]:
    if period_end is None:
        return []
    rows = q(
        session,
        """
        SELECT li.line_item_key, li.normalized_value,
               li.reported_unit, fs.id AS statement_id
        FROM financial_statement_line_items li
        JOIN financial_statements fs ON fs.id = li.statement_id
        WHERE fs.company_id = :cid AND fs.is_current
          AND fs.statement_type = 'income'
          AND fs.period_end = :pend AND li.is_current
        ORDER BY li.line_item_key
        """,
        {"cid": company_id, "pend": period_end},
    )
    wanted = set(INCOME_KEYS)
    return [r for r in rows if r["line_item_key"] in wanted]


def company_auditor_opinion(session, company_id: int) -> dict | None:
    return q1(
        session,
        """
        SELECT id, opinion_type, firm_name, opinion_date,
               quality_status
        FROM auditor_opinions
        WHERE company_id = :cid AND is_current
        ORDER BY opinion_date DESC NULLS LAST LIMIT 1
        """,
        {"cid": company_id},
    )


def macro_rows(session) -> list[dict]:
    return q(
        session,
        """
        SELECT id, indicator_code, value, unit, observation_date,
               quality_status
        FROM economic_indicators
        WHERE is_current AND observation_date <= :cutoff
        ORDER BY indicator_code, observation_date DESC
        """,
        {"cutoff": DATA_CUTOFF_DATE},
    )


def regime_row(session) -> dict | None:
    return q1(
        session,
        """
        SELECT id, regime_label, observation_date, evidence,
               quality_status
        FROM macro_regimes
        ORDER BY observation_date DESC LIMIT 1
        """,
    )


# ----------------------------------------------------------------
# Draft assembly helpers
# ----------------------------------------------------------------


def draft_header(
    template_key: str, subject_type: str, subject_key: str, subject_label: str, price_date=None
) -> dict:
    tpl = TEMPLATES[template_key]
    return {
        "template_key": template_key,
        "template_version": "v1",
        "title": tpl["title"],
        "subject_type": subject_type,
        "subject_key": subject_key,
        "subject_label": subject_label,
        "report_date": REPORT_DATE.isoformat(),
        "data_cutoff_date": DATA_CUTOFF_DATE.isoformat(),
        "price_date": (price_date or PRICE_DATE).isoformat(),
        "audience": tpl["audience"],
        "methodology": tpl["methodology"],
    }


def section(key: str, body: str) -> dict:
    title = dict(TEMPLATES_SECTION_TITLES).get(key, key)
    return {"section_key": key, "title": title, "body_markdown": body}


TEMPLATES_SECTION_TITLES: list = []
for _tpl in TEMPLATES.values():
    TEMPLATES_SECTION_TITLES.extend(_tpl["sections"])


def disclosures_section(figures: list[dict]) -> dict:
    sources = sorted({f["source_table"] for f in figures})
    body = (
        "Methodology: figures are pulled from stored platform "
        "rows only, as described in the template methodology "
        "above; no new market data was collected for this "
        "report. Source tables used: " + ", ".join(sources) + ". "
        "Every figure states its computation status and "
        "inherits its inputs' quality status; a figure with "
        "status insufficient_inputs or not_applicable carries "
        "its reason in the figures table, never a number. " + DISCLAIMER
    )
    return section("disclosures", body)


def base_warnings(
    session, company: dict, statements: list[dict], decision: dict | None
) -> list[dict]:
    warnings: list[dict] = []
    if not statements:
        warnings.append(
            {
                "warning_kind": "missing",
                "message": (
                    f"No stored statements for {company['ticker']}; "
                    "statement-derived sections are not available."
                ),
                "source_table": "financial_statements",
                "source_row_ids": [],
            }
        )
        return warnings
    latest = max(s["period_end"] for s in statements)
    stale = stale_warning(latest)
    if stale:
        warnings.append(
            {
                "warning_kind": "stale",
                "message": stale,
                "source_table": "financial_statements",
                "source_row_ids": [s["id"] for s in statements if s["period_end"] == latest],
            }
        )
    latest_pub = max(
        (s["publication_date"] for s in statements if s["publication_date"] is not None),
        default=None,
    )
    if latest_pub is None:
        warnings.append(
            {
                "warning_kind": "unknown_date",
                "message": (
                    "Latest statement publication date is unknown "
                    "(NULL in the stored row); point-in-time "
                    "validity cannot be verified."
                ),
                "source_table": "financial_statements",
                "source_row_ids": [s["id"] for s in statements],
            }
        )
    if decision:
        gates = decision.get("gate_reasons") or []
        if isinstance(gates, dict):
            gates = list(gates.keys())
        for gate in gates:
            warnings.append(
                {
                    "warning_kind": "gate",
                    "message": f"Phase 15 decision gate active: {gate}.",
                    "source_table": "decisions",
                    "source_row_ids": [decision["id"]],
                }
            )
    return warnings


def company_price_figures(price: dict | None, ticker: str) -> list[dict]:
    if price is None:
        return [
            figure(
                "close_price",
                f"{ticker} close price",
                kind="sourced_fact",
                status="insufficient_inputs",
                source_table="market_prices",
                source_row_ids=[],
                source_note=f"No stored price row for {ticker} on {PRICE_DATE}.",
            )
        ]
    return [
        figure(
            "close_price",
            f"{ticker} close price",
            kind="sourced_fact",
            status="computed",
            value=price["close_price"],
            unit="PKR",
            source_table="market_prices",
            source_row_ids=[price["id"]],
            source_note=f"Stored close for {PRICE_DATE}.",
            quality_status=price["quality_status"],
        ),
        figure(
            "volume",
            f"{ticker} volume",
            kind="sourced_fact",
            status="computed",
            value=price["volume"],
            unit="shares",
            source_table="market_prices",
            source_row_ids=[price["id"]],
            source_note=f"Stored volume for {PRICE_DATE}.",
            quality_status=price["quality_status"],
        ),
    ]


def _company_figures(session, company: dict) -> tuple[list[dict], dict]:
    """Shared figure set for company-subject reports. Returns
    (figures, bundle) where bundle holds the loaded rows the
    section writers need."""
    price = company_price(session, company["security_id"])
    statements = company_statements(session, company["company_id"])
    pend = latest_period_end(session, company["company_id"])
    fundamentals = company_fundamentals(session, company["company_id"], pend)
    health = company_health(session, company["company_id"], pend)
    valuations = company_valuations(session, company["security_id"])
    decision = company_decision(session, company["company_id"])
    risk = company_risk(session, company["security_id"])
    flags = company_flags(session, company["company_id"])
    ownership = company_ownership(session, company["company_id"])
    actions = company_actions(session, company["company_id"])
    events = company_events(session, company["company_id"])
    alerts = company_alerts(session, company["company_id"])
    bundle = {
        "price": price,
        "statements": statements,
        "period_end": pend,
        "fundamentals": fundamentals,
        "health": health,
        "valuations": valuations,
        "decision": decision,
        "risk": risk,
        "flags": flags,
        "ownership": ownership,
        "actions": actions,
        "events": events,
        "alerts": alerts,
    }
    figures = company_price_figures(price, company["ticker"])
    figures.append(
        figure(
            "statement_count",
            "Stored statements",
            kind="deterministic_calculation",
            status="computed",
            value=len(statements),
            unit="statements",
            source_table="financial_statements",
            source_row_ids=[s["id"] for s in statements],
            source_note="Count of current stored statement rows.",
        )
    )
    if pend is not None:
        figures.append(
            figure(
                "latest_period_end",
                "Latest statement period end",
                kind="sourced_fact",
                status="computed",
                value_text=pend.isoformat(),
                source_table="financial_statements",
                source_row_ids=[s["id"] for s in statements if s["period_end"] == pend],
                source_note="Latest period_end among current statements.",
            )
        )
    else:
        figures.append(
            figure(
                "latest_period_end",
                "Latest statement period end",
                kind="sourced_fact",
                status="insufficient_inputs",
                source_table="financial_statements",
                source_row_ids=[],
                source_note="No stored statements for this company.",
            )
        )
    latest_pub = max(
        (s["publication_date"] for s in statements if s["publication_date"] is not None),
        default=None,
    )
    if latest_pub is not None:
        figures.append(
            figure(
                "latest_publication_date",
                "Latest publication date",
                kind="sourced_fact",
                status="computed",
                value_text=latest_pub.isoformat(),
                source_table="financial_statements",
                source_row_ids=[s["id"] for s in statements if s["publication_date"] == latest_pub],
                source_note="Latest known publication date.",
            )
        )
    else:
        figures.append(
            figure(
                "latest_publication_date",
                "Latest publication date",
                kind="sourced_fact",
                status="insufficient_inputs",
                source_table="financial_statements",
                source_row_ids=[s["id"] for s in statements],
                source_note="Publication date is NULL in stored rows.",
            )
        )
    if decision is not None:
        figures.append(
            figure(
                "decision_research_conclusion",
                "Phase 15 research conclusion",
                kind="model_output",
                status="computed",
                value_text=decision["research_conclusion"],
                source_table="decisions",
                source_row_ids=[decision["id"]],
                source_note="Phase 15 research conclusion, reproduced verbatim.",
                quality_status=decision["quality_status"],
            )
        )
        figures.append(
            figure(
                "decision_user_facing",
                "Phase 15 user-facing value",
                kind="model_output",
                status="computed",
                value_text=decision["user_facing"],
                source_table="decisions",
                source_row_ids=[decision["id"]],
                source_note="User-facing values are WITHHELD in this run.",
                quality_status=decision["quality_status"],
            )
        )
        figures.append(
            figure(
                "decision_confidence",
                "Phase 15 confidence",
                kind="model_output",
                status="computed",
                value_text=decision["confidence"],
                source_table="decisions",
                source_row_ids=[decision["id"]],
                source_note="Confidence caps at LOW on UNVERIFIED inputs.",
                quality_status=decision["quality_status"],
            )
        )
    figures.append(
        figure(
            "alert_count",
            "Stored alerts",
            kind="deterministic_calculation",
            status="computed",
            value=len(alerts),
            unit="alerts",
            source_table="alerts",
            source_row_ids=[a["id"] for a in alerts],
            source_note="Alerts are notifications, not instructions.",
        )
    )
    figures.append(
        figure(
            "event_count",
            "Stored news events",
            kind="deterministic_calculation",
            status="computed",
            value=len(events),
            unit="events",
            source_table="news_events",
            source_row_ids=[e["id"] for e in events],
            source_note="Events on or before the data cut-off only.",
        )
    )
    return figures, bundle


def _ratio_figures(fundamentals: list[dict]) -> list[dict]:
    by_key = {f["metric_key"]: f for f in fundamentals}
    out: list[dict] = []
    for key in DOSSIER_RATIOS:
        row = by_key.get(key)
        if row is None:
            out.append(
                figure(
                    f"ratio_{key}",
                    f"Ratio {key}",
                    kind="deterministic_calculation",
                    status="insufficient_inputs",
                    source_table="fundamental_metric_values",
                    source_row_ids=[],
                    source_note=f"No stored Phase 8 row for {key}.",
                )
            )
        elif row["computation_status"] == "computed":
            out.append(
                figure(
                    f"ratio_{key}",
                    f"Ratio {key}",
                    kind="deterministic_calculation",
                    status="computed",
                    value=row["value"],
                    unit=row["unit"],
                    source_table="fundamental_metric_values",
                    source_row_ids=[row["id"]],
                    source_note=f"Phase 8 {key} at the latest period.",
                    quality_status=row["quality_status"],
                )
            )
        else:
            out.append(
                figure(
                    f"ratio_{key}",
                    f"Ratio {key}",
                    kind="deterministic_calculation",
                    status=row["computation_status"],
                    source_table="fundamental_metric_values",
                    source_row_ids=[row["id"]],
                    source_note=f"Phase 8 {key} is "
                    f"{row['computation_status']}; see the "
                    "Phase 8 run report for the reason.",
                    quality_status=row["quality_status"],
                )
            )
    return out


def _health_figures(health: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in health:
        if row["score"] is None:
            out.append(
                figure(
                    f"health_{row['category']}",
                    f"Health {row['category']}",
                    kind="model_output",
                    status="insufficient_inputs",
                    source_table="financial_health_assessments",
                    source_row_ids=[row["id"]],
                    source_note="Sector category carries no score by design.",
                    quality_status=row["quality_status"],
                )
            )
        else:
            out.append(
                figure(
                    f"health_{row['category']}",
                    f"Health {row['category']}",
                    kind="model_output",
                    status="computed",
                    value=row["score"],
                    source_table="financial_health_assessments",
                    source_row_ids=[row["id"]],
                    source_note="Descriptive health dimension, not a rating.",
                    quality_status=row["quality_status"],
                )
            )
    return out


def _valuation_figures(valuations: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in valuations:
        assumptions = row["assumptions"] or {}
        status = assumptions.get("computation_status", "insufficient_inputs")
        reason = assumptions.get("reason", "No reason recorded.")
        if status == "computed" and row["estimated_value"] is not None:
            out.append(
                figure(
                    f"valuation_{row['method']}",
                    f"Valuation {row['method']}",
                    kind="model_output",
                    status="computed",
                    value=row["estimated_value"],
                    unit="PKR",
                    source_table="valuations",
                    source_row_ids=[row["id"]],
                    source_note=f"Phase 9 {row['method']}.",
                    quality_status=row["quality_status"],
                )
            )
        else:
            out.append(
                figure(
                    f"valuation_{row['method']}",
                    f"Valuation {row['method']}",
                    kind="model_output",
                    status=status,
                    source_table="valuations",
                    source_row_ids=[row["id"]],
                    source_note=f"Phase 9 {row['method']}: {reason}",
                    quality_status=row["quality_status"],
                )
            )
    return out


def _thesis_text(bundle: dict, ticker: str) -> tuple[str, str]:
    """Thesis and counter-thesis grounded only in stored rows:
    health scores, the Phase 15 conclusion, and stored
    conflicts. No new judgement is introduced."""
    decision = bundle["decision"]
    health = {h["category"]: h["score"] for h in bundle["health"]}
    profitability = health.get("profitability")
    earnings_quality = health.get("earnings_quality")
    if decision is not None:
        conclusion = decision["research_conclusion"]
        confidence = decision["confidence"]
        thesis = (
            f"Phase 15 records a research conclusion of "
            f"{conclusion} at {confidence} confidence for "
            f"{ticker} (user-facing value WITHHELD). "
        )
    else:
        thesis = f"No Phase 15 decision is stored for {ticker}; no conclusion is drawn here. "
    if profitability is not None:
        thesis += f"Profitability health is {profitability}. "
    conflicts = []
    if decision is not None:
        raw = decision.get("conflicts") or []
        if isinstance(raw, dict):
            conflicts = list(raw.keys())
        elif isinstance(raw, list):
            conflicts = [str(c) for c in raw]
    if conflicts:
        counter = (
            "Stored conflicts (preserved, never averaged away): " + "; ".join(conflicts) + ". "
        )
    elif (
        profitability is not None
        and earnings_quality is not None
        and earnings_quality < profitability
    ):
        counter = (
            f"Earnings quality ({earnings_quality}) trails "
            f"profitability ({profitability}), so the headline "
            "margin strength is not matched by earnings "
            "quality in the stored health assessment. "
        )
    else:
        counter = (
            "No stored conflict is recorded for this company; "
            "that absence is not evidence of strength, only of "
            "the stored rows. "
        )
    counter += (
        "All inputs are UNVERIFIED, forecasts are abstained, "
        "and user-facing values are WITHHELD, so this report "
        "draws no executable conclusion."
    )
    return thesis, counter


# ----------------------------------------------------------------
# Builders
# ----------------------------------------------------------------


def build_company_dossier(session, ticker: str) -> dict:
    company = resolve_company(session, ticker)
    if company is None:
        raise ValueError(f"unknown ticker {ticker}")
    figures, bundle = _company_figures(session, company)
    figures += _ratio_figures(bundle["fundamentals"])
    figures += _health_figures(bundle["health"])
    figures += _valuation_figures(bundle["valuations"])
    thesis, counter = _thesis_text(bundle, ticker)
    price = bundle["price"]
    price_text = (
        f"Close price on {PRICE_DATE}: {price['close_price']} PKR "
        f"with volume {price['volume']} shares. "
        if price
        else f"Close price on {PRICE_DATE}: not available. "
    )
    opinion = company_auditor_opinion(session, company["company_id"])
    opinion_text = (
        f"Auditor opinion on file: {opinion['opinion_type']} by {opinion['firm_name']}. "
        if opinion
        else "Auditor opinion: not available (no stored opinion row). "
    )
    sections = [
        section(
            "executive_summary",
            f"{company['legal_name']} ({ticker}, "
            f"{company['sector_name'] or 'sector not available'}). "
            + price_text
            + opinion_text
            + f"Stored statements: {len(bundle['statements'])}; "
            f"stored alerts: {len(bundle['alerts'])}; stored "
            f"news events: {len(bundle['events'])}. "
            "Key figures are in the figures table; see "
            "close_price, latest_period_end, and "
            "decision_research_conclusion.",
        ),
        section("thesis", thesis + "See close_price and decision_research_conclusion."),
        section("counter_thesis", counter + " See decision_research_conclusion."),
        section(
            "financial_snapshot",
            f"Latest statement period end: "
            f"{bundle['period_end'] or 'not available'}. "
            "Ratios below are the Phase 8 values at that "
            "period; see ratio_gross_margin, ratio_net_margin, "
            "ratio_current_ratio, and ratio_ocf.",
        ),
        section(
            "valuation",
            "Each Phase 9 method stands alone; see "
            "valuation_multiples:pe_trailing and "
            "valuation_asset_based:equity_book_value_total. "
            "No method is averaged with another, and no "
            "price objective is stated.",
        ),
        section(
            "risks",
            "Stored risk flags: "
            + (
                "; ".join(flag_message(f) for f in bundle["flags"])
                if bundle["flags"]
                else "not available — no stored risk flags for this company. "
            )
            + "Flags are review-only. See alert_count.",
        ),
        section(
            "catalysts",
            "Stored news events: "
            + (
                "; ".join(
                    f"{e['event_type']} on {e['event_date'] or 'unknown date'}: {e['headline']}"
                    for e in bundle["events"]
                )
                if bundle["events"]
                else "not available — no stored news events for this company. "
            )
            + "See event_count.",
        ),
        section(
            "uncertainty",
            "All inputs are UNVERIFIED; forecasts are "
            "abstained; technical values are not calculable "
            "from one price date; user-facing values are "
            "WITHHELD. See decision_confidence and "
            "decision_user_facing.",
        ),
        section(
            "monitoring",
            "Watch for a fresh statement with a known "
            "publication date, a second price date carrying "
            "previous_close, and any new stored alert. "
            "See latest_publication_date and alert_count.",
        ),
        disclosures_section(figures),
    ]
    warnings = base_warnings(session, company, bundle["statements"], bundle["decision"])
    for flag in bundle["flags"]:
        warnings.append(
            {
                "warning_kind": "risk_flag",
                "message": flag_message(flag),
                "source_table": "risk_flags",
                "source_row_ids": [flag["id"]],
            }
        )
    return {
        "header": draft_header(
            "company_dossier", "company", ticker, f"{company['legal_name']} ({ticker})"
        ),
        "sections": sections,
        "figures": figures,
        "warnings": warnings,
    }


def build_earnings_update(session, ticker: str) -> dict:
    company = resolve_company(session, ticker)
    if company is None:
        raise ValueError(f"unknown ticker {ticker}")
    figures, bundle = _company_figures(session, company)
    lines = company_income_lines(session, company["company_id"], bundle["period_end"])
    by_key = {r["line_item_key"]: r for r in lines}
    for key in INCOME_KEYS:
        row = by_key.get(key)
        if row is None:
            figures.append(
                figure(
                    f"income_{key}",
                    f"Income line {key}",
                    kind="sourced_fact",
                    status="insufficient_inputs",
                    source_table="financial_statement_line_items",
                    source_row_ids=[],
                    source_note=f"No stored income line {key} at the latest period.",
                )
            )
        else:
            figures.append(
                figure(
                    f"income_{key}",
                    f"Income line {key}",
                    kind="sourced_fact",
                    status="computed",
                    value=row["normalized_value"],
                    unit=row["reported_unit"],
                    source_table="financial_statement_line_items",
                    source_row_ids=[row["statement_id"]],
                    source_note=f"Stored income line {key} at the latest period.",
                )
            )
    pend = bundle["period_end"]
    period_text = (
        f"Latest income period ends {pend}. " if pend else "Latest income period: not available. "
    )
    pat = by_key.get("profit_after_tax") or by_key.get("pat") or by_key.get("net_profit")
    pat_text = (
        f"Profit after tax: {pat['normalized_value']} {pat['reported_unit']}. "
        if pat
        else "Profit after tax: not available. "
    )
    sections = [
        section(
            "executive_summary",
            f"{company['legal_name']} ({ticker}) earnings update. "
            + period_text
            + pat_text
            + "See income_profit_after_tax and "
            "latest_period_end.",
        ),
        section(
            "results",
            period_text + pat_text + "Income lines are cumulative interim columns "
            "where the statement says so; no standalone "
            "quarter is derived and no annualisation is "
            "applied. See income_revenue and "
            "income_profit_after_tax.",
        ),
        section("thesis", _thesis_text(bundle, ticker)[0] + "See decision_research_conclusion."),
        section(
            "counter_thesis", _thesis_text(bundle, ticker)[1] + " See decision_research_conclusion."
        ),
        section(
            "risks",
            "Stored risk flags: "
            + (
                "; ".join(flag_message(f) for f in bundle["flags"])
                if bundle["flags"]
                else "not available. "
            )
            + "See alert_count.",
        ),
        section(
            "uncertainty",
            "All inputs are UNVERIFIED; the latest "
            "publication date may be unknown (see "
            "latest_publication_date); forecasts are "
            "abstained.",
        ),
        section(
            "monitoring",
            "Watch for the next stored income period and "
            "for a known publication date. See "
            "latest_publication_date.",
        ),
        disclosures_section(figures),
    ]
    warnings = base_warnings(session, company, bundle["statements"], bundle["decision"])
    return {
        "header": draft_header(
            "earnings_update", "company", ticker, f"{company['legal_name']} ({ticker})"
        ),
        "sections": sections,
        "figures": figures,
        "warnings": warnings,
    }


def build_valuation_report(session, ticker: str) -> dict:
    company = resolve_company(session, ticker)
    if company is None:
        raise ValueError(f"unknown ticker {ticker}")
    figures, bundle = _company_figures(session, company)
    figures += _valuation_figures(bundle["valuations"])
    computed = [
        v
        for v in bundle["valuations"]
        if (v["assumptions"] or {}).get("computation_status") == "computed"
    ]
    unavailable = [
        v
        for v in bundle["valuations"]
        if (v["assumptions"] or {}).get("computation_status") != "computed"
    ]
    sections = [
        section(
            "executive_summary",
            f"{company['legal_name']} ({ticker}) valuation. "
            f"Computed methods: {len(computed)}; unavailable "
            f"methods: {len(unavailable)}. See "
            "valuation_multiples:pe_trailing and "
            "valuation_asset_based:equity_book_value_total.",
        ),
        section(
            "methods",
            "Methods are Phase 9 rows, each with its own "
            "inputs and reason. See "
            "valuation_multiples:pe_trailing and "
            "valuation_asset_based:equity_book_value_total.",
        ),
        section(
            "scenarios",
            "Computed: "
            + (
                ", ".join(f"valuation_{v['method']}" for v in computed)
                if computed
                else "not available — no computed method. "
            )
            + "Unavailable (with reasons in the figures table): "
            + (", ".join(v["method"] for v in unavailable) if unavailable else "not available. ")
            + "No scenario states a price objective.",
        ),
        section("thesis", _thesis_text(bundle, ticker)[0] + "See decision_research_conclusion."),
        section(
            "counter_thesis", _thesis_text(bundle, ticker)[1] + " See decision_research_conclusion."
        ),
        section(
            "risks",
            "Valuation inputs are UNVERIFIED; share-count "
            "methods are unavailable without authoritative "
            "shares-outstanding data; DCF methods are "
            "unavailable without source-backed discount "
            "rates. See decision_confidence.",
        ),
        section(
            "uncertainty",
            "All inputs are UNVERIFIED; no price target is "
            "stated; user-facing values are WITHHELD. "
            "See decision_user_facing.",
        ),
        disclosures_section(figures),
    ]
    warnings = base_warnings(session, company, bundle["statements"], bundle["decision"])
    return {
        "header": draft_header(
            "valuation_report", "company", ticker, f"{company['legal_name']} ({ticker})"
        ),
        "sections": sections,
        "figures": figures,
        "warnings": warnings,
    }


def build_sector_outlook(session, sector_name: str) -> dict:
    sector = q1(
        session,
        "SELECT id, name FROM sectors WHERE name = :name",
        {"name": sector_name},
    )
    if sector is None:
        raise ValueError(f"unknown sector {sector_name}")
    members = q(
        session,
        """
        SELECT c.id AS company_id, s.ticker
        FROM companies c
        JOIN securities s ON s.company_id = c.id
        WHERE c.sector_id = :sid ORDER BY s.ticker
        """,
        {"sid": sector["id"]},
    )
    member_ids = [m["company_id"] for m in members]
    stmt_companies: list[str] = []
    if member_ids:
        rows = q(
            session,
            """
            SELECT DISTINCT s.ticker
            FROM financial_statements fs
            JOIN securities s ON s.company_id = fs.company_id
            WHERE fs.company_id = ANY(:ids) AND fs.is_current
            ORDER BY s.ticker
            """,
            {"ids": member_ids},
        )
        stmt_companies = [r["ticker"] for r in rows]
    breadth = q1(
        session,
        """
        SELECT id, scope, trading_date, metric_key, metric_value,
               status, quality_status
        FROM market_breadth
        WHERE scope = :scope AND trading_date = :pdate
          AND metric_key = 'priced_coverage'
        """,
        {"scope": f"SECTOR:{sector_name}", "pdate": PRICE_DATE},
    )
    regime = regime_row(session)
    figures = [
        figure(
            "sector_members",
            "Sector members",
            kind="deterministic_calculation",
            status="computed",
            value=len(members),
            unit="companies",
            source_table="companies",
            source_row_ids=member_ids,
            source_note="Registry members of this sector.",
        ),
        figure(
            "sector_statement_companies",
            "Statement companies",
            kind="deterministic_calculation",
            status="computed",
            value=len(stmt_companies),
            unit="companies",
            source_table="financial_statements",
            source_row_ids=[],
            source_note="Members with at least one current statement.",
        ),
    ]
    if breadth is not None:
        b_status = breadth_status(breadth["status"])
        if breadth["metric_value"] is None:
            b_status = "insufficient_inputs"
        figures.append(
            figure(
                "sector_priced_coverage",
                "Sector priced coverage",
                kind="deterministic_calculation",
                status=b_status,
                value=breadth["metric_value"] if b_status == "computed" else None,
                source_table="market_breadth",
                source_row_ids=[breadth["id"]],
                source_note=f"Phase 12 breadth for {PRICE_DATE} "
                f"(breadth status: {breadth['status']}).",
                quality_status=breadth["quality_status"],
            )
        )
    if regime is not None:
        figures.append(
            figure(
                "macro_regime",
                "Macro regime",
                kind="model_output",
                status="computed",
                value_text=regime["regime_label"],
                source_table="macro_regimes",
                source_row_ids=[regime["id"]],
                source_note="Phase 10 regime label.",
                quality_status=regime["quality_status"],
            )
        )
    coverage_text = (
        f"{len(stmt_companies)} of {len(members)} members have "
        f"stored statements: {', '.join(stmt_companies) or 'not available'}. "
    )
    regime_text = (
        f"Macro regime: {regime['regime_label']}. " if regime else "Macro regime: not available. "
    )
    sections = [
        section(
            "executive_summary",
            f"Sector outlook for {sector_name}. "
            + coverage_text
            + regime_text
            + "See sector_members and "
            "sector_statement_companies.",
        ),
        section(
            "coverage",
            coverage_text + "A sector with one statement "
            "company is described as such, never as "
            "sector-wide evidence. See "
            "sector_statement_companies.",
        ),
        section("thesis", regime_text + "See macro_regime."),
        section(
            "counter_thesis",
            "Coverage is statement-thin: most members have "
            "no stored statements, so no sector-wide "
            "conclusion is drawn. See "
            "sector_statement_companies.",
        ),
        section(
            "risks",
            "All inputs are UNVERIFIED; breadth is one "
            "trading date only. See sector_priced_coverage.",
        ),
        section(
            "uncertainty",
            "Macro context is Phase 10 only; forecasts are "
            "abstained; user-facing values are WITHHELD. "
            "See macro_regime.",
        ),
        section(
            "monitoring",
            "Watch for statement expansion beyond the "
            "current statement companies and for new price "
            "dates. See sector_statement_companies.",
        ),
        disclosures_section(figures),
    ]
    warnings = []
    if len(stmt_companies) < len(members):
        warnings.append(
            {
                "warning_kind": "coverage",
                "message": (
                    f"Only {len(stmt_companies)} of {len(members)} "
                    "sector members have stored statements."
                ),
                "source_table": "financial_statements",
                "source_row_ids": [],
            }
        )
    return {
        "header": draft_header("sector_outlook", "sector", sector_name, sector_name),
        "sections": sections,
        "figures": figures,
        "warnings": warnings,
    }


def build_event_brief(session, subject_key: str) -> dict:
    figures: list[dict] = []
    warnings: list[dict] = []
    if subject_key.startswith("macro:"):
        _, date_part, event_type = subject_key.split(":", 2)
        event = q1(
            session,
            """
            SELECT id, event_date, event_type, title, note,
                   quality_status
            FROM macro_events
            WHERE event_date = :d AND event_type = :t
            """,
            {"d": date_part, "t": event_type},
        )
        if event is None:
            raise ValueError(f"unknown macro event {subject_key}")
        label = f"{event['title']} ({event['event_date']})"
        figures.append(
            figure(
                "event_date",
                "Event date",
                kind="sourced_fact",
                status="computed",
                value_text=str(event["event_date"]),
                source_table="macro_events",
                source_row_ids=[event["id"]],
                source_note="Stored macro event date.",
                quality_status=event["quality_status"],
            )
        )
        figures.append(
            figure(
                "event_type",
                "Event type",
                kind="sourced_fact",
                status="computed",
                value_text=event["event_type"],
                source_table="macro_events",
                source_row_ids=[event["id"]],
                source_note="Stored macro event type.",
                quality_status=event["quality_status"],
            )
        )
        event_body = (
            f"Macro event: {event['title']} on {event['event_date']}. "
            f"Note: {event['note'] or 'not available'}. "
        )
        if event["event_date"] > DATA_CUTOFF_DATE:
            warnings.append(
                {
                    "warning_kind": "scheduled",
                    "message": (
                        f"Event dated {event['event_date']} is after "
                        "the data cut-off; it is scheduled, not "
                        "occurred."
                    ),
                    "source_table": "macro_events",
                    "source_row_ids": [event["id"]],
                }
            )
            event_body += (
                "This event is SCHEDULED (after the data "
                "cut-off) and is not presented as occurred. "
            )
        sections = [
            section("executive_summary", event_body + "See event_date."),
            section("event", event_body + "See event_type."),
            section(
                "thesis",
                "Macro context only; no conclusion about any "
                "security is drawn from this event alone. "
                "See event_date.",
            ),
            section(
                "counter_thesis",
                "A single macro event does not determine market direction. See event_date.",
            ),
            section("risks", "Event quality: " + event["quality_status"] + ". See event_date."),
            section(
                "uncertainty",
                "All inputs are UNVERIFIED unless the figure note says otherwise. See event_date.",
            ),
            section(
                "monitoring",
                "Watch for the stored outcome of this event once its date passes. See event_date.",
            ),
            disclosures_section(figures),
        ]
        return {
            "header": draft_header("event_brief", "macro_event", subject_key, label),
            "sections": sections,
            "figures": figures,
            "warnings": warnings,
        }
    if subject_key.startswith("news:"):
        _, ticker, substring = subject_key.split(":", 2)
        company = resolve_company(session, ticker)
        if company is None:
            raise ValueError(f"unknown ticker {ticker}")
        event = q1(
            session,
            """
            SELECT ne.id, ne.event_date, ne.date_status, ne.event_type,
                   ne.headline, ne.summary, ne.publisher,
                   ne.source_type, ne.review_status,
                   ne.quality_status
            FROM news_events ne
            JOIN news_event_companies nec ON nec.event_id = ne.id
            WHERE nec.company_id = :cid
              AND ne.event_type ILIKE :pat
            ORDER BY ne.event_date NULLS LAST, ne.id LIMIT 1
            """,
            {"cid": company["company_id"], "pat": f"%{substring}%"},
        )
        if event is None:
            raise ValueError(f"no news event for {subject_key}")
        label = f"{ticker}: {event['headline']}"
        if event["event_date"] is None:
            figures.append(
                figure(
                    "event_date",
                    "Event date",
                    kind="sourced_fact",
                    status="insufficient_inputs",
                    source_table="news_events",
                    source_row_ids=[event["id"]],
                    source_note="Event date is NULL in the stored row.",
                    quality_status=event["quality_status"],
                )
            )
            warnings.append(
                {
                    "warning_kind": "unknown_date",
                    "message": "News event date is unknown (NULL); the "
                    "event is not dated by guesswork.",
                    "source_table": "news_events",
                    "source_row_ids": [event["id"]],
                }
            )
            date_text = "unknown date"
        else:
            figures.append(
                figure(
                    "event_date",
                    "Event date",
                    kind="sourced_fact",
                    status="computed",
                    value_text=str(event["event_date"]),
                    source_table="news_events",
                    source_row_ids=[event["id"]],
                    source_note="Stored news event date.",
                    quality_status=event["quality_status"],
                )
            )
            date_text = str(event["event_date"])
        figures.append(
            figure(
                "event_type",
                "Event type",
                kind="sourced_fact",
                status="computed",
                value_text=event["event_type"],
                source_table="news_events",
                source_row_ids=[event["id"]],
                source_note="Stored news event type.",
                quality_status=event["quality_status"],
            )
        )
        event_body = (
            f"News event for {ticker} on {date_text}: "
            f"{event['headline']} "
            f"({event['summary'] or 'not available'}). "
        )
        sections = [
            section("executive_summary", event_body + "See event_date."),
            section("event", event_body + "See event_type."),
            section(
                "thesis",
                "Event context only; no conclusion about "
                "any security is drawn from this event "
                "alone. See event_date.",
            ),
            section(
                "counter_thesis",
                "A single news event does not determine market direction. See event_date.",
            ),
            section(
                "risks",
                "Event quality: "
                + event["quality_status"]
                + "; review status: "
                + event["review_status"]
                + ". See event_date.",
            ),
            section(
                "uncertainty",
                "All inputs are UNVERIFIED unless the figure note says otherwise. See event_date.",
            ),
            section(
                "monitoring", "Watch for follow-up stored events for this company. See event_date."
            ),
            disclosures_section(figures),
        ]
        return {
            "header": draft_header("event_brief", "news_event", subject_key, label),
            "sections": sections,
            "figures": figures,
            "warnings": warnings,
        }
    raise ValueError(f"unsupported event subject {subject_key}")


def build_portfolio_review(session, name: str) -> dict:
    portfolio = q1(
        session,
        """
        SELECT id, name, method, capital, price_date, status,
               quality_status
        FROM simulated_portfolios WHERE name = :name
        """,
        {"name": name},
    )
    if portfolio is None:
        raise ValueError(f"unknown portfolio {name}")
    holdings = q(
        session,
        """
        SELECT id, ticker, sector, target_weight, actual_weight,
               units, value, price, price_date
        FROM simulated_portfolio_holdings
        WHERE portfolio_id = :pid ORDER BY ticker
        """,
        {"pid": portfolio["id"]},
    )
    exclusions = q(
        session,
        """
        SELECT id, ticker, reason_code, reason_detail
        FROM portfolio_exclusions
        WHERE portfolio_id = :pid ORDER BY ticker
        """,
        {"pid": portfolio["id"]},
    )
    sectors = q(
        session,
        """
        SELECT id, sector, invested_value, invested_weight,
               capital_weight
        FROM portfolio_sector_allocations
        WHERE portfolio_id = :pid ORDER BY sector
        """,
        {"pid": portfolio["id"]},
    )
    comparisons = q(
        session,
        """
        SELECT id, subject_name, baseline_name, method_compared,
               status, metrics, reasons
        FROM portfolio_comparisons
        WHERE subject_name = :name OR baseline_name = :name
        ORDER BY method_compared
        """,
        {"name": name},
    )
    invested = sum((h["value"] or 0) for h in holdings)
    figures = [
        figure(
            "portfolio_capital",
            "Hypothetical capital",
            kind="assumption",
            status="computed",
            value=portfolio["capital"],
            unit="PKR",
            source_table="simulated_portfolios",
            source_row_ids=[portfolio["id"]],
            source_note="Hypothetical capital, not real money.",
            quality_status=portfolio["quality_status"],
        ),
        figure(
            "portfolio_invested",
            "Invested value",
            kind="deterministic_calculation",
            status="computed",
            value=invested,
            unit="PKR",
            source_table="simulated_portfolio_holdings",
            source_row_ids=[h["id"] for h in holdings],
            source_note="Sum of stored holding values.",
            quality_status=portfolio["quality_status"],
        ),
        figure(
            "portfolio_holding_count",
            "Holdings",
            kind="deterministic_calculation",
            status="computed",
            value=len(holdings),
            unit="holdings",
            source_table="simulated_portfolio_holdings",
            source_row_ids=[h["id"] for h in holdings],
            source_note="Count of stored holdings.",
        ),
        figure(
            "portfolio_return",
            "Portfolio return",
            kind="model_output",
            status="insufficient_inputs",
            source_table="simulated_portfolio_holdings",
            source_row_ids=[h["id"] for h in holdings],
            source_note="One price date yields zero return observations; no return is invented.",
        ),
    ]
    for holding in holdings:
        figures.append(
            figure(
                f"holding_{holding['ticker']}",
                f"Holding {holding['ticker']}",
                kind="deterministic_calculation",
                status="computed",
                value=holding["value"],
                unit="PKR",
                source_table="simulated_portfolio_holdings",
                source_row_ids=[holding["id"]],
                source_note=f"{holding['units']} units at "
                f"{holding['price']} PKR on "
                f"{holding['price_date']}.",
            )
        )
    for allocation in sectors:
        figures.append(
            figure(
                f"sector_{slug(allocation['sector'])}",
                f"Sector {allocation['sector']} invested",
                kind="deterministic_calculation",
                status="computed",
                value=allocation["invested_value"],
                unit="PKR",
                source_table="portfolio_sector_allocations",
                source_row_ids=[allocation["id"]],
                source_note="Stored sector allocation for this simulated portfolio.",
            )
        )
    holdings_text = (
        "; ".join(f"{h['ticker']}: {h['units']} units, {h['value']} PKR" for h in holdings)
        if holdings
        else "not available — no stored holdings. "
    )
    exclusions_text = (
        "; ".join(f"{e['ticker']} ({e['reason_code']}: {e['reason_detail']})" for e in exclusions)
        if exclusions
        else "not available — no stored exclusions. "
    )
    comparisons_text = (
        "; ".join(
            f"{c['method_compared']}: {c['status']}"
            + (f" ({'; '.join(c['reasons'])})" if c["reasons"] else "")
            for c in comparisons
        )
        if comparisons
        else "not available — no stored comparisons. "
    )
    sections = [
        section(
            "executive_summary",
            f"SIMULATED portfolio {name} "
            f"({portfolio['method']}, hypothetical capital "
            f"{portfolio['capital']} PKR, price date "
            f"{portfolio['price_date']}). Holdings: "
            + holdings_text
            + " See portfolio_invested and "
            "portfolio_return.",
        ),
        section("holdings", holdings_text + " See portfolio_holding_count."),
        section("exclusions", exclusions_text + " See portfolio_holding_count."),
        section("comparison", comparisons_text + " See portfolio_return."),
        section(
            "thesis",
            "The simulated construction follows its stated "
            "method on stored closes only. See "
            "portfolio_invested.",
        ),
        section(
            "counter_thesis",
            "One price date means no return, no covariance, "
            "and no risk-adjusted comparison exists. See "
            "portfolio_return.",
        ),
        section(
            "risks",
            "All inputs are UNVERIFIED; this is a "
            "simulation, never a real holding. See "
            "portfolio_capital.",
        ),
        section(
            "uncertainty",
            "Returns are insufficient_inputs; forecasts are "
            "abstained; user-facing values are WITHHELD. "
            "See portfolio_return.",
        ),
        disclosures_section(figures),
    ]
    warnings = []
    for comp in comparisons:
        if comp["status"] != "COMPUTED":
            warnings.append(
                {
                    "warning_kind": "not_calculable",
                    "message": (
                        f"Comparison {comp['method_compared']} is "
                        f"{comp['status']}: " + ("; ".join(comp["reasons"] or []))
                    ),
                    "source_table": "portfolio_comparisons",
                    "source_row_ids": [comp["id"]],
                }
            )
    return {
        "header": draft_header(
            "portfolio_review", "portfolio", name, name, price_date=portfolio["price_date"]
        ),
        "sections": sections,
        "figures": figures,
        "warnings": warnings,
    }


def build_risk_report(session, subject_key: str) -> dict:
    if subject_key == "MARKET":
        rows = q(
            session,
            """
            SELECT id, metric_key, scope_key, value,
                   computation_status, reason, quality_status
            FROM risk_metric_values
            WHERE security_id IS NULL
            ORDER BY metric_key
            """,
        )
        flags: list[dict] = []
        label = "Market"
        subject_type = "market"
    else:
        company = resolve_company(session, subject_key)
        if company is None:
            raise ValueError(f"unknown ticker {subject_key}")
        rows = company_risk(session, company["security_id"])
        flags = company_flags(session, company["company_id"])
        label = f"{company['legal_name']} ({subject_key})"
        subject_type = "company"
    controls = q(
        session,
        """
        SELECT id, control_key, version, rule, rationale
        FROM risk_controls ORDER BY control_key
        """,
    )
    checks = q(
        session,
        """
        SELECT id, control_key, version, scope_key, as_of_date,
               outcome, observed_value, threshold_value, reason,
               quality_status
        FROM risk_control_checks ORDER BY id
        """,
    )
    stress = q(
        session,
        """
        SELECT id, scenario_key, scope_key, as_of_date, impact_pct,
               computation_status, reason, quality_status
        FROM stress_results ORDER BY scenario_key
        """,
    )
    figures: list[dict] = []
    for row in rows:
        if row["computation_status"] == "computed" and row["value"] is not None:
            figures.append(
                figure(
                    f"risk_{row['metric_key']}",
                    f"Risk {row['metric_key']}",
                    kind="model_output",
                    status="computed",
                    value=row["value"],
                    source_table="risk_metric_values",
                    source_row_ids=[row["id"]],
                    source_note=f"Phase 14 {row['metric_key']}.",
                    quality_status=row["quality_status"],
                )
            )
        else:
            figures.append(
                figure(
                    f"risk_{row['metric_key']}",
                    f"Risk {row['metric_key']}",
                    kind="model_output",
                    status=row["computation_status"],
                    source_table="risk_metric_values",
                    source_row_ids=[row["id"]],
                    source_note=f"Phase 14 {row['metric_key']}: "
                    f"{row['reason'] or 'No reason recorded.'}",
                    quality_status=row["quality_status"],
                )
            )
    for check in checks:
        figures.append(
            figure(
                f"control_{check['control_key']}_{check['scope_key']}",
                f"Control {check['control_key']} ({check['scope_key']})",
                kind="model_output",
                status="computed",
                value_text=check["outcome"],
                source_table="risk_control_checks",
                source_row_ids=[check["id"]],
                source_note=f"Observed {check['observed_value']} "
                f"against threshold {check['threshold_value']}. "
                f"{check['reason'] or ''}",
                quality_status=check["quality_status"],
            )
        )
    for scenario in stress:
        if scenario["computation_status"] == "computed" and scenario["impact_pct"] is not None:
            figures.append(
                figure(
                    f"stress_{scenario['scenario_key']}",
                    f"Stress {scenario['scenario_key']}",
                    kind="model_output",
                    status="computed",
                    value=scenario["impact_pct"],
                    unit="percent",
                    source_table="stress_results",
                    source_row_ids=[scenario["id"]],
                    source_note="Simulation arithmetic on stored closes only, never a forecast.",
                    quality_status=scenario["quality_status"],
                )
            )
        else:
            figures.append(
                figure(
                    f"stress_{scenario['scenario_key']}",
                    f"Stress {scenario['scenario_key']}",
                    kind="model_output",
                    status=scenario["computation_status"],
                    source_table="stress_results",
                    source_row_ids=[scenario["id"]],
                    source_note=f"Phase 14 {scenario['scenario_key']}: "
                    f"{scenario['reason'] or 'No reason recorded.'}",
                    quality_status=scenario["quality_status"],
                )
            )
    if not figures:
        figures.append(
            figure(
                "risk_none",
                "Risk metrics",
                kind="model_output",
                status="insufficient_inputs",
                source_table="risk_metric_values",
                source_row_ids=[],
                source_note=f"No stored risk rows for {subject_key}.",
            )
        )
    controls_text = (
        "; ".join(f"{c['control_key']}: {c['rule']}" for c in controls)
        if controls
        else "not available — no stored controls. "
    )
    figure_keys = [f["figure_key"] for f in figures]
    control_cite = next((k for k in figure_keys if k.startswith("control_")), None)
    stress_cite = next((k for k in figure_keys if k.startswith("stress_")), None)
    risk_cite = (
        "risk_volume_liquidity_tier"
        if "risk_volume_liquidity_tier" in figure_keys
        else next((k for k in figure_keys if k.startswith("risk_")), None)
    )
    metrics_cite = (
        "risk_priced_coverage"
        if subject_key == "MARKET" and "risk_priced_coverage" in figure_keys
        else risk_cite
    )
    sections = [
        section(
            "executive_summary",
            f"Risk report for {label}. Risk rows: {len(rows)}; "
            f"flags: {len(flags)}; controls: {len(controls)}; "
            "stress scenarios: " + str(len(stress)) + ". See "
            "risk_forecast_abstention_rate and "
            "risk_priced_coverage."
            if subject_key == "MARKET"
            else f"Risk report for {label}. Risk rows: {len(rows)}; "
            f"flags: {len(flags)}. See risk_volume_liquidity_tier.",
        ),
        section(
            "metrics",
            f"Stored risk metrics are in the figures table; see {metrics_cite}."
            if metrics_cite
            else "Stored risk metrics are not available.",
        ),
        section(
            "controls",
            controls_text
            + (f" See {control_cite}." if control_cite else " Control figures are not available."),
        ),
        section(
            "stress",
            "Stress impacts are simulation arithmetic on "
            "stored closes only."
            + (f" See {stress_cite}." if stress_cite else " Stress figures are not available."),
        ),
        section(
            "thesis",
            "Risk is described from stored rows only; no "
            "new risk number is introduced."
            + (f" See {risk_cite}." if risk_cite else " Risk figures are not available."),
        ),
        section(
            "counter_thesis",
            "Series risk metrics are unavailable on one "
            "price date, so this report cannot speak to "
            "volatility, beta, or drawdown. See "
            + ("risk_technical_coverage_rate." if subject_key == "MARKET" else "risk_volatility."),
        ),
        section(
            "uncertainty",
            "All inputs are UNVERIFIED; flags are review-only."
            + (f" See {risk_cite}." if risk_cite else " Risk figures are not available."),
        ),
        disclosures_section(figures),
    ]
    warnings = []
    for flag in flags:
        warnings.append(
            {
                "warning_kind": "risk_flag",
                "message": flag_message(flag),
                "source_table": "risk_flags",
                "source_row_ids": [flag["id"]],
            }
        )
    return {
        "header": draft_header("risk_report", subject_type, subject_key, label),
        "sections": sections,
        "figures": figures,
        "warnings": warnings,
    }


def build_market_overview(session) -> dict:
    breadth = q(
        session,
        """
        SELECT id, metric_key, metric_value, status,
               quality_status
        FROM market_breadth
        WHERE scope = 'MARKET' AND trading_date = :pdate
        ORDER BY metric_key
        """,
        {"pdate": PRICE_DATE},
    )
    regime = regime_row(session)
    screens = q(
        session,
        """
        SELECT d.name, r.matched_count, r.universe_size,
               r.insufficient_count
        FROM screen_runs r
        JOIN screen_definitions d ON d.id = r.screen_definition_id
        ORDER BY d.name
        """,
    )
    decisions = q(
        session,
        """
        SELECT d.id, s.ticker, d.research_conclusion,
               d.user_facing, d.confidence, d.quality_status
        FROM decisions d
        JOIN securities s ON s.company_id = d.company_id
        WHERE d.is_current ORDER BY s.ticker
        """,
    )
    alert_totals = q(
        session,
        """
        SELECT severity, COUNT(*) AS total
        FROM alerts GROUP BY severity ORDER BY severity
        """,
    )
    figures: list[dict] = []
    for row in breadth:
        b_status = breadth_status(row["status"])
        if row["metric_value"] is None:
            b_status = "insufficient_inputs"
        figures.append(
            figure(
                f"breadth_{row['metric_key']}",
                f"Market {row['metric_key']}",
                kind="deterministic_calculation",
                status=b_status,
                value=row["metric_value"] if b_status == "computed" else None,
                source_table="market_breadth",
                source_row_ids=[row["id"]],
                source_note=f"Phase 12 market breadth for {PRICE_DATE} "
                f"(breadth status: {row['status']}).",
                quality_status=row["quality_status"],
            )
        )
    if regime is not None:
        figures.append(
            figure(
                "macro_regime",
                "Macro regime",
                kind="model_output",
                status="computed",
                value_text=regime["regime_label"],
                source_table="macro_regimes",
                source_row_ids=[regime["id"]],
                source_note="Phase 10 regime label.",
                quality_status=regime["quality_status"],
            )
        )
    for screen in screens:
        figures.append(
            figure(
                f"screen_{screen['name']}",
                f"Screen {screen['name']} matches",
                kind="deterministic_calculation",
                status="computed",
                value=screen["matched_count"],
                unit="matches",
                source_table="screen_runs",
                source_row_ids=[],
                source_note=f"Phase 20 screen over universe "
                f"{screen['universe_size']}; "
                f"{screen['insufficient_count']} insufficient. "
                "Matches are filter results, not opportunities.",
            )
        )
    for decision in decisions:
        figures.append(
            figure(
                f"decision_{decision['ticker']}",
                f"Decision {decision['ticker']}",
                kind="model_output",
                status="computed",
                value_text=decision["research_conclusion"],
                source_table="decisions",
                source_row_ids=[decision["id"]],
                source_note=f"User-facing {decision['user_facing']}, "
                f"confidence {decision['confidence']}.",
                quality_status=decision["quality_status"],
            )
        )
    for total in alert_totals:
        figures.append(
            figure(
                f"alerts_{total['severity'].lower()}",
                f"Alerts {total['severity']}",
                kind="deterministic_calculation",
                status="computed",
                value=total["total"],
                unit="alerts",
                source_table="alerts",
                source_row_ids=[],
                source_note="Phase 21 alerts are notifications, not instructions.",
            )
        )
    breadth_text = (
        "; ".join(
            f"{r['metric_key']}={r['metric_value']}"
            for r in breadth
            if r["metric_value"] is not None
        )
        or "not available"
    )
    regime_text = (
        f"Macro regime: {regime['regime_label']}. " if regime else "Macro regime: not available. "
    )
    screens_text = (
        "; ".join(f"{s['name']}: {s['matched_count']} matches" for s in screens) or "not available"
    )
    decisions_text = (
        "; ".join(
            f"{d['ticker']}: {d['research_conclusion']} (user-facing {d['user_facing']})"
            for d in decisions
        )
        or "not available"
    )
    alerts_text = (
        "; ".join(f"{a['severity']}: {a['total']}" for a in alert_totals) or "not available"
    )
    sections = [
        section(
            "executive_summary",
            f"Market overview for {PRICE_DATE} (data cut-off "
            f"{DATA_CUTOFF_DATE}). Breadth: "
            + breadth_text
            + " "
            + regime_text
            + "See breadth_priced_coverage and "
            "macro_regime.",
        ),
        section(
            "breadth",
            "Market breadth: " + breadth_text + ". Advances, "
            "declines, and turnover are not available: "
            "previous_close and turnover are NULL on all "
            "stored price rows. See breadth_priced_coverage.",
        ),
        section("macro", regime_text + "See macro_regime."),
        section(
            "screens",
            "Screen outcomes (filter results, not "
            "opportunities): " + screens_text + ". See "
            "screen_liquid_leaders.",
        ),
        section(
            "decisions",
            "Decision context: " + decisions_text + ". All "
            "user-facing values are WITHHELD. See "
            "decision_HUBC.",
        ),
        section(
            "alerts",
            "Alert context: " + alerts_text + ". Alerts are "
            "notifications, not instructions. See "
            "alerts_info.",
        ),
        section("thesis", regime_text + "See macro_regime."),
        section(
            "counter_thesis",
            "Coverage is thin: 3 of 470 companies have "
            "stored statements, forecasts are abstained, "
            "and technical values are not calculable. See "
            "breadth_priced_coverage.",
        ),
        section(
            "risks", "All inputs are UNVERIFIED; one price date only. See breadth_priced_coverage."
        ),
        section(
            "uncertainty",
            "No forecast, no backtest result, and no "
            "executable conclusion appears in this report. "
            "See macro_regime.",
        ),
        disclosures_section(figures),
    ]
    warnings = [
        {
            "warning_kind": "missing",
            "message": "Advances/declines are not available: "
            "previous_close is NULL on all stored price rows.",
            "source_table": "market_prices",
            "source_row_ids": [],
        },
        {
            "warning_kind": "missing",
            "message": "Turnover distribution is not available: "
            "turnover is NULL on all stored price rows.",
            "source_table": "market_prices",
            "source_row_ids": [],
        },
        {
            "warning_kind": "coverage",
            "message": "Only 3 of 470 companies have stored statements.",
            "source_table": "financial_statements",
            "source_row_ids": [],
        },
    ]
    return {
        "header": draft_header("market_overview", "market", "market", "Market overview"),
        "sections": sections,
        "figures": figures,
        "warnings": warnings,
    }


BUILDERS = {
    "company_dossier": build_company_dossier,
    "earnings_update": build_earnings_update,
    "valuation_report": build_valuation_report,
    "sector_outlook": build_sector_outlook,
    "event_brief": build_event_brief,
    "portfolio_review": build_portfolio_review,
    "risk_report": build_risk_report,
    "market_overview": lambda session, subject_key: build_market_overview(session),
}


def build_draft(session, template_key: str, subject_key: str) -> dict:
    """Build and section-check a draft. The emitted section
    list must exactly equal the template's section list, or
    the build fails loudly instead of storing a malformed
    report."""
    if template_key not in TEMPLATES:
        raise ValueError(f"unknown template {template_key}")
    builder = BUILDERS[template_key]
    draft = builder(session, subject_key)
    expected = [key for key, _ in TEMPLATES[template_key]["sections"]]
    actual = [s["section_key"] for s in draft["sections"]]
    if actual != expected:
        raise ValueError(
            f"section list mismatch for {template_key}: expected {expected}, got {actual}"
        )
    return draft


SEED_REPORTS = [
    ("company_dossier", "HUBC"),
    ("company_dossier", "NML"),
    ("company_dossier", "OGDC"),
    ("earnings_update", "HUBC"),
    ("earnings_update", "NML"),
    ("earnings_update", "OGDC"),
    ("valuation_report", "HUBC"),
    ("valuation_report", "NML"),
    ("valuation_report", "OGDC"),
    ("sector_outlook", "POWER GENERATION & DISTRIBUTION"),
    ("sector_outlook", "TEXTILE COMPOSITE"),
    ("sector_outlook", "OIL & GAS EXPLORATION COMPANIES"),
    ("event_brief", "macro:2026-10-26:mpc_meeting"),
    ("event_brief", "news:HUBC:earning"),
    ("portfolio_review", "ew_statements_3_balanced"),
    ("portfolio_review", "rule_screen_pass_balanced"),
    ("portfolio_review", "rule_screen_pass_conservative"),
    ("risk_report", "HUBC"),
    ("risk_report", "NML"),
    ("risk_report", "OGDC"),
    ("risk_report", "MARKET"),
    ("market_overview", "market"),
]
