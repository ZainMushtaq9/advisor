"""Phase 10 pure helpers: point-in-time retrieval and vintage revision.

These functions operate on plain observation dicts (the shape the
runner builds from economic_indicators rows), so they are testable
without a database. Rules:

- availability_date(row) = source_timestamp when the publisher states
  a publication date, else collected_at. A value is provably public
  only from its availability date; collection time is never an
  observation time, and an unknown publication date is handled by the
  conservative fallback, never by guessing.
- point_in_time(rows, as_of): among CURRENT rows for one indicator,
  keep those with availability_date <= as_of, and return the one with
  the latest observation_date (ties: latest availability_date). Rows
  explicitly flagged is_current=False are ignored even if the caller
  forgot to filter them. If none qualifies, return None — the
  indicator is simply absent at that date, never zero-filled.
- revise(rows, indicator_code, observation_date, new_value,
  new_source_timestamp): returns (new_rows, new_row) where the old
  current row is flipped is_current=False (the only update the
  versioned trigger allows) and a new row is appended with
  version_number + 1 and supersedes_id pointing at the old row. The
  old row is never edited or deleted.
"""

from __future__ import annotations

from datetime import date


def _parse(d: str | date | None) -> date | None:
    if d is None:
        return None
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


def availability_date(row: dict) -> date | None:
    """Earliest date the observation is provably public."""
    pub = _parse(row.get("source_timestamp"))
    if pub is not None:
        return pub
    return _parse(row.get("collected_at"))


def point_in_time(rows: list[dict], as_of: str | date) -> dict | None:
    """Latest publicly known observation for one indicator at as_of.

    Callers pass rows already filtered to one indicator_code and
    is_current=True. Returns None when nothing was public yet.
    """
    cutoff = _parse(as_of)
    assert cutoff is not None, "as_of is required"
    candidates = []
    for row in rows:
        if row.get("is_current", True) is False:
            continue
        avail = availability_date(row)
        if avail is None or avail > cutoff:
            continue
        candidates.append(row)
    if not candidates:
        return None
    candidates.sort(key=lambda r: (_parse(r["observation_date"]), availability_date(r) or date.min))
    return candidates[-1]


def current_value(rows: list[dict]) -> dict | None:
    """Latest current observation regardless of publication date."""
    current = [r for r in rows if r.get("is_current", True)]
    if not current:
        return None
    current.sort(key=lambda r: _parse(r["observation_date"]))
    return current[-1]


def revise(
    rows: list[dict],
    indicator_code: str,
    observation_date: str | date,
    new_value: str,
    new_source_timestamp: str | date | None,
    collected_at: str | date,
) -> tuple[list[dict], dict]:
    """Create a new vintage for one observation.

    Raises ValueError when no current row exists for the
    (indicator_code, observation_date) grain — a revision needs
    something to supersede; a first observation is an insert, not a
    revision.
    """
    target = _parse(observation_date)
    old = None
    for row in rows:
        if (
            row.get("indicator_code") == indicator_code
            and _parse(row.get("observation_date")) == target
            and row.get("is_current", True)
        ):
            old = row
            break
    if old is None:
        raise ValueError(f"no current row to revise for {indicator_code} @ {observation_date}")
    new_rows = []
    for row in rows:
        if row is old:
            flipped = dict(row)
            flipped["is_current"] = False
            new_rows.append(flipped)
        else:
            new_rows.append(row)
    new_row = dict(old)
    new_row["value"] = new_value
    new_row["source_timestamp"] = new_source_timestamp
    new_row["collected_at"] = collected_at
    new_row["version_number"] = int(old.get("version_number", 1)) + 1
    new_row["supersedes_id"] = old.get("id")
    new_row["is_current"] = True
    new_rows.append(new_row)
    return new_rows, new_row
