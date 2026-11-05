# Data Source and Licensing Audit — PSX Intelligence AI (Independent Audit)

**Audit baseline:** branch `phase-30-release`, commit `8937338`.
**Audit date:** 2026-11-05 (Asia/Karachi).
**Governing principle:** public availability does NOT imply
republication permission, and a single public source does NOT make
data verified. This audit checks what permissions exist, what terms
say, and what the system actually does with each source — not what
the system hopes the terms allow.

## 1. PSX market data — Terms gate OPEN (critical external dependency)

**What the PSX Terms say (as established in Phase 1/4 review):**

- Systematic retrieval of content, and the creation of collections,
  compilations, or databases from it, is prohibited except with
  prior written permission.
- Automated access is prohibited except through generally available
  third-party browsers, unless prior written permission is granted.
- Redistribution, republication, dissemination, sale, or commercial
  use of the Market Data feed without the respective rights or
  licence is strictly prohibited.
- The documented contact for permission is
  `marketdatarequest@psx.com.pk`.
- The only allowance found: printing or downloading one copy of a
  single document for personal, non-commercial use.

**What exists:**

- A permission request was sent 2026-11-04 16:58:19 PKT from
  `zainmushtaq5439@gmail.com` to `marketdatarequest@psx.com.pk`
  (Gmail message/thread ID `1a1a66ca3ef85eeb`, label SENT).
  Sending proves acceptance by Gmail, not delivery to or reading
  by PSX.
- The user later reported a reply had arrived and that they
  permanently deleted it, including from trash. Its wording is
  therefore UNVERIFIABLE and does NOT clear the gate.
- No resend has been sent (user declined a resend on 2026-11-04
  and took the permission side onto themselves). A reply-watch
  cron (`psx-permission-reply-watch`, every 6 hours) remains
  active; it has not delivered a PSX reply during this audit.
- **This audit sends no email to PSX or anyone else, and claims
  NO clearance.** The gate is OPEN.

**What the system actually does (verified):**

- The 444-row price snapshot comes from a DPS market-summary CSV
  (mapped file, gitignored, never committed), ingested once with
  `--source-key dps_market_summary_2026-11-03`. No live PSX
  collection runs: the three collection jobs
  (`market_post_close`, `filing_check`, `macro_release_check`) are
  PAUSED with exact Terms reasons, the runner refuses paused jobs,
  and re-seeding preserves operator status (never re-enables a
  paused job). No automated PSX access occurs.
