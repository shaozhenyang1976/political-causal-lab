"""PR-6：生成误差和信息质量是两个独立步骤。"""

from __future__ import annotations

import unittest

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
from political_sim.core.random import SeededRandom
from political_sim.experiments.analysis import (
    belief_snapshot,
    intent_snapshot,
    preference_snapshot,
    stage_snapshot,
)
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.information import (
    GENERATION_RULE,
    aggregate_capabilities,
    aggregate_preferences,
)
from tests.test_information import weighted_world
from tests.test_transmission import chain_world


class GenerationErrorTests(unittest.TestCase):
    def test_generation_rule_is_locked(self) -> None:
        self.assertEqual(GENERATION_RULE, "G(p, e) = clamp(p - e, 0, 1)")
        with self.assertRaises(ValueError):
            SimulationEngine(chain_world(1), 0, generation_error=1.2)
        with self.assertRaises(ValueError):
            SimulationEngine(chain_world(1), 0, generation_error=-0.1)

    def test_two_thirds_splits_generation_from_quality(self) -> None:
        true = aggregate_preferences(weighted_world(), weighted_world().groups["G1"]).power
        self.assertEqual(true, (1.0 * 1.0 + 0.5 * 0.0) / 1.5)
        exact = _belief_power(weighted_world(), generation_error=0.0, information_quality=1.0)
        halved = _belief_power(weighted_world(), generation_error=0.0, information_quality=0.5)
        self.assertEqual(exact, true)
        self.assertEqual(halved, 0.5 * true)
        shifted = SimulationEngine(
            _uniform_world(0.8),
            0,
            information_quality=1.0,
            generation_error=0.2,
        )
        before = preference_snapshot(shifted.world)
        shifted.run(1)
        generated_power = min(1.0, max(0.0, 0.8 - 0.2))
        self.assertEqual(preference_snapshot(shifted.world), before)
        self.assertEqual(shifted.world.individuals["I01"].preferences.power, 0.8)
        self.assertEqual(
            shifted.world.beliefs[("R1", "G1")].estimated_preference.power,
            generated_power,
        )
        self.assertNotEqual(generated_power, 0.8)
        self.assertEqual(shifted.world.beliefs[("R1", "G1")].estimated_information, 1.0)
        generated = stage_snapshot(shifted.event_log, "signal_generated")[0]
        self.assertEqual(generated[3], "generation")
        self.assertEqual(generated[5], ())
        self.assertIn(f"generated_preference.power={generated_power!r}", generated[4])
        self.assertNotIn("true_", " ".join(generated[4]))
        self.assertNotIn("0.8", " ".join(generated[4]))

    def test_quality_does_not_change_the_generated_signal_or_repair_it(self) -> None:
        matrix = {}
        for error, quality in ((0.0, 1.0), (0.0, 0.5), (0.25, 1.0), (0.25, 0.5)):
            running = SimulationEngine(
                chain_world(1),
                0,
                information_quality=quality,
                generation_error=error,
            )
            reality = preference_snapshot(running.world)
            running.run(1)
            matrix[(error, quality)] = running
            self.assertEqual(preference_snapshot(running.world), reality)
            self.assertEqual(
                running.world.beliefs[("R1", "G1")].estimated_preference.power,
                quality * (1.0 - error),
            )
            self.assertEqual(
                running.world.beliefs[("R1", "G1")].estimated_information,
                quality,
            )
        self.assertEqual(
            stage_snapshot(matrix[(0.25, 1.0)].event_log, "signal_generated"),
            stage_snapshot(matrix[(0.25, 0.5)].event_log, "signal_generated"),
        )
        self.assertEqual(
            stage_snapshot(matrix[(0.0, 1.0)].event_log, "signal_generated"),
            stage_snapshot(matrix[(0.0, 0.5)].event_log, "signal_generated"),
        )
        self.assertNotEqual(
            stage_snapshot(matrix[(0.0, 1.0)].event_log, "signal_generated"),
            stage_snapshot(matrix[(0.25, 1.0)].event_log, "signal_generated"),
        )
        self.assertEqual(matrix[(0.25, 1.0)].world.beliefs[("R1", "G1")].estimated_preference.power, 0.75)
        self.assertNotEqual(
            matrix[(0.25, 1.0)].world.beliefs[("R1", "G1")].estimated_preference.power,
            1.0,
        )
        self.assertEqual(matrix[(0.25, 0.5)].world.beliefs[("R1", "G1")].estimated_preference.power, 0.375)
        self.assertEqual(_intent(matrix[(0.0, 1.0)]), "baseline:support")
        self.assertEqual(_intent(matrix[(0.0, 0.5)]), "baseline:abstain")
        self.assertEqual(_intent(matrix[(0.25, 1.0)]), "baseline:support")
        self.assertEqual(_intent(matrix[(0.25, 0.5)]), "baseline:oppose")

    def test_error_does_not_move_capabilities_or_reality(self) -> None:
        world = weighted_world()
        true_capability = aggregate_capabilities(world, world.groups["G1"])
        true_preference = aggregate_preferences(world, world.groups["G1"])
        running = SimulationEngine(world, 0, information_quality=1.0, generation_error=0.25)
        running.run(1)
        belief = running.world.beliefs[("R1", "G1")]
        self.assertEqual(belief.estimated_capability, true_capability)
        self.assertEqual(running.world.individuals["I01"].preferences.power, 1.0)
        self.assertEqual(
            belief.estimated_preference.power,
            min(1.0, max(0.0, true_preference.power - 0.25)),
        )
        self.assertNotEqual(belief.estimated_preference.power, true_preference.power)

    def test_hops_copy_the_first_transmitted_signal(self) -> None:
        running = SimulationEngine(
            chain_world(4),
            0,
            information_quality=0.5,
            generation_error=0.25,
        )
        running.run(1)
        generated = stage_snapshot(running.event_log, "signal_generated")
        self.assertEqual([record[1] for record in generated], [("R1",)])
        self.assertIn("generated_preference.power=0.75", generated[0][4])
        for observer_id in ("R1", "R2", "R3", "R4"):
            belief = running.world.beliefs[(observer_id, "G1")]
            self.assertEqual(belief.estimated_preference.power, 0.375)
            self.assertEqual(belief.estimated_information, 0.5)
        forwarded = stage_snapshot(running.event_log, "belief_updated")
        self.assertEqual(forwarded[-1][1], ("R4",))
        self.assertEqual(forwarded[-1][3], "information_forward")
        self.assertIn("received_preference.power=0.375", forwarded[-1][4])
        self.assertNotIn("0.75", " ".join(forwarded[-1][4]))
        types = [event.event_type for event in running.event_log]
        self.assertLess(types.index("signal_generated"), types.index("belief_updated"))
        self.assertLess(types.index("belief_updated"), types.index("action_intent"))
        self.assertEqual(running.rng.random(), SeededRandom(0).random())

    def test_intent_changes_only_through_belief_or_constraint(self) -> None:
        plain = SimulationEngine(chain_world(1), 0, information_quality=1.0, generation_error=0.25)
        delayed = SimulationEngine(
            chain_world(1),
            0,
            information_quality=1.0,
            generation_error=0.25,
            decision_constraints={"R1": ("delay",)},
        )
        larger_error = SimulationEngine(
            chain_world(1),
            0,
            information_quality=1.0,
            generation_error=0.5,
        )
        plain.run(1)
        delayed.run(1)
        larger_error.run(1)
        self.assertEqual(preference_snapshot(plain.world), preference_snapshot(delayed.world))
        self.assertEqual(preference_snapshot(plain.world), preference_snapshot(larger_error.world))
        self.assertEqual(belief_snapshot(plain.world), belief_snapshot(delayed.world))
        self.assertEqual(
            stage_snapshot(plain.event_log, "signal_generated"),
            stage_snapshot(delayed.event_log, "signal_generated"),
        )
        self.assertNotEqual(belief_snapshot(plain.world), belief_snapshot(larger_error.world))
        self.assertEqual(_intent(plain), "baseline:support")
        self.assertEqual(_intent(delayed), "constraint:delay")
        self.assertEqual(_intent(larger_error), "baseline:abstain")
        self.assertTrue(all(record[4] == () for record in intent_snapshot(plain.event_log)))

    def test_generation_clamps_and_does_not_restore_truth(self) -> None:
        running = SimulationEngine(
            _uniform_world(0.2),
            0,
            information_quality=1.0,
            generation_error=0.5,
        )
        running.run(1)
        self.assertEqual(running.world.individuals["I01"].preferences.power, 0.2)
        self.assertEqual(running.world.beliefs[("R1", "G1")].estimated_preference.power, 0.0)


def _belief_power(world: WorldState, **kwargs: float) -> float:
    running = SimulationEngine(world, 0, **kwargs)
    running.run(1)
    return running.world.beliefs[("R1", "G1")].estimated_preference.power


def _intent(engine: SimulationEngine) -> str:
    matches = [event for event in engine.event_log if event.event_type == "action_intent"]
    return matches[-1].cause


def _uniform_world(power: float) -> WorldState:
    edge = RepresentationEdge("R1", "G1", 0, 0, 0, 0, 0, 0, 0)
    return WorldState(
        individuals={
            "I01": Individual(
                "I01",
                Preferences(power, power, power, power, power),
                Capabilities(0, 0, 0, 0, 0),
            )
        },
        groups={"G1": Group("G1", ("I01",))},
        organizations={},
        representatives={"R1": Representative("R1")},
        factions={},
        coalitions={},
        institutions={},
        representation_edges={("R1", "G1"): edge},
        resources={},
        networks={},
        beliefs={},
        environment=Environment(0, 0, 0, 0),
    )


if __name__ == "__main__":
    unittest.main()
