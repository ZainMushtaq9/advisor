# Phase 4 — SECP LEAP sampled-verification load report (2026-11-04)

Branch: `phase-04-leap-load`, from `phase-04-sampled-verification` (`9204632`).
Procedure: `docs/phase-04/field_scoped_leap_promotion_procedure.md`.
Plan: `docs/phase-04/sampled_verification_plan_2026-11-04.md`.
Loader: `scripts/load_leap_evidence.py` (`--dry-run` default; fail-fast;
never calls `apply_verification_rules`, never writes identifiers,
never changes any status).
Observations: `docs/phase-04/leap_observations_2026-11-04.json`
(provenance copy of the browser delivery at
`workspace/psx-playbook/leap_observations_2026-11-04.json`,
collected 2026-11-04, 61 rows, 61 unique tickers; the delivery file
itself was left untouched).

## Verdict for the sampled-verification piece: LOADED, Phase 4 stays PARTIALLY COMPLETE

The browser half of the Phase 4 revisit is now closed in the
database. Sampled agreement alone NEVER flips Phase 4 to COMPLETE
(see re-judgment below).

## Load counts

| Measure | Value |
|---|---|
| Observations loaded | 61 / 61 attempted, 0 blocked |
| AGREE | 47 |
| DISAGREE | 5 |
| NOT_FOUND | 9 |
| BLOCKED | 0 |
| Derived summary | **47/61 LEAP-NAME-AGREED** (77.0% of the sample) |
| secp_leap evidence rows before → after | 0 → 61 |
| secp_leap rows with CUIN keys | 52 (47 AGREE + 5 DISAGREE) |
| secp_leap rows with NOT_FOUND keys | 9 |
| registry_evidence total before → after | 940 → 1001 |
| company_identifiers before → after | 0 → 0 (no identifier writes) |
| companies before → after | 470 → 470, all UNVERIFIED |
| securities before → after | 470 → 470, all UNVERIFIED |
| data_sources total after | 6 (2 prior + 3 from Phase 7 + 1 secp_leap provenance row inserted by the loader) |

Verification performed: `--dry-run` fully clean on first run
(61 validated, 61 to insert, 0 skipped); `--commit` wrote 61 rows;
a second `--commit` wrote 0 rows and skipped 61 identical rows
(idempotency proven); backend suite on this tree **56 passed**;
no loader code change was needed, so no new regression test was
added. Spot-checked in the DB after commit: AGHA row stores the
date part only, SSOM row carries the literal NOT_FOUND key with
the organization row in its note, BLUEX row carries the moved
other-candidates note.

## Handling decisions (no data silently dropped)

(a) Datetime incorporation dates (4): AGHA `19-11-2013 16:46:33`,
EFERT `29-06-2009 11:08:29`, GDL `21-10-2020 12:31:38`, PABC
`04-12-2014 15:35:53`. The loader's strict DD-MM-YYYY parser
rejects time components, so the branch copy of the observations
stores the DATE part only and appends the full shown datetime to
each observation's note (e.g. AGHA's note now records the full
`19-11-2013 16:46:33`). The time component is a LEAP display
timestamp, not part of the incorporation date. No loader code
change was needed.

(b) BLUEX extra field: the delivery carried `other_candidates_note`
(a RESERVED FOR CHANGE OF NAME row for BLUE-EX LIMITED itself,
same CUIN and date — the target name, not a different candidate).
The loader ignores unknown fields, which would have silently
dropped this content, so the field's content was moved verbatim
into the observation's notes (marked as moved) and the field
removed in the branch copy. Nothing was lost.

(c) SSOM NOT_FOUND with an organization row: SSOM (id 499) is
NOT_FOUND with a NON-NULL organization row (S. S. OIL MILLS
LIMITED, displayed 08-21-3990; its note mentions CUIN 0022304 /
CRO Lahore from that org row). Per the procedure the organization
row is never used: the loaded row's `source_record_key` is the
literal `NOT_FOUND` (NOT the org-row CUIN), `observed_name` is
NULL, and the org row stays recorded in the evidence note as
observed-but-unused. The loader accepted this as-is (it only
requires NOT_FOUND to carry no incorporated_row), so no loader
fix was needed.

