# Phase 14 — Stress Testing (simulation only)

All results are deterministic arithmetic on stored 2026-11-03
closes for the simulated equal-weight HUBC/NML/OGDC reference
portfolio (HUBC 197.24, NML 123.61, OGDC 303.63). No result here
is a forecast, and none is investment advice. Re-running the
runner writes 0 new rows.

## Computed scenarios

| Scenario | Scope | Portfolio impact | Method |
|---|---|---|---|
| market_minus_10 (whole market −10%) | SIMULATED_PORTFOLIO | −10.000000% | Uniform −10% on all three closes; weight-weighted mean |
| idiosyncratic_minus_20 (single name −20%) | HUBC | −6.666667% | Only HUBC shocked; weight × −20% |
| idiosyncratic_minus_20 | NML | −6.666667% | Only NML shocked; weight × −20% |
| idiosyncratic_minus_20 | OGDC | −6.666667% | Only OGDC shocked; weight × −20% |

## Defined but not computed

| Scenario | Scope | Reason |
|---|---|---|
| rate_plus_100bps | HUBC, NML, OGDC | No rate sensitivity coefficient stored (floating/fixed debt split unknown) |
| fx_pkr_minus_10 | NML, OGDC | No FX sensitivity coefficient stored (FX-denominated amounts unknown) |
| commodity_oil_minus_10 | OGDC | No revenue elasticity to oil prices stored |

A coefficient must come from stored data before its scenario may
run. Assuming one would be fabrication, so these scenarios stay
insufficient_inputs with their exact reasons.
