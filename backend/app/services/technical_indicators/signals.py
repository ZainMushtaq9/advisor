"""Signal-event engine (Phase 6) — deliberately separate.

This module is SEPARATE from any investment decision engine, which
does not exist in this project. A signal event here is a stored
observation that a deterministic, versioned rule condition held on
a stored indicator value at a given date. It is never a buy, sell,
or hold recommendation, never a guaranteed opportunity, and never
a prediction. No rule here promises any return.

Activation discipline (this is the point of the separation):

- ACTIVATED_RULES is empty by default. A rule becomes activated
  only by an explicit, versioned configuration change once its
  input indicators are actually calculable for the securities it
  would cover. Activating a rule on empty data would manufacture
  the appearance of coverage, so the engine refuses to evaluate
  rules whose inputs are missing: a missing input means no event,
  never a default event.
- Evaluation uses ONLY stored indicator values dated on or before
  the event date (no-look-ahead). A rule that needs a future value
  cannot fire.
- EXAMPLE_RULES below documents the shape of a rule (a golden
  cross) without activating it. It is documentation, not coverage.

Event records match the technical_signal_events table: security,
event_date, indicator_key, event_condition, observed_value,
parameter_configuration, evidence, calculation_version.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class SignalRule:
    """A deterministic, versioned signal rule."""

    key: str
    description: str
    indicator_keys: tuple[str, ...]
    condition: str
    parameters: dict = field(default_factory=dict)
    config_version: str = "1.0"


# No rule is activated: every input indicator is NOT_CALCULABLE on
# the production data, so any activation today would be theatre.
ACTIVATED_RULES: tuple[SignalRule, ...] = ()

# Documentation only: the shape a golden-cross rule would take once
# SMA(50) and SMA(200) are calculable. NOT evaluated.
EXAMPLE_RULES: tuple[SignalRule, ...] = (
    SignalRule(
        key="sma_golden_cross_example",
        description="Example only: SMA(50) crosses above SMA(200).",
        indicator_keys=("sma_50", "sma_200"),
        condition="sma_50 crosses from below to above sma_200",
        parameters={"fast": 50, "slow": 200},
    ),
)


def evaluate_rules(
    rules: tuple[SignalRule, ...],
    values_by_key: dict[str, Decimal],
    event_date: date,
) -> list[dict]:
    """Evaluate activated rules against stored values at one date.

    ``values_by_key`` must contain ONLY values dated on or before
    ``event_date`` (the caller enforces this; see the no-look-ahead
    test). A rule whose inputs are absent produces no event.
    Returns event dicts matching the signal-events table shape.
    """
    events: list[dict] = []
    for rule in rules:
        if any(k not in values_by_key for k in rule.indicator_keys):
            continue
        # No rule logic lives here yet by design: ACTIVATED_RULES is
        # empty, and a rule must ship its own pure evaluator before
        # activation. An activated rule without an evaluator is a
        # configuration error, surfaced loudly, never silently passed.
        raise NotImplementedError(
            f"Rule {rule.key} is activated but has no evaluator; "
            "refusing to fabricate events."
        )
    return events
