# PSX Intelligence AI — Analytics Specification

**Phase:** 1 of 30 — Specification only. No application code. STOP AFTER PHASE 1.
**Team:** Team 7 (Financial Analytics + Security + Governance)
**Companion documents:** `FINANCIAL_FORMULAS.md` (formula definitions), `FORECASTING_SPECIFICATION.md`, `VALUATION_SPECIFICATION.md`, `SECURITY_REQUIREMENTS.md`, `FINANCIAL_GOVERNANCE.md` — all in this same `docs/phase-01/` folder.
**Date / starting condition:** Verified 2026-11-04, reused verbatim — see §1.

## 1. Starting condition (reuse verbatim)

- Project folder `~/workspace/psx-intelligence-ai/` is new. Other teams may be creating sibling files; this team writes only its assigned files and never overwrites/touches sibling teams' files or the separate scaffold `~/workspace/psx-data-collection/` (stdlib collector with provenance / PKT / stale / conflict rules), which is REFERENCED only.
- Tools: Python 3.12.3, Node v24.22.1. Docker, psql, redis-cli NOT installed.
- Already verified (reuse): psx-dps (~496 trading vs ~1029 listed, ~5y EOD, today's ticks, 38 sectors, multi-node 404 quirk, no official PSX API); psxdata (daily OHLCV + live snapshots ONLY, no historical intraday archive — so VWAP / intraday-dependent metrics are limited to what data permits, and historical intraday backtests must not be assumed); Eulerpool: NO PSX coverage, vendor only, no paid API approved.
- SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use is UNVERIFIED — formulas depending on macro / fundamental feeds must state the feed as UNVERIFIED and define missing-data handling (skip / flag, never estimate silently).

## 2. Revised brief — merged

- **Budget: PKR 0 absolute zero-cost.** Analytics must use local open-source libraries only — Pandas / NumPy / scikit-learn / statsmodels / PyTorch where justified — and Ollama local inference only. No paid AI APIs, no paid subscriptions, no paid data vendor is approved or assumed. Local hardware, electricity, and internet are EXTERNAL operating expenses: disclose them as such, never call them "free". PKR 0 means zero project spend on software/APIs/subscriptions/vendors, not zero operating cost.
- **Phase 1 workflow (11 stages):** (1) brainstorm, (2) research, (3) validate, (4) data inspection — read-only only, NO full-scale live data collection in Phase 1, (5) architecture planning, (6) implementation specification, (7) documentation, (8) testing strategy — defined, not claimed passed, (9) independent audit, (10) correction, (11) checkpoint. This document is stages 6–7. It defines behaviour; it does not claim any test has passed, any data has been collected at scale, or any model has been trained.
- **No real trading initially.** The system must NOT execute real trades initially. Analytics outputs are informational only. No analytics output, score, or recommendation may be wired to an order, broker, or execution path in Phase 1 (see `SECURITY_REQUIREMENTS.md` §9 and `FINANCIAL_GOVERNANCE.md` §8). Paper / hypothetical illustrations, if ever added in a later phase, are not trades and must be labelled as such.
- **Critical rules preserved:** Financial calculations are deterministic Python functions ONLY; LLMs must NEVER invent numerical financial results; forecasts are probabilistic and evidence-based, never guaranteed; BUY / HOLD / SELL / WATCHLIST are probabilistic recommendations with uncertainty shown, not advice guarantees; no unauthorised trading; no fabricated data; no unsupported forecasts; no unverified recommendations; no concealed uncertainty; no unauthorised commercial redistribution.

## 3. What the "company view" is

The company view is a single, auditable presentation of one listed company, assembled from five analytic blocks. It is NOT a single number, NOT a single score, and NOT a recommendation by itself. A recommendation (BUY / HOLD / SELL / WATCHLIST) is a separate, governed output derived from the company view under the rules in §8 and `FINANCIAL_GOVERNANCE.md` — it is never the company view itself.

The five blocks:

| # | Block | What it contains | Data basis in Phase 1 |
|---|---|---|---|
| A | Fundamental analytics | Profitability, liquidity, leverage, valuation, growth ratios from `FINANCIAL_FORMULAS.md` §§1–5 | UNVERIFIED fundamental feed → in Phase 1 this block is **empty with a stated reason**, not estimated (see §4.1) |
| B | Technical analytics | SMA, EMA, RSI, MACD, Bollinger Bands, ATR, ADX, OBV, current-session VWAP only, from `FINANCIAL_FORMULAS.md` §6 | psx-dps EOD (~5y) / psxdata daily OHLCV — verified-in-principle, subject to data-quality gates (§5) |
| C | Sector analytics | Sector membership, sector-relative position of the company's technical measures, sector aggregates where constituents are verified | psx-dps 38-sector lists — verified-in-principle; sector aggregates require verified constituents (§6) |
| D | Macro analytics | Macro context (rates, inflation, FX, growth) shown ONLY as context, never as a company input unless a formula explicitly requires it | ALL macro feeds UNVERIFIED → in Phase 1 this block is **empty with a stated reason**, not estimated (see §4.3) |
| E | Health scoring | Deterministic composite health score(s) from blocks A–D under §7, shown ONLY when all gates in §5 pass | Depends on A–D; in Phase 1, with A and D empty, no full health score is shown (see §7.5) |

**Ordering rule.** Blocks are always shown in the order A–E with their availability status visible. A block that is empty must occupy its place with its reason ("Fundamental feed UNVERIFIED", "Macro feed UNVERIFIED", "Data stale", etc.) — it must never be silently omitted so that the view looks complete, and never backfilled with an LLM narrative, a peer's value, or a prior-period value relabelled as current.

**Tiny illustrative structure (not application code).** The company view is a data structure, not prose:

```python
# Illustrative shape only — not runnable application code.
company_view = {
    "symbol": "...", "as_of_pkt": "...",
    "fundamental": {"status": "unavailable", "reason": "fundamental_feed_unverified"},
    "technical": {"status": "available_or_gated", "indicators": {}},
    "sector": {"status": "...", "sector": "...", "member_count": None},
    "macro": {"status": "unavailable", "reason": "macro_feed_unverified"},
    "health_score": {"status": "withheld", "reason": "insufficient_verified_blocks"},
}
```

## 4. Each block in detail

### 4.1 Block A — Fundamental analytics

- **Contents:** Every ratio in `FINANCIAL_FORMULAS.md` §§1–5 that can be computed from verified statements, each with its value, period, source, and PKT as-of date. Ratios are grouped (profitability / liquidity / leverage / valuation / growth), never flattened into one list without group labels.
- **Phase 1 status: UNAVAILABLE.** No verified machine-readable fundamental feed exists in the starting condition. SECP filings and any vendor feed are UNVERIFIED. Therefore Block A shows no ratios in Phase 1. This is a deliberate, correct empty state — not a gap to be filled by hand-copying, estimating, or LLM recall.
- **What unblocks it (future phase, not Phase 1):** A verified feed with licence, format, coverage (which of ~1029 listed / ~496 trading symbols), update cadence, restatement policy, and adjustment status documented, plus the deterministic functions and tests in `FINANCIAL_FORMULAS.md` §9. Until then, any stakeholder request for "just show the P/E" must be answered with the unavailable reason, not a number from an unverified web page.
- **Sector guardrail:** Banks/financials/insurance ratios excluded or warned per `FINANCIAL_FORMULAS.md` §7 apply inside Block A whenever it becomes available. The guardrail is part of the specification now, even though the block is empty now.

### 4.2 Block B — Technical analytics

- **Contents:** Each indicator in `FINANCIAL_FORMULAS.md` §6, with its window/parameters, value, bar count, seed/warm-up status, and PKT as-of (EOD date). Indicators are shown as series + latest value, never as a lone latest value without its window and history length.
- **Sources:** psx-dps EOD closes/highs/lows/volumes (~5y) and psxdata daily OHLCV. Where the two sources disagree on the same date, the conflict rule in §5.4 applies — the indicator is withheld or flagged, never averaged silently.
- **Intraday limit (binding):** No historical intraday indicator series, no intraday backtest. Current-session VWAP only, labelled `VWAP (today, intraday, partial session)` where the live feed permits (see `FINANCIAL_FORMULAS.md` §6.10). A daily-bar approximation must never be labelled VWAP.
- **Interpretation ban:** Technical indicators are presented as measurements (e.g. "RSI-14 = 62 on 2026-11-03 EOD"), not as signals. Threshold language ("overbought", "bullish crossover", "buy signal") is NOT a deterministic output and must not be generated by the analytics layer. If an LLM layer later interprets indicators in prose, that prose must cite the deterministic values, must not invent new numbers, and is governed by `FINANCIAL_GOVERNANCE.md` (see §8.3).

### 4.3 Block D — Macro analytics (note: described before C in dependency order is avoided; see §4.4 for C)

- **Contents (when verified):** Policy rate, inflation (CPI), PKR/USD, GDP growth, and any other macro series a future verified specification names — each with source agency, release date, vintage, and revision status.
- **Phase 1 status: UNAVAILABLE.** SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use is UNVERIFIED. No macro number, chart, or "macro headwind/tailwind" claim may appear in Phase 1. Macro context must not be smuggled in via an LLM's training knowledge ("interest rates are high") — that is an unverified, undated claim and is prohibited as analytics input.
- **Role when available:** Context only. Macro series do not enter company health scoring ( §7) unless a future specification defines an explicit, tested macro-to-score rule. A macro shock is never, by itself, a reason to change a company score without a stated rule.

### 4.4 Block C — Sector analytics

- **Contents:** (a) The company's sector (from the psx-dps 38-sector list, with membership date); (b) the company's technical measures positioned against its sector peers on the SAME measure, SAME window, SAME date (e.g. RSI-14 distribution across verified sector members on the same EOD date); (c) sector aggregates (count, median, quartiles) computed deterministically from verified member values only.
- **Rules:**
  1. **Same-date, same-definition rule.** A sector comparison is valid only if every member value uses the same indicator, window, and EOD date. Mixed dates or windows → no comparison.
  2. **Coverage rule.** A sector aggregate is shown only if a stated minimum coverage is met (to be fixed at implementation and recorded — e.g. at least N verified members AND at least X% of trading members in the sector). Below coverage → aggregate withheld with `insufficient_sector_coverage` and the member count shown. The threshold itself must be recorded, not chosen per-company to make a result appear.
  3. **No invented benchmark.** No sector index level, sector benchmark return, or "sector average P/E" is shown unless its constituents, weights, and computation are verified and stated. In Phase 1, with Block A empty, no sector fundamental aggregate (e.g. sector P/E) exists at all.
  4. **Membership drift.** Sector membership changes over time. Every sector view carries its membership date and member count; a historical sector comparison must use historical membership if it claims to be historical, otherwise it is labelled current-membership-only.
  5. **Trading vs listed.** Sector member counts must distinguish trading members (~496 universe) from merely listed members (~1029). A sector aggregate over listed-but-not-trading symbols with stale prices is invalid.
- **Phase 1 status: PARTIALLY AVAILABLE in principle.** Sector lists exist via psx-dps, but any sector aggregate still passes through the §5 gates. If EOD data for enough members fails a gate, the aggregate is withheld — the sector block then shows membership only, with the aggregate reason stated.

## 5. Data-quality gates — before ANY score or company-view element is shown

No score, no recommendation, and no "complete" company view may be shown until every applicable gate below passes. Gates are deterministic checks, not LLM judgement. Failure of a gate withholds the affected element (or the whole score, per §5.5) and surfaces the reason. Gates run on every refresh, not once at onboarding.

### 5.1 Gate G1 — Source verification

- **Check:** Is the source for this element a verified source for this data type? (psx-dps for EOD/ticks/sector lists; psxdata for daily OHLCV/live snapshots — verified-in-principle per the starting condition; fundamental/macro/vendor feeds — UNVERIFIED.)
- **Fail →** Element withheld, reason `source_unverified`. This is why Blocks A and D are empty in Phase 1.

### 5.2 Gate G2 — Freshness / staleness

- **Check:** Is the as-of date within the element's stated freshness window? EOD data: the latest verified trading day (weekends/holidays/PSX calendar respected — a Friday close is not "stale" on Saturday merely because the calendar date advanced; staleness is measured in trading days, with the PSX trading calendar as the reference, which itself must be verified before it is used to excuse staleness).
- **Fail →** Element shown only with a prominent `stale_as_of_<date>` warning, or withheld if the score rules (§7) require fresh data. A stale price never feeds a valuation ratio or a score silently. Staleness thresholds per element type must be recorded in implementation (e.g. EOD: N trading days; statement: N months) — the threshold is part of the specification to be fixed, not invented per view.

### 5.3 Gate G3 — Completeness / minimum history

- **Check:** Does the series contain the minimum verified bars/periods the formula requires (e.g. SMA-50 needs 50 closes; CAGR needs both endpoints)? Partial windows are not full windows (see `FINANCIAL_FORMULAS.md` §6.1).
- **Fail →** Element withheld, or labelled `partial (n of N)` where the formula specification explicitly permits a partial display. Partial values never enter scores.

### 5.4 Gate G4 — Conflict

- **Check:** Do two verified sources agree on the same element/date within a stated tolerance? (psx-dps vs psxdata on the same EOD close, for example.) Tolerance, if any, must be recorded; a zero-tolerance default is safest for prices.
- **Fail →** Element withheld with `conflicting_sources`, both values and sources shown for audit, never averaged, never "picked the newer one" without a recorded precedence rule. Precedence rules, if ever adopted, belong to the data layer specification, not to ad-hoc analytics judgement. The psx-dps multi-node 404 quirk is a fetch failure, not a conflict and not a price — it triggers a data-availability flag, not G4.

### 5.5 Gate G5 — Applicability

- **Check:** Is this formula applicable to this company/sector? (Banks vs EV/EBITDA, negative-equity vs ROE, loss-making vs P/E — see `FINANCIAL_FORMULAS.md` §7.)
- **Fail →** Element withheld with `not_applicable_<reason>`, never a misleading number.

### 5.6 Gate outcome table — what the user sees

| Gate outcome | Company-view element | Health score | Recommendation |
|---|---|---|---|
| All applicable gates pass | Shown with provenance | May be computed (§7) | May be derived (§8) |
| Any gate fails for an element | That element withheld + reason shown | Score withheld if the element is a score input (§7.4) | Withheld if it depends on the withheld score/element |
| Source unverified (G1) for a whole block | Whole block empty + reason | Full score withheld (§7.5) | Withheld |

**No partial-credit presentation.** A company view with a failed gate must not be styled as complete. The UI must show the withheld element's row with its reason (see §9 for display rules), so absence is visible and auditable.

## 6. Combining blocks — the combination rule

Combination is deterministic assembly, not blending into an opaque number:

1. **Assemble, don't average away.** The company view presents Blocks A–E side by side with their own provenance. There is no step that averages a fundamental ratio with a technical indicator into a single "combined value" — different units, periods, and reliabilities make such averaging meaningless.
2. **Score separately, then combine by rule.** Health scoring (§7) is the ONLY place where blocks combine, and it does so through explicit sub-scores with explicit weights that sum to a stated total, each sub-score traceable to its block inputs.
3. **Macro never silently adjusts a company score.** See §4.3: macro is context unless a future specification defines a tested rule.
4. **Sector position is relative, not absolute.** A company's sector percentile (e.g. "RSI-14 at the 70th percentile of its sector on 2026-11-03") is a descriptive statistic, not a quality judgement. It must show the sector, date, member count, and coverage — never a bare percentile.
5. **Time alignment.** Every combined presentation states the as-of date of EACH block. A view mixing today's technicals with a year-old statement (when Block A becomes available) must label that vintage mismatch wherever the two appear together.

## 7. Health scoring — deterministic procedures, not LLM judgement

### 7.1 Principles

- A health score is a deterministic function of verified inputs, with fixed weights, fixed thresholds, and a worked audit trail. If two runs on identical inputs give different scores, the implementation is defective.
- **No LLM in the scoring path.** An LLM may explain a score after it is computed (citing its sub-scores and inputs, inventing no numbers); it may not set, adjust, override, or "interpret into" the score. Any LLM-generated text about a score must be labelled as interpretation, not as the score itself.
- **Scores are descriptive, not predictive, unless stated.** A health score describes the company's measured state on verified inputs. It is not a forecast and not a recommendation. Conflating health with expected return is prohibited.

### 7.2 Sub-score structure (specification — weights to be fixed at implementation and then frozen)

The full health score, when all blocks are available, is composed of sub-scores. The structure is specified now; the numeric weights and thresholds are NOT invented in Phase 1 and must be fixed, recorded, and frozen before any score is shown, with any later change versioned (old scores retain their version label).

| Sub-score | Inputs (deterministic only) | Phase 1 availability |
|---|---|---|
| Fundamental health | Profitability, liquidity, leverage ratios (Block A) | UNAVAILABLE (Block A empty) |
| Technical health | Trend/volatility/volume measures (Block B) — as measurements, not signals | Available in principle, subject to §5 gates |
| Sector-relative health | Sector percentiles on technical measures (Block C) | Available in principle, subject to §6 coverage rule |
| Macro-context flag | Macro regime flag, if a future rule defines it (Block D) | UNAVAILABLE, and never a silent adjuster (§4.3) |

**Weight rule.** Sub-score weights must sum to 100% of the inputs actually present — but ONLY if the missing-input rule in §7.4 permits a partial score at all. The default Phase 1 rule is: **no partial full-score**. See §7.4–§7.5 for the exact consequence.

### 7.3 Scoring procedure (deterministic steps)

For each sub-score, the procedure is:

1. **Collect** the verified inputs for that sub-score (each already gate-passed per §5).
2. **Normalise** each input by a FIXED, recorded rule (e.g. percentile within a stated universe and date, or banded thresholds fixed in advance). The normalisation rule, universe, and date must be recorded with the score. Normalisation against a cherry-picked peer set, or against a universe that changes per company, is prohibited.
3. **Weight and sum** by the frozen weights.
4. **Band** the numeric score into a labelled band (e.g. bands to be fixed at implementation — the band edges are part of the frozen specification, not chosen after seeing the score).
5. **Emit** the score WITH: numeric value, band label, version (weights/thresholds version), sub-scores, every input value with source and date, and every gate outcome. A score without its audit trail is not a valid output.

**Tiny illustrative shape (not application code, not real weights):**

```python
# Shape only: weights/thresholds are NOT fixed by this Phase 1 document.
# They must be fixed, recorded, and frozen before any real score is shown.
health_score = sum(weight[i] * normalised_subscore[i] for i in present_subscores)
# A score emitted without its sub-scores, inputs, version, and gate outcomes is invalid.
```

### 7.4 Missing / stale / conflicting inputs — what happens to the score

| Input condition | Effect on its sub-score | Effect on the full health score |
|---|---|---|
| Input missing (no verified value) | That input contributes nothing; the sub-score is computed only if its own minimum-input rule (fixed at implementation) is met, otherwise the sub-score is withheld | If any required sub-score is withheld, the FULL score is withheld (default rule) |
| Input stale (G2 fail) | Stale inputs never enter a sub-score silently; if the sub-score's freshness rule requires fresh data, the sub-score is withheld | Full score withheld |
| Input conflicting (G4 fail) | Conflicting input withheld from the sub-score | Full score withheld if the sub-score then fails its minimum-input rule |
| Input not applicable (G5 fail) | Excluded from that company's sub-score by rule, with reason recorded | Full score may still be computed ONLY if the specification's sector-specific scoring variant (fixed in advance for banks etc.) defines how — otherwise withheld |

**No imputation.** Missing inputs are never filled by mean, median, peer value, prior period, forecast, or LLM estimate. "Impute then score" is prohibited. The only permitted handling is withhold-and-state-reason.

### 7.5 Phase 1 consequence — no full health score is shown

Because Blocks A (fundamental) and D (macro) are UNVERIFIED/empty in Phase 1, and because the default rule is no partial full-score, **no full health score may be shown in Phase 1**. What MAY be shown in Phase 1, when gates pass, is:

- Individual technical indicators (Block B) with provenance;
- Sector-relative technical percentiles (Block C) with coverage;
- A clearly labelled **technical-only sub-score**, IF its weights/thresholds are fixed and frozen first — and it must be labelled `Technical health (sub-score only — NOT a full health score)` everywhere it appears, never shortened to "Health Score".

Any UI, report, or export that shortens that label is non-compliant with this specification.

### 7.6 Score history and comparability

- Every emitted score is stored with its version, inputs, and gate outcomes (see §10). Scores from different versions are NOT directly comparable; a version change must be shown as a break in any score history chart, not spliced.
- Score history is a record of past scores on past inputs — it is not a backtest of returns and must never be presented as evidence that high scores predict returns (that claim would require the backtesting discipline in `FORECASTING_SPECIFICATION.md` §7, on verified data, and is NOT made in Phase 1).

## 8. From company view to recommendation (governed, probabilistic, never guaranteed)

Recommendations (BUY / HOLD / SELL / WATCHLIST) are governed in full by `FINANCIAL_GOVERNANCE.md`. The analytics specification constrains them as follows:

1. **No recommendation without a score trail.** A recommendation may be derived only from a gate-passed company view (and, when required, a gate-passed health score) plus a recorded recommendation rule. A recommendation with no traceable inputs is an unverified recommendation and is prohibited.
2. **Probabilistic with uncertainty shown.** A recommendation is presented with its evidence list, its uncertainty (missing blocks, stale inputs, model limits), and its probabilistic framing — never as a certainty, target, or guarantee. See `FINANCIAL_GOVERNANCE.md` §5 for required wording and the DRAFT disclaimer.
3. **No recommendation in Phase 1 on an incomplete view.** With Blocks A and D empty and no full health score available (§7.5), no BUY / HOLD / SELL recommendation may be derived in Phase 1. WATCHLIST as a user-managed list (a user bookmarking a symbol to monitor) is not a system recommendation and must not be presented as one.
4. **LLM interpretation boundary.** An LLM (Ollama local inference only, per §2 — no paid AI APIs) may summarise the deterministic company view in prose, but: it must cite the deterministic values, must not invent numbers, must not upgrade a sub-score to a full score, must not convert a description into a recommendation, and its output must be labelled as AI-assisted interpretation of deterministic outputs (see `FORECASTING_SPECIFICATION.md` §8 for the parallel forecasting rule).

## 9. Display rules (what the user must always see)

Every company view, score, and recommendation display must show, without the user having to dig:

- Symbol, sector, and as-of date(s) in PKT, per block;
- Each block's availability status and reason if empty/withheld;
- Each value's source and vintage;
- Stale/conflict/partial flags where applicable;
- Score version, sub-scores, and weights reference (when a score is shown);
- Uncertainty and limitations (see `FINANCIAL_GOVERNANCE.md` §4);
- The DRAFT disclaimer (see `FINANCIAL_GOVERNANCE.md` §7) on any view that contains a score or recommendation.

A view that hides a withheld block, a stale flag, or uncertainty behind a "clean" presentation is non-compliant, even if every shown number is correct.

## 10. Audit, storage, and reproducibility

- **Store the inputs, not just the outputs.** For every company view/score/recommendation ever shown, store: inputs with sources and dates, gate outcomes, weights/thresholds version, computation timestamp (PKT), and the exact output shown. Re-running the deterministic functions on stored inputs must reproduce the stored output.
- **Independent Audit agent.** Scores and recommendations are subject to audit by the Independent Audit agent (see `FINANCIAL_GOVERNANCE.md` §6). Audit needs the stored trail in this section — an output without a trail cannot be audited and therefore cannot be shown.
- **Zero-cost storage note.** Storage in Phase 1 is local (no paid database service is assumed; Docker/psql/redis are NOT installed per the starting condition). The storage design belongs to sibling teams' architecture documents; this specification requires only that whatever local store is chosen can retain the audit trail above. No paid storage is approved.
- **No commercial redistribution.** Company views, scores, and underlying data must not be redistributed commercially without authorisation (see `FINANCIAL_GOVERNANCE.md` §8). Internal audit storage is not redistribution.

## 11. Testing strategy — defined, not claimed passed

Phase 1 defines the tests; it does not claim any test has passed (per the 11-stage workflow, stage 8):

1. **Gate tests:** Each gate G1–G5 tested with pass/fail fixtures, including stale, conflicting, partial-history, negative-equity, and thin-trading cases.
2. **Formula tests:** Per `FINANCIAL_FORMULAS.md` §9 (hand-computed cases, zero denominators, missing inputs).
3. **Combination tests:** Mixed-vintage views labelled correctly; withheld blocks visible; no silent averaging across blocks.
4. **Score tests:** Determinism (same inputs → same score); no-imputation tests (missing input → withheld, never filled); version-break tests (version change breaks history, not splices it); LLM-exclusion tests (scoring path contains no LLM call).
5. **Display tests:** Withheld-reason visibility; stale/conflict flag visibility; disclaimer presence on score/recommendation views.
6. **Negative tests:** Request a fundamental ratio, macro value, full health score, or recommendation in Phase 1 conditions → correctly withheld with reason (this is the expected, passing behaviour in Phase 1).

No test result is reported in this specification, because no implementation exists yet in Phase 1. Any later claim of "tests passed" must reference actual test runs, not this document.

## 12. Excluded / limited analytics (because data does not permit them)

1. **Fundamental analytics** — limited to unavailable until a fundamental feed is verified (§4.1).
2. **Macro analytics** — limited to unavailable until a macro feed is verified (§4.3).
3. **Full health score** — withheld in Phase 1 (§7.5).
4. **Any recommendation** — withheld in Phase 1 on an incomplete view (§8.3).
5. **Historical intraday analytics and intraday backtests** — excluded (no historical intraday archive).
6. **Sector fundamental aggregates** (e.g. sector P/E) — excluded until Block A is verified.
7. **Analyst-consensus, target-price, short-interest, or options-based analytics** — excluded (no verified feed in the starting condition).
8. **Full-scale live data collection** — NOT part of Phase 1 (read-only data inspection only, per the 11-stage workflow). Analytics in Phase 1 are specified against the already-verified source descriptions, not against a new bulk collection run.

---

*End of ANALYTICS_SPECIFICATION.md — Phase 1 specification only. No scores, recommendations, prices, or forecasts are contained in this document.*
