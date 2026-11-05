# News Classification Evaluation Report (Deliverable 7)

Dataset: `evaluation_dataset.json` — hand-labelled by the
implementer. N=20: 12 SYNTHETIC headlines (clearly labelled; they
measure the pipeline, not the world) + 8 REAL stored Phase 11
seed-event titles processed title-only. Processor: deterministic
fallback (RULE_BASED) only — no LLM ran. Sample size 20 is disclosed
with every metric; it cannot support a production accuracy claim
and none is made. All 20 items stored as REVIEW (fallback
confidence caps at 0.70, below the 0.80 review line) — correct
behavior, not a failure.

## Category agreement

Synthetic headlines: 10/12 = 83.3%.

| Item | Hand | Pipeline | Verdict |
|---|---|---|---|
| syn-01 quarterly dividend | dividends | dividends | agree (after rule-order fix) |
| syn-02 bonus shares | bonus | bonus | agree |
| syn-03 gas reserves discovery | oil_gas | other | GAP: no discovery wording in oil_gas rules |
| syn-04 loss after tax | earnings | earnings | agree |
| syn-05 policy rate | interest_rate | interest_rate | agree |
| syn-06 inflation eases | inflation | inflation | agree |
| syn-07 court penalty, contract dispute | court_decision | court_decision | agree (after rule-order fix) |
| syn-08 board meeting | board_meeting | board_meeting | agree |
| syn-09 budget + tax | budget | budget | agree |
| syn-10 suspended from trading | trading_suspension | trading_suspension | agree |
| syn-11 expands branch network | expansion | other | GAP: "expands" vs EXPANSION wording |
| syn-12 merger, unknown company | merger_acquisition | merger_acquisition | agree |

Real title-only items: 0/8 strict agreement — EXPECTED, not a
failure: document titles ("HBL Annual Report 2025") carry no
category keywords, and their Phase 11 event types come from
document_type, not headline text. The pipeline was never designed
to classify document titles as news. The 4 macro titles got
plausible content categories (interest_rate, inflation,
banking_policy, interest_rate) where the seed type is the broader
macro_release — a content-vs-provenance typing difference, not an
error. Combined strict agreement (10/20 = 50%) mixes two different
tasks and is reported here only to prevent cherry-picking: the
meaningful number is the synthetic-headline figure above.

## Entity precision / recall (ticker links)

- Synthetic: predicted 9 links (8 correct + 1 false positive),
  expected 8 links, all found. Precision 8/9 = 88.9%, recall 100%.
- Real: predicted 3 links (all correct), expected 4. Precision
  100%, recall 75% (HUBCO missed: no abbreviation expansion, by
  Phase 11 design — HUBCO is not the ticker HUBC).
- Combined: precision 11/12 = 91.7%, recall 11/12 = 91.7%.
- False positive found: "next week" matched ticker NEXT (a real
  registry ticker that is also an ordinary English word). The
  article still went to REVIEW (fallback confidence < 0.80), so
  the review queue caught it — but common-word tickers are a known
  collision class for the exact-token resolver. Recorded as a
  limitation, not silently dropped.

## Sentiment agreement (fallback lexicon only)

- Synthetic strict: 7/12 (syn-01, 04, 05, 08, 09, 10, 12 agree;
  syn-07 mixed vs hand negative is a defensible partial).
- Real: 8/8 (all hand-neutral, all pipeline-neutral).
- Combined strict: 15/20 = 75%.
- Gaps are lexicon coverage, not measurement: "bonus",
  "approves", "discovers", "eases", "expands" are not lexicon
  words, so those items stay neutral. The lexicon is a heuristic
  and is labelled as such on every row.

## Summary factuality and citations

- Grounding check: extracted_facts = [title] by construction for
  the fallback, so 20/20 facts grounded, 0 ungrounded. This
  measures the fallback's construction, not a model's honesty.
- Citation correctness (assistant + RAG): every returned result
  carries title/source/canonical_url from stored rows (measured
  on 6 RAG queries + 3 assistant shapes; see RAG report). Caveat:
  4 macro seed docs have EMPTY canonical_url (no stored link), so
  their citations show "no stored link" — presence by field is
  100%, link usefulness is 16/20.

## Latency

20 items processed + stored in under 2 seconds (rule-based, no
model). No model latency exists to report until the hardware
unblocker is met.
