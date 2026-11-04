# PSX Intelligence AI — Phase 1: Data Licensing Policy

**Status:** Policy for Phase 1 research/specification and for Phase 2 gates. This is
NOT legal advice. Where this file says "verify" or "seek permission", that step must be
done with the rights holder (or qualified legal advice) before the gated use begins.
**Budget:** PKR 0 absolute. Nothing in this policy authorises, budgets or assumes any
paid licence, subscription, data purchase or hosting. If a use requires a paid licence,
the policy outcome is "do not do that use under PKR 0", not "buy the licence".
Local hardware, electricity and internet are external operating expenses, never
called free, and no permanent free hosting is assumed.
**No real trades:** The system must NOT execute real trades initially. This policy
covers data licensing and governance for analysis/intelligence only. It does not
authorise broker access, order placement or live trading, and no data licence
discussed here should be read as a trading permission.

## 1. Core principles (non-negotiable)

1. **PSX data is PSX's to license.** Viewing PSX data on a public portal, or fetching
   it through an unofficial library, does not transfer any right in that data.
2. **No reselling or republishing a live PSX feed without a PSX agreement.** This
   includes: selling PSX prices/quotes, republishing a live or near-live PSX feed,
   offering a public PSX dataset/API, or embedding PSX data in a product sold as a
   data product — all prohibited until a PSX agreement is verified in writing.
3. **Free viewing ≠ redistribution.** "Free to view", "free library", "free API key"
   and "open data" are different statements with different legal effects. Each source
   is judged on its own terms (see §3), never on the word "free".
4. **No unauthorised commercial redistribution of ANY source.** Where a source's
   terms are unverified, the default is: internal analysis only, no commercial
   redistribution, until the terms are verified.
5. **No bypassing auth, access controls or rate limits.** No scraping against a
   site's terms, no evasion of a 429/block, no key/account/IP rotation to evade a
   limit, no use of a no-key fallback to evade a key requirement, no undocumented
   endpoint treated as a sanctioned API.
6. **Attribution is mandatory, but attribution alone is not a licence.** Giving
   credit does not cure a use the terms prohibit (e.g. commercial resale, AI
   training where prohibited, bulk redistribution where prohibited).
7. **No endorsement claims.** Never state or imply that PSX, SECP, SBP, PBS, Finance
   Division, World Bank, IMF or the St. Louis Fed endorses, certifies or sponsors
   PSX Intelligence AI. FRED requires an explicit non-endorsement notice (see §3);
   the same posture is adopted for all sources.
8. **Raw data stays raw, provenance stays attached.** Raw payloads are stored
   separately from processed records (scaffold rule); every stored/derived record
   carries source, source timestamp, collected-at (PKT) and freshness, plus licence
   gate status. If provenance is lost, the record is not used.
9. **Per-dataset, per-use gates.** A licence that covers one dataset or one use
   (e.g. World Bank CC BY 4.0 for a WBG-produced indicator) does not cover another
   dataset (third-party series) or another use (standalone sale, AI training).
   Gates are checked per dataset and per use, every time the use changes.

## 2. Rules for attribution, retention and commercial use

### Attribution (minimum, per display / per derived output)

- **PSX-derived output:** "Source: Pakistan Stock Exchange (PSX) Data Portal, via
  [psx-dps / psxdata — name the library actually used], retrieved [date/time PKT],
  source timestamp [value]. PSX data is subject to PSX licensing; this product is not
  endorsed by PSX." Do not shorten this to "Source: PSX" where the library route
  matters for reproducibility.
- **SECP:** "Source: Securities and Exchange Commission of Pakistan (SECP),
  [page/document], accessed [date]." Plus, for any reproduced SECP page material,
  respect the single-page, unmodified, non-commercial sharing limit in §3 — if the
  use exceeds it, do not reproduce it.
- **SBP:** "Source: State Bank of Pakistan (SBP), [EasyData / Monthly Statistical
  Bulletin, edition], accessed [date]." Licence status must be added once verified;
  until then, add "Licence UNVERIFIED — internal use only."
- **PBS:** "Source: Pakistan Bureau of Statistics (PBS), [publication/dataset],
  accessed [date]." (Attribution is required under the Tier 1 open-licence signal;
  add the exact licence text once directly verified.)
- **Finance Division:** "Source: Finance Division, Government of Pakistan,
  [Pakistan Economic Survey / Monthly Economic Update & Outlook, edition], accessed
  [date]." Where the figure's originator is SBP/PBS/IMF (as the Update itself states),
  cite the originator as well: "via Finance Division, originator: [SBP/PBS/IMF]."
