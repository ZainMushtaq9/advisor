"""Phase 29 acceptance runner: dry-run default, --commit writes one
run in a single transaction (and rolls back on failure instead of
storing a partial run).

Idempotency: the run row is the guard. A second --commit with the
same run_id writes nothing (0 created, 0 scenarios, 0
recomputations, 0 defects).

The runner never writes a business row, never promotes a status,
never collects new data, and never executes anything. It reads
stored rows, recomputes from them independently, runs worktree
scans, evaluates the gate, and — only on --commit — stores the
audit record itself.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.acceptance import (
    AcceptanceDefect,
    AcceptanceRecomputation,
    AcceptanceRun,
    AcceptanceScenario,
)
from app.services.acceptance.audits import run_audits
from app.services.acceptance.defects import build_register
from app.services.acceptance.gate import decide_verdict, evaluate_gate
from app.services.acceptance.recompute import run_recomputations
from app.services.acceptance.scenarios import run_scenarios

# This project runs on PKT (Asia/Karachi) dates throughout (Phase 25
# precedent: a UTC date would mislabel same-day artifacts).
PKT = ZoneInfo("Asia/Karachi")

DEFAULT_RUN_ID = "phase29-acceptance-2026-11-05"


def accept(session, run_id: str = DEFAULT_RUN_ID, commit: bool = False):
    """Run the full acceptance evaluation.

    Returns a report dict. On commit=True the run, scenarios,
    recomputations, and defects are inserted in one transaction;
    on a second commit with the same run_id, nothing is written.
    """
    existing = session.query(AcceptanceRun).filter_by(run_id=run_id).first()
    if existing is not None:
        return {
            "run_id": run_id,
            "committed": False,
            "already_exists": True,
            "verdict": existing.verdict,
            "scenarios_created": 0,
            "recomputations_created": 0,
            "defects_created": 0,
        }

    scenarios = run_scenarios(session)
    recomputations = run_recomputations(session)
    audits = run_audits(session)
    defects = build_register(session)
    gate = evaluate_gate(scenarios, recomputations, audits, defects)
    verdict = decide_verdict(gate, scenarios)

    run_date = datetime.now(PKT).date()
    report = {
        "run_id": run_id,
        "run_date": str(run_date),
        "verdict": verdict,
        "gate": gate,
        "audits": audits,
        "scenarios": scenarios,
        "recomputations": recomputations,
        "defects": defects,
        "committed": False,
        "already_exists": False,
        "scenarios_created": 0,
        "recomputations_created": 0,
        "defects_created": 0,
    }

    if not commit:
        return report

    try:
        session.add(
            AcceptanceRun(
                run_id=run_id,
                run_date=run_date,
                verdict=verdict,
                gate_evaluation={"gate": gate, "audits": audits},
            )
        )
        # Flush the run row FIRST, explicitly. The child tables
        # reference acceptance_runs.run_id (a unique column, not the
        # primary key) and no ORM relationships are defined, so the
        # unit of work cannot be trusted to order the inserts:
        # PostgreSQL rejects the children otherwise (SQLite, which
        # does not enforce foreign keys by default, hides the bug).
        session.flush()
        for item in scenarios:
            session.add(
                AcceptanceScenario(
                    run_id=run_id,
                    scenario_key=item["scenario_key"],
                    case_name=item["case_name"],
                    outcome=item["outcome"],
                    evidence=item["evidence"],
                    reason=item["reason"],
                )
            )
        for item in recomputations:
            session.add(
                AcceptanceRecomputation(
                    run_id=run_id,
                    check_key=item["check_key"],
                    claimed_value=item["claimed_value"],
                    recomputed_value=item["recomputed_value"],
                    matches=item["matches"],
                    tolerance=item["tolerance"],
                    method=item["method"],
                )
            )
        for item in defects:
            session.add(
                AcceptanceDefect(
                    run_id=run_id,
                    defect_key=item["defect_key"],
                    severity=item["severity"],
                    status=item["status"],
                    title=item["title"],
                    impact=item["impact"],
                    unblocker=item["unblocker"],
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise

    report["committed"] = True
    report["scenarios_created"] = len(scenarios)
    report["recomputations_created"] = len(recomputations)
    report["defects_created"] = len(defects)
    return report
