"""Action intent from the belief visible to the actor.

This module neither reads nor writes true state.
A constraint is checked before the baseline threshold. The threshold is not
a voting model. It separates "belief differs" from "constraint differs" into
two paths that can be experimented on separately.

With no constraint and exactly one belief:

    mean(perceived preference) > 0.5 → support
    mean(perceived preference) < 0.5 → oppose
    mean(perceived preference) = 0.5 → abstain

When several constraints are present, their order comes from the current
experimental specification, not from any inherent importance among them.
When there is not exactly one belief, the intent is seek_information.
Multiple beliefs are not combined into one preference.
"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.models.individual import PREFERENCE_FIELDS, Preferences
from political_sim.simulation.systems.information import ActorView, require_actor_view

INTENT_TYPES = ("support", "oppose", "abstain", "delay", "seek_information")
CONSTRAINT_NAMES = frozenset({"seek_information", "delay", "abstain"})
CONSTRAINT_PRECEDENCE_NOTE = (
    "Constraint precedence defined by the current experimental specification."
)
BASELINE_PERCEIVED_MEAN_CUTOFF = 0.5


@dataclass(frozen=True)
class ConstraintPolicy:
    """Experimental parameter. precedence states only which constraint this specification checks first."""

    name: str
    precedence: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or self.name == "":
            raise ValueError("constraint policy name must be a non-empty string")
        if not isinstance(self.precedence, tuple) or len(self.precedence) == 0:
            raise ValueError("constraint policy precedence must be a non-empty tuple")
        if len(set(self.precedence)) != len(self.precedence):
            raise ValueError("duplicate constraint in policy")
        for name in self.precedence:
            if name not in CONSTRAINT_NAMES:
                raise ValueError(f"unknown decision constraint {name!r}")


EXPERIMENTAL_CONSTRAINT_POLICY = ConstraintPolicy(
    "experimental-spec-0.2",
    ("seek_information", "delay", "abstain"),
)
CONSTRAINT_PRECEDENCE = EXPERIMENTAL_CONSTRAINT_POLICY.precedence


@dataclass(frozen=True)
class DecisionContext:
    observer_id: str
    subject_id: str | None
    perceived_preference: Preferences | None
    belief_confidence: float
    available_information: tuple[str, ...]
    known_constraints: tuple[str, ...]
    perception_status: str


@dataclass(frozen=True)
class ActionIntent:
    observer_id: str
    subject_id: str | None
    intent: str
    cause: str


def decision_context_from_view(
    view: ActorView, known_constraints: tuple[str, ...] = ()
) -> DecisionContext:
    checked = require_actor_view(view)
    constraints = _validate_constraints(known_constraints)
    if len(checked.beliefs) != 1:
        status = "none" if len(checked.beliefs) == 0 else "ambiguous"
        return DecisionContext(
            observer_id=checked.observer_id,
            subject_id=None,
            perceived_preference=None,
            belief_confidence=0.0,
            available_information=(),
            known_constraints=constraints,
            perception_status=status,
        )
    belief = checked.beliefs[0]
    received = tuple(
        f"received_preference.{field}={getattr(belief.estimated_preference, field)!r}"
        for field in PREFERENCE_FIELDS
    )
    return DecisionContext(
        observer_id=checked.observer_id,
        subject_id=belief.subject_id,
        perceived_preference=belief.estimated_preference,
        belief_confidence=belief.estimated_information,
        available_information=received,
        known_constraints=constraints,
        perception_status="single",
    )


def decide(
    context: DecisionContext,
    policy: ConstraintPolicy = EXPERIMENTAL_CONSTRAINT_POLICY,
) -> ActionIntent:
    if not isinstance(context, DecisionContext):
        raise TypeError("decide requires DecisionContext, not True State")
    if not isinstance(policy, ConstraintPolicy):
        raise TypeError("constraint precedence must be a ConstraintPolicy")
    for name in policy.precedence:
        if name in context.known_constraints:
            return _intent(context, name, f"constraint:{name}")
    if context.perception_status == "none":
        return _intent(context, "seek_information", "no_belief")
    if context.perception_status == "ambiguous":
        return _intent(context, "seek_information", "ambiguous_beliefs")
    assert context.perceived_preference is not None
    mean = _mean_preference(context.perceived_preference)
    if mean > BASELINE_PERCEIVED_MEAN_CUTOFF:
        intent = "support"
    elif mean < BASELINE_PERCEIVED_MEAN_CUTOFF:
        intent = "oppose"
    else:
        intent = "abstain"
    return _intent(context, intent, f"baseline:{intent}")


def _intent(context: DecisionContext, intent: str, cause: str) -> ActionIntent:
    return ActionIntent(
        observer_id=context.observer_id,
        subject_id=context.subject_id,
        intent=intent,
        cause=cause,
    )


def _mean_preference(preference: Preferences) -> float:
    total = sum(getattr(preference, field) for field in PREFERENCE_FIELDS)
    return total / len(PREFERENCE_FIELDS)


def _validate_constraints(known_constraints: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(known_constraints, tuple):
        raise TypeError("known_constraints must be a tuple")
    for name in known_constraints:
        if name not in CONSTRAINT_NAMES:
            raise ValueError(f"unknown decision constraint {name!r}")
    if len(known_constraints) != len(set(known_constraints)):
        raise ValueError("duplicate decision constraint")
    return known_constraints
