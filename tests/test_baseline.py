"""PR-7: baseline measurement. No new information mechanism is added."""

from __future__ import annotations

import unittest
from pathlib import Path

from political_sim.core.actions.action_resolver import CONSEQUENCE_RULE
from political_sim.experiments.analysis.resources import CONSERVATION_RULE, RESOURCE_OUTCOMES
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
from political_sim.core.contract import (
    ACTION_BOUNDARY_STATUS,
    CONSEQUENCE_STATUS,
    CONSERVATION_STATUS,
    CORE_BASELINE_STATUS,
    FROZEN_CLAUSES,
    FIDELITY_STATUS,
    LAYER_RULES,
    TRUST_GATE_STATUS,
    TRUST_INVARIANTS,
    TRUST_REJECTION_CLAUSES,
    TRUST_STATUS,
)
from political_sim.core.models.individual import PREFERENCE_FIELDS
from political_sim.experiments.analysis.baseline import (
    belief_to_intent_latency,
    intent_changes,
    reality_to_belief_latency,
    reconstruct,
)
from political_sim.experiments.runners.baseline import (
    constraint_baseline,
    generation_baseline,
    hop_baseline,
    quality_baseline,
)
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.information import (
    FIDELITY_RULE,
    GENERATION_ERROR_ROLE,
    GENERATION_RULE,
    QUALITY_RULE,
)
from tests.test_transmission import chain_world

ROOT = Path(__file__).resolve().parents[1]


