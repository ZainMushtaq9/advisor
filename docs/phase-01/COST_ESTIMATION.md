# PSX Intelligence AI — Cost Estimation (PKR 0 Absolute)

> **Budget rule: PKR 0 absolute.** No paid APIs, subscriptions, hosting,
> databases, storage, monitoring, or AI services in any phase or scenario.
> Every figure below is labelled **VERIFIED** (with source),
> **ESTIMATE** (with basis and range), or **UNVERIFIED** (with the check
> needed). No price is invented. Where a free solution cannot satisfy a
> requirement, the limitation is documented and scope is reduced or
> deferred — **no paid alternative is introduced** as the solution.
>
> **External operating expenses.** Local hardware, electricity, and
> internet are EXTERNAL operating expenses. They are disclosed here and
> are **never called free**. Their amounts depend on the user's existing
> hardware, tariff, and connection, which are not in the verified record
> for this project — so no PKR amount is stated for them (UNVERIFIED, see
> below). "Zero-budget" in this document means zero project spend on
> software, data, hosting, and services — not zero cost of running a computer.

## Labelling key

- **VERIFIED** — confirmed in the 2026-11-04 starting condition or in a
  cited free licence (MIT for `psx-dps` / `psxdata`).
- **ESTIMATE** — arithmetic or reasoning from a stated basis, given as a
  range, to be replaced by measured actuals in Phase 30's handover.
- **UNVERIFIED** — cannot be stated without a check that has not been done;
  the check is named. Never treat an UNVERIFIED figure as a budget line.

## Cost categories (all three scenarios)

| Category | What it covers | Project cost in all scenarios |
|---|---|---|
| Free software | Python, Node, SQLite, stdlib, free-licence libraries, version control tooling already available locally | **PKR 0 — VERIFIED** as zero licence cost for the named free tools in the verified baseline; any new library must pass the Phase 02 licence check before use |
| Free public data | `psx-dps` (MIT, zero deps, no API key), `psxdata` (MIT, PyPI alpha) | **PKR 0 — VERIFIED** (no API key, MIT licence, per 2026-11-04 record) |
| Local computing | Developer's own machine running local code | **PKR 0 project spend; hardware/electricity/internet are EXTERNAL — UNVERIFIED amount** (see external-expenses section) |
| Hosting | Any server hosting for an online deployment | **PKR 0 only where a legitimate free service is verified at deployment time (Scenario 3, conditional); otherwise PKR 0 because the component stays local (Scenarios 1–2)** |
| DB hosting | Hosted database service | **PKR 0 — no hosted DB is used; SQLite runs locally** (Scenarios 1–2); Scenario 3 uses a hosted DB only if a legitimate free service is verified, otherwise local |
| AI inference | AI forecasting / agent work (Phases 18, 25, 26) | **PKR 0 project spend — free/local options only; any paid AI service price is UNVERIFIED and, in any case, not used** |
| Storage | Local disk for DB + logs + dossiers | **PKR 0 project spend (local disk, already owned); capacity is an ESTIMATE in `RESOURCE_REQUIREMENTS.md`** |
| Monitoring | Scheduling / freshness / health monitoring (Phase 27) | **PKR 0 — local OS scheduler + local logs; no paid monitoring service** |
| Optional licensed market data | Any licensed/redistributed data beyond free sources | **NOT PURCHASED. Cost: not stated, not budgeted, not a line item — the requirement is documented as a limitation instead (see `FREE_VS_PAID_COMPARISON.md`)** |

## Scenario 1 — Zero-budget local development

**Definition.** Build Phases 01–28 on a developer machine only: local
repository, local SQLite, local collectors, local dashboard. No online
deployment, no subscription, no external service of any kind.

| Item | Cost | Label / basis |
|---|---|---|
| Software (Python 3.12.3, Node v24.22.1, SQLite, stdlib) | PKR 0 | VERIFIED (verified baseline tools; free licences) |
| Data (`psx-dps`, `psxdata`) | PKR 0 | VERIFIED (MIT, no API key) |
| Hosting / DB hosting / monitoring / AI services | PKR 0 (not used) | VERIFIED by design (nothing external is provisioned) |
| Storage (local disk) | PKR 0 project spend | ESTIMATE capacity: see `RESOURCE_REQUIREMENTS.md` (full-market EOD store in the low hundreds of MB range, plus indexes) |
| Hardware / electricity / internet | External expense, amount not stated | UNVERIFIED — check needed: user's hardware ownership, electricity tariff, internet plan; do not call this free |
| **Scenario 1 project total** | **PKR 0** | Plus external operating expenses (UNVERIFIED amount, disclosed, not in the total) |

**Limitations in this scenario (documented, not solved by purchase):**
no public online access to the dashboard; no hosted DB; AI capability
limited to free/local options; historical intraday unavailable; gated
sources (Phases 08, 09, 10, 14) remain gated.

## Scenario 2 — Zero-subscription local operation

**Definition.** Run the built system ongoing on local hardware: scheduled
refresh (Phase 07), dossier runs (Phase 26), monitoring (Phase 27), local
dashboard (Phase 28), with no subscription of any kind — no monthly fee,
no per-use service, no hosted component.

