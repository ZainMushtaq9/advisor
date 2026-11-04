# PSX Intelligence AI — Task × Acceptance-Criterion Matrix

> Canonical phase list: `MASTER_ROADMAP.md` (docs version). Status values:
> **PENDING-AUDIT** (not yet independently audited — the only status this
> Phase 1 document set may assign to itself), **PASS**, **FAIL**,
> **UNVERIFIED** (cannot be verified yet, with the reason stated).
> **No Phase 1 row is marked PASS by its author.** PASS/FAIL verdicts are
> entered only by the coordinator / independent audit (Phase 01 workflow
> stage 9, and Phase 24 for later phases). Testing strategy is defined
> here, not claimed passed.
>
> How to use this matrix: each phase row lists its acceptance criteria
> (from `PHASE_BREAKDOWN.md`, condensed). The audit records one status per
> criterion, with evidence, in the "Audit status" column. A phase is
> complete only when every criterion is PASS, or when a criterion is
> explicitly carried as an open item with a documented limitation
> (the completion conditions for gated phases 08, 09, 10, 14 allow this).

## Part A — All 30 phases at phase level

| # | Phase | Acceptance criteria (condensed) | Audit status |
|---|---|---|---|
| 01 | Requirements and architecture | 30 phases fully specified with the full field set; no invented price/benchmark/API/endpoint/capability; UNVERIFIED listed as blockers; audit + correction + checkpoint complete | PENDING-AUDIT |
| 02 | Repository and development environment | Fresh-checkout setup works from the guide alone; no paid tool required; smoke check runnable | PENDING-AUDIT (phase not started — STOP AFTER PHASE 1) |
| 03 | Database architecture | Migrations clean on empty local DB; duplicates cannot silently accumulate; backup/restore round-trip passes; no PostgreSQL deployment claimed | PENDING-AUDIT (phase not started) |
| 04 | PSX company registry | Every record has source + as-of; trading vs listed counts reported separately and reconciled (or gaps listed); no symbol without a status | PENDING-AUDIT (phase not started) |
| 05 | Backend foundation | Every fetch/derivation has a provenance record; stale flagged; conflicts keep both values; no secret in code/config | PENDING-AUDIT (phase not started) |
| 06 | Historical market data collector | Re-run adds zero duplicates; interrupted run resumes without loss; report accounts for every symbol; no silent complete with unresolved quarantine | PENDING-AUDIT (phase not started) |
| 07 | Market snapshot collector | Every snapshot has timestamp + source; stale flagged downstream; failures name symbols; no real-time guarantee | PENDING-AUDIT (phase not started) |
| 08 | Financial statement collector | No field without source label; no UNVERIFIED data; framework works on fixtures with zero verified sources; OR verified source populated | PENDING-AUDIT (phase not started; ingestion UNVERIFIED-gated) |
| 09 | Corporate announcement collector | No announcement without source + date; no UNVERIFIED data; duplicates not double-counted; OR verified source populated | PENDING-AUDIT (phase not started; ingestion UNVERIFIED-gated) |
| 10 | Macroeconomic data collector | No series without source + vintage; no UNVERIFIED data; no-macro fallback documented; OR verified series populated | PENDING-AUDIT (phase not started; ingestion UNVERIFIED-gated) |
| 11 | Fundamental analysis | Every metric matches a hand-computed fixture; source + as-of on every output; missing never zero-filled | PENDING-AUDIT (phase not started) |
| 12 | Technical analysis | Every indicator matches a hand-computed fixture; insufficient history → "insufficient data"; no indicator labelled buy/sell; deterministic | PENDING-AUDIT (phase not started) |
| 13 | Sector intelligence | Aggregates recompute from constituents; breadth denominators stated; no synthesised index; quarantined excluded | PENDING-AUDIT (phase not started) |
| 14 | News intelligence | No item without source + date; no UNVERIFIED content; classification method stated; OR verified source populated | PENDING-AUDIT (phase not started; ingestion UNVERIFIED-gated) |
| 15 | Financial health scoring | Scores match hand-computed fixtures; formula + inputs + limitations with every score; versioned; no guarantee wording | PENDING-AUDIT (phase not started) |
| 16 | Valuation engine | Valuations match fixtures or are withheld with reason; methods + assumptions + ranges with every output; no invented input | PENDING-AUDIT (phase not started) |
| 17 | Statistical forecasting | Out-of-sample evaluation for every baseline; horizon + method + error band on every forecast; no look-ahead; no guarantee | PENDING-AUDIT (phase not started) |
| 18 | AI forecasting | No uncited numeric claim; uncertainty + limitations on every output; token usage logged; no paid AI service | PENDING-AUDIT (phase not started) |
| 19 | Price target engine | Every target has method + inputs + horizon + range + limitations; no guarantee / no instruction to trade; no trade-execution path exists | PENDING-AUDIT (phase not started) |
| 20 | Backtesting | Report states universe, period, rules, limitations; no look-ahead; survivorship handled; no result as future guarantee | PENDING-AUDIT (phase not started) |
| 21 | Risk management | Measures match fixtures; method + window + limitations on every view; no trading-control path exists | PENDING-AUDIT (phase not started) |
| 22 | Investment recommendation engine | Every recommendation has inputs + reasoning + uncertainty + limitations + backtest context; no guarantee / no instruction to trade; no trade path exists | PENDING-AUDIT (phase not started) |
| 23 | Portfolio optimization | Holdings labelled user-entered; suggestions carry method + constraints + uncertainty + limitations; no instruction to trade; no broker path | PENDING-AUDIT (phase not started) |
| 24 | Independent audit | Every matrix item has an independent verdict with evidence; fails corrected or registered as open items; no self-marked pass | PENDING-AUDIT (phase not started) |
| 25 | Multi-agent orchestration | Every agent run logged; no agent trades/posts/sends without recorded human approval; validator flags uncited/guarantee-worded outputs | PENDING-AUDIT (phase not started) |
| 26 | Autonomous company research | Every dossier claim cited; every gap labelled with reason; no dossier finished without review clearance; no trading/posting/sending | PENDING-AUDIT (phase not started) |
| 27 | Scheduling and monitoring | Every scheduled job logged with outcome; stale/failed visible before downstream use; alerts only to approved channels, with history | PENDING-AUDIT (phase not started) |
| 28 | Frontend and dashboard integration | No figure without source + as-of; no forecast/target/recommendation view without uncertainty + limitations + no-trade text; stale banner-flagged; preferences persist locally | PENDING-AUDIT (phase not started) |
| 29 | Security and production hardening | Security review complete (findings resolved or open items registered); no secret in code/config/logs; licence register complete; backup/restore + rollback tested | PENDING-AUDIT (phase not started) |
| 30 | Full PSX rollout and final verification | Final verification covers completeness, calculations, UI disclosures, freshness; handover + open-items register published; no UNVERIFIED item presented as resolved; no paid service; no trade path | PENDING-AUDIT (phase not started) |

