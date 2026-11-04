# Phase 4 — Sync Configuration

## Principle

Phase 4 DEFINES sync configuration. It does NOT start a
scheduler, a periodic job, or any background collection. A
machine that is off collects nothing, and a configuration value
is not a running schedule.

## Configuration (`sync_config.py`)

- `SyncConfig(source_key, frequency, enabled, note)`.
- Allowed frequencies: manual, daily, weekly, monthly.
- Default configs (all manual, all disabled):
  - psx_official — manual, disabled.
  - dps — manual, disabled.
  - secp — manual, disabled.
- A non-manual frequency that is disabled is a documented
  intention, not an active schedule.

## Why manual-only in Phase 4

- No source was verified as machine-readable on this VM
  (see source_research.md). Scheduling a fetch against an
  unverified source would produce failures on a timer, not data.
- Frequencies in the source research are "unknown" unless a
  source states them. The sync config therefore does not claim
  that DPS updates daily, weekly, or at any other rate.
- Scheduling, catch-up, and overlap rules belong to the
  Phase 5 pipeline, which will set them from measured source
  behaviour, not from assumptions made here.

## Operator procedure (manual, current)

1. Obtain a dated snapshot from an official source by a
   documented method (live-browser DPS extraction is the
   known next step — see reconciliation_methodology.md).
2. Save it as a dated file under `docs/phase-04/` with source,
   date, and fetch method in its header.
3. Run `import_records` with that source_key and the snapshot
   date as collected_at.
4. Run `reconcile()` against the snapshot file and record the
   report. Do not proceed to a completeness claim unless the
   snapshot is complete and the reconciliation is clean.
