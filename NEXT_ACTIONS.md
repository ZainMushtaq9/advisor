# PSX Intelligence AI — Next Actions (after Phase 1 docs)

- **Date:** 2026-11-04
- **Phase:** Phase 1 of 30 — documentation only
- **Author:** Team 1 — Repository Audit + Product Requirements
- **Budget:** PKR 0 absolute. **Trading:** system must NOT execute real trades initially. **Stop rule:** STOP AFTER PHASE 1.

## 1. The rule in one paragraph

**Do NOT start Phase 2 until the Phase 1 audit passes.** The immediate next actions are: (1) coordinator independent audit, (2) fix loop, (3) checkpoint — and only then (4) Phase 2 *planning* only. Phase 2 planning is not Phase 2 building: no code, no install, no live collection run, no sign-up, no purchase, no broker connection, and no deployment may begin on the strength of Phase 1 documents alone. Any action below that says "verify" means a documented, read-only-until-approved check with a dated record — not a bulk collection, not a purchase, and not a claim upgrade without evidence.

## 2. Step 1 — Coordinator independent audit (workflow stage 9)

**Owner:** coordinator (must NOT be Team 1 — Team 1 cannot audit its own work as "passed").
**Inputs to audit:** all 8 Team 1 files + sibling Phase 1 documents in `docs/phase-01/` + the reference scaffold (read-only) + this file's criteria.
**Output required:** a dated audit record listing each criterion as PASS / FAIL / DEFERRED-WITH-REASON, plus a finding-by-finding fix list. A verbal "looks good" is not an audit record.

Audit criteria (all must be checked; any FAIL blocks checkpoint until fixed or formally deferred):

