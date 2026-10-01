"""PR-10: support and oppose may be admitted, and admission does not change WorldState."""

from __future__ import annotations

import unittest

from political_sim.core.actions import ACTION_ADMISSION_RULE, ADMISSIBLE_ACTION_TYPES, Action
from political_sim.core.contract import LAYER_RULES
from political_sim.experiments.analysis.baseline import preferences_from_labels
from political_sim.simulation.engine import SimulationEngine
from tests.test_engine import structural
from tests.test_fidelity import _lines
from tests.test_transmission import chain_world


class LayerSeparationTests(unittest.TestCase):
    def test_each_parameter_stays_on_its_own_layer(self) -> None:
        self.assertEqual(
            LAYER_RULES,
            (
                "e does not modify q, fidelity, or trust.",
                "q does not modify fidelity or trust.",
                "fidelity does not modify q or trust.",
                "trust does not modify signal or received values.",
            ),
        )
        generated = _run(generation_error=0.25)
        quality = _run(information_quality=0.5)
        forwarded = _run(fidelity=0.5)
        rejected = _run(trust=0.0)
        self.assertEqual(generated.information_quality, 1.0)
        self.assertEqual(generated.fidelity, 1.0)
        self.assertEqual(generated.trust, 1.0)
        self.assertEqual(quality.fidelity, 1.0)
        self.assertEqual(quality.trust, 1.0)
        self.assertEqual(quality.generation_error, 0.0)
        self.assertEqual(forwarded.information_quality, 1.0)
        self.assertEqual(forwarded.trust, 1.0)
        self.assertEqual(rejected.generation_error, 0.0)
        self.assertEqual(rejected.information_quality, 1.0)
        self.assertEqual(rejected.fidelity, 1.0)
        self.assertNotEqual(
            _lines(generated, "signal_generated", "R1"),
            _lines(quality, "signal_generated", "R1"),
        )
        self.assertEqual(
            _lines(quality, "signal_generated", "R1"),
            _lines(forwarded, "signal_generated", "R1"),
        )
        self.assertEqual(
            _lines(forwarded, "belief_updated", "R1"),
            _lines(rejected, "trust_rejected", "R1"),
        )
        self.assertEqual(
            forwarded.world.beliefs[("R1", "G1")].estimated_information,
            forwarded.information_quality,
        )
        self.assertEqual(forwarded.world.beliefs[("R4", "G1")].estimated_information, 1.0)
        self.assertEqual(forwarded.world.beliefs[("R4", "G1")].estimated_preference.power, 0.125)
        self.assertEqual(quality.world.beliefs[("R1", "G1")].estimated_information, 0.5)
        received = preferences_from_labels(
            _lines(quality, "belief_updated", "R1"), "received_preference"
        )
        self.assertEqual(received.power, 0.5)


class ActionBoundaryTests(unittest.TestCase):
    def test_only_support_and_oppose_are_admitted(self) -> None:
        self.assertEqual(
            ACTION_ADMISSION_RULE,
            "Only support and oppose may be admitted as actions. "
            "Admission records the action and does not change WorldState.",
        )
        self.assertEqual(ADMISSIBLE_ACTION_TYPES, frozenset({"support", "oppose"}))

    def test_admission_stays_separate_from_the_later_consequence(self) -> None:
        before = structural(chain_world(2))
        untouched = SimulationEngine(chain_world(2), 0)
        untouched.run(1)
        running = SimulationEngine(chain_world(2), 0)
        running.submit(Action("oppose", "R1", ("G1",), "chosen"))
        running.run(1)
        self.assertEqual(running.world.individuals, before[0])
        self.assertEqual(running.world.resources, {"R1": 1.0})
        self.assertEqual(untouched.world.resources, {})
        self.assertEqual(
            [event.event_type for event in untouched.event_log],
            [
                event.event_type
                for event in running.event_log
                if event.event_type not in {"action_accepted", "action_consequence"}
            ],
        )
        accepted = [event for event in running.event_log if event.event_type == "action_accepted"]
        intent = next(
            event
            for event in running.event_log
            if event.event_type == "action_intent" and event.actors == ("R1",)
        )
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0].cause, "admitted (chosen)")
        self.assertEqual(accepted[0].available_information, ("consequence=none",))
        self.assertEqual(accepted[0].state_change, ())
        self.assertEqual(intent.cause, "baseline:support")
        recorded = list(running.event_log)
        self.assertLess(recorded.index(intent), recorded.index(accepted[0]))

    def test_other_actions_remain_unimplemented(self) -> None:
        running = SimulationEngine(chain_world(2), 0)
        before = structural(running.world)
        running.submit(Action("vote", "R1", ("G1",)))
        running.submit(Action("abstain", "R1", ("G1",)))
        running.run(1)
        self.assertEqual(structural(running.world), before)
        causes = [
            event.cause
            for event in running.event_log
            if event.event_type == "action_rejected"
        ]
        self.assertEqual(
            causes,
            ["action effect is not implemented", "unknown action type"],
        )
        self.assertFalse(any(event.event_type == "action_accepted" for event in running.event_log))


def _run(**kwargs: float) -> SimulationEngine:
    running = SimulationEngine(chain_world(4), 0, **kwargs)
    running.run(1)
    return running


if __name__ == "__main__":
    unittest.main()
