"""Phase 26 evaluation models: dataset registry, model cards, promotion
gates, evaluation runs, evaluation metrics, golden test cases/results.

Seven tables, all owned by this phase (precedent: Phases 11-25 store
their own tables rather than retrofitting Phase 3 tables):

- ``evaluation_datasets``: every dataset an evaluation may draw on:
  its key, kind, version, out-of-sample split policy, as-of date,
  stored row count, and status. A dataset is a versioned pointer
  to stored rows, never a copy of them: re-running an evaluation
  against the same dataset version must reproduce the same inputs.
- ``model_cards``: one card per model/version in the system
  (forecasting baselines, decision rules, screener score, risk
  controls, RAG retrieval, orchestration fallback, technical
  registry, report QA gate). Each card states its purpose, what
  it was trained on (stored rows only — no external training
  data exists in this project), its evaluation status, its
  limitations, and its promotion status. Every card in the seed
  run is NOT_PROMOTED: no promotion gate has been met and no
  human approval gate has been granted.
- ``promotion_gates``: the gates a model must pass before it may
  be promoted (out-of-sample evidence, baselines and negative
  outcomes included, evidence-governed promotion, no unsupported
  accuracy claims, recorded human approval). All gates are
  NOT_MET in the seed run: no model has out-of-sample evaluated
  predictions, and no human approval has been recorded. A gate
  is never MET by the absence of failures — it is MET only by
  positive evidence, which does not exist yet.
- ``evaluation_runs``: one row per evaluation invocation, keyed
  by a unique run_id (idempotency key: a second --commit with
  the same run_id writes nothing).
- ``evaluation_metrics``: one row per (run, subject, metric):
  the value (NULL when not evaluable), the status
  (computed / insufficient_inputs / not_applicable /
  not_evaluable), the exact reason, and evidence JSON. A
  NOT_EVALUABLE metric is a stored fact, not a missing row —
  the same discipline as Phase 13 assessments.
- ``golden_test_cases``: the golden suite — deterministic cases
  for source matching, entity resolution, tool selection,
  citations, extraction, summarization, refusal/abstention,
  injection resistance, and conflicting sources. Each case
  states its category, its input description, and its expected
  outcome. Cases are checked either as pure functions (name
  normalization, alias capping, QA citation rule) or against
  stored rows (stored agent/RAG evaluations, stored decisions,
  stored registry status) — never by re-emitting adversarial
  input text and never by re-running another phase's retrieval.
- ``golden_test_results``: one row per (run, case): passed or
  failed with evidence. A failed golden case blocks promotion
  of every model it touches (see promotion gates); it never
  blocks the evaluation run itself from being recorded.

These tables carry no quality_status: they are evaluation
records, not business data, and no quality-status promotion
ever applies to them. No order, execution, external-send, or
publication concept exists in these tables. No credentials are
stored anywhere here.

ID deviation, deliberate (same reason as Phase 24 auth tables
and Phase 25 job tables): these tables do NOT use ``IdMixin``.
``IdMixin`` uses ``Identity(always=True)`` (PostgreSQL-only)
and a BigInteger PK is not a rowid alias on SQLite, so inserts
fail NOT NULL there. The evaluation tables use a plain Integer
primary key with autoincrement — SERIAL on PostgreSQL, INTEGER
rowid alias on SQLite — so the same code runs on both. The
migration matches this exactly.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin

DATASET_STATUSES = ("defined", "active", "retired")

PROMOTION_STATUSES = ("NOT_PROMOTED", "PROMOTED")

GATE_STATUSES = ("NOT_MET", "MET", "BLOCKED")

RUN_KINDS = (
    "forecast",
    "recommendation",
    "agent_rag",
    "backtest",
    "reports_qa",
    "drift",
    "golden",
    "full",
)

RUN_STATUSES = ("completed", "failed")

METRIC_STATUSES = ("computed", "insufficient_inputs", "not_applicable", "not_evaluable")


class EvaluationDataset(CreatedMixin, Base):
    """One versioned evaluation dataset (a pointer to stored rows)."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "evaluation_datasets"
    __table_args__ = (
        UniqueConstraint("dataset_key", name="uq_evaluation_datasets_key"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in DATASET_STATUSES)})",
            name="ck_evaluation_datasets_status",
        ),
    )

    dataset_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    # Out-of-sample split policy in words: how train/validation/test
    # are separated, and when a label counts as matured.
    split_policy: Mapped[str] = mapped_column(String(1000), nullable=False)
    as_of_date: Mapped[object | None] = mapped_column(Date)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    evidence: Mapped[dict | None] = mapped_column(JSON)


