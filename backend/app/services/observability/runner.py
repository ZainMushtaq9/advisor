"""Phase 27 observability runner: read stored rows, measure SLOs,
snapshot source health, queue exceptions, record incidents, and
probe performance.

Dry-run default: computes everything and writes nothing.
--commit: upserts SLO definitions and incidents (by key),
inserts the run + measurements + source health + exceptions +
performance, and commits once; a failure rolls back instead of
storing a partial run. A second --commit with the same run_id
writes nothing (idempotency: the run row is the guard).

The runner never writes a business row, never promotes a
status, never collects new data, and never executes anything:
it reads stored rows and writes observability records only.
Company identity is resolved by ticker everywhere (surrogate
ids shift across fresh imports — see Phase 23 repair).

Exception severity map (unmet SLO -> queue severity):
- drift_difference_count: high (a count moved without a
  recorded reason until explained).
- previous_close_completeness, price_coverage_latest_day,
  price_session_gap_weekdays: medium (analysis blocked, data
  still present and honestly labelled).
- news_company_coverage and every other unmet SLO: low.
Known states are queued as info, not failures: paused
collection jobs (Terms gate) and HBL pending (PDF obtained,
extraction in progress under a separate coordinator) are facts
to track, not alarms to hide.
"""

from __future__ import annotations

from app.models.observability import (
    ObservabilityException,
    ObservabilityIncident,
    ObservabilityRun,
    PerformanceBaseline,
    SloDefinition,
    SloMeasurement,
    SourceHealth,
)
from app.services.market_data.validation import karachi_today
from app.services.observability import performance as perf_lib
from app.services.observability import slos as slo_lib
from app.services.observability import source_health as health_lib

DEFAULT_RUN_ID = "phase27-observability-2026-11-05"

_EXCEPTION_SEVERITY: dict[str, str] = {
    "drift_difference_count": "high",
    "previous_close_completeness": "medium",
    "price_coverage_latest_day": "medium",
    "price_session_gap_weekdays": "medium",
}

# Historical incidents, recorded once (upsert by key) with their
# evidence. Resolved means recovered with evidence, not rewritten
# as if nothing happened.
INCIDENTS: list[dict] = [
    {
        "incident_key": "incident_vm_replacement_6",
        "severity": "sev3",
        "title": "VM replacement #6 during Phase 25 (2026-11-05)",
        "evidence": {
            "recovery": "PostgreSQL reinstalled, backup 2026-11-04T1230-PKT "
            "restored and manifest-verified, phases re-run in order.",
            "divergence": "RAG benchmark results 6, not 18: r1/r2 runs of "
            "superseded code could not be reproduced and were NOT "
            "fabricated. All other recorded counts reproduced exactly.",
        },
        "runbook_ref": "docs/phase-27/incident_playbooks.md#vm-replacement",
        "status": "resolved",
        "resolution_note": (
            "Recovery completed during Phase 25; full detail in "
            "docs/phase-25/run_report.md on the phase-25-automation branch."
        ),
    },
    {
        "incident_key": "incident_vm_replacement_5",
        "severity": "sev3",
        "title": "VM replacement #5 before Phase 22 (2026-11-05)",
        "evidence": {
            "recovery": "PostgreSQL reinstalled, backup restored, "
            "Phases 4-21 re-run deterministically; all 26 recorded "
            "end-of-Phase-21 counts matched exactly.",
            "finding": "Surrogate company ids shifted across the fresh "
            "import (HUBC 289 -> 759); Phase 23 repaired Phase 8/9/10 "
            "configs to ticker keys (commit a5077e0).",
        },
        "runbook_ref": "docs/phase-27/incident_playbooks.md#vm-replacement",
        "status": "resolved",
        "resolution_note": (
            "Recovery completed before Phase 22; ticker-keying repair landed in Phase 23."
        ),
    },
    {
        "incident_key": "incident_push_disconnect_phase26",
        "severity": "sev4",
        "title": "Phase 26 push failed on network disconnect, retry succeeded",
        "evidence": {
            "failure": "First push attempt: remote end hung up unexpectedly.",
            "recovery": "Retry succeeded; ls-remote confirms branch at b6f007c.",
        },
        "runbook_ref": "docs/phase-27/incident_playbooks.md#push-failure",
        "status": "resolved",
        "resolution_note": "No commit was in doubt; remote SHA verified after retry.",
    },
]


