# Phase 9 — Valuation methodology v1.0

## Entry dependency (brief)

Phase 9's brief requires "verified Phases 5, 7 and 8 data". The
honest entry state is weaker, and this methodology is written for
the actual state, not the brief's assumed state:

- Phase 5 prices: 444 rows, exactly one trading date (2026-11-03),
  all UNVERIFIED, unadjusted closes, no share-count data, no
  corporate-action adjustment methodology, no publication alignment
  beyond the statement publication dates recorded in Phase 7.
- Phase 7 statements: 3 companies (HUBC, NML, OGDC), all
  UNVERIFIED. HUBC FY2026 annual (audited, consolidated, published
  2026-09-21); NML nine months to 31 Mar 2025 (unaudited,
  consolidated, publication date NULL); OGDC six months to
  31 Dec 2025 (unaudited, consolidated, published 2026-02-23).
- Phase 8 ratios: 36 metrics, 108 value rows, all UNVERIFIED.
- HBL (Habib Bank Limited): PENDING — no statements loaded, so no
  valuation rows at all.

Every valuation row therefore carries quality_status UNVERIFIED and
its computation_status in the assumptions JSON. Calculation never
upgrades input quality.

## Valuation dates

- Price-based and assumption-gated methods: valuation_date =
  2026-11-03 (the price date).
- Statement-date methods (book value, sum-of-parts):
  valuation_date = the balance-sheet date. These are statement-date
  values, not market fair values at the price date, and the row
  flags say so.

## Point-in-time rule (historical validity)

A price-based method is point-in-time valid only when the statement
it uses was published on or before the valuation date:

- HUBC: published 2026-09-21 <= 2026-11-03 — valid.
- OGDC: published 2026-02-23 <= 2026-11-03 — valid.
- NML: publication date NULL — validity cannot be shown, so every
  NML price-based method is NOT_CALCULABLE even before the EPS test
  (its nine-month EPS is also negative, an independent block).

No future price and no statement published after the valuation date
is used anywhere. Restatements, when they arrive, are new valuation
rows (new method version), never edits of existing rows.

## The Phase 8 refinement (stated, not hidden)

Phase 8 recorded pe/pb/div_yield as insufficient_inputs for all
three companies for a combined reason (single unadjusted close, no
adjustment methodology, no share-count data, price/publication
misalignment). Phase 9 refines that ruling per method:

- Trailing P/E = close_price / EPS needs no share count, so it
  becomes computable where EPS is positive AND publication is known
  and on/before the valuation date (HUBC, OGDC). A single
  unadjusted official close is a valid point-in-time price;
  adjustment methodology matters for price series, not for a
  single-date multiple.
- P/B, P/S, market cap, enterprise value, EV multiples, cash-flow
  yield and dividend yield still need share counts (and DPS for the
  yield), which do not exist — they stay NOT_CALCULABLE.
- This does not revise any Phase 8 row. Phase 8 rows stand as
  Phase 8 scope; Phase 9 rows carry their own method keys and
  applicability rulings.

## What computed in v1.0 (7 of 51 rows)

| Company | Method | Value | Basis |
|---|---|---|---|
| HUBC | multiples:pe_trailing | 5.1553x | 197.24 / 38.26 (FY2026 EPS, published 2026-09-21) |
| OGDC | multiples:pe_trailing | 17.8816x | 303.63 / 16.98 (6M EPS, published 2026-02-23) |
| HUBC | asset_based:equity_book_value_total | Rs 258,007,509,000 | total_equity at 2026-06-30 |
| HUBC | asset_based:equity_book_value_owners | Rs 235,381,655,000 | owners equity at 2026-06-30 |
| NML | asset_based:equity_book_value_total | Rs 159,920,849,000 | total_equity at 2025-03-31 |
| NML | asset_based:equity_book_value_owners | Rs 146,538,114,000 | owners equity at 2025-03-31 |
| OGDC | asset_based:equity_book_value_total | Rs 1,383,637,471,000 | total_equity at 2025-12-31 |

Book values are company-level, not per-share, and are not market
fair values. P/E sensitivity is mechanical only: HUBC 4.6397x at
-10% price / 5.6708x at +10%; OGDC 16.0935x / 19.6698x. Sensitivity
is stored in the row's value_low/value_high and sensitivity JSON.

## What did not compute, and why (44 of 51 rows)

- Share-count methods (P/B, P/S, market cap, EV, EV/EBITDA,
  EV/EBIT, cash-flow yield): no share-count data. Share capital in
  PKR cannot be converted to shares without a par value, which is
  not in the data. Deriving one would be fabrication.
- Dividend yield / DDM: no dividend-per-share series; dividends_paid
  totals exist but no share count converts them to DPS, and no
  payout-growth pattern is established.
- DCF (FCFF/FCFE): no source-backed discount rate, growth rate, or
  forecast cash flows. Phase 10 macro inputs do not exist yet.
  Inventing a WACC would be fabrication. The models are implemented
  and hand-tested on fixtures; production runs return
  NOT_CALCULABLE by construction (no assumptions are passed).
- Peer median P/E: each company is alone in its sector among
  statement companies; cross-sector peers are never forced. The
  peer engine (sector + frequency + 90-day period alignment, 3x
  median outlier rule above 4 peers, median needs >= 3 peers) is
  implemented and tested on fixtures.
- Sum-of-parts: no segment-level statements.
- Residual income (bank): not_applicable for all three industrials.
  It is a bank model; HBL is pending, so no bank row exists yet.
- NML P/E: two independent blocks — negative nine-month EPS
  (-0.42, non-meaningful multiple) and unknown publication date.
- OGDC owners book value: no owners/NCI split on the extracted
  balance sheet.

## What this is not

Valuation outputs are descriptive estimates with stated assumptions
and uncertainty. They are NOT price targets presented as fact, NOT
investment advice, and NOT buy/sell signals. Phase 15 owns
proposals; Phase 9 does not pre-empt it. No incompatible models are
averaged: each row stands alone with its own method, inputs, and
reason. The health layer from Phase 8 is not reused as a valuation
input (it is descriptive, not a value driver).
