# Test and Regression Report (Deliverable 13)

## Suite results (branch news-intelligence, post-batch merge)

| Suite | Result |
|---|---|
| Backend pytest (full) | 520 passed, 0 failed |
| Frontend vitest | 11 passed |
| Frontend webpack build | PASS, 30 static pages (27 at handover + 3 new) |
| Scratch migration 0025 | Applied 0024 -> 0025, verified head; downgrade + re-upgrade verified |
| Scratch CLI runs | process 20/20 stored, enforce 8/8 refused, reactions 8/8 stored |

Backend count walk: 468 (post-batch) -> 520. The +52 is the new
news-intelligence suite (55 tests in the file, minus overlaps
with updated Phase 25 count assertions) plus the jobs-spec
regression tests. No pre-existing test was weakened: the two
Phase 25 count assertions were changed from hardcoded 8 to
`len(JOB_DEFINITIONS)` because the registry legitimately grew to
11 definitions — their intent (register inserts everything,
operator pauses preserved) is unchanged and now also asserts the
news jobs are seeded.

## Coverage by prompt section 15 area

Source permission enforcement, collection scheduling (jobs_spec +
HANDLERS wiring), source failure handling (RSS malformed -> ValueError,
Ollama unreachable -> ModelUnavailable), duplicate detection
(content_hash skip), timezone handling (PKT naive handling,
freshness, weekday rule), ticker resolution + incorrect-ticker
rejection (schema + guards + resolver tests), event
classification, JSON schema validation, LLM output validation
(malformed JSON -> REJECTED, unknown ticker -> REJECTED),
hallucination safeguards (grounding check), news-to-price
matching, event-study calculations (full + partial series),
look-ahead leakage prevention (aware-only, cutoff rule), forecast
evaluation (guards; no improvement claim), RAG citations, alert
deduplication (Phase 21 reuse — no separate table, no separate
test surface claimed), data freshness.

## Defects found by testing / evaluation and fixed in this work

1. **Sentiment lexicon case bug** (found by N=20 eval): lexicon
   words were lowercase while `normalize()` uppercases, so every
   sentiment came out neutral. Fixed: uppercase lexicon sets.
   Regression test added.
2. **Taxonomy rule-order bugs** (found by N=20 eval): "quarterly
   dividend" classified as earnings (QUARTERLY matched first);
   "contract dispute" in court classified as contract_order.
   Fixed: dividends before earnings, court_decision before
   contract_order. Regression tests added.
3. **RAG ticker-bonus-only returns** (found by RAG eval): a
   ticker-filtered document with zero query-token overlap was
   returned on the bonus alone. Fixed: bonus requires overlap.
   Regression tests added.
4. **Assistant cross-company answers** (found by RAG eval): "Show
   me LUCK dividends" answered with HUBC's dividends. Fixed:
   named-ticker scoping for dividends/negative/macro shapes.
   Regression tests added.
5. **Wrong schema column names** (found by scratch CLI run):
   runner queried `companies.company_name` / `sectors.sector_name`;
   real columns are `legal_name` / `name`. Fixed in runner + API.
   Regression test added (SQLite registry fixture).
6. **Impact NULL relevances** (found by scratch CLI run): macro
   items have NULL company/sector relevance by design, but the
   columns were NOT NULL, failing the whole commit. Fixed:
   columns nullable in model + migration (NULL = not applicable).
7. **SQLite Identity PKs** (found by model tests): BigInteger
   Identity does not auto-generate on SQLite. Fixed: Integer PKs
   (Phase 29 precedent) in models + migration.
8. **NEXT false positive** (found by N=20 eval): "next week"
   matched ticker NEXT. NOT fixed in code: exact-token matching
   is the Phase 11 resolver's design, and the REVIEW queue caught
   it. Recorded as a limitation.

## Independent audit of this work (self-audit, scoped to new code)

- Endpoints: 6 GET-only routes; no POST/PUT/DELETE/PATCH, no
  upload endpoint, no write route.
- Network: only urllib call in the package targets
  `http://localhost:11434` (Ollama default); no external host, no
  paid API import (no openai/gemini/groq/anthropic strings).
- Dangerous constructs: no docker, no eval/exec, no subprocess,
  no os.system in new code.
- Secrets/PII: none stored; the only "token" hits are query-token
  / significant-token vocabulary, not credentials.
- Datasets: evaluation items are synthetic or stored seed titles;
  no CSV/PDF committed; no credentials committed.
- What this audit is NOT: it is a self-audit by the implementer,
  not an independent review. The parent's independent 30-phase
  audit (verdict C, branch final-30-phase-verification-audit)
  covers the 8937338 baseline, not this branch.
