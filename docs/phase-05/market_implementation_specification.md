# Phase 5 — Market-Data Implementation Specification

**Scope: 470 Main Board / Normal Counter snapshot securities only.**
Never "KSE-100", never "full-market", until a separate verified
KSE-100 membership check against this snapshot is done. KSE-100
completeness is NOT established in this phase.

## 1. What this phase implements (and what it deliberately does not)

Implemented:
- Deterministic daily-OHLCV validation, quality assignment, and
  validated-file ingestion over the Phase 3 `market_prices` schema
  (no new tables, no migrations).
- GET-only `/api/v1/market/…` endpoints with truthful empty states.
- Safe catch-up (ingest only missing dates per security/source).
- A dry-run-default CLI for operator ingestion.
- A read-only frontend `/market` page rendering only API rows.
- Source research (15 fields/source) + comparison matrix, with
  per-source legal-accessibility verdicts.

NOT implemented, by evidence, not by omission:
- No live DPS adapter, no scraper, no psx-dps/psxdata install or
  call. Live DPS adapters are BLOCKED (D-51/D-52 + PSX Terms
  automated-navigation bar); see `market_source_research.md`.
- No intraday ingestion. Intraday is OUT OF SCOPE unless legally
  accessible free intraday is verified in writing (it is not).
- No real market observation is ingested in this phase:
  production `market_prices` remains 0. The engine is complete and
  tested; the data input it waits for is a validated dated file
  supplied through an authorised route (the same pattern as the
  registry snapshot), plus written resolution of the PSX Terms
  internal-use question.

## 2. Components

| Component | Location | Responsibility |
|---|---|---|
| Validation | `backend/app/services/market_data/validation.py` | Pure deterministic row validation; stable rejection codes |
| Quality | `backend/app/services/market_data/quality.py` | Quality assignment + v1 freshness label |
| Ingestion | `backend/app/services/market_data/ingestion.py` | Validated-file ingest; idempotent; never commits (caller does) |
| Scheduler | `backend/app/services/market_data/scheduler.py` | Pure missing-date / catch-up computation |
| API | `backend/app/api/v1/endpoints/market.py` | GET-only market endpoints |
| CLI | `scripts/run_market_ingestion.py` | Operator ingestion; `--dry-run` default |
| Frontend | `frontend/app/market/` + `frontend/lib/nav.ts` | Read-only market page + nav entry |

## 3. Data rules enforced in code (not prose)

- Grain: (security_id, trading_date, bar_type="daily",
  data_source_id). Re-ingest of the same grain SKIPS, never
  overwrites (market_prices is immutable per Phase 3 triggers).
- All stored prices `is_adjusted=False` (official unadjusted).
- Provenance on every stored row: source_key, source_timestamp,
  collected_at (Asia/Karachi, tz-aware), quality_status.
- Missing sessions are reported per security, never zero-filled,
  never stored as rows.
- Conflicting sources are stored side-by-side (grain includes
  source), each flagged CONFLICTED within one run; see the
  cross-run caveat in `phase_05_independent_audit.md` (A3).
- Unknown tickers fail the whole CLI run before any write
  (exit 2); wrong CSV headers abort before any DB work.
- No LLM computes any number; no network call exists in the new
  code (verified by grep in the audit).

## 4. Branch and safety

Working branch: `phase-05-snapshot-import` (holds the import script
and gate §12 evidence). No commit is made to
`phase-05-market-data-engine`. The seed CSV is gitignored
(`.gitignore:40: *.csv`) and untracked; it is never force-added.
No push to main, no merge to main, no force-push. Paid services:
ZERO. No external account, no ToS/payment/CAPTCHA step.
