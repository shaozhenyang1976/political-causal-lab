"""PR-11：被接纳的行动只给行动者增加 1 单位资源。"""

from __future__ import annotations

import unittest

from political_sim.core.actions import Action
from political_sim.core.actions.action_resolver import CONSEQUENCE_RULE
from political_sim.simulation.engine import SimulationEngine
from tests.test_transmission import chain_world


class ConsequenceTests(unittest.TestCase):
    def test_rule_is_locked(self) -> None:
        self.assertEqual(
            CONSEQUENCE_RULE,
            "An admitted action adds one resource unit to its actor. "
            "The addition does not change preferences, beliefs, information, fidelity, or trust.",
        )

    def test_admitted_action_adds_one_resource_after_acceptance(self) -> None:
        plain = _engine()
        acted = _engine()
        acted.submit(Action("support", "R1", ("G1",), "chosen"))
        plain.run(2)
        acted.run(2)
        self.assertEqual(acted.world.resources, {"R1": 1.0})
        self.assertEqual(plain.world.resources, {})
        self.assertEqual(acted.world.individuals, plain.world.individuals)
        self.assertEqual(acted.world.beliefs, plain.world.beliefs)
        for tick in (1, 2):
            self.assertEqual(
                _lines(acted, tick, "signal_generated", "R1"),
                _lines(plain, tick, "signal_generated", "R1"),
            )
            self.assertEqual(
                _lines(acted, tick, "belief_updated", "R1"),
                _lines(plain, tick, "belief_updated", "R1"),
            )
        self.assertEqual(acted.information_quality, plain.information_quality)
        self.assertEqual(acted.generation_error, plain.generation_error)
        self.assertEqual(acted.fidelity, plain.fidelity)
        self.assertEqual(acted.trust, plain.trust)
        accepted = _only(acted, "action_accepted")
        consequence = _only(acted, "action_consequence")
        intent = next(
            event
            for event in acted.event_log
            if event.event_type == "action_intent" and event.actors == ("R1",)
        )
        self.assertEqual(intent.cause, "baseline:oppose")
        self.assertEqual(accepted.available_information, ("consequence=none",))
        self.assertEqual(accepted.state_change, ())
        self.assertEqual(accepted.cause, "admitted (chosen)")
        self.assertEqual(consequence.cause, "accepted_action (chosen)")
        self.assertEqual(consequence.state_change, ("R1.resources=1.0",))
        self.assertEqual(consequence.available_information, ())
        recorded = list(acted.event_log)
        self.assertLess(recorded.index(intent), recorded.index(accepted))
        self.assertLess(recorded.index(accepted), recorded.index(consequence))
        self.assertEqual(
            [event.event_type for event in plain.event_log],
            [
                event.event_type
                for event in acted.event_log
                if event.event_type not in {"action_accepted", "action_consequence"}
            ],
        )

    def test_rejected_actions_do_not_add_resources(self) -> None:
        running = _engine({"R1": 0.5})
        running.submit(Action("vote", "R1", ("G1",)))
        running.submit(Action("support", "R1", ("G1",)))
        running.submit(Action("oppose", "R2", ("G1",)))
        running.run(1)
        self.assertEqual(running.world.resources, {"R1": 1.5, "R2": 1.0})
        consequences = [
            event for event in running.event_log if event.event_type == "action_consequence"
        ]
        self.assertEqual(
            [event.state_change for event in consequences],
            [("R1.resources=1.5",), ("R2.resources=1.0",)],
        )
        self.assertEqual(
            [event.cause for event in running.event_log if event.event_type == "action_rejected"],
            ["action effect is not implemented"],
        )


def _engine(resources: dict[str, float] | None = None) -> SimulationEngine:
    return SimulationEngine(
        chain_world(2, resources=resources),
        0,
        information_quality=0.5,
        generation_error=0.25,
        fidelity=0.5,
    )


def _lines(engine: SimulationEngine, tick: int, event_type: str, observer_id: str) -> tuple[str, ...]:
    return next(
        event.available_information
        for event in engine.event_log
        if event.tick == tick and event.event_type == event_type and event.actors == (observer_id,)
    )


def _only(engine: SimulationEngine, event_type: str):
    found = [event for event in engine.event_log if event.event_type == event_type]
    if len(found) != 1:
        raise AssertionError(f"expected one {event_type}, found {len(found)}")
    return found[0]


if __name__ == "__main__":
    unittest.main()