class ModelCard(CreatedMixin, Base):
    """One model card: purpose, training data, evaluation, limits, promotion."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "model_cards"
    __table_args__ = (
        UniqueConstraint("model_key", "version", name="uq_model_cards_key_version"),
        CheckConstraint(
            f"promotion_status IN ({', '.join(repr(s) for s in PROMOTION_STATUSES)})",
            name="ck_model_cards_promotion_status",
        ),
    )

    model_key: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    purpose: Mapped[str] = mapped_column(String(1000), nullable=False)
    # What the model was trained/fitted on. "Stored rows only" is
    # the honest answer for every model in this project: no
    # external training corpus exists here.
    training_data: Mapped[str] = mapped_column(String(1000), nullable=False)
    evaluation_status: Mapped[str] = mapped_column(String(1000), nullable=False)
    limitations: Mapped[str] = mapped_column(String(2000), nullable=False)
    promotion_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="NOT_PROMOTED"
    )
    evidence: Mapped[dict | None] = mapped_column(JSON)


class PromotionGate(CreatedMixin, Base):
    """One promotion gate: the requirement and whether it is met."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "promotion_gates"
    __table_args__ = (
        UniqueConstraint("gate_key", name="uq_promotion_gates_key"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in GATE_STATUSES)})",
            name="ck_promotion_gates_status",
        ),
    )

    gate_key: Mapped[str] = mapped_column(String(100), nullable=False)
    applies_to: Mapped[str] = mapped_column(String(100), nullable=False)
    requirement: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOT_MET")
    # Why the gate is or is not met, with the exact missing evidence.
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON)


class EvaluationRun(CreatedMixin, Base):
    """One evaluation invocation (idempotency key = run_id)."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "evaluation_runs"
    __table_args__ = (
        UniqueConstraint("run_id", name="uq_evaluation_runs_run_id"),
        CheckConstraint(
            f"kind IN ({', '.join(repr(s) for s in RUN_KINDS)})",
            name="ck_evaluation_runs_kind",
        ),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in RUN_STATUSES)})",
            name="ck_evaluation_runs_status",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False, default="full")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[dict | None] = mapped_column(JSON)


class EvaluationMetric(CreatedMixin, Base):
    """One evaluated metric: value (or NULL) + status + reason + evidence."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "evaluation_metrics"
    __table_args__ = (
        UniqueConstraint("run_id", "subject_key", "metric_key", name="uq_evaluation_metrics_grain"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in METRIC_STATUSES)})",
            name="ck_evaluation_metrics_status",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_key: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[object | None] = mapped_column(Numeric(24, 6), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON)


class GoldenTestCase(CreatedMixin, Base):
    """One golden test case with its expected outcome."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "golden_test_cases"
    __table_args__ = (UniqueConstraint("case_key", name="uq_golden_test_cases_key"),)

    case_key: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    input_desc: Mapped[str] = mapped_column(String(1000), nullable=False)
    expected_outcome: Mapped[str] = mapped_column(String(1000), nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON)


class GoldenTestResult(CreatedMixin, Base):
    """One golden case outcome within one evaluation run."""

    # Portable PK (see module docstring): NOT IdMixin.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    __tablename__ = "golden_test_results"
    __table_args__ = (UniqueConstraint("run_id", "case_key", name="uq_golden_test_results_grain"),)

    run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    case_key: Mapped[str] = mapped_column(String(100), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evidence: Mapped[dict | None] = mapped_column(JSON)
