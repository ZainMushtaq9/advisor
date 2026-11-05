# D-12 Covering Brief — Token-Gated Report Approval

**Status: PREPARATION ONLY — no implementation in this task.**
This brief is the unblocker named in the defect register for D-12
("A phase brief that covers it (belongs to no brief so far)").
Implementation needs the brief's approval first, and must be done as
its own work item on its own branch. Nothing in this document changes
any code, any report status, or any acceptance verdict.

**Defect:** D-12, low, open — "Token-gated report approval
(Phase 24 candidate)". Current state: report approval is an explicit
CLI transition only; it is not token-gated.

## 1. Current state (measured, 2026-11-05)

- Transitions: `DRAFT -> APPROVED` or `DRAFT -> REJECTED` only, via
  `backend/app/services/reports/runner.py` `approve()` /
  `reject()` and the CLI `scripts/run_reports.py --approve/--reject`.
  Both functions guard on `status == "DRAFT"` and return an error
  otherwise; neither records an actor, a reason, or an audit row.
- `APPROVED` means **internally reviewed only**. There is no publish
  step and no external-send path anywhere, so an APPROVED report is
  still internal. Token-gating must not be confused with publishing.
- Read paths (all GET-only, in `backend/app/api/v1/endpoints/reports.py`):
  `/reports/templates`, `/reports` (list), `/reports/status`,
  `/reports/{report_id}`. These serve report content today without a
  token requirement.
- Existing auth machinery (reuse, do not reinvent):
  `backend/app/services/auth/dependencies.py` — permissive mode
  (`optional_principal`: a presented Bearer token is validated, an
  absent/invalid one is simply None) and role-gated dependencies;
  `backend/app/services/auth/service.py` `validate_token`;
  `backend/app/api/v1/endpoints/auth.py` (`/auth/status`, `/auth/me`,
  `/auth/principal`); `AUTH_ENFORCEMENT` setting (`off`/`on`,
  production requires `on`).
- Hard constraint carried into any implementation: **auth tables are
  0/0/0 by parent/user decision — no live auth accounts are to be
  created without a separate authorization.** Token issuance therefore
  needs a bootstrap decision (see §5) before any gating can be
  exercised live.
- Related gap D-10 (accepted, low): "No frontend token support for
  enforced mode — needed only if enforced mode is ever required for
  the dashboard." Any API-side gating that the dashboard must use
  depends on D-10 being resolved first or in the same work item.

## 2. Scope

**In scope for the implementing work item:**

- The two write transitions: `DRAFT -> APPROVED` and
  `DRAFT -> REJECTED`, whether invoked from the CLI or from a new
  API route (see §4 for the route decision).
- The four read paths above: decide per path whether it stays open,
  becomes token-optional (permissive mode), or becomes token-required
  (see §4 — the brief recommends token-optional for reads, required
  for writes, but the implementer must confirm this with the parent
  before coding).
- Audit logging of every approval/rejection decision: who (token
  principal), what (report id, old/new status), when, and from where
  (CLI vs API). The audit row must be written in the same transaction
  as the status change, never after the fact.

**Out of scope:**

- Publishing, sharing, or any external send of reports (no such path
  exists; this brief does not create one).
- Changing what APPROVED means (still internally reviewed only).
- Changing report content, figures, or generation (Phases 22/29).
- Frontend token support itself (D-10) except as a dependency note.
- Any change to the acceptance gate, verdicts, or recomputations.

## 3. Threat model

The deployment is local/loopback-only (backend 127.0.0.1:8000,
frontend 127.0.0.1:3000, no TLS because traffic never leaves the
machine). The realistic threats are therefore narrow, and the design
must not over-build for a hosted threat model that does not exist:

1. **Accidental approval by the operator.** Today a single CLI
   invocation with no actor record flips a report to APPROVED. A
   mistaken id approves the wrong report, and nothing records who
   did it. *Mitigation:* require a token tied to a named principal
   and write an audit row; keep the DRAFT-only guard.
2. **A second local process or user on the same machine calling the
   API.** Loopback is not authentication. Any local process can
   today call the reports endpoints. *Mitigation:* token-required
   writes in enforced mode; reads stay permissive until D-10 lands.
3. **Token leakage via logs, exports, or the frontend.**
   *Mitigation:* never log a token value (existing redaction rules
   already forbid secret echo in `/config/status` and logs); tokens
   are validated by hash comparison, never stored in cleartext;
   frontend token storage is D-10's problem, not this item's.
4. **Replay / stale approval after a report is superseded.**
   Reports are versioned (`is_current`, `supersedes_id`).
   *Mitigation:* gating applies to the current version only; an
   approval attempt on a superseded version is rejected, same as
   the existing non-DRAFT rejection.
5. **Explicitly NOT in the threat model:** remote attackers (no
   exposed surface), broker/order paths (none exist), and report
   content forgery (figures carry their own provenance and quality
   status; gating the transition does not re-verify content).

## 4. Design (to be confirmed before implementation)

- **Token type:** reuse the existing Bearer token mechanism
  (`validate_token`), not a new scheme. Tokens are per-principal,
  stored hashed, with an expiry; the implementing item must state
  the expiry policy (recommendation: short-lived operator tokens,
  e.g. 24h, issued by an explicit operator command — not by the API
  itself).
- **Role requirements:** a single new role is enough:
  `report_approver`. The approval dependency requires
  (a) a valid token, (b) the `report_approver` role, and
  (c) enforced mode `on` for API calls. In permissive mode
  (`AUTH_ENFORCEMENT=off`, the current default), API approval
  attempts are rejected with 401 unless a valid approver token is
  presented — i.e. writes are always gated, reads follow the mode.
  (Alternative, to be decided by the parent: writes gated only when
  enforced mode is on, and open otherwise. The brief recommends
  always-gated writes because the CLI already proves the operator
  is local; the API needs no permissive backdoor.)
