# Phase 25 — Scheduling cadence

Schedules match real source cadence. Nothing is polled
excessively, and nothing assumes the runtime stays on:
the runner is invoked per pass (operator or host cron),
and every schedule is a due-DATE rule, not a timer.

## Source cadence table

| Source / task | Real cadence | Job | Schedule (PKT) |
|---|---|---|---|
| PSX trading session | Mon–Fri (see holiday note) | market_post_close | Weekdays 16:30, post-close — PAUSED (Terms-gated) |
| Issuer filings | Quarterly + annual reports | filing_check | Quarterly, day 15, 09:00 — PAUSED (polling not approved) |
| PBS CPI | Monthly (early month) | macro_release_check | Monthly, day 3, 09:00 — PAUSED (no automated fetch) |
| SBP monetary policy | Roughly six-weekly (MPS + minutes) | macro_release_check | Covered by the monthly check — PAUSED (same reason) |
| System health | Daily operator visibility | system_health | Daily 07:00 |
| Alert digest | Daily operator visibility | alert_digest | Daily 08:00 |
| Stored-state drift | Weekly is enough (state changes only on phase runs) | drift_check | Weekly Monday 07:30 |
| Report QA | Weekly is enough (reports change only on re-runs) | report_qa_audit | Weekly Sunday 08:00 |
| Audit retention | 12-month policy | retention_purge | Manual only — never auto-due |

## Why these times

- Post-close work belongs after the close (16:30 PKT
  leaves margin past the 15:30 regular close).
- Health before digest (07:00 before 08:00) so a digest
  never summarises an unchecked database.
- Drift on Monday, QA on Sunday: the QA audit depends
  on drift_check, but on different weekdays the
  dependency is not due on the QA date, so QA proceeds
  (dependency gating applies only to same-date runs).
  This is deliberate: same-date gating prevents auditing
  numbers from a day whose drift check errored, while
  different-weekday scheduling keeps the weekly cadence
  independent.

## Limitations, stated honestly

- **No PSX holiday calendar.** No verified holiday list
  exists in this project. Trading weekdays are
  Monday–Friday; a weekday with no stored price rows is
  an observed gap, never a claimed holiday and never a
  silent skip.
- **No daemon.** Due-ness is evaluated at invocation
  time. If the runner is not invoked for a month, the
  backlog is bounded (7 per job per pass) and drains
  over successive passes — it never storms.
- **No polling.** No job polls any source on a timer.
  Collection jobs are paused; enabled jobs read stored
  rows only. A future collection implementation must
  still respect source rate limits and the Terms gate.
- **PKT, no DST.** Pakistan has no daylight saving
  (none since 2009), so wall-clock schedules are stable.
- **Catch-up window.** A brand-new job looks back 30
  days, not to epoch; older history is backfilled only
  by explicit `run-one --date` invocations.
