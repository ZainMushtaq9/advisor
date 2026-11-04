# PSX Intelligence AI — Valuation Specification

**Phase:** 1 of 30 — Specification only. No application code. STOP AFTER PHASE 1.
**Team:** Team 7 (Financial Analytics + Security + Governance)
**Companion documents:** `FINANCIAL_FORMULAS.md`, `ANALYTICS_SPECIFICATION.md`, `FORECASTING_SPECIFICATION.md`, `SECURITY_REQUIREMENTS.md`, `FINANCIAL_GOVERNANCE.md` — all in this same `docs/phase-01/` folder.
**Date / starting condition:** Verified 2026-11-04, reused verbatim — see §1.

## 1. Starting condition (reuse verbatim)

- Project folder `~/workspace/psx-intelligence-ai/` is new. Other teams may be creating sibling files; this team writes only its assigned files and never overwrites/touches sibling teams' files or the separate scaffold `~/workspace/psx-data-collection/` (stdlib collector with provenance / PKT / stale / conflict rules), which is REFERENCED only.
- Tools: Python 3.12.3, Node v24.22.1. Docker, psql, redis-cli NOT installed.
- Already verified (reuse): psx-dps (~496 trading vs ~1029 listed, ~5y EOD, today's ticks, 38 sectors, multi-node 404 quirk, no official PSX API); psxdata (daily OHLCV + live snapshots ONLY, no historical intraday archive — so VWAP / intraday-dependent metrics are limited to what data permits, and historical intraday backtests must not be assumed); Eulerpool: NO PSX coverage, vendor only, no paid API approved.
- SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use is UNVERIFIED — formulas depending on macro / fundamental feeds must state the feed as UNVERIFIED and define missing-data handling (skip / flag, never estimate silently).

## 2. Revised brief — merged

- **Budget: PKR 0 absolute zero-cost.** Valuation must use local open-source libraries only — Pandas / NumPy / scikit-learn / statsmodels / PyTorch where justified — and Ollama local inference only for interpretation (never for numbers). No paid AI APIs, no paid subscriptions, no paid data vendor (including no paid valuation-data vendor) is approved or assumed. Local hardware, electricity, and internet are EXTERNAL operating expenses: disclose them as such, never call them "free".
- **Phase 1 workflow (11 stages):** (1) brainstorm, (2) research, (3) validate, (4) data inspection — read-only only, NO full-scale live data collection in Phase 1, (5) architecture planning, (6) implementation specification, (7) documentation, (8) testing strategy — defined, not claimed passed, (9) independent audit, (10) correction, (11) checkpoint. This document is stages 6–7. It specifies methods and required disclosures; it contains no valuation, no intrinsic value, and no price target.
- **No real trading initially.** The system must NOT execute real trades initially. A valuation is informational only and must never be wired to an order, broker, or execution path in Phase 1 (see `SECURITY_REQUIREMENTS.md` §9 and `FINANCIAL_GOVERNANCE.md` §8). A valuation is not a trade instruction, even when it differs from the market price.
- **Critical rules preserved:** Financial calculations are deterministic Python functions ONLY; LLMs must NEVER invent numerical valuation results; valuations are probabilistic/assumption-dependent estimates with uncertainty shown, never guaranteed intrinsic values; BUY / HOLD / SELL / WATCHLIST are probabilistic recommendations with uncertainty shown, not advice guarantees; no unauthorised trading; no fabricated data; no unsupported forecasts; no unverified recommendations; no concealed uncertainty; no unauthorised commercial redistribution.

## 3. What valuation is — and why no single method yields a guaranteed intrinsic value

Valuation estimates what a company *might* be worth under stated assumptions. It does not discover a hidden true price. The market price is an observed fact (when verified); intrinsic value is a model output that changes when its assumptions change. That is why this specification requires:

1. **Multiple methods, shown together.** No valuation view may present a single method's output as "the intrinsic value". Where multiple methods are available, all available methods are shown with their ranges, so disagreement is visible.
2. **Assumptions shown, not hidden.** Every valuation must display its key inputs and assumptions alongside its output (§4). A valuation without its assumptions is not a valid output.
3. **Ranges, not points, as the default.** Each method produces a range (from sensitivity/scenario analysis, §5) as its primary output; a point estimate, if shown, is shown inside its range, never alone.
4. **No guaranteed intrinsic value.** Language such as "true value", "fair value" (as a fact rather than a model label), "undervalued — buy now", or "will reach X" is prohibited. The permitted language is model-labelled and conditional: "DCF estimate (base assumptions): range X–Y PKR/share; market price on [date]: Z PKR/share" — with the DRAFT disclaimer (`FINANCIAL_GOVERNANCE.md` §7).

**Phase 1 availability warning (binding).** Every valuation method in §6 requires fundamental inputs (cash flows, dividends, earnings, book values) and/or market inputs (price, shares outstanding, peer multiples). Fundamental inputs are UNVERIFIED in Phase 1 (see §1). Therefore **no valuation may be computed or shown in Phase 1**. This document specifies how valuations WILL work when inputs are verified; it does not authorise a single valuation number today. Any valuation-like number produced in Phase 1 conditions (e.g. from hand-copied statements or LLM recall) is non-compliant.

### 3.1 Tiny illustrative structure (not application code, not real values)

```python
# Shape only — no valuation is contained in this document.
valuation_view = {
    "symbol": "...", "market_price_pkt_date": "...",
    "methods": {
        "dcf": {"status": "unavailable", "reason": "fundamental_feed_unverified"},
        "ddm": {"status": "unavailable", "reason": "fundamental_feed_unverified"},
        "comparables": {"status": "unavailable", "reason": "fundamental_feed_unverified"},
        "historical_multiples": {"status": "unavailable", "reason": "fundamental_feed_unverified"},
        "asset_based": {"status": "unavailable", "reason": "fundamental_feed_unverified"},
    },
    "disclaimer": "DRAFT — see FINANCIAL_GOVERNANCE.md section 7.",
}
```

## 4. Inputs and assumptions that MUST be shown to the user

For every valuation method that is ever shown, the display must include — in the same view, not behind a secondary click that hides them by default:

| Item | Must be shown | Why it matters |
|---|---|---|
| Market price + date (PKT) | Verified price, source, EOD date | The comparison point; a stale price invalidates the comparison |
| Shares outstanding + date | Count and vintage | Per-share values depend entirely on this; a stale count with a new price misleads |
| Input financials + period | Each input value, its statement period, source, and vintage | A valuation on year-old statements is not current |
| Forecast inputs (where used) | Each forecast input, its method, horizon, and interval (per `FORECASTING_SPECIFICATION.md`) | Forecast-based valuations inherit forecast uncertainty — hiding it conceals uncertainty |
| Discount rate + derivation | Rate value AND how it was derived (components, sources) | The single most sensitive DCF input; an unexplained rate is not auditable |
| Growth / terminal assumptions | Growth rates, terminal value method, terminal multiple if used, and their justification | Terminal value often dominates DCF — hiding it hides the valuation |
| Peer set (where used) | Every peer, its sector, and why it was included/excluded | Cherry-picked peers manufacture any multiple |
| Method version | Method definition version, so a later definition change breaks comparability explicitly | Prevents silent splicing across definition changes |
| Sensitivity range | At minimum the range under stated low/base/high assumption sets (§5) | A point without a range conceals assumption risk |
| Limitations | Method-specific limits from §6, in plain language | Prevents over-reliance on one method |
| Disclaimer | DRAFT disclaimer (`FINANCIAL_GOVERNANCE.md` §7) | Legal/governance protection; not legal advice (labelled as such) |

**Assumption-change rule.** If any shown assumption changes, the valuation must be recomputed and re-versioned, with the prior version retained in history (see §8). Editing an assumption in place and overwriting the prior valuation is prohibited — it destroys the audit trail.

## 5. Sensitivity and scenario handling (mandatory for every method)

1. **Base / low / high sets.** Every valuation is computed under at least three assumption sets: base (central stated assumptions), low (pessimistic on the key drivers), and high (optimistic). The sets are defined BEFORE computation, with each changed assumption listed. The output range is [low-set value, high-set value] with the base value inside it — if the base falls outside the low–high range, the sets are incoherent and the valuation is defective, not shown.
2. **One-way sensitivities (where the method supports them).** For DCF/DDM, show how the value moves when each key driver (discount rate, growth, margin, capex) moves by a stated step, one at a time, holding others at base. This reveals which assumption the valuation actually depends on.
3. **Scenario handling.** Scenarios (see `FORECASTING_SPECIFICATION.md` §4.5) may be applied to valuation inputs, but only as labelled, unweighted scenarios unless probabilities are assigned by a recorded rule. A scenario valuation is labelled with its scenario; scenarios are never averaged into a single "expected value" without a recorded probability rule.
4. **No narrowing for presentation.** Sensitivity ranges must not be narrowed, trimmed, or "cleaned up" to look more precise. A wide range is honest information about assumption risk; presenting a narrow range from wide assumptions is concealed uncertainty.
5. **Break-even disclosure.** Where informative, show the assumption value at which the valuation equals the current market price (e.g. "DCF equals today's price if perpetual growth is X% instead of base Y%"). This lets the user judge plausibility without the system asserting over/undervaluation as fact.

## 6. Valuation methods

### 6.1 Discounted cash flow (DCF)

- **Definition:** `Enterprise Value = Σ [FCF_t / (1 + WACC)^t] + Terminal Value / (1 + WACC)^n`, over an explicit forecast horizon n; `Equity Value = Enterprise Value − Net Debt` (plus/minus other stated adjustments); `Value per Share = Equity Value / Shares Outstanding`. FCF definition, WACC derivation, horizon n, and terminal-value method must all be stated.
- **Inputs:** Forecast free cash flows (period by period, with method per `FORECASTING_SPECIFICATION.md` — forecast inputs carry intervals, and DCF must propagate or at least display that uncertainty, not collapse a forecast interval to its point); WACC (with cost-of-equity, cost-of-debt, weights, and their sources — each component UNVERIFIED until a verified source exists; risk-free rate and market-risk-premium sources are UNVERIFIED in Phase 1, including any SBP/market source); terminal growth rate and/or terminal multiple; net debt; shares outstanding.
- **Assumptions that must be shown:** Every input above, plus the forecast horizon, the reason the horizon was chosen, and why the terminal assumption is plausible (or, if it is not demonstrably plausible, that it is an assumption, not evidence).
- **Sensitivity:** §5 applies with emphasis on WACC (± stated steps) and terminal growth — these two typically dominate DCF and must always appear in the sensitivity table.
- **Industry limitations:** Highly sensitive to WACC and terminal value (terminal value commonly exceeds 50% of DCF value — if it does, that fact must be stated, because the valuation then rests mostly on the terminal assumption, not the forecast years). Unreliable for loss-making, highly cyclical, or early-stage companies where FCF forecasts are speculative. For banks, FCF as defined for non-financials is NOT applicable (see §7) — a bank DCF on non-financial FCF is prohibited.
- **Validation:** Arithmetic tests (discounting, terminal value, net-debt bridge, per-share division); sensitivity coherence (§5.1: base inside low–high); terminal-share disclosure test (terminal value as % of enterprise value shown).

### 6.2 Dividend discount model (DDM)

- **Definition (Gordon form, the baseline illustration):** `Value per Share = DPS_1 / (k − g)`, where `DPS_1` is next-period dividends per share, `k` is cost of equity, `g` is perpetual dividend growth — valid ONLY when k > g and dividends are a meaningful, stable payout. Multi-stage DDM (explicit high-growth stage + terminal stage) must state each stage's length, growth, and payout. The form in use must be stated; Gordon and multi-stage outputs are never mixed under one label.
- **Inputs:** DPS history and forecast (UNVERIFIED dividend feed in Phase 1); cost of equity k (derivation as §6.1); growth g (with justification — historical dividend growth is not a promise of future growth); payout assumptions for multi-stage forms.
- **Assumptions that must be shown:** k, g, stage structure, DPS forecast method, and the k > g condition check. If k ≤ g, the Gordon form is undefined — show no value, not an infinite/negative value.
- **Sensitivity:** §5 on k and g (the model is extremely sensitive when k − g is small — a 1-point change in either can move value by multiples; this sensitivity must be shown, not hidden).
- **Industry limitations:** Applicable ONLY to stable dividend payers. Non-payers, irregular payers, cutters, and companies retaining earnings for growth cannot be valued by DDM — show no DDM value with reason `no_stable_dividend_history`, never a zero or forced value. Banks with regulated dividends need a payout-constraint note if DDM is ever applied to them.
- **Validation:** k > g gate test; stage-boundary test (multi-stage values reconcile to stage cash flows); sensitivity table presence test.

### 6.3 Comparable companies ("comps" / trading multiples)

- **Definition:** Value the company by applying peer-group multiples to its own metrics, e.g. `Implied Price = Peer Median P/E × Company EPS` (and analogously for P/B, P/S, EV/EBITDA where applicable). The multiple, the peer statistic (median vs mean — median is the default, stated), and the company metric must all be stated. Using the mean without disclosing outlier influence is prohibited.
- **Inputs:** Peer set (§4: every peer listed with inclusion/exclusion reasons); peer multiples (each computed per `FINANCIAL_FORMULAS.md` §4, with price dates and fundamental vintages); company metric (EPS/book/revenue/EBITDA — UNVERIFIED in Phase 1).
- **Assumptions that must be shown:** Peer selection criteria (sector, size band, listing status — fixed before seeing multiples, not chosen to produce a desired median); multiple date (all peer prices on the same EOD date, or the date-mismatch flagged); treatment of loss-making peers (excluded from P/E medians by rule, with count of exclusions shown — including them as negative P/Es corrupts the median).
- **Sensitivity:** §5 via peer-statistic range (e.g. interquartile range of peer multiples applied to the company metric, shown alongside the median-implied value). A single median-implied point without the peer spread conceals peer dispersion.
- **Industry limitations:** Multiples reflect market sentiment, not intrinsic worth — comps answer "what does the market pay for similar companies?", not "what is this company worth?". Cross-sector peers invalidate the comparison. Small peer sets (e.g. < 5 verified peers) produce unstable medians — below a fixed minimum peer count (fixed at implementation), no comps value is shown. Banks must be compared only to banks, on bank-appropriate multiples (P/B, P/E), never EV/EBITDA (see §7).
- **Validation:** Peer-set reproducibility test (same criteria → same peers); same-date test; loss-peer exclusion test; minimum-peer-count gate test.

### 6.4 Historical multiples (own-history multiples)

- **Definition:** Compare the company's CURRENT multiple (e.g. P/E today) with its OWN historical multiple distribution (e.g. median, quartiles over a stated window such as 3y/5y, where data permits). This is a relative-position description ("current P/E is at the Xth percentile of its own 5y history"), NOT a valuation that outputs an intrinsic price — unless a historical multiple is explicitly applied to a current metric to imply a price, in which case that implied price must be labelled `Implied price at historical-median multiple (descriptive, not intrinsic value)` with the window and percentile stated.
- **Inputs:** Historical prices (psx-dps EOD, ~5y max) and historical fundamental metrics (UNVERIFIED in Phase 1 — so historical multiples requiring fundamentals are unavailable in Phase 1; a price-only history alone cannot produce a P/E history).
- **Assumptions that must be shown:** Window, multiple definition, percentile statistic, and the fact that history length is capped at ~5y (so "5y median" may in practice be shorter for recently listed symbols — the actual bar count must be shown).
- **Sensitivity:** Show the full historical distribution (quartiles), not just the median. A current multiple at an extreme percentile must carry a regime note (the historical window may span a different earnings/rate regime — the multiple's history is not a target it must revert to).
- **Industry limitations:** Mean reversion of multiples is NOT guaranteed; structural change (business mix, leverage, sector re-rating) breaks historical comparability. A multiple can stay "cheap" or "expensive" versus history for years for valid reasons. Presenting historical-percentile position as a buy/sell signal is prohibited.
- **Validation:** Window/bar-count test; same-definition-across-history test (a definition change breaks the series with a note); percentile-computation test.

### 6.5 Asset-based valuation

- **Definition:** `Equity Value = Total Assets (at stated valuation basis) − Total Liabilities`; `Value per Share = Equity Value / Shares Outstanding`. The valuation basis MUST be stated: book values (as reported), adjusted book values (with stated adjustments per asset class), or liquidation values (with stated haircuts per asset class and wind-down costs). Book, adjusted, and liquidation outputs are three different valuations and must never share a label.
- **Inputs:** Asset and liability values by class (UNVERIFIED fundamental feed in Phase 1); adjustment/haircut schedules with justifications; shares outstanding.
- **Assumptions that must be shown:** Basis, every adjustment/haircut with its reason, treatment of intangibles (included at book? written to zero? — stated, never assumed), and treatment of contingent liabilities if known from a verified source (unknown contingencies are a stated limitation, not zero).
- **Sensitivity:** §5 via adjustment ranges (e.g. property/plant at book vs at a stated haircut). Liquidation values must show wind-down costs as a separate line, not netted invisibly.
- **Industry limitations:** Book values rarely equal market values (especially for intangibles, specialised plant, and property carried at historical cost). Asset-based value is a floor/liquidation reference, not a going-concern value — presenting it as going-concern intrinsic value is prohibited. For banks, asset-based value interacts with loan-book quality (provisions, non-performing loans) — a book-asset value without an asset-quality note is misleading.
- **Validation:** Balance-sheet identity test (assets − liabilities reconciles to equity on the stated basis); adjustment-trail test (every adjustment listed and summed); intangibles-treatment label test.

## 7. Industry limitations — banks vs non-financials (binding)

| Method | Banks / financials | Non-financials |
|---|---|---|
| DCF (FCF-based) | PROHIBITED on non-financial FCF definition. A bank-specific DCF (e.g. dividend/free-cash-flow-to-equity form) requires its own future specification — not authorised by this document. | Permitted when inputs verified, per §6.1. |
| DDM | Permitted in principle for stable dividend-paying banks, with payout/regulatory note (§6.2). | Permitted for stable payers only (§6.2). |
| Comps | Banks vs banks only; P/B and P/E only; EV/EBITDA prohibited for banks. | Sector-matched peers; EV/EBITDA permitted where applicable (§6.3). |
| Historical multiples | P/B and P/E history where data permits; EV/EBITDA history prohibited. | Per §6.4. |
| Asset-based | Book-asset value requires asset-quality (loan-book) note; liquidation basis needs regulatory wind-down assumptions stated. | Per §6.5. |

**General rule:** A valuation method applied to a sector where it is not applicable must be withheld with its reason, not computed with a warning as a fig leaf. Warnings accompany applicable methods; they do not rescue inapplicable ones.

## 8. Valuation history, audit, and comparability

- **Immutable history.** Every valuation ever shown is stored with its method version, inputs, assumptions, sensitivity sets, market price + date, and exact output shown. Prior versions are never overwritten (see `FORECASTING_SPECIFICATION.md` §8.1 for the parallel forecast rule and `FINANCIAL_GOVERNANCE.md` §6 for audit).
- **Version breaks.** A change in method definition, input definition, or peer criteria creates a new version; valuation history charts must show the break, not splice across it.
- **Actual-vs-valued evaluation (descriptive only).** Comparing past valuations with later market prices is a descriptive accuracy record (with sample size and horizon stated). It is NOT evidence that valuations predict prices, and a past valuation that "was right" does not validate the method — that claim would require the backtesting discipline of `FORECASTING_SPECIFICATION.md` §7, which is not satisfied by anecdote.
- **Independent Audit agent.** Valuations are subject to audit by the Independent Audit agent (`FINANCIAL_GOVERNANCE.md` §6). An unauditable valuation (missing assumptions, missing inputs, missing version) cannot be shown.

## 9. What a valuation view must NEVER contain

- A single "intrinsic value" or "fair value" presented as fact.
- A price target ("will reach X by [date]") — that is a forecast + valuation hybrid requiring both specifications' governance, and it is not authorised as a valuation output in Phase 1.
- A valuation without its assumptions, sensitivity range, method version, and disclaimer in the same view.
- A valuation for a company whose inputs fail the data-quality gates (`ANALYTICS_SPECIFICATION.md` §5) — stale price, conflicting sources, unverified fundamentals, or inapplicable method → withheld with reason.
- Any valuation number in Phase 1 (see §3: all inputs UNVERIFIED → all methods unavailable).

## 10. Testing strategy — defined, not claimed passed

Phase 1 defines the tests; it does not claim any test has passed (11-stage workflow, stage 8):

1. **Arithmetic tests:** Discounting, terminal value, net-debt bridge, per-share division, peer-median computation, percentile computation — hand-computed cases.
2. **Gate tests:** Unverified inputs → withheld; stale price → warning/withheld; inapplicable method (bank EV/EBITDA, non-payer DDM, k ≤ g) → withheld with reason.
3. **Sensitivity tests:** Base inside low–high; sensitivity tables present and coherent; terminal-share disclosure present for DCF.
4. **Assumption-display tests:** Every required §4 item present in the same view; missing item → view invalid.
5. **Version/history tests:** Assumption change creates a new version; prior version retained; history break shown, not spliced.
6. **Negative tests:** Request any valuation in Phase 1 conditions → correctly withheld with `fundamental_feed_unverified` (expected passing behaviour in Phase 1).
7. **LLM-exclusion tests:** Valuation path contains no LLM call; LLM interpretation cannot write valuation numbers.

No test result is reported in this specification, because no implementation exists yet in Phase 1.

---

*End of VALUATION_SPECIFICATION.md — Phase 1 specification only. No valuation, intrinsic value, price target, or recommendation is contained in this document.*
