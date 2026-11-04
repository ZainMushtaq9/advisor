# Workers — Tasks

Celery task definitions (collection, validation, analysis, PDF, report jobs) with idempotency keys. Status: skeleton only; Celery + Redis are NOT installed on the audit machine, so no worker runs yet. Bounded retries for transient failures only; audit vetoes and validation failures are never retried.

Status date: 2026-11-04 (Phase 2, Team A skeleton). If this directory's status changes, update this README in the same commit.