## Part B — Phase 01's 12 tasks in detail (coordinator audit fills the status)

Phase 01 work is organised here as 12 tasks (the Team 8 Phase 1 task set
for this roadmap/cost package). Each row is one task × its acceptance
criteria. **All statuses are PENDING-AUDIT until the coordinator audit
fills them. This document claims no pass.**

| # | Phase 01 task | Acceptance criteria | Audit status | Audit evidence (to be filled by audit) |
|---|---|---|---|---|
| 1.1 | Scope, non-goals, and rules fixed | Scope + non-goals + PKR 0 rule + no-trade rule + hard rules stated; no contradiction across docs | PENDING-AUDIT | |
| 1.2 | Verified starting condition recorded | Tools (Python 3.12.3, Node v24.22.1; Docker/psql/redis-cli absent), scaffold reference, and verified source facts recorded without extension | PENDING-AUDIT | |
| 1.3 | UNVERIFIED register created | SECP/SBP/PBS/Finance/WB/IMF/FRED + statement/announcement/news sources listed as UNVERIFIED with the check needed; none presented as available | PENDING-AUDIT | |
| 1.4 | 11-stage Phase 01 workflow applied | All 11 stages (brainstorm → checkpoint) recorded; stage 4 limited to read-only inspection; no full-scale live collection in Phase 1 | PENDING-AUDIT | |
| 1.5 | Architecture planned (intent, not code) | Module boundaries, data contracts, provenance/PKT/stale/conflict rules defined as intent; no application code delivered as Phase 1 | PENDING-AUDIT | |
| 1.6 | Exact 30-phase list fixed | Same 30 names in the same order in MASTER_ROADMAP (docs + root), PHASE_BREAKDOWN, PHASE_DEPENDENCY_MAP, and this matrix | PENDING-AUDIT | |
| 1.7 | Per-phase implementation specifications written | Every phase has objectives, tasks/subtasks, dependencies, inputs, outputs, required files, DB/API/agent requirements, free resources, test cases, acceptance criteria, known risks, completion conditions | PENDING-AUDIT | |
| 1.8 | Dependency map + critical path produced | Dependency table + Mermaid diagram + critical path consistent with the breakdown; gated phases identified; critical path does not wait on a gated source | PENDING-AUDIT | |
| 1.9 | Cost model produced (PKR 0, three scenarios) | Three scenarios (zero-budget local dev; zero-subscription local operation; conditional zero-cost online deployment) with the permanent-free-hosting caveat; hardware/electricity/internet disclosed as external expenses, never called free; no paid alternative introduced | PENDING-AUDIT | |
| 1.10 | Resource model produced | Per-phase/per-scenario compute, storage, volumes with ESTIMATE arithmetic shown and every figure labelled VERIFIED/ESTIMATE/UNVERIFIED | PENDING-AUDIT | |
| 1.11 | Free-coverage / gap analysis produced | Free coverage and free gaps (notably historical intraday, licensed redistribution, guaranteed real-time) documented; decision rule is document-the-limitation, never purchase | PENDING-AUDIT | |
| 1.12 | Handover to coordinator audit (no self-pass) | Package handed over with all Phase 1 rows PENDING-AUDIT; no later phase started; STOP AFTER PHASE 1 stated | PENDING-AUDIT | |

## Cross-cutting acceptance rules (apply to every row above)

- **No self-marking.** An implementing team never changes its own row to
  PASS. Only the coordinator / independent audit does, with evidence.
- **UNVERIFIED is a verdict, not a failure to hide.** A criterion that
  cannot be verified yet is marked UNVERIFIED with the check needed and
  carried as an open item — it is not marked PASS on assumption and not
  deleted.
- **Gated-phase completion.** For Phases 08, 09, 10, 14, a framework-complete
  + documented-limitation outcome satisfies the completion condition even
  with zero verified data, provided the limitation is published and
  downstream fallbacks are implemented.
- **No-trade verification.** For Phases 19, 22, 23, 25, 26, a PASS requires
  evidence of the no-trade-guard test (no order/broker/external-action
  code path), not just a statement that trading is out of scope.
- **PKR 0 verification.** For every phase, a PASS requires that no paid
  service is in use and none is proposed as the solution to a gap; gaps
  are documented limitations.
