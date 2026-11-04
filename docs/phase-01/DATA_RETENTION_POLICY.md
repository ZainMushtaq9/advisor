# PSX Intelligence AI — Data Retention Policy (Phase 1 of 30)

> **Status: POLICY DESIGN ONLY — Phase 1, Team 6. STOP AFTER PHASE 1.**
> No retention job, archival pass, deletion, or backup rotation in this
> document has been executed. Periods below are *specified policy* for
> a later phase to implement, not observed practice. Nothing has been
> deleted, archived, or retained under this policy yet, because no
> production data exists under it.
>
> **Budget context (mandatory):** PKR 0 for project software/storage
> services. Retention/archival on local disk + Parquet + optional
> self-hosted MinIO costs local disk capacity and operator time —
> external operating expenses (hardware / electricity / internet).
> Never describe retention as "free". If local capacity ever forces a
> choice between retention and cost, the policy's priority order in
> §2 governs, and any deviation needs explicit user approval.
>
> **Companions:** `DATABASE_DESIGN.md` (immutability, provenance),
> `DATABASE_ENTITY_CATALOG.md` (entity definitions),
> `DATABASE_RELATIONSHIPS.md` (delete rules: RESTRICT on history),
> `DATABASE_INDEXING_STRATEGY.md` (partitioning for archival),
> `STORAGE_ARCHITECTURE.md` (file classes, Parquet, backups).

## 1. Principles

1. **History is the product.** For a market-intelligence system, old
   prices, old statements, old forecasts and their evaluations, and
   the audit trail of what was claimed when, are not clutter — they
   are the evidence base. Retention therefore defaults to *long*,
   and deletion defaults to *never*, unless a class below explicitly
   says otherwise.
2. **Archive ≠ delete.** Moving data from online database partitions
   to Parquet, or from hot local disk to a colder local location,
   is archival — the data remains retrievable and hash-verified.
   Deletion means the data is gone and cannot be recovered from this
   system. The policy treats the two as entirely different actions
   with different approvals (see §5).
3. **Never delete to save space silently.** If capacity pressure
   arises, the order is: (a) compact Parquet partitions, (b) archive
   old online partitions to verified Parquet, (c) deduplicate
   (hash-dedup already prevents duplicate storage — re-check for
   orphans per storage architecture §8), (d) escalate to the user
   with a capacity report. Deleting a "never deleted" class (§3) to
   save space is prohibited, full stop.
4. **Legal/provenance holds override every period.** A hold (§6)
   freezes deletion and archival-removal for the held scope, for as
   long as the hold lasts, regardless of what §4 says. Holds are
   recorded, dated, and audit-logged; they are lifted only by the
   same authority that imposed them (or its documented successor).
5. **Deletion, when allowed, is logged and reversible-windowed.**
   Allowed deletions (§4) are soft first (status/`deleted_at` +
   audit log), then hard only after the reversibility window in §5
   expires without objection, and only if no hold applies. A hard
   delete without a prior soft-delete + audit entry is a policy
   violation.
6. **Retention periods run from a defined event, not from "whenever".**
   Each period in §4 states its clock (collection date, trading date,
   creation date, supersession date, account closure, …). A period
   with an undefined clock is not enforceable and must not be applied.

## 2. Priority order (when capacity or conflict forces a choice)

1. Audit logs + raw provenance (never deleted — §3).
2. Market history + financial statements (the core evidence base).
3. Forecasts + evaluations + recommendations (the accountability
   record for advice-like outputs — deleting these would destroy
   the ability to answer "was this recommendation any good?").
4. Processed documents + Parquet history (regenerable from 1–3, but
   expensive to regenerate — archive before deleting, never delete
   the only copy).
5. Live-quote history beyond the current marker (transient by nature
   — the most deletable history, but only per §4).
6. Backups (rotated per §4, but never below the minimum in §4.6).
7. Temporary/scratch data (deletable freely — the only class with
   no retention value).

A capacity decision that inverts this order (e.g. deleting audit logs
to keep scratch files) is a policy violation.

