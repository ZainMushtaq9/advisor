# Phase 16 — Methods

## Equal-weight baseline (constructed)

Equal weight over the eligible set, whole shares, residual cash.
This is the simple baseline every other method is compared
against. Baseline set: the 3 statement companies (HUBC, NML,
OGDC) under balanced constraints. HBL is out of baseline scope
(it has no statements) but its quote is ELIGIBLE — the exclusion
row says exactly that.

## Rule-based SCREEN_PASS (constructed)

Equal weight over Phase 15 SCREEN_PASS securities only (HUBC,
OGDC), under the chosen risk profile's constraints. SCREEN_FAIL
(NML: stale, publication unknown, valuation publication unknown)
and SCREEN_NOT_RUNNABLE (HBL: no_statements,
too_few_dimensions) names are excluded with reasons. The rule
uses research conclusions and screening outcomes, NOT issued
recommendations — every Phase 15 user-facing value in this run
is WITHHELD, and the portfolios' assumptions say so.

## Mean-variance (NOT_CALCULABLE — gated, never faked)

Requires (a) validated expected returns and (b) a covariance
matrix. Both fail:

1. Expected returns: Phase 13 computed 0 forecasts (all 120
   assessments insufficient_inputs; live forecasting abstained
   because no series meets any method's interval minimum).
2. Covariance: 1 price date gives 0 return observations (at
   least 2 closes are needed for a single return).

The comparison row `mean_variance vs ew_statements_3_balanced`
carries status NOT_CALCULABLE with both reasons and empty
metrics. No optimizer output, no efficient frontier, and no
"optimal" weight is shown anywhere — showing one would require
inventing the two missing inputs.

## Baseline comparison

| Subject | Holdings | Cash weight | Largest single weight | Largest sector weight (capital) |
|---|---|---|---|---|
| ew_statements_3_balanced (baseline) | 3 | 0.0527% | 33.3253% (NML) | 33.3253% |
| rule_screen_pass_balanced | 2 | 0.0419% | 49.9806% (HUBC) | 49.9806% |
| rule_screen_pass_conservative | 2 | 10.0116% | 44.9980% (OGDC) | 44.9980% |
| mean_variance | — | — | — | NOT_CALCULABLE |

Reading the comparison honestly: the rule-based portfolios are
MORE concentrated than the baseline (2 names vs 3, largest
weight ~50% vs ~33%) — screening for quality narrowed the set
and raised concentration. That trade-off is the finding, not a
defect to hide. The conservative profile's cash floor is the
only mechanism that reduced invested exposure (to 89.99%).
