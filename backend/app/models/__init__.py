"""Phase 3 SQLAlchemy models. Importing this package registers every
model on app.database.Base, so Alembic autogenerate and
Base.metadata.create_all see the full Phase 3 schema.

Table count: 54 (the 33 Phase 1 entities + 21 Phase 3 extension tables
for identifiers/sessions, documents, fundamentals/technicals detail,
health/warnings and sector profiles). The Phase 1 'ratios' entity is realised as
fundamental_metric_definitions + fundamental_metric_values (definition
+ value rows with input statement references); no second ratio table
exists, by design — see docs/phase-03/entity_catalog.md.

Phase 18 adds orchestration models (agent_definitions,
orchestration_runs, orchestration_tasks, agent_audit_logs,
agent_evaluations) to the same registry.
"""

from app.database import Base  # noqa: F401  (re-exported for Alembic / tests)
from app.models import (  # noqa: F401
    alerts,
    analysis,
    auth,
    backtesting,
    decision,
    evaluation,
    financial,
    forecasting,
    governance,
    jobs,
    macro,
    market,
    news_events,
    orchestration,
    ownership_actions,
    portfolio,
    rag,
    reference,
    registry,
    reports,
    risk,
    screener,
)

__all__ = [
    "Base",
    "alerts",
    "auth",
    "analysis",
    "backtesting",
    "decision",
    "evaluation",
    "financial",
    "forecasting",
    "governance",
    "jobs",
    "macro",
    "market",
    "news_events",
    "orchestration",
    "ownership_actions",
    "portfolio",
    "rag",
    "reference",
    "registry",
    "reports",
    "risk",
    "screener",
]
