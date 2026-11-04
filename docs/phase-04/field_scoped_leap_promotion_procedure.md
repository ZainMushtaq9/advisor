# Phase 4 — Field-scoped SECP LEAP promotion procedure

Date: 2026-11-04 (Phase 4 revisit, branch `phase-04-sampled-verification`).
Status: PROCEDURE ONLY in this run. No live LEAP query was executed by
this run (see `sampled_verification_plan_2026-11-04.md` for why: live
LEAP search needs a live-browser task, which a generic coordinator
cannot run). No record has been promoted by this procedure yet.

## 1. Why field scope is mandatory

Rule H1 (`backend/app/services/registry/verification.py`) promotes a
whole record to VERIFIED only when evidence from at least two distinct
sources agrees on the normalized name AND at least one source is in
OFFICIAL_SOURCES (`psx_official`, `secp`). The registry's status column
is per-record: it has no field dimension. Promoting a whole record on
a name-only second source would overclaim sector and ticker, which
LEAP never returns. Therefore LEAP evidence is stored as evidence
rows ONLY, and no status is ever changed by this procedure.

## 2. What LEAP returns, and what each field may claim

Source: SECP LEAP public company-name search,
https://leap.secp.gov.pk/#/landing-page (no sign-in, no fee, no
CAPTCHA on the search box itself). Fields returned, and only these:
company/LLP name, CUIN, Incorporation Date, CRO city, status badge.
NO sector, NO ticker/symbol, NO address, NO directors.

| Field | LEAP observation | Claim allowed |
|---|---|---|
| Legal name | INCORPORATED-row name, verbatim | AGREE / DISAGREE / NOT_FOUND against the registry `legal_name` under `normalize_name` (case-fold, punctuation collapsed, `&` = `and`, legal suffixes stripped for the match key only). The stored registry name is never edited by this procedure. |
| CUIN | INCORPORATED-row CUIN (7 digits) | RECORDED ONLY. The DPS snapshot carries no CUIN, so there is nothing for it to agree with. A CUIN is new identifier information, NOT an agreement, and is NEVER written to `company_identifiers` by this procedure. Identifier promotion needs a separate decision and procedure. |
| LEAP status badge | INCORPORATED badge | OBSERVED ONLY. LEAP "INCORPORATED" is not the same concept as DPS "Normal Counter" listing status, so no listing-status agreement is ever claimed. |
| Sector | (not returned) | NOT_VERIFIABLE_FROM_LEAP. Never claimed, never inferred. |
| Ticker | (not returned) | NOT_VERIFIABLE_FROM_LEAP. Never claimed, never inferred. |

## 3. Outcome definitions (per sampled company)

- AGREE: an INCORPORATED row exists whose normalized name equals the
  normalized registry `legal_name`.
- DISAGREE: the search unambiguously identifies the company (single
  candidate, or the operator's recorded selection among candidates)
  but its normalized name differs from the registry `legal_name`.
  This flags a possible registry name error or a LEAP name variant
  beyond normalization. It is recorded, never silently corrected.
- NOT_FOUND: no candidate, or candidates exist but none can be
  identified as the company. Candidates, if any, are listed in the
  note. Ambiguity is folded into NOT_FOUND (conservative): a guess
  is never recorded as a match.

## 4. Duplicate-row rule (recorded, never silently cleaned)

Every found company appears TWICE: one "organization" row with a
garbled year (e.g. 3993) and one INCORPORATED row with the correct
date. The INCORPORATED row is the observation. The duplicate row is
recorded in the evidence note, never hidden, never used as the
observation, and its garbled year is never stored as a date.

## 5. Evidence-row mapping (the only write this procedure allows)

Table `registry_evidence`, one row per sampled company:

- `entity_type` = `company`, `entity_id` = registry company id.
- `source_key` = `secp_leap`. This is DELIBERATE and load-bearing:
  it is not the OFFICIAL_SOURCES key `secp`, so the current
  promotion code (`apply_verification_rules`) can never promote a
  record from LEAP rows alone, even if it were run. The loader never
  calls `apply_verification_rules` in any case.
- `source_record_key` = the CUIN when a company is found, else the
  literal `NOT_FOUND`.
- `observed_name` = the LEAP INCORPORATED-row name verbatim, or NULL
  when NOT_FOUND.
- `observed_sector` = NULL always. LEAP returns no sector; writing
  the registry sector here would fabricate a second-source sector
  observation.
- `collected_at` = the browser observation timestamp (Asia/Karachi).
- `evidence_note` = structured text with: every query wording tried,
  in order, and which wording found the row; both duplicate rows
  (or their absence); CUIN, incorporation date (DD-MM-YYYY as
  shown), CRO city; outcome (AGREE / DISAGREE / NOT_FOUND); and the
  explicit non-claims: CUIN recorded, not agreed; INCORPORATED is
  not DPS listing status; sector and ticker not verifiable from
  LEAP; this row changes no status.

A `data_sources` row for `secp_leap` (display name "SECP LEAP public
company-name search", verification_status UNVERIFIED, terms note:
public search, no sign-in, sampled manual use only, bulk scraping
not approved) is written by the loader on `--commit` if absent.
It is provenance, not a verification claim.

## 6. Status rule (absolute)

`companies.status` and `securities.status` are NEVER changed by this
procedure — not for sampled companies, not for any company. The
sampled result is reported only as a derived summary, e.g.
"X/61 sampled companies LEAP-NAME-AGREED", where LEAP-NAME-AGREED
means: the company has a `secp_leap` evidence row whose
`observed_name` normalizes equal to its registry `legal_name`.
That summary is not a status, not a VERIFIED count, and not a
registry-wide claim. All 470 records stay UNVERIFIED until a
field-scoped promotion model exists in code AND a separate
approval authorizes running it.

## 7. What sampled verification does NOT do

- It does not verify the full 470. Full-registry name verification
  needs either an approved bulk route from SECP or sustained manual
  effort for all 470 (~16–40 hours at 2–5 minutes per company).
- It does not capture GEM (5) or Non-Compliant / Winding-Up (93).
- It does not establish KSE-100 completeness or make any KSE-100
  claim.
- It does not clear the PSX Terms basis for the populated registry.
- It does not promote CUINs to identifiers.
- It does not authorize any new PSX market-data collection.

## 8. Browser execution rules (for the live-query run)

- One query at a time, through the public search box only. No
  sign-in, no account creation. The older SECP eServices route
  (paid Rs. 100 account) is NOT used.
- Suggested first query per company: the registry `legal_name`
  verbatim (the 2026-11-04 probe found LUCK/OGDC with the "Limited"
  suffix despite the page's own rule saying names must not end with
  a suffix). Then, only if needed: the name without suffix, then a
  distinctive substring (e.g. "Hub Power"). Record every wording
  tried, in order.
- The page disclaimer applies: system-generated information, no
  name-reservation right, Registrar decides. Results are
  observations, not legal determinations.
- Firewall block ("Web Page Blocked!") or flaky load: wait, retry
  once, and if still blocked record that company as BLOCKED (query
  attempted, no observation) and continue. Never bypass, never
  automate, never scrape in bulk.
- Popup ("ATTENTION ALL COMPANIES") must be closed before
  searching; it is not an observation.
