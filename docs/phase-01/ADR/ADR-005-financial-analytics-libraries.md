# ADR-005 — Financial analytics: pandas + NumPy, scikit-learn, statsmodels, PyTorch (conditional)

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04

## Context

Indicators, backtest frames, and models over PSX OHLCV/fundamental data need
a dataframe layer, a general ML layer, and an econometrics layer — in Python,
at PKR 0, with every number reproducible from stored data (see ADR-010).

## Decision

- **Dataframes/numerics:** pandas + NumPy — every indicator, join, and
  backtest frame goes through them.
- **General ML:** scikit-learn — regression, classification, clustering,
  pipelines, cross-validation.
- **Econometrics/time series:** statsmodels — ARIMA-family models,
  stationarity tests, regression diagnostics (the layer scikit-learn does not
  specialise in).
- **Deep learning:** PyTorch — **CONDITIONAL ONLY, where justified.** It is not
  a default Phase 1 dependency. It is added only when a Phase 2 specification
  names a concrete task for which classical models have been tried and shown
  insufficient on a defined metric, with that justification written into the
  task spec before installation.

## Consequences

- Positive: one library per sub-role, no duplicated indicator code; all
  operate on NumPy arrays / pandas frames; PKR 0 as distributed.
- Negative: three (later possibly four) libraries to keep pinned and
  compatible; PyTorch, if ever added, is a large dependency with CPU/GPU
  weight — which is exactly why it is gated.
- Constraint: these libraries compute; they do not narrate. No LLM output is
  ever parsed back into a number (ADR-010). Forecasts are probabilistic, never
  guaranteed, and shown with their inputs and provenance.

## Alternatives considered

- Polars — rejected as primary: would split dataframe code across two APIs;
  revisit only on a measured pandas bottleneck (none claimed).
- TensorFlow — rejected: a second deep-learning framework alongside
  conditional PyTorch; never both.
- Hand-rolled indicator math in plain loops — rejected: slower, buggier,
  untestable against library behaviour.

## Verification / open checks

- [ ] At Phase 2 setup: pin pandas/NumPy/scikit-learn/statsmodels; read and
  record their LICENSE files (UNVERIFIED in Phase 1). PyTorch's LICENSE is
  likewise UNVERIFIED until its gated adoption, if ever.
