"""PR-3：真实状态、传递质量和信念。"""

from __future__ import annotations

import unittest
from pathlib import Path

from political_sim.core.models import (
    Capabilities,
    Environment,
    Group,
    Individual,
    Preferences,
    RepresentationEdge,
    Representative,
    WorldState,
)
from political_sim.core.mutation import CONSTITUTION
from political_sim.core.random import SeededRandom
from political_sim.scenarios.sandbox import ScenarioGenerator
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.information import (
    GroupObservation,
    actor_view,
    aggregate_preferences,
    preference_distance,
    require_actor_view,
    signal_record,
    transmit,
)
from political_sim.simulation.tick_processor import TICK_PHASES, TickProcessor

ROOT = Path(__file__).resolve().parents[1]


def _edge(information_up: float, represented_id: str = "G1") -> RepresentationEdge:
    return RepresentationEdge(
        representative_id="R1",
        represented_entity_id=represented_id,
        fidelity=0.2,
        accountability=0.2,
        information_up=information_up,
        information_down=0.2,
        trust=0.2,
        dependency=0.2,
        duration=0,
    )


def weighted_world(information_up: float = 0.2) -> WorldState:
    return WorldState(
        individuals={
            "I01": Individual(
                "I01",
                Preferences(1, 1, 1, 1, 1),
                Capabilities(0, 0, 1, 0, 0),
            ),
            "I02": Individual(
                "I02",
                Preferences(0, 0, 0, 0, 0),
                Capabilities(0, 0, 0, 0, 0),
            ),
        },
        groups={"G1": Group("G1", ("I01", "I02"))},
        organizations={},
        representatives={"R1": Representative("R1")},
        factions={},
        coalitions={},
        institutions={},
        representation_edges={("R1", "G1"): _edge(information_up)},
        resources={},
        networks={},
        beliefs={},
        environment=Environment(0, 0, 0, 0),
    )


