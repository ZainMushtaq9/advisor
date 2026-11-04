# Phase 21 — Alerts and Event-Driven Monitoring: Implementation Specification

## Scope

Phase 21 notifies about events that already exist in stored rows:
market prices, macro events, news events, risk flags, control
checks, dividend actions, valuations, and technical values. It
introduces no new collection, no new price, no forecast, and no
recommendation. Every alert carries its trigger rule, its source
row reference, its event time, its processing time, its
evidence, its severity, and its deduplication key.

## Tables (migration 20261104_0018)

- `alert_rules`: versioned trigger definitions (rule key, name,
  category, origin, severity, trigger JSON, max event age,
  optional daily limit, enabled flag).
- `notification_preferences`: one local profile row. Channels
  are recorded as in-app enabled and email/SMS/push disabled;
  external consent is False. A quiet window may be set; the
  seed profile sets none, so seed alerts deliver immediately.
- `alerts`: the event ledger. UNIQUE on `dedup_key`, where the
  key is `rule_key|source_ref|event_date`: one row per source
  event, so distinct events for the same subject on the same
  date (e.g. several risk flags for one company) never
  collapse into one another.
- `alert_deliveries`: one attempt row per (alert, channel).
- `alert_runs`: one evaluation pass per (rule, as-of date,
  processing time), with evaluated/created/duplicates/suppressed
  counts. Suppression is evidence, not silence.

## Origin discipline

- OFFICIAL: the event was published by an authority (SBP/PBS
  macro events, issuer earnings disclosures, issuer dividend
  actions). The alert repeats the stored publication fact; it
  does not re-verify it.
- DERIVED: the alert is computed from stored rows (volume
  threshold on the single stored trading date).
- MODEL_WARNING: the alert restates a model output (a risk flag,
  a breached control check). Flags are review-only: never fraud,
  default, or solvency conclusions.

## Delivery discipline

- Only `in_app` is attempted, and it is a local ledger write,
  not a message. Any other channel returns BLOCKED_NO_CONSENT
  without sending anything. No paid service, no external
  account, and no external communication exists in this phase.
- Quiet window: a processing time inside the window defers
  delivery (DEFERRED_QUIET); a later run outside the window
  retries it. The seed profile has no window.
- Rule mute: a rule muted in preferences skips delivery
  (SKIPPED_MUTED) while the alert itself stays NEW.
- Frequency limit: a rule's daily limit caps newly created
  alerts per processing date; excess candidates are suppressed
  as FREQUENCY_LIMIT.
- Idempotency: alerts are keyed by dedup key; deliveries are
  skipped once DELIVERED; runs are keyed by (rule, as-of date,
  processing time). A second identical commit writes no new
  alerts and no new deliveries.

## Staleness and future control

An event is suppressed as STALE when its date is older than
the rule's maximum event age measured against the processing
date, as FUTURE_SCHEDULED when it falls after the evaluation
date, and as UNKNOWN_DATE when the source carries no usable
date. Rules whose series does not exist (dividend actions with
no dates, a single valuation run, zero calculable indicators,
all-NULL previous closes) produce NO_SERIES / NO_EVENT_DATE
suppression counts, never invented alerts.

## Lifecycle

NEW -> ACKNOWLEDGED -> RESOLVED, NEW -> MUTED -> NEW (unmute)
or RESOLVED. RESOLVED is terminal. Transitions run through the
CLI (`scripts/run_alerts.py --acknowledge/--mute/--resolve/
--unmute`); the API is GET-only. Invalid transitions raise and
write nothing.

## False positives and alert volume

False-positive rate is NOT_MEASURABLE in the seed run: no user
feedback labels exist yet (no alert has been acknowledged with
an outcome). What is measured instead: alert volume per rule,
duplicates skipped, and suppression counts by reason. These
are reported in `delivery_dedup_report.md` and served by
`GET /api/v1/alerts/status`. They are not a false-positive
rate, and the status endpoint says so explicitly.

## What this phase does not do

- It does not send email, SMS, or push notifications.
- It does not reintroduce Phase 15 user-facing values (all
  WITHHELD) or Phase 13 forecasts (all abstained) as alert
  content or score inputs.
- It does not present a single-day snapshot as a backtest, a
  screen match as an opportunity, or a flag as a conclusion.
- It does not promote any quality status and does not create
  any broker, order, or execution concept.
