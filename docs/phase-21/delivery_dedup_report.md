# Phase 21 — Delivery, Deduplication, and False-Positive Report

## Delivery

- Channel: in-app ledger only. 89 attempts, 89 DELIVERED,
  0 DEFERRED_QUIET (seed profile has no quiet window),
  0 SKIPPED_MUTED (no muted rules), 0 BLOCKED_NO_CONSENT
  (no external channel ever attempted), 0 FAILED.
- External channels (email, SMS, push) are recorded disabled
  with consent False; the delivery gate refuses them without
  sending anything (pure-tested per channel).
- Retry policy: a DEFERRED_QUIET row is retried by a later
  run outside quiet hours; a DELIVERED row is never retried.
  No deferred rows exist in the seed run, so retry is
  implemented and fixture-tested, not production-observed.
- Failures: a local write error aborts the run instead of
  being recorded as delivered. No failures occurred.

## Deduplication

- Key: `rule_key|source_ref|event_date`, UNIQUE in the
  database. One row per source event.
- First commit: 0 duplicates (fresh ledger). Second commit
  (same day): 53 duplicates + 36 FREQUENCY_LIMIT on
  high_volume = 68 accounted; 0 new alerts, 0 new deliveries.
- Duplicate storms are prevented structurally: re-evaluating
  the same stored event reproduces the same key, and the
  UNIQUE constraint rejects any second row even if the
  application check were bypassed.

## Stale-trigger control

- STALE (1), FUTURE_SCHEDULED (2), UNKNOWN_DATE (1),
  NO_EVENT_DATE (5), NO_SERIES (3) — see run_report.md.
  Stale and future candidates never become alerts, and
  their counts live in `alert_runs.suppressed`, served by
  `GET /api/v1/alerts/runs` and `/alerts/status`.

## Alert volume

- Total 89 alerts from 9 rules on one evaluation date.
  Largest rule: high_volume (68), capped at 100/day.
  No rule exceeded its frequency limit on first commit.
- Volume is reported per rule in every run row; no
  volume-based throttling beyond the per-rule daily limit
  was needed.

## False positives

- False-positive rate: NOT_MEASURABLE. No user feedback
  labels exist yet: all 89 alerts are NEW, none acknowledged
  with an outcome, so no rate can be computed honestly.
- What is measured instead: volume per rule, duplicates
  skipped, and suppression reasons. A future feedback pass
  (acknowledge/resolve outcomes with a correct/incorrect
  marker, which does not exist yet) would be needed before
  any false-positive rate may be claimed.
- Known precision caveat, stated not hidden: high_volume
  alerts are point-in-time threshold crossings on a single
  trading date, not moves or spikes; risk-flag alerts are
  review-only flags, not conclusions; the control-breach
  alert concerns a SIMULATED portfolio, not a real holding.
  Each alert's evidence states its basis so the reader can
  judge it.
