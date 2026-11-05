# GitHub Branch and Commit Audit — PSX Intelligence AI

**Audit baseline:** branch `phase-30-release`, tip `8937338`
(`893733861a9ce2d9ba1a35c7d55bacf15abcb582` — Phase 30 handover
`6b1ff9f` + parent consolidation #2 `8937338`).
**Audit date:** 2026-11-05 (Asia/Karachi).
**Method:** read-only. `git ls-remote` (fresh, by the auditor),
`git merge-base --is-ancestor`, `git ls-tree`, `gh repo view`,
`gh pr list`, `gh run list`, `gh api` branch-protection checks,
tracked-file and history secret scans. No commits, pushes, merges,
settings changes, or deletions were made by this audit. No credential
value is printed anywhere in this report.

## 1. Repository identity (verified via `gh repo view --json`)

| Field | Verified value |
|---|---|
| Owner | `ZainMushtaq9` |
| Name | `advisor` |
| URL | https://github.com/ZainMushtaq9/advisor |
| Visibility | PUBLIC |
| Default branch | `main` |
| Description | (empty) |
| Created | 2026-11-04T06:35:28Z |
| Last pushed (at audit time) | 2026-11-05T01:47:12Z |

## 2. Remote branch tips — all verified, none moved

Every claimed tip was re-verified by the auditor with
`git ls-remote origin 'refs/heads/*' 'refs/tags/*'` and matched
exactly (40 branch heads + 1 tag). No tip moved during the audit.

| Branch | Tip (short) | Branch | Tip (short) |
|---|---|---|---|
| phase-02-repository-foundation | 016f3c8 | phase-17-backtesting | 5bea951 |
| phase-03-database-storage | b22281a | phase-18-orchestration | 6b8ba4d |
| phase-04-company-registry | 0f4342f | phase-19-rag-knowledge-base | 3cd98e7 |
| phase-04-completion | c078c0b | phase-20-screener | c91acb1 |
| phase-04-sampled-verification | 9204632 | phase-21-alerts | dbeee4a |
| phase-04-leap-load | eb2e331 | phase-22-reports | 45d08ec |
| phase-05-snapshot-import | ffc9d61 | phase-23-dashboard | 6662d34 |
| phase-05-completion | f4b703d | phase-24-security | f648bd5 |
| phase-05-revisit | e281c73 | phase-25-automation | a129614 |
| phase-06-technical-analytics | 6efede9 | phase-26-evaluation | b6f007c |
| phase-06-completion | e556806 | phase-27-observability | 544fecc |
| phase-06-revisit | 85f4a72 | phase-28-deployment | b791b7d |
| phase-07-financial-statements | 366ed32 | phase-29-acceptance | 858e914 |
| phase-07-remainders | 59834f1 | phase-30-release | 8937338 |
| phase-07-hbl-followup | f53cde8 | main | eb6025b |
| phase-07-hbl-extraction | 42bd8e2 | — | — |
| phase-08-fundamental-analysis | 9969f5a | phase-09-valuation | f9de2cc |
| phase-10-macro-sector | 9df2266 | phase-11-news-events | b6c6026 |
| phase-12-ownership-actions-breadth | a58a104 | phase-13-forecasting | 9eb2f41 |
| phase-14-risk-management | 04ad858 | phase-15-decision-engine | 9f78fb4 |
| phase-16-portfolio-construction | cb2a70c | — | — |

## 3. Tags

- Exactly one tag exists, local and remote agree: `v0.2.0-handover`,
  object `3dcae17`, **annotated** (not lightweight).
- It peels to `6b1ff9f` (the Phase 30 run-report commit), **not** to
  the current tip `8937338`. The final consolidation commit is
  therefore untagged. Tag message states the system verdict
  (PARTIALLY COMPLETE), "No production release, no merge to main, no
  human sign-off claimed" — consistent with the handover.
- No other tags exist.

## 4. Ancestry — what is integrated and what is not (headline finding)

**Main-line chain, fully integrated (every link verified ancestor of
the next, through to `8937338`):**

`016f3c8 → b22281a → 0f4342f → 366ed32 → 59834f1 → f53cde8 →
9969f5a → f9de2cc → 9df2266 → b6c6026 → a58a104 → 9eb2f41 →
04ad858 → 9f78fb4 → cb2a70c → 5bea951 → 6b8ba4d → 3cd98e7 →
c91acb1 → dbeee4a → 45d08ec → 6662d34 → f648bd5 → a129614 →
b6f007c → 544fecc → b791b7d → 858e914 → 8937338`

`8937338` has 53 commits in its history and a single parent
(`6b1ff9f`); there are **zero merge commits** in its history.

**Side branches NOT integrated into the phase-30 tree** (each tested
`git merge-base --is-ancestor <sha> 8937338` → NOT ancestor), with
file-level proof (`git ls-tree` on `8937338`):

| Branch (tip) | Distinctive files ABSENT from `8937338` |
|---|---|
| phase-04-completion (c078c0b) | `backend/app/api/v1/endpoints/universe.py` (the Phase 4 universe endpoint), `docs/phase-04/phase_04_completion_2026-11-04.md`, `docs/phase-04/phase_04_rejudgment_2026-11-04.md` |
| phase-04-sampled-verification (9204632) | LEAP procedure/plan docs (see leap-load row) |
| phase-04-leap-load (eb2e331) | `scripts/load_leap_evidence.py`, `backend/app/services/registry/leap_evidence.py`, `backend/tests/test_leap_evidence.py`, `docs/phase-04/leap_load_report_2026-11-04.md`, `docs/phase-04/leap_observations_2026-11-04.json`, `docs/phase-04/field_scoped_leap_promotion_procedure.md`, `docs/phase-04/sampled_verification_plan_2026-11-04.md` — the entire LEAP loader is absent; `git ls-tree … | grep -i leap` on `8937338` returns nothing |
| phase-05-completion (f4b703d) | `docs/phase-05/phase_05_rejudgment_2026-11-04.md` |
| phase-05-revisit (e281c73) | Above + `docs/phase-05/phase_05_rejudgment_2026-11-04_revisit.md` |
| phase-06-completion (e556806) | `docs/phase-06/completion_addendum_2026-11-04.md` |
| phase-06-revisit (85f4a72) | Above + `docs/phase-06/phase_06_rejudgment_2026-11-04_revisit.md` |
| phase-07-hbl-extraction (42bd8e2) | `docs/phase-07/page_maps/hbl_{sfp,pl,cf,ce}.json`, `docs/phase-07/run_report_hbl_2026-11-05.md` — the only `hbl`-named file in the `8937338` tree is `docs/phase-07/hbl_followup_blocked_2026-11-04.md` |

**What this means (severity: MEDIUM, integration gap):**

- The Phase 5/6 engines ARE in the tree: `ffc9d61`
  (phase-05-snapshot-import) and `6efede9`
  (phase-06-technical-analytics) are ancestors of `8937338`, and all
  phase runner scripts are present. The non-ancestor branches are the
  completion/rejudgment documentation branches plus the two
  data-producing side branches (LEAP load, HBL extraction).
- The LEAP evidence ROWS in the database were produced by code that is
  not in the released tree, and the HBL extraction code (page maps and
  the `skip_values` / `blank_columns` / `label_parts` extractor
  options — verified absent from `backend/app/services/
  financial_statements/extract.py` on `8937338`) is not in the
  released tree either. The released tree alone therefore cannot
  reproduce two parts of its own database state; reproduction requires
  checking out `eb2e331` and `42bd8e2` (which this audit does, in
  detached scratch worktrees, without committing their code).
- Commit `8937338` is titled "Parent consolidation #2: Phases 8-30,
  LEAP load, HBL outcomes, recoveries 5-7, Phase 28 follow-up", yet
  its own diff touches only 3 documentation files (49 insertions:
  `docs/development/MASTER_EXECUTION_LOG.md` +6,
  `PHASE_COMPLETION_REGISTER.md` +35, `PROJECT_EXECUTION_STATE.md`
  +8) and it is a single-parent commit, not a merge. The
  consolidation is documentary, not a code integration of those side
  branches. The "LEAP load" and "HBL outcomes" named in its title are
  not reflected in its tree.
- The missing universe endpoint (`/api/v1/data/universe`) breaks
  nothing at runtime: no backend or frontend code on `8937338`
  references `data/universe`. It is a missing deliverable, not a
  broken integration.

**Main vs phase branches:** `git merge-base eb6025b 8937338` exits 1
with empty output — **no merge base; unrelated histories, as
claimed**. `main` is a single commit (`eb6025b`, "Initial commit",
README `# advisor` only).

## 5. Pull requests, merges, Actions, branch protection

- `gh pr list --state all` → empty. **No pull requests exist in any
  state. No merge to main exists.**
- `git log --merges 8937338` → 0 merge commits. All phase work reached
  the remote only as direct branch pushes, never via PR or merge.
- `gh run list` → empty. **No Actions runs exist.**
- `.github/workflows/ci.yml` on `8937338` triggers only on push/PR to
  `main`/`development`, with a single `env-and-hygiene` job (no
  backend pytest or frontend jobs). `workers.yml` is documented as
  "NOT yet run in CI" and triggers only on `workers/**` paths.
  Combined with zero PRs and main never receiving a push, the empty
  run list is fully consistent with the workflow definitions.
  **CI-in-CI is UNVERIFIED (MEDIUM, open).**
- Branch protection (`gh api …/branches/{main,phase-30-release}/
  protection`) → HTTP 404 "Branch not protected" for both (GitHub's
  documented not-protected signal, not an auth failure — the same
  session listed the repo, PRs, and runs). **Both `main` and
  `phase-30-release` are UNPROTECTED (MEDIUM, open).** No setting was
  modified by this audit.

## 6. Commit integrity

- Latest commits on `8937338` (author = committer,
  `psx-intelligence-ai-team-a <team-a@localhost>`):
  `8937338` (consolidation #2), `6b1ff9f` (Phase 30 run report),
  `e84e92b` (Phase 30 release snapshot), `858e914` (Phase 29
  SHA-record), `2334df7` (Phase 29 acceptance).
- Signatures: `git log --show-signature` shows no signature block;
  `%G?` = `N` (no signature) for the top commits. **All commits are
  unsigned** — reported, not treated as a defect by itself.
- Force-push status is **not determinable remotely** (remote tips
  only show current state; reflog is local-only). The local
  remote-tracking reflog shows sequential parent-child updates only;
  no evidence of a rewrite was observed in the linear chain.

## 7. Secrets exposure

- Tracked-file pattern scan on `8937338` (password/passwd/secret/
  token/api-key/private-key across `*.py`, `*.sh`, `*.yml`, `*.yaml`,
  `*.json`, `*.example`): only template warnings, CI sanity-check
  wording, auth-posture documentation ("deliberately NO login… route
  over HTTP"), config comments ("nothing secret is hardcoded"), and
  hash-only auth model documentation. **No literal credential value
  was observed.**
- `git ls-tree -r --name-only 8937338 | grep -iE '\.env$|\.pem$|
  \.key$|credentials'` → **empty. No tracked `.env`, `.pem`, `.key`,
  or credentials file exists.**
- Phase 28 `.env.example` CHANGEME remediation: five template files
  are tracked (`.env.example`, `backend/.env.example`,
  `database/.env.example`, `deployment/.env.example`,
  `ops/env.production.example`). `database/.env.example` has exactly
  2 `CHANGEME` occurrences, on its two sensitive assignments
  (`DATABASE_URL` line 7, `PGPASSWORD` line 12). The remediation is
  present; the earlier template version (`31cc01d`) had 0
  `CHANGEME` occurrences, so the placeholder style evolved — an
  observation, not an exposure finding.
- Force-added `backend/app/services/auth/tokens.py`: confirmed
  tracked despite the blanket `.gitignore` line 14 (`*token*`),
  consistent with a force-add. Content contains no literal token or
  secret: `TOKEN_PREFIX = "psx_"`, runtime generation via
  `secrets.token_urlsafe(32)`, SHA-256 hashing only, "shown to its
  owner exactly once, at issue time, and never logged, never returned
  again, and never stored."
- History scans: `git log --all -S 'PGPASSWORD'` returns 5 commits
  (template/script references to the variable name, not values);
  `git log --all -- '*token*'` returns exactly one commit (`f648bd5`,
  Phase 24, which introduced `tokens.py`). **No credential values
  found in history.**

## 8. Push log staleness (LOW)

`docs/development/GITHUB_PUSH_LOG.md` on `8937338` (143 lines) does
NOT cover phases 8–30: its dated sections run only through
2026-11-04 (Phases 2–5), its header still reads "NOT PUSHED YET",
and its last entry is the Phase 5 snapshot-import push attempt
(2026-11-04, tip `5c6536c`, BLOCKED on credentials). It must not be
cited as evidence of current push state; the remote tip list in §2
above is the authoritative record.

## 9. Verdict for this audit area

- Remote state matches all prior claims exactly; nothing moved.
- No PRs, no merges, no Actions runs, no branch protection.
- Main remains the single README commit with unrelated history.
- **Integration gap (MEDIUM):** LEAP loader, universe endpoint, and
  HBL extraction code are absent from the phase-30 tree; the
  consolidation commit is documentary, not a code merge.
- **Secrets: PASS** — no tracked secret files, no literal values,
  CHANGEME remediation present, `tokens.py` clean.
- **Open items:** CI-in-CI (UNVERIFIED), branch protection (absent),
  unsigned commits (noted), force-push status (not determinable).
