# PSX Intelligence AI — Security Requirements

**Phase:** 1 of 30 — Specification only. No application code, no credentials, no keys. STOP AFTER PHASE 1.
**Team:** Team 7 (Financial Analytics + Security + Governance)
**Companion documents:** `FINANCIAL_FORMULAS.md`, `ANALYTICS_SPECIFICATION.md`, `FORECASTING_SPECIFICATION.md`, `VALUATION_SPECIFICATION.md`, `FINANCIAL_GOVERNANCE.md` — all in this same `docs/phase-01/` folder.
**Date / starting condition:** Verified 2026-11-04, reused verbatim — see §1.

## 1. Starting condition (reuse verbatim)

- Project folder `~/workspace/psx-intelligence-ai/` is new. Other teams may be creating sibling files; this team writes only its assigned files and never overwrites/touches sibling teams' files or the separate scaffold `~/workspace/psx-data-collection/` (stdlib collector with provenance / PKT / stale / conflict rules), which is REFERENCED only.
- Tools: Python 3.12.3, Node v24.22.1. Docker, psql, redis-cli NOT installed.
- Already verified (reuse): psx-dps (~496 trading vs ~1029 listed, ~5y EOD, today's ticks, 38 sectors, multi-node 404 quirk, no official PSX API); psxdata (daily OHLCV + live snapshots ONLY, no historical intraday archive — so VWAP / intraday-dependent metrics are limited to what data permits, and historical intraday backtests must not be assumed); Eulerpool: NO PSX coverage, vendor only, no paid API approved.
- SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use is UNVERIFIED — formulas depending on macro / fundamental feeds must state the feed as UNVERIFIED and define missing-data handling (skip / flag, never estimate silently).

## 2. Revised brief — merged

- **Budget: PKR 0 absolute zero-cost.** Security controls in this specification must use local open-source mechanisms and built-in platform features only. No paid security product, paid identity service, paid WAF, paid audit tool, or paid subscription is approved or assumed. Local hardware, electricity, and internet are EXTERNAL operating expenses: disclose them as such, never call them "free". PKR 0 means zero project spend on software/APIs/subscriptions/vendors, not zero operating cost.
- **Phase 1 workflow (11 stages):** (1) brainstorm, (2) research, (3) validate, (4) data inspection — read-only only, NO full-scale live data collection in Phase 1, (5) architecture planning, (6) implementation specification, (7) documentation, (8) testing strategy — defined, not claimed passed, (9) independent audit, (10) correction, (11) checkpoint. This document is stages 6–7. It specifies controls; it does not claim any control is implemented, tested, or audited yet.
- **No real trading initially — EXPLICIT (see §9).** The system must NOT execute real trades initially. Trading restrictions are a security control in this document, not merely a governance preference, and they are enforced by design (no execution path exists in Phase 1), not by policy alone.
- **Critical rules preserved:** No sign-ups, installs, purchases, credentials, API keys, broker connections, live polling, trading, or posting in Phase 1. No credential, secret, token, password, or API key appears in this document, in any chat, or in any code or doc produced under this specification. Never invent an API, endpoint, price, benchmark, or capability.

## 3. Security principles

1. **Least privilege.** Every user, service, and job gets only the permissions it needs for its defined function, for the shortest time needed. No shared superuser for routine work.
2. **Deny by default.** Anything not explicitly permitted by this specification (or a later, approved specification) is denied — including network egress to new hosts, new data sources, and new execution paths.
3. **No security by obscurity.** Controls must work even if an attacker knows the design. Hiding an endpoint, a parameter, or a file path is not a control.
4. **Auditability over convenience.** If an action cannot be logged with who/what/when (PKT)/outcome, it must not be permitted for sensitive operations (see §10).
5. **Fail closed.** On error, ambiguity, or control failure (e.g. authentication service unavailable), the system denies access rather than granting it. A failed auth check is never treated as "no restriction".
6. **Data minimisation.** Collect and retain only what the analytics/governance specifications require. Personal data that is not needed is not collected; data that is collected is retained only as long as its stated purpose requires (see §7).
7. **Zero-cost does not mean zero-security.** The PKR 0 constraint limits tooling choices to open-source/local mechanisms; it does not waive any control in this document. Where a control cannot be met at zero cost, the feature it protects is withheld until a compliant, approved route exists — the control is never silently dropped.

## 4. User authentication

### 4.1 Requirements (implementation-agnostic; no product is mandated or invented)

- **Unique identity per user.** Every user has a unique, non-shared account. Shared accounts for a team, a role, or "admin" routine use are prohibited.
- **Strong authentication.** Passwords, where used, must meet a stated policy fixed at implementation (minimum length, breach-list screening where a local mechanism permits, no maximum-length truncation that silently weakens passwords). Passwords must never be stored in plaintext or with a reversible encoding — only a modern, salted, slow hash (the algorithm and parameters are fixed at implementation from current open-source best practice and recorded; this Phase 1 document mandates the property, not a specific algorithm version, because algorithm guidance changes).
- **Multi-factor authentication (MFA).** MFA is REQUIRED for: administrator accounts, audit accounts, and any account that can change scoring weights, valuation assumptions, recommendation rules, or user roles. MFA is RECOMMENDED for all other accounts and REQUIRED wherever a local open-source MFA mechanism can be deployed at zero cost. MFA must use a standard local mechanism (e.g. TOTP via an authenticator app) — SMS-based codes are not relied upon as the sole second factor where a stronger local option exists, and no paid SMS service is approved.
- **Session management.** Sessions expire after a stated inactivity timeout and an absolute maximum lifetime (both fixed at implementation and recorded). Sessions are invalidated on logout, on password change, and on role change. Session tokens are random, unguessable, transmitted only over encrypted channels, and never appear in URLs, logs, or error messages.
- **Account lifecycle.** Provisioning, role assignment, suspension, and deprovisioning follow a recorded procedure with an approver distinct from the requester for privileged roles. Dormant accounts (no login within a stated period, fixed at implementation) are suspended pending review. Departed users' accounts are disabled promptly; deletion follows the retention rule in §7.4 (audit logs referencing a user are retained even if the account is removed — the log entry is anonymised only if a future, approved privacy rule requires it, and the anonymisation itself is logged).
- **Failed-login handling.** Rate-limit failed logins per account and per source (see §8), lock or progressively delay after a stated number of failures, and log failures without revealing whether the username or the password was wrong (generic failure message to the user; detail only in the audit log).

### 4.2 What is NOT authorised in Phase 1

- No user registration, sign-up flow, social login, or external identity provider is specified or approved in Phase 1. Authentication design here is a specification for a later phase; no account is created, no password is set, and no identity service is connected under this document.
- No credential, password, token, or secret is to be shared in chat, docs, or code at any stage (see §11).

## 5. Role-based access control (RBAC)

### 5.1 Roles (minimum set; additional roles only by approved specification change)

| Role | Permitted (illustrative scope — fixed at implementation) | Explicitly denied |
|---|---|---|
| Viewer / Reader | Read company views, scores, forecasts, valuations that have passed gates; read own profile and own activity | No configuration change, no data write, no export of bulk data, no audit-log access |
| Analyst | Viewer + draft analytics notes / interpretations (labelled as drafts, never as system outputs); propose (not apply) weight/assumption changes | Cannot apply weight/assumption/rule changes; cannot publish a score/recommendation; cannot access audit logs |
| Administrator | User provisioning (per §4.1 lifecycle), role assignment (with separate approver), system configuration | Cannot unilaterally change scoring/valuation/recommendation rules without audit review (§5.2); cannot delete audit logs; cannot execute trades (no execution path exists, §9) |
| Auditor (Independent Audit agent / human auditor) | Read-only access to ALL records: inputs, gates, scores, forecasts, valuations, recommendations, configuration history, audit logs | No write access to analytics, scores, forecasts, valuations, or configuration; no user provisioning |
| System / Service | Machine access scoped to its single job (e.g. data inspection read-only in Phase 1), with its own credential (see §6) | No human-login use; no privilege beyond its job scope |

### 5.2 Separation of duties (binding)

- **No single person** may both propose and apply a change to: scoring weights/thresholds, valuation assumptions/methods, recommendation rules, or data-source precedence. Proposal, independent review, and application are three distinct steps with distinct actors (or, for automated steps, distinct approvals recorded in the audit log).
- **Auditor independence.** The Auditor role must not hold Analyst or Administrator privileges simultaneously. The Independent Audit agent's access is read-only by design; an audit finding cannot be "fixed" by editing the audited record — fixes are new records referencing the finding (see `FINANCIAL_GOVERNANCE.md` §6).
- **Break-glass.** Emergency access (e.g. to contain an incident, §12) follows a recorded break-glass procedure: time-limited, separately approved, fully logged, and reviewed after use. Break-glass must never become routine access, and any use triggers a post-incident review.

### 5.3 Permission enforcement

- Permissions are enforced server-side on every request, not merely hidden in the UI. A UI that hides a button is not access control.
- Permission checks use the authenticated identity + role + resource scope; direct object references (e.g. guessing an ID to access another user's data or an unpublished draft) must be denied.
- Role/permission changes take effect promptly (stated maximum propagation time fixed at implementation) and are logged with before/after values.

## 6. API key management

- **Scope.** This section covers machine credentials for any future API access (data sources, internal services). In Phase 1, NO API key is created, requested, or used — no sign-up, no paid API, no broker connection. This section specifies how keys WILL be managed when a future, approved integration requires them.
- **Rules (binding when keys exist):**
  1. Keys are generated per-service, per-purpose, with least-privilege scope (read-only where read-only suffices; never a write-capable key for a read job).
  2. Keys are stored ONLY in the approved secure store (see §11) — never in code, docs, chat, environment files committed to a repository, or client-side code.
  3. Keys are rotated on a stated schedule (fixed at implementation) and immediately on suspected compromise, personnel departure from a privileged role, or vendor change.
  4. Keys are never logged (values or full keys), never returned in API responses, and never displayed after creation (only a masked identifier/fingerprint is shown).
  5. Expired/revoked keys fail closed (deny, with an alert — not a fallback to an older key).
  6. A key inventory (purpose, owner, scope, creation/expiry, last rotation, last use) is maintained and reviewed periodically; orphaned keys (no owner, no recent use) are revoked.
  7. No key is shared between environments (development keys never work in production, and vice versa) or between services.
- **Zero-cost note.** Key management at PKR 0 uses local/open-source secret storage (§11) and built-in platform features. If a future integration requires a paid key-management service, that service is NOT approved by this document and requires a separate budget/approval decision.

## 7. Database security and user privacy

### 7.1 Database security (local, Phase 1 context)

- **Local-only in Phase 1.** Docker, psql, and redis-cli are NOT installed (starting condition). No database service is assumed, installed, or connected under this document. Database requirements here are specifications for the local store chosen by sibling teams' architecture, and they apply whenever a store exists.
- **When a database exists, it must:** enforce authenticated access (no anonymous/unauthenticated access); enforce least-privilege database roles mirroring §5 (application role, read-only audit role, backup role — never a single superuser for all); encrypt data in transit (TLS where the store supports it) and at rest (platform/filesystem encryption where available at zero cost, with key handling per §11); separate production data from test/development data (no production copy in a dev environment without the same controls); and log database access for sensitive tables (see §10).
- **No credentials in connection strings in code/docs.** Connection parameters that include secrets live only in the secure store (§11) and are injected at runtime, never committed.

### 7.2 User privacy

- **Data collected (minimum):** Account identity (for authentication/audit), user preferences strictly needed for the service (e.g. watchlist symbols the user chose — a user-managed list, not a system recommendation), and audit/activity records required by §10. No data beyond this list is collected without a new, approved specification.
- **Purpose limitation.** Personal data is used only for the purpose it was collected for (authentication, service delivery to that user, audit/security). It is not used for marketing, not sold, and not shared with third parties — and unauthorised commercial redistribution is prohibited (see `FINANCIAL_GOVERNANCE.md` §8).
- **User rights (design requirements).** Users can: view their own stored data; correct inaccurate account data; request deletion of their account data subject to the audit-retention rule (§7.4 — audit logs may be retained in anonymised form where the law/policy requires retention); and export their own watchlist/preferences in a portable form where the implementation provides it.
- **No tracking beyond necessity.** No third-party trackers, advertising SDKs, or analytics beacons are approved. Usage measurement, if any, is local, aggregated, and disclosed — never per-user behavioural profiling for commercial purposes.

### 7.3 Financial-data handling

- Market and fundamental data are handled under their sources' terms (see `FINANCIAL_GOVERNANCE.md` §8 on redistribution). Raw vendor data, if ever licensed in a future phase, is never republished in bulk; derived analytics (ratios, scores, forecasts) are the system's outputs, and their redistribution is governed separately.
- Personal financial information (if a user ever links a portfolio — NOT part of Phase 1 and NOT authorised here) would require its own specification, consent, and encryption design. No portfolio, holdings, or brokerage data is collected in Phase 1.

### 7.4 Retention

- Retention periods per data class are fixed at implementation and recorded (e.g. audit logs retained longest; session records shortest; derived analytics retained with their audit trail per `ANALYTICS_SPECIFICATION.md` §10). Data past its retention period is deleted by a scheduled, logged process — not retained indefinitely "just in case".
- Deletion is verifiable (the deletion job logs what was deleted, when, under which rule). Backup copies follow the same retention rule (§11.3) — a backup is not a loophole for indefinite retention.

## 8. Input validation and rate limiting

### 8.1 Input validation (all inputs, including internal ones)

- **Validate everything:** User inputs, API parameters, file uploads (if ever offered), and — critically — data-source payloads (a malformed or unexpected field from psx-dps/psxdata must not crash analytics or inject a value). Validation is allow-list based (expected type, range, format) rather than block-list based.
- **Financial-input validation:** Symbols must match a known, verified symbol list (a mistyped symbol is an error, not a fuzzy match to another symbol); dates must be valid trading/calendar dates in PKT; numeric inputs must be within stated sane ranges (a price of 0 or negative, a volume that overflows, or a ratio input that violates its formula's domain is rejected with a reason, not clamped silently).
- **Injection prevention:** Parameterised queries / safe APIs only (no string-concatenated queries); output encoding for any user-supplied text displayed in the UI; file-path inputs confined to an allow-listed directory (no traversal); no evaluation/execution of user-supplied code, formulas, or expressions in the analytics path (formulas are fixed deterministic functions — see `FINANCIAL_FORMULAS.md` — not user-entered expressions).
- **Error handling:** Validation failures return a generic, non-revealing message to the caller and a detailed entry in the audit/security log. Stack traces, internal paths, database errors, and source-system details must never leak to the user.
- **LLM-input boundary:** Text sent to local Ollama inference (interpretation layer only) is sanitised and scoped: it contains deterministic values to be explained, not credentials, personal data beyond necessity, or instructions that could alter system behaviour. LLM output is treated as untrusted text — it is never executed, never written to the forecast/valuation/score stores, and never displayed without its interpretation label (see `FORECASTING_SPECIFICATION.md` §8.3).

### 8.2 Rate limiting and abuse prevention

- **Per-account and per-source limits** (thresholds fixed at implementation and recorded): login attempts (§4.1), API requests, data-refresh requests, and export requests. Limits are enforced server-side.
- **Behaviour on limit:** Excess requests are rejected with a generic rate-limit response (and, for repeated abuse, temporary suspension with audit logging). Rate limiting must not be bypassable by rotating a trivial identifier (e.g. changing a query parameter); limits key on authenticated identity and/or stable source, as appropriate.
- **Resource protection:** Request size limits, query-complexity limits (no unbounded date-range or symbol-list requests that could exhaust local compute), and timeouts — so a single request cannot deny service to others on shared local hardware.
- **No live polling in Phase 1.** Rate limiting here is a specification for later phases; Phase 1 authorises no live polling, no bulk fetching, and no automated refresh loop (read-only data inspection only, per the 11-stage workflow).

## 9. Trading restrictions — system must NOT execute real trades initially (EXPLICIT)

This section is a security control, not a suggestion. It is stated here AND in `FINANCIAL_GOVERNANCE.md` §8 so that neither document can be read as permitting trading by omission.

1. **No execution path exists in Phase 1.** There is no broker connection, no order API, no order form that submits to a market, and no background job that places orders. The absence is by design and must be preserved: a later phase that proposes any execution capability requires a separate, explicit approval naming the broker, the account, the order types, the limits, and the audit controls — and that approval is NOT granted by this document.
2. **No output is a trade instruction.** Scores, forecasts, valuations, and recommendations are informational. They must never be formatted, transmitted, or stored as orders, and no component may interpret them as orders.
3. **No auto-trading, no algo-trading, no scheduled orders.** Automated execution on a signal, schedule, threshold, or recommendation is prohibited initially and is not specified here.
4. **Paper / hypothetical illustrations are not trades.** If a later phase adds clearly labelled hypothetical illustrations (e.g. "if this rule had been followed on historical data…"), they must be labelled `hypothetical — not a trade, not a profit claim`, must use the backtesting discipline of `FORECASTING_SPECIFICATION.md` §7, and must never be presented as executed trades or realised profits.
5. **User funds and brokerage credentials are out of scope.** No brokerage account, bank account, card, or trading credential is collected, stored, or requested in Phase 1. Any request for such credentials under the guise of this project must be treated as unauthorised and reported through the incident process (§12).
6. **Enforcement.** Code review and audit (§12, `FINANCIAL_GOVERNANCE.md` §6) must verify the absence of execution paths: no broker SDK, no order endpoint, no execution configuration, and no "trade" button wired to anything beyond an informational display. Discovery of an execution path in a Phase 1 build is a blocking audit finding.

## 10. Audit logs

- **What is logged (minimum):** Authentication successes/failures; role/permission changes; configuration changes (scoring weights, valuation assumptions, recommendation rules, source precedence) with before/after values; score/forecast/valuation/recommendation generation (with model version and input references — the full trail lives in the analytics stores per `ANALYTICS_SPECIFICATION.md` §10, and the audit log records that generation occurred); data-source fetch failures and conflicts; rate-limit triggers; break-glass access; backup/restore events; and security incidents (§12).
- **Log properties:** Each entry carries timestamp in PKT, actor (user/service identity), action, resource, outcome (success/failure), and relevant identifiers (never secrets, passwords, keys, or personal data beyond the actor identifier). Logs are append-only in design (entries are never edited or deleted within retention; corrections are new entries referencing the original).
- **Log protection:** Audit logs are readable only by the Auditor role (§5.1) and the incident-response process (§12). Administrators cannot delete or modify audit logs. Logs are backed up with the same protection as the data they audit (§11.3).
- **Review cadence:** Audit logs are reviewed on a stated schedule (fixed at implementation — e.g. weekly for privileged actions, monthly for general review) and on every incident. Unreviewed logs are not a control.

## 11. Backup procedures and secrets handling

### 11.1 Secrets handling (binding — no credentials in chat/docs/code)

- **No credential, secret, token, password, API key, or private key appears in:** chat messages, documentation (including this document), source code, configuration files committed to any repository, logs, error messages, screenshots, or exports.
- **Approved secure store only.** Secrets live only in the approved secure store / vault mechanism chosen at implementation from local/open-source options at zero cost (the mechanism is recorded when chosen; this Phase 1 document mandates the property — single approved store, access-logged, least-privilege — not a specific product, and no paid vault service is approved).
- **Access to the store** is limited to the services/users that need each secret, is logged, and is reviewed periodically. Human access to raw secret values is minimised (services read secrets at runtime; humans do not copy them into chat or tickets).
- **Rotation and compromise:** Secrets rotate on schedule (§6) and immediately on suspected compromise. A compromised secret is revoked, rotated, and the exposure window is assessed through audit logs (§10) as part of incident handling (§12).
- **Development hygiene:** Example/dummy values in docs/tests are clearly marked as examples and are never valid credentials. Pre-commit checks (or their manual equivalent at zero cost) must reject committed secrets; a committed secret is treated as compromised (revoke + rotate + log), not merely deleted from the file.

### 11.2 Backup procedures

- **What is backed up:** Application configuration (versioned), analytics/score/forecast/valuation stores with their audit trails, audit logs, and user account/role data (subject to §7 retention). Raw market-data caches are backed up only if re-fetching them would be costly or impossible — otherwise they are re-derivable and need not be backed up (the decision is recorded).
- **Backup properties:** Backups are encrypted (key handling per §11.1), access-controlled (backup role only, §7.1), tested by restore (see §11.3), and retained per §7.4 (backups do not extend retention indefinitely).
- **Backup schedule:** Frequency and retention are fixed at implementation and recorded (e.g. daily incremental + weekly full as an illustration — the actual schedule is an implementation decision, not a Phase 1 claim). The schedule must reflect that audit trails are the system's evidence: losing them destroys auditability.

### 11.3 Restore testing (defined, not claimed passed)

- Restore is tested on a stated schedule (fixed at implementation) in an isolated environment — a backup that has never been restored is not a backup, it is a hope. Restore tests verify: completeness (all required data classes present), integrity (audit trails intact, no silent truncation), and that restored data does not overwrite current production data during the test.
- Restore-test results are logged and reviewed. A failed restore test is an incident (§12) until resolved.

## 12. Incident handling outline

1. **Detect:** Monitoring of audit logs (§10), authentication failures, rate-limit triggers, data-source anomalies (e.g. unexpected psx-dps 404 patterns, conflicting sources), and user reports. Detection in Phase 1 is by log review and report, since no live monitoring service is assumed at zero cost beyond local mechanisms.
2. **Contain:** Suspend affected accounts/keys, revoke compromised secrets (§11.1), disable affected features, and preserve evidence (freeze relevant logs and data snapshots — do not delete or "clean up" during an incident).
3. **Assess:** Determine scope (which users/data/outputs affected), whether any score/forecast/valuation/recommendation shown to users was based on compromised or incorrect data, and whether any user-facing correction is required (see `FINANCIAL_GOVERNANCE.md` §6 on corrections — corrections are new records, not edits).
4. **Notify:** Notify affected users and, where required, relevant authorities/partners, with factual, non-speculative information (what happened, what data was affected, what is being done). Notification templates and thresholds are fixed in a later, approved incident plan — this outline does not invent legal notification duties.
5. **Eradicate and recover:** Remove the cause, rotate affected secrets, restore from verified backups where needed (§11.3), and re-validate affected analytics (recompute from verified inputs; do not trust pre-incident outputs).
6. **Learn:** Post-incident review with findings, fixes, and specification updates where needed. Incident records are retained per §7.4 and reviewed by the Auditor role. Repeated incidents of the same cause without a fix are a governance failure, not bad luck.
7. **Trading-specific incident rule:** Any discovery of an unauthorised execution path, a trade instruction, or a brokerage-credential request (§9) is treated as a critical incident: contain immediately (disable the path), preserve evidence, and escalate — it is never handled as a routine bug.

## 13. Testing strategy — defined, not claimed passed

Phase 1 defines the tests; it does not claim any test has passed (11-stage workflow, stage 8):

1. **Authentication tests:** Unique accounts, MFA for privileged roles, session expiry/invalidation, failed-login handling, generic failure messages.
2. **RBAC tests:** Each role's allowed/denied matrix (§5.1); server-side enforcement (UI hiding is not enforcement); direct-object-reference denial; separation-of-duties enforcement.
3. **Key/secret tests:** No secret in code/docs/logs (automated scan or manual equivalent); masked display; rotation; revoked-key denial.
4. **Validation tests:** Injection attempts, traversal attempts, malformed source payloads, out-of-range financial inputs, mistyped symbols — all rejected with generic messages and logged detail.
5. **Rate-limit tests:** Limits trigger correctly per account/source; abuse does not bypass via trivial identifier change.
6. **Audit-log tests:** Every §10 event logged with PKT timestamp/actor/outcome; logs append-only; Auditor-only read; admin cannot delete.
7. **Backup/restore tests:** Restore in isolation verifies completeness and integrity (§11.3).
8. **Trading-absence tests (blocking):** No broker SDK, order endpoint, execution configuration, or trade-wired button exists in the build (see §9.6). Failure of this test blocks release.
9. **Incident-tabletop test:** A simulated incident (e.g. compromised key, conflicting data shown to users) is walked through §12 steps to verify the outline is operable.

No test result is reported in this specification, because no implementation exists yet in Phase 1.

---

*End of SECURITY_REQUIREMENTS.md — Phase 1 specification only. No credential, secret, key, or password is contained in this document, and none may be added to it.*
