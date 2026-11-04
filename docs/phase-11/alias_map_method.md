# Phase 11 Alias Map Method

## Generation rules (deterministic, no LLM, no fuzzy)

1. Normalize: NFKC → upper → punctuation to space → collapse spaces.
2. Strip TRAILING legal suffixes repeatedly: LIMITED, LTD, PVT LTD,
   PRIVATE LIMITED, PLC, INC, CORPORATION, COMPANY, CO.
3. Variants per company: TICKER (1.0), LEGAL normalized name (0.95),
   LEGAL_STRIPPED (0.85), PAREN_STRIPPED — parenthetical qualifier
   dropped, e.g. "(Pakistan)", "(Pref)", "(RIGHT)" (0.80),
   PAREN_STRIPPED_SUFFIX (0.75).
4. NO abbreviation expansion: IND is not INDUSTRIES, and "D G" is not
   DG. NO token merging. An alias matches exactly or not at all.

## Resolver rules

- Ticker tokens match only on word boundaries: HBL inside HBLXYZ does
  not match; standalone HBL does.
- Full-alias phrases match only on word boundaries.
- Single generic tokens never resolve: no alias equals PAKISTAN, BANK
  or MILLS, so those words alone match nothing.
- For one company, only the highest-confidence matching alias is kept.
- Every match carries alias, type, confidence, ambiguity flag and an
  evidence string.

## Ambiguity (measured, not assumed)

1,376 alias rows were generated for 470 companies. 10 aliases collide
across two companies each (20 ambiguous rows). All are genuine:

| Alias | Companies | Why it collides |
|---|---|---|
| ARIF HABIB | Arif Habib Corporation (AHCL) / Arif Habib Ltd (AHL) | Distinct issuers, same stripped name |
| GHANI CHEMWORLD (+ LIMITED) | Ghani Chemworld (GCWL) / Ghani Chemworld (PRS) (GCWLPRS) | Ordinary vs preference |
| JAVEDAN | Javedan Corporation (JVDC) / Javedan Corporation (Pref) (JVDCPS) | Ordinary vs preference |
| MUGHAL IRON STEEL INDUSTRIES | Mughal Iron & Steel (MUGHAL) / …(C) (MUGHALC) | Ordinary vs class C |
| POWER CEMENT | Power Cement (POWER) / Power Cement (Pref) (POWERPS) | Ordinary vs preference |
| PREMIER INSURANCE (+ LIMITED) | Premier Insurance (PINL) / …(RIGHT) (PINLR) | Ordinary vs rights |
| SUPERNET TECHNOLOGIES (+ LIMITED) | Supernet Technologies (STL) / …(Right) (STLR) | Ordinary vs rights |

Consequence: a bare-name match for any of these aliases is capped at
0.50 confidence and forced to review. Only the ticker disambiguates
the security. This is the correct behaviour, and it is why the
Phase 4 LEAP procedure records preference qualifiers rather than
dropping them silently.

## False-positive tests (all in `test_news_events_phase11.py`)

- "HBLXYZ announced a deal" → no match.
- "PAKISTAN" alone → no match.
- "STEEL INDUSTRIES LIMITED" (LEAP-style expansion, no ticker) → no match.
- "AGHA STEEL INDUSTRIES LIMITED" → ticker-token match only, no
  name-alias match (documents the no-expansion rule precisely).
- "Agha Steel Ind.Ltd reports" → AGHA match via registry name.
- Shared alias (ABC Limited / ABC Ltd fixture) → both capped 0.50,
  both flagged ambiguous.