- **CLI vs API paths:** the CLI keeps working, but it must also
  present a token once gating lands — via an environment-provided
  token (`PSX_APPROVER_TOKEN`, never a CLI argument, never logged)
  or via a local operator credential file (0600, gitignored, same
  pattern as `database/.env`). The CLI must NOT gain an ungated
  bypass flag: a bypass would defeat the entire item. The API route
  (if added) is `POST /reports/{report_id}/approve` and
  `POST /reports/{report_id}/reject`, both requiring the approver
  dependency; the runner functions gain a `principal` parameter and
  write the audit row. If the parent prefers CLI-only approval to
  remain the only write path, the API route is dropped and only the
  CLI token + audit row are implemented — that is a smaller, still
  complete resolution of D-12.
- **Audit logging:** one row per decision in the existing auth audit
  table (or a new `report_approval_audits` table if the auth table's
  shape does not fit — decide at implementation time, do not mix
  concerns silently). Fields: report id, old status, new status,
  principal, token id (never the value), path (CLI/API), timestamp.
  The audit write shares the status-change transaction.
- **Backward compatibility:** existing CLI invocations without a
  token must fail loudly (exit non-zero, clear message) after the
  change lands — not silently succeed. No existing APPROVED/REJECTED
  row is rewritten; history keeps its (absent) actor as-is, and the
  run report for the implementing item must say so. The DRAFT-only
  guard, the runner's error strings, and the "APPROVED means
  internally reviewed" semantics are unchanged.
- **Interaction with enforced mode:** production already refuses to
  boot unless `AUTH_ENFORCEMENT=on`. Gating must be tested in both
  modes: permissive (reads open, writes gated) and enforced (reads
  per §4 decision, writes gated). The readiness endpoint's
  `auth_enforcement` field already reports the mode.
- **Interaction with D-10:** until the frontend can present tokens,
  the dashboard cannot use a gated approval route. The implementing
  item must either (a) land D-10 first, (b) land both together, or
  (c) keep approval CLI-only and gate only the CLI. Option (c) is
  the smallest complete step and the brief's recommendation if
  D-10 is not funded.

## 5. Prerequisites and decisions needed before implementation

1. Parent/user decision: CLI-only gating vs CLI + API routes (§4).
2. Parent/user decision: always-gated writes vs gated-only-when-enforced.
3. Parent/user decision: token bootstrap — who issues the first
   approver token, and under what authorization, given that no live
   auth accounts exist today (0/0/0 by decision). No account or
   token is created by this brief.
4. D-10 sequencing decision (see §4).
5. Expiry policy for approver tokens (recommendation in §4).

## 6. Tests to be written (by the implementing item)

- CLI approve/reject without a token fails non-zero and changes
  nothing; with a valid approver token succeeds and writes exactly
  one audit row with the correct principal, old/new status, and path.
- CLI approve on a non-DRAFT report still errors (existing guard
  preserved); approve on an unknown id still errors.
- API approve/reject (if routes are added): no token → 401; valid
  token without the approver role → 403; valid approver token →
  200 with status change + audit row; second approve → error
  (non-DRAFT guard).
- Read paths: permissive mode serves without a token; enforced mode
  follows the §4 decision (test both).
- No token value appears in any log, error message, or export
  (redaction test, same pattern as the existing secret-echo tests).
- Existing approval semantics unchanged: APPROVED still means
  internally reviewed; no publish/send path appears (scan test,
  same pattern as the existing execution-identifier scans).
- Regression: the full backend suite, the acceptance runner
  (approval is not an acceptance check today — confirm it stays
  that way), and the frontend suite if any dashboard surface changes.

## 7. Acceptance criteria

- D-12 moves from open to fixed only on measured evidence: the tests
  above pass, a live (non-production) approval with a token writes
  an audit row, and an approval without a token is refused.
- The defect register entry for D-12 is updated by the implementing
  item (not by this brief) with that evidence.
- No report status, figure, or acceptance verdict changes as a side
  effect of landing the gating.
- The run report for the implementing item records the §5 decisions
  as given, not as assumed.

## 8. Risks

- **Token bootstrap chicken-and-egg:** the first approver token
  needs an issuer, and no accounts exist. If the parent does not
  authorize account creation, the item stalls at §5 — that is a
  correct stall, not a reason to ship an ungated fallback.
- **Operator friction:** a token requirement on a local CLI annoys
  the single operator. Mitigate with a documented, short operator
  flow (one command to mint, env var to present), not with a bypass.
- **Scope creep into publishing:** APPROVED is easily misread as
  "ready to share". The implementing item must keep the
  internally-reviewed wording everywhere it appears.
- **D-10 dependency:** dashboard approval cannot work until the
  frontend presents tokens; landing API routes without D-10 creates
  a route nobody can use from the UI.

## 9. Rollout steps (for the implementing item)

1. Get the §5 decisions in writing from the parent/user.
2. Implement on a fresh branch from the then-current tip (not this
   branch); CLI token + audit row first, API routes second if
   approved.
3. Tests (§6) green, full regression green, acceptance run
   unaffected (verify, do not assert).
4. Operator runbook: minting, presenting, rotating, and revoking
   approver tokens; what to do when a token is lost (revoke + reissue,
   never recover).
5. Commit, push, verify remote SHA; propose the register entry to
   the parent (do not edit the consolidated registers directly).
