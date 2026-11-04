# Phase 4 — Sampled SECP LEAP verification plan (2026-11-04)

Branch: `phase-04-sampled-verification`. Procedure:
`docs/phase-04/field_scoped_leap_promotion_procedure.md`.
Loader: `scripts/load_leap_evidence.py` (`--dry-run` default).

## Status: NOT EXECUTED

The live LEAP queries below were NOT run in this revisit.
A generic coordinator cannot drive the LEAP search UI (an
Angular single-page app); a text fetch of the landing page
returned an upstream HTTP 500 and was not retried. The live
queries require a live-browser task (parent routing).
Everything else in this plan — procedure, sample, loader,
tests — is complete and verified on this branch.

## Sampling rule (deterministic, reproducible)

- Population: the 470 Main Board / Normal Counter registry
  companies (live DB, 2026-11-04), ordered by ticker.
- Systematic pick: every 10th company in global ticker order
  (positions 10, 20, …, 470) = 47 companies.
- Sector top-up: for each of the 37 sectors with no systematic
  pick, add its first company in ticker order = 14 companies.
- Total sample: 61 companies (13.0% of 470), all 37 sectors
  covered, ticker range 786–ZUMA. The 13.0% (not exactly 10%)
  is the direct consequence of the minimum-1-per-sector rule.
- The 3 companies probed on 2026-11-04 (LUCK, OGDC, HUBC) are
  NOT pre-credited: HUBC is in this sample by the rule and
  must be re-queried in the browser run; LUCK/OGDC are not in
  the sample and stay documentation-only until a future run.

## Sample table (61 companies)

