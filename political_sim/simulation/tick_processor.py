"""一个 Tick 的 17 个槽位。

顺序来自规范第 30 节。
代表者只有在信号被采信后，才根据 ActorView 产生行动意图。未采信则意图为 seek_information，原因是 trust_rejected。
组织决策、激励、联盟、权力等槽位仍然为空。
"""

from __future__ import annotations

from political_sim.core.actions.action_resolver import Action, ActionResolver
from political_sim.core.events.event_log import Event, EventLog
from political_sim.core.models.world_state import WorldState
from political_sim.core.random.seeded_random import SeededRandom
from political_sim.simulation.systems.decision import (
    ConstraintPolicy,
    ActionIntent,
    decide,
    decision_context_from_view,
)
from political_sim.simulation.systems.information import (
    GroupObservation,
    TransmittedSignal,
    actor_view,
    apply_generation_error,
    belief_from_signal,
    deliver,
    generate_observations,
    generation_record,
    signal_record,
)
from political_sim.simulation.systems.trust import admits

TICK_PHASES = (
    "environment_update",
    "information_generation",
    "information_transmission",
    "belief_update",
    "incentive_update",
    "coalition_evaluation",
    "representative_decision",
    "organization_decision",
    "political_action",
    "conflict_bargaining",
    "resource_allocation",
    "power_recalculation",
    "representation_update",
    "network_update",
    "survival_replacement",
    "metrics",
    "event_log",
)


class _TickContext:
    def __init__(
        self,
        *,
        tick: int,
        world: WorldState,
        actions: tuple[Action, ...],
        resolver: ActionResolver,
        events: EventLog,
        rng: SeededRandom,
        information_quality: float,
        generation_error: float,
        trust: float,
        trust_threshold: float,
        fidelity: float,
        decision_constraints: dict[str, tuple[str, ...]],
        constraint_policy: ConstraintPolicy,
    ) -> None:
        self.tick = tick
        self.world = world
        self.actions = actions
        self.resolver = resolver
        self.events = events
        self.rng = rng
        self.information_quality = information_quality
        self.generation_error = generation_error
        self.trust = trust
        self.trust_threshold = trust_threshold
        self.fidelity = fidelity
        self.decision_constraints = decision_constraints
        self.constraint_policy = constraint_policy
        self.observations: tuple[GroupObservation, ...] = ()
        self.deliveries: tuple[tuple[TransmittedSignal, str], ...] = ()
        self.rejections: dict[str, list[tuple[str, tuple[str, ...]]]] = {}


class TickProcessor:
    def __init__(self) -> None:
        self.phases = {
            "environment_update": _empty_phase,
            "information_generation": _information_generation,
            "information_transmission": _information_transmission,
            "belief_update": _belief_update,
            "incentive_update": _empty_phase,
            "coalition_evaluation": _empty_phase,
            "representative_decision": _representative_decision,
            "organization_decision": _empty_phase,
            "political_action": _political_action,
            "conflict_bargaining": _empty_phase,
            "resource_allocation": _empty_phase,
            "power_recalculation": _empty_phase,
            "representation_update": _empty_phase,
            "network_update": _empty_phase,
            "survival_replacement": _empty_phase,
            "metrics": _empty_phase,
            "event_log": _event_log,
        }

    def step(
        self,
        *,
        tick: int,
        world: WorldState,
        actions: tuple[Action, ...],
        resolver: ActionResolver,
        events: EventLog,
        rng: SeededRandom,
        information_quality: float,
        generation_error: float,
        trust: float,
        trust_threshold: float,
        fidelity: float,
        decision_constraints: dict[str, tuple[str, ...]],
        constraint_policy: ConstraintPolicy,
    ) -> int:
        context = _TickContext(
            tick=tick + 1,
            world=world,
            actions=actions,
            resolver=resolver,
            events=events,
            rng=rng,
            information_quality=information_quality,
            generation_error=generation_error,
            trust=trust,
            trust_threshold=trust_threshold,
            fidelity=fidelity,
            decision_constraints=decision_constraints,
            constraint_policy=constraint_policy,
        )
        for name in TICK_PHASES:
            self.phases[name](context)
        context.world.validate()
        return context.tick


def _empty_phase(context: _TickContext) -> None:
    del context


def _information_generation(context: _TickContext) -> None:
    true_observations = generate_observations(context.world)
    context.observations = tuple(
        apply_generation_error(observation, context.generation_error)
        for observation in true_observations
    )
    for observation in context.observations:
        context.events.record(
            Event(
                tick=context.tick,
                event_type="signal_generated",
                actors=(observation.observer_id,),
                targets=(observation.subject_id,),
                cause="generation",
                available_information=generation_record(observation, context.generation_error),
                incentives=(),
                state_change=(),
            )
        )


def _information_transmission(context: _TickContext) -> None:
    deliveries, ambiguous = deliver(
        context.observations,
        context.information_quality,
        tuple(context.world.networks.values()),
        fidelity=context.fidelity,
    )
    context.deliveries = deliveries
    for observer_id, subject_id in ambiguous:
        context.events.record(
            Event(
                tick=context.tick,
                event_type="transmission_ambiguous",
                actors=(observer_id,),
                targets=(subject_id,),
                cause="ambiguous_transmission",
                available_information=(),
                incentives=(),
                state_change=(),
            )
        )


def _belief_update(context: _TickContext) -> None:
    context.rejections = {}
    for signal, cause in context.deliveries:
        received, changed = signal_record(signal)
        if not admits(context.trust, context.trust_threshold):
            context.rejections.setdefault(signal.observer_id, []).append(
                (signal.subject_id, received)
            )
            context.events.record(
                Event(
                    tick=context.tick,
                    event_type="trust_rejected",
                    actors=(signal.observer_id,),
                    targets=(signal.subject_id,),
                    cause="trust_rejected",
                    available_information=received,
                    incentives=(),
                    state_change=(),
                )
            )
            continue
        context.resolver.commit_belief(
            context.world,
            belief_from_signal(signal),
            tick=context.tick,
            events=context.events,
            available_information=received,
            state_change=changed,
            cause=cause,
        )


def _representative_decision(context: _TickContext) -> None:
    for observer_id in context.world.representatives:
        rejected = context.rejections.get(observer_id)
        if rejected:
            subject_id = rejected[0][0] if len(rejected) == 1 else None
            received: tuple[str, ...] = ()
            for _subject_id, info in rejected:
                received = received + info
            context.resolver.record_intent(
                ActionIntent(observer_id, subject_id, "seek_information", "trust_rejected"),
                tick=context.tick,
                events=context.events,
                available_information=("intent=seek_information",) + received,
            )
            continue
        view = actor_view(context.world, observer_id)
        constraints = context.decision_constraints.get(observer_id, ())
        decision_context = decision_context_from_view(view, constraints)
        intent = decide(decision_context, context.constraint_policy)
        context.resolver.record_intent(
            intent,
            tick=context.tick,
            events=context.events,
            available_information=decision_context.available_information,
        )


def _political_action(context: _TickContext) -> None:
    for action in context.actions:
        context.resolver.resolve(
            context.world,
            action,
            tick=context.tick,
            events=context.events,
            rng=context.rng,
        )


def _event_log(context: _TickContext) -> None:
    context.events.record(
        Event(
            tick=context.tick,
            event_type="tick_completed",
            actors=(),
            targets=(),
            cause="tick_protocol",
            available_information=(),
            incentives=(),
            state_change=(),
        )
    )
