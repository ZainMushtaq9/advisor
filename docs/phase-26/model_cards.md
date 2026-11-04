# Phase 26 — Model Cards

Nine cards. Every card's training data is "stored rows only":
no external training corpus exists in this project, and
claiming one would be fabrication. Every card is NOT_PROMOTED.

| Model | Version | Evaluation status | Key limitation |
|---|---|---|---|
| forecasting_baselines | baselines-v1 | Not evaluable: 0 predictions, 0 matured labels; fixture-tested only | No interval validatable without residual history; naive point-only outputs recorded as abstained |
| forecasting_candidates | candidates-registered-only | Not implemented; nothing to evaluate | Must not be presented as available methods |
| decision_rules | decision-rules-v1 | Abstention measurable (WITHHELD 4/4); performance not evaluable (0 outcomes) | Confidence caps at LOW while inputs are UNVERIFIED; calibration NOT_ESTABLISHED |
| screener_score | screener-score-v1 | Match counts reproducible (1,418 results, 241 MATCH) | Matches are filter results, not opportunities or recommendations |
| risk_controls | controls-v1 | Checks reproducible (5 pass, 1 breach on SIMULATED portfolio, 1 blocked) | Series risk metrics NOT_CALCULABLE |
| rag_retrieval | retrieval-token-v1 | r3: 6/6 passed, recall@5 1.0, mean citation precision 0.4667 | Token heuristics outscore figure rows; vector retrieval NOT_IMPLEMENTED (no verified embedding model) |
| orchestration_fallback | fallback-v1 | 6/6 evaluations PASS | No verified local model; consequential actions denied to all |
| technical_indicators | registry-v1.0 | 0 calculable values (470 assessed, 124 errors) | Daily return missing_data(470): previous_close NULL |
| reports_qa_gate | qa-v1 | 22 drafts pass QA; 0 approved; 0 published | QA proves internal consistency, not truth: every input is UNVERIFIED |

## Promotion gates (all NOT_MET)

1. **out_of_sample_evidence** — 0 predictions, 0 matured
   labels, 0 outcomes.
2. **baselines_and_negatives_included** — negatives are
   recorded (abstention 100%, WITHHELD 4/4, NOT_RUNNABLE
   backtests), but no baseline-relative comparison is
   computable without evaluated predictions.
3. **evidence_governed_promotion** — runs, cards, and gates
   now exist, but no model has evaluated out-of-sample
   performance to govern a promotion.
4. **no_unsupported_accuracy_claims** — the framework enforces
   NULL for unevaluated claims, but no evaluated claim exists
   yet to check.
5. **human_approval_recorded** — no human approval gate has
   been granted for any promotion, report approval, live
   account, or release.
