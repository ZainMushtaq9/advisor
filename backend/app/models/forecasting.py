"""Phase 13 forecasting models.

Three tables. Design rules from the Phase 13 brief:

- Forecasts are probabilistic by design, but a forecast row in the
  Phase 3 ``forecasts`` table REQUIRES non-null interval_low,
  interval_high and uncertainty by construction. With one trading
  date of prices, zero calculable technical values and single-period
  statements, no residual history exists from which any interval
  could be validated — so Phase 13 writes ZERO rows to the Phase 3
  ``forecasts`` / ``forecast_evaluations`` tables. Writing a point
  estimate with an invented interval would violate the brief's
  uncertainty rule; abstaining is the brief-compliant outcome.
  (Precedent: Phase 12's investor_flows table, intentionally empty.)
- What Phase 13 DOES store: (1) the forecast target registry —
  every target x horizon the brief requires, with the minimum
  observations each baseline method needs; (2) a feature store —
  snapshots of already-stored Phase 8/9/10/12 values as of the
  forecast origin, so later phases can build features without
  re-reading source documents; (3) one assessment row per
  (security, target, horizon) stating computed /
  insufficient_inputs / not_applicable with the exact reason and
  the per-method breakdown in evidence JSON. A NOT_CALCULABLE
  assessment is a stored fact, not a missing row.
- No temporal leakage by construction: the runner only reads rows
  whose as-of/publication date is on or before the forecast origin
  (2026-11-03 for prices, statement period ends for fundamentals).
  There is no future data in the store to leak — the single price
  date IS the origin — and the walk-forward validator enforces
  chronological folds (expanding window, never shuffled) on any
  series it is given.
- New rows carry their inputs' status, never higher: every
  assessment and snapshot here is UNVERIFIED, matching its inputs.

Quality vocabulary mirrors migration 20261104_0003.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import CreatedMixin, IdMixin, ProvenanceMixin


class ForecastTarget(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One forecast target x horizon from the Phase 13 registry.

    ``target_key`` is the target (close_price, return, direction,
    volatility, volume, earnings, macro_policy_rate, macro_cpi_yoy).
    ``horizon`` is one of 1d, 1w, 1m, 3m, 6m, 12m. ``min_observations``
    is the smallest series length at which ANY baseline method can
    produce a point estimate for this target; interval estimation
    needs strictly more (see ``method_requirements``). ``scope`` is
    'company' (security_id set) or 'macro' (security_id NULL).
    """

    __tablename__ = "forecast_targets"
    __table_args__ = (
        UniqueConstraint("target_key", "horizon", name="uq_forecast_targets_key_horizon"),
        Index("idx_forecast_targets_key", "target_key"),
    )

    target_key: Mapped[str] = mapped_column(String(100), nullable=False)
    horizon: Mapped[str] = mapped_column(String(30), nullable=False)
    target_type: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(30), nullable=False)
    min_observations: Mapped[int] = mapped_column(nullable=False)
    method_requirements: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="defined")


class ForecastFeatureSnapshot(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One feature-store row: a stored value frozen as of an origin.

    ``feature_key`` names the source metric (e.g.
    ``fundamental:roe``, ``valuation:trailing_pe``,
    ``price:close``, ``macro:policy_rate``). ``evidence`` records
    the source row ids and as-of dates, so a snapshot can be traced
    back without re-reading source documents. Snapshots are never
    revised in place: a new origin writes new rows.
    """

    __tablename__ = "forecast_feature_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "security_id",
            "origin_date",
            "feature_key",
            name="uq_forecast_feature_snapshots_grain",
        ),
        Index("idx_forecast_feature_snapshots_origin", "origin_date"),
    )

    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=True
    )
    origin_date: Mapped[object] = mapped_column(Date, nullable=False)
    feature_key: Mapped[str] = mapped_column(String(200), nullable=False)
    feature_value: Mapped[object | None] = mapped_column(Numeric(24, 6), nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ForecastAssessment(IdMixin, CreatedMixin, ProvenanceMixin, Base):
    """One assessment row per (security, target, horizon) at an origin.

    ``computation_status`` is 'computed' (a forecast with a validated
    interval exists — none in this run), 'insufficient_inputs'
    (the target is in scope but the series is too short, with the
    exact shortfall in ``reason``), or 'not_applicable' (the target
    cannot apply to this security, e.g. a bank target on an
    industrial — none in this run either; every company target here
    is insufficient_inputs). ``point_estimate``, ``interval_low``
    and ``interval_high`` are NULL unless computed; they are never
    filled with a baseline point alone, because a point without a
    validated interval is not a Phase 13 forecast. ``evidence``
    carries the per-method breakdown, the inputs with as-of dates,
    the baseline comparison (none available) and the calibration
    status ('not_calibrated_insufficient_history' throughout).
    """

    __tablename__ = "forecast_assessments"
    __table_args__ = (
        UniqueConstraint(
            "security_id",
            "target_key",
            "horizon",
            "origin_date",
            name="uq_forecast_assessments_grain",
        ),
        Index("idx_forecast_assessments_security", "security_id"),
    )

    security_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("securities.id", ondelete="RESTRICT"), nullable=True
    )
    target_key: Mapped[str] = mapped_column(String(100), nullable=False)
    horizon: Mapped[str] = mapped_column(String(30), nullable=False)
    origin_date: Mapped[object] = mapped_column(Date, nullable=False)
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    computation_status: Mapped[str] = mapped_column(String(30), nullable=False)
    point_estimate: Mapped[object | None] = mapped_column(Numeric(24, 6), nullable=True)
    interval_low: Mapped[object | None] = mapped_column(Numeric(24, 6), nullable=True)
    interval_high: Mapped[object | None] = mapped_column(Numeric(24, 6), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
