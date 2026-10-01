"""四组基线。只重复已有链条，不加入新的信息传递机制。"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.models import (
    Capabilities,
    Environment,
    Group,
    Individual,
    NetworkLink,
    Preferences,
    RepresentationEdge,
    Representative,
    WorldState,
    network_link_key,
)
from political_sim.experiments.analysis.baseline import (
    ActorTick,
    ErrorDecomposition,
    decompose,
    reconstruct,
)
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.decision import (
    EXPERIMENTAL_CONSTRAINT_POLICY,
    ConstraintPolicy,
)
from political_sim.simulation.systems.information import (
    INFORMATION_FORWARD,
    aggregate_preferences,
    preference_distance,
)

BASELINE_ERRORS = (0.0, 0.1, 0.25, 0.5)
BASELINE_QUALITIES = (1.0, 0.75, 0.5, 0.0)
BASELINE_HOPS = (1, 2, 3, 4)


@dataclass(frozen=True)
class BaselinePoint:
    generation_error: float
    information_quality: float
    hops: int
    policy_name: str
    intent_cause: str
    estimated_information: float
    decomposition: ErrorDecomposition
    trace: ActorTick


def generation_baseline() -> tuple[BaselinePoint, ...]:
    return tuple(_point(hops=1, error=error, quality=1.0) for error in BASELINE_ERRORS)


def quality_baseline() -> tuple[BaselinePoint, ...]:
    return tuple(_point(hops=1, error=0.0, quality=quality) for quality in BASELINE_QUALITIES)


def hop_baseline() -> tuple[BaselinePoint, ...]:
    return tuple(_point(hops=hops, error=0.25, quality=0.5) for hops in BASELINE_HOPS)


def constraint_baseline() -> tuple[BaselinePoint, ...]:
    delay_first = ConstraintPolicy(
        "baseline-delay-first",
        ("delay", "abstain", "seek_information"),
    )
    shared = {"R1": ("delay", "seek_information")}
    return (
        _point(
            hops=1,
            error=0.0,
            quality=1.0,
            constraints=shared,
            policy=EXPERIMENTAL_CONSTRAINT_POLICY,
        ),
        _point(hops=1, error=0.0, quality=1.0, constraints=shared, policy=delay_first),
    )


def _point(
    *,
    hops: int,
    error: float,
    quality: float,
    constraints: dict[str, tuple[str, ...]] | None = None,
    policy: ConstraintPolicy = EXPERIMENTAL_CONSTRAINT_POLICY,
) -> BaselinePoint:
    world = _preference_chain(hops)
    reality = aggregate_preferences(world, world.groups["G1"])
    running = SimulationEngine(
        world,
        0,
        information_quality=quality,
        generation_error=error,
        decision_constraints=constraints,
        constraint_policy=policy,
    )
    running.run(1)
    records = reconstruct(running.event_log)
    direct = _one(records, "R1")
    if direct.generated is None or direct.received is None or direct.intent_cause is None:
        raise ValueError("R1 is missing a generation, belief, or intent event")
    stored = running.world.beliefs[("R1", "G1")].estimated_preference
    transmission_gap = preference_distance(direct.received, stored)
    for record in records:
        if record.received is None:
            continue
        transmission_gap = max(transmission_gap, preference_distance(direct.received, record.received))
    parts = decompose(reality, direct.generated, direct.received, stored)
    return BaselinePoint(
        generation_error=error,
        information_quality=quality,
        hops=hops,
        policy_name=policy.name,
        intent_cause=direct.intent_cause,
        estimated_information=running.world.beliefs[("R1", "G1")].estimated_information,
        decomposition=ErrorDecomposition(
            parts.generation_gap,
            parts.quality_gap,
            transmission_gap,
            parts.belief_gap,
        ),
        trace=direct,
    )


def _one(records: tuple[ActorTick, ...], actor_id: str) -> ActorTick:
    matches = [record for record in records if record.actor_id == actor_id]
    if len(matches) != 1:
        raise ValueError(f"expected one trace for {actor_id}")
    return matches[0]


def _preference_chain(hops: int) -> WorldState:
    representatives = {f"R{index}": Representative(f"R{index}") for index in range(1, hops + 1)}
    links = {}
    for index in range(1, hops):
        link = NetworkLink(f"R{index}", f"R{index + 1}", INFORMATION_FORWARD)
        links[network_link_key(link)] = link
    edge = RepresentationEdge("R1", "G1", 0, 0, 0, 0, 0, 0, 0)
    return WorldState(
        individuals={
            "I01": Individual("I01", Preferences(1, 1, 1, 1, 1), Capabilities(0, 0, 0, 0, 0))
        },
        groups={"G1": Group("G1", ("I01",))},
        organizations={},
        representatives=representatives,
        factions={},
        coalitions={},
        institutions={},
        representation_edges={("R1", "G1"): edge},
        resources={},
        networks=links,
        beliefs={},
        environment=Environment(0, 0, 0, 0),
    )
