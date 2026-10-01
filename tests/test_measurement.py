"""Causal-chain measurement. Reads one finished run and separates reality, information, belief, and intent."""

from __future__ import annotations

import unittest

from political_sim.core.models.belief import Belief
from political_sim.experiments.analysis import (
    belief_snapshot,
    intent_snapshot,
    preference_snapshot,
    subject_payloads,
)
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.decision import (
    INTENT_TYPES,
    DecisionContext,
)
from political_sim.simulation.systems.information import ActorView, TransmittedSignal
from tests.test_information import weighted_world
from tests.test_transmission import chain_world


class MeasurementTests(unittest.TestCase):
    def test_information_changes_belief_and_intent_without_changing_reality(self) -> None:
        full = SimulationEngine(weighted_world(), 4, information_quality=1.0)
        none = SimulationEngine(weighted_world(), 4, information_quality=0.0)
        before = preference_snapshot(full.world)
        full.run(1)
        none.run(1)
        self.assertEqual(preference_snapshot(full.world), before)
        self.assertEqual(preference_snapshot(none.world), before)
        self.assertNotEqual(belief_snapshot(full.world), belief_snapshot(none.world))
        full_intents = intent_snapshot(full.event_log)
        none_intents = intent_snapshot(none.event_log)
        self.assertEqual(full_intents[0][3], "baseline:support")
        self.assertEqual(none_intents[0][3], "baseline:oppose")
        self.assertTrue(all(record[4] == () for record in full_intents + none_intents))

    def test_constraint_changes_intent_without_changing_belief(self) -> None:
        plain = SimulationEngine(weighted_world(), 4, information_quality=1.0)
        delayed = SimulationEngine(
            weighted_world(),
            4,
            information_quality=1.0,
            decision_constraints={"R1": ("delay",)},
        )
        plain.run(1)
        delayed.run(1)
        self.assertEqual(preference_snapshot(plain.world), preference_snapshot(delayed.world))
        self.assertEqual(belief_snapshot(plain.world), belief_snapshot(delayed.world))
        plain_cause = next(record[3] for record in intent_snapshot(plain.event_log) if record[1] == ("R1",))
        delayed_cause = next(
            record[3] for record in intent_snapshot(delayed.event_log) if record[1] == ("R1",)
        )
        self.assertEqual(plain_cause, "baseline:support")
        self.assertEqual(delayed_cause, "constraint:delay")

    def test_hop_count_does_not_change_payload_or_world(self) -> None:
        runs = []
        for depth in (1, 2, 3, 4):
            running = SimulationEngine(chain_world(depth), 1, information_quality=0.5)
            before = preference_snapshot(running.world)
            running.run(1)
            self.assertEqual(preference_snapshot(running.world), before)
            runs.append(running)
        reference = subject_payloads(runs[0].world, "G1")[0][1:]
        for running in runs:
            payloads = subject_payloads(running.world, "G1")
            self.assertTrue(all(payload[1:] == reference for payload in payloads))
            causes = {record[3] for record in intent_snapshot(running.event_log)}
            self.assertEqual(causes, {"baseline:abstain"})
        self.assertEqual(len(subject_payloads(runs[-1].world, "G1")), 4)

    def test_frozen_layer_interfaces(self) -> None:
        self.assertEqual(
            tuple(ActorView.__dataclass_fields__),
            ("observer_id", "beliefs"),
        )
        self.assertEqual(
            tuple(TransmittedSignal.__dataclass_fields__),
            (
                "observer_id",
                "subject_id",
                "preference",
                "capability",
                "information_quality",
            ),
        )
        self.assertEqual(
            tuple(Belief.__dataclass_fields__),
            (
                "observer_id",
                "subject_id",
                "estimated_preference",
                "estimated_capability",
                "estimated_loyalty",
                "estimated_information",
            ),
        )
        self.assertEqual(
            tuple(DecisionContext.__dataclass_fields__),
            (
                "observer_id",
                "subject_id",
                "perceived_preference",
                "belief_confidence",
                "available_information",
                "known_constraints",
                "perception_status",
            ),
        )
        self.assertEqual(
            INTENT_TYPES,
            ("support", "oppose", "abstain", "delay", "seek_information"),
        )


if __name__ == "__main__":
    unittest.main()