| Ticker | Company id | Registry legal name | Sector | Suggested first query |
|---|---|---|---|---|
| 786 | 90 | 786 Investments Limited | INV. BANKS / INV. COS. / SECURITIES COS. | 786 Investments Limited |
| ABOT | 94 | Abbott Laboratories (Pakistan) Limited | PHARMACEUTICALS | Abbott Laboratories (Pakistan) Limited |
| AGHA | 99 | Agha Steel Ind.Ltd | ENGINEERING | Agha Steel Ind.Ltd |
| AHTM | 109 | Ahmad Hassan Textile Mills Limited | TEXTILE COMPOSITE | Ahmad Hassan Textile Mills Limited |
| ALTN | 119 | Altern Energy Limited | POWER GENERATION & DISTRIBUTION | Altern Energy Limited |
| APL | 126 | Attock Petroleum Limited | OIL & GAS MARKETING COMPANIES | Attock Petroleum Limited |
| ARPAK | 129 | Arpak International Investments Ltd. | MISCELLANEOUS | Arpak International Investments Ltd. |
| ASHT | 131 | Ashfaq Textile Mills Limited | TEXTILE WEAVING | Ashfaq Textile Mills Limited |
| ATIL | 139 | Atlas Insurance Limited | INSURANCE | Atlas Insurance Limited |
| ATRL | 141 | Attock Refinery Limited | REFINERY | Attock Refinery Limited |
| BATA | 149 | Bata Pakistan Limited | LEATHER & TANNERIES | Bata Pakistan Limited |
| BGL | 157 | Baluchistan Glass Limited | GLASS & CERAMICS | Baluchistan Glass Limited |
| BIFO | 159 | Biafo Industries Limited | CHEMICAL | Biafo Industries Limited |
| BLUEX | 161 | Blue-Ex Limited | TRANSPORT | Blue-Ex Limited |
| BNWM | 164 | Bannu Woollen Mills Limited | WOOLLEN | Bannu Woollen Mills Limited |
| BTL | 169 | Blessed Textiles Limited | TEXTILE COMPOSITE | Blessed Textiles Limited |
| CHCC | 179 | Cherat Cement Company Limited | CEMENT | Cherat Cement Company Limited |
| CSIL | 189 | Crescent Star Insurance Limited | INSURANCE | Crescent Star Insurance Limited |
| DGKC | 199 | D.G. Khan Cement Company Limited | CEMENT | D.G. Khan Cement Company Limited |
| EFERT | 209 | Engro Fertilizers Limited | FERTILIZER | Engro Fertilizers Limited |
| EMCO | 214 | Emco Industries Limited | CABLE & ELECTRICAL GOODS | Emco Industries Limited |
| EWIC | 219 | East West Insurance Company Limited | INSURANCE | East West Insurance Company Limited |
| FCONM | 229 | First Constellation Modaraba | MODARABAS | First Constellation Modaraba |
| FHAM | 239 | First Habib Modaraba | MODARABAS | First Habib Modaraba |
| FTMM | 249 | First Treet Manufacturing Modaraba | MODARABAS | First Treet Manufacturing Modaraba |
| GATI | 254 | Gatron (Industries) Limited | SYNTHETIC & RAYON | Gatron (Industries) Limited |
| GDL | 259 | Ghani Dairies Limited | FOOD & PERSONAL CARE PRODUCTS | Ghani Dairies Limited |
| GRYL | 269 | Grays Leasing Limited | LEASING COMPANIES | Grays Leasing Limited |
| HCAR | 279 | Honda Atlas Cars (Pakistan) Limited | AUTOMOBILE ASSEMBLER | Honda Atlas Cars (Pakistan) Limited |
| HGFA | 280 | HBL Growth Fund | CLOSE - END MUTUAL FUND | HBL Growth Fund |
| HUBC | 289 | The Hub Power Company Limited | POWER GENERATION & DISTRIBUTION | The Hub Power Company Limited |
| IDYM | 299 | Indus Dyeing & Manufacturing Co. Limited | TEXTILE SPINNING | Indus Dyeing & Manufacturing Co. Limited |
| IMAGE | 303 | Image Pakistan Limited | APPAREL | Image Pakistan Limited |
| IREIT | 309 | Image REIT | REAL ESTATE INVESTMENT TRUST | Image REIT |
| JLICL | 319 | Jubilee Life Insurance Company Limited | INSURANCE | Jubilee Life Insurance Company Limited |
| JVDCPS | 329 | Javedan Corporation (Pref) | PROPERTY | Javedan Corporation (Pref) |
| KHTC | 333 | Khyber Tobacco Company Limited | TOBACCO | Khyber Tobacco Company Limited |
| KOHTM | 339 | Kohat Textile Mills Limited | TEXTILE SPINNING | Kohat Textile Mills Limited |
| LOTCHEM | 349 | Lotte Chemical Pakistan Limited | CHEMICAL | Lotte Chemical Pakistan Limited |
| MARI | 358 | Mari Energies Limited | OIL & GAS EXPLORATION COMPANIES | Mari Energies Limited |
| MCB | 359 | MCB Bank Limited | COMMERCIAL BANKS | MCB Bank Limited |
| MLCF | 369 | Maple Leaf Cement Factory Limited | CEMENT | Maple Leaf Cement Factory Limited |
| MWMP | 379 | Mandviwala Mauser Plastic Industries | MISCELLANEOUS | Mandviwala Mauser Plastic Industries |
| NETSOL | 389 | NetSol Technologies Limited | TECHNOLOGY & COMMUNICATION | NetSol Technologies Limited |
| NRSL | 399 | Nimir Resins Limited | CHEMICAL | Nimir Resins Limited |
| PABC | 409 | Pakistan Aluminium Beverage Cans Limited | MISCELLANEOUS | Pakistan Aluminium Beverage Cans Limited |
| PGLC | 419 | Pak-Gulf Leasing Company Limited | LEASING COMPANIES | Pak-Gulf Leasing Company Limited |
| PKGP | 429 | Pakgen Power Limited | POWER GENERATION & DISTRIBUTION | Pakgen Power Limited |
| PQGTL | 439 | Pak Qatar General Takaful Limited | INSURANCE | Pak Qatar General Takaful Limited |
| PTL | 449 | Panther Tyres Ltd. | AUTOMOBILE PARTS & ACCESSORIES | Panther Tyres Ltd. |
| SANSM | 459 | Sanghar Sugar Mills Limited | SUGAR & ALLIED INDUSTRIES | Sanghar Sugar Mills Limited |
| SEPL | 469 | Security Papers Limited | PAPER, BOARD & PACKAGING | Security Papers Limited |
| SHSML | 479 | Shahmurad Sugar Mills Limited | SUGAR & ALLIED INDUSTRIES | Shahmurad Sugar Mills Limited |
| SNBL | 489 | Soneri Bank Limited | COMMERCIAL BANKS | Soneri Bank Limited |
| SSOM | 499 | S.S.Oil Mills Limited | VANASPATI & ALLIED INDUSTRIES | S.S.Oil Mills Limited |
| SYM | 509 | Symmetry Group Limited | TECHNOLOGY & COMMUNICATION | Symmetry Group Limited |
| TICL | 519 | The Thal Industries Corporation Limited | SUGAR & ALLIED INDUSTRIES | The Thal Industries Corporation Limited |
| TREET | 529 | Treet Corporation Limited | FOOD & PERSONAL CARE PRODUCTS | Treet Corporation Limited |
| UBLPETF | 539 | UBLPakistan Enterprise ETF | EXCHANGE TRADED FUNDS | UBLPakistan Enterprise ETF |
| WAHN | 549 | Wah Noble Chemicals Limited | CHEMICAL | Wah Noble Chemicals Limited |
| ZUMA | 559 | Zuma Resources Limited | TECHNOLOGY & COMMUNICATION | Zuma Resources Limited |

