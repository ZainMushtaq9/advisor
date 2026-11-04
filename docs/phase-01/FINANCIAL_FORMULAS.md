# PSX Intelligence AI — Financial Formulas Specification

**Phase:** 1 of 30 — Specification only. No application code in this phase beyond tiny formula examples shown below.
**Team:** Team 7 (Financial Analytics + Security + Governance)
**Date / starting condition:** Verified 2026-11-04, reused verbatim (see §0).
**Status:** DRAFT specification. Nothing in this document is a price, forecast, recommendation, or investment advice.

## 0. Starting condition and governing rules (reuse verbatim)

- Project folder `~/workspace/psx-intelligence-ai/` is new. Other teams may be creating sibling files.
- Existing separate scaffold to REFERENCE but NEVER overwrite/touch: `~/workspace/psx-data-collection/` (stdlib collector with provenance / PKT / stale / conflict rules).
- Tools: Python 3.12.3, Node v24.22.1. Docker, psql, redis-cli NOT installed.
- Already verified (reuse): psx-dps (~496 trading vs ~1029 listed, ~5y EOD, today's ticks, 38 sectors, multi-node 404 quirk, no official PSX API); psxdata (daily OHLCV + live snapshots ONLY, no historical intraday archive — so VWAP / intraday-dependent metrics are limited to what data permits, and historical intraday backtests must not be assumed); Eulerpool: NO PSX coverage, vendor only, no paid API approved.
- SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use is UNVERIFIED — formulas depending on macro / fundamental feeds must state the feed as UNVERIFIED and define missing-data handling (skip / flag, never estimate silently).

### 0.0 Revised brief — merged (PKR 0 budget, 11-stage workflow, no real trading)

- **Budget: PKR 0 absolute zero-cost.** Analytics and forecasting in this specification must use local open-source libraries only — Pandas / NumPy / scikit-learn / statsmodels / PyTorch where justified — and Ollama local inference only. No paid AI APIs, no paid subscriptions, no paid data vendor is approved or assumed anywhere in this document. Eulerpool is vendor-only with no paid API approved (see §0); that position is unchanged.
- **"Free" disclosure rule.** Local hardware, electricity, and internet are EXTERNAL operating expenses. They must be disclosed as such wherever cost is discussed, and must never be described as "free". PKR 0 means zero project spend on software, APIs, subscriptions, and vendors — not zero operating cost to run a machine.
- **Phase 1 workflow (11 stages, this document sits inside it):** (1) brainstorm, (2) research, (3) validate, (4) data inspection — read-only only, NO full-scale live data collection in Phase 1, (5) architecture planning, (6) implementation specification, (7) documentation, (8) testing strategy — defined, not claimed passed, (9) independent audit, (10) correction, (11) checkpoint. This file is a specification (stages 6–7); it is not an implementation, not a test pass, and not a data-collection run.
- **No real trading initially.** The system must NOT execute real trades initially. This is stated explicitly in `SECURITY_REQUIREMENTS.md` (trading restrictions) and `FINANCIAL_GOVERNANCE.md`, and it constrains every formula in this document: no formula output is a trade instruction, and no output may be wired to an order, broker, or execution path in Phase 1.
- **STOP AFTER PHASE 1.** No Phase 2 work, no application code beyond the tiny formula examples in §0.3, and no live polling, broker connection, sign-up, install, purchase, or credential is authorised by this specification.

### 0.1 Non-negotiable calculation rules

1. **Deterministic Python functions ONLY.** Every numerical financial result in the future system must be produced by a deterministic, testable Python function from recorded inputs. LLMs must NEVER invent numerical financial results, fill a missing input with a plausible value, or round away uncertainty.
2. **No fabricated data.** If an input is absent, the output is absent (or explicitly flagged), not estimated. Silent estimation is prohibited.
3. **Provenance on every result.** Every computed value must carry: source(s), as-of date/time in PKT, data vintage, and staleness/conflict flags inherited from the `psx-data-collection` provenance rules.
4. **Probabilistic, never guaranteed.** Forecasts and BUY / HOLD / SELL / WATCHLIST outputs are probabilistic recommendations with uncertainty shown, not advice guarantees (see `FORECASTING_SPECIFICATION.md` and `FINANCIAL_GOVERNANCE.md`).
5. **No unauthorised trading, no live polling, no broker connection, no sign-up, install, purchase, credential, or API key in this phase.** No API, endpoint, price, benchmark, or capability is invented in this document. Anything not verified is marked UNVERIFIED.
6. **Currency and units.** Unless a future verified source states otherwise, monetary values are in PKR as reported by the source; ratios are unitless; yields/margins/growth are shown as percentages with the raw ratio retained. Never convert currency without a stated, sourced FX rate and date.

### 0.2 How to read each formula entry

Every formula below follows the same template:

- **Mathematical definition** — the exact formula.
- **Input variables** — each variable, its meaning, and its unit.
- **Data sources** — verified vs UNVERIFIED, with the exact limitation.
- **Calculation frequency** — when the value is (re)computed.
- **Missing-data handling** — skip / flag rule. Never silent estimation.
- **Industry limitations** — where the formula breaks or misleads.
- **Validation method** — how the deterministic function is tested.

### 0.3 Tiny formula examples (illustrative only, not application code)

These snippets show the *shape* of a deterministic function. They are not a runnable module and must not be copied into production without tests, provenance, and the missing-data rules in §0.1.

```python
def gross_margin(gross_profit, revenue):
    # Returns None when inputs are missing or revenue is zero — never 0 by default.
    if gross_profit is None or revenue is None or revenue == 0:
        return None
    return gross_profit / revenue

def current_ratio(current_assets, current_liabilities):
    if current_assets is None or current_liabilities is None or current_liabilities == 0:
        return None
    return current_assets / current_liabilities
```

A function returning `None` must surface in the UI as "Not available — [reason]" (see `ANALYTICS_SPECIFICATION.md` §5), never as 0, a dash silently treated as 0, or a prior-period value relabelled as current.

---

## 1. Profitability

All profitability inputs (revenue, gross profit, operating income, net income, total assets, equity, invested capital, NOPAT) come from company financial statements.

- **Data source status: UNVERIFIED for machine use.** No verified machine-readable PSX fundamental feed was confirmed in the 2026-11-04 starting condition. SECP filings and any vendor fundamental feed are UNVERIFIED until a future phase verifies licence, format, coverage, and update cadence. Do NOT assume psx-dps or psxdata supplies fundamentals — psx-dps supplies EOD prices / ticks and sector lists; psxdata supplies daily OHLCV + live snapshots only.
- **Consequence:** Until a fundamental feed is verified, every ratio in §1 must display as "Not available — fundamental feed UNVERIFIED" rather than a computed value, even if a value could be hand-copied from a filing. Manual entry, if ever allowed in a later phase, requires its own provenance, reviewer, and audit rule and is NOT authorised by this specification.

### 1.1 Gross margin

- **Definition:** `Gross Margin = Gross Profit / Revenue`
- **Inputs:** `Gross Profit` (PKR, revenue minus cost of goods sold / cost of sales); `Revenue` (PKR).
- **Sources:** Company financial statements — UNVERIFIED machine feed (see §1 header).
- **Frequency:** On each new verified financial statement (quarterly / annual as reported); otherwise unchanged, with its statement period shown.
- **Missing-data handling:** If either input is missing, or revenue = 0, return no value and flag `missing_input`. Never substitute operating profit for gross profit.
- **Industry limitations:** Not comparable across sectors with structurally different cost bases (e.g. banks do not report gross profit in the same way as manufacturers; trading companies vs cement vs banks are not like-for-like). Negative gross profit yields a negative margin — show it, do not clamp to 0.
- **Validation:** Unit test with known statement pairs; test revenue = 0 → no value; test negative gross profit → negative result; test that a missing input never yields a prior-period value.

### 1.2 Operating margin

- **Definition:** `Operating Margin = Operating Income (EBIT) / Revenue`
- **Inputs:** `Operating Income` (PKR, earnings before interest and tax); `Revenue` (PKR).
- **Sources:** As §1 header — UNVERIFIED.
- **Frequency:** Per verified statement, as §1.1.
- **Missing-data handling:** Missing EBIT or revenue, or revenue = 0 → no value, flag `missing_input`. Do not derive EBIT from net income by adding back an assumed tax/interest figure.
- **Industry limitations:** One-off gains/losses, revaluations, and differing treatment of other income distort comparability. Banks' "operating income" definitions differ from non-financials; cross-sector ranking on this ratio alone is misleading.
- **Validation:** As §1.1, plus a test that one-off items are NOT stripped out silently — any adjusted operating margin is a separate, labelled metric, not a replacement.

### 1.3 Net margin

- **Definition:** `Net Margin = Net Income / Revenue`
- **Inputs:** `Net Income` (PKR, profit after tax attributable as reported); `Revenue` (PKR).
- **Sources:** As §1 header — UNVERIFIED.
- **Frequency:** Per verified statement.
- **Missing-data handling:** Missing either input or revenue = 0 → no value. Do not use profit before tax as a proxy for net income.
- **Industry limitations:** Tax, financing structure, and non-recurring items dominate differences; a high net margin does not imply a high-quality or sustainable margin. Loss-making companies show negative margins — show them.
- **Validation:** As §1.1.

### 1.4 Return on assets (ROA)

- **Definition:** `ROA = Net Income / Average Total Assets`, where `Average Total Assets = (Total Assets at start of period + Total Assets at end of period) / 2`.
- **Inputs:** `Net Income` (PKR, period); `Total Assets` (PKR, start and end of period).
- **Sources:** As §1 header — UNVERIFIED.
- **Frequency:** Per verified statement period. If only end-of-period assets are available, do NOT silently use end assets as the average — see missing-data rule.
- **Missing-data handling:** If start-of-period assets are missing, either (a) show no ROA, or (b) show a separately labelled `ROA (end-of-period assets)` with the substitution stated in the UI. The default is (a). Never average across a missing endpoint.
- **Industry limitations:** Asset-light vs asset-heavy sectors are not comparable; banks' balance sheets make ROA structurally lower than manufacturers'. Asset revaluations inflate the denominator without changing earnings power.
- **Validation:** Test two-point average; test missing start assets → no (default) ROA; test that ROA is period-matched (annual income over annual-average assets, not mixed with quarterly income without annualisation stated).

### 1.5 Return on equity (ROE)

- **Definition:** `ROE = Net Income / Average Shareholders' Equity`, where average equity is the two-point average as in §1.4.
- **Inputs:** `Net Income` (PKR); `Shareholders' Equity` (PKR, start and end).
- **Sources:** As §1 header — UNVERIFIED.
- **Frequency:** Per verified statement period.
- **Missing-data handling:** As §1.4. If average equity ≤ 0 (negative equity), ROE is not meaningful — show no value with flag `non_meaningful_negative_equity`, never a large positive/negative percentage from dividing by a near-zero or negative base.
- **Industry limitations:** Leverage inflates ROE without improving operating performance; buybacks, revaluations, and negative equity break interpretation. Banks vs non-financials are not directly comparable.
- **Validation:** Test negative/zero equity → no value; test leverage sensitivity is documented, not hidden.

### 1.6 Return on invested capital (ROIC)

- **Definition:** `ROIC = NOPAT / Average Invested Capital`, where `NOPAT = EBIT × (1 − Effective Tax Rate)` and `Invested Capital = Total Debt + Shareholders' Equity` (or equivalently total assets minus non-interest-bearing current liabilities, if that definition is the one the verified source uses — the definition in use must be stated wherever ROIC is shown).
- **Inputs:** `EBIT` (PKR); `Effective Tax Rate` (ratio, as reported — never an assumed statutory rate unless labelled as an assumption); `Total Debt` (PKR); `Shareholders' Equity` (PKR).
- **Sources:** As §1 header — UNVERIFIED. Effective tax rate in particular must come from the reported statements, not an assumed rate.
- **Frequency:** Per verified statement period.
- **Missing-data handling:** Missing EBIT, tax rate, debt, or equity → no value. If the tax rate is missing, do NOT assume a rate. If invested capital ≤ 0 → no value with `non_meaningful` flag.
- **Industry limitations:** Definition of invested capital varies by source (operating leases, cash treatment, goodwill). Cross-source ROIC comparisons are invalid unless the same definition is used. Banks: ROIC as defined for non-financials is generally NOT applicable — see §7. Do not show a bank ROIC computed with a non-financial definition without an explicit warning.
- **Validation:** Test that changing the invested-capital definition changes the label; test missing tax rate → no value; test that NOPAT is never computed from net income plus an assumed interest figure.

---

## 2. Liquidity

Balance-sheet inputs. Same UNVERIFIED fundamental-feed status as §1. Liquidity ratios are point-in-time (statement date), not averages.

### 2.1 Current ratio

- **Definition:** `Current Ratio = Current Assets / Current Liabilities`
- **Inputs:** `Current Assets` (PKR); `Current Liabilities` (PKR), both at the same statement date.
- **Sources:** Company financial statements — UNVERIFIED machine feed.
- **Frequency:** Per verified statement; show statement date alongside.
- **Missing-data handling:** Missing either input or current liabilities = 0 → no value.
- **Industry limitations:** A ratio > 1 does not guarantee liquidity (inventory may be unsaleable, receivables may be uncollectable). Sector norms differ sharply; banks' current/non-current split is not equivalent to manufacturers'.
- **Validation:** Date-matching test (assets and liabilities from different statement dates must not be combined); zero-denominator test.

### 2.2 Quick ratio (acid-test)

- **Definition:** `Quick Ratio = (Current Assets − Inventory) / Current Liabilities`
- **Inputs:** `Current Assets`, `Inventory`, `Current Liabilities` (PKR, same date).
- **Sources:** As §2 header — UNVERIFIED.
- **Frequency:** Per verified statement.
- **Missing-data handling:** Missing inventory → no quick ratio. Do NOT assume inventory = 0 (that would silently equate quick ratio with current ratio). If a company genuinely reports no inventory, that fact must be recorded as an input value of 0 from the source, not inferred.
- **Industry limitations:** Still includes receivables of uncertain collectability. For banks and service companies, inventory is typically absent or immaterial — the ratio adds little and must not be ranked against manufacturers.
- **Validation:** Test missing inventory → no value (not current ratio); test recorded-zero inventory → quick ratio computed and labelled.

### 2.3 Cash ratio

- **Definition:** `Cash Ratio = (Cash + Cash Equivalents) / Current Liabilities`
- **Inputs:** `Cash + Cash Equivalents` (PKR); `Current Liabilities` (PKR, same date).
- **Sources:** As §2 header — UNVERIFIED.
- **Frequency:** Per verified statement.
- **Missing-data handling:** Missing cash or liabilities, or liabilities = 0 → no value. Do not include short-term investments unless the source's definition of cash equivalents explicitly includes them and the label says so.
- **Industry limitations:** Most conservative liquidity measure; a low cash ratio is normal for many healthy companies and does not alone signal distress. Point-in-time cash can be window-dressed around statement dates.
- **Validation:** Test that short-term investments are excluded by default; test date-matching as §2.1.

---

## 3. Leverage

Balance-sheet and income-statement inputs. Same UNVERIFIED status as §1.

### 3.1 Debt-to-equity ratio

- **Definition:** `Debt-to-Equity = Total Debt / Shareholders' Equity`. The debt definition in use (interest-bearing debt only, vs total liabilities) MUST be stated wherever the ratio is shown, because sources differ.
- **Inputs:** `Total Debt` (PKR, per stated definition); `Shareholders' Equity` (PKR, same date).
- **Sources:** Company financial statements — UNVERIFIED machine feed.
- **Frequency:** Per verified statement.
- **Missing-data handling:** Missing debt or equity, or equity ≤ 0 → no value (negative-equity flag as §1.5). If the debt definition changes between periods, the series must break with a stated definition-change note, not be spliced silently.
- **Industry limitations:** Banks are inherently highly levered by business model — a bank debt-to-equity ratio is not comparable to a manufacturer's. Total-liabilities vs interest-bearing-debt definitions give materially different values.
- **Validation:** Test definition label travels with the value; test negative equity → no value; test definition-change break.

### 3.2 Interest coverage ratio

- **Definition:** `Interest Coverage = EBIT / Interest Expense`
- **Inputs:** `EBIT` (PKR, period); `Interest Expense` (PKR, same period).
- **Sources:** As §3 header — UNVERIFIED.
- **Frequency:** Per verified statement period.
- **Missing-data handling:** Missing either input or interest expense = 0 → no value (a zero interest expense does not mean infinite coverage; it means the ratio is undefined on that input). Do not substitute finance cost aggregates that include non-interest items without labelling the substitution.
- **Industry limitations:** EBIT volatility makes a single-period coverage ratio noisy; lumpy interest (e.g. Sukuk / bond coupons) distorts quarterly coverage. Islamic-finance profit/rental charges may not be labelled "interest" — mapping them to interest expense without a stated rule is prohibited.
- **Validation:** Test zero interest → no value; test period-matching; test that any finance-cost mapping rule is recorded and shown.

### 3.3 Net debt

- **Definition:** `Net Debt = Total Debt − (Cash + Cash Equivalents)`. A negative result means net cash — show it as negative net debt / net cash, do not clamp to 0.
- **Inputs:** `Total Debt` (PKR, per stated definition as §3.1); `Cash + Cash Equivalents` (PKR, same date).
- **Sources:** As §3 header — UNVERIFIED.
- **Frequency:** Per verified statement.
- **Missing-data handling:** Missing debt or cash → no value. Do not assume cash = 0.
- **Industry limitations:** Net debt flatters companies holding cash for a stated purpose (e.g. earmarked capex) and penalises none of the maturity structure — short-term vs long-term debt mix is invisible in this single number. Always show gross debt and cash alongside net debt.
- **Validation:** Test net-cash (negative) case is shown, not clamped; test missing cash → no value.

---

## 4. Valuation ratios

Price inputs come from market data; per-share fundamental inputs come from statements. Both legs must be verified before a ratio is shown.

- **Price source status:** psx-dps EOD prices are the verified-in-principle market source (subject to its ~5y history, multi-node 404 quirk, and trading-vs-listed distinction); psxdata daily OHLCV is a secondary verified-in-principle source. Any price used must carry its source, date (PKT), and staleness flag. A stale price (per `psx-data-collection` rules) must not feed a valuation ratio without a staleness warning.
- **Fundamental leg status:** EPS, book value per share, revenue per share, EBITDA, dividends per share, free cash flow — all UNVERIFIED machine feed (see §1 header).
- **Consequence:** Until the fundamental leg is verified, valuation ratios in §4 must show as "Not available" with the reason stated, even when a price is available. A price alone never yields a P/E, P/B, or P/S.

### 4.1 Price-to-earnings (P/E)

- **Definition:** `P/E = Market Price per Share / Earnings per Share (EPS)`. State whether EPS is trailing-twelve-months (TTM) or annual — mixing them without a label is prohibited.
- **Inputs:** `Price` (PKR/share, dated); `EPS` (PKR/share, stated period).
- **Sources:** Price — psx-dps / psxdata (see §4 header). EPS — UNVERIFIED fundamental feed.
- **Frequency:** On each new price (daily, EOD) AND on each new verified EPS; show both dates.
- **Missing-data handling:** Missing price, EPS, or EPS ≤ 0 → no P/E. Negative EPS yields no meaningful P/E — flag `negative_earnings`, never a negative P/E presented as a valuation signal. Do not annualise a quarterly EPS silently; if annualised, label it `P/E (annualised EPS)` with the method stated.
- **Industry limitations:** Cyclical earnings, one-offs, and loss years break P/E comparability. Banks' EPS reflects provisioning cycles. A low P/E is not by itself a buy signal.
- **Validation:** Test negative EPS → no value; test stale price → warning travels with ratio; test TTM vs annual label.

### 4.2 Price-to-book (P/B)

- **Definition:** `P/B = Market Price per Share / Book Value per Share (BVPS)`, where `BVPS = Shareholders' Equity / Shares Outstanding`.
- **Inputs:** `Price` (PKR/share, dated); `Equity` (PKR); `Shares Outstanding` (count, same date basis).
- **Sources:** Price — as §4 header. Equity / shares — UNVERIFIED fundamental feed.
- **Frequency:** As §4.1.
- **Missing-data handling:** Missing any input, shares = 0, or equity ≤ 0 → no value (negative book value flag).
- **Industry limitations:** Book value understates asset-light / intangible-heavy companies and is distorted by revaluations, impairments, and buybacks. Banks are the classic P/B sector, but even there, asset quality (not book alone) drives value.
- **Validation:** Test shares-outstanding vintage (a stale share count with a new price must be flagged); test negative equity → no value.

### 4.3 Price-to-sales (P/S)

- **Definition:** `P/S = Market Price per Share / Revenue per Share`, or equivalently `Market Capitalisation / Revenue`. The form in use must be stated; both require the same revenue period.
- **Inputs:** `Price` (PKR/share) or `Market Cap` (PKR); `Revenue` (PKR, stated period); `Shares Outstanding` if using the per-share form.
- **Sources:** Price — as §4 header. Revenue / shares — UNVERIFIED fundamental feed.
- **Frequency:** As §4.1.
- **Missing-data handling:** Missing revenue, or revenue ≤ 0 → no value. Do not substitute gross profit or operating income for revenue.
- **Industry limitations:** Ignores profitability entirely — a company can have a low P/S while loss-making. Margin structure differs so much across sectors that cross-sector P/S ranking is misleading.
- **Validation:** Test per-share vs aggregate form give the same result on identical inputs; test missing revenue → no value.

### 4.4 Enterprise value / EBITDA (EV/EBITDA)

- **Definition:** `EV/EBITDA = Enterprise Value / EBITDA`, where `Enterprise Value = Market Capitalisation + Total Debt − (Cash + Cash Equivalents)` (plus preferred / minority interest if the verified source includes them — the EV definition in use must be stated).
- **Inputs:** `Market Cap` (PKR, dated price × shares); `Total Debt`, `Cash` (PKR, same statement date basis); `EBITDA` (PKR, stated period).
- **Sources:** Price leg — as §4 header. Debt / cash / EBITDA — UNVERIFIED fundamental feed.
- **Frequency:** On new price and on new verified statement; show both dates. A price from today combined with a year-old balance sheet must carry a vintage-mismatch warning.
- **Missing-data handling:** Missing any input, or EBITDA ≤ 0 → no value. Do not derive EBITDA from EBIT by adding back an assumed depreciation figure.
- **Industry limitations:** NOT meaningful for banks and financials (their debt is operating raw material, not financing — EV as defined here is misleading for banks; see §7). EBITDA ignores capex, working capital, and tax. Definition of EV varies by source.
- **Validation:** Test bank tickers are excluded or explicitly warned (see §7); test negative EBITDA → no value; test EV-definition label.

### 4.5 Price/earnings-to-growth (PEG)

- **Definition:** `PEG = P/E / EPS Growth Rate (%, annualised)`. EPS growth must be stated as TTM, annual, or CAGR, and the period must be shown.
- **Inputs:** `P/E` (as §4.1); `EPS Growth Rate` (percentage, stated period/method).
- **Sources:** As §4.1, plus growth derivation in §5 — all fundamental legs UNVERIFIED.
- **Frequency:** On new P/E or new verified growth rate.
- **Missing-data handling:** Missing P/E or growth, growth ≤ 0, or P/E missing (e.g. negative EPS) → no PEG. A PEG from a single exceptional growth year is not a stable signal and must carry its period label.
- **Industry limitations:** Extremely sensitive to the growth estimate; a one-year spike produces a misleadingly low PEG. PEG < 1 is NOT by itself an undervaluation signal. Forward-growth PEG requires a forecast EPS — forecasts are probabilistic (see `FORECASTING_SPECIFICATION.md`) and a forecast-based PEG must be labelled as forecast-based with its interval.
- **Validation:** Test growth ≤ 0 → no value; test forecast-based PEG carries forecast label and interval reference; test that trailing and forward PEG are never mixed under one label.

### 4.6 Dividend yield

- **Definition:** `Dividend Yield = Dividends per Share (trailing 12 months, or stated period) / Market Price per Share`.
- **Inputs:** `Dividends per Share` (PKR/share, stated period); `Price` (PKR/share, dated).
- **Sources:** Price — as §4 header. Dividends — UNVERIFIED fundamental / corporate-action feed. Dividend announcements, ex-dates, and payment history have NO verified machine feed in the starting condition — do not assume psx-dps or psxdata supplies them.
- **Frequency:** On new price and on each verified dividend event.
- **Missing-data handling:** Missing DPS or price → no value. A company that paid no dividend in the period has DPS = 0 only if that zero is confirmed from a verified source for that period — otherwise show "Not available", not 0%.
- **Industry limitations:** Trailing yield says nothing about future dividends; a very high yield often reflects a fallen price, not a sustainable payout. Special / one-off dividends distort trailing yield unless separately labelled.
- **Validation:** Test unconfirmed-zero vs confirmed-zero distinction; test special-dividend labelling rule.

### 4.7 Free cash flow yield

- **Definition:** `FCF Yield = Free Cash Flow per Share / Market Price per Share`, where `Free Cash Flow = Operating Cash Flow − Capital Expenditure` (definition in use must be stated).
- **Inputs:** `Operating Cash Flow`, `Capital Expenditure` (PKR, stated period); `Shares Outstanding`; `Price` (PKR/share, dated).
- **Sources:** Price — as §4 header. Cash-flow legs — UNVERIFIED fundamental feed.
- **Frequency:** As §4.1.
- **Missing-data handling:** Missing any leg → no value. Do not derive FCF from net income plus an assumed depreciation/capex figure.
- **Industry limitations:** FCF is lumpy (capex cycles); a single-period FCF yield is noisy. Banks' operating cash flow is not comparable to non-financials' — FCF yield for banks must be excluded or explicitly warned (see §7).
- **Validation:** Test lumpy-capex disclosure (period shown); test bank exclusion/warning; test missing capex → no value (not operating-cash-flow yield mislabelled as FCF yield).

---

## 5. Growth

All growth inputs are fundamental (UNVERIFIED feed, see §1 header). Growth rates require at least two comparable periods from the same source and definition.

### 5.1 Revenue growth (period-over-period)

- **Definition:** `Revenue Growth = (Revenue_t − Revenue_{t−1}) / Revenue_{t−1}`, for the same period length (e.g. year-on-year, quarter-on-quarter as labelled).
- **Inputs:** `Revenue` for two consecutive comparable periods (PKR).
- **Sources:** UNVERIFIED fundamental feed.
- **Frequency:** On each new verified statement.
- **Missing-data handling:** Missing either period, or prior-period revenue ≤ 0 → no value. Do not compare a quarterly figure with an annual figure, or restated with unrestated figures, without a break note.
- **Industry limitations:** Base effects (a depressed prior year inflates growth); acquisitions/divestitures create non-organic jumps that must be noted if known from a verified source, never assumed.
- **Validation:** Test period-length matching; test restatement break handling; test prior ≤ 0 → no value.

### 5.2 EPS growth

- **Definition:** `EPS Growth = (EPS_t − EPS_{t−1}) / EPS_{t−1}`, same period basis as §5.1.
- **Inputs:** `EPS` for two comparable periods (PKR/share).
- **Sources:** UNVERIFIED fundamental feed.
- **Frequency:** On each new verified statement.
- **Missing-data handling:** Missing either period, or prior EPS ≤ 0 → no value (growth from a loss base is not meaningful as a percentage).
- **Industry limitations:** As §5.1, plus share-count changes (buybacks/issues) move EPS independently of earnings. One-off earnings distort the base.
- **Validation:** As §5.1.

### 5.3 Revenue CAGR

- **Definition:** `Revenue CAGR = (Revenue_end / Revenue_start)^(1 / n) − 1`, where `n` = number of years between start and end (fractional years only if the method is stated).
- **Inputs:** `Revenue_start`, `Revenue_end` (PKR); `n` (years).
- **Sources:** UNVERIFIED fundamental feed.
- **Frequency:** On each new verified statement; recomputed for standard windows (e.g. 3y, 5y) only when both endpoints are verified.
- **Missing-data handling:** Missing either endpoint, start ≤ 0, or endpoints from different definitions → no value. Do not interpolate a missing endpoint year.
- **Industry limitations:** CAGR hides volatility and the path between endpoints; two companies with the same CAGR can have very different risk. Endpoint sensitivity (a depressed start year flatters CAGR) must be disclosed by showing start/end values and years alongside.
- **Validation:** Test endpoint-sensitivity disclosure; test missing endpoint → no value; test that CAGR is never computed across a definition change without a break.

### 5.4 Earnings CAGR

- **Definition:** `Earnings CAGR = (Earnings_end / Earnings_start)^(1 / n) − 1`, where earnings is net income (or EBIT if labelled as EBIT CAGR — never mix without a label).
- **Inputs:** As §5.3, for earnings.
- **Sources:** UNVERIFIED fundamental feed.
- **Frequency:** As §5.3.
- **Missing-data handling:** Missing endpoint, start ≤ 0 (including loss-making start) → no value.
- **Industry limitations:** As §5.3, amplified: earnings are more volatile than revenue, so earnings CAGR over short windows is especially misleading.
- **Validation:** As §5.3.

### 5.5 Dividend growth

- **Definition:** `Dividend Growth = (DPS_t − DPS_{t−1}) / DPS_{t−1}`, for comparable periods; multi-year dividend CAGR uses the §5.3 form on DPS.
- **Inputs:** `DPS` for two comparable periods (PKR/share).
- **Sources:** UNVERIFIED dividend / corporate-action feed (see §4.6).
- **Frequency:** On each verified dividend event / statement.
- **Missing-data handling:** Missing either period, prior DPS = 0 with no confirmed prior dividend policy (i.e. initiation vs missing data cannot be distinguished) → no value or a separately labelled "Dividend initiated" flag only if initiation is confirmed from a verified source. Never present initiation as infinite growth.
- **Industry limitations:** Dividend cuts, omissions, and special dividends break the series; payout policy changes are not growth. A maintained dividend is not growth.
- **Validation:** Test initiation vs missing-data distinction; test special-dividend exclusion labelling.

---

## 6. Technical indicators

Price/volume inputs come from market data. The verified-in-principle sources are psx-dps EOD (~5y) and psxdata daily OHLCV. Today's ticks exist via psx-dps but are NOT a historical intraday archive.

### 6.1 General technical rules (apply to all of §6)

- **Warm-up / minimum history:** No indicator is shown until its minimum lookback of verified closes is present (e.g. SMA-50 needs 50 closes). Partial-window values must not be shown as if they were full-window values; if a partial value is ever shown, it must be labelled `partial (n of N bars)`.
- **Adjusted vs unadjusted closes:** State whether closes are adjusted for splits/bonus/rights. If adjustment status is unknown from the source, state "adjustment status unverified" and do not compare across corporate-action dates silently. No verified adjustment feed is claimed in this specification.
- **Stale / missing bars:** A missing trading day is not filled with the prior close silently. Gaps are carried as gaps; indicators that require consecutive bars either skip the gap with a flag or show no value, per the per-indicator rule. Trading-vs-listed distinction (~496 trading vs ~1029 listed) means many listed symbols will have no recent bars — they get no technical values, not zero values.
- **Multi-node 404 quirk (psx-dps):** A fetch failure from one node is a data-availability flag, not a price of 0 and not evidence the symbol stopped trading. Retry / alternate-node logic belongs to the data layer, not to the formula layer.
- **Intraday limit (applies to §6.9 and any future intraday indicator):** Historical intraday bars are NOT available (psxdata: daily OHLCV + live snapshots ONLY; psx-dps: today's ticks only). Therefore no historical intraday indicator, intraday backtest, or intraday VWAP history may be presented. See §6.9 for the exact permitted scope.

### 6.2 Simple moving average (SMA)

- **Definition:** `SMA_N = (Close_{t} + Close_{t−1} + … + Close_{t−N+1}) / N`
- **Inputs:** `Close` prices (PKR), N bars. Standard windows are illustrative only (e.g. 20, 50, 200) — the window in use must be shown.
- **Sources:** psx-dps EOD / psxdata daily closes (verified-in-principle, subject to §6.1).
- **Frequency:** Daily, on each new verified EOD close.
- **Missing-data handling:** Fewer than N verified closes → no SMA (or labelled partial, per §6.1). A missing bar inside the window → no SMA unless the gap rule for that series is stated.
- **Industry limitations:** Lagging indicator; whipsaws in sideways markets; equal weighting gives stale bars the same weight as recent bars.
- **Validation:** Hand-computed test on a small series; test N-bar minimum; test gap handling.

### 6.3 Exponential moving average (EMA)

- **Definition:** `EMA_t = Price_t × k + EMA_{t−1} × (1 − k)`, where `k = 2 / (N + 1)`, seeded with the SMA of the first N closes (the seeding method must be stated, because seeding choices change early EMA values).
- **Inputs:** `Close` prices, N, seeding method.
- **Sources:** As §6.2.
- **Frequency:** Daily, on each new verified EOD close.
- **Missing-data handling:** Before the seed SMA exists → no EMA. A missing bar breaks the recursion — either no EMA until re-seeded with a stated rule, or a flagged carry-forward, never a silent fill.
- **Industry limitations:** Still lagging, though less than SMA; seeding differences make early-period EMAs non-comparable across implementations. Always state N and seeding.
- **Validation:** Test seed method; test recursion against a hand-computed series; test missing-bar break.

### 6.4 Relative strength index (RSI)

- **Definition (Wilder):** `RS = Average Gain over N periods / Average Loss over N periods`; `RSI = 100 − (100 / (1 + RS))`. Standard N = 14 (illustrative; the N in use must be shown). Wilder smoothing must be stated, as alternative smoothing gives different values.
- **Inputs:** `Close` prices, N = 14 unless otherwise stated.
- **Sources:** As §6.2.
- **Frequency:** Daily, on each new verified EOD close.
- **Missing-data handling:** Fewer than N+1 closes → no RSI. Average loss = 0 (all gains) → RSI = 100 by definition, shown with its window; average gain = 0 → RSI = 0. These edge cases are definitional, not missing data.
- **Industry limitations:** Overbought / oversold thresholds (commonly 70 / 30) are conventions, NOT verified PSX thresholds and NOT buy/sell triggers in this system. RSI diverges, stays overbought in strong trends, and is meaningless on thinly traded symbols with stale prices.
- **Validation:** Test all-gain / all-loss edges; test Wilder vs simple-average distinction is labelled; test minimum-history rule.

### 6.5 MACD

- **Definition:** `MACD Line = EMA_12 − EMA_26`; `Signal Line = EMA_9 of MACD Line`; `Histogram = MACD Line − Signal Line`. Windows 12/26/9 are the conventional illustration; the windows in use must be shown.
- **Inputs:** `Close` prices; EMA windows (fast, slow, signal).
- **Sources:** As §6.2.
- **Frequency:** Daily, on each new verified EOD close.
- **Missing-data handling:** No MACD until both EMAs exist (i.e. until the slow EMA is seeded); no signal until its EMA of MACD exists. Partial MACD must not be shown as full MACD.
- **Industry limitations:** Lagging trend-following indicator; crossovers whipsaw in sideways markets; histogram sign alone is not a recommendation. Requires the EMA seeding caveat from §6.3.
- **Validation:** Test against hand-computed EMA chain; test minimum-history rule for each leg.

### 6.6 Bollinger Bands

- **Definition:** `Middle Band = SMA_N`; `Upper Band = SMA_N + (k × Standard Deviation_N)`; `Lower Band = SMA_N − (k × Standard Deviation_N)`. Conventional N = 20, k = 2 (illustrative; both must be shown). Standard deviation is the population or sample form — state which, because they differ.
- **Inputs:** `Close` prices, N, k, standard-deviation form.
- **Sources:** As §6.2.
- **Frequency:** Daily, on each new verified EOD close.
- **Missing-data handling:** Fewer than N closes → no bands. Missing bar inside window → no bands (per §6.1) unless gap rule stated.
- **Industry limitations:** Bands widen/narrow with volatility; touching a band is NOT a reversal signal by itself. Assumes roughly normal distribution of returns, which equity returns violate (fat tails).
- **Validation:** Test standard-deviation form is labelled; test band-width computation; test minimum-history rule.

### 6.7 Average true range (ATR)

- **Definition:** `True Range_t = max(High_t − Low_t, |High_t − Close_{t−1}|, |Low_t − Close_{t−1}|)`; `ATR_N = Wilder-smoothed average of True Range over N periods` (conventional N = 14, illustrative; state N and smoothing).
- **Inputs:** `High`, `Low`, `Close` (PKR), N.
- **Sources:** psx-dps EOD / psxdata daily OHLCV (verified-in-principle, subject to §6.1). High/low availability depends on the source's daily bars — if a source supplies close only, ATR cannot be computed from it.
- **Frequency:** Daily, on each new verified EOD bar.
- **Missing-data handling:** Missing high, low, or prior close → no true range for that bar; fewer than N true ranges → no ATR. Do not substitute close-to-close range for true range without relabelling.
- **Industry limitations:** Volatility measure only, not direction; not comparable across price levels without normalisation (e.g. ATR as % of price, separately labelled). Thin trading produces artificially low ATR.
- **Validation:** Test true-range three-way maximum; test first-bar rule (no prior close → true range = high − low, stated); test smoothing label.

### 6.8 Average directional index (ADX)

- **Definition (Wilder):** From +DM / −DM and true range, compute smoothed +DI and −DI over N periods (conventional N = 14), then `DX = |+DI − −DI| / (+DI + −DI) × 100`, and `ADX = Wilder-smoothed average of DX over N periods`. Full Wilder steps must be implemented exactly and stated; summarised "ADX" without the DI legs is not acceptable as a specification.
- **Inputs:** `High`, `Low`, `Close`, N.
- **Sources:** As §6.7.
- **Frequency:** Daily, on each new verified EOD bar.
- **Missing-data handling:** Requires substantially more history than N bars before ADX stabilises (Wilder smoothing warm-up) — the system must not show early ADX values as stable trend-strength readings. Until the warm-up rule (to be fixed in implementation testing, e.g. a stated multiple of N) is met, show no ADX or a labelled `warming_up` value. Missing high/low → no update.
- **Industry limitations:** Lagging; thresholds (e.g. 25 for "trend") are conventions, NOT verified PSX thresholds and NOT recommendation triggers. ADX measures trend strength, not direction — direction comes from +DI / −DI, which must be shown alongside ADX if ADX is shown.
- **Validation:** Test DI legs are computed and retained; test warm-up rule; test that ADX alone is never presented as a directional signal.

### 6.9 On-balance volume (OBV)

- **Definition:** `OBV_t = OBV_{t−1} + Volume_t` if `Close_t > Close_{t−1}`; `OBV_t = OBV_{t−1} − Volume_t` if `Close_t < Close_{t−1}`; unchanged if closes are equal. Seed `OBV_0 = 0` at the start of the verified series (state the seed date — OBV levels are arbitrary and only changes/divergences are interpretable).
- **Inputs:** `Close`, `Volume` (shares), seed date.
- **Sources:** psx-dps EOD / psxdata daily OHLCV (volume availability per source; if a source lacks volume, OBV cannot be computed from it).
- **Frequency:** Daily, on each new verified EOD bar.
- **Missing-data handling:** Missing volume or close → no OBV update for that bar, with a gap flag. Do not carry forward a stale volume.
- **Industry limitations:** OBV level is meaningless without its seed date; only slope/divergence is read, and divergence is judgement, not a deterministic signal — the system must present OBV as a series, not as a buy/sell flag. Thin-volume symbols produce flat/noisy OBV.
- **Validation:** Test up/down/equal close rules; test seed-date label travels with the series.

### 6.10 Volume-weighted average price (VWAP) — LIMITED, intraday-data limit stated explicitly

- **Definition:** `VWAP = Σ (Typical Price × Volume) / Σ Volume` over the session, where `Typical Price = (High + Low + Close) / 3` for each intraday bar (or trade price if trade-level data is the verified source — the bar/trade basis must be stated).
- **Inputs:** Intraday bars or trades: price, volume, timestamp (PKT).
- **Sources — LIMIT:** Historical intraday bars are NOT available. psxdata supplies daily OHLCV + live snapshots ONLY (no historical intraday archive). psx-dps supplies today's ticks only. Therefore:
  - **Permitted:** A *current-session* VWAP computed live from today's ticks/snapshots while the session is in progress, labelled `VWAP (today, intraday, partial session)` with its start time and bar basis, and only if the tick/snapshot feed is verified at implementation time.
  - **NOT permitted:** Any historical intraday VWAP series, any VWAP backtest, any multi-day VWAP, any "VWAP over the last N days" computed from daily bars and mislabelled as VWAP (a daily-bar approximation, if ever shown, must be labelled `Daily-bar VWAP approximation — NOT intraday VWAP` and must not be used for backtesting or recommendation evidence).
  - **NOT permitted in Phase 1:** Any claim that VWAP history exists or will exist without a verified intraday archive vendor/feed.
- **Frequency:** Intraday only, for the current session; resets each session (state reset rule).
- **Missing-data handling:** Missing volume or price in a bar → that bar is excluded with a flag, or the session VWAP is flagged partial. A snapshot-only feed (no bar history within the session) cannot produce a VWAP — show no VWAP, not a snapshot-price mislabelled as VWAP.
- **Industry limitations:** VWAP is a session benchmark, not a valuation; comparing a price to VWAP intraday says nothing about fundamental value. Thin trading makes session VWAP unstable.
- **Validation:** Test session reset; test that a daily-bar input is rejected for true VWAP; test partial-session labelling; test that no historical VWAP series can be generated from the permitted sources (negative test: request a past-date VWAP → no value with `intraday_archive_unavailable` flag).

---

## 7. Sector-specific and industry limitations (cross-cutting)

| Sector / case | What breaks | Required handling |
|---|---|---|
| Banks & financials | Gross margin, ROIC (non-financial definition), EV/EBITDA, FCF yield, current/quick ratio as defined for manufacturers | Exclude or explicitly warn; use sector-appropriate measures only when a future verified specification defines them. Never rank banks against manufacturers on these ratios. |
| Insurance | Revenue, leverage, and margin definitions differ (premiums, claims, reserves) | Same as banks: exclude/warn until a sector-specific specification is verified. |
| Asset-light / intangible-heavy | P/B understates value; ROA overstates vs asset-heavy peers | Show alongside a warning; do not rank on P/B alone. |
| Cyclicals (cement, steel, commodities) | P/E, margins, growth at cycle peaks/troughs mislead | Show multi-year context (when verified data permits) and cycle note; never annualise a peak/trough quarter silently. |
| Loss-making / negative-equity companies | P/E, PEG, ROE, P/B undefined or misleading | No value + `non_meaningful` flag, per per-formula rules. Never a negative P/E as a signal. |
| Thinly traded / suspended / delisted (within ~1029 listed vs ~496 trading) | Stale prices, zero volume, missing bars | No technical or valuation values from stale prices without a staleness warning; suspended symbols show status, not a computed view. |
| Islamic-finance instruments | "Interest" labels (coverage, debt) may not map cleanly | No silent mapping of profit/rental charges to interest; mapping rule must be stated or the ratio withheld. |

Sector classification itself: the 38 sectors come from psx-dps sector lists (verified-in-principle). Sector membership changes over time — every sector aggregate must carry its membership date and member count. No sector benchmark, index level, or sector average is invented in this specification; sector aggregates are defined in `ANALYTICS_SPECIFICATION.md` and require verified constituents before they are shown.

## 8. What is EXCLUDED or LIMITED because data does not permit it

1. **All fundamental ratios (§1–§5, valuation legs in §4)** — LIMITED to "Not available" until a fundamental machine feed is verified. No hand-copied filing value is authorised by this specification.
2. **Historical intraday VWAP and any intraday backtest** — EXCLUDED (see §6.10). No historical intraday archive exists in the verified sources.
3. **Historical intraday-dependent indicators generally** (e.g. intraday RSI/MACD history, intraday ATR history) — EXCLUDED for history; current-session only where the live feed permits, with the same labelling as §6.10.
4. **Adjusted-close indicators across corporate actions** — LIMITED: adjustment status unverified; do not silently compare across splits/bonus/rights dates until an adjustment feed is verified.
5. **Macro-conditioned ratios** (e.g. inflation-adjusted returns, real yields) — EXCLUDED until a macro feed (SBP / PBS / Finance Division / World Bank / IMF / FRED) is verified for machine use. All such feeds are currently UNVERIFIED.
6. **Analyst-estimate-based ratios** (forward P/E on consensus EPS, target-price-based upside) — EXCLUDED: no verified analyst-estimate feed exists in the starting condition, and no estimate is invented.
7. **Any ratio requiring short interest, options, or derivatives data** — EXCLUDED: no verified PSX source for these is in the starting condition.

## 9. Validation summary (applies to every formula)

- Deterministic unit tests with hand-computed cases, including: missing input → no value; zero denominator → no value; negative-base cases → no value or correctly signed value per the per-formula rule; date/period mismatch → no combined value.
- Provenance test: every output carries source, PKT as-of, vintage, and stale/conflict flags.
- Label test: every output that uses a non-default definition, partial window, annualisation, approximation, or forecast input carries that label in the UI, not only in documentation.
- Regression rule: a change in a source definition or window must change the label or break the series with a note — never a silent splice.
- No LLM is in the validation path for numbers. An LLM may explain a deterministic result in words; it may not produce, adjust, or round the number (see `FINANCIAL_GOVERNANCE.md`).

---

*End of FINANCIAL_FORMULAS.md — Phase 1 specification only. No prices, forecasts, or recommendations are contained in this document.*
