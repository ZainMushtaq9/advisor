# RAG Evaluation Report (Deliverable 9)

Retrieval: deterministic full-text fallback, labelled
`FULL_TEXT_FALLBACK` everywhere. Vector retrieval is registered
but NOT implemented (no verified local embedding model); no vector
score is claimed. Method mirrors Phase 19's contract: metadata
filters before scoring, 2.0 per distinct query token, 5.0 exact
phrase bonus, 3.0 ticker bonus (only with token/phrase overlap —
see the defect note below), zero-score documents never returned,
snippets capped at 500 chars.

## Queries over the 20 stored scratch articles

| Query | Top-1 result | Correct? |
|---|---|---|
| "HUBC dividend" | HUBC announces quarterly dividend (4.0) | Yes |
| "OGDC gas reserves" | OGDC discovers new gas reserves (6.0) | Yes |
| "HBL loss" | HBL reports loss after tax (4.0) | Yes |
| "policy rate" | State Bank raises policy rate (9.0) | Yes (tied with SBP decision, also 9.0) |
| "HUBC dividend" + ticker=HUBC | HUBC dividend (7.0, with ticker bonus) | Yes |
| "dividend" + ticker=LUCK | (empty) | Yes — no LUCK documents exist |

Top-1 accuracy on this tiny set: 4/4 content queries. This is a
smoke result on N=20, not a retrieval quality claim.

## Citation correctness

Every returned result carries title, source, and canonical_url
taken from stored rows — 6/6 queries, 100% by field. Caveat: the
4 macro seed documents have EMPTY canonical_url (no link stored),
so a citation to one of them renders as "no stored link". Field
presence is 100%; link usefulness is 16/20 documents.

## Defect found and fixed during this evaluation

A ticker-filtered search returned a document with zero query-token
overlap purely on the ticker bonus (e.g. "dividend" + ticker=OGDC
returned a gas discovery). Fix: the ticker bonus now applies only
when the document already has token or phrase overlap. Regression
tests cover both directions (bonus with overlap still applies;
bonus alone never returns a document).

## Assistant shapes (measured on the same 20 docs)

- "Should I buy HUBC?" -> uncertainty, 0 citations (correct: no
  signal is ever issued).
- "Show me HUBC dividends" -> direct_evidence, 1 citation (the
  HUBC dividend article only — scoped, not all dividends).
- "Compare HUBC news with price movement" -> comparison, 2 stored
  items, reaction reported INSUFFICIENT_DATA with the reason (not
  fabricated).
- "Show me LUCK dividends" -> missing_data, 0 citations (the
  named-ticker scoping fix: another company's dividends are never
  presented as LUCK's).
