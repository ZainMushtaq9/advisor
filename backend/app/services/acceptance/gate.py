"""Phase 29 acceptance-gate evaluation.

Five items, each met / not_met / partial, with evidence. The verdict
follows from the items — never the reverse:

- FAILED: any scenario outcome is fail, or G3 (no look-ahead or
  fabrication) is not met, or G2/G4 is not met (an open
  critical/high defect, or restricted data/secret in the public
  repo, is a release failure).
- PARTIALLY COMPLETE: no failure, but G1 is not met (the HBL chain
  is blocked pending the post-Phase-30 re-runs) and/or G5 is
  partial (human sign-off pending). This is the expected outcome.
- COMPLETE: all five items met. G5 can only be met by a recorded
  human sign-off, never by this code — so COMPLETE is not
  reachable from a CLI run alone, by design.
- BLOCKED: reserved for a run that cannot evaluate the gate at all
  (for example, the database is unreachable); the runner reports
  it, it is not computed here.
"""

from __future__ import annotations

KNOWN_RECOMPUTATION_EXCEPTIONS = {
    "report_figure_census",  # D-05: omission/staleness, not fabrication
    "decision_completeness",  # D-05: same
    "drift_vs_phase24_baseline",  # expected HBL drift, not a failure
}


def evaluate_gate(scenarios, recomputations, audits, defects):
    """Evaluate the five gate items from run results."""
    by_scenario = {s["scenario_key"]: s["outcome"] for s in scenarios}
    by_check = {r["check_key"]: r["matches"] for r in recomputations}
    audit_by_name = {a["name"]: a["status"] for a in audits}

    # G1: all critical workflows pass.
    chain_keys = [
        "chain_hubc_full",
        "chain_ogdc_full",
        "chain_nml_full",
        "chain_hbl_full",
    ]
    chain_outcomes = [by_scenario.get(k) for k in chain_keys]
    if all(o == "pass" for o in chain_outcomes):
        g1 = ("met", "All four company chains pass.")
    elif any(o == "fail" for o in chain_outcomes):
        g1 = ("not_met", f"Chain outcomes: {dict(zip(chain_keys, chain_outcomes))}.")
    else:
        # HBL re-run batch: the old else text cited D-03
        # ("blocked at statements"); the HBL chain is now
        # measured by chain_hbl_full, so a non-pass/non-fail
        # outcome is reported generically, never as D-03.
        g1 = (
            "not_met",
            "A company chain outcome is blocked or not_evaluable. "
            f"Chain outcomes: {dict(zip(chain_keys, chain_outcomes))}.",
        )

    # G2: critical/high defects resolved.
    open_severe = [
        d["defect_key"]
        for d in defects
        if d["severity"] in ("critical", "high") and d["status"] == "open"
    ]
    if not open_severe:
        g2 = ("met", "0 critical, 0 high defects open.")
    else:
        g2 = ("not_met", f"Open critical/high defects: {open_severe}.")

    # G3: no look-ahead or fabricated financial data.
    point_in_time = by_scenario.get("point_in_time")
    model_failure = by_scenario.get("model_failure")
    unexpected_mismatch = [
        key
        for key, matches in by_check.items()
        if not matches and key not in KNOWN_RECOMPUTATION_EXCEPTIONS
    ]
    if point_in_time == "pass" and model_failure == "pass" and not unexpected_mismatch:
        g3 = (
            "met",
            "Point-in-time checks pass; forecasts abstain honestly; "
            "every recomputation matches except the documented D-05 "
            "omissions and the expected HBL drift.",
        )
    else:
        g3 = (
            "not_met",
            f"point_in_time={point_in_time}, model_failure={model_failure}, "
            f"unexpected recomputation mismatches={unexpected_mismatch}.",
        )

    # G4: public repo contains no restricted dataset or secret.
    repo_audits = [
        "execution_identifiers",
        "dangerous_constructs",
        "write_routes",
        "upload_endpoints",
        "docker_invocations",
        "tracked_datasets",
        "tracked_secrets",
        "branch_tip_datasets",
        "pii_columns",
    ]
    failed_audits = [name for name in repo_audits if audit_by_name.get(name) != "pass"]
    if not failed_audits:
        g4 = (
            "met",
            "All security/licensing/privacy scans pass. Boundary: "
            "dataset/secret scans cover branch tips, not every "
            "historical commit.",
        )
    else:
        g4 = ("not_met", f"Failed scans: {failed_audits}.")

    # G5: independent auditor signs off with evidence. This code can
    # supply the evidence but never the human sign-off.
    g5 = (
        "partial",
        "Independent recomputation, scenario, and scan evidence is "
        "complete in this run; human sign-off belongs to the "
        "user/parent and is pending.",
    )

    gate = {
        "g1_critical_workflows": {"result": g1[0], "evidence": g1[1]},
        "g2_defects_resolved": {"result": g2[0], "evidence": g2[1]},
        "g3_no_fabrication": {"result": g3[0], "evidence": g3[1]},
        "g4_repo_clean": {"result": g4[0], "evidence": g4[1]},
        "g5_auditor_signoff": {"result": g5[0], "evidence": g5[1]},
    }
    return gate


def decide_verdict(gate, scenarios):
    """Decide the run verdict from the gate evaluation."""
    any_fail = any(s["outcome"] == "fail" for s in scenarios)
    if any_fail:
        return "FAILED"
    if gate["g3_no_fabrication"]["result"] != "met":
        return "FAILED"
    if gate["g2_defects_resolved"]["result"] != "met":
        return "FAILED"
    if gate["g4_repo_clean"]["result"] != "met":
        return "FAILED"
    if gate["g1_critical_workflows"]["result"] != "met":
        return "PARTIALLY COMPLETE"
    if gate["g5_auditor_signoff"]["result"] != "met":
        return "PARTIALLY COMPLETE"
    return "COMPLETE"
