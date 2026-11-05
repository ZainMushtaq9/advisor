# Security and Privacy Audit — PSX Intelligence AI (Independent Audit)

**Audit baseline:** branch `phase-30-release`, commit `8937338`.
**Audit date:** 2026-11-05 (Asia/Karachi).
**Method:** static code review (verified in the audit worktree),
live runtime checks against the scratch backend, the acceptance
scanner's 9/9 pass (re-run by the audit's Phase 29 commit), the
GitHub secret scans (see GITHUB_BRANCH_AND_COMMIT_AUDIT.md), and a
fresh `pip-audit` run. No penetration test was performed; no live
auth account was created (parent/user decision).

## 1. Authentication — implemented, not operational

- **Design (verified in code):** CLI-only account management; no
  HTTP login route; passwords via PBKDF2-HMAC-SHA256, 600,000
  iterations, per-user salt; opaque tokens (`psx_` prefix, 32
  bytes via `secrets.token_urlsafe`), stored as SHA-256 hashes
  only, shown to the owner exactly once at issue, never logged,
  never returned again, never stored in plaintext.
- **Reality (verified in scratch):** `auth_users 0, auth_tokens 0,
  auth_audit_logs 0` — empty by decision. The readiness endpoint
  reports `auth_enforcement: "off"`.
- **Plain statement:** CLI-only accounts with empty user tables
  is NOT operational user authentication. Until the first live
  account is created (a parent/user decision), the API serves
  data without authentication. The fail-closed design (enforcement
  activates on the first account) is sound, but it has never been
  exercised with a real account, so the enforced mode is itself
  UNVERIFIED. Severity MEDIUM for production; not a defect in the
  implemented code.

## 2. Authorisation (RBAC)

- 5 roles over a closed 5-permission list (verified in the Phase
  24 report and consistent with the code structure).
- **No permission name exists** for orders, publication, external
  sends, or quality promotion. Those actions cannot be authorised
  because they cannot be named — a structural guarantee, stronger
  than a runtime check. Combined with the GET-only API and the
  absence of any execution route, unauthorised trading or
  publication is impossible through the current API surface, not
  merely forbidden.

## 3. Audit logs

- `auth_audit_logs` is append-only: no update or delete function
  exists for it (verified in the Phase 24 report; the acceptance
  `pii_columns` scan and the auth-tables check both pass).
- Agent audit logs (6 rows in scratch) and orchestration audit
  logs are written by the runners and are part of the evidence
  chain, not user-editable through the API (GET-only).

## 4. Rate limits, CSRF, headers

- **Rate limits:** 300/min API, 30/min auth, in-memory and
  single-process. Adequate for a local single-process deployment;
  NOT adequate as a production control (no shared state, no
  persistence across restarts, no per-account bucketing until
  accounts exist). Not load-tested by this audit.
- **CSRF:** ruled not-applicable today — GET-only API, no cookies,
  no session. The mandatory rule for any future write route
  (Bearer + dependency check) is documented and must be enforced
  at that time; the current GET-only surface gives no CSRF
  surface to test.
- **Security headers:** reviewed in Phase 24 (report carried);
  not re-verified live by this audit because no production host
  exists to probe. Recorded as carried, not as audit-verified.

## 5. Secrets (verified — see also the GitHub audit)

- No tracked `.env`, `.pem`, `.key`, or credentials file on
  `8937338`; history scans find variable-name references only
  (5 commits mention `PGPASSWORD` as a name; 1 commit touches
  `*token*` paths, the Phase 24 introduction of `tokens.py`).
- `database/.env.example` carries `CHANGEME` on both sensitive
  assignments (the Phase 28 remediation, verified present).
- Force-added `backend/app/services/auth/tokens.py` (tracked
  despite `.gitignore` `*token*`) contains no literal secret:
  prefix constant, runtime generation, SHA-256 hashing only.
- The role password lives ONLY in `database/.env` (gitignored,
  mode 0600). This audit never printed, logged, or committed it,
  and no credential value appears in any audit report. (Process
  listings observed during the audit showed the DATABASE_URL
  reference redacted, not the value.)
- No credential value appears in any audit report.

## 6. Code-level security (authoritative scanner, re-run by this audit)

The Phase 29 acceptance run executed by this audit against
scratch produced 9/9 PASS with the scanner's scoping honestly
stated (`.py`/`.sh`, non-test, self-excluded; branch-tip datasets
scanned across 41 tips):

| Scan | Expected | Found |
|---|---|---|
| execution_identifiers | 0 | 0 |
| dangerous_constructs | 0 | 0 |
| write_routes | 0 | 0 |
| upload_endpoints | 0 | 0 |
| docker_invocations | 0 | 0 |
| tracked_datasets | 0 | 0 |
| tracked_secrets | 0 | 0 |
| branch_tip_datasets (41 tips) | 0 | 0 |
| pii_columns (auth tables 0/0/0) | 0 | 0 |

The auditor's own independent greps corroborate: zero
TODO/FIXME/XXX/HACK in `backend/app`, `scripts`, `frontend/app`,
`frontend/lib`; zero `eval(`/`exec(`/`os.system`/`shell=True`/
`pickle.load` calls outside a scanner comment; zero non-GET
routes; zero execution identifiers outside the scanner's own
pattern list. (An ad-hoc grep across docs/test-data would give
false positives and was NOT used as findings — the scanner's
scoping governs.)

**Caveat carried from the gate itself:** "dataset/secret scans
cover branch tips, not every historical commit." A secret buried
in a non-tip historical commit would not be caught by the tip
scan; the auditor's `git log --all -S PGPASSWORD` history scan
(variable names only) partially mitigates this, but a full
historical secret scan (e.g., gitleaks across all commits) was
not run and is recommended before any public-release use.

## 7. Privacy

- **No PII columns:** the `pii_columns` scan passes (0 hits); the
  data model carries company/market data, not personal data.
  The only personal identifiers in the project are operational
  (the user's own email in the permission-request record, GitHub
  identity in commit metadata) — not in the application database.
- No user tracking, no analytics, no external calls from the
  application code (no HTTP fetch in the job runner; no message
  sending; no report publication).
- The `certification.pdf` prohibition (identity number on two
  pages) was respected: no such file is tracked or referenced in
  the audited tree.

## 8. Dependency vulnerabilities

- `pip-audit` run by this audit against pinned
  `backend/requirements.txt` (fresh clone, network available):
  **No known vulnerabilities found** (all pinned dependencies,
  including fastapi 0.162.0, uvicorn 0.54.0, sqlalchemy 2.1.8,
  pymupdf 2.1, pdfplumber 0.11.10). Closes the Phase 24 gap.
  Re-run before production deployment (vulnerability data is
  time-sensitive); frontend (`npm audit`) was not run by this
  audit and is recorded as not run.

## 9. Verdict for this audit area

- Implemented security controls are sound and scanner-clean.
- Operational security is NOT established: no accounts, no
  enforced authentication, no production host, no historical
  secret scan, no frontend audit. The system is safe to run
  locally (GET-only, no secrets in the tree, no execution path)
  and NOT ready to expose (see production readiness).
