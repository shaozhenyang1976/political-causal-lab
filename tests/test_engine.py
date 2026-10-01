"""PR-2: tick loop, action gate, and event record. Political decision is not included."""

from __future__ import annotations

import random
import unittest
from pathlib import Path
from unittest.mock import patch

from political_sim.core.actions import SPEC_ACTION_TYPES, Action
from political_sim.core.mutation import DirectMutationError
from political_sim.core.random import SeededRandom
from political_sim.scenarios.sandbox import ScenarioGenerator
from political_sim.simulation.engine import SimulationEngine

ROOT = Path(__file__).resolve().parents[1]


def engine(seed: int = 0, information_quality: float = 1.0) -> SimulationEngine:
    return SimulationEngine(
        ScenarioGenerator().generate(seed),
        seed,
        information_quality=information_quality,
    )


def structural(world: object) -> object:
    return (
        world.individuals,
        world.groups,
        world.organizations,
        world.representatives,
        world.factions,
        world.coalitions,
        world.institutions,
        world.representation_edges,
        world.resources,
        world.networks,
        world.environment,
    )


def of_type(log: object, tick: int, event_type: str) -> list[object]:
    return [event for event in log if event.tick == tick and event.event_type == event_type]


class EngineLoopTests(unittest.TestCase):
    def test_one_tick_and_one_hundred_ticks_keep_a_valid_world(self) -> None:
        initial = ScenarioGenerator().generate(0)
        one = engine(0)
        one.run(1)
        self.assertEqual(one.tick, 1)
        self.assertEqual(structural(one.world), structural(initial))
        self.assertEqual(
            set(one.world.beliefs),
            {("R1", "G1"), ("R2", "G2"), ("R3", "G3"), ("R4", "G4")},
        )
        one.world.validate()

        hundred = engine(0)
        hundred.run(100)
        self.assertEqual(hundred.tick, 100)
        self.assertEqual(structural(hundred.world), structural(initial))
        hundred.world.validate()
        self.assertEqual(len(hundred.event_log), 1300)
        completed = of_type(hundred.event_log, 100, "tick_completed")
        self.assertEqual(len(completed), 1)
        self.assertEqual(
            [event.tick for event in hundred.event_log if event.event_type == "tick_completed"],
            list(range(1, 101)),
        )
        self.assertEqual(hundred.world.coalitions, {})
        for faction in hundred.world.factions.values():
            self.assertEqual(faction.member_ids, ())

    def test_split_runs_match_one_run(self) -> None:
        left = engine(4)
        left.run(1)
        left.run(99)
        right = engine(4)
        right.run(100)
        self.assertEqual(left.world, right.world)
        self.assertEqual(left.event_log, right.event_log)
        self.assertEqual(left.tick, right.tick)

    def test_same_seed_is_identical_and_ticks_draw_no_random_numbers(self) -> None:
        first = engine(5)
        second = engine(5)
        calls: list[str] = []
        original_random = SeededRandom.random
        original_uniform = SeededRandom.uniform

        def spy_random(rng: SeededRandom) -> float:
            calls.append("random")
            return original_random(rng)

        def spy_uniform(rng: SeededRandom, low: float, high: float) -> float:
            calls.append("uniform")
            return original_uniform(rng, low, high)

        random.seed(5)
        before = random.getstate()
        with patch.object(SeededRandom, "random", spy_random), patch.object(
            SeededRandom, "uniform", spy_uniform
        ):
            first.run(100)
            second.run(100)
        self.assertEqual(calls, [])
        self.assertEqual(random.getstate(), before)
        self.assertEqual(first.world, second.world)
        self.assertEqual(first.event_log.as_tuple(), second.event_log.as_tuple())

    def test_tick_events_do_not_copy_true_state(self) -> None:
        running = engine(0)
        running.run(1)
        completed = of_type(running.event_log, 1, "tick_completed")
        self.assertEqual(len(completed), 1)
        event = completed[0]
        self.assertEqual(event.actors, ())
        self.assertEqual(event.targets, ())
        self.assertEqual(event.cause, "tick_protocol")
        self.assertEqual(event.available_information, ())
        self.assertEqual(event.incentives, ())
        self.assertEqual(event.state_change, ())
        for belief_event in of_type(running.event_log, 1, "belief_updated"):
            text = " ".join(belief_event.available_information + belief_event.state_change)
            self.assertNotIn("true_preference", text)
            self.assertEqual(belief_event.incentives, ())

    def test_zero_steps_and_negative_steps(self) -> None:
        running = engine(0)
        running.run(0)
        self.assertEqual(running.tick, 0)
        self.assertEqual(len(running.event_log), 0)
        with self.assertRaises(ValueError):
            running.run(-1)
        with self.assertRaises(ValueError):
            running.run(True)  # type: ignore[arg-type]

    def test_world_stays_sealed_after_ticks(self) -> None:
        running = engine(0)
        running.run(100)
        with self.assertRaises(DirectMutationError):
            running.world.resources["I01"] = 0.0


