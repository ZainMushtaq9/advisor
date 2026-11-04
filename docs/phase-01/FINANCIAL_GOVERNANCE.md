# PSX Intelligence AI — Financial Governance

**Phase:** 1 of 30 — Specification only. No application code, no advice, no legal advice. STOP AFTER PHASE 1.
**Team:** Team 7 (Financial Analytics + Security + Governance)
**Companion documents:** `FINANCIAL_FORMULAS.md`, `ANALYTICS_SPECIFICATION.md`, `FORECASTING_SPECIFICATION.md`, `VALUATION_SPECIFICATION.md`, `SECURITY_REQUIREMENTS.md` — all in this same `docs/phase-01/` folder.
**Date / starting condition:** Verified 2026-11-04, reused verbatim — see §1.

## 1. Starting condition (reuse verbatim)

- Project folder `~/workspace/psx-intelligence-ai/` is new. Other teams may be creating sibling files; this team writes only its assigned files and never overwrites/touches sibling teams' files or the separate scaffold `~/workspace/psx-data-collection/` (stdlib collector with provenance / PKT / stale / conflict rules), which is REFERENCED only.
- Tools: Python 3.12.3, Node v24.22.1. Docker, psql, redis-cli NOT installed.
- Already verified (reuse): psx-dps (~496 trading vs ~1029 listed, ~5y EOD, today's ticks, 38 sectors, multi-node 404 quirk, no official PSX API); psxdata (daily OHLCV + live snapshots ONLY, no historical intraday archive — so VWAP / intraday-dependent metrics are limited to what data permits, and historical intraday backtests must not be assumed); Eulerpool: NO PSX coverage, vendor only, no paid API approved.
- SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use is UNVERIFIED — formulas depending on macro / fundamental feeds must state the feed as UNVERIFIED and define missing-data handling (skip / flag, never estimate silently).

## 2. Revised brief — merged

- **Budget: PKR 0 absolute zero-cost.** Governance in this specification requires no paid service: analytics/forecasting use local open-source libraries (Pandas / NumPy / scikit-learn / statsmodels / PyTorch where justified) and Ollama local inference only; no paid AI APIs or subscriptions are approved. Local hardware, electricity, and internet are EXTERNAL operating expenses: disclose them as such, never call them "free". PKR 0 means zero project spend on software/APIs/subscriptions/vendors, not zero operating cost.
- **Phase 1 workflow (11 stages):** (1) brainstorm, (2) research, (3) validate, (4) data inspection — read-only only, NO full-scale live data collection in Phase 1, (5) architecture planning, (6) implementation specification, (7) documentation, (8) testing strategy — defined, not claimed passed, (9) independent audit, (10) correction, (11) checkpoint. This document is stages 6–7. It defines governance; it does not claim any governance control has operated, any audit has passed, or any disclosure has been legally reviewed.
- **No real trading initially — EXPLICIT (see §8).** The system must NOT execute real trades initially. Trading restrictions are stated here AND in `SECURITY_REQUIREMENTS.md` §9. Governance alone does not authorise trading; a future trading capability would require separate, explicit approval plus its own governance, and it is NOT granted by this document.
- **Critical rules preserved:** Financial calculations are deterministic Python functions ONLY; LLMs must NEVER invent numerical financial results; forecasts are probabilistic and evidence-based, never guaranteed; BUY / HOLD / SELL / WATCHLIST are probabilistic recommendations with uncertainty shown, not advice guarantees; no unauthorised trading; no fabricated data; no unsupported forecasts; no unverified recommendations; no concealed uncertainty; no unauthorised commercial redistribution.

## 3. Purpose and scope of governance

Financial governance answers one question before any number reaches a user: **is this output evidenced, uncertain-where-uncertain, auditable, and honestly labelled — or must it be withheld?** If the answer is not clearly the former, the output is withheld. Governance is not a disclaimer pasted onto an otherwise unsupported number; a disclaimer does not rescue an unevidenced forecast, an invented ratio, or a recommendation without a trail.

**Scope.** This document governs: all financial calculations, analytics, scores, forecasts, valuations, recommendations, and any prose about them (including AI-assisted interpretation). It governs what may be shown, what must accompany it, who may change the rules, and how errors are corrected. It does not govern general product design, which belongs to sibling teams — except where general design touches financial outputs, in which case this document prevails for those outputs.

**Authority.** Changes to this governance document, to scoring weights/thresholds, valuation assumptions/methods, recommendation rules, or data-source precedence require: a written proposal, Independent Audit review (§6), and a recorded approval distinct from the proposer (separation of duties per `SECURITY_REQUIREMENTS.md` §5.2). No single person, and no LLM, may change a financial rule unilaterally.

## 4. Financial disclosures — what the user must always be told

Every financial view (company view, score, forecast, valuation, recommendation) must disclose, in plain language in the same view:

1. **What this is.** The output type (measurement, score, probabilistic forecast, model valuation, or recommendation) — never a bare number without its type.
2. **What it is based on.** Sources, dates (PKT), vintages, and training windows, per `ANALYTICS_SPECIFICATION.md` §9 and `FORECASTING_SPECIFICATION.md` §5.
3. **What is missing.** Empty blocks, withheld elements, and their reasons (UNVERIFIED feed, stale data, conflict, insufficient history, inapplicable method). Absence must be visible (§4, `ANALYTICS_SPECIFICATION.md` §5.6).
4. **How uncertain it is.** Intervals for forecasts, sensitivity ranges for valuations, sub-scores and version for scores, and the plain-language uncertainty statement in §7.
5. **What it is not.** Not a guarantee, not a promise of return, not personalised advice (see §5.3), not a trade instruction (see §8).
6. **Model limitations.** The relevant limits from `FINANCIAL_FORMULAS.md` §§6–7, `FORECASTING_SPECIFICATION.md` §§6–7, and `VALUATION_SPECIFICATION.md` §§6–7, summarised in the view — not buried in documentation the user never sees. At minimum: data-history limits (~5y EOD; no historical intraday archive), fundamental/macro feed status, and the single-method warning for valuations.
7. **When it was computed and when it expires.** Computation timestamp (PKT) and the as-of dates of its inputs. A forecast or valuation does not silently stay "current" — staleness rules (`ANALYTICS_SPECIFICATION.md` §5.2) determine when it must be refreshed or withdrawn.

**Disclosure failure = output failure.** A correct number shown without its required disclosures is a governance failure, not a minor presentation issue. It must be corrected (new record, §6.4) and, if users acted on it, assessed under the incident process (`SECURITY_REQUIREMENTS.md` §12).

## 5. Investment risk warnings and recommendation governance

### 5.1 Risk warnings (required content, plain language)

The following risks must be warned about wherever recommendations, forecasts, or valuations appear (wording in §7 is the DRAFT UI text; this section states the substance that wording must convey):

- **Capital risk:** Investing in listed equities can lose money, including loss of invested capital. Past price movements do not predict future movements.
- **Volatility and liquidity risk:** PSX prices can move sharply, including overnight gaps and circuit moves; thinly traded symbols may be difficult to buy or sell at the shown price, and the shown price may be stale.
- **Model risk:** Scores, forecasts, and valuations are model outputs with assumptions that may be wrong. Different assumptions give different results (hence ranges, not points).
- **Data risk:** Outputs depend on data that may be stale, incomplete, conflicting, or (for fundamentals/macro) currently UNVERIFIED. An output built on limited data is limited evidence.
- **Concentration and sector risk:** Single-company and single-sector exposures carry risks that a company view alone does not capture.
- **No personalisation:** Outputs are general information based on the stated inputs. They do not consider any individual user's financial situation, goals, risk tolerance, or tax position, and they are not personalised investment advice.

### 5.2 Recommendation governance — evidence, uncertainty, audit

A recommendation (BUY / HOLD / SELL / WATCHLIST as a *system* output — distinct from a user's own bookmark list) may be issued ONLY when ALL of the following hold:

1. **Evidence trail complete.** The company view passes all applicable data-quality gates (`ANALYTICS_SPECIFICATION.md` §5); the health score (when required by the recommendation rule) is gate-passed with its version and sub-scores; forecasts/valuations cited (if any) are gate-passed with intervals/ranges. The full trail is stored (`ANALYTICS_SPECIFICATION.md` §10).
2. **Uncertainty shown.** The recommendation displays: its evidence list, its uncertainty (missing blocks, stale inputs, interval widths, sensitivity ranges, model limits), and its probabilistic framing. A recommendation without uncertainty is invalid.
3. **Rule-based derivation.** The recommendation is derived by a recorded, deterministic recommendation rule (inputs → output mapping, fixed in advance, versioned), not by ad-hoc judgement or LLM choice. The rule version is shown with the recommendation.
4. **Independent Audit.** The recommendation rule and a sample of issued recommendations are subject to audit by the Independent Audit agent (§6). A rule that has not passed audit review must not issue recommendations.
5. **No guarantee language.** See §8 strict rules and §7 DRAFT wording. "BUY" means, at most, "under the stated rule and evidence, this output is categorised as BUY (probabilistic, with the shown uncertainty)" — never "you should buy" as personal advice, and never a promise of gain.
6. **Phase 1 consequence.** With Blocks A/D empty and no full health score available, NO system recommendation may be issued in Phase 1 (`ANALYTICS_SPECIFICATION.md` §8.3). This is the correct, compliant state — not a missing feature to be worked around with weaker evidence.

### 5.3 Not personalised advice — boundary

- The system provides general information and model outputs. It does not provide personalised investment advice, financial planning, tax advice, or legal advice.
- The system must not ask for, or use, a user's holdings, income, risk profile, or financial goals to tailor a recommendation in Phase 1 (no such personalisation is specified or approved). If a later phase proposes personalisation, it requires its own specification, consent design, and governance review — and it does not retroactively convert Phase 1 outputs into advice.
- Any user-facing text that could be read as "you should…" must be rewritten into output language ("this output is categorised as… under [rule], with [uncertainty]") or removed.

### 5.4 Conflicts and incentives (disclosure)

- Any commercial relationship, sponsorship, or incentive that could affect which companies, sectors, or outputs are featured must be disclosed in the same view. In Phase 1, no such relationship is approved or assumed — if one ever arises, non-disclosure is a governance failure.
- The system must not prioritise, promote, or suppress a company because of any undisclosed relationship. Ranking/sorting rules (e.g. by score) must be stated where a ranked list is shown, with the score version and gate status.

## 6. Model limitations and Independent Audit

### 6.1 Model limitations — summary (detail in companion specs)

| Area | Key limitation (must be disclosed where relevant) |
|---|---|
| Price history | ~5y EOD only; limited regimes; survivorship bias (trading vs listed); adjustment status unverified |
| Intraday | No historical intraday archive; no intraday backtests; current-session VWAP only |
| Fundamentals | Feed UNVERIFIED → Block A, valuation legs, and fundamental forecasts unavailable in Phase 1 |
| Macro | All macro feeds UNVERIFIED → macro block unavailable in Phase 1; macro never silently adjusts scores |
| Technical indicators | Lagging, window-dependent, threshold conventions (e.g. RSI 70/30) are NOT verified PSX signals |
| Forecasts | Price-only methods cannot foresee earnings, policy, or structural breaks; intervals widen with horizon; 6m/12m weakest |
| Valuations | Assumption-sensitive (especially WACC/terminal value); no single method gives a guaranteed intrinsic value; banks need sector-specific methods |
| Scores | Descriptive, not predictive, unless a future validated claim proves otherwise; version-dependent; no partial full-score in Phase 1 |
| LLM interpretation | Explains deterministic outputs only; invents no numbers; local Ollama only; no paid AI APIs |

### 6.2 Independent Audit agent — role and powers

- **Independence.** The Independent Audit agent (and any human auditor acting in that role) holds read-only access (`SECURITY_REQUIREMENTS.md` §5.1), holds no Analyst/Administrator privilege simultaneously, and does not author the outputs it audits.
- **Scope of audit.** Data-quality gates; formula implementations against `FINANCIAL_FORMULAS.md`; scoring weights/thresholds/versions; forecast methods, validation windows, and coverage; valuation assumptions, peer sets, and sensitivity ranges; recommendation rules and issued recommendations; disclosure presence (§4); trading-absence (§8 / `SECURITY_REQUIREMENTS.md` §9.6); and audit-trail completeness.
- **Audit triggers.** Scheduled review (cadence fixed at implementation); any rule/weight/assumption change; any incident (§12 in `SECURITY_REQUIREMENTS.md`); any user complaint about a financial output; and before any new output type becomes user-facing.
- **Audit outcomes.** Pass; pass with corrections (corrections tracked to closure); or fail/block (output type or rule must not be user-facing until corrected and re-audited). A fail/block on a recommendation rule suspends that rule's recommendations.
- **Audit records.** Findings, evidence examined, outcome, and corrective actions are stored immutably and are readable by the Auditor role. Audit records are not edited after the fact — follow-ups are new records.

### 6.3 Testing as governance (not just engineering)

Testing strategy is defined in each companion spec (§10/§11) and in `SECURITY_REQUIREMENTS.md` §13. Governance requires that: test definitions exist before implementation claims; no "passed" claim is made without actual test runs referenced; and negative tests (withheld-with-reason in Phase 1 conditions) are treated as first-class passing behaviour, not as failures to be fixed by weakening gates.

### 6.4 Corrections — how errors are fixed without rewriting history

1. **New record, never overwrite.** A corrected score/forecast/valuation/recommendation is a NEW stored record referencing the original record ID, the reason for correction, the actor, and the timestamp (PKT). The original remains in history.
2. **User-facing correction notice.** If the original was shown to users, the correction is shown to affected users (or, for broadly shown outputs, in the same place the original appeared) with what changed and why — in plain language, without minimising language ("small error" for a material change is prohibited).
3. **Coverage/statistics integrity.** Corrected forecasts remain in actual-vs-predicted statistics under their original values unless the correction was due to a data error in the stored inputs themselves — in which case both the original and corrected evaluations are retained with reasons. Deleting misses is falsification (§8).
4. **Root-cause and prevention.** Every material correction triggers a root-cause note and, where needed, a specification or test update — otherwise the same error recurs and governance has failed.

## 7. Required disclaimer wording — DRAFT text for the UI (labelled DRAFT, not legal advice)

> **IMPORTANT: The text below is DRAFT wording for UI display. It is NOT legal advice, has NOT been legally reviewed, and must be reviewed by qualified legal counsel before any public or user-facing use. Do not present it to users as final legal text until that review is recorded.**

**DRAFT — General financial information disclaimer (to appear on every company view, score, forecast, valuation, and recommendation view):**

> This information is general information only. It is not personalised investment advice, financial planning advice, tax advice, or legal advice, and it does not consider your financial situation, goals, or risk tolerance. Scores, forecasts, and valuations are model outputs based on the stated sources, dates, and assumptions shown with them. They are probabilistic and uncertain — they are not guarantees, promises of return, or predictions of what will happen. Past price movements do not predict future movements. Investing in listed equities can lose money, including loss of invested capital. Prices shown may be stale, and thinly traded securities may not be tradeable at the shown price. Before making any investment decision, consider seeking independent, qualified financial advice and verifying the information from primary sources. [DRAFT — not legal advice.]

**DRAFT — Forecast-specific addition (to appear on every forecast view, alongside the general disclaimer):**

> This forecast shows a range of possible outcomes (intervals) for the stated horizon, based on the stated method and historical data. The true outcome may fall outside even the widest interval shown. Longer horizons are more uncertain than shorter ones. This forecast is not a recommendation to buy or sell. [DRAFT — not legal advice.]

**DRAFT — Valuation-specific addition (to appear on every valuation view, alongside the general disclaimer):**

> This valuation is an estimate under the stated assumptions. Different assumptions give different values, as shown in the sensitivity range. No single valuation method gives a guaranteed intrinsic value, and a valuation that differs from the market price does not by itself mean the market price is wrong or that you should trade. This valuation is not a recommendation to buy or sell. [DRAFT — not legal advice.]

**DRAFT — Recommendation-specific addition (to appear on every system recommendation, alongside the general disclaimer):**

> This BUY / HOLD / SELL / WATCHLIST categorisation is a probabilistic output of the stated rule, based on the evidence and uncertainty shown with it. It is not a guarantee, not a promise of return, and not personalised advice to buy, sell, or hold any security. [DRAFT — not legal advice.]

**Display rules for disclaimers:** Disclaimers appear in the same view as the output (not only on a separate terms page), in readable size/contrast, without requiring the user to expand a hidden section to see that uncertainty exists. A disclaimer hidden behind a collapsed section, a tooltip-only disclosure, or a separate page the user never visits does not satisfy §4.

## 8. Strict rules list (binding — violation blocks the output)

1. **No guaranteed returns.** No output, text, or marketing claim may guarantee, promise, or imply certainty of returns, profits, price targets, or outcomes. Words such as "guaranteed", "certain", "will [gain/rise]", "safe bet", and "risk-free" (for equities) are prohibited in financial outputs.
2. **No fabricated data.** No value may be presented as sourced/verified when it is estimated, hand-copied without provenance, recalled by an LLM, or taken from an UNVERIFIED feed without its UNVERIFIED label. Missing data is shown as missing with its reason.
3. **No unsupported forecasts.** No forecast without a named method, model version, training window, horizon, origin, and quantified intervals (§5 in `FORECASTING_SPECIFICATION.md`) may be shown.
4. **No unauthorised trading.** No trade may be executed, ordered, scheduled, or auto-triggered by the system initially (§9 below; `SECURITY_REQUIREMENTS.md` §9). No output is a trade instruction.
5. **No unverified recommendations.** No BUY / HOLD / SELL / WATCHLIST system recommendation without a complete evidence trail, shown uncertainty, a recorded rule version, and audit review (§5.2) may be issued. In Phase 1, no system recommendation may be issued at all.
6. **No concealed uncertainty.** Intervals, ranges, sub-scores, missing blocks, stale/conflict flags, and limitations must be shown with the output. Narrowing, averaging away, or hiding uncertainty to make an output look more precise or confident is prohibited.
7. **No unauthorised commercial redistribution.** Market data, fundamental data, derived analytics, scores, forecasts, and valuations must not be redistributed commercially, republished in bulk, or sold without explicit authorisation naming the data, the recipient, and the terms. Internal audit storage and user-facing display to the system's own users (under the system's own terms) are not commercial redistribution; bulk export, API resale, and third-party republication are, and they require separate approval.
8. **No silent estimation.** Never estimate silently: no imputed inputs, no filled gaps, no assumed rates, no peer substitutions, no prior-period values relabelled as current — in any calculation, score, forecast, or valuation.
9. **No LLM-invented numbers.** No LLM output may create, adjust, or replace a numerical financial result. LLM interpretation is labelled, cites deterministic values exactly, and cannot write to financial stores (`FORECASTING_SPECIFICATION.md` §8.3).
10. **No rewriting history.** Stored forecasts, valuations, scores, and recommendations are immutable; corrections are new records (§6.4). Deleting misses, backdating re-issues, or editing audit logs is falsification.

## 9. Trading restrictions — system must NOT execute real trades initially (EXPLICIT)

Stated here in full so this document alone cannot be misread as permitting trading:

1. The system must NOT execute real trades initially. No broker connection, order API, order submission, auto-trading, algo-trading, or scheduled-order capability exists in Phase 1 or is authorised by this document.
2. No score, forecast, valuation, or recommendation is a trade instruction and must never be formatted, transmitted, or interpreted as one.
3. Paper/hypothetical illustrations, if ever added in a later phase, must be labelled `hypothetical — not a trade, not a profit claim` and must follow the backtesting discipline of `FORECASTING_SPECIFICATION.md` §7. They are not executed trades.
4. No brokerage, bank, card, or trading credential is collected, stored, or requested in Phase 1. Any such request under this project's name is unauthorised and must be reported as a critical incident (`SECURITY_REQUIREMENTS.md` §12.7).
5. Any future trading capability requires: separate explicit approval naming broker, account, order types, limits, and audit controls; its own governance and security specifications; and Independent Audit review — none of which is granted here.
6. Discovery of an execution path in a Phase 1 build is a blocking audit finding (`SECURITY_REQUIREMENTS.md` §9.6).

## 10. Phase 1 governance status — what is true right now

- **Governed and specified:** Formulas, analytics combination, scoring procedures, forecasting methods, valuation methods, security controls, disclosures, strict rules, audit role, correction procedure, and DRAFT disclaimer wording — all in this Phase 1 document set.
- **NOT yet true (and must not be claimed):** No implementation exists; no test has passed; no audit has been performed; no score, forecast, valuation, or recommendation has been issued; no fundamental/macro feed is verified; no legal review of the DRAFT disclaimer has occurred; no trading capability exists or is approved.
- **Correct Phase 1 user-facing state:** Company views show technical measures (where gates pass) with fundamental/macro blocks empty and reasons stated; no full health score; no system recommendation; no valuation; no forecast — unless a future, approved implementation step within a later phase satisfies every gate, validation, and audit rule in this document set. Withholding is compliance, not incompleteness.

---

*End of FINANCIAL_GOVERNANCE.md — Phase 1 specification only. The disclaimer text in §7 is DRAFT, not legal advice, and has not been legally reviewed. No advice, recommendation, forecast, valuation, or price is contained in this document.*
