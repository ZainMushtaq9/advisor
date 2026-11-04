# ADR-010 — Deterministic calculations vs LLM: numbers from code only, LLM for research text only

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04

## Context

A financial product that shows a wrong number is worse than one that shows no
number. LLMs are probabilistic text generators; financial calculations must be
reproducible. This ADR draws the boundary that every other ADR depends on, and
it applies whether or not any model is ever adopted (ADR-007).

## Decision

- **Deterministic functions only for numbers.** Every financial number shown to
  a user — price, indicator, return, ratio, forecast value, backtest result —
  comes from a deterministic Python function (pandas/NumPy/scikit-learn/
  statsmodels, or plain Python) over stored data, with its inputs, function
  version, and source timestamps recorded. The same inputs always produce the
  same output.
- **LLM for research text only.** A local Ollama model (if adopted via the
  ADR-007 gate) may draft research prose, summarise stored documents, and
  explain a computed result — in words, around numbers that code already
  computed. It may not originate, estimate, round into existence, or "fill in"
  a number.
- **Tool boundary.** The only way an LLM touches a number is by calling a named
  deterministic calculation tool with explicit arguments, and quoting the
  tool's returned value verbatim. LLM output is never parsed back into a
  number, and a number is never accepted from free-form LLM text.
- **Forecasts are probabilistic, never guaranteed.** No UI copy, report
  template, or LLM prompt may present a forecast as certain. Every forecast
  carries its model, inputs, and uncertainty framing.

## Audit trail (mandatory, not aspirational)

Every LLM interaction logs: the model (name/version, once adopted), the prompt
or task, every tool call with its arguments, every tool result, and the final
text produced. Every computed number logs: function name + version, inputs
(including source + source_timestamp), and output. If either log is missing,
the corresponding output is not shown — it is treated as unverified.

```python
# Illustrative shape only (not application code):
# result = calculate_rsi(closes, period=14)   # deterministic, versioned
# llm_text = draft_research_text(context={"rsi": result.value})  # text only
# assert "rsi" not in llm_freeform_numbers  # numbers come from result, never from text
```

## Consequences

- Positive: numbers are reproducible, testable, and traceable to source data;
  LLM failures degrade to "no draft text", never to "wrong number".
- Negative: LLM features are deliberately less "magical" — an LLM cannot
  answer "what will this stock do?" with a number, because no such number
  exists outside a named model run over named inputs.
- Constraint: the LLM-as-PDF-extractor pattern is prohibited (ADR-006); the
  LLM-as-calculator pattern is prohibited here; the LLM-as-data-source pattern
  (inventing a price, a filing, or a company fact) is prohibited everywhere.

## Alternatives considered

- "LLM does everything, code checks it later" — rejected: post-hoc checking
  of free-form numbers is unreliable and unauditable.
- "LLM with retrieval, numbers quoted from documents" — rejected as a number
  source: quoting a document's number still requires extraction (ADR-006) and
  verification, not LLM recall.
- "No LLM at all, ever" — not chosen: research drafting is a legitimate,
  bounded LLM use, and the stack already works fully without it (ADR-007).

## Verification / open checks

- [ ] Phase 2: a test that feeds the LLM layer a prompt asking it to invent a
  number and asserts no number from its text reaches any display path except
  via a calculation tool result. Strategy defined here; no test is claimed
  passed in Phase 1.
