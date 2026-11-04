# Phase 12 ownership dataset — HUBC as at 2026-06-30

Source: HUBC Integrated Annual Report 2026, "Categories of
Shareholding" (printed p. 383, PDF p. 384) and "Key Shareholding"
(printed p. 384, PDF p. 385). Extracted with PyMuPDF and pdfplumber;
both agreed on all values.

## Category totals (17 rows + 1 totals row)

| Category | Holders | Shares | % |
|---|---|---|---|
| Individuals — Local | 79,262 | 496,387,210 | 38.27 |
| Individuals — Foreign | 320 | 300,283 | 0.02 |
| Joint Stock Companies | 310 | 40,466,679 | 3.11 |
| Financial Institutions | 45 | 72,134,823 | 5.56 |
| Investment Companies | 32 | 26,577,092 | 2.05 |
| Insurance Companies | 28 | 77,235,790 | 5.95 |
| Associated Companies | 7 | 264,146,002 | 20.36 |
| Directors | 9 | 1,006,244 | 0.08 |
| Executives | 5 | 14,400 | 0.00 |
| NIT & ICP | 0 (printed "-") | 0 (printed "-") | NULL (printed "-") |
| Modaraba / Mutual Fund & Leasing | 115 | 140,321,749 | 10.82 |
| Others — Government of Balochistan | 1 | 358,607 | 0.03 |
| Others — GDR Depository | 1 | 650 | 0.00 |
| Others — Charitable Trusts | 49 | 122,848,220 | 9.47 |
| Others — Cooperative Societies | 8 | 1,085,522 | 0.08 |
| Others — Provident / Pension / Gratuity | 184 | 48,996,921 | 3.78 |
| Employee's Old Age Benefits Institution | 1 | 5,274,195 | 0.41 |
| **TOTAL** | **80,377** | **1,297,154,387** | **100.00** |

Reconciliation: holders sum to 80,377; shares sum to 1,297,154,387;
percentages sum to 99.99 (printed total 100.00; 0.01 rounding).
CDC note printed in the document: 76,194 shareholders holding
1,293,129,998 shares via CDC; the remainder (4,183 holders /
4,024,389 shares) is held outside CDC. The "OTHERS" line is a section
header, not a category; only its six sub-rows are stored.

## Named key holders (16 rows)

Associated companies (7 rows, sum 264,146,002 = category total):
MEGA CONGLOMERATE (PVT.) LIMITED appears under two folios
(28,213,975 and 224,428,064) and is stored as two rows; other names:
Imperial Developers and Builder (235,967), Forbes Shipping
(2,871,885), Inservey Pakistan (216,910), Inshipping (3,310,721),
Askari Bank (4,868,480).

Directors (9 rows, sum 1,006,244 = category total): Muhammad Habib
Ullah Khan (560), Aly Khan (560), Aleeya Khan (560), Shafiuddin
Ghani Khan (203,000), Saad Iqbal (613,870), Syed Bakhtiyar Kazmi
(50), Manzoor Ahmed (5), Muhammad Kamran Kamal under two folios
(87,639 and 100,000).

## NOT in this dataset

- Free float: no free-float figure is published in this document,
  and PSX free-float data is Terms-gated. No free-float-adjusted
  measure is computed.
- Beneficial ownership beyond the printed categories/names: never
  inferred.
- Any other company: only HUBC's document was loaded in this run.
  NML and OGDC interim reports carry no shareholding pattern tables.
