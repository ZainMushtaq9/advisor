# Dated official-source snapshot — PSX homepage scrip tables (PARTIAL)

- Source URL: https://www.psx.com.pk/
- Source name: Pakistan Stock Exchange Limited — homepage (psx.com.pk)
- Fetched: 2026-11-04 12:56 PKT (page crawled 2026-11-04 07:56 UTC, per fetch header)
- Fetch method: text fetch only (browser.open). No live-browser visit, no sign-in, no form use.
- Completeness: PARTIAL. The homepage itself does NOT state that these tables are a complete
  listed-company registry. These are the scrip rows actually shown in the fetched homepage text
  (volume leaders / GEM / highlighted symbols / futures / CDEC rows). No rows have been added,
  completed, or guessed. Company full names are NOT shown on this page — only scrip/symbol codes.
- Market context shown on the same fetch (not registry rows): Market Status Open;
  Current Index 170,625.32; Change 2606.46; Percent Change 1.55%; High 170,625.32;
  Low 168,355.26; Volume 162,397,606; Previous Close 168,018.86; Value 14,161,627,531.
- Row count in this file: 26 scrip rows (7 + 3 + 6 + 5 + 5). Futures/contract symbols
  (e.g. CNERGY-NOV, PPL-NOVB) are counted as shown, as separate rows, not merged with the
  underlying equity symbol. No sector, listing-status, or company-name field is shown for
  these rows on this page.

## Table 1 — SCRIP | PRICE | HIGH | LOW | CHANGE | VOLUME (7 rows)

| SCRIP | PRICE | HIGH | LOW | CHANGE | VOLUME |
|---|---|---|---|---|---|
| TPLP | 13.19 | 13.19 | 12.0 | 1.2 | 46,895,066 |
| PASL | 5.96 | 5.96 | 5.19 | 1.0 | 40,911,182 |
| CNERGY | 11.94 | 12.15 | 11.74 | 0.2 | 33,822,508 |
| BAPLR1 | 1.62 | 1.95 | 1.62 | -1.0 | 16,377,957 |
| MLCF | 97.0 | 97.5 | 93.4 | 4.02 | 15,993,101 |
| BOP | 29.19 | 29.35 | 28.2 | 1.1 | 15,576,315 |
| WTL | 0.92 | 0.97 | 0.91 | -0.03 | 14,327,535 |

## Table 2 — GEM board SCRIP | PRICE | HIGH | LOW | CHANGE | VOLUME (3 rows)

| SCRIP | PRICE | HIGH | LOW | CHANGE | VOLUME |
|---|---|---|---|---|---|
| GEMBCEM | 13.0 | 13.0 | 11.66 | 0.09 | 566 |
| GEMPACRA | 38.0 | 38.0 | 32.0 | 3.0 | 401 |
| GEMMEL | 32.3 | 32.3 | 32.3 | -2.95 | 1 |

## Table 3 — SYMBOL | PRICE | CHANGE | %CHANGE | VOLUME (6 rows)

| SYMBOL | PRICE | CHANGE | %CHANGE | VOLUME |
|---|---|---|---|---|
| AABS | 673.93 | 10.02 | 1.52 | 0.001 |
| KAPCO | 24.4 | 0.26 | 1.07 | 0.245 |
| KML | 8.3 | 0.43 | 5.38 | 0.397 |
| OGDC | 309.88 | 6.25 | 2.06 | 1.667 |
| PAEL | 32.35 | 0.44 | 1.38 | 7.188 |
| PPL | 217.45 | 4.54 | 2.13 | 1.695 |

## Table 4 — Futures SYMBOL | OPEN | HIGH | LOW | CURRENT | CHANGE | VOLUME (5 rows)

| SYMBOL | OPEN | HIGH | LOW | CURRENT | CHANGE | VOLUME |
|---|---|---|---|---|---|---|
| CNERGY-NOV | 11.84 | 12.22 | 11.81 | 12.02 | 0.18 | 16904500 |
| TPLP-NOV | 12.06 | 13.27 | 12.02 | 13.27 | 1.21 | 15710500 |
| PPL-NOVB | 213.3 | 218.0 | 214.0 | 217.6 | 4.3 | 5436500 |
| MLCF-NOV | 93.55 | 97.9 | 93.76 | 97.5 | 3.95 | 5221500 |
| PPL-NOVC | 213.23 | 217.8 | 214.48 | 217.4 | 4.17 | 5204000 |

## Table 5 — CDEC SYMBOL | OPEN | HIGH | LOW | CURRENT | CHANGE | VOLUME (5 rows)

| SYMBOL | OPEN | HIGH | LOW | CURRENT | CHANGE | VOLUME |
|---|---|---|---|---|---|---|
| AIRLINK-CDEC | 174.69 | 0 | 0 | 0 | (blank in source) | 4000 |
| FCCL-CDEC | 53.8 | 0 | 0 | 0 | (blank in source) | 2000 |
| OGDC-CDEC | 268.11 | 0 | 0 | 0 | (blank in source) | 2000 |
| HUBC-CDEC | 223.86 | 0 | 0 | 0 | (blank in source) | 1000 |
| PPL-CDEC | 212.82 | 0 | 0 | 0 | (blank in source) | 1000 |

## Excluded from the row count (not ticker rows)

The same homepage fetch also showed a "Financial results" table naming companies without
tickers (Quice Food; Atlas Honda Ltd; Hum Network twice; TPL Insurance; Amreli Steels)
and dated PSX/company announcements (symbols OLPL, BAPL, LSECL in announcement titles).
Those names/symbols were NOT counted as registry rows because the page gives no
sector, listing-status, or company-to-ticker mapping for them in that table.
