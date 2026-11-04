# Phase 6 — Quality governance

## Rules inherited from Phase 5 (unchanged)

- Rejected rows are never stored, so they cannot enter an
  indicator. If one ever appeared, it would be excluded the
  same way CONFLICTED rows are.
- CONFLICTED input bars make ALL indicators for that security
  NOT_CALCULABLE with reason conflicted_input (never computed
  from a disputed price, never silently dropped to compute
  anyway). Mechanism (audit H2): the runner excludes such rows
  from the series but flags their tickers, and coverage
  reports conflicted_input for flagged tickers — including
  tickers whose only rows were conflicted, which would
  otherwise have looked like missing data. The test suite
  proves both the coverage path and the runner's load_series
  flagging (fake session, no DB).
- Missing bars are absent, never zero-filled. A blank
  previous_close is missing data, never zero or the close.
- Single source -> UNVERIFIED; two agreeing sources ->
  PARTIALLY_VERIFIED; official + agreeing -> VERIFIED. Today
  every input is single-source, so every value would be
  UNVERIFIED (and none exists yet).

## Quality inheritance

A computed value inherits the LOWEST quality of its input bars
(VERIFIED > PARTIALLY_VERIFIED > UNVERIFIED > CONFLICTED).
Calculation never upgrades quality: a clever formula does not
turn an unverified price into a verified indicator. The value
row also carries its source_key (single key if all bars share
one, else "multiple") and its last_input_observation_date, so
any consumer can trace exactly which observations produced it.

## Immutability and versioning

- Output tables (values, signal events, features, regime
  observations) are append-only: the 20261104_0005 migration
  applies psx_prevent_mutation() as a BEFORE UPDATE OR DELETE
  trigger, proven to fire on both operations with zero residue
  in a rolled-back transaction.
- Corrections arrive as NEW configuration versions, never
  edits. Old rows stay, so any consumer can reproduce an
  earlier value exactly.
- Run rows and error rows are NOT trigger-locked: a run row
  legitimately changes status (running -> completed), and
  error rows are append-only logs corrected by a new run, not
  by editing an old row.

## Freshness

Phase 5 freshness (STALE after 30 days past trading_date) is a
Phase 5 label on price rows. Indicator values inherit their
inputs' dates, and the coverage API reports the as-of date, so
a stale input can never masquerade as current: the value's
last_input_observation_date says when its inputs stopped.
