# Phase 20 — Filter Registry

Every filter: key, category, unit, source table, sector
applicability, supported threshold kinds, and the exact
semantics. The registry lives in
`backend/app/services/screener/__init__.py` (FILTER_REGISTRY);
this document is its human-readable mirror. If they ever
disagree, the code is authoritative and this document is the
bug.

## Price / volume (source: market_prices, 2026-11-03)

| Filter | Unit | Kinds | Semantics |
|---|---|---|---|
| close_price | PKR | absolute, percentile | Official unadjusted close on 2026-11-03. NULL when no price row → MISSING_VALUE. |
| volume | shares | absolute, percentile | Traded volume on 2026-11-03. NULL when no price row → MISSING_VALUE. |
| price_present | boolean | presence | Pass iff a 2026-11-03 price row exists. Absence is a FAIL, not missing data: the question asked is existence. |
| volume_share_pct | pct | absolute, percentile | Phase 12 share of total 2026-11-03 market volume. |

## Fundamentals (source: fundamental_metric_values, latest computed row per company)

Industrial-only: NOT_APPLICABLE for COMMERCIAL BANKS (HBL).
A non-bank company without a computed row → MISSING_VALUE.

| Filter | Unit | Notes |
|---|---|---|
| roe_total | ratio | Total ROE, latest computed period. |
| roa | ratio | Return on assets. |
| net_margin | ratio | Net margin. |
| gross_margin | ratio | Gross margin. |
| current_ratio | x | Current ratio. |
| receivables_days | days | Receivables days. |
| debt_to_equity | ratio | Leverage. |

## Valuation (source: valuations)

| Filter | Unit | Notes |
|---|---|---|
| pe_trailing | x | Phase 9 multiples:pe_trailing. HUBC 5.1553 (FY2026, full-year); OGDC 17.8816 (6-month interim — labelled as such in evidence); NML insufficient (negative EPS and unknown publication date) → MISSING_VALUE. P/B, P/S, market cap, EV multiples are NOT offered: Phase 9 recorded them insufficient (no share counts). |

## Dividend (source: corporate_action_records)

| Filter | Unit | Notes |
|---|---|---|
| dividend_per_share | PKR | Presence: pass iff a DIVIDEND_CASH action exists. Absolute: compares the maximum stored amount — all stored actions carry NULL dates, so the latest action cannot be determined and the value is labelled "maximum stored amount", never "latest". HUBC 10.00, NML 5.00. |

## News / event / risk / freshness

| Filter | Unit | Notes |
|---|---|---|
| news_event_present | boolean | Pass iff ≥ 1 company-linked news event exists (via news_event_companies or primary_company_id). Coverage caveat: events loaded for 3 companies only. |
| risk_flag_present | boolean | Pass iff ≥ 1 review-only risk flag exists. Flags are never fraud, default, or solvency findings. |
| statement_age_days | days | Days from latest statement period end to screen as-of date (2026-11-04). Over 365 days also raises STALE_INPUT (NML 583 days; HUBC 127; OGDC 308). |

## Technical (source: technical_indicator_values)

| Filter | Unit | Notes |
|---|---|---|
| sma_5 | PKR | NOT_CALCULABLE for all 470: 0 calculable values; 5 closes needed, 1 trading date exists. |
| rsi_14 | points | NOT_CALCULABLE for all 470: 0 calculable values; 15 observations needed, 1 trading date exists. |

## Percentile semantics

percentile = 100 × (peers with a strictly smaller present
value) / (peers with any present value). Price/volume peer
set = the 444 priced securities. Ratio peer set = the
statement companies with a computed value (at most 3), named
in evidence. A peer set of size 1 yields 0.0 with a
degenerate-peer-set flag; a peer set of size 0 yields
MISSING_VALUE. Ties: equal values do not count as "below",
so a tied top value can miss a percentile threshold — that
is the documented rule, not a bug.

## Reason codes

PASS, FAIL_THRESHOLD, MISSING_VALUE, NOT_CALCULABLE,
SECTOR_NOT_APPLICABLE, plus the evidence-only STALE_INPUT
flag (staleness never changes a score).
