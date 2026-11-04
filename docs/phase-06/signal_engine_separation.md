# Phase 6 — Signal-engine separation

## The separation, stated once and enforced in code

The signal engine is a SEPARATE module
(`services/technical_indicators/signals.py`). It is not an
investment decision engine, and no investment decision engine
exists in this project. The engine:

- starts only from STORED technical_indicator_values rows, never
  from raw prices;
- evaluates only rules that are ACTIVATED by an explicit
  versioned configuration change;
- uses only values dated on or before the event date
  (no-look-ahead, same rule as the indicator layer);
- produces no event when a rule's inputs are missing, and
  raises NotImplementedError loudly for an activated rule that
  has no evaluator — it never fabricates an event to fill a gap.

ACTIVATED_RULES is empty by default, and it is empty today.
No signal event exists in production (0 rows).

## What an event means (and what it never means)

An event is a stored observation that a deterministic,
versioned rule condition held on a stored indicator value at a
date. It is NOT a buy/sell/hold recommendation, NOT a
guaranteed opportunity, and NOT a prediction. The API response
carries this note on every signals response, and the frontend
page repeats it. No guaranteed returns anywhere; no real
trades; no broker or order path exists in this codebase, and
none is added here.

## The documented-but-not-activated example

EXAMPLE_RULES contains one shape only — a golden cross
(SMA(50) crossing above SMA(200)) — written to show the rule
schema (inputs, condition, version) without activating it.
Evaluating it raises NotImplementedError, which the test suite
asserts, because the inputs are not calculable and no
evaluator exists. Activating any rule requires: (1) its inputs
calculable on real data, (2) a versioned evaluator, (3) a
recorded configuration change. All three are future work, and
none is silently assumed.

## Why separation matters for audit

If a future phase ever adds a decision layer, it must consume
signal events as observations and add its own probabilistic
framing, horizons and uncertainty — it must not reach into the
indicator layer and re-interpret raw values as decisions. This
document is the contract that future phase will be audited
against.
