"""从事件日志重建生成、收到的信号和意图。不运行模拟，也不写世界。"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.events.event_log import EventLog
from political_sim.core.models.individual import PREFERENCE_FIELDS, Preferences
from political_sim.simulation.systems.information import preference_distance


@dataclass(frozen=True)
class ErrorDecomposition:
    generation_gap: float
    quality_gap: float
    transmission_gap: float
    belief_gap: float


@dataclass(frozen=True)
class ActorTick:
    tick: int
    actor_id: str
    generated: Preferences | None
    received: Preferences | None
    intent_cause: str | None


@dataclass(frozen=True)
class IntentChange:
    actor_id: str
    from_tick: int
    to_tick: int
    old_cause: str
    new_cause: str
    old_received: Preferences | None
    new_received: Preferences | None


def decompose(
    reality: Preferences,
    generated: Preferences,
    received: Preferences,
    belief: Preferences,
) -> ErrorDecomposition:
    generation_gap = preference_distance(reality, generated)
    quality_gap = preference_distance(generated, received)
    transmission_gap = preference_distance(received, belief)
    belief_gap = preference_distance(reality, belief)
    return ErrorDecomposition(generation_gap, quality_gap, transmission_gap, belief_gap)


def preferences_from_labels(lines: tuple[str, ...], stem: str) -> Preferences:
    values = {field: _labeled_float(lines, f"{stem}.{field}") for field in PREFERENCE_FIELDS}
    return Preferences(**values)


def reconstruct(event_log: EventLog) -> tuple[ActorTick, ...]:
    records: dict[tuple[int, str], dict[str, object]] = {}
    order: list[tuple[int, str]] = []
    for event in event_log:
        if event.event_type not in {"signal_generated", "belief_updated", "action_intent"}:
            continue
        if len(event.actors) != 1:
            raise ValueError("baseline events record one actor")
        key = (event.tick, event.actors[0])
        if key not in records:
            records[key] = {"generated": None, "received": None, "intent_cause": None}
            order.append(key)
        slot = records[key]
        if event.event_type == "signal_generated":
            slot["generated"] = preferences_from_labels(
                event.available_information, "generated_preference"
            )
        elif event.event_type == "belief_updated":
            slot["received"] = preferences_from_labels(
                event.available_information, "received_preference"
            )
        else:
            slot["intent_cause"] = event.cause
    return tuple(
        ActorTick(
            tick=tick,
            actor_id=actor_id,
            generated=records[(tick, actor_id)]["generated"],  # type: ignore[arg-type]
            received=records[(tick, actor_id)]["received"],  # type: ignore[arg-type]
            intent_cause=records[(tick, actor_id)]["intent_cause"],  # type: ignore[arg-type]
        )
        for tick, actor_id in order
    )


def intent_changes(records: tuple[ActorTick, ...]) -> tuple[IntentChange, ...]:
    previous: dict[str, ActorTick] = {}
    changes: list[IntentChange] = []
    for record in records:
        if record.intent_cause is None:
            continue
        earlier = previous.get(record.actor_id)
        if earlier is not None and earlier.intent_cause != record.intent_cause:
            changes.append(
                IntentChange(
                    actor_id=record.actor_id,
                    from_tick=earlier.tick,
                    to_tick=record.tick,
                    old_cause=earlier.intent_cause,
                    new_cause=record.intent_cause,
                    old_received=earlier.received,
                    new_received=record.received,
                )
            )
        previous[record.actor_id] = record
    return tuple(changes)


def reality_to_belief_latency(event_log: EventLog) -> int:
    intervention_tick: int | None = None
    for event in event_log:
        if event.event_type == "experiment_intervention":
            intervention_tick = event.tick
            break
    if intervention_tick is None:
        raise ValueError("no reality intervention in the event log")
    for event in event_log:
        if event.event_type == "belief_updated" and event.tick > intervention_tick:
            return event.tick - intervention_tick
    raise ValueError("belief did not update after the reality intervention")


def belief_to_intent_latency(event_log: EventLog, tick: int) -> int:
    belief_tick: int | None = None
    intent_tick: int | None = None
    for event in event_log:
        if event.tick != tick:
            continue
        if event.event_type == "belief_updated" and belief_tick is None:
            belief_tick = event.tick
        if event.event_type == "action_intent" and intent_tick is None:
            intent_tick = event.tick
    if belief_tick is None or intent_tick is None:
        raise ValueError(f"tick {tick} is missing a belief or an intent")
    return intent_tick - belief_tick


def _labeled_float(lines: tuple[str, ...], label: str) -> float:
    prefix = label + "="
    found = [line[len(prefix) :] for line in lines if line.startswith(prefix)]
    if len(found) != 1:
        raise ValueError(f"expected one {label}")
    return float(found[0])