class InformationBeliefTests(unittest.TestCase):
    def test_constitution_and_tick_slots(self) -> None:
        self.assertEqual(
            CONSTITUTION,
            "WorldState is mutable only through authorized state transitions.",
        )
        self.assertEqual(len(TICK_PHASES), 17)
        self.assertEqual(
            TICK_PHASES,
            (
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
            ),
        )
        self.assertEqual(tuple(TickProcessor().phases), TICK_PHASES)

    def test_same_seed_reproduces_world_and_belief(self) -> None:
        first = SimulationEngine(ScenarioGenerator().generate(3), 3, information_quality=0.6)
        second = SimulationEngine(ScenarioGenerator().generate(3), 3, information_quality=0.6)
        first.run(4)
        second.run(4)
        self.assertEqual(first.world, second.world)
        self.assertEqual(first.event_log, second.event_log)
        self.assertEqual(set(first.world.beliefs), {("R1", "G1"), ("R2", "G2"), ("R3", "G3"), ("R4", "G4")})

    def test_lower_information_quality_increases_belief_error(self) -> None:
        perfect = SimulationEngine(weighted_world(), 0, information_quality=1.0)
        high = SimulationEngine(weighted_world(), 0, information_quality=0.8)
        low = SimulationEngine(weighted_world(), 0, information_quality=0.2)
        perfect.run(1)
        high.run(1)
        low.run(1)
        true_preference = aggregate_preferences(perfect.world, perfect.world.groups["G1"])
        expected = (1.0 * 1.0 + 0.5 * 0.0) / 1.5
        self.assertEqual(true_preference.power, expected)
        self.assertNotEqual(true_preference.power, 0.5)
        perfect_belief = perfect.world.beliefs[("R1", "G1")].estimated_preference
        high_belief = high.world.beliefs[("R1", "G1")].estimated_preference
        low_belief = low.world.beliefs[("R1", "G1")].estimated_preference
        self.assertEqual(preference_distance(true_preference, perfect_belief), 0.0)
        self.assertGreater(
            preference_distance(true_preference, low_belief),
            preference_distance(true_preference, high_belief),
        )
        self.assertGreater(preference_distance(true_preference, high_belief), 0.0)
        self.assertEqual(low.world.individuals["I01"].preferences.power, 1.0)
        self.assertEqual(low.world.representation_edges[("R1", "G1")].information_up, 0.2)

    def test_edge_field_is_not_the_transmission_quality(self) -> None:
        low_edge = SimulationEngine(weighted_world(0.1), 0, information_quality=0.4)
        high_edge = SimulationEngine(weighted_world(0.9), 0, information_quality=0.4)
        low_edge.run(1)
        high_edge.run(1)
        self.assertEqual(
            low_edge.world.beliefs[("R1", "G1")].estimated_preference,
            high_edge.world.beliefs[("R1", "G1")].estimated_preference,
        )

    def test_true_state_can_move_without_updating_belief(self) -> None:
        running = SimulationEngine(weighted_world(), 0, information_quality=1.0)
        running.run(1)
        before = actor_view(running.world, "R1")
        running.intervene_preference("I01", "power", 0.0)
        after = actor_view(running.world, "R1")
        self.assertEqual(before, after)
        true_preference = aggregate_preferences(running.world, running.world.groups["G1"])
        self.assertNotEqual(
            true_preference.power,
            after.beliefs[0].estimated_preference.power,
        )
        self.assertEqual(running.event_log[-1].event_type, "experiment_intervention")
        self.assertEqual(running.event_log[-1].available_information, ())
        self.assertEqual(running.event_log[-1].incentives, ())

    def test_actor_view_hides_true_state(self) -> None:
        running = SimulationEngine(weighted_world(), 0, information_quality=0.5)
        running.run(1)
        view = require_actor_view(actor_view(running.world, "R1"))
        self.assertEqual(view.observer_id, "R1")
        self.assertEqual(view.beliefs[0].subject_id, "G1")
        self.assertFalse(hasattr(view, "individuals"))
        self.assertFalse(hasattr(view, "groups"))
        self.assertFalse(hasattr(view, "world"))
        with self.assertRaises(TypeError):
            require_actor_view(running.world)

    def test_event_records_received_signal_only(self) -> None:
        observation = GroupObservation(
            observer_id="R1",
            subject_id="G1",
            preference=Preferences(1, 1, 1, 1, 1),
            capability=Capabilities(0, 0, 0, 0, 0),
        )
        received, changed = signal_record(transmit(observation, 0.5))
        text = " ".join(received + changed)
        self.assertIn("received_preference.power=0.5", text)
        self.assertNotIn("1.0", text)
        self.assertNotIn("true_", text)

    def test_non_group_edges_do_not_invent_beliefs(self) -> None:
        individual = Individual("I01", Preferences(1, 0, 0, 0, 0), Capabilities(0, 0, 0, 0, 0))
        world = WorldState(
            individuals={"I01": individual},
            groups={},
            organizations={},
            representatives={"R1": Representative("R1")},
            factions={},
            coalitions={},
            institutions={},
            representation_edges={("R1", "I01"): _edge(0.4, "I01")},
            resources={},
            networks={},
            beliefs={},
            environment=Environment(0, 0, 0, 0),
        )
        running = SimulationEngine(world, 0, information_quality=0.3)
        running.run(1)
        self.assertEqual(running.world.beliefs, {})

    def test_simulation_stream_stays_independent(self) -> None:
        running = SimulationEngine(ScenarioGenerator().generate(7), 7, information_quality=0.3)
        running.run(10)
        self.assertEqual(running.rng.random(), SeededRandom(7).random())

    def test_information_quality_bounds_and_system_does_not_write_world(self) -> None:
        with self.assertRaises(ValueError):
            SimulationEngine(weighted_world(), 0, information_quality=1.2)
        source = (ROOT / "political_sim" / "simulation" / "systems" / "information.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("mutation_scope", source)
        self.assertNotIn(".beliefs[", source)


if __name__ == "__main__":
    unittest.main()
