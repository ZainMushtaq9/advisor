# Phase 12 breadth and liquidity — 2026-11-03 snapshot

Source: stored Phase 5 prices only (444 rows, one date, UNVERIFIED).

## Market breadth (13 rows)

| Metric | Value | Status |
|---|---|---|
| priced_coverage | 94.468085% (444/470) | computed |
| missing_securities | 26 | computed |
| total_volume | 441,360,098 | computed |
| median_volume | 54,631.5 | computed |
| top10_volume_share_pct | 49.249694% | computed |
| zero_volume_securities | 0 | computed |
| advances | NULL | insufficient_inputs — previous_close NULL on all rows |
| declines | NULL | insufficient_inputs — previous_close NULL on all rows |
| unchanged | NULL | insufficient_inputs — previous_close NULL on all rows |
| new_highs | NULL | insufficient_inputs — one date, no history |
| new_lows | NULL | insufficient_inputs — one date, no history |
| turnover_distribution | NULL | insufficient_inputs — turnover NULL on all rows |
| trading_day_frequency | 1 | partial — snapshot count, not a frequency |

## Sector participation (37 rows)

One `priced_coverage` row per sector (priced/total). Full coverage
(100%) in 23 sectors; lowest: SUGAR & ALLIED INDUSTRIES 19/24,
TEXTILE COMPOSITE 28/33, INSURANCE 25/29, TEXTILE SPINNING 32/34,
APPAREL 4/5, LEASING COMPANIES 2/3. The 26 missing tickers are the
13 Phase 5 rejections (ADAMS, AHTM, ALIFE, ASLCPS, BTL, GCWLPRS,
HAFL, IGIL, PRWM, SHSML, SNAI, TSML, SASML) plus the 13 absent
symbols (AGLNCPS, AKGL, ANLPS, AWTX, CENIR, EWIC, FCONM, GIL,
MSOTPS, SANSM, SAPT, SLCPA, STLR).

## Liquidity (889 rows)

Per-security volume + volume share for all 444 priced securities,
plus one MARKET total-volume row. Largest volumes: CNERGY
114,826,728 (26.02% of total), PRL 29,593,338, OBOY 13,005,389.
No turnover-based liquidity row exists (turnover NULL on all rows).

## Concentration — what is and is not claimed

- Volume concentration IS claimed: top-10 share 49.249694%.
- Market-cap concentration is NOT claimed: no share counts exist
  for the universe (HUBC only) and no free-float figure exists.
- Free-float-adjusted market measures are NOT computed.
