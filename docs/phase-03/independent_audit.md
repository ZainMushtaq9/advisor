# Phase 3 — Independent Audit

**Auditor:** Independent audit agent (did NOT build Phase 3).
**Date:** 2026-11-04. **Branch:** `phase-03-database-storage`.
**Scope:** Phase 3 only — Complete Database Architecture and Financial
Data Storage Engine. Phase 2 is taken as its own report states it
(see §1); Docker/Playwright were NOT re-tested here.

**Method (what the auditor actually did, not what was claimed):**

- Read `docs/phase-02/PHASE_2_ACCEPTANCE_REPORT.md`,
  `docs/phase-03/test_report.md`, and all 24 files in `docs/phase-03/`.
- Read all five model files, both new migrations, `env.py`,
  `storage/phase3_engine.py`, and `backend/app/services/data_quality.py`.
- Counted model tables by importing `app.models` metadata (not by
  trusting docstrings): **54**.
- Ran read-only PostgreSQL queries (SELECT only) and `alembic current`
  with `DATABASE_URL` sourced from the gitignored `database/.env`
  (never printed, never committed). **No `alembic downgrade` or
  `upgrade` was run** — the task forbade it — so the migration
  down/up cycle and the restore run are coordinator-claimed only
  (see Limitations).
- Re-ran the four test suites exactly as specified (see §3).
- Ran seven rolled-back audit probes in a single transaction each
  (all rolled back; production tables still hold zero rows afterwards).
- Ran `git status`, a full secret-name column scan over all 54 tables,
  `alembic check` (read-only metadata-vs-database comparison), and
  re-hashed the 2026-11-04T1217-PKT backup files.
- **Nothing was committed, pushed, migrated, or collected. No PSX
  data, no money, no Phase 4 work.**

## Verdict: PASS WITH LIMITATIONS — Phase 3 is NOT COMPLETE

The Phase 3 foundation is real and mostly as claimed: the schema
exists in the live database at the claimed revision, all 44 tests
pass on re-run, the backup hashes match, there are zero business
rows, zero secret-named columns, zero paid services, and zero broker
or trade paths. Phase 4 design work may proceed against this schema.

But a COMPLETE stamp would be dishonest today, for three HIGH
reasons (§4, H1–H3) plus the uncommitted state of the work (M8):

1. The quality-vocabulary CHECK that the migration docstring claims
   for "every provenance-carrying table" covers only 21 of the 22
   such tables — `financial_statements` itself is unprotected, and
   the auditor inserted a `BOGUS_STATUS` there successfully.
2. The data-quality registry cannot be resolved as documented: the
   immutability trigger blocks the very status change the docs
   describe for resolution.
3. The duplicate-prevention grains fail when the source is NULL
   (PostgreSQL treats NULLs as distinct) — duplicate market prices
   were inserted successfully — and several tables documented as
   "append-only" have no trigger at all.

Fix H1–H3, commit the work (M8), and either independently re-run
the migration cycle and restore in a scratch database or explicitly
waive those two re-runs in writing. Until then the honest status is
**PASS WITH LIMITATIONS**, in the same spirit as Phase 2's
PARTIALLY COMPLETE.

**No CRITICAL rating — and why.** No finding touches live money,
live data, or secrets today: all business tables hold zero rows, no
ingest writer exists yet, and every money/secret/trade claim
verified true. The HIGH findings are latent: they become
data-corrupting or verification-falsifying the moment ingest begins
on this schema. If Phase 3 were stamped COMPLETE without fixing
them, H1 in particular would deserve re-rating to CRITICAL.

## 1. Phase 2 gate (carried forward, not re-audited)

| Phase 2 claim | Auditor check |
|---|---|
| PARTIALLY COMPLETE; all 22 items pass or pass via item-17 alternative | Read the acceptance report; consistent with its own text. Not re-run. |
| Docker definition-only, Playwright not run | Carried forward unchanged. Phase 3 docs repeat this honestly (`database_architecture.md`: "no Docker/Playwright verification (both remain UNVERIFIED from Phase 2)"). Still open. |
| Migration fresh down/up team-reported (Phase 2 limitation) | Still team-reported. Phase 3's own cycle claim has the same status for this auditor (see Limitations). |

