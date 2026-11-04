# PSX Intelligence AI — Account Register

Date: 2026-11-04 (Phase 2, interim — updated when any account status changes)

## Standing authorization and hard restriction (read first)

- The user has authorized Muse to independently register/create FREE project-related accounts using zainmushtaq5439@gmail.com, including ordinary registration forms with accurate project information, usernames, free configuration, email verification via authorized mailbox access, login, settings, and connecting authorized project tools, without repeated conversational permission for each ordinary step.
- HARD RESTRICTION — this overrides any broader reading of that authorization: Muse must NOT purchase subscriptions, start paid trials requiring payment details, add payment cards, accept financial obligations, misrepresent identity, use fabricated personal information, bypass CAPTCHA or identity verification, circumvent security restrictions, or ACCEPT LEGALLY BINDING AGREEMENTS ON THE USER'S BEHALF.
- Practical consequence, applied in Phase 2: almost every registration requires accepting Terms of Service, which is a legally binding agreement. Therefore, for any account proposed in the future, STOP at the ToS/payment/CAPTCHA/identity-verification step, report the EXACT requirement (service, ToS link, payment/CAPTCHA/verification step), and do NOT click accept, enter payment details, or bypass the check. The parent will route that specific acceptance to the user (e.g. via browser takeover) — an account must never be pretended to have been created past that step.
- NO SPECULATIVE ACCOUNTS: an account is created only when a phase component actually requires it, it is free, and it passes the restriction check above.
- NEVER stored in this file, in source code, in git commits, in logs, or in ordinary documentation: passwords, recovery codes, authentication tokens, or session cookies. Where a future account requires credentials, use the platform's secure credential mechanism / secure generated passwords or passkeys where supported; enable 2FA where possible; never disable existing security protections to bypass an authentication requirement.
- Mailbox note: no email verification was needed or attempted for any Phase 2 account below, so no mailbox-connection blocker arises in Phase 2. If mailbox verification is ever needed and the authorized connection is unavailable in the environment, that exact blocker must be reported instead of inventing a verification.

## Phase 2 outcome: No external account created in Phase 2

**No external account was created in Phase 2 — because no Phase 2 component actually requires an external account.**

Components checked (all Phase 2, local development only):

| Component | External account required? | Reason / status |
|---|---|---|
| Frontend (Next.js/React/TypeScript/Tailwind) | No | Local dev server and build only. No Vercel/Netlify/hosting account was created or needed in Phase 2. |
| Backend (FastAPI) | No | Local uvicorn only. No hosted API account needed. |
| PostgreSQL (self-hosted) | No — local role only, not an external account | Local server + local role `psx_app` (Team D). The role password lives only in `database/.env` (mode 0600, gitignored) and is NOT recorded here, in code, or in git. This is not a website account. |
| Redis (self-hosted) | No | Local server only, if running. No managed Redis account. |
| Celery/workers | No | Local workers only. No cloud queue account. |
| Docker Engine | No | Local engine use only. No Docker Hub account was created; no Docker Hub sign-in was performed for Phase 2 verification (Docker itself remains unverified at interim — see LIVE_TEST_REPORT.md). Base-image pulls, if any in a later verified Docker run, must still pass the ToS/restriction check before any account step. |
| Ollama / open-weight models | No | Not installed in Phase 2; local inference is a later-phase concern. No Ollama Cloud account, no `:cloud` models, no account/key. |
| Playwright browsers | No | Not installed in Phase 2 (Team B follow-up). No account. |
| Monitoring/logging | No | Local logging only. No paid/hosted monitoring account. |
| GitHub | No NEW account created in Phase 2 | See the pre-existing account row below. This is not a new registration. |

## Pre-existing account (NOT created by Muse in Phase 2)

| Website name | Official URL | Registration email | Account purpose | Registration date | Free-plan status | Verification status | Connected project components |
|---|---|---|---|---|---|---|---|
| GitHub (user's existing account) | https://github.com/ | zainmushtaq5439@gmail.com (user's known project Gmail, per authorization) | Permanent project repository host for PSX Intelligence AI | Pre-existing — created by the user, NOT by Muse in Phase 2 (date not recorded by Muse; do not invent one) | GitHub Free (per Phase 1 stack; full GitHub Free terms remain UNVERIFIED per Phase 1 gate G-02 — re-check at push time) | User-created repo verified by the user as README-only at decision time: ZainMushtaq9/advisor (https://github.com/ZainMushtaq9/advisor) | Phase 2 push target ONLY, after Phase 2 passes its independent audit, to branch phase-02-repository-foundation. No push has been made yet. No PR created. No merge to main. |

Notes on the GitHub row:
- No GitHub remote is configured in the local Phase 2 repository at interim (verified: `git remote -v` returns nothing).
- Push authentication, if it requires a sign-in or a runtime approval card, is a separate step from registration: if a runtime approval card blocks it, report the exact permission/approval setting with evidence, mark the push BLOCKED pending that setting, and do NOT bypass it.
- Before any push, re-verify remote state, local git status, and that no secrets/.env/credentials are included (see GITHUB_PUSH_LOG.md pre-push checklist).
- The GitHub account's own Terms of Service were accepted by the user when they created the account/repo, not by Muse. Muse must not accept any NEW legally binding agreement on the user's behalf for this or any other service.

## Accounts proposed but NOT created (none in Phase 2)

None. No account was proposed in Phase 2 that reached a ToS/payment/CAPTCHA/identity-verification step, so no such step is reported here. If a later phase proposes an account, its exact ToS link and verification step must be added to this file BEFORE any acceptance click, and the parent must route that acceptance to the user.

## Update rule

Append a row to the table above for every future account actually created (with website, URL, email, purpose, date, free-plan status, verification status, connected components), and never add a password, recovery code, token, or session cookie to this file. If an account creation is blocked at ToS/payment/CAPTCHA/verification, record the service, the exact requirement, and the status BLOCKED — never as created.
