"""Phase 4 registry services: normalization, matching, import,
verification, reconciliation, and sync configuration."""

from app.services.registry import (  # noqa: F401
    importer,
    matching,
    normalization,
    reconciliation,
    sync_config,
    verification,
)