## 2. Evidence table — every Phase 3 claim checked

| # | Claim | Evidence found | Verdict |
|---|---|---|---|
| 1 | 54 SQLAlchemy model tables in `backend/app/models/` | Imported metadata: exactly 54 tables; per-file counts reference 11, market 8, financial 15, analysis 13, governance 7. | PASS |
| 2 | 56 public PostgreSQL tables | Live query: 56 = 54 models + `phase2_probe` + `alembic_version`. `database_architecture.md` states this decomposition correctly. | PASS |
| 3 | 14 triggers (7 immutable + 7 versioned) | Live `pg_trigger` count: 14. Immutable: audit_logs, market_prices, raw_payloads, data_quality_reports, market_snapshots, announcements, news. Versioned: financial_statements, financial_statement_line_items, economic_indicators, valuations, forecasts, recommendations, financial_health_assessments. | PASS (count); see H2/H3/M3/M4 for scope gaps |
| 4 | Quality CHECK constraints on 21 tables | Live query: exactly 21 `ck_*_quality_status` constraints, matching migration `20261104_0003`'s `QUALITY_TABLES`. | PASS (count); FAIL on the "every provenance table" wording — see H1 |
| 5 | Alembic env wired to `app.models` | `database/migrations/env.py` imports `app.models.Base`; `alembic current` reads `20261104_0003 (head)`. The BASE_DIR path fix is real (3 levels up). | PASS |
| 6 | Fresh migration down/up cycles passed | NOT re-verified by this auditor (migrations forbidden by task). `alembic check` (read-only) shows zero model-vs-database drift except the intentional `phase2_probe` retention. Head revision and 56 tables / 14 triggers corroborate the post-upgrade state, but the cycle itself remains coordinator-claimed. | NOT INDEPENDENTLY VERIFIED |
| 7 | Storage engine `storage/phase3_engine.py` | Read in full. Manifest register/verify, quarantine, tmp-prune (dry-run default), pyarrow guard all behave as documented; storage tests pass. See L5 for edge gaps. | PASS with L5 |
| 8 | Data-quality helpers `backend/app/services/data_quality.py` | Read in full. OHLC, balance-sheet, cash-flow, conflict, duplicate-key helpers work as tested. See M1 (upgrade bypass) and L7 (tolerance underspecified). | PASS with M1 |
| 9 | 44 tests passing | Re-run: **44 passed, 1 warning** (see §3). Exact per-file match. | PASS |
| 10 | Backup 2026-11-04T1217-PKT, SHAs match, restore VERIFIED to separate DB | Re-hashed both files: dump SHA `76596f98…b5958` and archive SHA `555c5b8f…9ec6` match `manifest.json` exactly. Restore-test database `psx_intelligence_restore_test` exists. Restore itself NOT re-run by this auditor; row-count gate 0=0 is consistent with current probe row count 0. | PASS (hashes + DB existence); restore run itself NOT INDEPENDENTLY VERIFIED |
| 11 | Paid services ZERO | Backend requirements are free/open-source pins only; no paid dependency, no hosted DB, no new dependency in Phase 3. pyarrow absent, guard live. | PASS |
| 12 | No PSX data collected | Full row count over all 54 model tables: **0**. Probe table: 0. | PASS |
| 13 | No real trades / broker path | Full column scan over all 54 tables: zero columns matching password/api_key/secret/token/broker/credential. No order table. Portfolios are paper-only in code and docs. | PASS (stronger than the test, which checks only 2 tables — see L4) |
| 14 | No secrets in code/commits | Grep over new models, services, engine, migrations, docs: no credential values, keys, or tokens. `database/.env` is gitignored (mode 0600); `.venv/`, `node_modules/`, `storage/backups/*` are gitignored; `git status` shows none of them untracked-for-commit. | PASS, except the work itself is uncommitted — see M8 |
| 15 | 33 Phase 1 entities covered | All 32 non-ratio Phase 1 entities exist verbatim; `ratios` is split into `fundamental_metric_definitions` + `fundamental_metric_values`. See M5 for what the split loses. | PASS with M5 |
| 16 | Docs: "24 files + test_report.md = 25" | Actual: **24 files total in `docs/phase-03/`, including `test_report.md`**. The claim overcounts by one. This audit file is the 25th. | FAIL (count only; content unaffected) — L1 |
| 17 | "CHECK-enforced on 21 tables" (entity_catalog, provenance doc, migration guide) | Accurate as a count. The problem is only the stronger wordings elsewhere ("every provenance-carrying table", "on every record") — see H1/M7. | PASS (count) |
| 18 | "Duplicates are prevented by grains and hashes" | Grains hold only when source is non-NULL (see H3); hashes are unique-constrained ONLY on `raw_payloads.content_hash` — announcement/news/document hashes are nullable and non-unique (see M6). | FAIL (overclaim) |
| 19 | "Resolution is a status change plus a new row" (data_quality_reports) | Status change is trigger-blocked (probe D). The doc describes a workflow the database forbids. | FAIL — H2 |
| 20 | Indexed-query test proves index use | Test asserts index *existence* in `pg_indexes`, not a planner index scan — but its own comment and `indexing_strategy.md` disclose this honestly. Planner behaviour at scale is explicitly deferred to Phase 5/6. | PASS with disclosure — L3 |
| 21 | SQLite decision (metadata-only schema tests) | Honest and correct: PostgreSQL Identity on BIGINT cannot be reproduced on SQLite; the tests say what they prove and what they do not. No SQLite schema claim is made. | PASS |
| 22 | Phase 3 HEAD = the Phase 3 work | **False in git terms.** Branch is `phase-03-database-storage`, but HEAD is still the Phase 2 commit `016f3c8`; all Phase 3 files are uncommitted working-tree changes (see M8). The work exists on disk and in the live DB, but not in any commit. | FAIL — M8 |

