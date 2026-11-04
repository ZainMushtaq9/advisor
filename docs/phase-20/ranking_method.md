# Phase 20 — Opportunity Ranking Method (screener-score-v1)

## Score

score = passed / scored, where scored counts only filters
with a pass or fail outcome. Missing and not_applicable
outcomes are excluded from numerator and denominator — they
are reported in reason codes and evidence, never scored as
zero and never scored as a pass.

## Outcome rule

- MATCH: scored ≥ 1 and passed == scored.
- NO_MATCH: scored ≥ 1 and passed < scored.
- INSUFFICIENT_DATA: scored == 0. Never a match, never a
  recommendation, never hidden.

## What the score is not

- Not a probability, not a confidence, not an expected
  return. No validated returns exist (Phase 13 abstained on
  all 120 assessments) and no covariance matrix exists
  (Phase 16 mean-variance NOT_CALCULABLE), so no
  probabilistic or optimized ranking is offered.
- Not a recommendation. Phase 15 user-facing values are
  WITHHELD; the screener surfaces the Phase 15 research
  conclusion and WITHHELD status as evidence only, never as
  a score input and never upgraded to a BUY/HOLD/SELL label.
- Not a forecast. No forward-looking value is produced.
- Not a guarantee. Every API response, every CLI report, and
  every stored result evidence carries the disclaimer:
  "Screen match, not an investment opportunity, not a
  recommendation, not a forecast."

## Evidence per result

Per-filter outcome, reason, stored value (or NULL with its
reason), percentile and peer-set size where applicable,
source table and row reference, period/as-of dates,
statement age and STALE_INPUT flag where applicable,
decision context (research conclusion, WITHHELD user-facing
value, confidence), and the disclaimer.

## Sorting and pagination

Default sort: score descending (NULL scores last), then
ticker ascending. Alternative sort: ticker ascending. Only
these two keys exist; anything else is a 400 error.
Pagination: limit 1..100, offset ≥ 0; violations are 400
errors, never silent clamps. Outcome filtering accepts
exactly MATCH, NO_MATCH, INSUFFICIENT_DATA.

## Reproducibility

A saved screen is (name, version, filter list, universe).
Re-running the same version at the same as-of date reuses
the stored run and writes nothing. A changed filter list
requires a new version; a changed as-of date is a new run.
Results are never overwritten, so a screen's history is
auditable run by run.
