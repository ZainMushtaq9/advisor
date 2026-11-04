# Phase 3 — Fundamentals and Technicals Schema

## Fundamentals

fundamental_metric_definitions (metric_key unique, category,
formula_text, formula_version, required_inputs, unit) +
fundamental_metric_values (company x metric x period_end x
calculation_version; value NULL = NOT_CALCULABLE, never a guessed
zero; input_statement_ids = the exact statement version ids used).

This is the Phase 1 'ratios' entity, realised as definition +
value. A ratio without a formula version and input references is
not a Phase 3 ratio.

Supporting tables: fundamental_analysis_runs,
fundamental_trend_observations, earnings_quality_observations
(warning language POTENTIAL_WARNING / REQUIRES_REVIEW /
UNUSUAL_PATTERN / INSUFFICIENT_EVIDENCE, each with evidence —
never an automatic fraud classification),
financial_health_assessments (category scores + method version +
evidence; score NULL = INSUFFICIENT_DATA; a score here is NOT an
established credit rating), sector_metric_profiles
(applicability + source requirements per sector; unavailable =
UNAVAILABLE, never estimated), fundamental_warning_events.

## Technicals

technical_indicator_definitions (formula, default parameters,
warmup periods, formula version) + _configurations (parameters +
config version, active flag) + _values (security x configuration
x observation_date x timeframe; last_input_observation_date
recorded so warmup and staleness are checkable).

Supporting tables: quantitative_market_features (deterministic
regime/feature summaries with versioned threshold configs; a
feature may use only information available at or before its
observation date — no look-ahead), market_regime_observations
(heuristic classification, never a proven prediction),
technical_signal_events (event candidates with condition, value,
parameters, evidence, quality, calculation version — stored
separately from any future decision engine, never equated with a
guaranteed buy/sell opportunity), technical_calculation_runs /
_errors (insufficient_warmup, missing_data, invalid_ohlc, ...).

## Shared rule

Every computed value carries its calculation/formula version and
its input references. Recomputation must be reproducible from
those references; a value whose inputs cannot be named is not a
Phase 3 value.
