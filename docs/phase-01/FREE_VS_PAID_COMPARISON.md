# PSX Intelligence AI — Free Coverage, Free Gaps, and the No-Purchase Decision Rule

> **Budget rule: PKR 0 absolute.** This document compares what free
> resources cover against what they do not cover. It does **not**
> introduce a paid alternative: where free cannot satisfy a requirement,
> the limitation is documented, scope is reduced or deferred, and the
> requirement stays open. No paid API, subscription, hosting, DB, storage,
> monitoring, or AI service is recommended, specified, or priced here.
> No price, vendor, or paid capability is stated as fact.
>
> Terminology: "free" below means free-licence / no-API-key / locally
> runnable as verified for the named items. Local hardware, electricity,
> and internet are EXTERNAL operating expenses — disclosed, never called
> free (see `COST_ESTIMATION.md`).

## What free sources cover (VERIFIED, 2026-11-04)

| Need | Free coverage | Source / label |
|---|---|---|
| PSX EOD history (~5 years) | Covered for the trading universe, subject to the backfill report's actual coverage | `psx-dps` — VERIFIED (MIT, zero deps, no API key, ~5y EOD) |
| Daily OHLCV + live snapshots | Covered as daily rows and snapshot values | `psxdata` — VERIFIED (MIT, PyPI alpha 0.1.0a1, daily OHLCV + live snapshots ONLY) |
| Today's ticks / snapshot view | Covered as today's values from a verified source | `psx-dps` today's ticks — VERIFIED as a source property; freshness-labelled, not real-time-guaranteed |
| Symbol universe + sectors | ~496 trading vs ~1029 listed; 38 sectors | VERIFIED counts (2026-11-04) |
| Local database, backend, analysis | Fully covered locally | Python stdlib, SQLite, free-licence libraries passing the Phase 02 licence check — VERIFIED for the named free tools |
| Scheduling, monitoring, logging | Fully covered locally | Local OS scheduler + local logs — VERIFIED by design (no external service needed) |
| AI-assisted explanation/forecasting | Covered only to the extent a free/local AI option satisfies the task | Free/local options only — the specific option and its capability are recorded by the implementing team; no paid option is introduced if it falls short (see gaps) |

## What free sources do NOT cover (gaps — documented, not solved by purchase)

| Gap | Consequence | Handling (no purchase) |
|---|---|---|
| **Historical intraday archive** | No intraday history, no intraday backtest, no intraday chart history | Scope limit: all analysis, forecasting, and backtesting are EOD-only (Phases 06, 12, 17, 20). Today's ticks are snapshots, not history, and are never presented as an archive. |
| **Guaranteed real-time feed** | No guaranteed real-time prices, no real-time alerts on a guaranteed latency | Snapshots are freshness-labelled with retrieval timestamps; stale data is flagged; no real-time claim is made anywhere (Phases 07, 27, 28). |
| **Licensed redistribution** | Free-source data may not be redistributable beyond its licence terms; redistribution rights are per-source and must be checked, not assumed | Licence/attribution register (Phase 29); any use a licence forbids is removed, not worked around by acquiring a licence. |
| **Financial statements (machine-readable)** | No verified machine-readable statement source is asserted | Phase 08 gated: framework + checklist first; downstream phases work without statement inputs, with gaps labelled. |
| **Corporate announcements (machine-readable)** | No verified machine-readable announcement source is asserted | Phase 09 gated: framework + checklist first; downstream phases work without announcement inputs. |
| **Macroeconomic series (machine-readable)** | SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use UNVERIFIED | Phase 10 gated per series: framework + checklist first; analysis works on verified PSX data alone. |
| **News (lawfully usable, machine-readable)** | No verified news source is asserted | Phase 14 gated: framework + taxonomy + checklist first; downstream phases work without news inputs. |
| **Guaranteed free online hosting (permanent)** | No free tier is guaranteed permanent; terms/limits can change or be withdrawn | Permanent-free-hosting caveat: online deployment (Scenario 3) only where verified at deployment time, with local fallback always available (Phases 29–30). |
| **Paid-grade AI capability** | A free/local AI option may be slower or less capable than a hypothetical paid model on some sub-tasks | Reduce scope or frequency of that sub-task, or defer it (Phases 18, 25–27 scaling triggers). Capability limits are documented, not solved by purchase. |
| **Official PSX API** | No official PSX API is asserted (VERIFIED: no official PSX API in the 2026-11-04 record) | Work through the verified free sources only; do not invent or assume an official endpoint. |

## What a paid option would theoretically add — deliberately NOT specified

This section exists only to record why it is empty. Under the PKR 0
absolute budget, this roadmap does not specify, recommend, compare prices
for, or select any paid API, data licence, hosting tier, database service,
monitoring service, or AI service. Naming a paid option — even as a
"theoretical" alternative — would invite the exact spend this budget
forbids and would risk presenting an unverified price or capability as
fact. Therefore:

- No paid vendor, product, tier, or price appears in this document.
- No "if free fails, buy X" fallback appears in any phase.
- The only fallback for a free gap is: document the limitation, reduce
  scope, defer the requirement, or use the local fallback (Scenario 2).

If a future, separately authorised task ever revisits the budget, that
task — not this document — would need to verify a specific paid option's
terms and price from its official source and obtain explicit user approval.
This roadmap does not grant that authorisation.

## Decision rule: paid only after documented proof — as applied under PKR 0

The original decision rule ("paid only after documented proof that free
is insufficient, with user approval") is applied here under the stricter
revised budget as follows:

1. **Prove insufficiency with evidence, not assertion.** A free gap is
   recorded only after the relevant phase's framework + checklist work
   (Phases 08, 09, 10, 14) or measurement (Phases 27, 29) demonstrates it
   on the actual system — not from a general claim that "free is limited".
2. **Document the limitation.** The gap, its consequence, and the
   reduced/deferred scope go into the phase report, the acceptance
   matrix (as UNVERIFIED or open item), and Phase 30's open-items register.
3. **Do not introduce a paid alternative.** Steps 1–2 end the decision
   under this budget. No purchase is proposed, specified, or budgeted.
4. **User approval is required for any future change to this rule.**
   Changing the PKR 0 rule itself — not just a single purchase — would
   require a separate explicit user decision outside Phase 1, which this
   roadmap does not seek or assume.

## Free-resource checklist per phase (summary; detail in PHASE_BREAKDOWN.md)

- Phases 01–07, 11–13, 15–17, 19–23, 25–30: free/local resources suffice
  for the specified scope (verified sources + stdlib + SQLite + local
  tooling), subject to the gaps above.
- Phases 08, 09, 10, 14: free/local resources suffice for framework +
  checklist; data ingestion depends on a future verification, not on a
  purchase.
- Phase 18, 25, 26: free/local AI only; capability limits are documented
  limitations, not purchase triggers.
- Phase 30: online deployment only via a verified legitimate free service,
  with the permanent-free-hosting caveat and local fallback.

## Eulerpool note (VERIFIED, 2026-11-04)

Eulerpool has NO PSX coverage, is vendor-only, and no paid API is approved.
It is therefore not a free source, not a gap-filler, and not an alternative
for any phase in this roadmap. It is recorded here so no later phase
re-introduces it as a candidate without re-verifying coverage from scratch.
