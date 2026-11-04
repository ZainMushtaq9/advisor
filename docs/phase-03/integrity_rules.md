# Phase 3 — Integrity Rules

These rules are enforced by schema, trigger, helper or test — not
merely documented. Each rule names its enforcement so a later
phase can check it rather than trust it.

| # | Rule | Enforcement |
|---|---|---|
| 1 | Never overwrite observations or published/revised statements | Triggers (23, migrations 20261104_0003 + 20261104_0004): 12 append-only tables reject UPDATE/DELETE; 8 versioned tables allow only is_current changes; data_quality_reports allows only resolution changes; live_quotes only is_latest; agent_executions only status/ended_at (all tested) |
| 2 | Never mark unverified as verified without evidence | `upgrade_quality_status` raises without evidence for ANY transition into VERIFIED/PARTIALLY_VERIFIED (audit M1 fix); quality_status defaults UNVERIFIED; CHECK vocabulary on 22 tables |
| 3 | Never delete provenance | Provenance columns are NOT NULL where the design requires; data_source_id SET NULL keeps source_key on the row; audit_logs append-only |
| 4 | Never silently merge conflicting sources | Grain includes source; conflicts are two CONFLICTED rows; `values_conflict` helper reports, never picks |
| 5 | Missing is never zero | NULL stored, MISSING status, tested (close_price/volume NULL, never 0) |
| 6 | Collection time is never observation time | Separate source_timestamp / collected_at columns, documented in every provenance doc |
| 7 | OHLC must be internally consistent | `validate_ohlc` helper + tests (high/low bounds, negatives, missing) |
| 8 | Balance sheet must balance (within rounding) | `check_balance_sheet` helper, tolerance documented (0.01) |
| 9 | Cash flow must reconcile (within rounding) | `check_cash_flow` helper, tolerance documented |
| 10 | A failed validation never silently rejects a whole document | Helpers return findings; field-level and document-level quality statuses are separate |
| 11 | Synthetic/test data is TEST ONLY, separate from production | Tests run in rolled-back transactions or temp dirs; production tables hold zero business rows at phase end |
| 12 | No secrets in logs, code, commits or docs | Column inspection test (no broker/api_key/password/secret columns); git staging check before commit; fake test secret from Phase 2 is a test fixture only |
| 13 | No real trades, no broker path | No brokerage columns, no order table, paper portfolios only |
| 14 | No fabricated data in dashboards | No Phase 3 frontend data pages exist; Phase 2 shells remain empty-state only |

## Rules that are documented but NOT yet enforced

- Company/security lifecycle status vocabulary (not CHECK-
  constrained; Phase 4 must verify the vocabulary before
  constraining it).
- Partitioning, PITR/WAL archiving, and query-time budgets at
  real scale (Phase 5 measurements, not Phase 3 claims).
