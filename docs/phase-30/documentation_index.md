# Phase 30 — Documentation Index

The authoritative current-state document is `handover_report.md` (this
folder). The table below maps each documentation area the Phase 30
brief requires to where it actually lives. Per-phase
`implementation_specification.md` + `run_report.md` files under
`docs/phase-NN/` are the evidence for each phase; this index does not
duplicate them.

| Area | Location | Status |
|---|---|---|
| Architecture | `docs/phase-01/` (TECH_STACK_DECISIONS, ADRs, AGENT_ARCHITECTURE, DATABASE_DESIGN, DATA_FLOW_DIAGRAM, DEPLOYMENT_ARCHITECTURE) + per-phase specs | Complete as designed; Phase 23 dashboard + Phase 24 auth + Phase 25 jobs + Phase 28 ops extend it. No single consolidated architecture diagram post-Phase 2 — the per-phase specs are the record. |
| API reference | `backend/app/api/v1/endpoints/` (24 files, all GET-only except none — there are no write routes) + `docs/phase-04/api_documentation.md`, `docs/phase-05/market_api_documentation.md`, `docs/phase-06/api_documentation.md`, per-phase endpoint docs | No single consolidated API reference document exists (gap, recorded honestly). The endpoint files are the reference; OpenAPI docs are disabled in production (Phase 24). |
| Schema | `database/migrations/` (0001 → `20261104_0024`) + `docs/phase-01/DATABASE_DESIGN.md`, `DATABASE_ENTITY_CATALOG.md` + per-phase migration notes | Complete to head `20261104_0024`. |
| Model methodology | `docs/phase-01/FINANCIAL_FORMULAS.md`, `FORECASTING_SPECIFICATION.md` + Phase 8–17 implementation specs + Phase 26 model cards (9, all NOT_PROMOTED) | Complete for what is implemented; every NOT_CALCULABLE method carries its exact reason. |
| Data sources | `docs/phase-30/licence_and_source_inventory.md` + Phase 4/5/7/10 source matrices + `docs/phase-07/source_matrix.md` | Complete, with verdicts (ALLOWED / DISCOVERY ONLY / NOT USED / BLOCKED). |
| Operations | `ops/README.md` + `docs/phase-25/` (jobs) + `docs/phase-27/` (SLOs, playbooks) + `docs/phase-28/` (deployment guide, operations handover) + `docs/phase-30/release_checklist.md` | Complete for operator-invoked operation; no daemon, no host cron, no system-wide service install (operator decisions, D-09). |
| Troubleshooting | `docs/phase-02/TROUBLESHOOTING.md` + `docs/phase-27/incident_playbooks.md` + recovery recipes in Phase 22/25/28/29 run reports | Complete, including the 7-times-proven VM-replacement recovery recipe. |
| Security | `docs/phase-24/` (rbac_model, threat_model, incident_response_plan, audit_logging, vulnerability_test_report) + Phase 29 `security_licensing_privacy_audit.md` | Complete for the current posture; open items are D-07 (no live accounts), D-10 (frontend token support), D-12 (token-gated approval). |
| Backup / restore | `docs/phase-02/DATABASE_SETUP.md` + `docs/phase-28/` (backup retention policy, restore drill, fresh-environment test) + `database/backup.sh`, `restore.sh`, `verify_restore.sh` (headers document usage + safety) | Complete; drill re-proven in Phase 30 (`run_report.md`). |
| User guide | `docs/phase-30/user_guide.md` | Written in Phase 30 (no standalone user guide existed before). |
| Developer guide | `docs/phase-30/developer_guide.md` | Written in Phase 30 (branch/commit/DB/testing/recovery discipline consolidated from phase run reports). |
| Licence + source inventory | `docs/phase-30/licence_and_source_inventory.md` | Written in Phase 30 (backend LICENCES.md + frontend installed-metadata licences + data-source verdicts). |
| Changelog | `CHANGELOG.md` (root) | `[0.2.0-handover]` entry added in Phase 30; earlier entries are Phase 2-era and are preserved as history, not rewritten. |
| Registers (parent-consolidated) | `docs/development/PHASE_COMPLETION_REGISTER.md`, `PROJECT_EXECUTION_STATE.md`, `MASTER_EXECUTION_LOG.md` | Last updated on the Phase 7 remainders branch (`59834f1`); consolidation #2 (LEAP load, HBL blocked report, Phases 8–30, recoveries #5–#7, D-05/D-13 fixes, Phase 28 post-report follow-up) is the parent's post-Phase-30 task — NOT done by any phase coordinator, by design. `GITHUB_PUSH_LOG.md` intentionally not updated (gap noted since Phase 4). |

## Gaps stated plainly (not hidden)

1. No single consolidated API reference document (endpoint files +
   per-phase docs are the reference).
2. No single consolidated post-Phase-2 architecture diagram (per-phase
   specs are the record).
3. Registers are stale (last consolidated at `59834f1`); consolidation
   #2 is owed by the parent after Phase 30.
4. No standalone data dictionary beyond the entity catalog + migration
   files + per-phase model/registry docs.
5. No hosted demo, no screenshots of a deployed instance (no deployment
   exists); dashboard behaviour is specified by the Phase 23/26/27/28/29
   Playwright suites, not by deployment evidence.