## 3. Test re-run (auditor-observed, 2026-11-04)

Command: `backend/.venv/bin/python -m pytest
database/tests/test_phase3_schema.py
database/tests/test_phase3_postgres.py backend/tests
storage/test_phase3_engine.py -q` with `DATABASE_URL` sourced from
`database/.env`.

| Suite | Auditor result | Claimed |
|---|---|---|
| `database/tests/test_phase3_schema.py` | 10 passed | 10 passed |
| `database/tests/test_phase3_postgres.py` | 10 passed | 10 passed |
| `backend/tests/` (Phase 2 suite, re-run) | 18 passed | 18 passed |
| `storage/test_phase3_engine.py` | 6 passed | 6 passed |
| **Total** | **44 passed, 0 failed, 1 warning** (Starlette deprecation, non-blocking, as claimed) | 44 passed, 1 warning |

No test failed. Every test failure below would have been reported
as a finding; there were none. Test *strength* gaps (as opposed to
failures) are recorded as L3/L4 and in M1/M2 (untested invariants).

## 4. Findings

### HIGH

**H1 — `financial_statements.quality_status` has no CHECK constraint,
despite the claim that the vocabulary is enforced "on every
provenance-carrying table".**
Migration `20261104_0003`'s docstring says the CHECK is enforced
"on every provenance-carrying table", and `database_architecture.md`
principle 1 says quality status is on "every market/financial/news/
analysis record". In fact there are 22 tables with a `quality_status`
column (all `ProvenanceMixin` tables plus hand-defined
`financial_statement_line_items`), but `QUALITY_TABLES` lists only
21 — `financial_statements` is missing. Live verification: it is
absent from `information_schema` CHECKs, and audit probe A inserted
`quality_status='BOGUS_STATUS'` into `financial_statements`
successfully (rolled back). Compounding it, `base.py` defines a
`QUALITY_CHECK` CheckConstraint that is **never attached to any
table** — dead code that looks like model-layer enforcement but
enforces nothing. The 21-table count itself is accurate; the
"every table" wording and the missing constraint are the defect.
*Fix:* new migration adding `ck_financial_statements_quality_status`
(and either attach `QUALITY_CHECK` to provenance tables or delete
the dead definition so it cannot mislead again).

