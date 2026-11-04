"""Phase 3 SQLAlchemy models. Importing this package registers every
model on app.database.Base, so Alembic autogenerate and
Base.metadata.create_all see the full Phase 3 schema.

Table count: 54 (the 33 Phase 1 entities + 21 Phase 3 extension tables
for identifiers/sessions, documents, fundamentals/technicals detail,
health/warnings and sector profiles). The Phase 1 'ratios' entity is realised as
fundamental_metric_definitions + fundamental_metric_values (definition
+ value rows with input statement references); no second ratio table
exists, by design — see docs/phase-03/entity_catalog.md.
"""

from app.database import Base  # noqa: F401  (re-exported for Alembic / tests)
from app.models import (  # noqa: F401
    analysis,
    financial,
    forecasting,
    governance,
    macro,
    market,
    news_events,
    ownership_actions,
    reference,
    registry,
    risk,
)

__all__ = [
    "Base",
    "analysis",
    "financial",
    "forecasting",
    "governance",
    "macro",
    "market",
    "news_events",
    "ownership_actions",
    "reference",
    "registry",
    "risk",
]
