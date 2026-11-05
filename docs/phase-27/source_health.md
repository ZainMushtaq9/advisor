# Phase 27 — Source Health Snapshot

Freshness is judged per source against that source's own
threshold. A source with no rows is "unknown", never "fresh"
and never zero-filled. Coverage is reported beside freshness,
never merged into it: a source can be fresh and narrow
(statements: 3 of 470 companies) and the snapshot says both.

## Thresholds

| Source | Stale after | Why |
|---|---|---|
| market_prices | 1 day | A trading weekday without a session is already a gap |
| registry | 30 days | A snapshot, not a feed |
| statements | 180 days | Annual/interim clock |
| macro | 45 days | Monthly releases |
| news | 30 days | Seed-only feed |
| jobs / evaluation / reports / alerts | 7 days | They move only when an operator runs them |

## Seed snapshot (run `phase27-observability-2026-11-05`, 2026-11-05)

| Source | Latest observation | Coverage | Freshness | Status | Notes |
|---|---|---|---|---|---|
| market_prices | 2026-11-03 | 444 / 470 | 2 days | stale | Later weekdays have no session (Terms-gated) |
| registry | 2026-11-04 | 470 / 470 | 1 day | fresh | DPS snapshot + LEAP sampled verification (61) |
| statements | 2026-06-30 | 3 / 470 | 128 days | fresh | 3-company sample; HBL pending |
| macro | 2026-10-31 | 12 rows | 5 days | fresh | 6 VERIFIED by cross-publisher agreement, 6 UNVERIFIED |
| news | 2026-11-02 | 3 / 470 | 3 days | fresh | Seed events only; 2 scheduled future events excluded from freshness |
| jobs | 2026-11-04 | 71 runs | 1 day | fresh | 3 collection jobs paused (Terms gate) |
| evaluation | 2026-11-04 | 1 run | 1 day | fresh | All cards NOT_PROMOTED, all gates NOT_MET |
| reports | 2026-11-04 | 22 | 1 day | fresh | All DRAFT; no publish step exists |
| alerts | 2026-11-04 | 89 | 1 day | fresh | In-app delivery only; external consent False |

## Correction made during the run (not hidden)

News freshness first used the maximum event date, which is a
SCHEDULED future event (SBP meeting 2026-12-14) and reported a
negative freshness (-39 days) with status "fresh". That is
technically true and practically misleading: a future meeting
is not an observation. Fixed before commit: freshness uses the
latest event date on or before the run date (2026-11-02), and
the 2 scheduled future events are noted, not dated.