def _exceptions_for_measurements(measurements: list[dict]) -> list[dict]:
    out: list[dict] = []
    for m in measurements:
        if m["status"] != "unmet":
            continue
        out.append(
            {
                "exception_key": f"slo_unmet_{m['slo_key']}",
                "severity": _EXCEPTION_SEVERITY.get(m["slo_key"], "low"),
                "title": f"SLO unmet: {m['slo_key']}",
                "evidence": {
                    "value": str(m["value"]) if m["value"] is not None else None,
                    "reason": m["reason"],
                },
                "status": "open",
                "resolution_note": None,
            }
        )
    return out


def _known_state_exceptions() -> list[dict]:
    # HBL re-run batch: the known_hbl_pending exception is
    # RESOLVED and removed from the seed list. Its premise
    # (HBL statements not yet loaded) ended: the CY2025 report
    # was extracted (30 statements, 800 line items) and Phases
    # 8-22 re-ran for HBL (dossier, earnings update, valuation
    # report all DRAFT; chain measured in the new acceptance
    # run). The Phase 27 run's exception row stays in the
    # database as history (run-scoped rows are never edited).
    return [
        {
            "exception_key": "known_collection_jobs_paused",
            "severity": "info",
            "title": "3 collection jobs paused (Terms gate)",
            "evidence": {
                "reason": "No new PSX collection without written permission "
                "evidence; collection handlers are explicit stubs that "
                "dead-letter if ever dispatched.",
                "jobs": ["market_post_close", "filing_check", "macro_release_check"],
            },
            "status": "open",
            "resolution_note": None,
        },
    ]


def observe(session, run_id: str = DEFAULT_RUN_ID, commit: bool = False) -> dict:
    """Run one observability pass. Returns the summary dict."""
    today = karachi_today()
    measurements = slo_lib.measure_slos(session, run_date=today)
    health = health_lib.source_health(session, run_date=today)
    exceptions = _exceptions_for_measurements(measurements) + _known_state_exceptions()
    probes = perf_lib.measure_performance(session)

    met = sum(1 for m in measurements if m["status"] == "met")
    unmet = sum(1 for m in measurements if m["status"] == "unmet")
    not_evaluable = sum(1 for m in measurements if m["status"] == "not_evaluable")
    stale = [h["source_key"] for h in health if h["status"] == "stale"]
    unknown = [h["source_key"] for h in health if h["status"] == "unknown"]

    summary = {
        "run_id": run_id,
        "run_date": str(today),
        "slos_total": len(measurements),
        "slos_met": met,
        "slos_unmet": unmet,
        "slos_not_evaluable": not_evaluable,
        "sources_total": len(health),
        "sources_stale": stale,
        "sources_unknown": unknown,
        "exceptions_total": len(exceptions),
        "exceptions_open": sum(1 for e in exceptions if e["status"] == "open"),
        "incidents_total": len(INCIDENTS),
        "incidents_open": sum(1 for i in INCIDENTS if i["status"] == "open"),
        "performance_probes": len(probes),
        "committed": False,
    }

    existing = session.query(ObservabilityRun).filter_by(run_id=run_id).first()
    if existing is not None:
        summary["committed"] = False
        summary["skipped_existing"] = True
        return summary

    if not commit:
        summary["would_write"] = {
            "measurements": len(measurements),
            "source_health": len(health),
            "exceptions": len(exceptions),
            "performance": len(probes),
        }
        return summary

    for definition in slo_lib.SLO_DEFINITIONS:
        row = session.query(SloDefinition).filter_by(slo_key=definition["slo_key"]).first()
        if row is None:
            session.add(SloDefinition(**definition))
    for incident in INCIDENTS:
        row = (
            session.query(ObservabilityIncident)
            .filter_by(incident_key=incident["incident_key"])
            .first()
        )
        if row is None:
            session.add(ObservabilityIncident(**incident))
    session.add(ObservabilityRun(run_id=run_id, kind="full", status="completed", summary=summary))
    for m in measurements:
        session.add(SloMeasurement(run_id=run_id, **m))
    for h in health:
        session.add(SourceHealth(run_id=run_id, **h))
    for e in exceptions:
        session.add(ObservabilityException(run_id=run_id, **e))
    for p in probes:
        session.add(PerformanceBaseline(run_id=run_id, **p))
    session.commit()
    summary["committed"] = True
    return summary
