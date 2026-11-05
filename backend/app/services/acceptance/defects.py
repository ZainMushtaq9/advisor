"""Phase 29 defect register (severity-ranked).

Severity rules: critical = data corruption, security breach, or
execution risk; high = a wrong financial output or a broken critical
workflow; medium = a misstated metric, a blocked workflow with a
documented workaround, or a pre-distribution review item; low = an
accepted limitation with no wrong output.

Lifecycle: open = has an exact fix; accepted = documented and
consciously deferred with a stated trigger; fixed = fixed in this
run with regression tests. ``accepted`` is not a silent pass.

D-05 is MEASURED, not asserted: resolve_d05_status() reads the live
census and decision rows. The stale artifacts arose when recovery
#6 re-ran decisions and reports from an intermediate news state; a
later clean re-derivation in the correct order (news fixed before
decisions and reports) resolves them legitimately — that is a
rebuild from source after a total loss, not a hand-edit of stored
rows, and the mechanism is recorded in the run report.
"""

from __future__ import annotations

from sqlalchemy import text

DEFECTS: list[dict] = [
    {
        "defect_key": "D-01",
        "severity": "medium",
        "status": "accepted",
        "title": "Terms gate: collection jobs paused, GEM/Non-Compliant missing",
        "impact": "Full-470 VERIFIED blocked; PSX announcement collection "
        "blocked; free-float data unavailable; more trading days "
        "blocked.",
        "unblocker": "Written PSX permission evidence (user-owned). "
        "Do not claim clearance without it.",
    },
    {
        "defect_key": "D-02",
        "severity": "medium",
        "status": "accepted",
        "title": "Single trading day (2026-11-03)",
        "impact": "Technical values, forecasts, backtests, and series "
        "risk metrics are NOT_CALCULABLE; 4 of 14 SLOs unmet.",
        "unblocker": "More trading days of price data (Terms-gated). "
        "2 closes unlock returns; 5 unlock SMA(5); 11 unlock naive "
        "forecast intervals; 30 unlock volatility/beta/Sharpe/AR(1); "
        "251 unlock VaR/ES.",
    },
    {
        "defect_key": "D-03",
        "severity": "medium",
        "status": "accepted",
        "title": "HBL Phases 8+ re-runs pending",
        "impact": "HBL statements are loaded (30 statements, 800 line "
        "items) but no fundamentals, valuations, "
        "decision-with-evidence, or reports exist for HBL; the "
        "HBL chain is BLOCKED.",
        "unblocker": "Post-Phase-30 HBL re-run batch, starting from a "
        "branch containing both the phase lineage and the "
        "phase-07-hbl-extraction code. Banking rule: Phase 9 "
        "must use the bank residual-income model for HBL.",
    },
    {
        "defect_key": "D-04",
        "severity": "medium",
        "status": "open",
        "title": "Surrogate-id traps: macro sector ids, news publication-date maps",
        "impact": "Fresh imports shift surrogate ids; the macro seed "
        "and the news seed still key by pre-replacement ids. "
        "Workaround documented (temporary patch + revert + "
        "re-run); no committed code changed on their account.",
        "unblocker": "Permanent name-based sector resolution and "
        "ticker-based news publication-date mapping, with "
        "fixture tests. Fix only if a phase brief covers it.",
    },
    {
        "defect_key": "D-05",
        "severity": "medium",
        "status": "open",
        "title": "Stale downstream artifacts from recovery #6 intermediate news state",
        "impact": "One report figure (event_brief news:HUBC:earning, "
        "event_date) was insufficient_inputs while its export "
        "showed computed; HUBC/OGDC decision snapshots recorded "
        "NULL news dates, so scored_dimensions were 5/7 instead "
        "of 6/7. Totals, conclusions, confidence, and "
        "user-facing values were unaffected.",
        "unblocker": "Re-run the decision engine and regenerate the one "
        "event brief as part of the post-Phase-30 HBL re-run "
        "batch — or, after a total loss, a clean re-derivation "
        "in the correct order (news fixed before decisions and "
        "reports). Never hand-edit the stored rows.",
    },
    {
        "defect_key": "D-06",
        "severity": "low",
        "status": "accepted",
        "title": "Vector retrieval registered but not implemented",
        "impact": "RAG retrieval is deterministic full-text only; no "
        "embedding is computed, stored, or claimed.",
        "unblocker": "A verified local embedding model.",
    },
    {
        "defect_key": "D-07",
        "severity": "low",
        "status": "accepted",
        "title": "No live auth accounts; enforced mode fail-closed",
        "impact": "Enforced mode returns 401 until an admin account is "
        "created; the dashboard calls public GET APIs only.",
        "unblocker": "Parent/user decision to create the first live admin "
        "account (CLI-only, never in this audit run).",
    },
    {
        "defect_key": "D-08",
        "severity": "low",
        "status": "accepted",
        "title": "4 of 14 SLOs unmet (data limitations)",
        "impact": "Price coverage, session gap, previous-close "
        "completeness, and news coverage are below target — "
        "all Terms-gated data limitations, not code defects.",
        "unblocker": "Written PSX permission evidence + more trading days.",
    },
    {
        "defect_key": "D-09",
        "severity": "low",
        "status": "accepted",
        "title": "No persistent backup-encryption key; no service install; no host cron",
        "impact": "Backups are plaintext by default (GPG optional, "
        "key not persisted); services start manually via "
        "ops/start.sh; jobs run operator-invoked.",
        "unblocker": "Operator decision + documented install/cron steps "
        "(Phase 28 operations handover).",
    },
    {
        "defect_key": "D-10",
        "severity": "low",
        "status": "accepted",
        "title": "No frontend token support for enforced mode",
        "impact": "The dashboard cannot call enforced-mode APIs; it calls public GET APIs only.",
        "unblocker": "Needed only if enforced mode is ever required for the dashboard.",
    },
    {
        "defect_key": "D-11",
        "severity": "low",
        "status": "accepted",
        "title": "RAG benchmark history partial (r3 only)",
        "impact": "rag_benchmark_results holds 6 rows (r3, 6/6); r1/r2 "
        "runs of superseded retrieval code were not reproduced "
        "after VM replacement #6 and were not fabricated.",
        "unblocker": "None — the honest recorded state. Do not re-fabricate.",
    },
    {
        "defect_key": "D-12",
        "severity": "low",
        "status": "open",
        "title": "Token-gated report approval (Phase 24 candidate)",
        "impact": "Report approval is an explicit CLI transition only; it is not token-gated.",
        "unblocker": "A phase brief that covers it (belongs to no brief so far).",
    },
    {
        "defect_key": "D-13",
        "severity": "low",
        "status": "fixed",
        "title": "PyMuPDF/pdfplumber unpinned and unrecorded",
        "impact": "Two extraction dependencies were used by Phase 7 "
        "but absent from backend/requirements.txt (unpinned) "
        "and backend/LICENCES.md (Phase 1 gates G-02/G-04 "
        "require recording before use).",
        "unblocker": "Fixed in this run: pins added to requirements.txt, "
        "licence rows added to LICENCES.md, regression test "
        "added (test_acceptance_phase29.py).",
    },
    {
        "defect_key": "D-14",
        "severity": "medium",
        "status": "accepted",
        "title": "PyMuPDF AGPL-3.0-or-commercial: review before public hosted distribution",
        "impact": "No current violation: the project is local research, "
        "not a distributed network service. The licence "
        "becomes a blocker only at public hosted deployment "
        "or redistribution.",
        "unblocker": "Licence review with the stated trigger before any "
        "public hosted deployment or redistribution.",
    },
]


