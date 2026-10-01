"""PR-12: the resource increment equals the number of admitted actions and does not enter the next tick's cognitive layer."""

from __future__ import annotations

import unittest
from pathlib import Path

from political_sim.core.actions import Action
from political_sim.core.contract import (
    FIELD_PRESENCE_RULE,
    OPEN_LOOP_FACTS,
    OPEN_LOOP_STATUS,
    RESOURCE_ADMISSION,
    RESOURCE_ADR_QUESTIONS,
    RESOURCE_ADR_STATUS,
    RESOURCE_CAUSAL_GATE,
    RESOURCE_CLAUSES,
    RESOURCE_DEFINITION,
    RESOURCE_LEDGER_LIMIT,
    RESOURCE_ONE_EDGE_RULE,
    SKELETON_STATUS,
    STAGE_STATUS,
)
from political_sim.experiments.analysis.resources import (
    CONSERVATION_RULE,
    RESOURCE_OUTCOMES,
    resource_account,
)
from political_sim.simulation.engine import SimulationEngine
from tests.test_transmission import chain_world

ROOT = Path(__file__).resolve().parents[1]


class ResourceConservationTests(unittest.TestCase):
    def test_rule_is_locked(self) -> None:
        self.assertEqual(CONSERVATION_RULE, "resources_before + accepted_actions = resources_after")
        self.assertEqual(
            RESOURCE_OUTCOMES,
            (
                "rejected_action adds 0 resources.",
                "no_action adds 0 resources.",
                "support adds 1 resource.",
                "oppose adds 1 resource.",
            ),
        )
        source = (ROOT / "political_sim" / "experiments" / "analysis" / "resources.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("SimulationEngine", source)
        self.assertNotIn("mutation_scope", source)
        semantics = (ROOT / "docs" / "RESOURCE_SEMANTICS.md").read_text(encoding="utf-8")
        self.assertEqual(len(RESOURCE_CLAUSES), 8)
        for clause in RESOURCE_CLAUSES:
            self.assertIn(clause, semantics)
        self.assertIn("No resource-feedback loop has been formed.", semantics)
        self.assertIn(SKELETON_STATUS, semantics)
        self.assertIn(RESOURCE_DEFINITION, semantics)
        self.assertIn(FIELD_PRESENCE_RULE, semantics)
        self.assertIn(STAGE_STATUS, semantics)
        self.assertIn(RESOURCE_LEDGER_LIMIT, semantics)
        self.assertIn(RESOURCE_CAUSAL_GATE, semantics)
        self.assertIn(
            "PR-13 is not started until Resource's causal meaning is defined independently.",
            semantics,
        )
        self.assertIn(OPEN_LOOP_STATUS, semantics)
        for fact in OPEN_LOOP_FACTS:
            self.assertIn(fact, semantics)
        self.assertEqual(len(RESOURCE_ADMISSION), 10)
        for gate in RESOURCE_ADMISSION:
            self.assertIn(gate, semantics)
        self.assertIn(RESOURCE_ONE_EDGE_RULE, semantics)
        record = (ROOT / "docs" / "RESOURCE_SEMANTIC_ADR.md").read_text(encoding="utf-8")
        self.assertIn(OPEN_LOOP_STATUS, record)
        self.assertIn(RESOURCE_ONE_EDGE_RULE, record)
        self.assertEqual(record.count(RESOURCE_ADR_STATUS), 6)
        self.assertEqual(len(RESOURCE_ADR_QUESTIONS), 5)
        for question in RESOURCE_ADR_QUESTIONS:
            self.assertIn(question, record)
        self.assertIn(RESOURCE_DEFINITION, semantics)
        self.assertIn("RepresentationEdge.trust", semantics)
        self.assertIn("RepresentationEdge.fidelity", semantics)

    def test_only_accepted_actions_add_one(self) -> None:
        idle = _run()
        rejected = _run(Action("vote", "R1", ("G1",)))
        supported = _run(Action("support", "R1", ("G1",)))
        opposed = _run(Action("oppose", "R1", ("G1",)))
        self.assertEqual(_delta(idle), 0.0)
        self.assertEqual(_delta(rejected), 0.0)
        self.assertEqual(_delta(supported), 1.0)
        self.assertEqual(_delta(opposed), 1.0)
        rejected_account = resource_account(
            {"R1": 0.5}, rejected.event_log, dict(rejected.world.resources)
        )
        self.assertEqual(rejected_account.accepted_actions, 0)
        self.assertEqual(rejected_account.rejected_actions, 1)
        self.assertEqual(idle.world.beliefs, supported.world.beliefs)
        self.assertEqual(idle.world.individuals, opposed.world.individuals)
        for tick in (1, 2):
            self.assertEqual(
                _lines(idle, tick, "signal_generated", "R1"),
                _lines(supported, tick, "signal_generated", "R1"),
            )
            self.assertEqual(
                _lines(idle, tick, "belief_updated", "R1"),
                _lines(opposed, tick, "belief_updated", "R1"),
            )

    def test_mixed_actions_conserve_each_actor(self) -> None:
        before = {"R1": 0.5, "I01": 2.0}
        running = SimulationEngine(chain_world(2, resources=dict(before)), 0)
        running.submit(Action("vote", "R1", ("G1",)))
        running.submit(Action("support", "R1", ("G1",)))
        running.submit(Action("oppose", "R2", ("G1",)))
        running.run(1)
        account = resource_account(before, running.event_log, dict(running.world.resources))
        self.assertEqual(account.resources_before + account.accepted_actions, account.resources_after)
        self.assertEqual(account.accepted_actions, 2)
        self.assertEqual(account.rejected_actions, 1)
        self.assertEqual(account.predicted, (("I01", 2.0), ("R1", 1.5), ("R2", 1.0)))
        self.assertEqual(dict(account.predicted), dict(running.world.resources))


def _run(*actions: Action) -> SimulationEngine:
    running = SimulationEngine(
        chain_world(2, resources={"R1": 0.5}),
        0,
        information_quality=0.5,
        generation_error=0.25,
        fidelity=0.5,
    )
    for action in actions:
        running.submit(action)
    running.run(2)
    return running


def _delta(engine: SimulationEngine) -> float:
    account = resource_account({"R1": 0.5}, engine.event_log, dict(engine.world.resources))
    if account.resources_before + account.accepted_actions != account.resources_after:
        raise AssertionError("resource conservation failed")
    return account.resources_after - account.resources_before


def _lines(engine: SimulationEngine, tick: int, event_type: str, observer_id: str) -> tuple[str, ...]:
    return next(
        event.available_information
        for event in engine.event_log
        if event.tick == tick and event.event_type == event_type and event.actors == (observer_id,)
    )


if __name__ == "__main__":
    unittest.main()
