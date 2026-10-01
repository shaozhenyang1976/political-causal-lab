"""五个架构不变量。它们约束以后的机制，而不是增加政治规则。"""

from __future__ import annotations

import inspect
import unittest

from political_sim.core.actions.action_resolver import ActionResolver
from political_sim.core.models.individual import PREFERENCE_FIELDS
from political_sim.core.mutation import (
    CONSTITUTION,
    DECISION_BOUNDARY,
    EVENT_BOUNDARY,
    INFORMATION_BOUNDARY,
    STATE_MUTATION_BOUNDARY,
    DirectMutationError,
)
from political_sim.scenarios.sandbox import ScenarioGenerator
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.decision import decide
from political_sim.simulation.systems.information import (
    actor_view,
    aggregate_preferences,
    preference_distance,
    require_actor_view,
)
from tests.test_information import weighted_world


class InvariantTests(unittest.TestCase):
    def test_i01_reality_isolation(self) -> None:
        running = SimulationEngine(weighted_world(), 0, information_quality=1.0)
        running.run(1)
        old_belief = running.world.beliefs[("R1", "G1")].estimated_preference.power
        old_true = running.world.individuals["I01"].preferences.power
        running.intervene_preference("I01", "power", 0.0)
        self.assertNotEqual(running.world.individuals["I01"].preferences.power, old_true)
        self.assertEqual(running.world.beliefs[("R1", "G1")].estimated_preference.power, old_belief)

    def test_i02_information_degradation(self) -> None:
        def error(quality: float) -> float:
            running = SimulationEngine(weighted_world(), 0, information_quality=quality)
            running.run(1)
            true_preference = aggregate_preferences(running.world, running.world.groups["G1"])
            estimated = running.world.beliefs[("R1", "G1")].estimated_preference
            return preference_distance(true_preference, estimated)

        baseline = error(0.5)
        self.assertGreaterEqual(error(0.2), baseline)
        self.assertLessEqual(error(0.8), baseline)

    def test_i03_information_boundary(self) -> None:
        self.assertEqual(INFORMATION_BOUNDARY, "No actor may directly observe WorldState.")
        self.assertEqual(
            DECISION_BOUNDARY,
            "Actor decisions must be based only on permitted ActorView / DecisionContext.",
        )
        self.assertEqual(
            STATE_MUTATION_BOUNDARY,
            "WorldState may only be mutated through ActionResolver.",
        )
        self.assertEqual(
            EVENT_BOUNDARY,
            "Every accepted state mutation must produce an EventLog entry.",
        )
        running = SimulationEngine(weighted_world(), 0, information_quality=0.5)
        running.run(1)
        view = require_actor_view(actor_view(running.world, "R1"))
        self.assertFalse(hasattr(view, "world"))
        self.assertFalse(hasattr(view, "individuals"))
        with self.assertRaises(TypeError):
            require_actor_view(running.world)
        with self.assertRaises(TypeError):
            decide(running.world)  # type: ignore[arg-type]

    def test_i04_determinism(self) -> None:
        def once() -> tuple[object, tuple[object, ...]]:
            running = SimulationEngine(
                ScenarioGenerator().generate(11),
                11,
                information_quality=0.55,
            )
            running.run(2)
            return running.world, running.event_log.as_tuple()

        self.assertEqual(once(), once())

    def test_i05_event_sourcing(self) -> None:
        self.assertEqual(
            CONSTITUTION,
            "WorldState is mutable only through authorized state transitions.",
        )
        fresh = ScenarioGenerator().generate(2)
        running = SimulationEngine(ScenarioGenerator().generate(2), 2)
        running.run(1)
        for individual_id in fresh.individuals:
            self.assertEqual(
                running.world.individuals[individual_id].preferences,
                fresh.individuals[individual_id].preferences,
            )
        self.assertTrue(any(event.event_type == "belief_updated" for event in running.event_log))
        self.assertTrue(any(event.event_type == "action_intent" for event in running.event_log))
        for event in running.event_log:
            if event.event_type == "action_intent":
                self.assertEqual(event.state_change, ())
                self.assertEqual(event.incentives, ())
        running.intervene_preference("I01", "security", 0.0)
        interventions = [
            event for event in running.event_log if event.event_type == "experiment_intervention"
        ]
        self.assertEqual(len(interventions), 1)
        self.assertEqual(
            interventions[0].state_change,
            ("I01.preferences.security=0.0",),
        )
        self.assertNotIn("mutation_scope", inspect.getsource(ActionResolver.record_intent))
        with self.assertRaises(DirectMutationError):
            running.world.individuals["I01"].preferences.security = 1.0
        self.assertIn("power", PREFERENCE_FIELDS)


if __name__ == "__main__":
    unittest.main()