(d) ABOT date reconciliation: ABOT (id 94, CUIN 0000192, CRO
Karachi) has conflicting date readings in its notes — an earlier
07-02-1948 reading vs the reported screenshot-verified 02-07-1948.
The reported 02-07-1948 value was accepted. Reconciliation: the
organization row displays dates MM-DD-style (07-02-3948, garbled
year) while the INCORPORATED row displays DD-MM (02-07-1948);
both point to 2 July 1948, and the outcome is AGREE either way.
No change to the observation was needed.

(e) IREIT weak NOT_FOUND — flagged, not upgraded: IREIT (id 309)
verbatim "Image REIT" returned 0 results, but the "REIT" wording
returned 118 results of which only the first page (10 rows) was
checked. The NOT_FOUND stands on the verbatim-0 evidence, but it
is WEAK: an Image REIT row could exist on an unchecked page.
No re-query was done (no browser work in this run). A future run
that pages through the REIT results could overturn this one row;
it cannot change the 47/61 summary by more than one.

(f) Loader fail-fast mismatches: NONE. All 61 company_id / ticker /
legal_name checks passed against the live DB. Open question (not
a conclusion): the plan's company ids (e.g. HUBC 289) differ from
ids quoted in the Phase 7 report (e.g. HUBC 759). The loader
validates against the live DB, and it accepted 289 with matching
ticker and legal name, so the plan ids are the ones the live
registry uses. The Phase 7 figure is left as an unexplained
difference for a future cross-check, not resolved here.

## Every DISAGREE — registry-name review flags

All five are name-token differences only. CUINs are recorded, not
agreed, and no registry name was edited.

| Ticker | Registry legal name | LEAP INCORPORATED name | Token difference | CUIN |
|---|---|---|---|---|
| AGHA | Agha Steel Ind.Ltd | AGHA STEEL INDUSTRIES LIMITED | IND vs INDUSTRIES — abbreviation not expanded by normalization | 0085815 |
| ARPAK | Arpak International Investments Ltd. | ARPAK INTERNATIONAL INVESTMENT LIMITED | INVESTMENTS (plural) vs INVESTMENT (singular) | 0005840 |
| JVDCPS | Javedan Corporation (Pref) | JAVEDAN CORPORATION LIMITED | (Pref) qualifier absent in the LEAP name | 0001313 |
| MWMP | Mandviwala Mauser Plastic Industries | MANDVIWALLA MAUSER PLASTIC INDUSTRIES LIMITED | MANDVIWALA vs MANDVIWALLA (single vs double L) | 0018069 |
| PKGP | Pakgen Power Limited | PAKGEN LIMITED | POWER absent in the LEAP name | 0035039 |

NOT_FOUND (9): FCONM, FHAM, FTMM, HGFA, IREIT (weak, see above),
LOTCHEM, SSOM (org-row-only, see above), UBLPETF, WAHN. A NOT_FOUND
means the sampled LEAP search found no INCORPORATED row for that
name; it is not evidence the company does not exist.

## Phase 4 re-judgment

Verdict: **PARTIALLY COMPLETE (unchanged)**. The sampled
verification piece is now complete in the database (procedure +
61-company sample + browser observations + 61 evidence rows +
this report), and the derived summary is 47/61 LEAP-NAME-AGREED.
But sampled agreement is a derived summary, not a status and not
a registry-wide claim: all 470 records stay UNVERIFIED, no
identifier was written, and no sector or ticker was verified from
LEAP. Sampled agreement alone never flips Phase 4 to COMPLETE.

Remaining blockers (unchanged, with exact unblockers):

1. GEM (5) + Non-Compliant/Winding-Up (93) capture — unblocker:
   written PSX permission evidence, produced and verified for its
   exact terms (internal, non-commercial, private-database use).
   None exists; the permission side is user-owned.
2. Full-470 VERIFIED — unblocker: full manual LEAP run (~16–40
   hours) or an approved bulk route from SECP, plus a field-scoped
   promotion model in code and a separate approval to run it.
3. KSE-100 completeness — unblocker: a verified membership list
   from an official source; needed only if a KSE-100 claim is ever
   made. None is made.
4. Terms basis for the populated registry — OPEN, same permission
   evidence as (1).
5. News alias generation — documented variance; no news pipeline
   exists in Phases 1–6 scope.
6. CI-in-CI — unblocker: a main/development push or PR (separate
   approval; not done here).
