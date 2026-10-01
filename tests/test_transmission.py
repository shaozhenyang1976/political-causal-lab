"""PR-5：无噪声多层传递。层数增加，内容不变。"""

from __future__ import annotations

import unittest

from political_sim.core.actions.action_resolver import ActionResolver
from political_sim.core.events.event_log import EventLog
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
from political_sim.core.random import SeededRandom
from political_sim.scenarios.sandbox import ScenarioGenerator
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.decision import EXPERIMENTAL_CONSTRAINT_POLICY
from political_sim.simulation.systems.information import (
    INFORMATION_FORWARD,
    GroupObservation,
    deliver,
)
from political_sim.simulation.tick_processor import (
    _belief_update,
    _information_transmission,
    _representative_decision,
    _TickContext,
)


def _edge(representative_id: str, fidelity: float) -> RepresentationEdge:
    return RepresentationEdge(
        representative_id=representative_id,
        represented_entity_id="G1",
        fidelity=fidelity,
        accountability=0.0,
        information_up=0.0,
        information_down=0.0,
        trust=0.0,
        dependency=0.0,
        duration=0,
    )


def chain_world(
    depth: int,
    fidelity: float = 0.0,
    resources: dict[str, float] | None = None,
) -> WorldState:
    representatives = {
        f"R{index}": Representative(f"R{index}") for index in range(1, depth + 1)
    }
    links = {}
    for index in range(1, depth):
        link = NetworkLink(
            source_id=f"R{index}",
            target_id=f"R{index + 1}",
            kind=INFORMATION_FORWARD,
        )
        links[network_link_key(link)] = link
    return WorldState(
        individuals={
            "I01": Individual(
                "I01",
                Preferences(1, 1, 1, 1, 1),
                Capabilities(0, 0, 0, 0, 0),
            )
        },
        groups={"G1": Group("G1", ("I01",))},
        organizations={},
        representatives=representatives,
        factions={},
        coalitions={},
        institutions={},
        representation_edges={("R1", "G1"): _edge("R1", fidelity)},
        resources={} if resources is None else resources,
        networks=links,
        beliefs={},
        environment=Environment(0, 0, 0, 0),
    )


