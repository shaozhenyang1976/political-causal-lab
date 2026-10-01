"""政治行动进入 WorldState 的唯一入口。

PR-10 只打开 Intent 与 Action 的边界：support 和 oppose 可以被接纳。
接纳只记事件，不改变 WorldState。后果仍未实现。
规范里的 permission、resource requirement、institutional constraint、
actor capability 都还没有规则可查，因此这里不判断它们。
也不实现投票、联盟、任命或其他政治后果。
"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.events.event_log import Event, EventLog
from political_sim.core.models.belief import Belief, belief_key
from political_sim.core.models.individual import PREFERENCE_FIELDS, Preferences
from political_sim.core.models.world_state import WorldState
from political_sim.core.mutation import EVENT_BOUNDARY, mutation_scope
from political_sim.core.random.seeded_random import SeededRandom
from political_sim.simulation.systems.decision import INTENT_TYPES, ActionIntent

SPEC_ACTION_TYPES = frozenset(
    {
        "form_coalition",
        "leave_coalition",
        "appoint",
        "remove",
        "vote",
        "allocate",
        "sanction",
        "negotiate",
        "support",
        "oppose",
        "recruit",
        "defect",
    }
)
ADMISSIBLE_ACTION_TYPES = frozenset({"support", "oppose"})
ACTION_ADMISSION_RULE = (
    "Only support and oppose may be admitted as actions. "
    "Admission records the action and does not change WorldState."
)
CONSEQUENCE_RULE = (
    "An admitted action adds one resource unit to its actor. "
    "The addition does not change preferences, beliefs, information, fidelity, or trust."
)


@dataclass(frozen=True)
class Action:
    action_type: str
    actor_id: str
    target_ids: tuple[str, ...] = ()
    cause: str = ""

    def __post_init__(self) -> None:
        _require_token("action.action_type", self.action_type)
        _require_token("action.actor_id", self.actor_id)
        if isinstance(self.cause, str) is False:
            raise TypeError("action.cause must be a string")
        if not isinstance(self.target_ids, tuple):
            raise TypeError("action.target_ids must be a tuple")
        for index, target_id in enumerate(self.target_ids):
            _require_token(f"action.target_ids[{index}]", target_id)


class ActionResolver:
    def resolve(
        self,
        world: WorldState,
        action: Action,
        *,
        tick: int,
        events: EventLog,
        rng: SeededRandom,
    ) -> None:
        del rng  # PR-2 不消耗随机流。效果实现后只能使用这条 SeededRandom。
        reason = self._structural_failure(world, action)
        if reason is None and action.action_type in ADMISSIBLE_ACTION_TYPES:
            events.record(
                Event(
                    tick=tick,
                    event_type="action_accepted",
                    actors=(action.actor_id,),
                    targets=action.target_ids,
                    cause=_with_submitted_cause("admitted", action.cause),
                    available_information=("consequence=none",),
                    incentives=(),
                    state_change=(),
                )
            )
            self._apply_consequence(world, action, tick=tick, events=events)
            return
        if reason is None:
            with mutation_scope():
                applied = self._apply(world, action)
            if applied:
                raise RuntimeError(
                    "accepted action effects are outside the core contract; " + EVENT_BOUNDARY
                )
            reason = "action effect is not implemented"
        events.record(
            Event(
                tick=tick,
                event_type="action_rejected",
                actors=(action.actor_id,),
                targets=action.target_ids,
                cause=_with_submitted_cause(reason, action.cause),
                available_information=(),
                incentives=(),
                state_change=(),
            )
        )

    def commit_belief(
        self,
        world: WorldState,
        belief: Belief,
        *,
        tick: int,
        events: EventLog,
        available_information: tuple[str, ...],
        state_change: tuple[str, ...],
        cause: str = "information_transmission",
    ) -> None:
        known_ids = world.known_actor_ids()
        if belief.observer_id not in known_ids or belief.subject_id not in known_ids:
            raise ValueError("belief refers to an unknown actor")
        with mutation_scope():
            world.beliefs[belief_key(belief)] = belief
        events.record(
            Event(
                tick=tick,
                event_type="belief_updated",
                actors=(belief.observer_id,),
                targets=(belief.subject_id,),
                cause=cause,
                available_information=available_information,
                incentives=(),
                state_change=state_change,
            )
        )

    def commit_preference(
        self,
        world: WorldState,
        *,
        individual_id: str,
        field: str,
        value: float,
        tick: int,
        events: EventLog,
    ) -> None:
        if field not in PREFERENCE_FIELDS:
            raise ValueError(f"unknown preference field {field!r}")
        individual = world.individuals.get(individual_id)
        if individual is None:
            raise ValueError(f"invalid individual reference: {individual_id}")
        updated = {
            name: value if name == field else getattr(individual.preferences, name)
            for name in PREFERENCE_FIELDS
        }
        with mutation_scope():
            individual.preferences = Preferences(**updated)
        events.record(
            Event(
                tick=tick,
                event_type="experiment_intervention",
                actors=(individual_id,),
                targets=(),
                cause="exogenous_true_state_change",
                available_information=(),
                incentives=(),
                state_change=(f"{individual_id}.preferences.{field}={value!r}",),
            )
        )

    def record_intent(
        self,
        intent: ActionIntent,
        *,
        tick: int,
        events: EventLog,
        available_information: tuple[str, ...],
    ) -> None:
        if intent.intent not in INTENT_TYPES:
            raise ValueError(f"unknown action intent {intent.intent!r}")
        events.record(
            Event(
                tick=tick,
                event_type="action_intent",
                actors=(intent.observer_id,),
                targets=() if intent.subject_id is None else (intent.subject_id,),
                cause=intent.cause,
                available_information=available_information,
                incentives=(),
                state_change=(),
            )
        )

    def _apply_consequence(
        self,
        world: WorldState,
        action: Action,
        *,
        tick: int,
        events: EventLog,
    ) -> None:
        updated = world.resources.get(action.actor_id, 0.0) + 1.0
        with mutation_scope():
            world.resources[action.actor_id] = updated
        events.record(
            Event(
                tick=tick,
                event_type="action_consequence",
                actors=(action.actor_id,),
                targets=action.target_ids,
                cause=_with_submitted_cause("accepted_action", action.cause),
                available_information=(),
                incentives=(),
                state_change=(f"{action.actor_id}.resources={updated!r}",),
            )
        )

    def _structural_failure(self, world: WorldState, action: Action) -> str | None:
        problems: list[str] = []
        if action.action_type not in SPEC_ACTION_TYPES:
            problems.append("unknown action type")
        known_ids = world.known_actor_ids()
        if action.actor_id not in known_ids:
            problems.append("invalid actor reference")
        for target_id in action.target_ids:
            if target_id not in known_ids:
                problems.append(f"invalid target reference: {target_id}")
        if not problems:
            return None
        return "; ".join(problems)

    def _apply(self, world: WorldState, action: Action) -> bool:
        del world, action
        return False


def _with_submitted_cause(reason: str, submitted: str) -> str:
    if submitted == "":
        return reason
    return f"{reason} ({submitted})"


def _require_token(name: str, value: object) -> None:
    if not isinstance(value, str) or value == "" or value != value.strip():
        raise ValueError(f"{name} must be a non-empty string")
