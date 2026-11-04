# Phase 15 Run Report — 2026-11-04

Verdict: **PARTIALLY COMPLETE**. Branch: `phase-15-decision-engine`
(from `04ad858`). Migration head: `20261104_0012`.

## Decisions (decision date 2026-11-04, price date 2026-11-03)

| Company | Screening | Research conclusion | User-facing | Confidence | Total | Scored dims | Gates | Conflicts |
|---|---|---|---|---|---|---|---|---|
| HUBC | SCREEN_PASS | HOLD_CANDIDATE | WITHHELD | LOW | +2 | 6/7 | — | 3 |
| NML | SCREEN_FAIL | INSUFFICIENT_EVIDENCE | WITHHELD | NONE | −3 | 4/7 | stale_latest_statement, publication_date_unknown, valuation_publication_unknown | 0 |
| OGDC | SCREEN_PASS | HOLD_CANDIDATE | WITHHELD | LOW | 0 | 6/7 | — | 3 |
| HBL | SCREEN_NOT_RUNNABLE | INSUFFICIENT_EVIDENCE | WITHHELD | NONE | −1 | 2/7 | no_statements, too_few_dimensions | 0 |

Dimension scores (fundamentals / valuation / technical /
news_event / macro / liquidity / risk):

- HUBC: +1 / +1 / ABSENT / 0 / −1 / +1 / 0 = +2.
- OGDC: +1 / 0 / ABSENT / 0 / −1 / 0 / 0 = 0.
- NML: −1 / ABSENT / ABSENT / ABSENT / −1 / 0 / −1 = −3
  (scores recorded for audit; the conclusion is forced by gates).
- HBL: ABSENT / ABSENT / ABSENT / ABSENT / −1 / ABSENT / 0 = −1
  (macro regime and risk-no-warning-flags are the only scored
  dimensions; the conclusion is forced by gates).

## DB counts before / after

- Before: 0 Phase 15 rows; migration head `20261104_0011`.
- After: +1 decision rule (decision-rules-v1), +4 decisions,
  +0 outcomes (intentionally — no later observation exists yet).
  All 4 decisions UNVERIFIED. Prior rows untouched (statements
  88, prices 444, valuations 51, indicators 12, news events 7,
  ownership 34, forecast assessments 120, risk values 81).
- Idempotency proven: second --commit wrote 0 new rows
  (1 rule + 4 decisions skipped).

## Hand-check (independent audit)

- HUBC total: profitability 100 + solvency 100, no negative-PAT
  warning → +1; P/E 5.1553 < 10 → +1; earnings event known
  2026-09-21 → 0; tightening → −1; tier HIGH → +1; info-only
  flags → 0. Total +2, 6 scored → HOLD_CANDIDATE. ✓
- OGDC total: profitability 73.33 + solvency 100 → +1; P/E
  17.8816 in [10, 25] → 0; earnings event known 2026-02-23 → 0;
  tightening → −1; tier MEDIUM → 0; info-only flags → 0.
  Total 0, 6 scored → HOLD_CANDIDATE. ✓
- NML gates: latest period end 2025-03-31 is 583 days before
  2026-11-04 (> 365) → stale; publication NULL → unknown;
  computed book values reference statements with NULL
  publication → valuation gate. ✓
- HBL: 0 statements → no_statements; 2 scored dimensions (< 3)
  → too_few_dimensions. ✓
- No-look-ahead: latest publications 2026-09-21 (HUBC) and
  2026-02-23 (OGDC) are before 2026-11-04; regime observation
  2026-11-04 equals the decision date. No violation. ✓

## Tests and live checks

- Backend suite 236 passed, 0 failed (224 prior + 12 new pure
  tests: scoring, mapping, gates, confidence caps, user-facing
  withholding, rules/gates documentation, no-execution-path scan).
- Ruff check + format clean on all new/changed files.
- Live API: /decisions/rules 200 (1 rule), /decisions 200
  (4 decisions), per-ticker 200 (HUBC/NML/OGDC/HBL with correct
  conclusions), unknown ticker 404, /decisions/status 200
  (2 HOLD_CANDIDATE, 2 INSUFFICIENT_EVIDENCE, 4 WITHHELD,
  0 outcomes).

## HBL pending note

Habib Bank Limited (company 277, COMMERCIAL BANKS) has an
explicit INSUFFICIENT_EVIDENCE decision (not a silent omission):
its CY2025 statements are not loaded (PDF blocked at download;
live-browser download runs separately). A Phase 7 load plus a
Phase 15 re-run adds HBL's evidence without redesign; the
banking rule (no industrial ratios blindly applied) carries
forward.

## Remaining blockers (exact unblockers)

1. User-facing issuance — inputs at least PARTIALLY_VERIFIED
   (H1 second agreeing source incl. official) + calibration
   established (Phase 13 evaluations on longer series).
2. Technical dimension — calculable technical values (Phase 6
   needs more trading days: 5 closes for SMA(5)).
3. HBL conclusion — live-browser HBL CY2025 PDF download, then
   a Phase 7 load, then a Phase 15 re-run.
4. NML conclusion — a fresh NML statement with a known
   publication date (Phase 7 expansion).
5. Wider-company coverage — Phase 7 expansion beyond the
   3-company sample.
6. Outcomes — a later price or statement observation dated
   after 2026-11-04, recorded (never backfilled) in
   decision_outcomes.
7. VERIFIED promotion — H1 second agreeing source including an
   official source; everything stays UNVERIFIED until then.