- The Phase 11 PSX collector is a GATED STUB (registered, not
  implemented — see the code audit section of the main report).
  No PSX announcements were collected (listed in NOT_COLLECTED
  with the unblocker "written PSX permission evidence, verified
  for its exact terms").
- DPS use is discovery-only: the DPS filing-download route is
  BLOCKED for download use (the LUCK DPS link is recorded as
  blocked, not used). DPS listing-status data was used for the
  registry snapshot, which is the weakest link in the chain: a
  single DPS source cannot satisfy H1 (see §4), and the DPS terms
  for structured reuse were not established beyond discovery.

**Consequence:** every market-data-dependent phase (5, 6, 12, 13,
14, 16, 17, 20, 21) is capped at PARTIALLY COMPLETE until written
PSX permission, verified for its exact terms, exists. The system's
own design respects this (paused jobs, gated stub, honest
UNVERIFIED labels) — the gap is a permission gap, not a
compliance violation in the code. But the data already stored
(444 prices, 470-company registry) was collected without that
permission, and its lawful basis for retention and any future use
is exactly what the permission request must settle. The audit
does not resolve that question; it records it as the project's
top shared blocker.

## 2. Company documents (issuer filings)

- **HUBC** annual report 2026, **NML** quarterly Q3 2025, **OGDC**
  interim H1 2025 (via RNS), **HBL** annual report 2025: all four
  PDFs are gitignored (never committed), sourced from issuer IR
  pages / RNS, and used for internal analysis only, with no
  republication. Sampled issuer-IR use is consistent with
  internal-analysis-only practice; no republication path exists
  (reports are DRAFT, exports are local files, no publish step).
- **LUCK FY2026 extraction remains parked**, blocked on DPS
  filing-download terms or an issuer-hosted URL — correctly not
  forced.
- **KSE-100 statement coverage:** 4 of 470 companies have
  statements. The other 466 are honestly absent, not estimated.

## 3. Macro sources (SBP / PBS / press)

- 12 economic indicators: 6 VERIFIED under a documented SBP/PBS
  cross-publisher caveat, 6 UNVERIFIED. The caveat matters: the
  VERIFIED label here does NOT mean H1-verified in the registry
  sense (two distinct agreeing sources including one official
  recorded in the registry). It means two publishers (SBP + PBS,
  or SBP + press reporting the same release) agreed. The audit
  records this as a documented definitional difference, not as a
  silent promotion — but any reader who takes "VERIFIED" at face
  value across tables will over-read it. Recommendation: rename
  the macro VERIFIED status or attach the caveat wherever the
  macro table is displayed (see remediation roadmap).
- October CPI YoY official read: still blocked on a live-browser
  PBS PDF fetch (Phase 10 blocker 1) — not audit scope, recorded
  as open.

## 4. Verification rule H1 (registry) — applied, not met

H1: VERIFIED requires ≥ 2 distinct agreeing sources including one
official (`psx_official`, `secp`); PARTIALLY_VERIFIED = ≥ 2
agreeing without official; single source = UNVERIFIED; same-
publisher pages are NOT distinct sources.

- Registry evidence: 940 DPS + 61 secp_leap = 1,001 rows, but the
  LEAP rows cover only 61 companies and the loader NEVER changes
  statuses and NEVER writes identifiers (by design, procedure §6).
  Result: all 470 companies remain UNVERIFIED, 0 identifiers —
  the system correctly refuses to promote on this evidence. The
  field-scoped LEAP promotion procedure exists as a document on
  the unmerged side branch, not as executed promotions.
- No company, price, statement, valuation, or decision row in the
  scratch reproduction carries VERIFIED or PARTIALLY_VERIFIED
  except the 6 caveated macro indicators. The audit made no
  promotion and exercised no promotion path.

## 5. Dependency licences (verified pins + fresh vulnerability scan)

Pins verified in `backend/requirements.txt`: fastapi 0.162.0,
uvicorn 0.54.0, SQLAlchemy 2.1.8, alembic 1.20.1, psycopg[binary]
3.3.7, fpdf2 2.9.0, PyMuPDF 2.1, pdfplumber 0.11.10.
`backend/LICENCES.md` records the licence inventory.

**PyMuPDF AGPL-3.0-or-commercial trigger analysis (defect D-14,
MEDIUM in the register):**

- PyMuPDF is dual-licensed AGPL-3.0-or-commercial. The AGPL
  trigger is distribution of the software (including public
  hosted/network use of an AGPL program, via the network-use
  clause) or redistribution of the code.
- Current state: the system runs locally (audit backend on
  localhost, no public hosting, no redistribution of PyMuPDF
  itself, no hosted service offered to third parties). **No
  current violation is claimed.**
- Trigger conditions that WOULD activate AGPL obligations: (a)
  deploying the backend as a publicly accessible hosted service;
  (b) distributing the application (including a Docker image or
  installer bundling PyMuPDF) to third parties. Either step
  requires a prior licence decision: comply with AGPL-3.0
  (including corresponding-source obligations) or obtain a
  commercial PyMuPDF licence. This is a pre-deployment gate, not
  a reason to stop local development. D-14's review trigger is
  correctly recorded in the register.

**Other licences:** no paid dependency is adopted (PKR 0 rule
holds for dependencies); local hardware, electricity, and internet
are external operating expenses, disclosed as such, never called
free. No LLM API is used (AI = Ollama + open-weight local models
only, and no local model is verified as installed — see the
production readiness audit).

**Dependency vulnerabilities (new audit evidence):** `pip-audit`
run by this audit against the pinned `backend/requirements.txt`
in the fresh clone (network available): **No known
vulnerabilities found** across all pinned dependencies, including
fastapi, uvicorn, sqlalchemy, pymupdf 2.1, and pdfplumber. This
closes the Phase 24 gap (pip-audit/safety unavailable offline
then). The scan was run in scratch venv only; nothing was
committed. Re-run before any production deployment, since
vulnerability data is time-sensitive.

## 6. Model licences

- No verified local LLM or embedding model exists in the audited
  system (vector retrieval is registered but NOT implemented;
  the orchestration run notes "LLM execution unavailable: all
  agents ran in rule-based fallback mode"). There is therefore no
  model licence to audit — and no model capability to claim.
  Any future model adoption needs its own licence check (open
  weights ≠ unrestricted use).

## 7. Verdict for this audit area

- PSX Terms gate: OPEN (no verifiable permission). This alone
  caps market-data phases at PARTIALLY COMPLETE.
- No compliance violation was found in what the system DOES
  (paused collection, gated stub, gitignored sources, no
  republication, no promotion).
- PyMuPDF AGPL: no current violation; a hard pre-deployment gate.
- Dependencies: pinned, licence-inventoried, vulnerability-clean
  at audit time.
- The honest labelling (UNVERIFIED everywhere, caveated macro
  VERIFIED) is the system's main licensing defence — and the
  macro VERIFIED caveat needs surfacing wherever macro data is
  displayed.
