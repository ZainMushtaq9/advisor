# Phase 9 — Run report (2026-11-04)

## Verdict: PARTIALLY COMPLETE

The valuation engine is complete and independently verified
end-to-end (statements + prices → assessment → commit → push). The
verdict is PARTIALLY COMPLETE, not COMPLETE, because the brief's
entry dependency (verified Phases 5, 7, 8 data) is unmet in the
strong sense — all inputs are UNVERIFIED — and because share-count
methods, DCF/DDM, and peer multiples are methodologically
unavailable, and HBL is pending. Nothing mandatory is claimed as
done that is not evidenced.

## What changed

- Branch: `phase-09-valuation`, new branch from `9969f5a` (Phase 8
  tip). Base tip unmoved; `main` untouched at `eb6025b`.
- Engine: `backend/app/services/valuation/` (`__init__.py` registry,
  `formulas.py`, `coverage.py`, `peers.py`, `runner.py`).
- CLI: `scripts/run_valuation.py` (--dry-run default / --commit,
  --company filter).
- API (GET-only): `backend/app/api/v1/endpoints/valuations.py`
  (valuations, methods) + router registration.
- Tests: `backend/tests/test_valuation_phase09.py` (15 tests).
- Docs: `docs/phase-09/` (methodology.md, model_library.md,
  run_report.md).
- No new migration: the Phase 3 `valuations` table already holds
  everything (estimated_value, value_low/high, assumptions JSON,
  input_statement_ids, input_price_ids, quality_status).
- No register edits, per the parent brief (parent consolidates).

## DB counts before / after (live DB verified)

- Before: 3 documents, 88 statements, 1,316 line items, 444 prices,
  0 valuation rows.
- After: +51 valuation rows (17 per company: 7 computed, 41
  insufficient_inputs, 3 not_applicable; 0 non-UNVERIFIED).
  Statements/line items/prices unchanged.
- Idempotency proven: second `--commit` wrote 0 new rows (51
  skipped as existing).

## What valued vs NOT_CALCULABLE

Computed (7): HUBC trailing P/E 5.1553x; OGDC trailing P/E
17.8816x; book-value totals for all 3 companies; book-value owners
for HUBC and NML. NOT_CALCULABLE (41): all share-count methods,
DCF (FCFF/FCFE), DDM, peer median P/E, sum-of-parts, OGDC owners
book value, NML P/E. Not applicable (3): bank residual-income for
the three industrials. Full per-method reasons are in
methodology.md and in every row's assumptions JSON.

## Tests and live checks

- New tests: 15 passed. Full backend suite: 162 passed, 0 failed
  (147 prior + 15 new).
- Ruff check + format clean on all new/changed backend files; the
  CLI matches the Phase 8 CLI precedent (same single BLE001
  blind-except finding, which the Phase 8 CLI also carries).
- Live API: ratios-style valuations endpoint 200 for HUBC/NML/OGDC
  with correct computed sets, HBL 200 pending, unknown ticker 404,
  methods endpoint 200 with the 17-method registry.

## HBL pending note

Habib Bank Limited (company 277, COMMERCIAL BANKS) has no
valuation rows: its CY2025 statements are not loaded (PDF blocked
at download; live-browser download runs separately). Design accepts
a 4th company via one PERIODS entry (reused from Phase 8) plus a
price row; the bank residual-income model must be used for it, never
an industrial enterprise-value DCF.

## Remaining blockers (exact unblockers)

1. **Wider-company / KSE-100 expansion** — Phase 7 expansion beyond
   the 3-company sample (per-company source verification pass).
2. **HBL statements** — separate live-browser HBL CY2025 PDF
   download, then a Phase 7 load, then a Phase 9 re-run with HBL
   added (bank residual-income model).
3. **Share-count data** — an authoritative shares-outstanding
   source (with par value / diluted counts) unlocks P/B, P/S,
   market cap, EV multiples, cash-flow yield, and dividend yield.
4. **Source-backed discount rates and forecasts** — Phase 10 macro
   inputs (risk-free rate, market premium, validated WACC
   methodology) unlock DCF; DPS series + payout pattern unlock DDM.
5. **VERIFIED promotion** — H1 second agreeing source including an
   official source; everything stays UNVERIFIED until then.
6. **Peer multiples** — same-sector statement companies with
   aligned periods (>= 3 peers for a median).
7. **TTM / full-year flows** — full-year income rows for NML/OGDC
   (or a validated TTM construction rule) for trailing multiples
   on a full-year basis. OGDC's P/E is a 6M interim-period trailing
   multiple and is labelled as such; HUBC's is full-year FY2026.
