# Phase 15 Decision Policy Specification — rules v1

Decision date: 2026-11-04. Price reference date: 2026-11-03.
Rule version: `decision-rules-v1`. Status: PARTIALLY COMPLETE.

## Three levels, never collapsed

1. **Screening outcome** — a mechanical data-availability and
   freshness check. SCREEN_PASS (data present, latest statement
   within 365 days, publication date known), SCREEN_FAIL (data
   present but stale or publication unknown), SCREEN_NOT_RUNNABLE
   (no statements at all).
2. **Research conclusion** — BUY_CANDIDATE / HOLD_CANDIDATE /
   SELL_CANDIDATE / WATCHLIST / INSUFFICIENT_EVIDENCE, from the
   versioned rule set below. A "candidate" is a research opinion,
   never an order and never personalized advice.
3. **User-facing recommendation** — issued only when a research
   conclusion exists AND confidence is at least MEDIUM; otherwise
   WITHHELD with its reason. In this run every user-facing value
   is WITHHELD: all inputs are UNVERIFIED, calibration is
   NOT_ESTABLISHED (Phase 13 abstained on every target), and
   technical evidence is absent for every company, so no
   confidence above LOW is reachable. That is the rule working,
   not a failure to decide.

## Dimensions and scoring (weights equal, 1 each, in v1)

| Dimension | +1 | 0 | −1 | ABSENT |
|---|---|---|---|---|
| Fundamentals (Phase 8 health) | profitability ≥ 70 and solvency ≥ 70, no negative-PAT warning | otherwise | negative-PAT warning, or profitability 0 | health rows missing |
| Valuation (Phase 9 trailing P/E) | P/E < 10 | P/E in [10, 25] | P/E > 25 | P/E not computed |
| Technical (Phase 6) | — | — | — | always in this run (0 calculable values) |
| News/event (Phase 11) | — (never directional in v1: no expectations data) | earnings event, known date | — | event date unknown / no event |
| Macro (Phase 10 regime) | — | regime not tightening | regime tightening | no regime row |
| Liquidity (Phase 14 tier) | tier HIGH | tier MEDIUM | tier LOW | no tier row |
| Risk (Phase 14 flags) | — | info-only flags or none | any warning-severity flag | — (0 when no flags) |

Book values are evidence, not a scored input, in v1. Forecasts
are not a dimension at all: Phase 13 abstained on all 120
assessments, so forecast evidence contributes nothing, and that
absence is recorded in every decision's evidence snapshot.

## Conclusion mapping

Total = sum of scored dimensions (ABSENT excluded).

- BUY_CANDIDATE: total ≥ +3 AND fundamentals +1 AND valuation +1.
- SELL_CANDIDATE: total ≤ −3 AND fundamentals −1.
- HOLD_CANDIDATE: ≥ 5 scored dimensions and total in [−2, +2].
- WATCHLIST: 3–4 scored dimensions.
- INSUFFICIENT_EVIDENCE: any blocking gate, or fewer than 3
  scored dimensions.

## Blocking gates (any one forces INSUFFICIENT_EVIDENCE)

- `no_statements` — no statement rows for the company.
- `stale_latest_statement` — latest period end more than 365
  days before the decision date (Phase 14 threshold).
- `publication_date_unknown` — latest statement publication date
  NULL, so the no-look-ahead check cannot be verified.
- `valuation_publication_unknown` — a computed valuation's input
  statement publication date NULL.
- `too_few_dimensions` — fewer than 3 scored dimensions.

## Confidence (categorical, from measured factors only)

- HIGH: inputs VERIFIED, calibration established, completeness
  7/7, agreement ≥ 0.80, no unresolved conflicts.
- MEDIUM: inputs at least PARTIALLY_VERIFIED, calibration
  established, completeness ≥ 6/7, agreement ≥ 0.66.
- LOW: any conclusion not meeting MEDIUM. In this run every
  conclusion is LOW.
- NONE: no conclusion (gated).

No probabilities are invented. Agreement for a directional
conclusion is the share of scored dimensions that do not
contradict its direction; for a neutral conclusion (HOLD /
WATCHLIST) it is the share of zero-scored dimensions. For
INSUFFICIENT_EVIDENCE agreement is NULL (no conclusion to agree
with).

## Evidence precedence (selection, not overriding)

1. Audited statements over interim statements.
2. Newer publication over older publication.
3. Official sources (SBP/PBS) over issuer documents over press.
4. Domain applicability: banking rules are never applied to
   industrials, nor industrial ratios blindly to a bank.

Precedence selects which evidence is used; it never overrides a
score. Remaining disagreements are preserved as unresolved
conflicts in the decision record (see evidence_aggregation.md).

## Risk warnings (displayed with every decision)

Outputs are research information, not personalized guaranteed
advice. No output here is a buy/sell signal, a forecast, or a
guaranteed result. No brokerage order path exists in this
project, and none may be added: proposals are opinions on
stored evidence, and execution is denied by design.