class BaselineTests(unittest.TestCase):
    def test_locked_rules(self) -> None:
        self.assertEqual(GENERATION_RULE, "G(p, e) = clamp(p - e, 0, 1)")
        self.assertEqual(
            GENERATION_ERROR_ROLE,
            "generation_error is a system experiment parameter for signal generation, "
            "not actor bias, intentional distortion, or trust.",
        )
        self.assertEqual(
            QUALITY_RULE,
            "information_quality = 1 does not mean the signal is true. "
            "It means the system does not further reduce an already generated signal.",
        )
        spec = (ROOT / "docs" / "BASELINE_EXPERIMENT_SPEC.md").read_text(encoding="utf-8")
        self.assertIn(QUALITY_RULE, spec)
        self.assertIn(GENERATION_RULE, spec)
        self.assertIn(FIDELITY_RULE, spec)
        for clause in TRUST_INVARIANTS:
            self.assertIn(clause, spec)
        self.assertEqual(CORE_BASELINE_STATUS, "CORE BASELINE — FROZEN")
        self.assertIn(CORE_BASELINE_STATUS, spec)
        for clause in FROZEN_CLAUSES:
            self.assertIn(clause, spec)
        self.assertEqual(TRUST_STATUS, "acceptance gate")
        self.assertEqual(TRUST_GATE_STATUS, "PR-8 TRUST GATE — FROZEN")
        self.assertIn(TRUST_GATE_STATUS, spec)
        self.assertEqual(FIDELITY_STATUS, "PR-9 FIDELITY — FROZEN")
        self.assertIn(FIDELITY_STATUS, spec)
        for clause in LAYER_RULES:
            self.assertIn(clause, spec)
        self.assertEqual(ACTION_BOUNDARY_STATUS, "PR-10 ACTION BOUNDARY — FROZEN")
        self.assertIn(ACTION_BOUNDARY_STATUS, spec)
        self.assertEqual(CONSEQUENCE_STATUS, "PR-11 CONSEQUENCE — FROZEN")
        self.assertIn(CONSEQUENCE_STATUS, spec)
        self.assertIn(CONSEQUENCE_RULE, spec)
        self.assertEqual(CONSERVATION_STATUS, "PR-12 RESOURCE CONSERVATION — FROZEN")
        self.assertIn(CONSERVATION_STATUS, spec)
        self.assertIn(CONSERVATION_RULE, spec)
        for outcome in RESOURCE_OUTCOMES:
            self.assertIn(outcome, spec)
        for clause in TRUST_REJECTION_CLAUSES:
            self.assertIn(clause, spec)
        self.assertIn("trust", SimulationEngine.__init__.__annotations__)
        self.assertIn("trust_threshold", SimulationEngine.__init__.__annotations__)

    def test_generation_error_domain(self) -> None:
        self.assertEqual(_power(_uniform(0.0), error=0.25, quality=1.0), 0.0)
        self.assertEqual(_power(_uniform(1.0), error=1.0, quality=1.0), 0.0)
        self.assertEqual(_power(_uniform(0.2), error=0.5, quality=1.0), 0.0)
        self.assertEqual(_power(_uniform(1.0), error=0.0, quality=1.0), 1.0)
        with self.assertRaises(ValueError):
            SimulationEngine(_uniform(1.0), 0, generation_error=-0.1)
        untouched = SimulationEngine(_uniform(0.2), 0, information_quality=1.0, generation_error=0.5)
        untouched.run(1)
        self.assertEqual(untouched.world.individuals["I01"].preferences.power, 0.2)
        self.assertEqual(untouched.world.beliefs[("R1", "G1")].estimated_information, 1.0)

    def test_error_and_quality_baselines_add_up(self) -> None:
        by_error = {point.generation_error: point for point in generation_baseline()}
        self.assertEqual(by_error[0.0].intent_cause, "baseline:support")
        self.assertEqual(by_error[0.1].intent_cause, "baseline:support")
        self.assertEqual(by_error[0.25].intent_cause, "baseline:support")
        self.assertEqual(by_error[0.5].intent_cause, "baseline:abstain")
        self.assertEqual(by_error[0.25].trace.received.power, 0.75)
        self.assertEqual(by_error[0.25].decomposition.quality_gap, 0.0)
        self.assertGreater(by_error[0.25].decomposition.belief_gap, 0.0)
        self.assertEqual(by_error[0.25].estimated_information, 1.0)

        by_quality = {point.information_quality: point for point in quality_baseline()}
        self.assertEqual(by_quality[1.0].intent_cause, "baseline:support")
        self.assertEqual(by_quality[0.75].intent_cause, "baseline:support")
        self.assertEqual(by_quality[0.5].intent_cause, "baseline:abstain")
        self.assertEqual(by_quality[0.0].intent_cause, "baseline:oppose")
        self.assertEqual(by_quality[0.5].decomposition.generation_gap, 0.0)
        self.assertEqual(by_quality[0.5].decomposition.quality_gap, 0.5)
        self.assertEqual(by_quality[0.5].trace.generated.power, 1.0)
        self.assertEqual(by_quality[0.5].trace.received.power, 0.5)

        for point in (*generation_baseline(), *quality_baseline(), *hop_baseline()):
            parts = point.decomposition
            self.assertEqual(parts.transmission_gap, 0.0)
            self.assertEqual(
                parts.generation_gap + parts.quality_gap + parts.transmission_gap,
                parts.belief_gap,
            )

    def test_hops_do_not_add_error(self) -> None:
        points = hop_baseline()
        self.assertEqual([point.hops for point in points], [1, 2, 3, 4])
        received = points[0].trace.received
        for point in points:
            self.assertEqual(point.trace.received, received)
            self.assertEqual(point.trace.generated, points[0].trace.generated)
            self.assertEqual(point.intent_cause, "baseline:oppose")
            self.assertEqual(point.decomposition.belief_gap, points[0].decomposition.belief_gap)
            self.assertEqual(point.decomposition.transmission_gap, 0.0)

    def test_constraint_baseline_holds_belief_fixed(self) -> None:
        first, second = constraint_baseline()
        self.assertEqual(first.trace.generated, second.trace.generated)
        self.assertEqual(first.trace.received, second.trace.received)
        self.assertEqual(first.decomposition, second.decomposition)
        self.assertEqual(first.intent_cause, "constraint:seek_information")
        self.assertEqual(second.intent_cause, "constraint:delay")

    def test_event_log_reconstructs_latency(self) -> None:
        running = SimulationEngine(chain_world(1), 0, information_quality=1.0, generation_error=0.0)
        running.run(1)
        for field in PREFERENCE_FIELDS:
            running.intervene_preference("I01", field, 0.0)
        held = [record for record in reconstruct(running.event_log) if record.actor_id == "R1"]
        self.assertEqual(held[-1].intent_cause, "baseline:support")
        self.assertEqual(held[-1].received.power, 1.0)
        self.assertTrue(
            any(event.event_type == "experiment_intervention" for event in running.event_log)
        )
        self.assertFalse(
            any(
                event.event_type == "belief_updated" and event.tick > running.tick
                for event in running.event_log
            )
        )
        running.run(1)
        self.assertEqual(reality_to_belief_latency(running.event_log), 1)
        self.assertEqual(belief_to_intent_latency(running.event_log, 2), 0)
        changes = intent_changes(reconstruct(running.event_log))
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].old_cause, "baseline:support")
        self.assertEqual(changes[0].new_cause, "baseline:oppose")
        self.assertEqual(changes[0].from_tick, 1)
        self.assertEqual(changes[0].to_tick, 2)
        self.assertEqual(changes[0].old_received.power, 1.0)
        self.assertEqual(changes[0].new_received.power, 0.0)
        types = [event.event_type for event in running.event_log]
        self.assertLess(types.index("experiment_intervention"), types.index("signal_generated", 1))

    def test_measurement_does_not_run_or_mutate(self) -> None:
        source = (ROOT / "political_sim" / "experiments" / "analysis" / "baseline.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("SimulationEngine", source)
        self.assertNotIn("mutation_scope", source)


def _power(world: WorldState, error: float, quality: float) -> float:
    running = SimulationEngine(world, 0, information_quality=quality, generation_error=error)
    running.run(1)
    return running.world.beliefs[("R1", "G1")].estimated_preference.power


def _uniform(power: float) -> WorldState:
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
