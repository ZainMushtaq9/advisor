# Phase 4 — Independent Audit

**Auditor role:** independent auditor. This auditor did NOT write the Phase 4 code.
**Date:** 2026-11-04 (Asia/Karachi).
**Branch audited:** `phase-04-company-registry`
**Scope:** PSX Company & Security Registry Discovery, Verification and Population —
engine (`backend/app/services/registry/`), APIs (`backend/app/api/v1/endpoints/registry.py`),
frontend (`frontend/app/companies/page.tsx`), tests (`backend/tests/test_registry.py`),
migration `a909e8449cdd`, live-PostgreSQL check script, and all files in `docs/phase-04/`.
**What the auditor did NOT do:** fix code, edit any project file except this report,
commit, push, merge, write any production database row, or start Phase 5.
All live-database adversarial work ran inside transactions that were rolled back,
and live counts were re-verified as 0 afterwards.

## Verdict: PASS WITH LIMITATIONS

The engine, APIs, frontend, tests, migration, and documentation claims reproduce
under independent re-runs. The production registry is genuinely empty (0 companies,
0 securities, 0 sectors, 0 evidence rows), so no live record is currently mislabeled
and no test data leaked into production. **PARTIALLY COMPLETE on population grounds
is justified** — the source research honestly records why no usable official registry
source was obtainable, and the stale/partial material was correctly NOT imported.

The limitations are real and must be addressed before any `VERIFIED` label is relied
upon or before population begins:

- The single HIGH finding (H1) is a trust-boundary weakness in the verification
  rule itself, not a typo: one import labelled `psx_official` promotes a record to
  `VERIFIED` with no independent corroboration, because the "agreeing" evidence row
  is generated from the very record being imported and `source_key` is
  caller-supplied. The docs' wording ("import success alone never promotes") is
  therefore inaccurate for the official-source path, even though the code behaves
  exactly as `verification.py` and its own test specify.
- MEDIUM findings M1–M5 (name-disagreement merge via ISIN/identifier, ticker
  mutation on a conflicted record, non-idempotent quality-report rows, silently
  dropped `listing_status`, identifiers lost on the matched path) are all reproduced
  below with concrete evidence. None of them affects the current empty production
  registry, but all of them would matter the moment real imports start.

## Commands run and actual counts (auditor's own runs, not the coordinator's)

| Check | Command (from repo root unless noted) | Auditor result |
|---|---|---|
| Backend pytest | `backend/.venv/bin/python -m pytest tests/ -q` | **36 passed, 1 warning** (Starlette deprecation warning, same as claimed) |
| Ruff, Phase 4 files | `backend/.venv/bin/python -m ruff check app/services/registry/ app/api/v1/endpoints/registry.py app/models/registry.py tests/test_registry.py` (from `backend/`) | **All checks passed** |
| Ruff, whole backend | `backend/.venv/bin/python -m ruff check app/ tests/` (from `backend/`) | **All checks passed** |
| Live-PG check script | `DATABASE_URL` from `database/.env` (value never printed) + `backend/.venv/bin/python scripts/run_phase4_pg_check.py` | **PHASE4_PG_CHECK_OK**; import 2 TEST ONLY records, re-import skipped_as_duplicate=2, reconcile coverage=None, API 200s, 404s, 422 as claimed, statistics companies=0 securities=0, transaction rolled back |
| Frontend typecheck | `npm run typecheck` (from `frontend/`) | pass |
| Frontend lint | `npm run lint` (from `frontend/`) | pass |
| Frontend build | `npm run build` (from `frontend/`) | pass, `/companies` route present |
| Frontend Vitest | `npm test` (from `frontend/`) | **3 files, 11 tests, all passed** |
| Alembic current (before) | `alembic -c alembic.ini current` (from `database/`) | `a909e8449cdd (head)` |
| Alembic downgrade + upgrade | `alembic -c alembic.ini downgrade 20261104_0004` then `upgrade head` (from `database/`) | Downgrade to `20261104_0004`, upgrade back to `a909e8449cdd (head)` — cycle works |
| Live counts (before and after all audit work) | read-only `SELECT count(*)` on `companies`, `securities`, `sectors`, `registry_evidence`, `data_quality_reports`, `data_sources`, `exchanges` | **all 0** both times |
| Public table count | `information_schema.tables` where schema `public` | **57** (Phase 3 claim 56 + `registry_evidence` = 57, consistent) |
| `phase2_probe` | table present in the 57-table list | retained, not dropped by the Phase 4 migration (see migration section) |

