"""Read-only measurement of a simulation that has already finished.

This module does not advance a tick and does not write WorldState.
"""

from __future__ import annotations

from political_sim.core.events.event_log import EventLog
from political_sim.core.models.individual import Preferences
from political_sim.core.models.world_state import WorldState


def preference_snapshot(world: WorldState) -> tuple[tuple[str, Preferences], ...]:
    return tuple(
        (individual_id, world.individuals[individual_id].preferences)
        for individual_id in world.individuals
    )


def belief_snapshot(
    world: WorldState,
) -> tuple[tuple[tuple[str, str], Preferences, float], ...]:
    rows = []
    for key in sorted(world.beliefs):
        belief = world.beliefs[key]
        rows.append((key, belief.estimated_preference, belief.estimated_information))
    return tuple(rows)


def intent_snapshot(
    event_log: EventLog,
) -> tuple[tuple[int, tuple[str, ...], tuple[str, ...], str, tuple[str, ...]], ...]:
    return tuple(
        (event.tick, event.actors, event.targets, event.cause, event.state_change)
        for event in event_log
        if event.event_type == "action_intent"
    )


def subject_payloads(
    world: WorldState, subject_id: str
) -> tuple[tuple[str, Preferences, float], ...]:
    rows = []
    for (observer_id, subject), belief in sorted(world.beliefs.items()):
        if subject == subject_id:
            rows.append((observer_id, belief.estimated_preference, belief.estimated_information))
    return tuple(rows)


def stage_snapshot(
    event_log: EventLog, event_type: str
) -> tuple[tuple[int, tuple[str, ...], tuple[str, ...], str, tuple[str, ...], tuple[str, ...]], ...]:
    return tuple(
        (
            event.tick,
            event.actors,
            event.targets,
            event.cause,
            event.available_information,
            event.state_change,
        )
        for event in event_log
        if event.event_type == event_type
    )