| Item | Cost | Label / basis |
|---|---|---|
| All software / data / DB / monitoring / AI | PKR 0 | As Scenario 1 (VERIFIED for named free tools/data; free/local AI only) |
| Subscriptions | PKR 0 (none exist) | VERIFIED by design (no subscription is created) |
| Ongoing data refresh requests | PKR 0 | VERIFIED for the free sources (no API key); request counts are ESTIMATE/UNVERIFIED in `RESOURCE_REQUIREMENTS.md` (volume, not price) |
| Hardware / electricity / internet (ongoing) | External expense, amount not stated | UNVERIFIED — check needed: user's ongoing tariff/plan and machine runtime; a machine left running for scheduling consumes electricity, which is not free |
| **Scenario 2 project total (recurring)** | **PKR 0 per month** | Plus external operating expenses (UNVERIFIED amount, disclosed, not in the total) |

**Limitations:** same as Scenario 1, plus: scheduling depends on the
local machine being on at scheduled times (a documented operational
limitation — if the machine is off, a refresh is missed and flagged stale,
not silently backfilled as if on time, unless a catch-up run is defined
in Phase 27).

## Scenario 3 — Zero-cost online deployment (conditional only)

**Definition.** Deploy some or all of the system online **ONLY where a
legitimate free service is verified as available at deployment time**
(Phase 29–30 decision point). This scenario is not a promise of a free
full-stack deployment.

**Permanent-free-hosting caveat (applies to every component in this
scenario).** No free tier is guaranteed permanent. A provider may change
terms, reduce limits, or withdraw a free tier. Therefore:
(a) every online component must have a documented local fallback
(Scenario 2); (b) the deployment decision record (Phase 30) must name
the service, its free terms as verified on that date, and its limits;
(c) if the free service disappears, the system reverts to local operation
— it is never "saved" by purchasing a paid tier.

| Component | Zero-cost online treatment | Label / basis |
|---|---|---|
| Static frontend / documentation | May use a legitimate free static-hosting service **if verified at deployment time** (terms, limits, and attribution checked then) | UNVERIFIED until Phase 30 verification — no specific service or term is asserted here |
| Backend / API / collectors | Online only if a legitimate free service covering compute + scheduling is verified at deployment time; otherwise stays local | UNVERIFIED until Phase 30 verification |
| Database | Online only if a legitimate free DB service is verified at deployment time; otherwise SQLite stays local | UNVERIFIED until Phase 30 verification |
| Monitoring / AI | Local/free only, as Scenarios 1–2; no paid service introduced to make online deployment work | VERIFIED by design (constraint, not a price) |
| **Scenario 3 project total** | **PKR 0 for components covered by a verified free service; PKR 0 (local) for components not covered** | Plus external operating expenses (UNVERIFIED amount) |

**If no legitimate free service covers a component, that component stays
local and the limitation is documented.** The system is still complete
under Scenario 2. An online deployment that requires a paid service to
function is not a Scenario 3 deployment — it is out of budget and is not
proposed.

## Estimate summary (all figures labelled; detail in RESOURCE_REQUIREMENTS.md)

| Quantity | Figure | Label / basis |
|---|---|---|
| Project spend, Scenarios 1–2 | PKR 0 (one-off and recurring) | VERIFIED by design + VERIFIED free tools/data |
| Project spend, Scenario 3 (covered components) | PKR 0 | Conditional on Phase 30 verification (UNVERIFIED until then) |
| Hardware / electricity / internet | Amount not stated | UNVERIFIED — user's tariff/plan/hardware; never called free |
| Full-market EOD store size | Low hundreds of MB incl. indexes (range in RESOURCE_REQUIREMENTS.md) | ESTIMATE — arithmetic from ~496 symbols × ~1,250 trading days (see that file) |
| Daily EOD volume | ~496 rows/day (trading universe) | ESTIMATE — 1 row per trading symbol per trading day; actuals measured by Phase 06/07 reports |
| Backfill API requests | Not stated as a single figure | UNVERIFIED — depends on source request granularity, not measured in Phase 1 |
| AI token usage | Ranges in RESOURCE_REQUIREMENTS.md (counts only, no price) | ESTIMATE (counts) — price UNVERIFIED and not used, since only free/local AI is permitted |
| Any paid-service price | Not stated | UNVERIFIED and out of scope — no paid service is budgeted or proposed |

## What would change these figures (and what would not)

- **Would change them:** a measured backfill report (Phase 06) replacing
  EOD-volume estimates with actuals; a Phase 30 verification naming a
  specific free service and its limits for Scenario 3; a user's own
  electricity/internet bill providing the external-expense amount.
- **Would not change them:** a vendor price seen in an advertisement or
  an unverified web page — such a figure is not entered into this budget
  without verification, and even if verified it is not adopted, because
  the budget is PKR 0 absolute.

## Budget control rule (all phases)

Before any phase introduces a new tool, library, source, or service, it
must pass: (1) licence check (free, Phase 02 policy); (2) PKR 0 check
(no payment, subscription, or paid tier required for the needed use);
(3) fallback check (what happens if the free service changes/withdraws).
Failure on any check means the item is not adopted and the limitation is
documented. Phase 24 audits this rule; Phase 30 re-verifies it at rollout.