Note on alembic invocation: `alembic` run from `backend/` with `backend/alembic.ini`
fails with "Can't locate revision identified by 'a909e8449cdd'" because that
configuration only knows the Phase 2 baseline (`0001_baseline_empty.py`). The
working invocation is from `database/` with `database/alembic.ini` (see LOW finding L1).
The auditor's downgrade/upgrade cycle used the working invocation and restored head.

## Disk / live state verified

- `git branch --show-current`: `phase-04-company-registry`.
- `git status` at audit start: modified `backend/app/api/v1/router.py`,
  `backend/app/models/__init__.py`, `frontend/app/companies/page.tsx`; untracked
  `backend/app/api/v1/endpoints/registry.py`, `backend/app/models/registry.py`,
  `backend/app/services/registry/`, `backend/tests/test_registry.py`,
  `database/migrations/versions/a909e8449cdd_phase_4_registry_evidence.py`,
  `docs/phase-04/`, `scripts/run_phase4_pg_check.py`. Nothing was committed by the auditor.
- Four log files (`DEVELOPMENT_LOG.md`, `PROJECT_STATUS.md`,
  `docs/development/DEFECT_REGISTER.md`, `docs/development/MASTER_EXECUTION_LOG.md`;
  30 insertions total) changed during the audit window. The auditor did not write
  them; the only file written by the auditor is this report.
- `docs/phase-04/` contents confirmed: `api_documentation.md`,
  `data_quality_policies.md`, `frontend_documentation.md`, `import_pipeline.md`,
  `normalization_and_matching.md`, `reconciliation_methodology.md`,
  `registry_architecture.md`, `registry_statistics.md`, `source_research.md`,
  `source_research_raw/` (2 snapshots), `sync_configuration.md`, `test_report.md`,
  plus this audit report.
- Migration `a909e8449cdd`, `down_revision = '20261104_0004'`: `upgrade()` creates
  only `registry_evidence` (with unique constraint
  `uq_registry_evidence_entity_source_key`) and contains an explicit comment that
  the `phase2_probe` drop was removed intentionally. `downgrade()` drops only
  `registry_evidence`. Verified by reading the file and by the live
  downgrade/upgrade cycle above.

## Adversarial testing — task items (a)–(f)

All adversarial cases below were run by the auditor against the live PostgreSQL
database inside a transaction that was rolled back, plus pure-function matcher
calls. Live counts after rollback were re-verified as 0.

### (a) Does any path mark a record VERIFIED on import success alone?

