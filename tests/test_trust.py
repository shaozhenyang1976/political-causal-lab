"""PR-8: admission threshold. It does not change the signal and does not write trust into belief error."""

from __future__ import annotations

import inspect
import unittest

from political_sim.core.models import Belief, Capabilities, Preferences, Representative, WorldState
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.information import apply_generation_error, deliver, transmit
from political_sim.simulation.systems.trust import TRUST_GATE_RULE, admits
from tests.test_transmission import chain_world


class TrustGateTests(unittest.TestCase):
    def test_gate_rule_and_threshold(self) -> None:
        self.assertIn("admission failure before DecisionContext", TRUST_GATE_RULE)
        self.assertTrue(admits(1.0, 0.5))
        self.assertTrue(admits(0.5, 0.5))
        self.assertFalse(admits(0.0, 0.5))
        with self.assertRaises(ValueError):
            SimulationEngine(chain_world(1), 0, trust=1.2)
        with self.assertRaises(ValueError):
            SimulationEngine(chain_world(1), 0, trust_threshold=-0.1)
        self.assertNotIn("trust", inspect.getsource(deliver))
        self.assertNotIn("trust", inspect.getsource(transmit))
        self.assertNotIn("trust", inspect.getsource(apply_generation_error))

    def test_passing_the_gate_matches_the_baseline(self) -> None:
        baseline = _run(0.0, 1.0, 1.0, 0.5)
        admitted = _run(0.25, 0.5, 1.0, 0.5)
        plain = SimulationEngine(
            chain_world(1),
            0,
            information_quality=0.5,
            generation_error=0.25,
        )
        plain.run(1)
        self.assertEqual(baseline.world.beliefs[("R1", "G1")].estimated_preference.power, 1.0)
        self.assertEqual(_cause(baseline), "baseline:support")
        self.assertFalse(any(event.event_type == "trust_rejected" for event in baseline.event_log))
        self.assertEqual(admitted.world.beliefs, plain.world.beliefs)
        self.assertEqual(
            [event.event_type for event in admitted.event_log],
            [event.event_type for event in plain.event_log],
        )
        self.assertEqual(admitted.world.beliefs[("R1", "G1")].estimated_preference.power, 0.375)
        self.assertEqual(chain_world(1).representation_edges[("R1", "G1")].trust, 0.0)

    def test_rejection_keeps_the_signal_and_the_old_belief(self) -> None:
        accepted = _run(0.25, 0.5, 1.0, 0.5)
        rejected = _run(0.25, 0.5, 0.0, 0.5)
        closed = _run(0.0, 1.0, 0.0, 0.5)
        self.assertEqual(closed.world.beliefs, {})
        self.assertEqual(_cause(closed), "trust_rejected")
        self.assertIn("received_preference.power=1.0", _received(closed))
        self.assertEqual(_generated(accepted), _generated(rejected))
        self.assertEqual(_received(accepted), _received(rejected))
        self.assertEqual(rejected.world.beliefs, {})
        self.assertIn("received_preference.power=0.375", _received(rejected))
        self.assertIn("generated_preference.power=0.75", _generated(rejected))
        self.assertEqual(_cause(rejected), "trust_rejected")
        self.assertIn("intent=seek_information", _intent_event(rejected).available_information)
        self.assertEqual(_event(rejected, "trust_rejected").state_change, ())
        self.assertNotIn("belief_updated", [event.event_type for event in rejected.event_log])

        held = SimulationEngine(
            _with_prior(0.2),
            0,
            information_quality=1.0,
            generation_error=0.0,
            trust=0.0,
            trust_threshold=0.5,
            decision_constraints={"R1": ("delay",)},
        )
        held.run(1)
        self.assertEqual(held.world.beliefs[("R1", "G1")].estimated_preference.power, 0.2)
        self.assertEqual(len(held.world.beliefs), 1)
        self.assertEqual(_cause(held), "trust_rejected")
        self.assertNotEqual(_cause(held), "constraint:delay")
        self.assertEqual(_cause(held, "R2"), "no_belief")
        self.assertFalse(
            any(event.event_type == "trust_rejected" and event.actors == ("R2",) for event in held.event_log)
        )

    def test_forwarded_signal_is_unchanged_by_the_gate(self) -> None:
        rejected = SimulationEngine(
            chain_world(4),
            0,
            information_quality=0.5,
            generation_error=0.25,
            trust=0.0,
            trust_threshold=0.5,
        )
        rejected.run(1)
        self.assertEqual(rejected.world.beliefs, {})
        received = [
            event.available_information
            for event in rejected.event_log
            if event.event_type == "trust_rejected"
        ]
        self.assertEqual(len(received), 4)
        self.assertEqual(len(set(received)), 1)
        self.assertIn("received_preference.power=0.375", received[0])


def _run(error: float, quality: float, trust: float, threshold: float) -> SimulationEngine:
    running = SimulationEngine(
        chain_world(1),
        0,
        information_quality=quality,
        generation_error=error,
        trust=trust,
        trust_threshold=threshold,
    )
    running.run(1)
    return running


def _cause(engine: SimulationEngine, observer_id: str = "R1") -> str:
    return _intent_event(engine, observer_id).cause


def _intent_event(engine: SimulationEngine, observer_id: str = "R1"):
    matches = [
        event
        for event in engine.event_log
        if event.event_type == "action_intent" and event.actors == (observer_id,)
    ]
    return matches[-1]


def _generated(engine: SimulationEngine) -> tuple[str, ...]:
    return _event(engine, "signal_generated").available_information


def _received(engine: SimulationEngine) -> tuple[str, ...]:
    for event_type in ("belief_updated", "trust_rejected"):
        matches = [
            event
            for event in engine.event_log
            if event.event_type == event_type and event.actors == ("R1",)
        ]
        if matches:
            return matches[0].available_information
    raise AssertionError("no received signal")


def _event(engine: SimulationEngine, event_type: str):
    return next(event for event in engine.event_log if event.event_type == event_type)


def _with_prior(power: float) -> WorldState:
    source = chain_world(1)
    belief = Belief(
        "R1",
        "G1",
        Preferences(power, power, power, power, power),
        Capabilities(0, 0, 0, 0, 0),
        0.0,
        1.0,
    )
    representatives = dict(source.representatives)
    representatives["R2"] = Representative("R2")
    return WorldState(
        individuals=dict(source.individuals),
        groups=dict(source.groups),
        organizations={},
        representatives=representatives,
        factions={},
        coalitions={},
        institutions={},
        representation_edges=dict(source.representation_edges),
        resources={},
        networks={},
        beliefs={("R1", "G1"): belief},
        environment=source.environment,
    )


if __name__ == "__main__":
    unittest.main()
