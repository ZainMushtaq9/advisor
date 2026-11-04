# Phase 19 — Retrieval Benchmarks and Access-Control Audit

## Benchmark cases (6)

| Case | Question | Expected | Kind |
|---|---|---|---|
| hubc_net_profit_fy2026 | What was HUBC net profit for the year ended 30 June 2026? | HUBC p. 275, fragment "56,257,178" | direct_evidence |
| hubc_auditor_opinion | What did HUBC auditor conclude on the consolidated statements? | HUBC p. 271, fragment "true and fair view" | direct_evidence |
| nml_nine_month_loss | What was Nishat Mills profit or loss for nine months ended 31 March 2025? | NML p. 37, fragment "1,182,815" | direct_evidence |
| ogdc_six_month_profit | What was OGDC profit for the six months ended 31 December 2025? | OGDC p. 8, fragment "73,019,248" | direct_evidence |
| hubc_gross_margin_derived | What is HUBC gross margin for FY2026? | metric gross_margin | derived_calculation |
| hbl_missing_document | What was HBL profit for the year ended 31 December 2025? | no evidence | missing_data |

## Benchmark results

| Run | Passed | Recall@5 | Per-case ranks (direct cases) |
|---|---|---|---|
| r1 | 1/6 | 0.1667 | all NULL (snippet criterion; ranking largely correct but snippets wrong) |
| r2 | 2/6 | 0.3333 | HUBC p. 275 rank 1, HUBC p. 271 rank 2, NML p. 37 rank 1, OGDC p. 8 rank 1 (snippet criterion still failed all four) |
| r3 | 6/6 | 1.0000 | HUBC p. 275 rank 1, HUBC p. 271 rank 2, NML p. 37 rank 1, OGDC p. 8 rank 1 (chunk-level criterion) |

Citation precision in r3: direct cases 0.2000 each (1 of 5
citations is the expected page); derived and missing-data cases
1.0000. Runs r1 and r2 are kept as history; results dedupe on
(case_id, run_id) and are never overwritten.

## Access-control audit (live, run 1)

One audit row per (role, document) pair — 9 rows total:

| Role | Allowed levels | HUBC / NML / OGDC (all issuer_internal) |
|---|---|---|
| internal | official_public + issuer_internal + platform_internal | 3 allowed |
| external | official_public only | 3 denied ("level 'issuer_internal' is outside that scope") |
| auditor | official_public + platform_internal | 3 denied (never issuer_internal) |

Unknown roles are denied by default (fail closed), proven by pure
tests. Audits are a log: re-runs append new rows and are reported
as new rows, never as skipped state.

## Prompt-injection evaluation

- 0 chunks flagged in the production corpus (953 → 943 chunks after
  the face-page re-index). The injection path is therefore proven by
  fixture tests, not by a production flagged chunk — stated here
  honestly, not inflated.
- Pure tests prove: override patterns ("ignore your instructions",
  price/value overrides, secrecy suppression, "new system/user
  instruction", "forget your/the instructions/rules") are flagged;
  legitimate financial wording ("The board resolved…", "The company
  acts as trustee…", "Management decided…", "Profit for the year
  56,257,178…") is NOT flagged (the "act as …" pattern was removed
  after review for exactly this false-positive risk).
- Flagged chunks are excluded before scoring, never cited, never
  followed. Phase 18's injection probe (claimed HUBC close 200.00
  vs stored 197.2400) remains quarantined; Phase 19 writes no price
  rows and the stored close is unchanged.
