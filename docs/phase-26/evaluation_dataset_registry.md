# Phase 26 — Evaluation Dataset Registry

Eight versioned datasets. A dataset is a pointer to stored rows,
never a copy: re-running an evaluation against the same dataset
version must reproduce the same inputs. Row counts below are
the seed-run values; the runner recomputes them from stored
rows and reports differences as drift findings.

| Dataset key | Version | Rows | Split policy |
|---|---|---|---|
| forecast_targets_v1 | targets-v1 | 48 | Expanding-window walk-forward, chronological, never shuffled; matured labels only after the full horizon elapses + an actual observation at/after the horizon date |
| forecast_assessments_2026_11_04 | assessments-2026-11-04 | 120 | Origin 2026-11-03; no horizon elapsed in data, so no matured label |
| decisions_2026_11_04 | decisions-v1-2026-11-04 | 4 | Decision date is the split; only observations after 2026-11-04 count as outcomes; nothing backfilled |
| rag_benchmark_r3 | phase19-benchmark-2026-11-04-r3 | 6 | Fixed golden set; page-level traceability is the acceptance criterion; snippet precision reported separately |
| agent_evaluations_demo | phase18-demo-graph | 6 | Fixed case names every run |
| backtest_metrics_2026_11_04 | backtests-2026-11-04 | 55 | Single-date window: 0 computed, 50 insufficient, 5 not applicable; never presented as a result |
| report_qa_2026_11_04 | reports-2026-11-04 | 541 | Every figure kinded + statused; non-computed figures carry no value; approval is CLI-only |
| golden_cases_v1 | golden-v1 | 14 | Fixed case keys + expected outcomes; a failed case blocks promotion of every model it touches |

## Known divergence (recorded, not hidden)

RAG benchmark results number 6 in the live database (r3 only).
The r1 (1/6) and r2 (2/6) rows were runs of superseded
retrieval code and were NOT reproduced after VM replacement #6;
they were not fabricated. Any future benchmark re-run creates
a new run id (r4, …) — it never rewrites r3 history.
