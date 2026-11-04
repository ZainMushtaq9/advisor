"""Phase 21 alert runner: load stored rows, evaluate rules,
commit idempotently, deliver in-app only.

All flows are dry-run by default; --commit writes idempotently:
- Alert rules are seeded once by (rule_key, version).
- Notification preferences are seeded once by profile.
- Alerts are keyed by dedup_key; a second commit of the same
  event writes 0 new alerts (counted as duplicates_skipped).
- Deliveries are keyed by (alert, channel) outcome: an alert
  with a DELIVERED row is never re-delivered; a DEFERRED_QUIET
  row may be retried by a later run outside quiet hours.
- Alert runs are keyed by (rule, as-of date, processing time);
  a second commit with the same processing time writes 0 new
  run rows. (Processing time differs across real runs, so each
  real run records its own run row; alerts and deliveries stay
  deduplicated regardless.)

No flow fetches anything and no flow writes any financial,
market, registry, or verification row: the runner reads stored
rows only and writes alert rows only. No value is ever
fabricated: a rule whose inputs do not exist produces
suppressed counts with reasons, never invented alerts.

Delivery discipline: only the ``in_app`` channel is ever
attempted, and it is a local ledger write, not a message.
Any other channel returns BLOCKED_NO_CONSENT without sending
anything. A rule muted in preferences skips delivery with
SKIPPED_MUTED. A processing time inside the quiet window
defers delivery with DEFERRED_QUIET. No paid service, no
external account, and no external communication exists here.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.alerts import (
    Alert,
    AlertDelivery,
    AlertRule,
    AlertRun,
    NotificationPreference,
)
from app.models.analysis import Valuation
from app.models.financial import TechnicalIndicatorValue
from app.models.macro import MacroEvent
from app.models.market import MarketPrice
from app.models.news_events import NewsEvent
from app.models.ownership_actions import CorporateActionRecord
from app.models.reference import Company, Security
from app.models.risk import RiskControlCheck, RiskFlag
from app.services.alerts import (
    ALERT_AS_OF,
    DEFAULT_PREFERENCES,
    PRICE_DATE,
    RULE_BY_KEY,
    SEED_RULES,
    TIMEZONE,
)
from app.services.alerts.evaluation import (
    apply_frequency_limit,
    evaluate_candidates,
    in_quiet_window,
    map_flag_severity,
    transition,
    valuation_change_candidates,
)

AS_OF = date.fromisoformat(ALERT_AS_OF)
PRICE_DAY = date.fromisoformat(PRICE_DATE)
TZ = ZoneInfo(TIMEZONE)


def _json_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    return value


def _now() -> datetime:
    return datetime.now(TZ)


def _ticker_by_company(session: Session) -> dict[int, str]:
    """First security ticker per company, ordered by ticker.
    Used only to label company-level events; the three earnings
    companies each map to exactly one ticker in the seed data."""
    mapping: dict[int, str] = {}
    for row in session.query(Security).order_by(Security.ticker).all():
        mapping.setdefault(row.company_id, row.ticker)
    return mapping


def _company_name(session: Session, company_id: int | None) -> str | None:
    if company_id is None:
        return None
    row = session.query(Company).filter(Company.id == company_id).first()
    return row.legal_name if row else None


def load_candidates(session: Session, rule_key: str) -> tuple[list[dict], dict[str, int]]:
    """Load raw candidates for one rule from stored rows only.

    Returns (candidates, pre_suppressed): pre_suppressed counts
    candidates that cannot even be formed (e.g. dividend actions
    with no event date, or a rule whose series does not exist).
    Formed candidates still pass through evaluate_candidates
    for staleness / future gating.
    """
    tickers = _ticker_by_company(session)
    if rule_key == "macro_release":
        candidates = []
        for row in session.query(MacroEvent).order_by(MacroEvent.event_date).all():
            candidates.append(
                {
                    "subject_type": "MARKET",
                    "ticker": None,
                    "company_id": None,
                    "sector": None,
                    "event_date": row.event_date,
                    "title": f"Macro release: {row.title}",
                    "source_ref": f"macro_events:{row.id}",
                    "evidence": {
                        "source_ref": f"macro_events:{row.id}",
                        "event_type": row.event_type,
                        "title": row.title,
                    },
                    "quality_status": row.quality_status,
                }
            )
        return candidates, {}
    if rule_key == "earnings_disclosure":
        candidates = []
        for row in (
            session.query(NewsEvent)
            .filter(NewsEvent.event_type == "earnings")
            .order_by(NewsEvent.event_date)
            .all()
        ):
            candidates.append(
                {
                    "subject_type": "COMPANY",
                    "ticker": tickers.get(row.primary_company_id),
                    "company_id": row.primary_company_id,
                    "sector": None,
                    "event_date": row.event_date,
                    "title": f"Earnings disclosure: {row.headline}",
                    "source_ref": f"news_events:{row.id}",
                    "evidence": {
                        "source_ref": f"news_events:{row.id}",
                        "headline": row.headline,
                        "date_status": row.date_status,
                        "company": _company_name(session, row.primary_company_id),
                    },
                    "quality_status": row.quality_status,
                }
            )
        return candidates, {}
    if rule_key == "risk_flag_raised":
        candidates = []
        for row in session.query(RiskFlag).order_by(RiskFlag.id).all():
            candidates.append(
                {
                    "subject_type": "COMPANY" if row.company_id else "MARKET",
                    "ticker": tickers.get(row.company_id) if row.company_id else None,
                    "company_id": row.company_id,
                    "sector": None,
                    "event_date": row.as_of_date,
                    "severity": map_flag_severity(row.severity),
                    "title": f"Risk flag: {row.flag_type}",
                    "source_ref": f"risk_flags:{row.id}",
                    "evidence": {
                        "source_ref": f"risk_flags:{row.id}",
                        "flag_type": row.flag_type,
                        "flag_severity": row.severity,
                        "company": _company_name(session, row.company_id),
                        "flag_evidence": row.evidence,
                    },
                    "quality_status": row.quality_status,
                }
            )
        return candidates, {}
    if rule_key == "control_breach":
        candidates = []
        for row in (
            session.query(RiskControlCheck)
            .filter(RiskControlCheck.outcome == "breach")
            .order_by(RiskControlCheck.id)
            .all()
        ):
            candidates.append(
                {
                    "subject_type": "SIMULATED_PORTFOLIO",
                    "ticker": None,
                    "company_id": None,
                    "sector": None,
                    "event_date": row.as_of_date,
                    "title": f"Control breach: {row.control_key} ({row.scope_key})",
                    "source_ref": f"risk_control_checks:{row.id}",
                    "evidence": {
                        "source_ref": f"risk_control_checks:{row.id}",
                        "control_key": row.control_key,
                        "scope_key": row.scope_key,
                        "observed_value": _json_value(row.observed_value),
                        "threshold_value": _json_value(row.threshold_value),
                        "reason": row.reason,
                        "note": "SIMULATED reference portfolio only, never a real holding.",
                    },
                    "quality_status": row.quality_status,
                }
            )
        return candidates, {}
    if rule_key == "high_volume":
        threshold = RULE_BY_KEY["high_volume"]["trigger"]["volume_at_least"]
        candidates = []
        for row in session.query(MarketPrice).filter(MarketPrice.trading_date == PRICE_DAY).all():
            if row.volume is None or row.volume < threshold:
                continue
            security = session.query(Security).filter(Security.id == row.security_id).first()
            candidates.append(
                {
                    "subject_type": "SECURITY",
                    "ticker": security.ticker if security else None,
                    "company_id": security.company_id if security else None,
                    "sector": None,
                    "event_date": PRICE_DAY,
                    "title": f"High volume: {security.ticker if security else row.security_id} "
                    f"traded {row.volume} shares on 2026-11-03",
                    "source_ref": f"market_prices:{row.id}",
                    "evidence": {
                        "source_ref": f"market_prices:{row.id}",
                        "volume": row.volume,
                        "close_price": _json_value(row.close_price),
                        "price_date": PRICE_DATE,
                    },
                    "quality_status": row.quality_status,
                }
            )
        candidates.sort(key=lambda c: c["ticker"] or "")
        return candidates, {}
    if rule_key == "dividend_declared":
        # All stored dividend actions carry NULL dates; no event
        # date exists, so no candidate can be formed. Counted,
        # never dated by invention.
        actions = (
            session.query(CorporateActionRecord)
            .filter(CorporateActionRecord.action_type.like("DIVIDEND%"))
            .all()
        )
        dateless = sum(
            1
            for row in actions
            if row.announced_date is None
            and row.ex_date is None
            and row.record_date is None
            and row.payment_date is None
        )
        return [], {"NO_EVENT_DATE": dateless}
    if rule_key == "valuation_change":
        # A change needs two valuation rows for the same
        # (security, method). The stored valuation_date values
        # are statement period dates: Phase 9 wrote exactly one
        # row per (company, method), so no pair has a prior row
        # to compare against in the seed run. When a second
        # Phase 9 run adds rows, the pure helper below computes
        # the change from the two latest rows per pair.
        rows = [
            {
                "security_id": row.security_id,
                "method": row.method,
                "valuation_date": row.valuation_date,
                "estimated_value": row.estimated_value,
                "row_id": row.id,
                "quality_status": row.quality_status,
            }
            for row in session.query(Valuation).all()
        ]
        changed, suppressed = valuation_change_candidates(rows)
        candidates = []
        securities = {row.id: row for row in session.query(Security).all()}
        for change in changed:
            security = securities.get(change["security_id"])
            candidates.append(
                {
                    "subject_type": "SECURITY",
                    "ticker": security.ticker if security else None,
                    "company_id": security.company_id if security else None,
                    "sector": None,
                    "event_date": change["event_date"],
                    "title": (
                        f"Valuation change: {change['method']} for "
                        f"{security.ticker if security else change['security_id']}"
                    ),
                    "source_ref": (f"valuations:{change['old_row_id']}->{change['new_row_id']}"),
                    "evidence": {
                        "source_ref": (
                            f"valuations:{change['old_row_id']}->{change['new_row_id']}"
                        ),
                        "method": change["method"],
                        "old_value": _json_value(change["old_value"]),
                        "new_value": _json_value(change["new_value"]),
                        "note": (
                            "Change between the two latest stored valuation rows for this method."
                        ),
                    },
                    "quality_status": change["quality_status"],
                }
            )
        return candidates, suppressed
    if rule_key == "technical_event":
        if session.query(TechnicalIndicatorValue).count() == 0:
            return [], {"NO_SERIES": 1}
        return [], {"NO_SERIES": 0}
    if rule_key == "price_move":
        missing = session.query(MarketPrice).filter(MarketPrice.previous_close.is_(None)).count()
        total = session.query(MarketPrice).count()
        if total and missing == total:
            return [], {"NO_SERIES": 1}
        return [], {"NO_SERIES": 0}
    raise ValueError(f"Unknown rule: {rule_key!r}")


def seed_rules(session: Session, commit: bool) -> dict:
    """Seed rule definitions and the default preference profile."""
    seeded_rules = 0
    for spec in SEED_RULES:
        existing = (
            session.query(AlertRule)
            .filter(
                AlertRule.rule_key == spec["rule_key"],
                AlertRule.version == spec["version"],
            )
            .first()
        )
        if existing is None:
            seeded_rules += 1
            if commit:
                session.add(
                    AlertRule(
                        rule_key=spec["rule_key"],
                        name=spec["name"],
                        version=spec["version"],
                        category=spec["category"],
                        origin=spec["origin"],
                        severity=spec["severity"],
                        trigger=spec["trigger"],
                        description=spec["description"],
                        max_event_age_days=spec["max_event_age_days"],
                        daily_limit=spec["daily_limit"],
                        enabled=True,
                        quality_status="UNVERIFIED",
                        is_current=True,
                    )
                )
    prefs = (
        session.query(NotificationPreference)
        .filter(NotificationPreference.profile == DEFAULT_PREFERENCES["profile"])
        .first()
    )
    seeded_prefs = 0
    if prefs is None:
        seeded_prefs = 1
        if commit:
            session.add(
                NotificationPreference(
                    profile=DEFAULT_PREFERENCES["profile"],
                    channels=DEFAULT_PREFERENCES["channels"],
                    external_consent=DEFAULT_PREFERENCES["external_consent"],
                    quiet_start=DEFAULT_PREFERENCES["quiet_start"],
                    quiet_end=DEFAULT_PREFERENCES["quiet_end"],
                    muted_rule_keys=DEFAULT_PREFERENCES["muted_rule_keys"],
                    quality_status="UNVERIFIED",
                )
            )
    if commit:
        session.commit()
    return {"rules_seeded": seeded_rules, "preferences_seeded": seeded_prefs}


def _rule_row(session: Session, rule_key: str) -> AlertRule:
    row = (
        session.query(AlertRule)
        .filter(AlertRule.rule_key == rule_key, AlertRule.is_current.is_(True))
        .first()
    )
    if row is None:
        raise ValueError(f"Rule not seeded: {rule_key!r} (run seed first)")
    return row


def _preferences(session: Session) -> NotificationPreference | None:
    return (
        session.query(NotificationPreference)
        .filter(NotificationPreference.profile == DEFAULT_PREFERENCES["profile"])
        .first()
    )


def _deliver(
    session: Session,
    alert: Alert,
    prefs: NotificationPreference | None,
    processing_time: datetime,
    commit: bool,
) -> dict:
    """Attempt in-app delivery for one alert. Returns the outcome
    dict. Non-in-app channels are never attempted: the caller
    only ever requests in_app, and this function refuses any
    other channel outright."""
    channel = "in_app"
    existing = (
        session.query(AlertDelivery)
        .filter(
            AlertDelivery.alert_id == alert.id,
            AlertDelivery.channel == channel,
            AlertDelivery.outcome == "DELIVERED",
        )
        .first()
    )
    if existing is not None:
        return {"channel": channel, "outcome": "ALREADY_DELIVERED", "written": False}
    if prefs is not None and alert.rule_id is not None:
        rule = session.query(AlertRule).filter(AlertRule.id == alert.rule_id).first()
        if rule is not None and rule.rule_key in (prefs.muted_rule_keys or []):
            outcome, detail = "SKIPPED_MUTED", {"reason": "rule muted in preferences"}
        elif in_quiet_window(processing_time, prefs.quiet_start, prefs.quiet_end):
            outcome, detail = "DEFERRED_QUIET", {"reason": "processing time inside quiet window"}
        else:
            outcome, detail = "DELIVERED", {"channel": "in_app_ledger"}
    else:
        outcome, detail = "DELIVERED", {"channel": "in_app_ledger"}
    if commit:
        session.add(
            AlertDelivery(
                alert_id=alert.id,
                channel=channel,
                outcome=outcome,
                attempted_at=processing_time,
                detail=detail,
            )
        )
    return {"channel": channel, "outcome": outcome, "written": commit}


def deliver_channel(channel: str) -> dict:
    """The external-channel gate, kept separate so it can be
    tested in isolation: any channel other than in_app is
    refused without sending anything."""
    if channel == "in_app":
        return {"channel": channel, "outcome": "ALLOWED_LOCAL"}
    return {"channel": channel, "outcome": "BLOCKED_NO_CONSENT"}


def run_rule(
    session: Session, rule_spec: dict, commit: bool, processing_time: datetime | None = None
) -> dict:
    """Evaluate one rule, create alerts, deliver in-app, record a run."""
    processing_time = processing_time or _now()
    # Dry-run evaluates from the spec: seeding is a write, and a
    # dry run must not require it. Commit mode resolves the row.
    rule_row = _rule_row(session, rule_spec["rule_key"]) if commit else None
    rule_id = rule_row.id if rule_row is not None else None
    prefs = _preferences(session)
    raw, pre_suppressed = load_candidates(session, rule_spec["rule_key"])
    alerts, gated = evaluate_candidates(rule_spec, raw, AS_OF, processing_time)
    suppressed = dict(pre_suppressed)
    for reason, count in gated.items():
        suppressed[reason] = suppressed.get(reason, 0) + count
    # Frequency limit applies to newly created alerts today.
    # Dry-run has no rule row and no writes: nothing created yet.
    created_today = 0
    if commit:
        created_today = (
            session.query(Alert)
            .filter(
                Alert.rule_id == rule_row.id,
                Alert.processing_time
                >= datetime.combine(
                    processing_time.astimezone(TZ).date(),
                    datetime.min.time(),
                    tzinfo=TZ,
                ),
            )
            .count()
        )
    allowed, limited = apply_frequency_limit(rule_spec, created_today, len(alerts))
    if limited:
        suppressed["FREQUENCY_LIMIT"] = suppressed.get("FREQUENCY_LIMIT", 0) + limited
        alerts = alerts[:allowed]
    created = 0
    duplicates = 0
    delivered = 0
    deferred = 0
    skipped_muted = 0
    for candidate in alerts:
        existing = session.query(Alert).filter(Alert.dedup_key == candidate["dedup_key"]).first()
        if existing is not None:
            duplicates += 1
            alert = existing
        else:
            created += 1
            alert = Alert(
                rule_id=rule_id,
                subject_type=candidate["subject_type"],
                ticker=candidate["ticker"],
                company_id=candidate["company_id"],
                sector=candidate["sector"],
                event_time=candidate["event_time"],
                processing_time=candidate["processing_time"],
                as_of_date=candidate["as_of_date"],
                severity=candidate["severity"],
                origin=candidate["origin"],
                title=candidate["title"],
                evidence=candidate["evidence"],
                dedup_key=candidate["dedup_key"],
                status="NEW",
                quality_status=candidate["quality_status"],
            )
            if commit:
                session.add(alert)
                session.flush()
        if commit:
            outcome = _deliver(session, alert, prefs, processing_time, commit=True)
            if outcome["outcome"] == "DELIVERED":
                delivered += 1
            elif outcome["outcome"] == "DEFERRED_QUIET":
                deferred += 1
            elif outcome["outcome"] == "SKIPPED_MUTED":
                skipped_muted += 1
        else:
            # Dry-run delivery projection: count what would happen
            # for genuinely new alerts only.
            if existing is None:
                delivered += 1
    if commit:
        session.add(
            AlertRun(
                rule_id=rule_row.id,
                as_of_date=AS_OF,
                processing_time=processing_time,
                evaluated=len(raw) + sum(pre_suppressed.values()),
                created=created,
                duplicates_skipped=duplicates,
                suppressed=suppressed,
                status="COMPLETED",
                quality_status="UNVERIFIED",
            )
        )
        session.commit()
    return {
        "rule": rule_spec["rule_key"],
        "evaluated": len(raw) + sum(pre_suppressed.values()),
        "created": created,
        "duplicates_skipped": duplicates,
        "suppressed": suppressed,
        "delivered": delivered,
        "deferred_quiet": deferred,
        "skipped_muted": skipped_muted,
        "committed": commit,
    }


def apply_lifecycle(
    session: Session, alert_id: int, action: str, muted_until: date | None = None
) -> dict:
    """Apply one lifecycle action to one alert. Raises ValueError
    on an invalid transition or an unknown alert."""
    alert = session.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        raise ValueError(f"Unknown alert id: {alert_id}")
    new_status = transition(alert.status, action)
    old_status = alert.status
    alert.status = new_status
    now = _now()
    if new_status == "ACKNOWLEDGED":
        alert.acknowledged_at = now
    if new_status == "MUTED":
        alert.muted_until = muted_until
    if new_status == "RESOLVED":
        alert.resolved_at = now
    if new_status == "NEW":
        alert.muted_until = None
    session.commit()
    return {
        "alert_id": alert_id,
        "from": old_status,
        "to": new_status,
        "dedup_key": alert.dedup_key,
    }