## 3. What is NEVER deleted

The following are never hard-deleted in normal operation. "Never"
means: no retention period expires them, no capacity measure removes
them, and no routine job deletes them. The only exception is the
documented legal/provenance procedure in §6 — and even then, removal
is a reviewed, audit-logged, hold-aware operation, not a routine job.

| Class | Entities / files | Why never |
|---|---|---|
| Audit trail | `audit_logs` (alias `audit_records`) — all rows | Without audit, no write is trustworthy and no deletion is accountable. Deleting audit to hide a deletion defeats the entire policy. |
| Raw provenance | `raw_payloads` rows + raw files (original PDFs, raw JSON) | Raw is the evidence that processed values came from a real source. Replacing raw with processed-only data makes provenance unverifiable. |
| Market history (core) | `market_prices` (EOD at minimum), `market_snapshots` (run records) | The price record is the system's reason to exist. Archival to Parquet is allowed (§4); erasure is not. |
| Financial record | `financial_statements` + `financial_statement_line_items` (all versions, including superseded) | Restated statements are history, not errors to erase. Superseded versions prove what was originally filed. |
| Corporate event record | `corporate_actions`, `dividends` (all versions) | Dividend/action history drives adjusted prices and dividend analysis; erasing it corrupts derived series silently. |
| Announcement / news record | `announcements`, `news` (all versions, including superseded) | Publications are historical facts; corrections are new versions, not erasures. |
| Forecast accountability | `forecasts`, `forecast_evaluations`, `recommendations`, `valuations` (all versions) | Deleting poor forecasts/recommendations would falsify the track record. Accountability requires the failures to remain. |
| Model identity | `model_versions` (all versions, including retired) | A forecast that references a deleted model version becomes uninterpretable. Retire, never delete. |
| Source registry history | `data_sources` rows that any sourced row references | Deleting a source row orphans every row that cites it. Deprecate, never delete, while references exist. |
| Symbol history | `symbol_history` (all rows) | Rename history is what makes long price series continuous. Deleting it splits history. |
| Quality history | `data_quality_reports` (all rows, including resolved) | Resolved issues are evidence that problems were found and handled. Deleting them hides the quality record. |
| Reference identity | `companies`, `securities`, `exchanges`, `sectors` rows that any history references | Identity rows anchor history. Status-change (delisted/deprecated) is the mechanism, not deletion. |

**Consequence for implementers:** any retention job, ORM cascade, or
"cleanup" script that touches a table above must be rejected in
review. The relationship document's RESTRICT rules (§4 there) are the
database enforcement of this section; this policy is the human
enforcement. Both must agree — if a migration proposes CASCADE on a
never-deleted table, the migration is wrong.

## 4. Retention periods by class

Periods are specified policy, not measured practice. "Online" means
in the primary PostgreSQL tables with hot indexes. "Archived" means
in verified Parquet and/or colder local storage, retrievable via
manifest + database reference, with hashes verified at archival time.
"Deleted" means hard-deleted after the §5 procedure — only where the
table explicitly allows it.

### 4.1 Market data

| Data | Online | Archived | Deleted |
|---|---|---|---|
| `market_prices` EOD | Indefinitely online while capacity allows; yearly partitions detach to Parquet only after the partition is ≥ 2 years old AND its Parquet export is hash-verified (see storage §9) | Parquet, indefinitely (never deleted — §3) | Never |
| `market_prices` intraday/tick (today-only source) | Current + prior trading day online (ticks are transient by source design); older tick partitions archive to Parquet promptly | Parquet, indefinitely where stored; tick history beyond the verified source window is explicitly NOT promised (design U10) — absence is not a retention failure | Never (where stored); never synthesised where absent |
| `live_quotes` (append-only log) | `is_latest = TRUE` rows online indefinitely (current state). Non-latest rows online for 90 days from `quote_timestamp`, then archive to Parquet | Parquet, 2 years from `quote_timestamp`, then review (see note) | Non-latest quote rows older than 2 years in Parquet MAY be hard-deleted after review + audit, ONLY if their information is already captured in `market_prices` history for the same security/date — otherwise retain. Current (`is_latest`) rows are never deleted while they are current. |
| `market_snapshots` | Snapshot runs online for 1 year from `snapshot_at`, then archive to Parquet | Parquet, indefinitely (snapshot runs are market-history evidence — §3) | Never (run records); individual run rows are never selectively deleted to "thin" a run — a run is atomic |
| `trading_calendars` | Indefinitely online (small table; no archival benefit) | N/A | Never (while referenced by any quality/missing-session logic) |