- **World Bank:** "Source: The World Bank, [database/indicator code], accessed
  [date], licensed under CC BY 4.0 [only if the dataset's licence tag confirms
  CC BY 4.0]." If the tag says otherwise, quote that tag instead — never default
  to CC BY 4.0.
- **IMF:** Exactly "Source: International Monetary Fund, [Database Name], <link>"
  (IMF terms format), plus a transformation note if the data were materially
  transformed. For any distribution/download environment, also surface IMF's terms
  to downstream users (IMF condition).
- **FRED (if ever cleared for a specific use):** Prominently display "This product
  uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank
  of St. Louis." plus per-series source/copyright notes. Until cleared, FRED
  attribution is moot because FRED use for AI is on hold.

### Raw-data retention

- Retain raw payloads only as long as needed for provenance, audit and reproducibility
  of the project's own analysis, and only under the source's terms. Retention is
  NOT a redistribution right: a retained raw file must not be published, shared
  externally, or offered as a download.
- Retention limits per source (Phase 1 specification; Phase 2 must implement and log):
  - **PSX raw (via libraries):** internal only; no public raw dump; no live-feed
    republication; delete or restrict on PSX request or on licence verification
    failure.
  - **SECP:** no bulk retention of registry/filing data; single-company verification
    notes only, with the SECP page/document cited, not a scraped database.
  - **SBP/PBS/Finance:** retain the publication file + extraction log + vintage, so
    any figure can be traced to its PDF/table; do not retain microdata (PBS tiers
    3–4 are out of scope entirely).
  - **World Bank/IMF:** retain indicator code + vintage/edition + licence tag +
    retrieval date with every pull; full-refresh pulls replace prior pulls only
    with the vintage recorded, never silently.
  - **FRED:** no retention, caching or archiving for AI use until the Terms gate is
    cleared — this is a prohibition reported in the 2024 Terms update, not a
    retention preference. See §3.
- If any source's terms, on direct re-read, prohibit retention for the intended
  purpose, that prohibition overrides this section.

### What must be checked before ANY commercial use

Commercial use here means: selling, charging for, or monetising (including via ads,
subscriptions, or a paid tier) any product, service, output or dataset that contains,
is derived from, or republishes source data — or using source data to attract users
to a monetised product. Before ANY such use, ALL of these must be satisfied and
logged with evidence (document URL + date + excerpt):

1. The exact licence/terms text has been directly fetched (not via a third-party
   summary) and filed.
2. The per-dataset licence tag / per-use permission covers the specific commercial
   use (not just "viewing" or "personal use").
3. Any required permission has been obtained in writing (PSX agreement; IMF
   copyright@imf.org permission for potential commercial reuse; third-party series
   owners for FRED copyright series; SECP permission for hyperlinking/framing or
   any use beyond single-page sharing).
4. Attribution + non-endorsement wording for that source is in place.
5. No prohibited use is involved (see §4 prohibitions).
6. The PKR 0 gate is satisfied: no paid licence is being assumed. If the required
   permission is paid, the commercial use does NOT proceed under this policy.

Until all six are satisfied for a source, that source is **internal-analysis-only**
(or, for FRED AI use, **on hold entirely**).

## 3. Per-source licensing status

