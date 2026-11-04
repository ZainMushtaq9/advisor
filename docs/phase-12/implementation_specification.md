# Phase 12 implementation specification

Brief: playbook lines 1024–1083 (Ownership, Corporate Actions, Market
Breadth and Flow Intelligence). Dependencies: Phases 4, 5, 7, 10, 11
where source data exists.

## Architecture

```
stored Phase 5 prices ──► breadth.py (pure) ──► market_breadth
stored Phase 5 prices ──► breadth.py (pure) ──► liquidity_observations
HUBC annual report ──► seed data (two extractors) ──► ownership_holdings
Phase 7 statement faces ──► seed data ──► corporate_action_records
rule definitions ──► adjustment_rules (defined, never applied)
(no flow source) ──► investor_flows (empty by design)
```

Services live in `backend/app/services/ownership_actions/`:
`__init__.py` (seed data), `adjustments.py` (pure formulas),
`breadth.py` (pure breadth/liquidity math), `runner.py` (idempotent
DB load). CLI: `scripts/run_ownership_actions.py`. API: GET-only
`backend/app/api/v1/endpoints/ownership.py` (6 routes).

## Key design decisions

1. **Phase 3 table NOT reused.** `corporate_actions` requires a NOT
   NULL event_date and carries an adjustment_factor for application.
   Phase 12's evidenced actions have no published event date, so
   writing them there would force inventing one. The Phase 12
   registry is `corporate_action_records`; the Phase 3 table stays
   empty until an action gains a known ex-date, at which point the
   application layer writes the adjustment row there.
2. **Folio is part of the ownership grain.** The same holder name
   under two folios (MEGA CONGLOMERATE, MUHAMMAD KAMRAN KAMAL) is
   two rows, never merged.
3. **No adjusted series is stored.** Adjustment rules are definitions
   with a `requires` field. With no ex-date on any stored action,
   every rule is `defined_not_applied`, and raw price rows are never
   modified (is_adjusted stays False on all 444 rows).
4. **Breadth status vocabulary.** `computed` | `insufficient_inputs`
   | `not_applicable` | `partial`. Non-computed rows carry NULL values
   and a reason; the trading-day frequency row is `partial` because
   one observed day is a snapshot count, not a frequency.
5. **Flows are absent, not estimated.** The `investor_flows` table
   exists and holds zero rows. The brief's gate item ("no unsupported
   investor-flow claims") is satisfied by producing no flow claim.
6. **All new rows are UNVERIFIED.** Ownership comes from a single
   issuer document; breadth/liquidity from UNVERIFIED prices. Nothing
   is promoted.

## Period / date discipline

- Ownership reporting date 2026-06-30 ("As on June 30, 2026");
  publication date 2026-09-21 is the auditor-report date used as
  publication proxy (same convention as Phase 11 HUBC earnings).
- Action dates that are not published stay NULL with the reason in
  `date_evidence`; the statement period is the only date evidence.
- Breadth date is the single price date 2026-11-03; no look-ahead is
  possible or performed (no future observation exists in the inputs).
