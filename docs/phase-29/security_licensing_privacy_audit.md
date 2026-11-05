# Phase 29 — Security, licensing and privacy audit

Run: `phase29-acceptance-2026-11-05`. Nine audit checks, all PASS in
the committed run. Scans cover the repository working tree
(`backend/app`, `backend/tests`, `scripts`, `ops`, `docs`) plus the
tracked-file and branch-tip checks described below. The scan boundary
is stated, not hidden: dataset/secret scans cover branch tips, not
every historical commit.

## Results

| Check | Result | Detail |
|---|---|---|
| execution_identifiers | PASS, 0 hits | No place_order / execute_order / submit_order / execute_trade / place_trade, no Broker classes, no /orders routes anywhere in application or script code |
| dangerous_constructs | PASS, 0 hits | No eval / exec / os.system / subprocess shell=True / pickle.loads in application or script code (the one documented subprocess call uses a fixed argv list with no shell) |
| write_routes | PASS, 0 hits | No POST/PUT/PATCH/DELETE route decorators in the API |
| upload_endpoints | PASS, 0 hits | No UploadFile / multipart handling in the API |
| docker_invocations | PASS, 0 hits | No docker run/build/exec/compose/ps/pull/push and no docker-compose anywhere |
| tracked_datasets | PASS, 0 | No tracked CSV or financial-report PDF in the tree |
| tracked_secrets | PASS, 0 | No tracked .env, private key, or credential-looking file |
| branch_tip_datasets | PASS, 0 | No dataset or credential file at any pushed branch tip (origin/main fetched for the check; local main unmoved) |
| pii_columns | PASS, 0 | No column matching a PII pattern in the live schema |

## Self-scan correction (found and fixed in this run)

The first full-tree dry run reported execution_identifiers 7,
dangerous_constructs 1, upload_endpoints 1, docker_invocations 2 —
every hit was in the auditor file itself
(`backend/app/services/acceptance/audits.py`), which holds the search
patterns as data. The fix excludes that file from its own scans, with
a comment stating the same allowlist rationale the Phase 15–22 guard
tests already use for it. One further hit was a false positive in
the docker pattern: `scripts/check_env.sh` lists `docker` among
tools to probe for presence (`docker psql redis-cli …`); the pattern
matched `docker ps` as a prefix of `docker psql`. The pattern now
requires a word boundary after the verb, so `docker ps` still
matches and `docker psql` does not.

## Licensing

- All dependencies in `backend/requirements.txt` are now pinned and
  recorded in `backend/LICENCES.md`, including the two this phase
  found missing (defect D-13, fixed here): PyMuPDF 2.1 and
  pdfplumber 0.11.10, both used by Phase 7 extraction.
- PyMuPDF is dual-licensed GNU AFFERO GPL 3.0 or Artifex Commercial
  License. That is a REVIEW ITEM before any public hosted
  distribution or redistribution (defect D-14, accepted as a review
  item with a clear trigger) — not a current violation: the project
  is local research, not a distributed network service.
- The Phase 28 dependency-gate test allowlist was extended with
  pymupdf and pdfplumber so the gate stays green for the right
  reason (recorded pins), not by weakening the gate.

## Privacy and access

- Auth tables remain EMPTY BY DECISION (0 users, 0 tokens, 0 audit
  rows). No live account was created in this run. Enforced mode is
  fail-closed (401) until a parent/user decision creates the first
  admin account via the CLI-only tool.
- No permission name exists for orders, publication, external sends,
  or quality promotion, and none was invented in this phase.
- No external notification, publication, or send was made or added.
  Phase 21 external consent remains False; Phase 22 has no publish
  step; all 22 reports remain DRAFT.
- RAG snippets stay capped at 500 characters; no document body is
  served; the HBL report is not in the RAG index (it arrives with
  the post-Phase-30 re-runs).
- No credential, password, token, or session value is printed,
  logged, or committed anywhere in this phase's outputs. The
  database role password lives only in `database/.env` (gitignored,
  mode 0600).