**Quote-history note:** live quotes are the most transient history
in the system, which is why they are the only market-history class
with a deletion path at all — and even that path is conditional on
redundancy with `market_prices`. If a quote's information is NOT in
`market_prices` (e.g. bid/ask not stored as a price row), the quote
row is the only record and must be retained. Deleting the only record
of a displayed quote would break the "what was shown as live, when?"
audit question.

### 4.2 Fundamentals, events, announcements, news, economics

| Data | Online | Archived | Deleted |
|---|---|---|---|
| `financial_statements` + line items | Indefinitely online (statement volume is low relative to prices; archival benefit is minimal) | Parquet extract on demand, indefinitely where created | Never (§3) |
| `ratios` | Indefinitely online for the latest computation per (company, period, ratio); older computations online for 2 years, then archive to Parquet | Parquet, indefinitely | Never (ratio history is recomputation evidence; a deleted old ratio cannot be re-challenged) |
| `corporate_actions`, `dividends` | Indefinitely online | Parquet extract on demand | Never (§3) |
| `announcements` (+ PDFs) | Indefinitely online; PDFs on local disk / MinIO indefinitely | N/A (PDFs are already file-archival) | Never (§3), except §6 legal procedure |
| `news` | Online for 2 years from `published_at`, then archive to Parquet/file | Parquet/file, 5 years from `published_at`, then review | News rows older than 5 years in archive MAY be hard-deleted after review + audit, EXCEPT news rows linked to a recommendation/valuation/forecast as evidence (those follow the linked row's never-deleted rule). News is third-party reporting, not issuer record — hence the only deletion path in this section, and it is review-gated. |
| `economic_indicators` | Indefinitely online (series volume is low; observations are the macro evidence base) | Parquet extract on demand | Never (§3, as part of the evidence base for analysis that cites them) |

### 4.3 Analysis (valuations, forecasts, recommendations)

| Data | Online | Archived | Deleted |
|---|---|---|---|
| `valuations`, `forecasts`, `forecast_evaluations`, `recommendations` | Indefinitely online | Parquet extracts on demand, indefinitely | Never (§3 — accountability record) |
| `agent_executions`, `agent_outputs` (+ research reports) | Online for 2 years from `started_at`/`created_at`, then archive (report files + execution metadata to Parquet/file archive) | Archive, indefinitely for executions linked to a forecast/recommendation/valuation; 5 years otherwise, then review | Agent outputs NOT linked to a business row and older than 5 years in archive MAY be hard-deleted after review + audit. Linked outputs follow §3 (never). Draft reports (status `'draft'`) follow §4.5, not this row. |
| `model_versions` | Indefinitely online | N/A | Never (§3) |

### 4.4 Portfolios, users, roles

| Data | Online | Archived | Deleted |
|---|---|---|---|
| `portfolios`, `portfolio_holdings` (current) | Online while the portfolio is `'active'`; archived portfolios (status `'archived'`) remain online for 1 year after archival, then move to Parquet/file archive | Archive, 5 years after portfolio archival, then review | Portfolio/holding rows MAY be hard-deleted after the 5-year archive period + review + audit, ONLY if the portfolio owner (or account-closure procedure) requests deletion or the account is closed per §5 — and even then, holdings that are evidence for a recommendation/valuation linked to that portfolio follow §3 for the linked evidence. User-initiated deletion is a user right, not a capacity measure; it never overrides §3 or a §6 hold. |
| `users`, `roles`, `user_role_assignments` | Online while active; deactivated users/roles soft-deleted (`deleted_at`/status) and retained online for 1 year, then archived | Archive, 5 years after deactivation, then review | User/role rows MAY be hard-deleted after the 5-year archive period + review + audit + account-closure procedure, EXCEPT: (a) any `audit_logs` row naming the user as actor is never deleted (§3) — the audit row survives with the actor id intact even if the user row is removed, and the removal must be audit-logged before it happens; (b) a §6 hold blocks deletion. Deleting a user row does not delete their portfolios automatically — portfolio deletion follows its own row above. |
| `portfolios` broker data | N/A — no broker data exists by design | N/A | N/A |

### 4.5 Processed documents, Parquet datasets, research-report drafts

| Data | Online / hot | Archived | Deleted |
|---|---|---|---|
| Processed documents | Hot while their source statements/announcements are online; archive with their sources | Archive, indefinitely where they are the only processed copy of a raw source (regeneration cost); otherwise per source class | Processed documents that are regenerable from retained raw + a retained processing version MAY be hard-deleted after review + audit to save space — they are derived, not evidence. The regeneration recipe (raw ids + method version) must be retained even if the file is deleted. |
| Parquet datasets (analytical) | Hot per dataset manifest (current year + prior year hot; older partitions colder local storage) | Indefinitely where the Parquet copy is the archival copy of a detached database partition (§3/§4.1) | Parquet copies that duplicate retained online database rows MAY be deleted after review (they are copies, not the record) — EXCEPT archival Parquet copies of detached partitions, which ARE the record and follow §3. The manifest must state which role each Parquet file plays; a file whose role is ambiguous is treated as the record (never deleted) until clarified. |
| Research-report drafts (`'draft'`) | Hot for 90 days from creation, then review | — | Drafts older than 90 days with no promotion to `'final'` MAY be hard-deleted after review + audit (drafts are working papers, not evidence). A draft that was ever cited, shared, or linked to a business row is no longer a mere draft — it follows the linked row's rule. |
| Research reports (`'final'`, `'superseded'`) | Per §4.3 agent-outputs row | Per §4.3 | Never where linked (§3); otherwise per §4.3 review path |

### 4.6 Backups

| Backup class | Retention |
|---|---|
| Daily local backups (database dump + file copy + manifest) | 30 days online (local disk), then rotate: keep weekly snapshots for 12 weeks |
| Weekly snapshots | 12 weeks, then rotate: keep monthly snapshots for 12 months |
| Monthly snapshots | 12 months, then review: keep yearly snapshots indefinitely where they contain never-deleted classes (audit/raw/market history) — a yearly backup is often the only off-partition copy of a detached history, so deleting it needs the same review as deleting the history itself |
| Backup manifests | Retained with their backup, indefinitely for yearly backups; a manifest without its backup is retained as evidence of what was backed up, when |
| **Minimum floor** | At all times: at least 2 verified backups (different timestamps) + at least 1 yearly snapshot must exist before any rotation deletes an older backup. Rotation must never leave zero verified backups. A rotation job that would breach the floor must stop and alert, not proceed. |

Backup retention is a rotation policy, not a data-retention policy
for the underlying data: deleting an old backup does not delete the
live data it copied. Conversely, retaining a backup does not extend
the live data's retention — live deletion (where allowed) and backup
rotation are separate decisions, and a "deleted" live row may still
exist in an old backup until that backup rotates. That fact must be
disclosed to any user requesting deletion (§5.3): deletion from live
is not deletion from all backups until rotation completes.

### 4.7 Temporary / scratch data

| Data | Retention |
|---|---|
| `tmp/` scratch, failed-ingest temp files, unquarantined intermediates | No retention value. Deletable at any time without audit. If a file in `tmp/` is found to be the only copy of something valuable, that is an ingest bug (valuable files belong in §3 classes, not `tmp/`), and the file must be promoted to its proper class + provenance before `tmp/` is cleaned — not deleted with the scratch. |
| Quarantine (`quarantine/`) | 90 days from quarantine, then review: either ingest (with provenance completed), reclassify as a proper raw file, or delete after review + audit. Quarantine is not a trash can: an item that sits in quarantine past 90 days without review is a quality-process failure, and the review backlog itself must be reported. |

## 5. Deletion rules (where deletion is allowed at all)

### 5.1 General procedure (all allowed deletions)

1. **Check §3:** is the item in a never-deleted class? If yes, stop.
   No further step authorises deletion.
2. **Check §6 holds:** is the item (or its scope) under hold? If yes,
   stop until the hold is lifted by its authority.
3. **Check §4 period:** has the retention period expired, measured
   from its defined clock? If no, stop.
4. **Review:** a named reviewer (human, not the deletion job itself)
   approves the deletion batch (scope + row/file count + reason).
   Bulk auto-deletion without review is prohibited for every class
   except `tmp/` (§4.7).
5. **Soft-delete first:** set status/`deleted_at`, write an
   `audit_logs` row (what, why, who approved, what period expired,
   what hold check was performed). The data remains recoverable.
6. **Reversibility window:** 30 days (soft-deleted state) during
   which the deletion can be reversed without a backup restore.
   Objections during the window cancel the hard delete.
7. **Hard delete:** only after the window expires without objection,
   and only the approved scope. Verify post-delete: the item is gone
   from live, its audit entry remains, and no §3 item was affected
   (spot-check linked rows).
8. **Backup disclosure:** note in the audit entry that the item may
   persist in backups until rotation (§4.6).

### 5.2 What deletion never does

- Never cascades to §3 items (enforced by RESTRICT — relationships §4).
- Never deletes `audit_logs` rows about the deletion itself (the audit
  of a deletion is itself never-deleted).
- Never rewrites history to hide that data existed (soft-delete +
  audit preserves the fact of prior existence; hard delete removes
  content, not the audit fact, except where §6 requires otherwise).
- Never runs as an unattended job that deletes without review,
  except `tmp/` cleaning.

### 5.3 User-requested deletion (account / portfolio data)

- A user may request deletion of their own portfolio/user data
  (§4.4). The request is honoured per §5.1, subject to §3 (audit,
  linked evidence) and §6 (holds).
- The response to the user must state plainly: what was deleted from
  live, what remains in audit/linked evidence and why, and that
  backups may retain copies until rotation (§4.6). Over-promising
  ("everything is gone") when audit/backup copies remain is a
  misrepresentation.
- No user request can delete another user's data, market history,
  or audit logs. A request that asks for those is refused in scope,
  with the §3 reason given.

## 6. Legal / provenance holds

### 6.1 Hold types

| Hold | Imposed by | Effect |
|---|---|---|
| Legal hold | User instruction / legal requirement (documented, dated) | Freezes deletion AND archival-removal for the held scope. Held data stays online (or in its current archive) and retrievable until the hold is lifted. |
| Provenance hold | Data-quality / audit finding that the held data's provenance is under dispute or investigation | Freezes deletion and any re-processing that would overwrite derived artefacts from the held raw data. New versions may still be created (append-only), but old versions may not be removed. |
| Licensing hold | Licensing review finding (e.g. a PDF whose retention/redistribution right is unclear) | Freezes redistribution and, where the review requires it, freezes retention pending a decision — but the decision itself (retain vs remove under §6.3) must be documented; a licensing hold is not indefinite silent retention. |

### 6.2 Hold records

A hold is itself a record (later-phase operational table or a
`data_quality_reports` + `audit_logs` pair, at minimum):

- Scope (entity/table, row ids or file paths, date range, or
  "all data from source X").
- Reason, imposing authority, imposed date (PKT), expected review
  date (holds are reviewed, not indefinite by default — a hold
  without a review date must be given one within 30 days).
- Lifting authority + lifting date, when lifted.
- Every retention job must check active holds for its scope before
  acting. A job that does not check holds is non-compliant, even if
  it otherwise follows §4.

### 6.3 Removal under a legal/licensing procedure (the §3 exception)

When a documented legal or licensing procedure *requires* removal of
otherwise never-deleted data (e.g. a court order, a licence
withdrawal requiring deletion of specific PDFs):

1. The procedure (order/decision, scope, authority, date) is recorded
   in `audit_logs` BEFORE removal.
2. Removal is scoped to exactly the procedure's scope — no broader.
3. The audit entry recording the procedure and the scope survives
   removal (the fact of removal is itself audit history, even if the
   removed content is gone).
4. Derived artefacts that depend solely on the removed data are
   flagged (quality reports), not silently kept as if their source
   still existed. Derived artefacts with other sources remain, with
   the removed source noted as withdrawn.
5. Backups containing the removed data are handled per the procedure:
   if the procedure requires backup removal, backup rotation is
   accelerated for the affected backups with a new verified backup
   taken first (so removal does not destroy the only copy of
   unrelated never-deleted data). If the procedure does not require
   backup removal, the backup disclosure in §5.1 applies.
6. After removal, a verification step confirms the scope is gone from
   live (and from backups, if required) and that no §3 item outside
   the scope was affected.

This is the ONLY path by which §3 data may be hard-deleted. Any other
"exception" is not an exception — it is a violation.

## 7. Archival procedure (online → Parquet / colder local storage)

1. **Select scope** by §4 period + partition (yearly database
   partitions, Parquet partitions — indexing strategy §4, storage §6).
2. **Export** to Parquet with manifest (dataset, grain, date range,
   row count, schema version, source keys, hash).
3. **Verify:** row count matches the database partition; content hash
   of the export matches a recomputed hash; a sample of rows
   round-trips (Parquet → values = database values).
4. **Detach, don't delete:** detach/archive the database partition
   (or move files to colder local storage) only after verification.
   Keep the manifest reference in the database so the archived
   period remains discoverable ("where did 2021 EOD go?" → manifest).
5. **Audit:** write an `audit_logs` row for the archival (scope,
   manifest id, verification outcome).
6. **Retrieval:** archived data must remain retrievable by the same
   hot-query patterns (HQ1, HQ9, etc.) via Parquet partition pruning
   or a documented retrieval procedure — archival that makes data
   practically unfindable is deletion by another name and is
   prohibited.

## 8. Review cadence (policy maintenance, not data deletion)

- **Quarterly:** review open quality reports, quarantine backlog
  (§4.7), hold review dates (§6.2), and backup floor compliance
  (§4.6). Report the review outcome (counts, not content dumps) in
  an audit-visible note.
- **Annually:** review §4 periods against actual volumes and local
  disk capacity. Period changes require a policy amendment (new
  version of this document, dated, with rationale) — retention jobs
  must not silently adopt new periods.
- **On trigger:** a legal/licensing event, a capacity crisis, or a
  user deletion request triggers an out-of-cycle review of the
  affected scope only.

## 9. UNVERIFIED assumptions (retention-specific)

| # | Assumption | What would verify it |
|---|---|---|
| R1 | The periods in §4 are appropriate for the project's actual volumes, legal obligations, and user expectations | A later-phase review once real volumes exist + any applicable legal/licensing advice. Phase 1 sets periods as policy design, not as legal advice — no period here is a legal opinion. |
| R2 | Local disk capacity can sustain "indefinitely" classes + backups | A capacity estimate once real row/file counts exist (storage S4). If capacity fails, §2 priority order + user escalation govern — not silent deletion. |
| R3 | Any legal obligation that would impose a specific retention or deletion period (e.g. financial-advice record-keeping, personal-data law) | Legal advice / user decision in a later phase. Until then, this policy does not claim compliance with any specific statute. |
| R4 | Backup tooling and restore testing (storage S5) | A provisioning decision + a tested restore (storage §11). Retention of backups is meaningless if restores do not work. |
| R5 | The 90-day / 2-year / 5-year figures in §4 are the right balances | Operational experience. They are starting policy values, chosen to be explicit and reviewable, not measured optima. The annual review (§8) is where they are corrected. |
