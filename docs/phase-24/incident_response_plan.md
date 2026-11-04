# Phase 24 — Incident Response Plan

Scope: this project only (local codebase, local database, no
external deployment, no real trades, no user accounts in
production use yet). If an external deployment ever exists,
this plan must be re-issued for that deployment before launch.

## Severity levels

| Level | Meaning | Example |
|---|---|---|
| SEV-1 | Active unauthorized access or data exfiltration | Valid token used by a non-owner; DB dump outside the project |
| SEV-2 | Attempted access, blocked, or credential suspected exposed | Repeated lockouts; revoked token replayed; token shared in chat |
| SEV-3 | Weakness found, no evidence of use | Dependency with a known CVE; permissive CORS found in a deployment |

## Response steps (in order, for any level)

1. **Contain first.** Revoke affected tokens by prefix
   (`scripts/manage_auth.py revoke-token --prefix <prefix>`).
   Disable affected accounts (`disable-user`). If the database
   itself is suspected, stop the application server; the data
   is local and there is no remote kill-switch to miss.
2. **Preserve evidence.** Copy (do not move) the audit tables
   (`auth_audit_logs`, `agent_audit_logs`, `rag_access_audits`)
   and the application logs before any cleanup. Audit rows are
   append-only — do not delete rows to "clean up"; deletions
   destroy the evidence chain.
3. **Assess.** Read the audit window (see audit_logging.md
   review procedure). Determine: which accounts, which tokens,
   which data was reachable (GET-only API: reads only; no
   order, publication, or promotion capability exists to abuse).
4. **Eradicate.** Rotate every credential that could be
   affected (DB role password in `database/.env`, then restart;
   all tokens for affected accounts). Fix the weakness that
   allowed it (code fix + test + review).
5. **Recover.** Re-enable accounts only after rotation.
   Re-verify: full backend suite green, auth endpoints behave
   (401 without token in enforced mode, 403 for lesser roles),
   counts unchanged except audit rows.
6. **Record.** Write a dated incident note under
   `docs/phase-24/incidents/` (none exist yet): timeline,
   evidence, actions, and the fix. No incident has occurred
   in this project to date.

## Specific playbooks

- **Token shared in chat / pasted publicly:** treat as
  exposed (per the project's standing Hugging Face token
  precedent: never saved, used, or repeated). Revoke by
  prefix immediately, issue a new token, note it in the
  incident file. Do not delete the chat message's record
  from the audit trail — the audit row stays.
- **Brute-force lockouts firing:** no action needed unless
  the same actor also shows `access_denied` on admin
  commands — then treat as SEV-2 and disable the targeted
  accounts pending review.
- **Suspected prompt injection via retrieved documents:**
  Phase 18 quarantine already handles this (probe quarantined,
  stored rows untouched). Confirm the quarantine row in
  `agent_audit_logs`, confirm no financial row changed
  (re-read a known value, e.g. HUBC close 197.2400), then
  record.
- **Backup file exposed:** backups contain hashes only, but
  treat as SEV-2: rotate the DB role password, re-encrypt
  (once backup encryption exists), and record.

## Contacts and authority

- Only the project owner (the user) may authorize: account
  re-enablement after a SEV-1, any external notification,
  any production deployment change. The coordinator/agent
  may contain (revoke/disable) without waiting, but may not
  re-enable or deploy without that authorization.
- No external incident-reporting obligation exists for this
  local-only project today. If it ever holds real user data
  or connects to a broker, this section must be rewritten
  before that connection is made.
