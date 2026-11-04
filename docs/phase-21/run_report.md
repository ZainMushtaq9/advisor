# Phase 21 — Run Report (seed run, evaluation date 2026-11-04)

## Outcome

- 9 rules seeded (v1), 1 preference profile seeded (local,
  in-app only, no quiet window, no muted rules).
- 89 alerts created, all starting NEW, all delivered in-app
  (89 DELIVERED rows, 0 deferred, 0 muted, 0 blocked).
- Severity: 82 INFO, 6 WARNING, 1 CRITICAL (single-name cap
  breach, SIMULATED portfolio only).
- By rule: macro_release 2, earnings_disclosure 1,
  risk_flag_raised 17, control_breach 1, high_volume 68,
  dividend_declared 0, valuation_change 0, technical_event 0,
  price_move 0.
- Prior tables untouched (statements 88, prices 444,
  decisions 4). No quality status changed anywhere.

## Suppression accounting (first commit)

| Reason | Count | Meaning |
|---|---|---|
| FUTURE_SCHEDULED | 2 | SBP minutes due 2026-11-20, MPC meeting 2026-12-14: not yet events |
| STALE | 1 | OGDC earnings 2026-02-23, older than the 90-day window |
| UNKNOWN_DATE | 1 | NML earnings, publication date NULL in Phase 7 |
| NO_EVENT_DATE | 5 | All 5 dividend actions dateless; no date invented |
| NO_SERIES | 3 | One each: valuation change (no prior run), technical event (0 calculable values), price move (previous_close NULL on all rows) |

## Audit corrections made during this run

1. Dedup key fixed before any push: the first key scheme
   (`rule|subject|date`) collapsed the 17 risk flags into 4
   alerts, because several flags share one company and one
   as-of date. The key is now `rule|source_ref|event_date`
   (one row per source event). The first, unpushed commit
   run was truncated (Phase 21 tables only, following the
   Phase 12 downgrade/re-run precedent) and re-run cleanly:
   89 alerts, 0 duplicates.
2. Dry-run fixed to evaluate without seeded rows: the first
   dry-run failed because seeding is a write and dry-run
   deliberately does not write. Dry-run now evaluates from
   the rule spec.
3. Valuation-change gate fixed: distinct `valuation_date`
   values are statement period dates, not run history. The
   rule now compares the two latest rows per
   (security, method) and reports NO_SERIES when no pair has
   two rows (the seed case: exactly one row per pair).

## Idempotency (second commit, same day)

Second commit: 0 alerts created, 0 deliveries, alerts and
deliveries unchanged (89/89). Duplicates counted 53, not 89,
because the high_volume daily limit (100) counts the 68
alerts already created today: 32 duplicates + 36
FREQUENCY_LIMIT = 68 accounted. The limit behaving this way
on re-runs is by design; on a later day the same re-run
would count all 89 as duplicates.

## Lifecycle (live, net-zero)

Alert 1 (macro_release, MPC decision): NEW -> MUTED (until
2026-11-20) -> NEW, muted_until cleared. Unknown alert id
acknowledgement exits 1 with no write. Invalid transitions
are covered by pure tests (RESOLVED is terminal).

## Tests

- Phase 21 pure suite: 14 passed (dedup, staleness boundary,
  future/unknown dates, mixed-batch gating, flag severity
  mapping, quiet windows incl. wrap-around, frequency cap,
  lifecycle incl. terminal RESOLVED, external-channel gate,
  pagination validation, taxonomy coverage, GET-only
  endpoints, no-execution scan, valuation-change pairs).
- Full backend suite: 326 passed, 0 failed (312 prior + 14
  new). Ruff check + format clean on all new/changed files.

## Live API check (TestClient, scratch script, not committed)

- /alerts/rules 200 (9), /alerts/preferences 200 (in-app
  only, consent False), /alerts 200 (89), rule/severity/
  status filters correct, /alerts/1 200 with dedup key,
  /alerts/1/deliveries 200 (in_app DELIVERED), /alerts/runs
  200, /alerts/status 200 (89 NEW; 82/6/1 by severity).
- Unknown alert id 404, unknown rule 404, limit=0 400.
  The 404 detail wording is the app's pre-existing global
  handler (same as the Phase 20 note), left unchanged.

## HBL pending note

Habib Bank Limited (company 277, COMMERCIAL BANKS) has a
high_volume alert (its 2026-11-03 quote is stored) but no
fundamental, valuation, or decision-derived alert: its CY2025
statements are not loaded (PDF blocked at download;
live-browser download runs separately). A Phase 7 load plus a
Phase 21 re-run adds HBL's evidence without redesign; the
banking rule (no industrial ratios blindly applied) carries
forward.

## Verdict

PARTIALLY COMPLETE. The engine, ledger, delivery, dedup,
lifecycle, and API are complete and verified, but coverage
is 89 alerts from stored rows only: 4 rules fire nothing for
lack of a series or a date, HBL has no statement-derived
alert, and no external channel exists by design.
