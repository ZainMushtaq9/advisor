"""Phase 13 computability assessment: what can be forecast, from what.

``assess`` is the single decision point the runner and the tests
share. Given a target, a horizon and the length of the target's own
series available on or before the origin, it returns the
computation status, the exact reason, and a per-method breakdown:

- 'computed' requires BOTH a point estimate AND a validated
  interval: at least one implemented method whose interval minimum
  is met (interval_min residuals exist). A point alone is never
  'computed' — that is the abstention rule, and it is why the
  production run stores zero computed forecasts even though naive
  persistence could name a point from one observation.
- 'insufficient_inputs' when the target applies but the series is
  too short for every implemented method's interval minimum (and,
  in the reason, how many observations each method still needs).
- 'not_applicable' is reserved for targets that cannot apply at all
  (no such case exists in the current registry: every target is
  defined for its scope). It is never used as a softer word for
  "data missing".

Horizon does not change the verdict: the minima are properties of
the series, not of how far ahead the forecast looks.
"""

from __future__ import annotations

from . import METHODS


def assess(target_key: str, horizon: str, series_length: int) -> dict:
    """Assess one (target, horizon) pair against a series length."""
    per_method = {}
    any_interval_ready = False
    for name, (point_min, interval_min, implemented) in METHODS.items():
        if not implemented:
            per_method[name] = {
                "status": "not_implemented",
                "reason": "Candidate method only; no validated fit exists on current data.",
            }
            continue
        if series_length >= interval_min:
            per_method[name] = {
                "status": "ready",
                "reason": f"Series length {series_length} meets interval minimum {interval_min}.",
            }
            any_interval_ready = True
        elif series_length >= point_min:
            per_method[name] = {
                "status": "point_only_abstained",
                "reason": (
                    f"Point estimate available ({series_length} >= {point_min}) "
                    f"but interval needs {interval_min} observations; "
                    f"shortfall {interval_min - series_length}. Point alone "
                    "is not a Phase 13 forecast, so abstained."
                ),
            }
        else:
            per_method[name] = {
                "status": "insufficient_inputs",
                "reason": (
                    f"Series length {series_length} below point minimum "
                    f"{point_min}; shortfall {point_min - series_length}."
                ),
            }
    if any_interval_ready:
        status = "computed"
        reason = (
            f"Series length {series_length} supports an interval-validated "
            f"forecast for {target_key} at horizon {horizon}."
        )
    else:
        status = "insufficient_inputs"
        ready_points = [
            name
            for name, detail in per_method.items()
            if detail["status"] == "point_only_abstained"
        ]
        if ready_points:
            reason = (
                f"Series length {series_length} for {target_key}: point "
                f"estimates exist ({', '.join(ready_points)}) but no method "
                "meets its interval minimum, so no forecast is stored "
                "(abstention rule). Shortest interval shortfall: "
                f"{min(METHODS[name][1] - series_length for name in ready_points)} "
                "observations."
            )
        else:
            reason = (
                f"Series length {series_length} for {target_key}: below "
                "every implemented method's point minimum; no forecast, "
                "no baseline comparison, no calibration is computable."
            )
    return {
        "target_key": target_key,
        "horizon": horizon,
        "series_length": series_length,
        "computation_status": status,
        "reason": reason,
        "per_method": per_method,
        "calibration_status": (
            "calibrated" if status == "computed" else "not_calibrated_insufficient_history"
        ),
    }