| # | Criterion | How to check |
|---|---|---|
| A1 | All 21 modules specified in `PRODUCT_REQUIREMENTS.md` | Count modules §3.1–§3.21; confirm each has objective, users, inputs, outputs, features, interactions, data/APIs, backend, DB, AI-agent, external-integration, security, testing, and acceptance criteria. Missing section = FAIL. |
| A2 | 8-group → 21-module mapping is present and does not lose scope | Check `PRODUCT_REQUIREMENTS.md` §1.3; confirm every original group A–H maps to at least one numbered module and no group content is dropped without a reason. |
| A3 | PKR 0 throughout | Search all Team 1 files + sibling files for any paid API, subscription, hosting, DB service, storage, monitoring, or AI/LLM subscription assumed as available. Any assumed paid service without a separate approval record = FAIL. "Free tier" without limits/terms documented = FAIL (see D3 in `DEVELOPMENT_LOG.md`). |
| A4 | No real trades | Confirm the no-trades statement in `PROJECT_STATUS.md`, this file, audit, workflow, and requirements (modules 13/15); confirm no broker/order/execution specification exists anywhere. Any execution wiring = FAIL. |
| A5 | No Phase 2 start smuggled in | Confirm no Team 1 file authorises building, installing, collecting at scale, signing up, or deploying; confirm sibling files do not contradict the stop rule without a flagged conflict. |
| A6 | UNVERIFIED labelling honest | Spot-check data claims against §4 below: any UNVERIFIED item presented as verified/covered/working = FAIL. Any invented endpoint, price, or capability = FAIL. |
| A7 | Sibling-file integrity | Confirm Team 1 did not modify sibling files, `~/workspace/*.md`, or `~/workspace/psx-data-collection/` (compare timestamps/content hashes if available; at minimum confirm Team 1's file list matches its 8 files and no other file was written by Team 1). |
| A8 | Internal consistency | Cross-check: module count (21), forecast horizons (1d/1w/1m/3m/6m/12m), provenance/PKT/stale/missing/conflict rules, probabilistic-only language, and file paths are the same across Team 1 files. Any contradiction = finding. |
| A9 | Cross-document consistency (Team 1 vs siblings) | Compare sibling architecture/database/agent/formula/roadmap/tech-stack documents against Team 1 requirements: conflicting module counts, conflicting storage assumptions, conflicting cost assumptions, or "implemented" wording for document-only designs must be listed as findings. Team 1 does not resolve these by editing siblings. |
| A10 | Starting-condition reconciliation | Decide the record for the "no folder exists" wording vs the pre-existing folder fact (`REPOSITORY_AUDIT.md` §2): correct the starting condition, or record why the original wording stands despite the listing. An unaddressed contradiction = FAIL. |
| A11 | No invented delivery | Confirm no file claims a passed project test suite, a live service, full-market coverage, a hosted URL, or a delivery date/time. Team 1 promises no delivery time; any such promise elsewhere = finding. |
| A12 | Legal-disclosure presence | Confirm legal disclosures are specified (public site, recommendations/forecasts, data-licence limits) in `PRODUCT_REQUIREMENTS.md` Module 1 and the global rules, with redistribution explicitly not authorised. Missing disclosure spec = finding. |

## 3. Steps 2–4 — Fix loop, checkpoint, then Phase 2 planning only

### Step 2 — Fix loop (workflow stage 10)
- **Owner:** the team owning each finding (Team 1 fixes Team 1 findings; sibling teams fix sibling findings; coordinator fixes cross-document findings).
- **Method:** edit the affected file(s) only; update `TASK_TRACKER.md` and `WORKFLOW_STAGE_TRACKER.md` to reflect the fix; do not edit another team's file to "fix" a conflict — raise it as a finding for that team's fix loop.
- **Disposition rule:** every finding ends as FIXED (with file + change noted) or DEFERRED-WITH-REASON (dated reason + the phase/check that will revisit it). No finding may be silently dropped.

### Step 3 — Checkpoint (workflow stage 11)
- **Owner:** coordinator.
- **Output:** a dated checkpoint note stating: Phase 1 outcome (pass/fail), files frozen, open/deferred items with owners, and the single next authorised step. Without this note, Phase 2 planning has not been authorised — regardless of how complete stages 1–8 look.
- **Checkpoint must restate:** docs only; no code/DB/deployment; PKR 0; no real trades initially; UNVERIFIED items still open (see §4).

### Step 4 — Phase 2 planning only (after checkpoint)
- Planning means: sequencing, dependency ordering, verification-check planning (§4), storage/cost/terms decisions at PKR 0, and test-strategy refinement — all still following the 11-stage workflow per task.
- Planning does NOT mean: writing application code, installing packages into a project environment, running a live collection, connecting a broker, signing up for a service, or deploying anything. Each of those needs its own phase authorisation beyond "planning".
- If Phase 2 planning discovers that a required component cannot be built at PKR 0, that is recorded as a blocker with the "free insufficient" evidence — it is not resolved by quietly assuming a paid service.

## 4. Per-UNVERIFIED-item verification checks (do after audit pass; each check follows the 11-stage workflow for its own scope)

Each check states: what to check, how (read-only first), and what evidence upgrades the status. Until the evidence exists, the status stays UNVERIFIED. No check authorises bulk collection, purchase, or sign-up by itself — if a check needs an account, key, or payment, stop and get separate approval first.

| ID | UNVERIFIED item | Verification check (in order) | Evidence that upgrades status |
|---|---|---|---|
| V1 | `psx-dps` as a working integration | Read-only first: re-read its public README + licence; then, only under Phase 2 planning authorisation, a small, named-symbol sample run (e.g. OGDC, as in the scaffold example) in an isolated environment, comparing snapshot/quote/EOD against the portal page itself; record node-404 behaviour, rate-limit behaviour, and timestamp/provenance handling. | Dated run record: symbols, endpoints/fields actually returned, source timestamps (PKT), stale/conflict handling observed, failures observed. README claim alone does NOT upgrade this. |
| V2 | `psxdata` as a working integration | Same pattern as V1: README + licence read; then a small sample run (same symbols as V1 where possible) for OHLCV + live snapshot; explicitly confirm the README's "daily + live snapshots only, no historical intraday archive" limit in practice. | Dated run record + a written confirmation (or correction) of the intraday limit. Alpha-version change risk noted. |
| V3 | Fundamentals claim (`psxdata` + PSX portal financials) | Per-source read: what fields, what companies, what periods, what format; then a small sample (one company, one period) with field-by-field comparison against the company's own published statement/portal page. | Dated sample record naming company, period, fields present/missing, and any mismatch. "Fundamentals claimed" alone does NOT upgrade this. |
| V4 | Announcements completeness (`psx-dps` 224k+ claim) | Read README claim; then a small sample: announcements for one symbol over a short, named window, with PDF URLs checked for reachability (read-only, no bulk download in the check itself unless separately authorised). | Dated sample record: window, count returned, PDF-URL sample result, gaps noted. |
| V5 | SECP machine-use coverage | Read `secp.gov.pk` public pages for filings/company information: is there a documented machine-readable route, a download format, terms of use? Record page + date. No scraping beyond terms. | Dated page record: route/format/terms found, or "no machine-readable route found". |
| V6 | SBP machine-use coverage | Same as V5 for `sbp.org.pk`: interest rates, monetary policy, banking/economic data — route, format, terms, update frequency as stated on the site. | Dated page record as in V5. |
| V7 | PBS machine-use coverage | Same as V5 for `pbs.gov.pk`: CPI, inflation, trade, economic indicators — route, format, terms, frequency as stated. | Dated page record as in V5. |
| V8 | Finance Division machine-use coverage | Same as V5 for `finance.gov.pk`: economic surveys, fiscal information — route, format, terms. | Dated page record as in V5. |
| V9 | World Bank machine-use coverage for this product's needs | Identify the specific indicators the product would actually need (macro context for market outlook/research) BEFORE checking; then check the World Bank's public API/documentation for those exact indicators, terms, and limits. Do not claim "World Bank covers it" in general. | Dated record naming indicators + API/terms/limits found, or "not found for these indicators". |
| V10 | IMF machine-use coverage for this product's needs | Same discipline as V9: named indicators first, then IMF public documentation/terms check. | Dated record as in V9. |
| V11 | FRED machine-use coverage for this product's needs | Same discipline as V9: named series first, then FRED public documentation/terms check (including any account/key requirement — if a key/account is required, that itself is a finding under PKR 0 / no-credentials-in-Phase-1 rules, not a silent pass). | Dated record as in V9, plus key/account finding if applicable. |
| V12 | Listed-company IR sites (per company) | Build the per-company registry first (company → IR URL → statement format → period availability) for a small pilot set; do not generalise from one company to all. | Pilot registry with per-company rows; all other companies remain UNVERIFIED. |
| V13 | Company master registry / full-market coverage | Reconcile counts from V1/V2 (trading symbols vs listed instruments vs tickers) + rename handling (e.g. ENGRO → ENGROH as cited in the scaffold) + sector-count difference (38 vs 37) with a written reconciliation rule; only then mark companies covered one by one in `coverage.json`-style records. | Reconciliation document + per-company coverage rows. No blanket "all companies covered" claim until every row is evidenced. |
| V14 | Historical intraday archive (any route) | Search public documentation for any free, lawful route to historical intraday PSX bars; record the result. If none is found, the status becomes "not available from verified free sources" — a design constraint, not a gap to fill by assumption. | Dated search record + named sources checked. |
| V15 | PSX redistribution / commercial-use licence | Read PSX portal terms + any published licensing information; if terms are unclear, record the exact question to put to PSX / a legal check. Do not proceed to any public republication planning until answered. | Dated terms record + open legal question (if any) with owner. |
| V16 | PKR 0 route for hosting | For each hosting option considered: terms, limits, expiry, card requirement, and what happens at the limit — documented from the provider's own pages. "Free hosting exists" without that record = still UNVERIFIED. Local-only hosting is the baseline comparator. | Dated terms/limits record per option; or a recorded decision to stay local-only. |
| V17 | PKR 0 route for database service | Same as V16 for any server/database service considered, compared against the local file/SQLite-style baseline (local hardware = external operating expense, not "free"). | Dated terms/limits record per option, or local-only decision. |
| V18 | PKR 0 route for monitoring / logging service | Same as V16 for any monitoring/logging service considered, compared against local log files. | Dated terms/limits record per option, or local-only decision. |
| V19 | PKR 0 route for AI/LLM use | For each AI-dependent module, document the zero-cost route that would actually serve it (local model, documented free-tier limits, or graceful degradation with no model) — including what the module shows when no model is available. A module that only works with a paid model = BLOCKED, not "free". | Per-module zero-cost route record + degradation behaviour. |
| V20 | Eulerpool (explicit non-PSX check) | Confirm from Eulerpool's own pages whether PSX-specific coverage is stated. Starting condition says NO PSX-specific coverage was stated. If a later page states it, record the page + date and re-evaluate as a vendor (still no paid approval). If not, the item stays "not a PSX source". | Dated page record. Never upgrade Eulerpool to "PSX source" without that page evidence. |
| V21 | Cross-document consistency (Team 1 vs siblings) | Coordinator re-check after the fix loop: module counts, storage assumptions, cost assumptions, and "implemented" wording aligned across all Phase 1 documents, or remaining conflicts listed as deferred findings with owners. | Updated audit record (stage 9 re-check) + fix-loop dispositions. |

## 5. What NOT to do next (explicit)

- Do NOT start Phase 2 (build, install, collect at scale, sign up, purchase, connect a broker, deploy) before the checkpoint in §3-step 3.
- Do NOT re-contact, re-verify, or re-claim any item in §4 by repeating its README/portal claim louder — only the dated evidence in the right-hand column upgrades a status.
- Do NOT treat draft creation, document creation, or planning as "sent", "scheduled", "live", "covered", or "tested-and-passing".
- Do NOT promise a delivery time for Phase 2. Team 1 promises no delivery time; the coordinator's checkpoint may set planning milestones, but those are not delivery promises for a built system.
- Do NOT execute real trades at any point in the next actions. Trading execution is explicitly out of scope initially and would need a separate, explicit decision beyond Phase 1 — which this document does not grant.

## 6. If the audit fails

- Stay in Phase 1. Return to the fix loop (§3-step 2), fix or formally defer each finding, and re-audit the fixed items.
- Do not "proceed with planning anyway" around a failed criterion. The stop rule exists precisely so a failed audit cannot be bypassed by relabelling build work as planning.
- If a finding cannot be fixed within Phase 1 (e.g. it needs a paid service or a legal answer), record it as BLOCKED with its owner and the approval/answer it needs — that record is a legitimate Phase 1 outcome, not a failure to hide.

## 7. Phase 2 update (2026-11-04, coordinator)

- Phase 2 acceptance: PARTIALLY COMPLETE — see docs/phase-02/PHASE_2_ACCEPTANCE_REPORT.md. Foundation is usable for Phase 3 design; Docker and Playwright verification must happen on a machine with working registry/CDN access, or be explicitly waived.
- Next step only: Phase 3, after a separate instruction AND its own gate check (Phase 2 acceptance report, PostgreSQL, SQLAlchemy/Alembic, migrations, storage, backup, git status).
- Push step: after audit, push verified Phase 2 changes to branch phase-02-repository-foundation in ZainMushtaq9/advisor, verify remote SHA, record in docs/development/GITHUB_PUSH_LOG.md. No force-push, no direct push to main, no merge (NOT MERGED pending separate approval).
- Do NOT start Phase 3, 4, or 5 from this file. Do NOT claim Docker or Playwright verified. Do NOT execute real trades.
