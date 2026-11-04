# PSX Intelligence AI — Forecasting Specification

**Phase:** 1 of 30 — Specification only. No application code. STOP AFTER PHASE 1.
**Team:** Team 7 (Financial Analytics + Security + Governance)
**Companion documents:** `FINANCIAL_FORMULAS.md`, `ANALYTICS_SPECIFICATION.md`, `VALUATION_SPECIFICATION.md`, `SECURITY_REQUIREMENTS.md`, `FINANCIAL_GOVERNANCE.md` — all in this same `docs/phase-01/` folder.
**Date / starting condition:** Verified 2026-11-04, reused verbatim — see §1.

## 1. Starting condition (reuse verbatim)

- Project folder `~/workspace/psx-intelligence-ai/` is new. Other teams may be creating sibling files; this team writes only its assigned files and never overwrites/touches sibling teams' files or the separate scaffold `~/workspace/psx-data-collection/` (stdlib collector with provenance / PKT / stale / conflict rules), which is REFERENCED only.
- Tools: Python 3.12.3, Node v24.22.1. Docker, psql, redis-cli NOT installed.
- Already verified (reuse): psx-dps (~496 trading vs ~1029 listed, ~5y EOD, today's ticks, 38 sectors, multi-node 404 quirk, no official PSX API); psxdata (daily OHLCV + live snapshots ONLY, no historical intraday archive — so VWAP / intraday-dependent metrics are limited to what data permits, and historical intraday backtests must not be assumed); Eulerpool: NO PSX coverage, vendor only, no paid API approved.
- SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use is UNVERIFIED — formulas depending on macro / fundamental feeds must state the feed as UNVERIFIED and define missing-data handling (skip / flag, never estimate silently).

## 2. Revised brief — merged

- **Budget: PKR 0 absolute zero-cost.** Forecasting must use local open-source libraries only — Pandas / NumPy / scikit-learn / statsmodels / PyTorch where justified — and Ollama local inference only. No paid AI APIs, no paid subscriptions, no paid data vendor is approved or assumed. Local hardware, electricity, and internet are EXTERNAL operating expenses: disclose them as such, never call them "free". PKR 0 means zero project spend on software/APIs/subscriptions/vendors, not zero operating cost.
- **Phase 1 workflow (11 stages):** (1) brainstorm, (2) research, (3) validate, (4) data inspection — read-only only, NO full-scale live data collection in Phase 1, (5) architecture planning, (6) implementation specification, (7) documentation, (8) testing strategy — defined, not claimed passed, (9) independent audit, (10) correction, (11) checkpoint. This document is stages 6–7. It defines methodologies and validation; it contains no forecast, no fitted model, and no backtest result.
- **No real trading initially.** The system must NOT execute real trades initially. Forecasts are informational only and must never be wired to an order, broker, or execution path in Phase 1 (see `SECURITY_REQUIREMENTS.md` §9 and `FINANCIAL_GOVERNANCE.md` §8).
- **Critical rules preserved:** Financial calculations are deterministic Python functions ONLY; LLMs must NEVER invent numerical forecast results; forecasts are probabilistic and evidence-based, never guaranteed; BUY / HOLD / SELL / WATCHLIST are probabilistic recommendations with uncertainty shown, not advice guarantees; no unauthorised trading; no fabricated data; no unsupported forecasts; no unverified recommendations; no concealed uncertainty; no unauthorised commercial redistribution.

## 3. What forecasting is — and is not — in this system

- **Is:** A probabilistic estimate of a future quantity (e.g. a price level, a return, or a direction probability) over a stated horizon, produced by a deterministic statistical procedure from verified historical data, presented as a distribution / interval with its evidence, assumptions, and limits.
- **Is not:** A prediction of what WILL happen, a price target, a guarantee, a recommendation by itself, or a substitute for the company view (`ANALYTICS_SPECIFICATION.md`). A forecast never, on its own, justifies a BUY / HOLD / SELL output — recommendations require the governed evidence trail in `FINANCIAL_GOVERNANCE.md` §5.
- **Scope in Phase 1:** Daily (EOD) price/return forecasting only, because that is what the verified data permits (~5y EOD from psx-dps; daily OHLCV from psxdata). Intraday forecasting history, fundamental forecasting (revenue/EPS forecasts), and macro forecasting are excluded or limited per §9 — they require feeds that are UNVERIFIED or archives that do not exist.

### 3.1 The one-sentence rule for every forecast

> Every forecast shown to a user must be traceable to a named method, a named fitted model version, verified training data with dates, a stated horizon, and a quantified uncertainty — or it must not be shown.

## 4. Forecasting methodologies

All methods below are implemented, when implemented, with local open-source libraries only (Pandas / NumPy / scikit-learn / statsmodels / PyTorch where justified). No method requires a paid API. Library choice per method is a justified engineering decision at implementation time, recorded with the model version — it is not a claim made in Phase 1.

Each method entry follows: what it is, what it assumes, what data it needs, what it cannot do, and how it is validated. No method is "best" in general; method selection per symbol/horizon must follow §4.6, not preference or novelty.

### 4.1 Regression (including regularised and time-series regression)

- **What:** Models a target (e.g. future return or price change) as a function of past features (lags, moving averages, volume, calendar features) with fitted coefficients. Includes ordinary least squares, Ridge/Lasso/Elastic Net, and autoregressive distributed-lag forms. Implemented with scikit-learn / statsmodels.
- **Assumptions that must be stated:** Linearity (or the stated non-linear form), stationarity of the target (or the transformation applied, e.g. log returns), no look-ahead (features use only data available at forecast origin), and stable relationships over the training window.
- **Data needs:** Verified EOD closes (and volumes where used), with a stated training window and a hold-out period. Minimum history fixed at implementation (e.g. a stated multiple of the feature count) — below it, no forecast.
- **Cannot do:** Capture regime changes, volatility clustering, or non-linear breaks without explicit features for them; extrapolate beyond the training range credibly; use future information (including future corporate actions) without labelling the forecast as conditional.
- **Validation:** Out-of-sample evaluation per §7 (walk-forward, not in-sample fit). Coefficient stability across windows must be reported; a model whose coefficients flip sign across windows is flagged unstable, not averaged away.

### 4.2 ARIMA / SARIMA (and seasonal variants where justified)

- **What:** Autoregressive Integrated Moving Average models of a (differenced, stationary) price or return series; seasonal variants only where a verified seasonal pattern is demonstrated, not assumed. Implemented with statsmodels.
- **Assumptions that must be stated:** Stationarity after the stated differencing order; order (p, d, q) selected by a recorded criterion (e.g. AIC/BIC on training data) and frozen per model version; residuals approximately white noise (tested, not assumed).
- **Data needs:** A single verified EOD series with enough history for the chosen order (minimum length fixed at implementation). Gaps (missing trading days, suspensions) must be handled by the stated gap rule — never silently filled with prior closes.
- **Cannot do:** Model volatility clustering (that is GARCH's role, §4.3); handle structural breaks, jumps, or thin-trading artefacts; produce credible long-horizon point forecasts — intervals widen with horizon and must be shown widening (§6).
- **Validation:** Residual diagnostics (autocorrelation tests) on training data; out-of-sample interval coverage per §7. A model failing residual diagnostics must not be promoted to user-facing forecasts.

### 4.3 GARCH (volatility modelling)

- **What:** Generalised Autoregressive Conditional Heteroskedasticity models of return volatility (e.g. GARCH(1,1) as the baseline illustration; other orders/variants only with justification). GARCH forecasts VOLATILITY, not price direction. Implemented with a local open-source library justified at implementation (e.g. an open-source GARCH implementation — the library name must be recorded; no paid library is approved).
- **Assumptions that must be stated:** Volatility clustering exists in the series (tested, not assumed); the stated distributional assumption for innovations (e.g. normal vs Student-t) and why; stationarity conditions for the chosen order.
- **Data needs:** Verified EOD returns with enough history for volatility estimation (minimum length fixed at implementation; short series produce unstable volatility estimates and must be withheld).
- **Cannot do:** Predict price direction or level by itself. A GARCH output shown alongside a price forecast supplies the uncertainty band — it must never be presented as a directional forecast. GARCH on thinly traded symbols with many zero-return days is unreliable and must be flagged or withheld.
- **Validation:** Out-of-sample volatility forecast evaluation (e.g. realised-volatility comparison where realised volatility can be computed from verified data) and interval-coverage contribution per §7. In-sample volatility fit alone is not validation.

### 4.4 Statistical ensembles

- **What:** A combination of two or more of the above (and/or other justified statistical) methods, combined by a FIXED, recorded rule (e.g. simple average of point forecasts, median, or inverse-error weighting computed on a validation window and then frozen). Ensembles are a combination rule, not a new method that escapes validation.
- **Assumptions that must be stated:** The member methods, the combination rule, the weights (and how they were computed), and the validation window used to set the weights. Weights computed on the same data used to evaluate the ensemble are in-sample and must be labelled as such — they are not evidence of skill.
- **Data needs:** Each member's data needs (§§4.1–4.3), plus a separate validation window for weight-setting that does not overlap the evaluation window.
- **Cannot do:** Fix fundamentally bad members by averaging — if members disagree wildly, the ensemble interval must widen to reflect disagreement (see §5.3), not hide it behind a single averaged point.
- **Validation:** The ensemble is validated as a whole (§7) AND each member is validated separately. An ensemble that beats its members only in-sample is not promoted.

### 4.5 Scenario modelling

- **What:** A set of explicitly stated "what-if" paths (e.g. base / upside / downside scenarios) generated by applying stated shocks or parameter shifts to a base method, OR by resampling historical return distributions (bootstrap) under stated assumptions. Scenarios are illustrations of possibilities, not probabilities, unless probabilities are explicitly assigned by a recorded rule.
- **Assumptions that must be stated — for every scenario:** The shock/parameter change, the base method, and whether the scenario carries a probability. A scenario without its assumption stated is not a scenario, it is a story.
- **Data needs:** Same as the base method, plus the stated scenario definitions. Historical-resampling scenarios need a stated resampling window and block structure (returns are autocorrelated; naive independent resampling understates path risk and must not be used without a block/copula justification recorded).
- **Cannot do:** Assign probabilities by intuition. "Downside scenario: 30% likely" requires a recorded probability rule (e.g. historical frequency under stated conditions) — otherwise the scenario is unweighted and must be labelled `unweighted scenario (illustrative only)`.
- **Validation:** Scenarios are validated by whether their assumptions are stated and their generation is reproducible from stored inputs — not by whether one scenario "came true" (a single realisation neither validates nor invalidates a scenario set).

### 4.6 Method selection — deterministic, not preferential

Method selection per symbol and horizon follows a recorded selection procedure, fixed before evaluation:

1. **Eligibility:** A method is eligible only if its data needs (§§4.1–4.5) and minimum-history rule are met for that symbol/horizon, and its training diagnostics (where applicable) pass.
2. **Validation ranking:** Eligible methods are ranked on the validation window (§7) by a FIXED criterion recorded in advance (e.g. interval coverage + interval width, or a stated scoring rule — the criterion is fixed before seeing validation results, not chosen to favour a preferred method).
3. **Selection vs ensemble:** Either the top-ranked method is used, or the ensemble rule (§4.4) is used — the choice is recorded per model version, not per forecast to make a forecast look better.
4. **No LLM selection.** An LLM must not select, weight, or override methods. LLM output about a forecast is interpretation only (§8).

## 5. Probabilistic output format (mandatory)

A forecast is NEVER a single number alone. Every user-facing forecast must contain all of the following; a forecast missing any element is incomplete and must not be shown.

### 5.1 Required elements

| Element | Content | Example shape (illustrative, no real values) |
|---|---|---|
| Point estimate | The central estimate (mean or median — state which) | "Median forecast: [value] PKR" |
| Prediction interval | At minimum an 80% interval AND a 95% interval, or a stated alternative pair, with the method used to compute them | "80% interval: [low]–[high]; 95% interval: [low]–[high]" |
| Distribution summary | Where the method supports it: quantiles (e.g. 10th/25th/50th/75th/90th) or a stated distributional form with parameters | Quantile table, labelled |
| Horizon | Exact horizon and forecast origin (see §6) | "Forecast origin: 2026-11-03 EOD; horizon: 1 week" |
| Method + model version | Named method(s), library, order/parameters, model version, training window dates | "ARIMA(1,1,1), statsmodels, trained 2021-11-03–2026-11-03, v1" |
| Training data provenance | Sources, date range, bar count, gap/conflict flags | "psx-dps EOD, N bars, 0 gaps" |
| Uncertainty statement | Plain-language statement that the interval is an estimate, past performance does not guarantee future results, and the true outcome may fall outside even the 95% interval | See `FINANCIAL_GOVERNANCE.md` §7 DRAFT disclaimer |
| What would change it | Key assumptions whose failure would invalidate the forecast (e.g. suspension, corporate action, regime break) | Stated per forecast |

### 5.2 What is prohibited in output

- A point forecast without intervals.
- An interval without its coverage level (e.g. "range: X–Y" with no % stated).
- A directional claim ("will rise") without its probability and interval.
- A probability without its method (e.g. "70% chance" with no model behind it).
- Rounding that hides uncertainty (e.g. showing a point to 2 decimals while the 95% interval spans 20%).
- Any guarantee language ("will", "guaranteed", "certain", "safe bet") — see `FINANCIAL_GOVERNANCE.md` §8 strict rules.

### 5.3 Disagreement widens uncertainty

When ensemble members disagree, or when a method's validation shows poor coverage, the shown interval must WIDEN (or the forecast must be withheld). Disagreement is information about uncertainty; averaging it away into a narrow interval is concealed uncertainty and is prohibited.

### 5.4 Tiny illustrative output shape (not application code, not real values)

```python
# Shape only — no real forecast is contained in this document.
forecast = {
    "symbol": "...", "origin_pkt": "...", "horizon": "1w",
    "method": "ARIMA(1,1,1)", "model_version": "v1",
    "median": None, "interval_80": (None, None), "interval_95": (None, None),
    "quantiles": {}, "training_window": ("...", "..."),
    "uncertainty_note": "Probabilistic estimate, not a guarantee.",
}
```

## 6. Horizon-specific rules

Horizons: 1 day, 1 week, 1 month, 3 months, 6 months, 12 months. "Week" and "month" mean TRADING days/months as defined here, not calendar approximations silently substituted: 1 week = 5 trading days (or the PSX trading calendar equivalent, stated); 1 month = ~21 trading days (stated); 3/6/12 months = ~63/~126/~252 trading days (stated). If the PSX trading calendar used is itself unverified, that fact must be stated and horizons labelled approximate-trading-day counts.

| Horizon | Permitted methods (illustrative baseline) | Interval behaviour | Special rules |
|---|---|---|---|
| 1 day | Regression, ARIMA, GARCH-informed intervals, ensembles | Narrowest intervals, but never zero-width; overnight-gap risk must be noted (EOD-to-EOD jumps include news/announcements) | Forecast origin must be the latest verified EOD close; a forecast made mid-session from a stale close must be labelled stale-origin |
| 1 week | As 1d, plus scenario illustrations | Intervals wider than 1d | Weekly aggregation must state whether it forecasts the week-end close or the path (these are different targets — never mix) |
| 1 month | Regression, ARIMA, ensembles, scenarios | Intervals materially wider; long-horizon ARIMA point forecasts converge toward trend/mean and must be labelled as such when they do | Corporate-action risk over a month (bonus/rights/splits) must be noted; adjustment status unverified (see `FINANCIAL_FORMULAS.md` §6.1) |
| 3 months | Ensembles and scenarios preferred; single-method point forecasts discouraged | Wide intervals; point estimate carries low weight in any display (interval-first presentation) | Fundamental/macro shifts over 3 months cannot be captured by price-only methods — this limit must be stated on every 3m forecast |
| 6 months | Scenarios + ensembles only as the default; single-method forecasts require explicit justification | Very wide intervals; distribution-first presentation (quantiles, not just a point) | Must carry a "structural-break risk" note: 6 months spans earnings cycles, policy changes, and sector rotations that price-only methods cannot foresee |
| 12 months | Scenarios + ensembles only; distribution-first; point estimate shown only alongside full quantiles | Widest intervals; if the 95% interval is so wide as to be uninformative, that must be stated rather than narrowing it for presentation | 12m price-only forecasts are the weakest in this system and must be labelled as such. No 12m forecast may be used as evidence for a recommendation without the full governance trail (`FINANCIAL_GOVERNANCE.md` §5). Fundamental-based 12m forecasts are EXCLUDED until Block A is verified (§9) |

**General horizon rules:**

- **Intervals widen with horizon.** Any implementation where a longer-horizon interval is narrower than a shorter-horizon interval for the same symbol/method (without a recorded, justified reason such as mean reversion with a stated mechanism) is defective and must be flagged, not shown.
- **No horizon is "safe".** Short horizons are not presented as low-risk; overnight gaps, suspensions, and circuit moves affect even 1-day forecasts.
- **Forecast origin discipline.** A forecast is always anchored to a stated origin (date + EOD close + source). Re-issuing the same forecast with a new date but old origin data, without recomputation, is prohibited — it must be recomputed or labelled as the original forecast with its original origin.

## 7. Validation — backtesting limits given ~5y EOD and no historical intraday archive

### 7.1 Backtesting discipline (mandatory)

- **Walk-forward only.** Backtests use expanding or rolling walk-forward splits: train on data up to origin T, forecast horizon H, evaluate against realised data at T+H, then step forward. In-sample fit, full-history training followed by evaluation on the same history, and look-ahead features are prohibited as validation evidence.
- **Multiple origins.** A backtest result from a single origin is not evidence. Validation requires a stated number of origins spanning different market conditions within the available history — and the limits of that span must be stated (§7.2).
- **Metrics (fixed before evaluation):** Point accuracy (e.g. MAE/RMSE on returns or prices, stated scale); interval coverage (empirical % of realisations inside the 80% and 95% intervals — the key probabilistic metric); interval width (average width, to penalise uselessly wide intervals); directional accuracy ONLY as a secondary metric with its base rate stated (a 55% directional hit rate is meaningless if the base rate is 54%).
- **No cherry-picking.** Backtest windows, symbols, and metrics are fixed before evaluation and reported in full — including windows where the method performed poorly. Reporting only the best window/symbol is prohibited.
- **Transaction-cost and tradability honesty.** Backtest returns, if ever reported, must state whether they are gross or net of costs, spreads, and tradability constraints. In Phase 1, with no trading, backtests report forecast accuracy (above), not trading profits. A backtest must never be presented as "what you would have earned".

### 7.2 Backtesting limits — stated plainly

1. **~5y EOD history only.** psx-dps supplies ~5 years of EOD data. That span contains limited market regimes (it does not contain, for example, every crisis, policy cycle, or sector rotation a longer history would). Backtest results therefore generalise weakly beyond those regimes, and that limit must be stated on every backtest summary.
2. **No historical intraday archive.** Intraday backtests, intraday strategy tests, and intraday VWAP history are EXCLUDED. Any backtest claiming intraday results from psxdata daily OHLCV or psx-dps today's ticks is invalid.
3. **Trading vs listed.** Backtests cover trading symbols with verified histories. Symbols with gaps, suspensions, or thin trading produce fewer valid origins — backtest coverage per symbol (origins attempted vs valid) must be reported, not hidden by restricting silently to liquid symbols and generalising to all.
4. **Survivorship and delisting.** The ~496 trading vs ~1029 listed distinction means a backtest universe built from today's trading symbols is survivorship-biased (delisted/suspended symbols that existed historically are missing). This bias must be disclosed on every backtest; it must never be described as eliminated unless a verified historical constituent list proves it.
5. **Corporate actions and adjustments.** Adjustment status is unverified (see `FINANCIAL_FORMULAS.md` §6.1). Backtests spanning splits/bonus/rights dates carry adjustment risk that must be disclosed; if adjustments are later verified, backtests must be re-run and versioned, not silently corrected.
6. **Overfitting risk.** With ~5y of daily data (~1,250 bars per symbol at most) and many candidate methods/parameters, overfitting is a first-order risk. Parameter search must use a separate validation window, and the number of configurations tried must be reported. A method selected after trying hundreds of configurations on the same validation window has not been validated — it has been fitted to the validation window.
7. **Phase 1 status: NO backtest results exist.** This specification defines backtesting; it does not report any backtest outcome, because no implementation exists yet in Phase 1 and no full-scale live data collection is authorised in Phase 1 (read-only inspection only). Any later backtest claim must reference actual walk-forward runs under this section.

### 7.3 Validation gates before a forecast is user-facing

A method/horizon/symbol combination becomes user-facing ONLY when: (a) its training diagnostics pass (where applicable); (b) its walk-forward validation is complete with coverage reported; (c) its interval behaviour across horizons is sane (§6); (d) its model version, training window, and validation window are recorded; and (e) it passes Independent Audit review (see `FINANCIAL_GOVERNANCE.md` §6). Until then, the forecast is withheld with its reason — exactly as with analytics gates (`ANALYTICS_SPECIFICATION.md` §5).

## 8. Forecast history, actual-vs-predicted evaluation, and the AI-interpretation boundary

### 8.1 Forecast history (immutable record)

Every forecast ever shown must be stored, immutably, with: symbol, origin (date + close + source), horizon, method + model version, training window, point estimate, full intervals/quantiles, and the exact text/values shown to the user. Stored forecasts are never edited, deleted, or "corrected" after the fact — corrections are new records that reference the original (see `FINANCIAL_GOVERNANCE.md` §6 on audit).

### 8.2 Actual-vs-predicted evaluation (ongoing, automatic in design)

- When a forecast's horizon elapses, the realised value (verified EOD close on the horizon date, with source and any gap/suspension flag) is recorded alongside the stored forecast.
- **Evaluation outputs (deterministic):** Whether the realisation fell inside the 80% interval, inside the 95% interval, or outside both; the forecast error (realised − point, on a stated scale); and the running coverage rates per method/horizon/symbol over all elapsed forecasts.
- **Evaluation cadence:** Coverage and error summaries are recomputed on a stated schedule (e.g. monthly, or on each horizon expiry batch) and versioned. A method whose running 95% coverage falls materially below 95% (threshold fixed in advance, e.g. with a statistical tolerance for sample size) is flagged for review and, if the shortfall persists, suspended from user-facing forecasts until revalidated. The suspension rule and threshold are fixed in advance, not chosen after seeing poor coverage.
- **Presentation honesty:** Actual-vs-predicted evaluation is shown as accuracy evidence with its sample size ("n = 42 elapsed 1-week forecasts"). Small-n evaluations (e.g. n < 20 for a horizon) must be labelled `small sample — coverage estimate unreliable`, never presented as precise.
- **No rewriting history.** A forecast that missed badly stays in the record and in the coverage statistics. Deleting misses, or re-issuing a forecast with a later origin and backdating it, is falsification and is prohibited under `FINANCIAL_GOVERNANCE.md` §8.

### 8.3 AI-assisted research may interpret deterministic outputs but may not invent forecast numbers

- **Permitted (Ollama local inference only; no paid AI APIs):** An LLM may summarise a deterministic forecast in prose, explain what an interval means, list the stated assumptions, or compare two stored forecasts — PROVIDED it cites the deterministic values exactly, invents no new number, probability, interval, or date, and its output is labelled as AI-assisted interpretation.
- **Prohibited:** An LLM generating, adjusting, narrowing, rounding, or "improving" a forecast number; an LLM producing a forecast where no deterministic forecast exists; an LLM converting a probabilistic forecast into a guarantee ("likely to rise, so buy"); an LLM filling a missing interval with a plausible range.
- **Enforcement in design:** The forecasting path (data → deterministic method → stored forecast → display) contains no LLM call. LLM interpretation, if offered, is a separate, labelled layer that reads stored forecasts and cannot write to the forecast store. Any implementation where LLM text can reach the forecast store or the display without passing through the deterministic values is non-compliant.
- **Research use:** AI-assisted research (e.g. summarising news or filings to contextualise a forecast) is interpretation of external material, not a forecast input, unless a future specification defines a tested, recorded feature pipeline for it. In Phase 1, no news/filing feed is verified, so no such pipeline is specified.

## 9. Excluded / limited forecasting (because data does not permit it)

1. **Historical intraday forecasting and intraday backtests** — EXCLUDED (no historical intraday archive).
2. **Fundamental forecasting** (revenue, EPS, dividend forecasts) — EXCLUDED until a fundamental feed is verified; price-only methods cannot substitute for fundamental forecasts.
3. **Macro forecasting** (rates, inflation, FX forecasts as system outputs) — EXCLUDED until a macro feed is verified; all macro feeds are currently UNVERIFIED.
4. **Analyst-consensus-based forecasts** — EXCLUDED (no verified analyst-estimate feed).
5. **Long-horizon single-method point forecasts presented as precise** — LIMITED per §6 (distribution-first, wide intervals, structural-break notes for 6m/12m).
6. **Any forecast for a suspended, delisted, or thinly traded symbol without a valid history** — WITHHELD under minimum-history and tradability gates, not produced from sparse data.
7. **Full-scale live data collection to build training sets** — NOT part of Phase 1 (read-only data inspection only).

## 10. Testing strategy — defined, not claimed passed

Phase 1 defines the tests; it does not claim any test has passed (11-stage workflow, stage 8):

1. **Method unit tests:** Each method reproduces hand-computed or reference-implementation results on a small verified series (within a stated tolerance for floating-point).
2. **No-look-ahead tests:** Features at origin T use only data ≤ T (test by shifting inputs and confirming outputs change only as expected).
3. **Walk-forward harness tests:** Splits, origins, and horizon alignment tested on synthetic series with known properties before any real data is used.
4. **Interval tests:** Coverage computation, widening-with-horizon (§6), and disagreement-widens-uncertainty (§5.3) tested.
5. **Negative tests:** Request a forecast with insufficient history, a suspended symbol, an intraday horizon history, or a fundamental/macro forecast in Phase 1 conditions → correctly withheld with reason.
6. **LLM-exclusion tests:** Forecasting path contains no LLM call; LLM interpretation layer cannot write to the forecast store.
7. **Reproducibility tests:** Same inputs + same model version → identical forecast (deterministic methods only; any stochastic component, e.g. bootstrap, uses a fixed, recorded seed).

No test result is reported in this specification, because no implementation exists yet in Phase 1.

---

*End of FORECASTING_SPECIFICATION.md — Phase 1 specification only. No forecast, price, or recommendation is contained in this document.*
