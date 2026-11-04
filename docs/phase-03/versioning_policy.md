# Phase 3 — Versioning Policy

## The rule

Never overwrite a revised report, a revised observation, or a
published statement. A revision is a NEW row with version_number
incremented and supersedes_id pointing at the row it replaces.

## How it is enforced (three layers)

1. **Application rule:** models carry VersionMixin
   (version_number, supersedes_id, is_current) on versioned
   tables; services must insert a new row for a revision.
2. **Database trigger (versioned tables):** BEFORE UPDATE OR
   DELETE. DELETE is always rejected. UPDATE is allowed ONLY for
   the is_current column (compared via jsonb with that key
   removed); any other column change raises. This exists because
   the is_current pointer must flip when a new version arrives —
   an earlier Phase 3 draft blocked ALL updates on these tables,
   which would have made 'current' unmaintainable; that draft was
   corrected before tests were claimed (see defect register).
3. **Database trigger (append-only tables):** BEFORE UPDATE OR
   DELETE always raises. Corrections are new rows, full stop.

## What 'current' means

For versioned tables, current = the row with is_current = TRUE for
its grain. Writer order (audit M2 partial-unique index): flip the
old row's flag to FALSE first, then insert the new version as
current, in one transaction — the reverse order violates the
one-current-per-grain partial unique index at flush. The index
exists on financial_statements and
financial_statement_line_items (the two core versioned tables);
other versioned tables rely on writer discipline plus the same
tiebreaker: the grain plus max(version_number) if flags ever
disagree, and a disagreement is a data-quality finding.

Supersedes chains (audit M2, accepted limitation): supersedes_id
is a logical link with no database foreign key, so a dangling
supersedes_id is possible at the schema level. It is recorded
here as an accepted limitation, not fixed by a same-table FK in
Phase 3, because version targets are resolved by Phase 7/8
services at write time and a FK migration would need a
same-table reference per versioned table. Phase 7 services must
validate supersedes targets before inserting a new version, and
must report a dangling link as a data-quality finding.

## Resolution class (audit H2)

data_quality_reports is neither append-only nor versioned: it has
its own trigger class. Only resolution_status and resolved_at may
change; DELETE is rejected; detail and all other columns are
immutable. See provenance_and_quality.md.

## Restatements and point-in-time

Original reported figures, restated figures and derived values are
separate rows with separate versions. A historical analysis must be
able to retrieve the figures that were available at a historical
date (publication_date + version), never a later restatement
presented as if it were known earlier. That query pattern is a
Phase 7/8 consumer requirement; Phase 3 provides the version
columns and the publication dates it needs.

## Derived values

A derived value (e.g. a standalone quarter computed from cumulative
interim figures, a normalized line item) is stored separately from
the reported value, marked is_derived = TRUE, with its derivation
formula recorded. Derived values never replace reported values.
