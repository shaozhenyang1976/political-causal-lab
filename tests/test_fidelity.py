"""PR-9: fidelity changes only the payload of later forwards. fidelity = 1 matches PR-8."""

from __future__ import annotations

import unittest

from political_sim.core.contract import TRUST_INVARIANTS
from political_sim.experiments.analysis.baseline import decompose, preferences_from_labels
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.information import FIDELITY_RULE
from tests.test_transmission import chain_world


class FidelityTests(unittest.TestCase):
    def test_rule_is_locked(self) -> None:
        self.assertEqual(
            FIDELITY_RULE,
            "Each information_forward hop multiplies the already received payload by fidelity. "
            "The first hop does not. fidelity = 1 leaves that payload unchanged.",
        )
        self.assertEqual(len(TRUST_INVARIANTS), 6)
        with self.assertRaises(ValueError):
            SimulationEngine(chain_world(2), 0, fidelity=-0.1)
        with self.assertRaises(ValueError):
            SimulationEngine(chain_world(2), 0, fidelity=1.1)

    def test_unit_fidelity_matches_the_untouched_baseline(self) -> None:
        plain = _run()
        explicit = _run(fidelity=1.0)
        rejected_plain = _run(trust=0.0)
        rejected_explicit = _run(trust=0.0, fidelity=1.0)
        self.assertEqual(plain.world.beliefs, explicit.world.beliefs)
        self.assertEqual(plain.event_log, explicit.event_log)
        self.assertEqual(rejected_plain.world.beliefs, rejected_explicit.world.beliefs)
        self.assertEqual(rejected_plain.event_log, rejected_explicit.event_log)
        self.assertEqual(_cause(plain, "R4"), _cause(explicit, "R4"))

    def test_lower_fidelity_changes_only_later_hops(self) -> None:
        intact = _run()
        distorted = _run(fidelity=0.5)
        self.assertEqual(_lines(intact, "signal_generated", "R1"), _lines(distorted, "signal_generated", "R1"))
        self.assertEqual(_lines(intact, "belief_updated", "R1"), _lines(distorted, "belief_updated", "R1"))
        self.assertEqual(distorted.world.beliefs[("R1", "G1")].estimated_preference.power, 1.0)
        self.assertEqual(distorted.world.beliefs[("R2", "G1")].estimated_preference.power, 0.5)
        self.assertEqual(distorted.world.beliefs[("R3", "G1")].estimated_preference.power, 0.25)
        self.assertEqual(distorted.world.beliefs[("R4", "G1")].estimated_preference.power, 0.125)
        for observer_id in ("R1", "R2", "R3", "R4"):
            self.assertEqual(
                distorted.world.beliefs[(observer_id, "G1")].estimated_information,
                1.0,
            )
        self.assertEqual(_types(intact), _types(distorted))
        self.assertEqual(_cause(intact, "R1"), "baseline:support")
        self.assertEqual(_cause(distorted, "R1"), "baseline:support")
        self.assertEqual(_cause(distorted, "R2"), "baseline:abstain")
        self.assertEqual(_cause(distorted, "R3"), "baseline:oppose")
        low_edge = _run(world_fidelity=0.1, fidelity=0.5)
        high_edge = _run(world_fidelity=0.9, fidelity=0.5)
        self.assertEqual(low_edge.world.beliefs, high_edge.world.beliefs)

        true_preference = intact.world.individuals["I01"].preferences
        generated = preferences_from_labels(
            _lines(distorted, "signal_generated", "R1"), "generated_preference"
        )
        first = preferences_from_labels(_lines(distorted, "belief_updated", "R1"), "received_preference")
        final = distorted.world.beliefs[("R4", "G1")].estimated_preference
        direct = decompose(
            true_preference,
            generated,
            first,
            distorted.world.beliefs[("R1", "G1")].estimated_preference,
        )
        downstream = decompose(true_preference, generated, first, final)
        self.assertEqual(direct.transmission_gap, 0.0)
        self.assertGreater(downstream.transmission_gap, 0.0)
        self.assertEqual(
            downstream.generation_gap + downstream.quality_gap + downstream.transmission_gap,
            downstream.belief_gap,
        )

    def test_trust_gate_still_sees_the_forwarded_payload(self) -> None:
        accepted = _run(fidelity=0.5)
        rejected = _run(fidelity=0.5, trust=0.0)
        self.assertEqual(_lines(accepted, "signal_generated", "R1"), _lines(rejected, "signal_generated", "R1"))
        self.assertEqual(_lines(accepted, "belief_updated", "R1"), _lines(rejected, "trust_rejected", "R1"))
        self.assertEqual(rejected.world.beliefs, {})
        self.assertIn("received_preference.power=0.125", _lines(rejected, "trust_rejected", "R4"))
        self.assertEqual(_cause(rejected, "R1"), "trust_rejected")
        self.assertEqual(_cause(rejected, "R4"), "trust_rejected")
        self.assertNotEqual(_cause(rejected, "R4"), "constraint:delay")
        self.assertNotEqual(_cause(rejected, "R4"), "no_belief")


def _run(
    *,
    fidelity: float = 1.0,
    trust: float = 1.0,
    world_fidelity: float = 0.0,
) -> SimulationEngine:
    running = SimulationEngine(
        chain_world(4, fidelity=world_fidelity),
        0,
        information_quality=1.0,
        generation_error=0.0,
        trust=trust,
        trust_threshold=0.5,
        fidelity=fidelity,
    )
    running.run(1)
    return running


def _types(engine: SimulationEngine) -> list[str]:
    return [event.event_type for event in engine.event_log]


def _cause(engine: SimulationEngine, observer_id: str) -> str:
    return next(
        event.cause
        for event in engine.event_log
        if event.event_type == "action_intent" and event.actors == (observer_id,)
    )


def _lines(engine: SimulationEngine, event_type: str, observer_id: str) -> tuple[str, ...]:
    return next(
        event.available_information
        for event in engine.event_log
        if event.event_type == event_type and event.actors == (observer_id,)
    )


if __name__ == "__main__":
    unittest.main()
