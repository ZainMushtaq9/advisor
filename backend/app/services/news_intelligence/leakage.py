"""Look-ahead leakage prevention (prompt section 9).

A forecast may use ONLY news available before its prediction
timestamp. The rule is strict and mechanical:

- usable(published_at, prediction_timestamp) is True ONLY when
  both timestamps are timezone-aware and published_at <=
  prediction_timestamp. A naive (timezone-less) timestamp is
  rejected as unknown — never silently assumed to be Karachi
  time here, because a leakage guard that guesses is not a
  guard.
- A forecast snapshot is immutable: its input cutoff is
  recorded at creation, and any article published after the
  cutoff is excluded from that snapshot, even if it arrives
  before the forecast is evaluated.
- Backtest vs live distinction is carried on the snapshot
  record (``snapshot_kind``), not inferred from dates.
"""

from __future__ import annotations

from datetime import datetime


def usable_for_forecast(
    published_at: datetime | None,
    prediction_timestamp: datetime | None,
) -> tuple[bool, str]:
    """(usable, reason). False unless both are aware datetimes
    and published_at <= prediction_timestamp."""
    if published_at is None:
        return False, "publication timestamp unknown: excluded (never assumed)"
    if prediction_timestamp is None:
        return False, "prediction timestamp unknown: excluded"
    if published_at.tzinfo is None or prediction_timestamp.tzinfo is None:
        return False, "naive timestamp rejected: timezone required for cutoff checks"
    if published_at <= prediction_timestamp:
        return True, "published at or before the prediction timestamp"
    return False, "published after the prediction timestamp: future-news leakage"


def snapshot_allows(
    snapshot_cutoff: datetime | None,
    article_published_at: datetime | None,
) -> tuple[bool, str]:
    """Same rule, phrased for immutable snapshots: an article is
    in a snapshot ONLY if published at or before its cutoff."""
    return usable_for_forecast(article_published_at, snapshot_cutoff)
