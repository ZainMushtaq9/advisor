# Phase 8 — Health method health-v1

> **Descriptive profile only. NOT a credit rating, NOT investment
> advice, and NOT a buy/sell signal.** Scores describe the computed
> ratios against the bands below; they do not predict solvency,
> default, or future performance. This disclaimer is stored in every
> health row's evidence JSON and returned by the API.

## Structure

Seven scored dimensions: profitability, liquidity, solvency,
efficiency, cash_flow, growth, earnings_quality. Each dimension
scores 0–100 as the equal-weighted mean of its available sub-scores.
A dimension with no computable input scores NULL
(INSUFFICIENT_DATA), never zero. **No single aggregate grade is
produced** — deliberately, so the profile cannot masquerade as a
rating. The `sector` category likewise carries no numeric score,
only sector-profile evidence.

## Bands

Higher-is-better metrics: value ≥ first bound → 100; ≥ second
bound → 60; below → 0 for return/growth metrics, 20 otherwise.

| Metric | 100 | 60 | Below |
|---|---|---|---|
| net_margin, roa | ≥ 0.10 | ≥ 0 | 0 |
| roe_total | ≥ 0.15 | ≥ 0 | 0 |
| current_ratio | ≥ 2 | ≥ 1 | 20 |
| quick_ratio | ≥ 1 | ≥ 0.5 | 20 |
| cash_ratio | ≥ 0.5 | ≥ 0.2 | 20 |
| interest_coverage | ≥ 3 | ≥ 1.5 | 20 |
| dividend_cash_coverage | ≥ 1.5 | ≥ 1 | 20 |
| revenue_growth, pat_growth, eps_growth | ≥ 0.10 | ≥ 0 | 0 |

Lower-is-better metrics: value ≤ first bound → 100; ≤ second
bound → 60; above → 20.

| Metric | 100 | 60 | Above |
|---|---|---|---|
| debt_to_assets | ≤ 0.4 | ≤ 0.6 | 20 |
| debt_to_equity | ≤ 1 | ≤ 2 | 20 |
| receivables_days | ≤ 60 | ≤ 120 | 20 |
| inventory_days | ≤ 90 | ≤ 180 | 20 |
| accruals_to_pat (absolute) | ≤ 0.25 | ≤ 0.5 | 20 |
| gross_margin_change_pp (absolute) | ≤ 2 | ≤ 5 | 20 |

Special cases:

- **cash_conversion:** 0.8–1.2 → 100; 0.5–0.8 or 1.2–1.5 → 60;
  otherwise 20. When OCF and PAT are both negative, the ratio is
  arithmetically positive but economically meaningless: it scores
  20 with the `both_negative_do_not_interpret_as_strength` flag.
- **fcf_sign:** positive free cash flow → 100; otherwise 20.
- **Margin levels (gross/operating margin) are not scored.** Margin
  levels differ structurally by sector; scoring them would penalise
  textiles against power generation for structure, not health.
- **Earnings-quality cap:** when receivables grow faster than
  revenue by more than 10 percentage points, the earnings_quality
  dimension is capped at 60 pending review.

## Dimension composition

| Dimension | Sub-scores |
|---|---|
| profitability | net_margin, roa, roe_total |
| liquidity | current_ratio, quick_ratio, cash_ratio |
| solvency | debt_to_assets, debt_to_equity, interest_coverage (excluded when not applicable, e.g. OGDC) |
| efficiency | receivables_days, inventory_days (payables_days is reported, not scored: longer payables are neither inherently good nor bad) |
| cash_flow | cash_conversion, dividend_cash_coverage, fcf_sign |
| growth | revenue_growth, pat_growth, eps_growth |
| earnings_quality | accruals_to_pat, gross_margin_change_pp (+ divergence cap) |
| sector | no score; profile evidence only |

## Worked scores (this run)

| Dimension | HUBC FY2026 | NML 9M Mar 2025 | OGDC 6M Dec 2025 |
|---|---|---|---|
| profitability | 100.0000 | 0.0000 | 73.3333 |
| liquidity | 73.3333 | 46.6667 | 73.3333 |
| solvency | 100.0000 | 73.3333 | 100.0000 |
| efficiency | 60.0000 | 80.0000 | 60.0000 |
| cash_flow | 46.6667 | 20.0000 | 46.6667 |
| growth | 40.0000 | 0.0000 | 0.0000 |
| earnings_quality | 20.0000 | 60.0000 | 40.0000 |
| sector | NULL | NULL | NULL |

NML profitability is 0 because all three return sub-scores are
negative (negative PAT); that is the band outcome for losses, not a
missing-data default. OGDC solvency is 100 from its two available
leverage sub-scores; interest coverage is excluded as not
applicable, not scored as zero.