## Browser execution spec (for the parent-routed live task)

1. Open https://leap.secp.gov.pk/#/landing-page. Close the
   "ATTENTION ALL COMPANIES" popup with its X button.
2. For each company, in table order: try the suggested first
   query (registry legal name verbatim) in the "Company Name
   Search / Check Name Availability" box. If it finds nothing,
   try the name without suffix, then a distinctive substring.
   Record EVERY wording tried, in order, and which one found
   the row. No sign-in, no eServices paid route, no bulk
   scraping, one query at a time.
3. For each company record: both duplicate rows (INCORPORATED
   row = observation; organization row + garbled displayed
   date noted, never used), CUIN, incorporation date as shown,
   CRO city, any other candidates shown, and the outcome
   (AGREE / DISAGREE / NOT_FOUND per the procedure §3).
4. If the page shows "Web Page Blocked!" or fails to load:
   wait, retry once; if still blocked, record that company as
   BLOCKED (query attempted, no observation) and continue.
   Never bypass the block.
5. Deliver the results as the JSON schema below. The loader
   validates every observation and fails fast on any
   inconsistency; it writes evidence rows only and changes
   no status (procedure §6).

## Observations JSON schema

```json
{
  "collected_date": "YYYY-MM-DD",
  "observations": [
    {
      "company_id": 289,
      "ticker": "HUBC",
      "registry_legal_name": "The Hub Power Company Limited",
      "query_wordings": ["<wording 1>", "<wording 2>"],
      "query_that_found": "<wording that found the row, or null>",
      "incorporated_row": {"name": "<LEAP name verbatim>",
        "cuin": "<7 digits>", "incorporation_date": "DD-MM-YYYY",
        "cro_city": "<city>"},
      "organization_row": {"name": "<verbatim>",
        "displayed_date": "<as shown, garbled year kept>"},
      "other_candidates": ["<names shown, if any>"],
      "outcome": "AGREE | DISAGREE | NOT_FOUND",
      "notes": "<anything else observed>"
    }
  ]
}
```

For NOT_FOUND: `"incorporated_row": null, "query_that_found": null`.
For BLOCKED (firewall, no observation): omit the company from
`observations` and list it separately in the delivery note —
a blocked company gets NO evidence row, never a NOT_FOUND row.

## Re-judgment after the browser run

When the observations JSON is loaded (`--dry-run` then
`--commit` on a follow-up branch from this branch): report
AGREE / DISAGREE / NOT_FOUND / BLOCKED counts, the derived
"X/61 LEAP-NAME-AGREED" summary, and every DISAGREE as a
registry-name review flag. The Phase 4 verdict stays
PARTIALLY COMPLETE until the remaining blockers clear
(GEM/Non-Compliant capture, full-470 verification, KSE-100
list, Terms basis, news aliases, CI-in-CI — see the
completion report). Sampled agreement alone never flips the
verdict to COMPLETE.

