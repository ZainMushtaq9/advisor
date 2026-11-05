# Phase 29 — Defect register

Run: `phase29-acceptance-2026-11-05`. Fourteen defects, 0 critical,
0 high, 6 medium, 8 low. Statuses: 2 open, 2 fixed, 10 accepted.
"Accepted" means the limitation is understood, documented, and has
an exact unblocker — not that it is resolved. No defect was closed
by rewording.

| Key | Severity | Status | Title | Unblocker |
|---|---|---|---|---|
| D-01 | medium | accepted | Terms gate: collection jobs paused, GEM/Non-Compliant missing | Written PSX permission evidence (user-owned). Do not claim clearance without it. |
| D-02 | medium | accepted | Single trading day (2026-11-03) | More trading days of price data (Terms-gated). 2 closes unlock returns; 5 unlock SMA(5); 11 unlock naive forecast intervals; 30 unlock volatility/beta/Sharpe/AR(1); 251 unlock VaR/ES. |
| D-03 | medium | accepted | HBL Phases 8+ re-runs pending | Post-Phase-30 HBL re-run batch, starting from a branch containing both the phase lineage and the phase-07-hbl-extraction code. Banking rule: Phase 9 must use the bank residual-income model for HBL. |
| D-04 | medium | open | Surrogate-id traps: macro sector ids, news publication-date maps | Permanent name-based sector resolution and ticker-based news publication-date mapping, with fixture tests. Fix only if a phase brief covers it. |
| D-05 | medium | fixed | Stale downstream artifacts from recovery #6 intermediate news state | Resolved by clean re-derivation in recovery #7 (news fixed before decisions and reports). Measured: census 335/199/7; HUBC scored 6/7, OGDC scored 6/7. Never hand-edit stored rows. |
| D-06 | low | accepted | Vector retrieval registered but not implemented | A verified local embedding model. |
| D-07 | low | accepted | No live auth accounts; enforced mode fail-closed | Parent/user decision to create the first live admin account (CLI-only, never in this audit run). |
| D-08 | low | accepted | 4 of 14 SLOs unmet (data limitations) | Written PSX permission evidence + more trading days. |
| D-09 | low | accepted | No persistent backup-encryption key; no service install; no host cron | Operator decision + documented install/cron steps (Phase 28 operations handover). |
| D-10 | low | accepted | No frontend token support for enforced mode | Needed only if enforced mode is ever required for the dashboard. |
| D-11 | low | accepted | RAG benchmark history partial (r3 only) | None — the honest recorded state. Do not re-fabricate r1/r2. |
| D-12 | low | open | Token-gated report approval (Phase 24 candidate) | A phase brief that covers it (belongs to no brief so far). |
| D-13 | low | fixed | PyMuPDF/pdfplumber unpinned and unrecorded | Fixed in this run: pins added to requirements.txt, licence rows added to LICENCES.md, regression test added. |
| D-14 | medium | accepted | PyMuPDF AGPL-3.0-or-commercial: review before public hosted distribution | Licence review with the stated trigger before any public hosted deployment or redistribution. No current violation. |

## Fixed in this run, with evidence

- **D-05.** The stale artifacts arose in recovery #6: decisions were
  re-run before the news fix (links created 23:41:01), and report
  figures were regenerated mid-recovery but not reverted, leaving
  one stale event_date figure (census 334/200/7) and HUBC/OGDC
  decision snapshots at scored 5/7. Recovery #7 re-derived
  everything in the correct order (news fixed before decisions and
  reports), restoring the original Phase 15/22 values. The runner
  measures this, it does not assert it: `resolve_d05_status()`
  returns "fixed" only when the census is exactly 335/199/7 AND
  HUBC and OGDC are both scored 6/7. The committed run measured
  "fixed". The history is preserved here because the recovery
  recipe must record how it arose and how it was resolved.
- **D-13.** PyMuPDF 2.1 and pdfplumber 0.11.10 were used by Phase 7
  extraction but absent from `backend/requirements.txt` and
  `backend/LICENCES.md` (which still carried the Phase 2 note that
  PyMuPDF was deliberately NOT included, and that a later phase
  adding one must record its licence first, per Phase 1 gates
  G-02/G-04). Pins and licence rows were added, the Phase 28
  dependency-gate allowlist was extended, and a regression test
  pins the rows. Documentation and pinning only — no behaviour
  changed.
