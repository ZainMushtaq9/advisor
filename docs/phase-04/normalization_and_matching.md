# Phase 4 — Normalization and Matching

## Normalization (match keys only)

Original values are ALWAYS stored untouched. Normalization produces
a match key, never a display value and never evidence of identity.

- Ticker: NFKC, upper-case, whitespace removed. A suffix such as
  `.KAR` is KEPT — collapsing it could merge two listings.
  Empty or >50 characters: rejected.
- Company name: NFKC, upper-case, punctuation collapsed to spaces,
  the word AND removed (so "Oil & Gas" and "Oil and Gas" match),
  common legal suffixes stripped REPEATEDLY (LIMITED, LTD, PVT LTD,
  PRIVATE LIMITED, PLC, INC, CORPORATION, COMPANY, CO) — so
  "Engro Corporation Limited" and "Engro" share a key. Empty after
  normalization: rejected.
- Sector name: NFKC, upper-case, punctuation collapsed. Used only
  to find an existing row from the SAME source — never to merge
  taxonomies across sources.
- ISIN: upper-case, no whitespace, format-checked
  (2 letters + 9 alphanumerics + 1 digit). The check digit is NOT
  recomputed here; a format failure is a rejection, not a
  correction.

Two defects found by tests during this phase are recorded in the
defect register (D-50): suffix stripping originally stopped after
one suffix ("Engro Corporation Limited" kept "CORPORATION"), and
"&" vs "and" did not collapse. Both are fixed and regression-tested.

## Matching (deterministic, narrow by design)

A record matches an existing entity ONLY when a hard identifier
agrees, in this priority:

1. ISIN agrees (strongest), or
2. a stored identifier (type + value) agrees, or
3. normalized ticker AND normalized company name both agree.

Ticker alone is NOT enough (tickers are reused after delisting
and renamed). Name alone is NOT enough (names collide). Same
ticker with a different name is a rename/reuse/conflict — never a
silent match; it is recorded as ambiguous.

## Outcomes

- `unique` — exactly one candidate passes a rule: import proceeds
  against that entity (idempotent re-import, or a ticker change
  recorded in symbol_history when matched by ISIN/identifier).
- `none` — no candidate passes: a new company + security are
  created, status UNVERIFIED.
- `ambiguous` — two or more candidates pass, or rules disagree:
  the record is kept original, marked PENDING_REVIEW via a
  DataQualityReport row, and NEVER auto-merged. Resolution
  requires a human or a later verified source.

No LLM is used anywhere in matching. No fuzzy score, no threshold,
no probabilistic merge exists in this phase.
