# Contributing to PSX Intelligence AI

## Non-negotiable rules (from Phase 1, binding on every contributor)

1. **PKR 0 absolute.** No paid dependency, paid tier, paid API, or paid
   hosting. If a step would cost anything, stop and get a separate, explicit
   approval — it is not covered by any standing instruction.
2. **No secrets in git history.** Never commit `.env`, passwords, API keys,
   tokens, private keys, credentials files, or personal information. The
   `.gitignore` excludes these; if one is committed by accident, stop and
   report it — do not try to quietly rewrite shared history.
3. **No fabricated data.** Never invent a price, symbol, company figure,
   sector count, endpoint, or capability. Anything unverified is marked
   UNVERIFIED with the check still needed.
4. **Never silently harmonise conflicts.** ~496 trading vs ~1029 listed vs
   1000+ tickers, and 38 vs 37 sectors, are unresolved. Keep both values with
   provenance and route the conflict; do not pick one quietly.
5. **Deterministic numbers only.** Financial numbers come from deterministic
   functions over stored, provenance-tagged data. An LLM explains or selects a
   calculation; it never produces the number.
6. **No real trades.** No broker connection, order path, or execution branch.
7. **Licence gate (G-02).** Before installing a dependency, read its shipped
   LICENSE file and record it in `docs/phase-02/LICENSE_REGISTER.md`. If it
   requires payment, stop and replace it.
8. **One sending/computation method per job.** Never run two methods for the
   same job at once (applies to email-style batches, workers, and schedulers).
9. **Do not commit another team's work.** Each team commits only its own
   files. If you find another team's in-progress files untracked, leave them
   alone and tell them.

## Branches (Phase 2 foundation)

- `main` — stable skeleton; initial commit lives here.
- `development` — integration branch for Phase 2 work.
- `feature/frontend-foundation`, `feature/backend-foundation`,
  `feature/database-foundation` — foundation work per area.

Create further branches only when a team actually needs one; do not create
branches speculatively.

## Workflow for a change

1. Work on the branch for your area; keep changes scoped to your team's files.
2. Run the checks for your area (backend: pytest offline-first; frontend:
   `npm run lint` / `npm run build`; docs: re-read for unverified claims).
3. Confirm no secret, data file, or large generated dataset is staged:
   `git status` and `git diff --cached --stat` before committing.
4. Write a commit message stating what changed and what is still UNVERIFIED.
5. Never claim a test, install, or verification you did not run.

## Environment

See `docs/phase-02/LOCAL_DEVELOPMENT_GUIDE.md`. Configure from
`.env.example` (copy to `.env`, never commit it). PostgreSQL, Redis, Docker,
and Ollama are optional for skeleton work; the guide states what works
without each of them.

## Data licensing posture

PSX data use is internal analysis only until PSX terms are verified in
writing. No resale, live-feed republication, public dataset/API, or commercial
embedding of PSX data. FRED is gated out of AI training, caching, and
commercial output until its Terms are re-read. Full policy:
`docs/phase-01/DATA_LICENSING_POLICY.md`. This file is not legal advice.
