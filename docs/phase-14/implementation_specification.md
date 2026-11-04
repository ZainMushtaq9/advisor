# Phase 14 — Implementation Specification

## Brief source

Playbook `~/workspace/psx-playbook/psx_playbook.txt`, lines 1143–1203
(Phase 14: Risk Management and Exposure Analytics Engine).

## Objective (brief)

Quantify security, company, sector, market, portfolio, liquidity and
model risks and create transparent risk controls for downstream
decisions. No live execution exists anywhere in this project.

## Entry state (verified before implementation)

- Prices: 444 rows, one trading date 2026-11-03, all UNVERIFIED,
  previous_close NULL on all rows, turnover NULL on all rows.
- Statements: 3 companies (HUBC id 289, NML id 394, OGDC id 403),
  88 statements, 1,316 line items, all UNVERIFIED.
- Phase 6: 0 calculable indicator values (62-indicator registry).
- Phase 8: 108 value rows, 8 warnings, 24 health rows.
- Phase 10: 12 macro observations, 6 exposures, 1 regime (tightening).
- Phase 11: 7 seed news events, 1,376 aliases, coverage 3/470.
- Phase 12: 34 HUBC ownership rows, 5 dividend actions (dates NULL),
  50 breadth rows, 889 liquidity rows, 0 investor flows.
- Phase 13: 120 assessments, all insufficient_inputs, 0 forecasts.
- HBL (company 277) pending: no Phase 14 rows for HBL.

## Architecture (follows Phases 8–13)

- `backend/app/models/risk.py` — 7 tables (see migration 0011).
- `backend/app/services/risk_analytics/__init__.py` — metric library
  (22 definitions), control rules v1 (5), stress scenarios (5),
  reference portfolio definition.
- `backend/app/services/risk_analytics/formulas.py` — pure Decimal
  math; every function returns None below its minimum input.
- `backend/app/services/risk_analytics/runner.py` — reads stored rows
  only, writes idempotently (unique grains; second --commit writes 0).
- `scripts/run_risk_analytics.py` — --dry-run default / --commit,
  --company filter.
- `backend/app/api/v1/endpoints/risk.py` — GET-only: metrics,
  profile, market, controls, stress, status.
- `database/migrations/versions/20261104_0011_phase_14_risk.py`
  (head 0011).

## What is computable, and what is not

Computed (46 value rows): volume liquidity tiers (3), sector
participation (37), market priced coverage (1), top-10 volume share
(1), HUBC largest/top-3 holder shares (2), forecast abstention
rate (100%), technical coverage rate (0%).

NOT_CALCULABLE (35 value rows, never zero-filled): all 8 series
metrics × 3 securities (volatility, beta, drawdown, downside
deviation, VaR95, ES95, correlation, gap risk — one close, no
benchmark series, previous_close NULL), turnover liquidity × 3
(turnover NULL), sector volume HHI (per-sector volume shares not
stored), 6 sensitivity coefficients (exposure direction evidenced,
coefficient inputs absent), input drift (single vintage).

Flags (17): 8 Phase 8 warnings mapped, auditor-opinion absent
(NML, OGDC — info, not adverse), publication-date unknown (NML —
warning), statement stale (NML, 583 days > 365 — warning), and 5
market flags (forecast abstention, technical coverage zero,
previous_close absent, turnover absent, 26 missing tickers).
No flag infers fraud, default or solvency.

Controls v1 (5 rules, 7 checks): single-name cap 25% → BREACH
(reference portfolio holds 33.333333% per name, by construction);
sector cap 50% → PASS; drawdown warning −10% → BLOCKED (no series);
min daily volume 50,000 → PASS for all 3 names; min
diversification 3 names → PASS.

Stress (5 scenarios, 10 results): market −10% → −10.000000%
(computed); idiosyncratic −20% per name → −6.666667% portfolio
impact each (computed); rate +100bps × 3, FX −10% × 2, oil −10% × 1
→ insufficient_inputs (no coefficient stored). All results are
simulation arithmetic on 2026-11-03 closes, never forecasts.

## Acceptance gate

- [x] Risk formulas pass tests (14 pure tests).
- [x] Assumptions and historical windows are visible (every row
      carries reason + evidence JSON with window/as-of dates).
- [x] Missing data blocks or downgrades dependent decisions
      (insufficient_inputs rows, BLOCKED control check, abstained
      forecasts carried forward as a warning flag).
- [x] Stress tests are reproducible (deterministic arithmetic on
      stored closes; re-run writes 0 new rows) and no live
      execution exists (no order/trade path in code or API).

## Verdict: PARTIALLY COMPLETE

The engine, register, controls and stress framework are complete
and verified end-to-end. Coverage is 3 companies, series risk
metrics are all unavailable, sensitivity coefficients are absent,
and HBL is pending — so the gate's coverage items cannot pass yet.
Nothing mandatory is claimed as done that is not evidenced.
