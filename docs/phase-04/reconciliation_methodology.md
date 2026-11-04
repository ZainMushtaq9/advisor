# Phase 4 — Reconciliation Methodology

## Purpose

Reconciliation compares the registry against a DATED official
source snapshot used as a baseline. It answers: how many of the
snapshot's tickers are in the registry, which are missing, and
which registry tickers are extra? It never pads the registry to
match the snapshot, and it never edits the snapshot to match the
registry.

## Snapshot format

A JSON file: `{"source": ..., "snapshot_date": ...,
"tickers": [...]}`. Tickers are normalized on load; invalid
entries are dropped and the drop count is reported. The snapshot
must state its source and date; an undated list is not a baseline.

## What counts as a usable snapshot

- A complete (or explicitly partial, labelled as such) list from
  an official source, obtained on a stated date, with a stated
  fetch method.
- A market-watch table of traded symbols on one day is NOT a
  registry snapshot: it omits non-traded listings and carries no
  company names.
- A cached copy crawled months earlier is NOT a current snapshot:
  its crawl date is its date, and staleness must be stated.
- A JavaScript table that yields 0 rows to a text fetch is NOT a
  snapshot at all — it is an unextracted source.

## Result in this phase

NO usable snapshot was obtained (see source_research.md):
- DPS Listing Status via text fetch: 0 rows (JS rendering).
- DPS direct access from this VM: connection failure.
- DPS market-watch text copy: crawled 2026-01-25, stale, no
  company names, sector codes without a name mapping.
- PSX homepage: 26 partial scrip rows, no company names, no
  sectors, no listing statuses, and not stated to be complete.

Therefore `reconcile()` was run with snapshot=None, which returns
registry counts with `coverage_ratio=None` and the explicit note
that no coverage claim is made. That is the honest result: a
coverage ratio against an invented or partial baseline would be
a fabricated completeness claim.

## What unblocks reconciliation

A live-browser extraction of the DPS Listing Status table (Main
Board / GEM Board / Normal Counter / Non-Compliant / Winding-Up)
on a stated date, saved as a dated snapshot file, or a documented
machine-readable official list. This is a parent task (generic
subagents cannot operate a live browser) and is recorded as the
Phase 4 population blocker in the completion report. Phase 5's
gate check must re-verify this before treating the registry as a
population base — Phase 5 must not invent a replacement list.
