# Phase 15 Evidence Aggregation and Conflict Resolver

## What is aggregated

For each company the runner reads only already-stored rows:

- Phase 7 statements: latest period end, publication date, age.
- Phase 8 health scores (profitability, solvency, liquidity,
  efficiency, cash_flow, growth, earnings_quality) and warning
  events.
- Phase 9 valuations: computed trailing P/E and book values,
  with input statement references.
- Phase 10 macro regime (latest observation).
- Phase 11 news events: earnings event, known vs unknown date.
- Phase 12 breadth (market context, via Phase 14 tiers).
- Phase 13 assessments: abstention status only (120 total, 0
  computed) — forecasts contribute no evidence.
- Phase 14 risk flags (severity) and volume liquidity tier.
- Phase 6 coverage: technical coverage 0 (technical ABSENT).

Every decision's `evidence_snapshot` JSON records the input row
references, values, as-of and publication dates, rule version,
dimension scores, and the reason each dimension scored as it did,
so any historical decision can be reconstructed exactly.

## Conflict rules (generic, derived from stored rows)

| Conflict type | Fires when |
|---|---|
| profitability_vs_earnings_quality | profitability ≥ 70 while earnings_quality < 40 |
| cheap_vs_cash_quality | valuation +1 while a cash-conversion or receivables warning exists |
| profitability_vs_receivables | profitability ≥ 70 while a receivables-days-over-one-year warning exists |
| profitability_without_growth | profitability ≥ 70 while growth is 0 |
| fundamentals_vs_macro_headwind | fundamentals +1 while the macro regime is tightening |

Conflicts are preserved as unresolved disagreements. Precedence
(audited over interim, newer over older, official over issuer
over press, domain applicability) selects which evidence is
used; it never overrides a score and never averages a conflict
away.

## Production conflicts (2026-11-04 run)

- HUBC (3): profitability_vs_earnings_quality (100 vs 20 — the
  high net margin rests on post-tax associate profit, per the
  Phase 8 sector profile note); cheap_vs_cash_quality (P/E 5.16x
  against low cash conversion and receivables growing faster than
  revenue); fundamentals_vs_macro_headwind (fundamentals +1
  against the tightening regime).
- OGDC (3): profitability_vs_receivables (profitability 73.33
  against receivables days 571.3, over one year);
  profitability_without_growth (profitability 73.33, growth 0);
  fundamentals_vs_macro_headwind.
- NML, HBL: no conflicts recorded — both are abstentions, and
  there is no conclusion for a conflict to attach to. NML's
  tensions (efficiency 80 against profitability 0, negative PAT
  against positive solvency) remain visible in its stored health
  rows and warnings, not in a decision it did not receive.

## Missing inputs are never filled

- Technical: ABSENT for every company (0 calculable values).
- Forecasts: abstained, recorded as absence, never a number.
- NML publication dates: NULL, recorded as a gate, never
  guessed (its earnings event date is likewise unknown).
- HBL: no statements, no health, no valuations — an explicit
  abstention row, not a silent omission.
- OGDC owners book value: not computed in Phase 9 (no
  owners/NCI split) — absent from OGDC's evidence, never
  estimated from the total.
