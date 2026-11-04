# Phase 6 — Architecture

## Data flow (one direction, no loops back to collection)

```
market_prices (committed Phase 5 rows, daily, UNVERIFIED)
    -> runner.load_series()          [excludes CONFLICTED/REJECTED]
    -> coverage.assess_market()      [as-of slice, warm-up checks]
    -> formulas.compute_indicator()  [pure Decimal, no I/O]
    -> technical_indicator_values    [CALCULABLE only, new grains]
       + technical_calculation_runs  [one row per run]
       + technical_calculation_errors [aggregate NOT_CALCULABLE rows]
    -> API (GET only)                [coverage / values / signals]
    -> frontend /indicators          [tables, truthful empty states]
```

Signal events will live on a separate path that starts from
STORED indicator values, never from raw prices directly, and
only for activated rules (none today). The diagram below is
the FUTURE path — no code calls evaluate_rules or persists
events today; signals.py is library-only (audit M10):

```
technical_indicator_values -> signals.evaluate_rules()  [FUTURE]
    -> technical_signal_events       [observations only]
```

There is no write path from the API (GET only, mirroring Phase
5), no scheduler daemon (the CLI is operator-run, like Phase
5's), and no network call anywhere in the new code
(grep-verified: no requests/httpx/urllib in the package).

## Module map

| Piece | File | Responsibility |
|---|---|---|
| Registry | services/technical_indicators/conventions.py | 62 outputs, warm-ups, formula text |
| Formulas | services/technical_indicators/formulas.py | Pure Decimal math, InsufficientData |
| Aggregation | services/technical_indicators/aggregation.py | Daily -> weekly/monthly, partial status |
| Coverage | services/technical_indicators/coverage.py | Verdicts, reasons, unblockers, as-of slice |
| Runner | services/technical_indicators/runner.py | DB assessment, seeding, idempotent writes |
| Signals | services/technical_indicators/signals.py | Separate event engine, empty rule set |
| CLI | scripts/run_technical_indicators.py | --dry-run / --commit, JSON report |
| API | api/v1/endpoints/indicators.py | coverage, values, signals (GET only) |
| Frontend | app/indicators/page.tsx | Coverage + ticker verdict tables |
| Migration | database/migrations/versions/20261104_0005_... | Immutability triggers on output tables |

## Key design decisions (and their alternatives, rejected)

1. Reuse Phase 3 tables instead of new ones. Alternative (new
   tables) was rejected: it would duplicate the grain, the
   provenance block, and the run/error model for no benefit.
2. Aggregate error rows instead of per-security rows. 470 x 62
   per-security error rows would be ~29,000 rows restating two
   facts (1 bar, or 0 bars). Aggregates + the live API preserve
   all information with 124 rows.
3. No "current value" magic. The values endpoint returns rows
   for all configurations with their versions shown; callers
   pick a version explicitly. A hidden "latest wins" rule would
   be a silent convention mix.
4. Weekly/monthly periods are always "partial" until a trading
   calendar is validated. The alternative (calling a 5-bar week
   complete) would assert knowledge of holidays we do not have.
5. No scheduler daemon. Phase 5 deliberately introduced none,
   and a daemon that recomputes on empty data adds nothing; the
   operator-run CLI is the Phase 6 entry point, documented as
   such.
