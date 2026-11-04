"""Field-scoped SECP LEAP evidence: pure validation and mapping.

Implements docs/phase-04/field_scoped_leap_promotion_procedure.md.
Pure functions only: no database, no network, no status changes.
The loader (scripts/load_leap_evidence.py) owns all database writes,
and it never calls apply_verification_rules and never writes
company_identifiers.

Field scope enforced here:
- legal name: AGREE / DISAGREE / NOT_FOUND under normalize_name.
- CUIN: recorded only, never an agreement, never an identifier row.
- LEAP INCORPORATED badge: observed only, never DPS listing status.
- sector / ticker: not verifiable from LEAP, never emitted.
"""

from __future__ import annotations

import re
from datetime import datetime

from app.services.registry.normalization import normalize_name

SOURCE_KEY = "secp_leap"
NOT_FOUND_KEY = "NOT_FOUND"

_CUIN_RE = re.compile(r"^\d{7}$")


def parse_cuin(value: object) -> str:
    """Validate a LEAP CUIN: exactly 7 digits, returned unchanged."""
    if not isinstance(value, str) or not _CUIN_RE.match(value):
        raise ValueError(f"CUIN must be exactly 7 digits, got {value!r}")
    return value


def parse_leap_date(value: object) -> str:
    """Validate a LEAP incorporation date (DD-MM-YYYY as shown).

    The garbled duplicate-row years (e.g. 3993) are rejected here:
    only real calendar dates pass. Returns the value unchanged.
    """
    if not isinstance(value, str):
        raise ValueError(f"LEAP date must be a string, got {value!r}")
    try:
        datetime.strptime(value, "%d-%m-%Y")
    except ValueError as exc:
        raise ValueError(f"LEAP date must be DD-MM-YYYY, got {value!r}") from exc
    return value


def build_evidence_note(obs: dict) -> str:
    """Build the structured evidence note for one observation.

    The note always carries the explicit non-claims, so a reader can
    never mistake a LEAP row for a whole-record verification.
    """
    lines = [
        f"LEAP queries tried (in order): {'; '.join(obs['query_wordings'])}",
        f"Query that found the row: {obs.get('query_that_found') or 'none'}",
    ]
    inc = obs.get("incorporated_row")
    if inc:
        lines.append(
            "LEAP INCORPORATED row: name={name!r}, CUIN={cuin}, "
            "incorporation_date={date}, CRO={cro}".format(
                name=inc["name"],
                cuin=inc["cuin"],
                date=inc["incorporation_date"],
                cro=inc["cro_city"],
            )
        )
    org = obs.get("organization_row")
    if org:
        lines.append(
            "LEAP duplicate organization row (not the observation): "
            f"name={org.get('name')!r}, displayed_date={org.get('displayed_date')!r}"
        )
    if obs.get("other_candidates"):
        lines.append(f"Other candidates shown: {'; '.join(obs['other_candidates'])}")
    lines.append(f"Outcome: {obs['outcome']}")
    if obs.get("notes"):
        lines.append(f"Notes: {obs['notes']}")
    lines.append(
        "Non-claims: CUIN recorded, not agreed; LEAP INCORPORATED is "
        "not DPS listing status; sector and ticker are not verifiable "
        "from LEAP; this row changes no status."
    )
    return "\n".join(lines)


def validate_observation(obs: dict, registry_legal_name: str) -> list[str]:
    """Validate one browser observation. Returns a list of errors.

    An empty list means the observation is internally consistent and
    its outcome follows from its rows under normalize_name.
    """
    errors: list[str] = []
    outcome = obs.get("outcome")
    if outcome not in ("AGREE", "DISAGREE", "NOT_FOUND"):
        errors.append(f"outcome must be AGREE, DISAGREE or NOT_FOUND, got {outcome!r}")
        return errors
    wordings = obs.get("query_wordings")
    if (
        not isinstance(wordings, list)
        or not wordings
        or not all(isinstance(w, str) and w.strip() for w in wordings)
    ):
        errors.append("query_wordings must be a non-empty list of strings")
    inc = obs.get("incorporated_row")
    if outcome in ("AGREE", "DISAGREE"):
        if not isinstance(inc, dict):
            errors.append(f"outcome {outcome} requires an incorporated_row")
            return errors
        try:
            cuin = parse_cuin(inc.get("cuin"))
        except ValueError as exc:
            errors.append(str(exc))
            cuin = None
        try:
            parse_leap_date(inc.get("incorporation_date"))
        except ValueError as exc:
            errors.append(str(exc))
        if not inc.get("name") or not isinstance(inc.get("name"), str):
            errors.append("incorporated_row.name must be a non-empty string")
        if not inc.get("cro_city") or not isinstance(inc.get("cro_city"), str):
            errors.append("incorporated_row.cro_city must be a non-empty string")
        if inc and isinstance(inc.get("name"), str) and inc["name"].strip():
            try:
                agrees = normalize_name(inc["name"]) == normalize_name(registry_legal_name)
            except (ValueError, TypeError) as exc:
                errors.append(f"name normalization failed: {exc}")
                agrees = None
            if agrees is True and outcome != "AGREE":
                errors.append(
                    "incorporated_row name normalizes equal to the registry "
                    "name, so outcome must be AGREE"
                )
            if agrees is False and outcome != "DISAGREE":
                errors.append(
                    "incorporated_row name differs from the registry name "
                    "under normalization, so outcome must be DISAGREE"
                )
        if outcome == "AGREE" and cuin is None:
            errors.append("AGREE requires a valid CUIN")
    else:  # NOT_FOUND
        if inc is not None:
            errors.append("NOT_FOUND must not carry an incorporated_row")
    return errors


def observation_to_evidence_row(obs: dict) -> dict:
    """Map a validated observation to a registry_evidence row dict.

    observed_sector is always None: LEAP returns no sector.
    source_key is deliberately 'secp_leap', not the OFFICIAL_SOURCES
    key 'secp', so the current promotion code can never promote a
    record from these rows alone.
    """
    inc = obs.get("incorporated_row")
    return {
        "entity_type": "company",
        "entity_id": obs["company_id"],
        "source_key": SOURCE_KEY,
        "source_record_key": inc["cuin"] if inc else NOT_FOUND_KEY,
        "observed_name": inc["name"] if inc else None,
        "observed_sector": None,
        "evidence_note": build_evidence_note(obs),
    }