| Source | Status (Phase 1 evidence) | What is permitted on current evidence | What is NOT permitted / gated |
|---|---|---|---|
| PSX Portal + psx-dps + psxdata (data) | **UNVERIFIED terms; code licences verified (MIT for both libraries).** Free to view / free libraries do not license the data. | Internal analysis/research use of fetched snapshots/EOD for the project's own intelligence, with PSX attribution + provenance, pending PSX terms verification. | Any resale, live-feed republication, public dataset/API, bulk redistribution, or commercial product embedding PSX data — all gated on a PSX agreement. Library MIT licences cover code only. |
| SECP | **PARTIALLY VERIFIED — Terms of Use directly fetched 2026-11-04.** | Residents/citizens of Pakistan may copy electronically / print single pages of SECP copyright material, unmodified, solely to share information with other citizens/residents without cost. General-information viewing. | Bulk extraction/scraping; redistribution beyond single-page non-commercial sharing; hyperlinking/framing without prior SECP permission; use of third-party-copyright material on SECP pages; any claim SECP endorses the product; reliance without independent verification against the official SECP record (SECP's own disclaimer). |
| SBP | **UNVERIFIED.** No terms/licence page found. | Internal analysis of publicly presented statistics, with SBP attribution, pending terms verification. | Any commercial redistribution, republication or resale — gated until SBP terms are fetched. No "free = redistributable" inference. |
| PBS | **PARTIALLY VERIFIED — Data Dissemination Policy via search snippet.** Tier 1/2 open government licence signal: copy/adapt/commercial + non-commercial reuse WITH attribution; standard products free at point of use. | Internal analysis + attributed reuse of Tier 1 aggregate tables/indicators/publications, once the exact licence text + per-dataset tier are directly verified. | Identifiable microdata, Tier 3 licensed files without application/endorsement/NDA, Tier 4 non-disseminable data — all prohibited/out of scope. Any reuse before licence-text verification is internal-only. Custom-tabulation charges (if any) are not assumed under PKR 0. |
| Finance Division | **UNVERIFIED.** No terms/licence page found. | Internal analysis of published Survey/Update figures, with Finance Division + originator attribution, pending terms verification. | Any commercial redistribution/republication — gated until terms are fetched. Secondary figures must not be presented as Finance Division-originated where the Update cites SBP/PBS/IMF. |
| World Bank | **PARTIALLY VERIFIED — blog/Data360/FAQ via search.** CC BY 4.0 default for WBG-produced open data; per-dataset tags + third-party exceptions override. | Attributed reuse, including commercial reuse, of a dataset ONLY where its licence tag confirms CC BY 4.0 (or another permitting licence), with World Bank + provider attribution and no endorsement claim. | Redistribution/reuse of a dataset whose tag restricts it, or of third-party data without the provider's consent; any endorsement implication; any use that drops the licence tag check. |
| IMF | **PARTIALLY VERIFIED — Copyright and Usage page via search (effective 2024-10-11 per excerpts).** Data-use regime permits download/extract/derivative/publish/distribute WITH attribution + conditions. | Attributed internal analysis and non-commercial distribution within the Data terms (accurate reproduction, transformation noted, downstream terms communicated, standalone-sale free-availability disclosure if ever applicable). | ANY potential commercial reuse without first emailing copyright@imf.org for permission; systematic copying / substantial reuse of general (non-Data) Content beyond fair use without written permission; sale of IMF Data as a standalone product without the free-availability disclosure; any alteration affecting data integrity. |
| FRED | **PARTIALLY VERIFIED — Terms/API Terms/2024 update via search. ON HOLD for AI use.** Non-commercial/educational/personal framing; mandatory non-endorsement notice; third-party-copyright rule. | On current evidence: NOTHING for PSX Intelligence AI beyond reading the Terms. No training, caching, redistribution or commercial output is approved. (A purely personal, non-commercial, non-AI lookup by an individual is a different use and is not this project's use.) | AI/ML development or training (including LLM/deep-learning/generative-AI) using FRED Services/Content; storing/caching/archiving FRED content or providing it to third parties or incorporating it in a database/compilation/archive/cache; wholesale downloading in violation of Terms; replicating/replacing the FRED user experience; endorsement claims; use of copyright-noticed series beyond personal use without the data owner's permission; any use that evades the API-key requirement. |

## 4. Strict rules (apply to every team, every phase)

- **No unauthorised commercial redistribution.** See §1–§3. "Publicly accessible"
  is not authorisation.
- **No bypassing auth / access controls / rate limits.** Includes: scraping a site
  that restricts automated access, using an undocumented endpoint as if it were a
  sanctioned API, evading 429/blocks, rotating identities to evade limits, and using
  a no-key fallback to evade a key requirement.
- **No live-feed republication without agreement.** Especially PSX: no public
  streaming, mirroring, API or dataset of live/near-live PSX data without a PSX
  agreement.
- **No standalone sale of another publisher's data.** IMF standalone-sale disclosure
  and World Bank/PBS attribution rules apply even if a future commercial model is
  proposed; under PKR 0, no such model is approved here.
- **No microdata, no personal data, no confidential data.** PBS tiers 3–4, SECP
  restricted records, IMF confidential/unpublished data, and any personal data in
  filings/registries are out of scope. Do not collect, retain or publish them.
- **No legal-advice claims.** This policy records what pages state and what checks
  remain; it does not advise that any use is lawful. Gated uses need rights-holder
  confirmation or qualified legal advice.
- **Stop-and-log rule.** If a source blocks access, changes terms, or a licence gate
  fails, stop that source's gated use, log the event with date + evidence, and do
  not route around it via another source that carries the same restriction.

## 5. Governance note — no real trades

Data licensing does not create trading authority. The system must NOT execute real
trades initially, and no licence, library or free data source in this file authorises
trading, broker connectivity, order placement, or investment advice. If a future
phase ever proposes trading, it requires: (i) a separate user decision, (ii) a
separate broker/execution risk and compliance assessment, and (iii) a fresh
licensing check (market-data licences for trading use are commonly stricter than
for internal analysis). Until then, all PSX data use under this policy is
analysis/intelligence only.