def resolve_d05_status(session) -> tuple[str, str]:
    """Measure D-05 against the live database.

    Returns (status, evidence): "fixed" only when the report-figure
    census is exactly 335/199/7 AND HUBC/OGDC scored_dimensions are
    both 6; otherwise "open" with the measured values.
    """
    census = dict(
        session.execute(
            text(
                "SELECT computation_status, COUNT(*) FROM report_figures "
                "GROUP BY computation_status"
            )
        ).fetchall()
    )
    scored = dict(
        session.execute(
            text(
                "SELECT s.ticker, d.scored_dimensions FROM decisions d "
                "JOIN securities s ON s.id = d.security_id"
            )
        ).fetchall()
    )
    census_ok = (
        census.get("computed") == 335
        and census.get("insufficient_inputs") == 199
        and census.get("not_applicable") == 7
    )
    scored_ok = scored.get("HUBC") == 6 and scored.get("OGDC") == 6
    evidence = (
        f"census computed={census.get('computed')} "
        f"insufficient_inputs={census.get('insufficient_inputs')} "
        f"not_applicable={census.get('not_applicable')}; "
        f"HUBC scored={scored.get('HUBC')}, OGDC scored={scored.get('OGDC')}"
    )
    if census_ok and scored_ok:
        return "fixed", evidence + " — resolved by clean re-derivation."
    return "open", evidence


def build_register(session):
    """Return the defect register with D-05 status measured live."""
    status, evidence = resolve_d05_status(session)
    register = []
    for defect in DEFECTS:
        entry = dict(defect)
        if entry["defect_key"] == "D-05":
            entry["status"] = status
            entry["impact"] = entry["impact"] + " Measured now: " + evidence
        register.append(entry)
    return register
