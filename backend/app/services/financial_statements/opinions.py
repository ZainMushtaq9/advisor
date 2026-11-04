"""Structured auditor-opinion records (Phase 7 remainders).

Rules:
- Source wording is preserved verbatim in ``opinion_text``; nothing
  is paraphrased into a stronger claim.
- ``opinion_type = 'none'`` records the explicit ABSENCE of an
  opinion (unaudited interim statements): firm/UDIN/text stay NULL
  and ``absence_note`` states what was checked. Never invent an
  opinion, firm, or UDIN.
- Every record is UNVERIFIED (single source, rule H1). No promotion
  in this phase.
- Loads are idempotent: a re-run with the same (company, document,
  scope, version) writes nothing new. Corrections are new versions,
  never edits (the versioned trigger enforces this).
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

PKT = ZoneInfo("Asia/Karachi")

OPINION_TYPES = ("unmodified", "qualified", "adverse", "disclaimer", "none")


def validate_opinion_record(record: dict) -> list[str]:
    """Pure validation of one opinion JSON record. Returns errors
    (empty = valid). Used by the loader and by tests; no DB needed."""
    errors = []
    for field in ("company_symbol", "opinion_scope", "opinion_type"):
        if not record.get(field):
            errors.append(f"missing {field}")
    otype = record.get("opinion_type")
    if otype and otype not in OPINION_TYPES:
        errors.append(f"unknown opinion_type: {otype}")
    if otype == "none":
        for field in ("firm_name", "engagement_partner", "udin", "opinion_text"):
            if record.get(field):
                errors.append(f"absence record must not carry {field}")
        if not record.get("absence_note"):
            errors.append("absence record requires absence_note")
    elif otype in ("unmodified", "qualified", "adverse", "disclaimer"):
        for field in ("firm_name", "opinion_date", "opinion_text"):
            if not record.get(field):
                errors.append(f"present opinion requires {field}")
        if record.get("absence_note"):
            errors.append("present opinion must not carry absence_note")
    return errors


def load_opinion(session, *, company_id, data_source, document_id, record):
    """Write one opinion row (or skip if it already exists).

    Returns (row, created_bool). Never updates an existing row.
    """
    from app.models.financial import AuditorOpinion

    existing = (
        session.query(AuditorOpinion)
        .filter_by(
            company_id=company_id,
            document_id=document_id,
            opinion_scope=record["opinion_scope"],
            version_number=1,
        )
        .one_or_none()
    )
    if existing is not None:
        return existing, False
    op_date = record.get("opinion_date")
    row = AuditorOpinion(
        company_id=company_id,
        document_id=document_id,
        data_source_id=data_source.id if data_source is not None else None,
        source_key=data_source.source_key if data_source is not None else None,
        collected_at=datetime.now(PKT),
        quality_status="UNVERIFIED",
        version_number=1,
        is_current=True,
        opinion_scope=record["opinion_scope"],
        opinion_type=record["opinion_type"],
        firm_name=record.get("firm_name"),
        engagement_partner=record.get("engagement_partner"),
        opinion_date=date.fromisoformat(op_date) if op_date else None,
        udin=record.get("udin"),
        opinion_text=record.get("opinion_text"),
        going_concern_material_uncertainty=record.get("going_concern_material_uncertainty"),
        going_concern_note=record.get("going_concern_note"),
        absence_note=record.get("absence_note"),
        opinion_page=record.get("opinion_page"),
        signature_page=record.get("signature_page"),
    )
    session.add(row)
    session.flush()
    return row, True
