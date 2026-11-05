# Actual Market-Reaction Evaluation Report (Deliverable 8)

Method: `run_news_intelligence.py reactions --commit` on scratch
computed one reaction row per stored Phase 11 event (8 events)
against the stored market prices (444 rows, single trading date
2026-11-03, all UNVERIFIED). No price was invented, estimated, or
zero-filled. Correlation is not causality: every row carries that
note.

## Result: 8/8 INSUFFICIENT_DATA (honest, expected)

| Event | Ticker | Event date | Why INSUFFICIENT_DATA |
|---|---|---|---|
| 1 HUBC earnings | HUBC | 2026-09-21 | No price observation before the event date (prices start 2026-11-03); no session after post for any window |
| 2 NML earnings | NML | NULL (unknown) | Date unknown in the Phase 11 record — never guessed |
| 3 OGDC earnings | OGDC | 2026-02-23 | Same as event 1: no pre observation, no post windows |
| 4 HBL earnings | HBL | 2026-03-03 | Price date 2026-11-03 is after the event, so no pre observation and no window after post |
| 5 SBP policy decision | (macro, no company) | 2026-10-26 | No company link: no company series to react |
| 6 PBS inflation report | (macro, no company) | 2026-11-02 | Same as event 5 |
| 7 SBP MPC minutes due | (macro, no company) | 2026-11-20 | Same as event 5 |
| 8 SBP MPC meeting scheduled | (macro, no company) | 2026-12-14 | Same as event 5 (future scheduled date) |

## What this proves and what it does not

- Proves: the event-study math runs, names its exact missing
  pieces per window (pre observation, 1/5/10/20-day windows), and
  refuses to fabricate. The unit tests prove the math itself on
  full series (all four windows compute; 1-day return 0.1 on the
  fixture) and on partial series (computed windows kept,
  missing windows named, status INSUFFICIENT_DATA).
- Does NOT prove: any news→price relationship. With one price
  date, no event study in this project can currently show one,
  and none is claimed.
- Unblocker (pre-existing, not created by this engine): more
  trading days — 2 closes unlock returns, 5 unlock SMA(5), 11
  unlock naive forecast intervals, 30 unlock volatility/beta/
  Sharpe/AR(1), 251 unlock VaR/ES. Until then, every reaction row
  in this project is INSUFFICIENT_DATA by construction.

## Forecast integration

Leakage guards (`usable_for_forecast`, `snapshot_allows`) are
implemented and unit-tested: published_at must be timezone-aware
and <= prediction_timestamp, or the item is excluded. No forecast
improvement claim is made or measured: forecasts abstain
(156 assessments, all abstained post-batch), and news is not
credited with improving them. Any future claim needs
out-of-sample evaluation with these guards on — not a backtest
that peeks at future news.
