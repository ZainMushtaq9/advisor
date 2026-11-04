# Phase 3 — Duplicate Detection

## Principle

Duplicates are prevented by grains and hashes, not by convention
or by 'the collector should know better'.

## Mechanisms (all tested or schema-enforced)

1. **Unique grains** (see relationships_and_constraints.md):
   re-ingesting the same security/date/bar/source price, the same
   statement version, or the same indicator value is rejected by
   the database, not by application memory.
2. **Content hashes:** raw_payloads.content_hash (unique),
   announcements.document_hash, news.content_hash,
   financial_documents.content_hash. The duplicate-detection key
   helper (`duplicate_key_for_document`) prefers the hash, falls
   back to the source URL, and returns None (flag for review)
   when neither exists — a missing key is never a pass.
3. **Dividend 1:1:** dividends.corporate_action_id is unique, so
   a dividend event cannot be double-counted across
   corporate_actions and dividends.
4. **Storage write-once:** the Phase 2 storage helper refuses to
   overwrite an existing file with different bytes; a correction
   is a new file with a new hash. Phase 3's dataset manifests
   make the same guarantee checkable across a whole dataset
   (verify_dataset re-hashes every file).
5. **Idempotent recalculation:** recalculating an indicator or
   ratio for the same grain + calculation version overwrites
   nothing and creates nothing new unless the value or version
   changed — and a changed value is a new version row for
   versioned tables, not an edit. (Recalculation endpoints are a
   later-phase consumer; Phase 3 provides the grain + version
   columns that make idempotency possible.)

## What duplicate detection does NOT do

It does not merge conflicting sources (that would destroy
evidence), it does not deduplicate across sources (different
sources are different rows by grain), and it does not guess that
two similar titles are the same announcement (hash or URL, or
human review).