**H2 — `data_quality_reports` cannot be resolved as documented: the
immutability trigger blocks its own resolution workflow.**
`data_quality_reports` is in the immutable trigger set, so UPDATE
and DELETE always raise. But `provenance_and_quality.md` and
`governance.py` both describe resolution as "a status change plus a
new row where data changed", and the table's own
`resolution_status` (default `open`) and `resolved_at` columns exist
precisely to be updated. Audit probe D confirmed: updating
`resolution_status` to `resolved` raises `ProgrammingError` from the
trigger. As built, every report is stuck `open` forever, or
resolution requires inserting a duplicate report row while the
original stays open — corrupting resolution counts either way.
*Fix (choose one, document it):* move `data_quality_reports` to the
versioned-trigger set (only `resolution_status`/`resolved_at` may
change), or change the docs and workflow to resolution-by-new-row
with a link to the original and a query that treats the latest row
as current. Do not leave the contradiction in place.

**H3 — Duplicate-prevention grains fail when `data_source_id` is
NULL (PostgreSQL NULLs are distinct).**
`market_prices`, `index_prices`, and `financial_statements` all put
nullable `data_source_id` in their unique grain. Audit probe B
inserted two `market_prices` rows for the same security, date, and
bar type with `data_source_id = NULL` and different closes —
both accepted. The same hole applies to the other two grains.
`relationships_and_constraints.md` does disclose this ("NULL
weakens a grain… production ingest must always set a source"), so
this is a known, disclosed limitation rather than a hidden false
claim — but disclosure is not enforcement, and the
duplicate-detection doc still claims duplicates "are prevented by
grains". *Fix before production ingest:* `NOT NULL` on
`data_source_id` for grain tables, or partial unique indexes
excluding NULL-source rows plus a rule that source-less rows go
through review, with a test inserting the NULL-source duplicate.

### MEDIUM

**M1 — `upgrade_quality_status` guards only one upgrade path.**
The helper raises without evidence only for
`UNVERIFIED → VERIFIED/PARTIALLY_VERIFIED`. Audit probes confirmed
`REJECTED`, `CONFLICTED`, `MISSING`, `STALE`, and `PENDING_REVIEW`
all upgrade to `VERIFIED` with empty evidence, silently. The
integrity-rules claim ("helper raises without evidence") is stated
without that qualification, and the existing test covers only the
`UNVERIFIED` path. No production writer calls this helper yet, so
the exposure is latent — but this is the named enforcement point
for "never mark unverified as verified", and it is weaker than
claimed. *Fix:* require evidence for ANY transition into
`VERIFIED`/`PARTIALLY_VERIFIED` from any non-verified state
(including re-affirmation), and add tests for the bypass states.
Note the helper can never be the whole enforcement: direct database
writes bypass it entirely, which is why H1's CHECK matters.

**M2 — Version chains are unenforced: no FK on `supersedes_id`,
no single-current invariant.**
`supersedes_id` is a bare `BigInteger` on every `VersionMixin`
table and on `financial_document_versions` — no foreign key.
Audit probe G inserted `supersedes_id = 999999999` (nonexistent)
successfully. Audit probe E inserted two `financial_statements`
rows for the same grain both with `is_current = TRUE` — nothing
prevents it (no partial unique index on grain + `is_current`).
`versioning_policy.md` acknowledges flags "if [they] ever
disagree" and names max(`version_number`) as tiebreaker, but no
check, query, or test detects a disagreement, so the tiebreaker is
aspirational. *Fix:* add self-referencing FKs on `supersedes_id`
(where the design allows it) and either a partial unique index
enforcing one current row per grain or a scheduled data-quality
check that reports multi-current grains as findings.

**M3 — `financial_document_versions` is versioned in name only.**
It has `version_number` and `supersedes_id` but no `VersionMixin`
(no `is_current` column at all) and no versioned trigger. Audit
probe C updated a version row's `content_hash` in place
successfully. `versioning_policy.md` claims "models carry
VersionMixin on versioned tables" — false for this table.
*Fix:* give it `VersionMixin` (or document why it is exempt) and
add it to the versioned-trigger set.

**M4 — Several tables documented as "append-only" have no trigger.**
`market.py`'s module docstring says "All append-only", and
`schema_reference.md` groups the market tables under "Market
(append-only)". But `index_prices`, `corporate_actions`
("Append-only dated events"), and `symbol_history` ("Append-only
rename/transfer history") have no immutability trigger: audit
probes H/H2/H3 updated all three in place successfully.
`model_versions` ("Immutable reference"), `forecast_evaluations`
("Append-only"), and `agent_executions` ("Append-only run record")
are likewise unprotected (the last legitimately needs status
updates, which is exactly why its docstring overclaims).
`live_quotes` mutability is justified by the `is_latest` marker,
but nothing stops editing/deleting *old* quote rows either.
*Fix:* either add the missing triggers (with the documented
`is_latest`-style carve-outs where a marker must flip) or correct
every "append-only" docstring to name the tables that are actually
protected. The trigger list in `entity_catalog.md` is accurate;
the surrounding prose is not.

**M5 — Phase 1 `ratios` mapping is lossy.**
The split into `fundamental_metric_definitions` +
`fundamental_metric_values` is a reasonable realisation, and the
catalog documents it — but three Phase 1 `ratios` properties are
silently dropped: (a) `security_id` — per-security multiples such
as P/E cannot be represented (values are company-only); (b)
`computation_status` (`computed`/`failed`/`insufficient_inputs`) —
a NULL value is commented as NOT_CALCULABLE but no status column
distinguishes "not calculable" from "not yet computed"; (c)
`input_price_id` — price-based multiples have no price linkage.
`input_statement_ids` is also JSON, not a foreign-key array, so
dangling statement references are possible (same class of gap as
M2). Additionally, `entity_catalog.md`'s arithmetic is wrong: it
says "33 plus 21 extension tables", but the true decomposition is
32 direct Phase 1 tables + 2 ratio-split tables + 20 other
extensions = 54 (its own enumeration omits `index_prices` and
`financial_documents`). *Fix:* record the three drops as explicit
design decisions (or restore `security_id`/`computation_status` to
`fundamental_metric_values`) and correct the catalog arithmetic.

**M6 — Hash duplicate detection is not schema-enforced except on
`raw_payloads`.**
Only `raw_payloads.content_hash` is unique. `announcements.
document_hash`, `news.content_hash`, and `financial_documents.
content_hash` are nullable and non-unique, so re-ingesting the same
announcement or document creates a duplicate row — the database
will not stop it. `duplicate_detection.md` claims duplicates "are
prevented by grains and hashes, not by convention", which overstates
the hash half: for announcements/documents, duplicate prevention is
currently convention (or a future collector check), not schema.
*Fix:* add unique constraints on the hash columns (with the
NULL-hash case routed to review, as the helper already specifies),
or soften the doc to state exactly which hashes are enforced.

**M7 — Provenance block is incomplete where the architecture claims
it is universal.**
`database_architecture.md` principle 1 claims source, source
timestamp, collected-at, and quality status on "every
market/financial/news/analysis record" (dropping `base.py`'s own
"where it is meaningful" qualifier). In fact
`financial_statement_line_items` carry no `data_source_id`,
`source_timestamp`, or `collected_at` (only a hand-defined
`quality_status`, plus extraction fields); `financial_documents`,
`forecast_evaluations`, `fundamental_analysis_runs`,
`technical_calculation_runs/errors`, and portfolio tables carry no
provenance block at all. Line-item provenance is parent-indirect
only (via the statement row), which is workable but is not what the
principle states. *Fix:* qualify the principle to "where
meaningful, else via the parent row", and list the tables that rely
on parent provenance.

**M8 — Phase 3 work is uncommitted; HEAD is still Phase 2.**
Branch `phase-03-database-storage` is checked out, but HEAD is
`016f3c8` (Phase 2 push-blocked record). `git status` shows one
modified file (`database/migrations/env.py`) and seven untracked
paths (`backend/app/models/`, `backend/app/services/`, both new
migrations, `database/tests/`, `docs/phase-03/`,
`storage/phase3_engine.py`, `storage/test_phase3_engine.py`).
No `.env`, `.venv`, backup dump, or `node_modules` is in commit
scope (all correctly gitignored) — the problem is the opposite:
nothing Phase 3 is preserved in any commit, so it cannot be
reviewed as a commit, pushed, or recovered from the branch. The
task's premise ("HEAD should be the Phase 3 work") is false.
*Fix:* commit the Phase 3 work on this branch and re-verify
`git status` clean (excluding ignored paths) before any COMPLETE
stamp. This audit file itself is untracked until that commit.

**M9 — Migration cycle and restore are coordinator-claimed, not
independently verified.**
This auditor was forbidden from running migrations and did not
re-run the restore. Corroboration exists (head revision, 56 tables,
14 triggers, backup SHAs, restore DB present, zero rows), but the
down/up cycle and the restore run itself rest on the coordinator's
report. *Fix before COMPLETE:* re-run a full downgrade/upgrade
cycle and a restore against a scratch database (never the live
one), or record an explicit written waiver naming these two items.

### LOW

**L1 — Doc count off by one.** `docs/phase-03/` holds 24 files
including `test_report.md`, not "24 + test_report = 25". This file
is the 25th.

**L2 — Dangling references.** `database_architecture.md` says
disagreements are "recorded in `phase_03_completion_report.md`",
and four docs refer to a "defect register" — neither file exists
in `docs/phase-03/`. The defect history (SQLite failure, downgrade
fixes, path bug) is narrated across docs but has no single home.

**L3 — Indexed-query test name overclaims.** The test is named
`test_indexed_query_uses_security_date_index` but asserts only
index existence + row return. Mitigated: its comment and
`indexing_strategy.md` disclose this explicitly. Rename or
re-scope the test name to match the assertion.

**L4 — No-secret test is narrower than its claim.** It checks only
`Portfolio` and `Company` columns for five names. The claim holds
(auditor's full 54-table scan found zero secret-named columns), but
the test should scan all tables to prove it. Residual note: JSON
payload/evidence columns (`agent_outputs.payload`,
`market_snapshots.payload`, evidence JSONs) cannot be constrained
by column names — keeping secrets out of them remains a convention,
not a schema guarantee.

**L5 — Storage engine edge gaps.** `quarantine_file` moves to
`quarantine/<basename>`, so quarantining two same-named files from
different directories silently overwrites the first (and its reason
file). `register_dataset` overwrites an existing manifest for the
same key without complaint. `verify_dataset` re-checks SHA-256 but
ignores the recorded `byte_size`. `RETENTION` is declarative only;
no engine function consults it (prune behaviour is hardcoded to
`tmp/`). None of these affects the tested happy paths.

**L6 — Source-verification vocabulary is unenforced and
inconsistent.** `data_sources.verification_status` defaults to
lowercase `unverified` while the quality vocabulary is uppercase
`UNVERIFIED`, with no CHECK constraint. The rule "an unverified
source's rows must not be presented as verified" is enforced
nowhere in code — it is a presentation rule for a later phase.
Record it as a Phase 5 consumer requirement, not a Phase 3
guarantee.

**L7 — Helper tolerances and edge cases.** `validate_ohlc` skips
high/low bound checks whenever any value is missing or negative
(the findings are still returned, so this is fail-visible, not
fail-silent). Balance-sheet/cash-flow tolerance `0.01` is absolute
with no documented unit or scale rule — for statements normalised
to base rupees from millions/billions reporting, the tolerance's
meaning needs one sentence in the doc.

**L8 — Carried-forward Phase 2 limitations (not Phase 3 defects).**
Docker definition-only, Playwright not run, CI not run in CI.
Phase 3 docs state these honestly; they still bar a
no-qualifications COMPLETE stamp for the project as a whole.

**L9 — `quality_status` default is Python-side only** (no server
default). Fail-safe direction: a raw-SQL insert omitting the column
fails on NOT NULL rather than silently defaulting. No action
needed; noted so a future "missing default" report is not mistaken
for a gap.

**L10 — `schema_reference.md` wording slips.** Forecasts are
described with intervals/scenarios "all NOT NULL where the design
requires" — in fact only `interval_low`, `interval_high`, and
`uncertainty` are NOT NULL (bear/base/bull/probabilities are
nullable, correctly). `financial_document_downloads` is grouped
under "(hash duplicate key)" but has no hash column.

## 5. What must be fixed before Phase 3 can be called COMPLETE

1. **H1:** migration adding the `financial_statements` quality
   CHECK; resolve or remove the dead `QUALITY_CHECK` in `base.py`.
2. **H2:** resolve the `data_quality_reports` trigger-vs-resolution
   contradiction (versioned trigger with a documented carve-out,
   or resolution-by-new-row workflow) and update docs + tests.
3. **H3:** close the NULL-source grain hole (NOT NULL or partial
   unique index + review path) with a regression test for the
   NULL-source duplicate.
4. **M8:** commit all Phase 3 work on `phase-03-database-storage`
   and verify clean status (ignored paths excluded).
5. **M9:** independently re-run the migration down/up cycle and the
   restore in a scratch database, or record an explicit waiver.
6. **M1–M7:** fix or explicitly accept-and-record each MEDIUM item
   (upgrade-bypass states, supersedes FK / single-current, document
   versions trigger, append-only prose vs triggers, ratios drops,
   hash uniqueness, provenance scope). Acceptance must be a written
   decision per item, not silence — several are currently
   documented as if already true.
7. **L1–L2:** correct the doc count and either create the
   completion report / defect register or remove the references.
8. Re-run the four suites after fixes and confirm 44+ passing
   (plus new regression tests for H1–H3) with zero business rows.

## 6. Limitations of this audit

- No migration was run (forbidden); no restore was re-run; no
  downgrade/upgrade behaviour was observed first-hand.
- No Docker, Playwright, frontend, or CI verification (carried
  forward from Phase 2, unchanged).
- No ingest, collector, API, or frontend consumer exists yet, so
  several findings are proven at the schema/helper level (probes,
  code reading) rather than through a production write path — which
  is precisely why they should be fixed before ingest begins.
- Audit probes ran inside rolled-back transactions; the auditor
  verified zero business rows afterwards, but did not re-verify
  every table's count post-probe beyond the full 54-table count
  (0) and the probe-table count (0).
- Secrets handling: `DATABASE_URL` was sourced, never printed, and
  appears nowhere in this report or in any file the auditor wrote.

## 7. Positive confirmations (for the record)

- `alembic check` (read-only) reports zero model-vs-database drift
  except the intentional `phase2_probe` retention — the autogenerated
  migration faithfully matches the models.
- Migration `645bcd200539` creates exactly 54 tables; its downgrade
  correctly avoids recreating the probe table (the documented
  hand-edit).
- The SQLite decision, the index-existence disclosure, the NULL-grain
  disclosure, the lifecycle-vocabulary deferral, and the
  "restore does NOT prove PITR/scale" caveats are all honest
  limitations stated in the docs — the Phase 3 team disclosed more
  than it overclaimed, and most findings above are cases where a
  doc sentence went one step further than the disclosed limitation.
- Zero rows, zero secrets, zero paid services, zero broker paths:
  all verified independently, not taken on trust.
