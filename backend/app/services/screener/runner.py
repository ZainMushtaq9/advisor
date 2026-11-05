"""Phase 20 screener runner: load stored rows, evaluate screens,
commit idempotently.

All flows are dry-run by default; --commit writes idempotently:
- Screen definitions are seeded once by (name, version).
- A screen run is keyed by (definition, as-of date); a second
  commit of the same pair writes 0 new rows.
- Screen results are keyed by (run, security); a second commit
  writes 0 new rows. Results are never overwritten: a changed
  definition needs a new version, and a changed as-of date is a
  new run. That is what makes saved screens reproducible.

No flow fetches anything and no flow writes any financial,
market, registry, or verification row: the runner reads stored
rows only and writes screener rows only. No value is ever
fabricated: a security without a stored value gets a missing
or not_applicable outcome with its reason, and a security
without any scored filter is INSUFFICIENT_DATA, never a match.

Decision context: each result's evidence carries the security's
Phase 15 decision (research conclusion, WITHHELD user-facing
value, confidence) when one exists — as evidence only. It is
never a score input, and a screen match never upgrades it to
a recommendation.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.analysis import Valuation
from app.models.decision import Decision
from app.models.financial import (
    FinancialStatement,
    FundamentalMetricDefinition,
    FundamentalMetricValue,
)
from app.models.market import MarketPrice
from app.models.news_events import NewsEvent, NewsEventCompany
from app.models.ownership_actions import CorporateActionRecord, LiquidityObservation
from app.models.reference import Company, Sector, Security
from app.models.risk import RiskFlag
from app.models.screener import ScreenDefinition, ScreenResult, ScreenRun
from app.services.screener import PRICE_DATE, SCREEN_AS_OF, SEED_SCREENS
from app.services.screener.filters import evaluate_filter, validate_filter_entry
from app.services.screener.ranking import score_outcomes

AS_OF = date.fromisoformat(SCREEN_AS_OF)
PRICE_DAY = date.fromisoformat(PRICE_DATE)

# Latest statement period ends per company, for the staleness
# filter (Phase 8/14 evidence: HUBC 2026-06-30, NML 2025-03-31,
# OGDC 2025-12-31 at the Phase 14 run; recomputed live here
# from stored statements, never hardcoded).
STALE_THRESHOLD_DAYS = 365


def _json_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    return value


def _outcome_to_json(outcome: dict) -> dict:
    evidence = dict(outcome["evidence"])
    for key in ("value", "threshold", "percentile"):
        if key in evidence:
            evidence[key] = _json_value(evidence[key])
    return {
        "filter": outcome["filter"],
        "outcome": outcome["outcome"],
        "reason": outcome["reason"],
        "value": _json_value(outcome.get("value")),
        "percentile": _json_value(outcome.get("percentile")),
        "evidence": evidence,
    }


def load_universe(session: Session, universe: str, as_of: date = AS_OF) -> list[dict]:
    """Build one security dict per universe member from stored
    rows only. "priced" = all 470 registry securities;
    "decision_companies" = the 4 securities with a Phase 15
    decision."""
    securities = session.query(Security).order_by(Security.ticker).all()
    company_by_id = {c.id: c for c in session.query(Company).all()}
    sector_by_id = {s.id: s for s in session.query(Sector).all()}
    if universe == "decision_companies":
        decision_security_ids = {
            d.security_id for d in session.query(Decision).all() if d.security_id
        }
        securities = [s for s in securities if s.id in decision_security_ids]
    elif universe != "priced":
        raise ValueError(f"Unknown universe: {universe!r}")

    price_by_security: dict[int, MarketPrice] = {}
    for row in session.query(MarketPrice).filter(MarketPrice.trading_date == PRICE_DAY).all():
        price_by_security[row.security_id] = row

    definition_by_id = {d.id: d for d in session.query(FundamentalMetricDefinition).all()}
    fundamentals: dict[int, dict] = {}
    for row in (
        session.query(FundamentalMetricValue)
        .order_by(FundamentalMetricValue.period_end.desc())
        .all()
    ):
        definition = definition_by_id.get(row.metric_definition_id)
        if definition is None:
            continue
        per_company = fundamentals.setdefault(row.company_id, {})
        # Latest period_end wins (rows arrive newest first).
        if definition.metric_key not in per_company:
            per_company[definition.metric_key] = {
                "value": row.value,
                "status": row.computation_status,
                "period_end": str(row.period_end),
                "row_id": row.id,
            }

    valuations: dict[int, dict] = {}
    for row in session.query(Valuation).all():
        per_security = valuations.setdefault(row.security_id, {})
        status = (row.assumptions or {}).get("computation_status")
        per_security[row.method] = {
            "value": row.estimated_value,
            "status": status,
            "period_note": (row.assumptions or {}).get("period_note"),
        }

    liquidity: dict[int, dict] = {}
    for row in (
        session.query(LiquidityObservation)
        .filter(LiquidityObservation.trading_date == PRICE_DAY)
        .all()
    ):
        per_security = liquidity.setdefault(row.security_id, {})
        per_security[row.metric_key] = row.metric_value

    dividends: dict[int, dict] = {}
    for row in session.query(CorporateActionRecord).all():
        # Stored action types are DIVIDEND_CASH (Phase 12);
        # match the dividend family, never a single spelling.
        if not (row.action_type or "").startswith("DIVIDEND"):
            continue
        current = dividends.get(row.company_id)
        if current is None or (row.amount_per_share or Decimal(0)) > (
            current["amount"] or Decimal(0)
        ):
            dividends[row.company_id] = {
                "amount": row.amount_per_share,
                "dates_known": bool(
                    row.announced_date or row.ex_date or row.record_date or row.payment_date
                ),
                # All stored actions carry NULL dates, so the
                # latest action cannot be determined: the
                # stored figure is the maximum stored amount,
                # labelled as such, never as "latest".
                "note": (
                    "Maximum stored dividend per share; action "
                    "dates are all NULL, so the latest action "
                    "cannot be determined."
                ),
            }

    news_counts: dict[int, int] = {}
    for row in session.query(NewsEventCompany).all():
        news_counts[row.company_id] = news_counts.get(row.company_id, 0) + 1
    for row in session.query(NewsEvent).all():
        if row.primary_company_id is not None:
            news_counts[row.primary_company_id] = news_counts.get(row.primary_company_id, 0) + 1

    flag_counts: dict[int, int] = {}
    for row in session.query(RiskFlag).all():
        if row.company_id is not None:
            flag_counts[row.company_id] = flag_counts.get(row.company_id, 0) + 1

    latest_period_end: dict[int, date] = {}
    for row in session.query(FinancialStatement).all():
        current = latest_period_end.get(row.company_id)
        if current is None or row.period_end > current:
            latest_period_end[row.company_id] = row.period_end

    decisions: dict[int, dict] = {}
    for row in session.query(Decision).all():
        if row.security_id is not None:
            decisions[row.security_id] = {
                "research_conclusion": row.research_conclusion,
                "user_facing": row.user_facing,
                "confidence": row.confidence,
                "decision_date": str(row.decision_date),
            }

    universe_rows: list[dict] = []
    for security in securities:
        company = company_by_id.get(security.company_id)
        sector_name = None
        if company is not None and company.sector_id is not None:
            sector = sector_by_id.get(company.sector_id)
            sector_name = sector.name if sector else None
        price = price_by_security.get(security.id)
        period_end = latest_period_end.get(security.company_id)
        dividend = dividends.get(security.company_id)
        universe_rows.append(
            {
                "ticker": security.ticker,
                "security_id": security.id,
                "company_id": security.company_id,
                "sector": sector_name,
                "close_price": price.close_price if price else None,
                "price_date": str(PRICE_DAY) if price else None,
                "volume": price.volume if price else None,
                "volume_share_pct": (liquidity.get(security.id) or {}).get("volume_share_pct"),
                "fundamentals": fundamentals.get(security.company_id, {}),
                "valuations": valuations.get(security.id, {}),
                "dividend_per_share": dividend["amount"] if dividend else None,
                "dividend_dates_known": dividend["dates_known"] if dividend else False,
                "dividend_amount_note": dividend["note"] if dividend else None,
                "news_event_count": news_counts.get(security.company_id, 0),
                "risk_flag_count": flag_counts.get(security.company_id, 0),
                "statement_age_days": ((as_of - period_end).days if period_end else None),
                "statement_period_end": str(period_end) if period_end else None,
                "decision": decisions.get(security.id),
            }
        )
    return universe_rows


def _peer_values(filter_key: str, universe_rows: list[dict]) -> list:
    """Collect present values for a percentile filter across
    the peer universe. Technical filters have no peer set."""
    values = []
    for row in universe_rows:
        if filter_key in ("close_price", "volume", "volume_share_pct"):
            value = row.get(filter_key)
        elif filter_key in (
            "roe_total",
            "roa",
            "net_margin",
            "gross_margin",
            "current_ratio",
            "receivables_days",
            "debt_to_equity",
        ):
            metric = (row.get("fundamentals") or {}).get(filter_key)
            value = metric["value"] if metric else None
        elif filter_key == "pe_trailing":
            valuation = (row.get("valuations") or {}).get("multiples:pe_trailing")
            value = valuation["value"] if valuation else None
        else:
            value = None
        if value is not None:
            values.append(value)
    return values


def evaluate_screen(screen: dict, universe_rows: list[dict], as_of_date: str = SCREEN_AS_OF) -> list[dict]:
    """Evaluate one seed screen over loaded universe rows.

    Returns one result dict per universe member, each with
    outcome, score, per-filter outcomes, and evidence. The
    peer values for percentile filters are computed once per
    filter from the same universe rows the screen runs over —
    never from a different date or a wider set."""
    filters = [validate_filter_entry(entry) for entry in screen["filters"]]
    peer_cache: dict[str, list] = {}
    results: list[dict] = []
    for row in universe_rows:
        outcomes = []
        for entry in filters:
            if entry["kind"] == "percentile":
                if entry["filter"] not in peer_cache:
                    peer_cache[entry["filter"]] = _peer_values(entry["filter"], universe_rows)
                peers = peer_cache[entry["filter"]]
            else:
                peers = None
            outcomes.append(evaluate_filter(entry, row, peers))
        scored = score_outcomes(outcomes)
        reason_codes = list(scored["reason_codes"])
        # Staleness is an evidence flag on statement-bearing
        # results, never a score input.
        age = row.get("statement_age_days")
        if age is not None and age > STALE_THRESHOLD_DAYS:
            reason_codes.append("STALE_INPUT")
        evidence = {
            "screen": screen["name"],
            "version": screen["version"],
            "score_version": "screener-score-v1",
            "as_of_date": as_of_date,
            "price_date": PRICE_DATE,
            "sector": row.get("sector"),
            "decision_context": row.get("decision"),
            "statement_age_days": age,
            "filter_outcomes": [_outcome_to_json(o) for o in outcomes],
            "disclaimer": (
                "Screen match, not an investment opportunity, not a recommendation, not a forecast."
            ),
        }
        results.append(
            {
                "ticker": row["ticker"],
                "security_id": row["security_id"],
                "outcome": scored["outcome"],
                "score": scored["score"],
                "passed_count": scored["passed_count"],
                "scored_count": scored["scored_count"],
                "reason_codes": reason_codes,
                "evidence": evidence,
            }
        )
    return results


def seed_definitions(session: Session, commit: bool) -> dict:
    """Seed the five v1 screens. Returns counts; writes
    nothing when commit is False ("to_write" is the would-write
    count in that case)."""
    seen = 0
    written = 0
    to_write = 0
    for screen in SEED_SCREENS:
        seen += 1
        existing = (
            session.query(ScreenDefinition)
            .filter(
                ScreenDefinition.name == screen["name"],
                ScreenDefinition.version == screen["version"],
            )
            .first()
        )
        if existing is not None:
            continue
        to_write += 1
        if commit:
            session.add(
                ScreenDefinition(
                    name=screen["name"],
                    version=screen["version"],
                    description=screen["description"],
                    universe=screen["universe"],
                    filters=screen["filters"],
                    quality_status="UNVERIFIED",
                    is_current=True,
                )
            )
            written += 1
    if commit:
        session.commit()
    return {"seen": seen, "written": written, "to_write": to_write}


def run_screen(session: Session, screen: dict, commit: bool, as_of: date | None = None) -> dict:
    """Run one seed screen. Returns the run summary with
    per-ticker outcomes. Idempotent on (definition, as-of).
    as_of defaults to SCREEN_AS_OF (2026-11-04). A later as-of
    creates a NEW run snapshot instead of overwriting: the HBL
    re-run batch re-runs only dividend_payers at 2026-11-05,
    the one screen whose HBL outcome changed (NO_MATCH ->
    MATCH on its newly stored dividend actions); the other
    screens' stored HBL outcomes are unchanged and their
    2026-11-04 runs stand."""
    as_of = as_of or AS_OF
    as_of_str = as_of.isoformat()
    definition = (
        session.query(ScreenDefinition)
        .filter(
            ScreenDefinition.name == screen["name"],
            ScreenDefinition.version == screen["version"],
        )
        .first()
    )
    if definition is None:
        if commit:
            return {"error": f"Screen not seeded: {screen['name']} {screen['version']}"}
        # Dry-run before the first commit: evaluate fresh
        # without a stored definition row. Nothing is written
        # and no run row is fabricated.
        universe_rows = load_universe(session, screen["universe"], as_of)
        results = evaluate_screen(screen, universe_rows, as_of_str)
        matched = sum(1 for r in results if r["outcome"] == "MATCH")
        insufficient = sum(1 for r in results if r["outcome"] == "INSUFFICIENT_DATA")
        return {
            "screen": screen["name"],
            "version": screen["version"],
            "as_of_date": as_of_str,
            "run_reused": False,
            "written": 0,
            "would_write": len(results),
            "universe_size": len(results),
            "matched_count": matched,
            "insufficient_count": insufficient,
            "matched_tickers": [r["ticker"] for r in results if r["outcome"] == "MATCH"],
            "insufficient_tickers": [
                r["ticker"] for r in results if r["outcome"] == "INSUFFICIENT_DATA"
            ],
            "note": "Dry-run evaluation; definition not yet seeded.",
        }
    existing_run = (
        session.query(ScreenRun)
        .filter(
            ScreenRun.screen_definition_id == definition.id,
            ScreenRun.as_of_date == as_of,
        )
        .first()
    )
    if existing_run is not None:
        stored = (
            session.query(ScreenResult).filter(ScreenResult.screen_run_id == existing_run.id).all()
        )
        return {
            "screen": screen["name"],
            "version": screen["version"],
            "as_of_date": as_of_str,
            "run_reused": True,
            "written": 0,
            "universe_size": existing_run.universe_size,
            "matched_count": existing_run.matched_count,
            "insufficient_count": existing_run.insufficient_count,
            "results": len(stored),
        }
    universe_rows = load_universe(session, screen["universe"], as_of)
    results = evaluate_screen(screen, universe_rows, as_of_str)
    matched = sum(1 for r in results if r["outcome"] == "MATCH")
    insufficient = sum(1 for r in results if r["outcome"] == "INSUFFICIENT_DATA")
    written = 0
    if commit:
        run = ScreenRun(
            screen_definition_id=definition.id,
            as_of_date=as_of,
            universe_size=len(results),
            matched_count=matched,
            insufficient_count=insufficient,
            status="COMPLETED",
            evidence={
                "price_date": PRICE_DATE,
                "score_version": "screener-score-v1",
                "filter_count": len(screen["filters"]),
            },
            quality_status="UNVERIFIED",
        )
        session.add(run)
        session.flush()
        for result in results:
            session.add(
                ScreenResult(
                    screen_run_id=run.id,
                    security_id=result["security_id"],
                    outcome=result["outcome"],
                    score=result["score"],
                    passed_count=result["passed_count"],
                    scored_count=result["scored_count"],
                    reason_codes=result["reason_codes"],
                    evidence=result["evidence"],
                    quality_status="UNVERIFIED",
                )
            )
            written += 1
        session.commit()
    return {
        "screen": screen["name"],
        "version": screen["version"],
        "as_of_date": as_of_str,
        "run_reused": False,
        "written": written,
        "would_write": 0 if commit else len(results),
        "universe_size": len(results),
        "matched_count": matched,
        "insufficient_count": insufficient,
        "matched_tickers": [r["ticker"] for r in results if r["outcome"] == "MATCH"],
        "insufficient_tickers": [
            r["ticker"] for r in results if r["outcome"] == "INSUFFICIENT_DATA"
        ],
    }


def run_all(session: Session, commit: bool, as_of: date | None = None) -> dict:
    """Seed definitions, then run every seed screen."""
    seeded = seed_definitions(session, commit=commit)
    runs = []
    for screen in SEED_SCREENS:
        runs.append(run_screen(session, screen, commit=commit, as_of=as_of))
    return {"seeded": seeded, "runs": runs}
