"""Phase 21 alerts and event-driven monitoring models.

Five tables. Design rules from the Phase 21 brief:

- An alert rule is a versioned, reusable trigger definition:
  rule key, category (the brief's taxonomy), origin (OFFICIAL /
  DERIVED / MODEL_WARNING), severity, trigger parameters (JSON),
  maximum event age, optional daily frequency limit, and an
  enabled flag. Rules are seeded by the CLI, never by an API
  write: all Phase 21 API routes are GET-only.
- Notification preferences are a single local profile row.
  Only the in-app channel is deliverable. Email, SMS, and push
  are recorded as disabled and consent for external channels is
  False; the delivery code refuses any non-in-app channel with
  BLOCKED_NO_CONSENT and never attempts an external send. No
  paid delivery service is introduced anywhere.
- An alert is one ledger row per (rule, subject, event date):
  trigger rule, source row reference, event time, processing
  time, evidence, severity, origin, and a deduplication key with
  a UNIQUE constraint. A second evaluation of the same event
  writes nothing: duplicates are skipped, never re-delivered.
- An alert delivery records one attempt per (alert, channel).
  Re-running delivery skips alerts that already have a
  DELIVERED row; a DEFERRED_QUIET row may be retried by a later
  run outside quiet hours. FAILED is a defined outcome that is
  unobserved in the seed run: a local write error aborts the
  run instead of being recorded as delivered.
- An alert run records one evaluation pass per rule: how many
  candidates were evaluated, created, skipped as duplicates,
  and suppressed, with suppression reasons. Suppression is
  evidence, not silence: stale, future-scheduled, dateless,
  and no-series candidates are counted with reasons in the run
  row and in the run report.
- Lifecycle lives on the alert row: NEW -> ACKNOWLEDGED ->
  RESOLVED, NEW -> MUTED -> NEW (unmute) or RESOLVED. RESOLVED
  is terminal. Transitions run through the CLI, never through
  an API write, and invalid transitions are rejected.
- Quality vocabulary mirrors migration 20261104_0003. An alert
  never upgrades a statement, price, calculation, decision, or
  verification row: it carries its source row's quality status.
- No order path exists anywhere in this project, and none is
  added here: alerts notify about stored events; they do not
  trade, recommend, or forecast. Phase 15 user-facing values
  are WITHHELD and Phase 13 forecasts are abstained, and this
  phase reintroduces neither.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

QUALITY_VALUES = (
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "UNVERIFIED",
    "CONFLICTED",
    "MISSING",
    "REJECTED",
    "STALE",
    "PENDING_REVIEW",
)

ORIGIN_VALUES = ("OFFICIAL", "DERIVED", "MODEL_WARNING")
SEVERITY_VALUES = ("INFO", "WARNING", "CRITICAL")
ALERT_STATUS_VALUES = ("NEW", "ACKNOWLEDGED", "MUTED", "RESOLVED")
DELIVERY_OUTCOME_VALUES = (
    "DELIVERED",
    "DEFERRED_QUIET",
    "SKIPPED_MUTED",
    "BLOCKED_NO_CONSENT",
    "FAILED",
)


def _quality_check(table: str) -> CheckConstraint:
    values = ", ".join(f"'{v}'" for v in QUALITY_VALUES)
    return CheckConstraint(f"quality_status IN ({values})", name=f"ck_{table}_quality_status")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rule_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    origin: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    trigger: Mapped[object] = mapped_column(JSON, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    max_event_age_days: Mapped[int] = mapped_column(BigInteger, nullable=False)
    daily_limit: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("rule_key", "version", name="uq_alert_rules_key_version"),
        CheckConstraint(
            f"origin IN ({', '.join(repr(v) for v in ORIGIN_VALUES)})",
            name="ck_alert_rules_origin",
        ),
        CheckConstraint(
            f"severity IN ({', '.join(repr(v) for v in SEVERITY_VALUES)})",
            name="ck_alert_rules_severity",
        ),
        _quality_check("alert_rules"),
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    profile: Mapped[str] = mapped_column(String(100), nullable=False)
    channels: Mapped[object] = mapped_column(JSON, nullable=False)
    external_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quiet_start: Mapped[object] = mapped_column(Time, nullable=True)
    quiet_end: Mapped[object] = mapped_column(Time, nullable=True)
    muted_rule_keys: Mapped[object] = mapped_column(JSON, nullable=False, default=list)
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")

    __table_args__ = (
        UniqueConstraint("profile", name="uq_notification_preferences_profile"),
        _quality_check("notification_preferences"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rule_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("alert_rules.id"), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(50), nullable=True)
    company_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sector: Mapped[str | None] = mapped_column(String(200), nullable=True)
    event_time: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    processing_time: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    as_of_date: Mapped[object] = mapped_column(Date, nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    origin: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence: Mapped[object] = mapped_column(JSON, nullable=False)
    dedup_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="NEW")
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")
    acknowledged_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    muted_until: Mapped[object] = mapped_column(Date, nullable=True)
    resolved_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("dedup_key", name="uq_alerts_dedup_key"),
        Index("idx_alerts_rule", "rule_id"),
        Index("idx_alerts_status", "status"),
        Index("idx_alerts_ticker", "ticker"),
        CheckConstraint(
            f"severity IN ({', '.join(repr(v) for v in SEVERITY_VALUES)})",
            name="ck_alerts_severity",
        ),
        CheckConstraint(
            f"origin IN ({', '.join(repr(v) for v in ORIGIN_VALUES)})",
            name="ck_alerts_origin",
        ),
        CheckConstraint(
            f"status IN ({', '.join(repr(v) for v in ALERT_STATUS_VALUES)})",
            name="ck_alerts_status",
        ),
        _quality_check("alerts"),
    )


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    alert_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("alerts.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    attempted_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    detail: Mapped[object] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_alert_deliveries_alert", "alert_id"),
        CheckConstraint(
            f"outcome IN ({', '.join(repr(v) for v in DELIVERY_OUTCOME_VALUES)})",
            name="ck_alert_deliveries_outcome",
        ),
    )


class AlertRun(Base):
    __tablename__ = "alert_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rule_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("alert_rules.id"), nullable=False)
    as_of_date: Mapped[object] = mapped_column(Date, nullable=False)
    processing_time: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluated: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duplicates_skipped: Mapped[int] = mapped_column(BigInteger, nullable=False)
    suppressed: Mapped[object] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNVERIFIED")

    __table_args__ = (
        UniqueConstraint("rule_id", "as_of_date", "processing_time", name="uq_alert_runs_grain"),
        Index("idx_alert_runs_rule", "rule_id"),
        _quality_check("alert_runs"),
    )
