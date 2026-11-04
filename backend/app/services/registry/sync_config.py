"""Configurable registry sync settings (Phase 4).

Phase 4 defines the sync configuration; it does NOT start a scheduler
or a periodic job (scheduling belongs to a later phase, and a machine
that is off collects nothing). The default is manual: an operator
runs an import with a stated source and a stated snapshot date.

Frequencies here are configuration values only. They are NOT claims
about how often a source actually updates — that is recorded per
source in the source research, and an unverified frequency stays
"unknown" there.
"""

from __future__ import annotations

from dataclasses import dataclass

ALLOWED_FREQUENCIES = ("manual", "daily", "weekly", "monthly")


@dataclass(frozen=True)
class SyncConfig:
    source_key: str
    frequency: str = "manual"
    enabled: bool = False
    note: str = "Manual only in Phase 4; no scheduler is started."

    def __post_init__(self) -> None:
        if self.frequency not in ALLOWED_FREQUENCIES:
            raise ValueError(f"Unknown sync frequency: {self.frequency!r}")
        if self.frequency != "manual" and not self.enabled:
            # A non-manual frequency that is disabled is a documented
            # intention, not an active schedule.
            pass


DEFAULT_SYNC_CONFIGS: tuple[SyncConfig, ...] = (
    SyncConfig(source_key="psx_official", frequency="manual", enabled=False),
    SyncConfig(source_key="dps", frequency="manual", enabled=False),
    SyncConfig(source_key="secp", frequency="manual", enabled=False),
)