**NOT PASS — see HIGH finding H1.** A single `import_records` call with
`source_key="psx_official"` for a brand-new record returns with
`company.status == "VERIFIED"` (auditor reproduction: record `AUD1`,
"Audit One Limited", ISIN `PK0011111111`, created=1, status `VERIFIED`).
The mechanism: the importer writes an evidence row from the same record, then
calls `verification.apply_verification_rules`, which finds an "official" evidence
row whose observed name trivially agrees with the stored name — because both came
from the same input. This is not an accident in the code: `test_import_official_source_verifies`
pins exactly this behaviour. The inaccurate part is the documentation claim in
`import_pipeline.md` ("Import success alone never [promotes]") and the
importer docstring ("The importer NEVER sets VERIFIED… Promotion happens only in
verification.py, from evidence rows"): the promotion happens inside the same
import call, on self-generated evidence. `PARTIALLY_VERIFIED` is different and
genuinely corroborated (it requires ≥2 distinct sources, confirmed by
`test_import_second_source_promotes_to_partially_verified` and by the auditor's
reading of the code).

### (b) Can a ticker-only or name-only match merge two entities?

**PASS.** Matcher reproductions:
- Same ticker, different name → `ambiguous`, rule `ticker_conflict_name`, no merge
  (and the importer's ambiguous path creates no company, only a quality report).
- Same name, different ticker → `none` (new entity, not a merge); the suite's
  rename test pins this (ENGRO vs ENGROH become 2 securities).
- Same ticker, name missing on one side → `none`, no merge.
- Multiple candidates → `ambiguous`.

### (c) Is a second import truly idempotent?

**PASS for core entities and evidence; FAIL for quality-report rows — see MEDIUM M3.**
Clean second import of the same record from the same source: `companies_created=0`,
`securities_created=0`, `evidence_created=0`, `skipped_as_duplicate=1`, and the
auditor's count delta across companies/securities/evidence/quality-reports/sectors
was `(0, 0, 0, 0, 0)`. The unique constraint on `registry_evidence` backs this in
the database, not just in application logic.

### (d) Does an ISIN disagreement really produce CONFLICTED rather than a merge?

**PASS for the core outcome, with a mutation caveat — see MEDIUM M2.**
Auditor reproduction: import `AUD2` with ISIN `PK0022222222`, then re-import same
ticker+name with ISIN `PK0033333333` → `conflicts=1`, company and security both
`CONFLICTED`, stored ISIN unchanged (`PK0022222222`), and a `conflicting_isin`
quality report is written. The conflicting ISIN is not merged in.

### (e) Can a sector from one source silently become canonical?

**PASS.** Auditor reproduction: import `AUD3` with sector "Sector X" from `src_a`,
then re-import the same company with sector "Sector Y" from `src_b`. Result: two
separate sector rows (`src_a`/`Sector X` and `src_b`/`Sector Y`), both with
`canonical_sector_id = NULL`, and the company's `sector_id` is unchanged (still
the first source's row). No canonical sector is assigned by guesswork. Note the
retained first-source sector is a documented design choice, not a silent promotion.

### (f) Does reconcile() ever invent a coverage ratio without a snapshot?

**PASS.** `reconcile(session, None)` returns `coverage_ratio=None` with an explicit
"no coverage claim" note (confirmed by the auditor and by the PG check script,
where in-transaction `registry_tickers=2` still yields coverage `None`).
`reconcile` with an empty-ticker snapshot also returns `None` (division guard:
`len(matched) / len(snap)` only when the snapshot set is non-empty).
With a real snapshot it reports matched/missing/extra honestly (suite fixture:
coverage 0.5, missing `MISSING`, extra `EXTRA`).

## Findings

### CRITICAL

None. No production data leak, no fabricated company/price/rating, no secret
exposure, and no live record is currently mislabeled (the registry is empty).

### HIGH

| ID | Finding | Evidence / reproduction |
|---|---|---|
| H1 | **VERIFIED on a single import labelled as an official source, with no independent corroboration.** `source_key` is a caller-supplied string; nothing in the importer or verifier checks that the data actually came from PSX or SECP. The "agreeing" evidence is self-generated from the same record, so the verification rule collapses to "the caller said this is official." The docs overstate the guarantee ("import success alone never promotes"; "derived from the evidence rows that actually exist, never from an import's success"). Any future collector that mislabels a source (typo, misconfiguration, or a scraped copy labelled `psx_official`) would produce `VERIFIED` rows that downstream consumers would trust as officially confirmed. | Auditor live-PG rollback run: single import with `source_key="psx_official"` → status `VERIFIED`. Code: `backend/app/services/registry/importer.py` (evidence written, then `verification.apply_verification_rules` called per record) and `backend/app/services/registry/verification.py` (`sources & OFFICIAL_SOURCES` → `VERIFIED`). The suite pins this in `test_import_official_source_verifies`. Fix direction (coordinator's job, not done here): correct the docs to state the rule honestly (single-official-source trust, not corroboration); add a provenance control before population — e.g. an allow-listed collector identity or a recorded source-provenance artifact per import batch — and consider requiring an official source PLUS one agreeing source, or a recorded official-document reference, before `VERIFIED` is granted. |

### MEDIUM

| ID | Finding | Evidence / reproduction |
|---|---|---|
| M1 | **ISIN or identifier agreement overrides a name disagreement without flagging it.** If ISIN matches candidate A, the matcher returns `unique` (rule `isin`) even when ticker and name both differ — the suite's `test_match_isin_wins` pins this (ticker `XXXX`, "Different Name" matched to the OGDC candidate). The importer's unique path then attaches the differently-named record's evidence to that company without writing any name-conflict quality report. The same applies to the identifier rule. ISIN-as-strongest-identifier is defensible, but a name that disagrees with the stored legal name should at minimum be flagged for review, since a wrong ISIN in the source would otherwise silently attach a stranger's evidence to a company. | Matcher reproduction: `match_record(ticker="NEW9", legal_name="Different Name Ltd", isin="PK0012345678", candidates=[OGDC candidate])` → `unique`, rule `isin`. Code: `matching.py` — the `ticker_conflict_name` guard only applies when it is the *sole* rule; any accompanying ISIN/identifier hit bypasses it. |
| M2 | **A conflicting import mutates the security's ticker before marking it CONFLICTED.** In the importer's unique path, the ticker-change block (adds a `SymbolHistory` row and rewrites `security.ticker`) runs *before* the ISIN-disagreement check, and the conflict branch then `continue`s without undoing it. A record that is ultimately rejected as conflicting still renames the security. | Auditor live-PG rollback run: import `AUD6` (ISIN `PK0066666666`, identifier NTN `1234567`); import via the same identifier with ticker `AUD6NEW` and ISIN `PK0077777777` → `conflicts=1`, status `CONFLICTED`, stored ISIN correctly kept, but ticker now `AUD6NEW` with a history row `('AUD6', 'AUD6NEW')`. Fix direction: check ISIN disagreement before applying the ticker change, or roll the ticker change back on conflict. |
| M3 | **Repeated ambiguous or conflicting imports are not idempotent in quality-report rows.** Core entities and evidence are idempotent (see (c)), but every ambiguous re-import appends a new `ambiguous_registry_record` row and every ISIN-conflict re-import appends a new `conflicting_isin` row and increments `conflicts` again. Re-importing a bad batch N times creates N duplicate reports. | Auditor live-PG rollback run: two identical ambiguous imports → quality-report delta +2, `pending_review=1` each time, companies unchanged; two identical ISIN-conflict imports → quality-report delta +1 on the second run, `conflicts=1` again. Fix direction: de-duplicate quality reports on (issue_type, affected entity, source, record key) or report "already reported" on repeats. |
| M4 | **`listing_status` is silently dropped.** `SourceRecord` accepts `listing_status` (`active` / `suspended` / `delisted` / `inactive`), but the importer never reads it: a new company is always created with `status="UNVERIFIED"` and `delisting_date=None`. A delisted issuer imported as `delisted` would be stored indistinguishably from an active one. | Auditor live-PG rollback run: import `AUD4` with `listing_status="delisted"` → company status `UNVERIFIED`, `delisting_date` `None`. Code: `importer.py` new-company branch sets no listing-status field. Fix direction: store the source's listing status verbatim on the record/evidence (or reject the field until it is stored) so the information is not silently lost. |
| M5 | **Identifiers supplied on a matched (re-import) path are used for matching but never stored.** Only the new-entity path writes `CompanyIdentifier` rows (plus the ISIN-fill branch). A second source that supplies a new identifier (e.g. SECP number) for an already-known company matches by ticker+name and then discards the identifier. Future matches that could have used that identifier therefore cannot. | Auditor live-PG rollback run: import `AUD7` from `src_a` with no identifiers; re-import from `src_b` with identifier `SECP`/`C-999` → stored identifiers for the company: `[]`. |

### LOW

| ID | Finding | Evidence / reproduction |
|---|---|---|
| L1 | **Two alembic configurations; the backend one cannot see Phase 3/4 revisions.** `backend/alembic.ini` points at `backend/alembic/versions/` (only `0001_baseline_empty.py`), so `alembic current` from `backend/` fails to locate `a909e8449cdd` or `20261104_0004`. The working path is `database/alembic.ini` (from `database/`). Phase 4 docs mention `alembic current` generically (`registry_statistics.md`) without stating which configuration, which will mislead the next operator. Pre-existing (Phase 2/3 layout), surfaced by Phase 4's migration. | Auditor runs: from `backend/` → "Can't locate revision identified by 'a909e8449cdd'"; from `database/` → head resolved and the downgrade/upgrade cycle worked. |
| L2 | **Evidence row with an empty `observed_name` counts as an agreeing source.** In `verification._distinct_agreeing_sources`, when the stored name or the observed name is missing, the `else` branch adds the source unconditionally instead of skipping the row. The importer always sets `observed_name`, so this is reachable only via direct evidence inserts today, but it weakens the "agrees on name" guarantee as written. | Code reading: `verification.py`, `_distinct_agreeing_sources` else branch. |
| L3 | **ISIN check digit is not recomputed** (format only). Documented in `normalization.py` as a Phase 5+ concern, so this is a recorded limitation, not a surprise — but a format-valid ISIN with a wrong check digit would still match and merge. | Code reading: `normalization.normalize_isin` docstring states the check digit is NOT recomputed. |
| L4 | **Frontend fetches `/registry/statistics` but discards the result.** `frontend/app/companies/page.tsx` requests statistics alongside companies and uses only the companies response; the badge shows the companies total. Harmless (no fabrication — it shows real API data), but the unused fetch should either drive the badge or be removed. | Code reading: `page.tsx` `Promise.all([...])` destructures only `[companies]`. |
| L5 | **`reconcile()` with a malformed snapshot dict raises `KeyError`.** It indexes `snapshot["tickers"]` directly; only `load_snapshot` guarantees the key. Reachable only by a direct caller passing a hand-built dict without `tickers`. | Code reading: `reconciliation.reconcile`. |
| L6 | **Pytest suite exercises the importer only against a fake session** (`FakeSession` in `test_registry.py`), which does not enforce real database constraints (evidence unique constraint, foreign keys) or real transaction semantics. The gap is partly mitigated by the rolled-back live-PG check script, but only for the clean import path — the ambiguous, conflict, and DQR-duplication paths (M2, M3) are not covered against real PostgreSQL by any test. | Code reading: `test_registry.py` header states tests are offline with a fake session; `run_phase4_pg_check.py` covers only clean import + reconcile-None + API smoke. |

## Claim-by-claim verification

| Coordinator claim | Auditor verdict |
|---|---|
| Phase 2 PARTIALLY COMPLETE carried forward (Docker definition-only, Playwright not run) | **Consistent.** `test_report.md` explicitly lists Docker, Playwright E2E, and CI as NOT run / NOT claimed. The auditor did not re-run Docker or Playwright. |
| Phase 3 COMPLETE baseline (54 tables, head `20261104_0004`, 56 public tables, 53 tests, 0 business rows) | **Consistent with the chain.** Live head before Phase 4's migration was `20261104_0004` (downgrade target confirmed); after Phase 4, 57 public tables = 56 + `registry_evidence`. The auditor did not re-audit Phase 3 itself. |
| Phase 4 adds migration `a909e8449cdd` creating `registry_evidence` | **Verified.** File read; live head is `a909e8449cdd`; downgrade/upgrade cycle works; `phase2_probe` retained. |
| Normalization / matching rules (ticker+name, ISIN, identifier; ticker-alone and name-alone insufficient; ambiguous never merged) | **Verified**, except for the M1 caveat (ISIN/identifier overrides a name disagreement). |
| Importer idempotent, never sets VERIFIED/PARTIALLY_VERIFIED, symbol_history on ticker change, CONFLICTED on ISIN disagreement | **Mostly verified, wording inaccurate.** Idempotency holds for companies/securities/evidence; CONFLICTED works; symbol_history works. But "never sets VERIFIED" is false in effect for the official-source path (H1), and the ticker-change + conflict ordering leaks a rename into a conflicted record (M2). |
| Verification: VERIFIED only from official sources agreeing on name; PARTIALLY_VERIFIED from ≥2 distinct agreeing sources | **PARTIALLY_VERIFIED verified; VERIFIED overstated.** The official-source rule holds as coded, but "agreeing" is self-agreement on a single import (H1), and `source_key` provenance is unchecked. |
| Reconciliation: no snapshot ⇒ coverage None, no claim | **Verified.** |
| Sync config: manual-only, no scheduler | **Verified by reading `sync_config.py`** (all defaults `frequency="manual"`, `enabled=False`) and by the absence of any scheduler in the Phase 4 files. |
| APIs: 9 endpoints, pagination max 200, 404s, 422 on bad limit | **Verified** via the PG check script's smoke test (all 9 paths 200 on empty DB, 404s for ids `999999`, 422 for `limit=999`) and by reading `registry.py` (`MAX_LIMIT = 200`, `skip < 0` → 422). Endpoints are read-only and return only existing rows; unconfigured DB → 503 (code path, not live-tested by the auditor since a DB was configured). |
| Frontend renders ONLY API rows, with empty/unavailable states; typecheck/lint/build pass; Vitest 11 passed | **Verified.** Auditor re-ran all four (typecheck pass, lint pass, build pass with `/companies`, Vitest 11 passed). Page code shows a "Registry unavailable" state and an honest empty-table description; no fabricated rows. |
| Backend pytest 36 passed (18 Phase 4 + 18 Phase 2 re-run), ruff clean | **Verified exactly** (36 passed, 1 warning; ruff clean on Phase 4 files and on the whole backend). |
| Live-PG check script `PHASE4_PG_CHECK_OK` with rollback and 0 live business rows | **Verified exactly**, including the post-rollback 0 counts. |
| Production registry EMPTY because no usable official source was obtainable | **Verified and the conclusion is justified.** `source_research.md` and its raw snapshots record: DPS Listing Status yields 0 rows via text fetch (JS-driven, caveat stated, not presented as proof DPS has no data); direct DPS access from this VM fails (`NoHealthyNode`); the DPS market-watch text copy is a stale 2026-01-25 cache (283 days old) with no company names and numeric sector codes without a mapping; the PSX homepage gives 26 partial scrip rows with no names/sectors/statuses. None of this material was imported, which is the correct decision — importing the stale cache or the partial rows would have fabricated registry content. README-derived figures (~496 symbols, 38/37 sectors) are explicitly labelled "README claim, not live-verified" and are not presented as registry data. |
| Live backend check on port 8003 (statistics 200, companies 200, health 200, server stopped) | **Not re-verified by the auditor** (the server was stopped per the report, and the auditor did not restart it). Nothing contradicts it; it is recorded here as coordinator-reported only. |
| Frontend live-preview status | **Verified as honestly UNVERIFIED.** `frontend_documentation.md` states the live preview URL is UNVERIFIED (github.dev returns a sign-in page), that no browser-rendered screenshot was obtained, and that this is a parent check if visual confirmation is required. No screenshot is claimed anywhere in `docs/phase-04/`. |
| "Verified" wording elsewhere in docs | **No other overclaim found.** `source_research.md` explicitly marks every unverified source as UNVERIFIED or README-only, and `registry_statistics.md` reports empty status breakdowns. The one wording problem is the verification guarantee itself (H1), not the population claims. |

## Secrets / fabrication check

- Grep over all new/changed Phase 4 files (`backend/app/services/registry/`,
  `backend/app/api/v1/endpoints/registry.py`, `backend/app/models/registry.py`,
  `docs/phase-04/`, `frontend/app/companies/page.tsx`,
  `scripts/run_phase4_pg_check.py`) for `password`, `secret`, `token`, `api_key`,
  `bearer`, and credential-like values: **no credential values found**. The only
  "password" hit is a sentence in `frontend_documentation.md` stating that no
  GitHub password was asked for or entered — not a credential.
- `database/.env` is git-ignored (`git check-ignore` confirms) and its value was
  never printed by the auditor or by the PG check script (the script asserts the
  variable exists but never logs it).
- No fabricated company, price, or rating found in code, docs, or frontend.
  Example company names in tests and docs (`OGDC`, `ENGROH`, `Test Alpha Limited`)
  are either real well-known tickers used as match fixtures or explicitly labelled
  TEST ONLY records that exist solely inside rolled-back transactions. The
  frontend's statistics fetch is real API data, not placeholder figures.
- The PG check script's `TESTA`/`TESTB` records and the auditor's `AUD1`–`AUD7`
  records existed only inside rolled-back transactions; final live counts are 0.

## What must happen before Phase 5 (auditor's recommendations, not fixes)

1. **Correct the verification wording and close H1's trust gap** before any
   population run: state plainly that a single official-source import is
   source-label trust, not corroboration, and add a provenance control for
   `source_key` (allow-listed collector or a recorded provenance artifact per
   batch). Until then, no downstream consumer should treat `VERIFIED` as
   independently confirmed.
2. **Fix M2's ordering** (ISIN-disagreement check before ticker mutation) and
   **M3's quality-report de-duplication** before the first real import batch,
   since both corrupt or pollute state on exactly the messy inputs real
   population will produce.
3. **Decide M4 and M5 explicitly**: either store `listing_status` and matched-path
   identifiers, or remove them from the import contract so a caller cannot
   believe they were recorded.
4. **Add one real-PostgreSQL importer test** (rolled-back transaction, in the
   style of `run_phase4_pg_check.py`) covering the ambiguous, conflict, and
   re-import paths, so L6's fake-session gap does not hide the next M2/M3-class
   defect.
5. **Record the working alembic invocation** (`database/alembic.ini` from
   `database/`) in the Phase 4 docs (L1) so the next operator does not follow
   the broken `backend/` path.
6. **Population remains blocked** on a usable official registry source. The
   PARTIALLY COMPLETE verdict stands until such a source is obtained and
   reconciled; the stale 2026-01-25 cache and the 26 partial homepage rows must
   not be promoted into registry rows to make the numbers look better.

## Auditor's closing statement

Phase 4 delivers a sound, honestly documented registry engine with a genuinely
empty production registry — the discipline this project requires. The defects
found are in the verification trust model and in messy-input edge cases, not in
the headline counts, and none of them has yet affected a real record because
there are no real records. Fix H1's wording/provenance and M2/M3 before
population, and this phase's work is a safe foundation for Phase 5.
