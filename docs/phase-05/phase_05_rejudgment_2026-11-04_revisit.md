# Phase 5 — Re-judgment, revisit run (2026-11-04, late evening)

## Verdict: PARTIALLY COMPLETE

This revisit re-verifies Phase 5 (market data engine / snapshot import)
on a fresh branch, as part of the user-ordered "complete the 4 to 7"
sequence. No code changed. No new market data was collected. No price
row was promoted. The single remaining blocker is unchanged: written
PSX Terms resolution. Nothing here claims COMPLETE.

Branch for this record: `phase-05-revisit` (new, from
`phase-05-completion` tip `f4b703d`). The `phase-05-completion` tip is
NOT moved. Main is untouched.

## 1. State re-verified (direct queries + test runs, this run)

| Measure | Value | Method |
|---|---|---|
| market_prices rows | 444 | Direct DB count, before and after all work |
| Distinct trading dates | 1 (2026-11-03 only) | Direct DB count |
| quality_status | UNVERIFIED on all 444 | `GROUP BY quality_status` |
| Price source | `dps_market_summary_2026-11-03` on all 444 | `GROUP BY source_key` |
| bar_type | daily on all 444 | `GROUP BY bar_type` |
| is_adjusted = true | 0 | Direct DB count |
| previous_close / turnover / source_timestamp non-NULL | 0 / 0 / 0 | Direct DB count (fields absent from source, stored NULL, never fabricated) |
| trading_sessions rows | 0 | Direct DB count |
| index_prices rows | 0 | Direct DB count |
| Registry (entry dependency) | 470 companies / 470 securities / 940 evidence, all UNVERIFIED | Direct DB count |
| DataSource rows | 5 | Direct DB count — see note below |
| Backend suite (this tree) | 85 passed, 0 failed | pytest in worktree |
| Ruff | Clean | `ruff check` on market_data package, market endpoint, ingestion CLI |
| Code drift vs `phase-05-completion` | None (`git diff` empty for backend/ and scripts/) | git |

DataSource note: the earlier re-judgment recorded 2 DataSource rows.
The live count is now 5 because Phase 7 added 3 filing sources
(HUBC annual report 2026, NML quarterly 2025 Q3, OGDC RNS interim
2025 H1). The 2 Phase 5 sources are unchanged. This is a Phase 7
effect, not a Phase 5 change, and it does not touch any price row.

## 2. Engine and endpoint re-checks (this tree)

- `backend/app/services/market_data/`: `validation.py` (10 rejection
  codes, re-confirmed by name: missing_field, unknown_ticker,
  unparseable_date, unparseable_number, unparseable_timestamp,
  non_positive_price, negative_volume, negative_turnover,
  ohlc_inconsistency, future_trading_date), `ingestion.py`,
  `quality.py`, `scheduler.py` — all present, unmodified.
- `backend/app/api/v1/endpoints/market.py`: exactly 3 routes, all
  GET (`/market/prices`, `/market/prices/{ticker}/latest`,
  `/market/status`). No write route exists.
- No live adapter exists: a search of the market_data package, the
  market endpoint, and the ingestion CLI for HTTP client usage and
  for PSX/DPS/psxdata references returned no matches. No network
  fetch of market data occurs anywhere in Phase 5 code.
- CLI `scripts/run_market_ingestion.py`: `--dry-run` (default),
  `--commit`, `--catch-up` with `--from-date`/`--to-date`, and
  `--source-key` all present. Fail-fast on unknown tickers is
  implemented in the CLI before any write and is covered by the
  passing suite.
- CSV header contract unchanged: exactly
  `ticker,trading_date,open,high,low,close,volume,turnover,previous_close,source_key,source_timestamp`.

## 3. Dry-run reproduction (read-only, rolled back)

The mapped source file (gitignored, never committed) was re-run
through the CLI in `--dry-run` mode with
`--source-key dps_market_summary_2026-11-03`:

- ingested 0, skipped 444 (already stored), rejected 13,
  conflicted 0, stale 0, dry_run true.
- Rejection reasons reproduced exactly: ohlc_inconsistency 12,
  non_positive_price 1.
- DB count after the dry run: still 444. Nothing was written.

A first dry-run attempt without `--source-key` was also instructive:
it rejected all 444 otherwise-valid rows as missing_field, because
the mapped rows carry no per-row source_key and the CLI's
`--source-key` override supplies it. That run changed nothing and
confirms the source-key rule is enforced, not assumed.

## 4. Gaps (unchanged, never zero-filled)

- 13 rejected: 12 OHLC inconsistency + 1 non-positive price
  (reproduced above).
- 13 absent: registry tickers with no row in the source file
  (carried from the earlier verified run; the absent list was not
  re-derived in this revisit, and no row was fabricated for them).
- 564 futures-like rows from the source file remain excluded, as
  before. Field-9 of the source file remains uninterpreted and is
  never stored or relied on.

## 5. Source verdicts (unchanged, not reopened)

DPS BLOCKED for live adapters (dated-file route only); psx-dps
BLOCKED; psxdata BLOCKED; PSX homepage NOT SELECTED; SECP NOT
SELECTED for prices; intraday OUT OF SCOPE. Daily Quotations PDF
2026-11-03 NOT usable as daily OHLCV. Market Summary (Closing)
2026-11-03 remains the single usable dated source. No new evidence
was found or sought that would change any of these verdicts.

## 6. The single remaining blocker for COMPLETE

**Written PSX Terms resolution.** The permission email was sent
2026-11-04 from the user's mailbox to PSX's market-data address;
the user later reported a reply had arrived and that they
permanently deleted it, including from trash, so its wording is
unverifiable. The Terms question is therefore OPEN. This revisit
sent no email to PSX, collected no new market data, and claims no
clearance.

Note on what clearance would and would not do: verified written
permission would clear the Terms basis for the populated registry
and for further dated-file ingestion, but it alone would NOT
promote any price row to VERIFIED — promotion still requires rule
H1 (at least two distinct agreeing sources, including one official
source). All 444 rows stay UNVERIFIED until that independent
condition is met.

## 7. What would change the verdict to COMPLETE

1. Written PSX permission evidence produced and verified against
   the exact use (internal, non-commercial, private database).
2. A second agreeing source for price promotion under H1, or an
   explicit, documented decision that UNVERIFIED single-source
   prices are the accepted terminal state for Phase 5 (a scoping
   decision, not a verification claim).
3. Further trading days ingested through the same dated-file route
   (needs item 1 first, since new collection is Terms-gated).

Until then Phase 5 stays PARTIALLY COMPLETE, with its engine,
endpoints, tests, and single-day snapshot all verified and intact.