class TransmissionTests(unittest.TestCase):
    def test_extra_hops_copy_the_same_payload(self) -> None:
        shallow = SimulationEngine(chain_world(1), 0, information_quality=0.5)
        deep = SimulationEngine(chain_world(4, fidelity=0.9), 0, information_quality=0.5)
        other_edge = SimulationEngine(chain_world(4, fidelity=0.1), 0, information_quality=0.5)
        shallow.run(1)
        deep.run(1)
        other_edge.run(1)
        direct = shallow.world.beliefs[("R1", "G1")]
        self.assertEqual(direct.estimated_preference.power, 0.5)
        self.assertEqual(direct.estimated_information, 0.5)
        for observer_id in ("R1", "R2", "R3", "R4"):
            belief = deep.world.beliefs[(observer_id, "G1")]
            self.assertEqual(belief.estimated_preference, direct.estimated_preference)
            self.assertEqual(belief.estimated_capability, direct.estimated_capability)
            self.assertEqual(belief.estimated_information, direct.estimated_information)
            self.assertEqual(
                other_edge.world.beliefs[(observer_id, "G1")].estimated_preference,
                belief.estimated_preference,
            )
        self.assertEqual(deep.world.individuals["I01"].preferences.power, 1.0)
        self.assertEqual(deep.rng.random(), SeededRandom(0).random())
        causes = {
            event.actors[0]: event.cause
            for event in deep.event_log
            if event.event_type == "belief_updated"
        }
        self.assertEqual(causes["R1"], "information_transmission")
        self.assertEqual(causes["R4"], "information_forward")
        forwarded = [
            event
            for event in deep.event_log
            if event.event_type == "belief_updated" and event.actors == ("R4",)
        ]
        self.assertNotIn("1.0", " ".join(forwarded[0].available_information))

    def test_structural_links_do_not_forward(self) -> None:
        world = chain_world(2)
        membership = NetworkLink("R1", "R2", "organization_membership")
        world_links = {
            network_link_key(membership): membership,
        }
        bare = WorldState(
            individuals=dict(world.individuals),
            groups=dict(world.groups),
            organizations={},
            representatives=dict(world.representatives),
            factions={},
            coalitions={},
            institutions={},
            representation_edges=dict(world.representation_edges),
            resources={},
            networks=world_links,
            beliefs={},
            environment=Environment(0, 0, 0, 0),
        )
        running = SimulationEngine(bare, 0, information_quality=1.0)
        running.run(1)
        self.assertEqual(set(running.world.beliefs), {("R1", "G1")})

    def test_sandbox_stays_one_hop(self) -> None:
        running = SimulationEngine(ScenarioGenerator().generate(5), 5, information_quality=1.0)
        running.run(1)
        self.assertEqual(
            set(running.world.beliefs),
            {("R1", "G1"), ("R2", "G2"), ("R3", "G3"), ("R4", "G4")},
        )

    def test_two_beliefs_are_not_averaged(self) -> None:
        edge_one = RepresentationEdge(
            "R1", "G1", 0, 0, 0, 0, 0, 0, 0
        )
        edge_two = RepresentationEdge(
            "R2", "G2", 0, 0, 0, 0, 0, 0, 0
        )
        link = NetworkLink("R2", "R1", INFORMATION_FORWARD)
        world = WorldState(
            individuals={
                "I01": Individual("I01", Preferences(1, 1, 1, 1, 1), Capabilities(0, 0, 0, 0, 0)),
                "I02": Individual("I02", Preferences(0, 0, 0, 0, 0), Capabilities(0, 0, 0, 0, 0)),
            },
            groups={"G1": Group("G1", ("I01",)), "G2": Group("G2", ("I02",))},
            organizations={},
            representatives={"R1": Representative("R1"), "R2": Representative("R2")},
            factions={},
            coalitions={},
            institutions={},
            representation_edges={("R1", "G1"): edge_one, ("R2", "G2"): edge_two},
            resources={},
            networks={network_link_key(link): link},
            beliefs={},
            environment=Environment(0, 0, 0, 0),
        )
        running = SimulationEngine(world, 0, information_quality=1.0)
        running.run(1)
        self.assertEqual(running.world.beliefs[("R1", "G1")].estimated_preference.power, 1.0)
        self.assertEqual(running.world.beliefs[("R1", "G2")].estimated_preference.power, 0.0)
        self.assertNotIn(("R1", "G1+G2"), running.world.beliefs)
        intent = [
            event
            for event in running.event_log
            if event.event_type == "action_intent" and event.actors == ("R1",)
        ][-1]
        self.assertEqual(intent.cause, "ambiguous_beliefs")
        self.assertEqual(running.world.individuals["I01"].preferences.power, 1.0)
        self.assertEqual(running.world.individuals["I02"].preferences.power, 0.0)

    def test_conflicting_payloads_are_dropped_instead_of_averaged(self) -> None:
        link_one = NetworkLink("R1", "C", INFORMATION_FORWARD)
        link_two = NetworkLink("R2", "C", INFORMATION_FORWARD)
        world = WorldState(
            individuals={},
            groups={"G1": Group("G1")},
            organizations={},
            representatives={
                "R1": Representative("R1"),
                "R2": Representative("R2"),
                "C": Representative("C"),
            },
            factions={},
            coalitions={},
            institutions={},
            representation_edges={},
            resources={},
            networks={
                network_link_key(link_one): link_one,
                network_link_key(link_two): link_two,
            },
            beliefs={},
            environment=Environment(0, 0, 0, 0),
        )
        context = _TickContext(
            tick=1,
            world=world,
            actions=(),
            resolver=ActionResolver(),
            events=EventLog(),
            rng=SeededRandom(0),
            information_quality=1.0,
            generation_error=0.0,
            trust=1.0,
            trust_threshold=0.5,
            fidelity=1.0,
            decision_constraints={},
            constraint_policy=EXPERIMENTAL_CONSTRAINT_POLICY,
        )
        zeros = Capabilities(0, 0, 0, 0, 0)
        context.observations = (
            GroupObservation("R1", "G1", Preferences(1, 1, 1, 1, 1), zeros),
            GroupObservation("R2", "G1", Preferences(0, 0, 0, 0, 0), zeros),
        )
        _information_transmission(context)
        _belief_update(context)
        _representative_decision(context)
        self.assertEqual(set(world.beliefs), {("R1", "G1"), ("R2", "G1")})
        self.assertNotEqual(
            world.beliefs[("R1", "G1")].estimated_preference.power,
            world.beliefs[("R2", "G1")].estimated_preference.power,
        )
        ambiguous = [
            event for event in context.events if event.event_type == "transmission_ambiguous"
        ]
        self.assertEqual(len(ambiguous), 1)
        self.assertEqual(ambiguous[0].actors, ("C",))
        self.assertEqual(ambiguous[0].targets, ("G1",))
        self.assertEqual(ambiguous[0].available_information, ())
        self.assertEqual(ambiguous[0].state_change, ())
        intents = [
            event for event in context.events if event.event_type == "action_intent" and event.actors == ("C",)
        ]
        self.assertEqual(intents[0].cause, "no_belief")
        delivered, conflicts = deliver(context.observations, 1.0, tuple(world.networks.values()))
        self.assertEqual(conflicts, (("C", "G1"),))
        self.assertNotIn("C", {signal.observer_id for signal, _cause in delivered})


if __name__ == "__main__":
    unittest.main()
