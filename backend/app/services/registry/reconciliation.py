"""Reconciliation of the registry against a dated official snapshot.

The snapshot is a file the operator obtained from an official source
on a stated date (see docs/phase-04/reconciliation_methodology.md).
It is a BASELINE, not a target to be forced: the registry is never
padded to match it, and the snapshot is never edited to match the
registry. The report states matched / missing / extra tickers and a
coverage ratio, and any gap is a finding, not a failure to hide.

No expected totals are invented. If no snapshot file is supplied,
reconcile() returns a report that says so explicitly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.reference import Security
from app.services.registry.normalization import normalize_ticker


@dataclass
class ReconciliationReport:
    snapshot_source: str | None
    snapshot_date: str | None
    snapshot_tickers: int = 0
    registry_tickers: int = 0
    matched: int = 0
    missing_from_registry: list[str] = field(default_factory=list)
    extra_in_registry: list[str] = field(default_factory=list)
    coverage_ratio: float | None = None
    note: str = ""


def load_snapshot(path: str | Path) -> dict:
    """Load a snapshot JSON file: {source, snapshot_date, tickers: [...]}.
    Tickers are normalized on load; invalid entries are dropped and
    counted in the caller's note, never silently kept.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("tickers"), list):
        # Audit LOW finding: a malformed snapshot previously raised
        # KeyError/AttributeError deep in the loader. Fail loudly
        # with a clear message instead.
        raise ValueError(
            "Snapshot file must be a JSON object with a 'tickers' list."
        )
    tickers: list[str] = []
    dropped = 0
    for raw in data.get("tickers", []):
        try:
            tickers.append(normalize_ticker(str(raw)))
        except (ValueError, TypeError):
            dropped += 1
    return {
        "source": data.get("source"),
        "snapshot_date": data.get("snapshot_date"),
        "tickers": sorted(set(tickers)),
        "dropped": dropped,
    }


def reconcile(session: Session, snapshot: dict | None) -> ReconciliationReport:
    registry = {normalize_ticker(s.ticker) for s in session.query(Security).all()}
    if snapshot is None:
        return ReconciliationReport(
            snapshot_source=None,
            snapshot_date=None,
            registry_tickers=len(registry),
            note=(
                "No dated official snapshot was available at reconciliation time, "
                "so no coverage claim is made. Registry counts are reported as-is."
            ),
        )
    snap = set(snapshot["tickers"])
    matched = snap & registry
    report = ReconciliationReport(
        snapshot_source=snapshot.get("source"),
        snapshot_date=snapshot.get("snapshot_date"),
        snapshot_tickers=len(snap),
        registry_tickers=len(registry),
        matched=len(matched),
        missing_from_registry=sorted(snap - registry),
        extra_in_registry=sorted(registry - snap),
        note=f"Dropped {snapshot.get('dropped', 0)} invalid snapshot entries on load.",
    )
    report.coverage_ratio = (len(matched) / len(snap)) if snap else None
    return report
