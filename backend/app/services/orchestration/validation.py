"""Phase 18 deterministic authority and hallucination controls.

The core guardrail: an agent output can never override a
verified numeric calculation. Two checks enforce it:

1. Deterministic authority: a numeric claim (ticker + metric +
   claimed value) is compared against the deterministic service
   value. Equal -> ACCEPT. Different -> QUARANTINE, and the
   stored row is left untouched. The runner proves this live by
   re-reading the stored row after the injection probe.
2. Hallucination: a numeric claim with no evidence reference
   (no stored row, document, or publication it cites) is
   quarantined as hallucinated, even if it happens to match a
   stored value — a correct guess without evidence is still not
   evidence.

Neither check writes anything: validation returns a verdict,
and the runner records it. Values are Decimal-compared as
strings to avoid float rounding disputes.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def _to_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def validate_numeric_claim(
    claimed_value: str, service_value: str | None, evidence_ref: str | None
) -> dict:
    """Validate one agent numeric claim against deterministic truth.

    Verdicts:
    - ACCEPT: claim equals the service value and cites evidence.
    - QUARANTINE_MISMATCH: claim differs from the service value.
    - QUARANTINE_NO_EVIDENCE: claim cites no evidence reference.
    - QUARANTINE_NO_SERVICE_VALUE: no deterministic value exists
      to check against (the claim is unverifiable, not accepted).
    The stored value is never modified by any verdict.
    """
    if not evidence_ref:
        return {
            "verdict": "QUARANTINE_NO_EVIDENCE",
            "reason": "numeric claim cites no evidence reference",
        }
    if service_value is None:
        return {
            "verdict": "QUARANTINE_NO_SERVICE_VALUE",
            "reason": "no deterministic service value exists for this claim",
        }
    claimed = _to_decimal(claimed_value)
    service = _to_decimal(service_value)
    if claimed is None or service is None:
        return {
            "verdict": "QUARANTINE_NO_SERVICE_VALUE",
            "reason": "claim or service value is not numeric",
        }
    if claimed == service:
        return {"verdict": "ACCEPT", "reason": "claim equals deterministic service value"}
    return {
        "verdict": "QUARANTINE_MISMATCH",
        "reason": f"claim {claimed} differs from deterministic value {service}",
    }


def validate_claim_batch(claims: list[dict], service_values: dict[str, str | None]) -> dict:
    """Validate a batch of claims; any quarantine quarantines the batch.

    ``claims`` items carry ticker, metric, claimed_value, and
    evidence_ref. ``service_values`` maps "TICKER:metric" to the
    deterministic value or None. Returns per-claim verdicts and
    an overall verdict (ACCEPT only if every claim accepts).
    """
    verdicts = []
    for claim in claims:
        key = f"{claim['ticker']}:{claim['metric']}"
        verdict = validate_numeric_claim(
            claim["claimed_value"], service_values.get(key), claim.get("evidence_ref")
        )
        verdicts.append({"claim": claim, **verdict})
    overall = "ACCEPT" if all(v["verdict"] == "ACCEPT" for v in verdicts) else "QUARANTINE"
    return {"verdicts": verdicts, "overall": overall}
