"""PR-4：相同信念下，约束改变意图；意图不改变世界。"""

from __future__ import annotations

import unittest

from political_sim.core.actions import SPEC_ACTION_TYPES, Action
from political_sim.core.models import (
    Belief,
    Capabilities,
    Environment,
    Group,
    Individual,
    Preferences,
    RepresentationEdge,
    Representative,
    WorldState,
)
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.decision import (
    CONSTRAINT_PRECEDENCE_NOTE,
    INTENT_TYPES,
    ConstraintPolicy,
    decide,
    decision_context_from_view,
)
from political_sim.simulation.systems.information import actor_view
from tests.test_information import weighted_world


def _intent(engine: SimulationEngine, observer_id: str = "R1") -> str:
    matches = [
        event
        for event in engine.event_log
        if event.event_type == "action_intent" and event.actors == (observer_id,)
    ]
    return matches[-1].cause


class DecisionTests(unittest.TestCase):
    def test_information_quality_changes_belief_and_can_change_intent(self) -> None:
        full = SimulationEngine(weighted_world(), 0, information_quality=1.0)
        none = SimulationEngine(weighted_world(), 0, information_quality=0.0)
        full.run(1)
        none.run(1)
        self.assertEqual(full.world.individuals["I01"].preferences, none.world.individuals["I01"].preferences)
        self.assertNotEqual(
            full.world.beliefs[("R1", "G1")].estimated_preference,
            none.world.beliefs[("R1", "G1")].estimated_preference,
        )
        self.assertEqual(_intent(full), "baseline:support")
        self.assertEqual(_intent(none), "baseline:oppose")
        self.assertEqual(full.world.resources, none.world.resources)

    def test_same_belief_and_different_constraint_changes_intent_only(self) -> None:
        unconstrained = SimulationEngine(weighted_world(), 0, information_quality=1.0)
        delayed = SimulationEngine(
            weighted_world(),
            0,
            information_quality=1.0,
            decision_constraints={"R1": ("delay",)},
        )
        unconstrained.run(1)
        delayed.run(1)
        self.assertEqual(unconstrained.world.beliefs, delayed.world.beliefs)
        self.assertEqual(unconstrained.world.individuals, delayed.world.individuals)
        self.assertEqual(_intent(unconstrained), "baseline:support")
        self.assertEqual(_intent(delayed), "constraint:delay")
        intent_event = [
            event for event in delayed.event_log if event.event_type == "action_intent"
        ][-1]
        self.assertEqual(intent_event.state_change, ())
        self.assertEqual(intent_event.incentives, ())
        self.assertEqual(delayed.world.beliefs[("R1", "G1")].estimated_information, 1.0)

    def test_constraint_precedes_the_baseline_and_seek_information_precedes_delay(self) -> None:
        running = SimulationEngine(
            weighted_world(),
            0,
            information_quality=1.0,
            decision_constraints={"R1": ("delay", "seek_information")},
        )
        running.run(1)
        self.assertEqual(_intent(running), "constraint:seek_information")
        self.assertEqual(
            CONSTRAINT_PRECEDENCE_NOTE,
            "Constraint precedence defined by the current experimental specification.",
        )
        self.assertEqual(
            INTENT_TYPES,
            ("support", "oppose", "abstain", "delay", "seek_information"),
        )
        reversed_policy = ConstraintPolicy(
            "experimental-spec-reverse",
            ("delay", "abstain", "seek_information"),
        )
        reversed_run = SimulationEngine(
            weighted_world(),
            0,
            information_quality=1.0,
            decision_constraints={"R1": ("delay", "seek_information")},
            constraint_policy=reversed_policy,
        )
        reversed_run.run(1)
        self.assertEqual(_intent(reversed_run), "constraint:delay")
        self.assertEqual(running.world.beliefs, reversed_run.world.beliefs)

    def test_exact_midpoint_abstains(self) -> None:
        individual = Individual("I01", Preferences(0.5, 0.5, 0.5, 0.5, 0.5), Capabilities(0, 0, 0, 0, 0))
        edge = RepresentationEdge(
            representative_id="R1",
            represented_entity_id="G1",
            fidelity=0,
            accountability=0,
            information_up=0,
            information_down=0,
            trust=0,
            dependency=0,
            duration=0,
        )
        world = WorldState(
            individuals={"I01": individual},
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
        running = SimulationEngine(world, 0, information_quality=1.0)
        running.run(1)
        self.assertEqual(_intent(running), "baseline:abstain")

    def test_missing_or_ambiguous_beliefs_seek_information_without_averaging(self) -> None:
        absent = decision_context_from_view(actor_view(_bare_world(), "R1"))
        self.assertEqual(decide(absent).cause, "no_belief")
        self.assertIsNone(absent.perceived_preference)
        ambiguous = decision_context_from_view(actor_view(_two_belief_world(), "R1"))
        self.assertEqual(ambiguous.perception_status, "ambiguous")
        self.assertIsNone(ambiguous.perceived_preference)
        self.assertEqual(decide(ambiguous).cause, "ambiguous_beliefs")

    def test_intent_names_are_not_world_changing_actions(self) -> None:
        self.assertTrue({"abstain", "delay", "seek_information"}.isdisjoint(SPEC_ACTION_TYPES))
        running = SimulationEngine(weighted_world(), 0)
        before = running.world.individuals["I01"].preferences
        running.submit(Action("support", "R1", ("G1",)))
        running.run(1)
        self.assertEqual(running.world.individuals["I01"].preferences, before)
        accepted = [event for event in running.event_log if event.event_type == "action_accepted"]
        self.assertEqual(accepted[0].cause, "admitted")
        self.assertEqual(accepted[0].state_change, ())
        self.assertEqual(
            [event for event in running.event_log if event.event_type == "action_rejected"],
            [],
        )

    def test_decision_module_does_not_read_true_state(self) -> None:
        from pathlib import Path

        source = Path("political_sim/simulation/systems/decision.py").read_text(encoding="utf-8")
        self.assertNotIn("WorldState", source)
        self.assertNotIn("generate_observations", source)
        self.assertNotIn("mutation_scope", source)
        with self.assertRaises(TypeError):
            decision_context_from_view(weighted_world())  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            SimulationEngine(weighted_world(), 0, decision_constraints={"R1": ("vote",)})


def _bare_world() -> WorldState:
    return WorldState(
        individuals={},
        groups={},
        organizations={},
        representatives={"R1": Representative("R1")},
        factions={},
        coalitions={},
        institutions={},
        representation_edges={},
        resources={},
        networks={},
        beliefs={},
        environment=Environment(0, 0, 0, 0),
    )


def _two_belief_world() -> WorldState:
    preference = Preferences(1, 0, 0, 0, 0)
    capability = Capabilities(0, 0, 0, 0, 0)
    beliefs = {}
    for subject_id, power in (("G1", 1.0), ("G2", 0.0)):
        belief = Belief(
            observer_id="R1",
            subject_id=subject_id,
            estimated_preference=Preferences(power, power, power, power, power),
            estimated_capability=capability,
            estimated_loyalty=0.0,
            estimated_information=1.0,
        )
        beliefs[(belief.observer_id, belief.subject_id)] = belief
    return WorldState(
        individuals={},
        groups={"G1": Group("G1"), "G2": Group("G2")},
        organizations={},
        representatives={"R1": Representative("R1")},
        factions={},
        coalitions={},
        institutions={},
        representation_edges={},
        resources={},
        networks={},
        beliefs=beliefs,
        environment=Environment(0, 0, 0, 0),
    )


if __name__ == "__main__":
    unittest.main()