class ActionGateTests(unittest.TestCase):
    def test_submitted_action_is_traced_and_does_not_change_state(self) -> None:
        initial = ScenarioGenerator().generate(1)
        running = SimulationEngine(ScenarioGenerator().generate(1), 1)
        running.submit(Action(action_type="vote", actor_id="I01", target_ids=("G1",)))
        running.run(2)
        self.assertEqual(structural(running.world), structural(initial))
        rejected = of_type(running.event_log, 1, "action_rejected")
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0].actors, ("I01",))
        self.assertEqual(rejected[0].targets, ("G1",))
        self.assertEqual(rejected[0].cause, "action effect is not implemented")
        self.assertEqual(rejected[0].available_information, ())
        self.assertEqual(rejected[0].incentives, ())
        self.assertEqual(rejected[0].state_change, ())
        tick_one = [event.event_type for event in running.event_log if event.tick == 1]
        self.assertEqual(
            tick_one,
            ["signal_generated"] * 4
            + ["belief_updated"] * 4
            + ["action_intent"] * 4
            + ["action_rejected", "tick_completed"],
        )
        tick_two = [event.event_type for event in running.event_log if event.tick == 2]
        self.assertEqual(
            tick_two,
            ["signal_generated"] * 4 + ["belief_updated"] * 4 + ["action_intent"] * 4 + ["tick_completed"],
        )

    def test_action_submitted_after_a_tick_waits_for_the_next_tick(self) -> None:
        running = engine(0)
        running.run(1)
        running.submit(
            Action(action_type="allocate", actor_id="OrgA", target_ids=("R1",), cause="queued")
        )
        running.run(1)
        tick_one = [event.event_type for event in running.event_log if event.tick == 1]
        self.assertEqual(tick_one[-1], "tick_completed")
        self.assertNotIn("action_rejected", tick_one)
        tick_two = [event for event in running.event_log if event.tick == 2]
        types = [event.event_type for event in tick_two]
        self.assertLess(types.index("action_rejected"), types.index("tick_completed"))
        self.assertEqual(
            tick_two[types.index("action_rejected")].cause,
            "action effect is not implemented (queued)",
        )

    def test_unknown_or_dangling_actions_are_rejected_without_effects(self) -> None:
        running = engine(0)
        fresh = ScenarioGenerator().generate(0)
        running.submit(Action(action_type="not_a_spec_action", actor_id="missing", target_ids=("ghost",)))
        running.run(1)
        rejected = of_type(running.event_log, 1, "action_rejected")
        self.assertEqual(
            rejected[0].cause,
            "unknown action type; invalid actor reference; invalid target reference: ghost",
        )
        self.assertEqual(structural(running.world), structural(fresh))

    def test_spec_action_names_are_recognized_but_not_implemented(self) -> None:
        self.assertEqual(
            SPEC_ACTION_TYPES,
            {
                "form_coalition",
                "leave_coalition",
                "appoint",
                "remove",
                "vote",
                "allocate",
                "sanction",
                "negotiate",
                "support",
                "oppose",
                "recruit",
                "defect",
            },
        )

    def test_mutation_scope_is_only_opened_by_the_resolver(self) -> None:
        users: list[str] = []
        for path in (ROOT / "political_sim").rglob("*.py"):
            if "with mutation_scope()" in path.read_text(encoding="utf-8"):
                users.append(path.relative_to(ROOT / "political_sim").as_posix())
        self.assertEqual(users, ["core/actions/action_resolver.py"])


if __name__ == "__main__":
    unittest.main()
