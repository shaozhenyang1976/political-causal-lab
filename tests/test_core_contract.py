"""Core contract. Each clause runs the current model and adds no new mechanism."""

from __future__ import annotations

import unittest
from pathlib import Path

from political_sim.core.actions.action_resolver import ActionResolver
from political_sim.core.contract import CORE_CONTRACT, INTENT_TRACE
from political_sim.core.events.event_log import EventLog
from political_sim.core.models import (
    Capabilities,
    Environment,
    Group,
    Individual,
    NetworkLink,
    Preferences,
    RepresentationEdge,
    Representative,
    WorldState,
    network_link_key,
)
from political_sim.core.random import SeededRandom
from political_sim.experiments.analysis import belief_snapshot, intent_snapshot, preference_snapshot
from political_sim.simulation.engine import SimulationEngine
from political_sim.simulation.systems.decision import (
    ConstraintPolicy,
    decide,
    decision_context_from_view,
)
from political_sim.simulation.systems.information import (
    INFORMATION_FORWARD,
    GroupObservation,
    deliver,
    require_actor_view,
)
from tests.test_information import weighted_world
from tests.test_transmission import chain_world

ROOT = Path(__file__).resolve().parents[1]


class CoreContractTests(unittest.TestCase):
    def test_contract_text_is_frozen(self) -> None:
        self.assertEqual(
            CORE_CONTRACT,
            (
                "Reality ≠ Belief",
                "Actor cannot observe WorldState",
                "Actor only decides from permitted information",
                "Intent ≠ Action",
                "Intent does not mutate WorldState",
                "WorldState mutation → ActionResolver",
                "Accepted mutation → EventLog",
                "Multiple conflicting signals ≠ automatic averaging",
                "Multiple beliefs ≠ automatic averaging",
                "Information forwarding is explicit",
                "Hop count does not imply attenuation",
                "Constraint precedence is experimental policy",
            ),
        )
        self.assertEqual(
            INTENT_TRACE,
            "Every representative records one action_intent on every tick.",
        )

    def test_01_reality_is_separate_from_belief(self) -> None:
        running = SimulationEngine(weighted_world(), 0, information_quality=1.0)
        running.run(1)
        belief = running.world.beliefs[("R1", "G1")].estimated_preference.power
        running.intervene_preference("I01", "power", 0.0)
        self.assertEqual(running.world.individuals["I01"].preferences.power, 0.0)
        self.assertEqual(running.world.beliefs[("R1", "G1")].estimated_preference.power, belief)
        self.assertNotEqual(running.world.individuals["I02"].preferences.power, belief)

    def test_02_actor_cannot_observe_world_state(self) -> None:
        world = weighted_world()
        with self.assertRaises(TypeError):
            require_actor_view(world)
        with self.assertRaises(TypeError):
            decision_context_from_view(world)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            decide(world)  # type: ignore[arg-type]
        source = (ROOT / "political_sim" / "simulation" / "systems" / "decision.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("WorldState", source)

    def test_03_decision_uses_only_the_context(self) -> None:
        source = (ROOT / "political_sim" / "simulation" / "systems" / "decision.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("generate_observations", source)
        self.assertNotIn("representation_edges", source)
        running = SimulationEngine(
            weighted_world(),
            0,
            information_quality=1.0,
            decision_constraints={"R1": ("delay",)},
        )
        running.run(1)
        self.assertEqual(_cause(running, "R1"), "constraint:delay")
        self.assertNotIn("1.0", _information(running, "R1"))

    def test_04_intent_is_not_an_action(self) -> None:
        from political_sim.core.actions import Action

        running = SimulationEngine(weighted_world(), 0, information_quality=1.0)
        running.submit(Action("support", "R1", ("G1",)))
        running.run(1)
        types = [event.event_type for event in running.event_log if event.actors == ("R1",)]
        self.assertIn("action_intent", types)
        self.assertIn("action_accepted", types)
        self.assertNotIn("action_rejected", types)
        accepted = [event for event in running.event_log if event.event_type == "action_accepted"]
        self.assertEqual(accepted[0].cause, "admitted")
        self.assertEqual(accepted[0].state_change, ())
        self.assertLess(types.index("action_intent"), types.index("action_accepted"))
        self.assertEqual(_cause(running, "R1"), "baseline:support")

    def test_05_intent_does_not_mutate_world_state(self) -> None:
        running = SimulationEngine(chain_world(2), 0, information_quality=1.0)
        before = preference_snapshot(running.world)
        running.run(2)
        self.assertEqual(preference_snapshot(running.world), before)
        intents = intent_snapshot(running.event_log)
        self.assertGreaterEqual(len(intents), 4)
        self.assertTrue(all(record[4] == () for record in intents))

    def test_06_mutation_goes_through_the_resolver(self) -> None:
        users = [
            path.relative_to(ROOT / "political_sim").as_posix()
            for path in (ROOT / "political_sim").rglob("*.py")
            if "with mutation_scope()" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(users, ["core/actions/action_resolver.py"])
        with self.assertRaises(Exception):
            weighted = weighted_world()
            engine = SimulationEngine(weighted, 0)
            engine.world.individuals["I01"].preferences.power = 0.2

    def test_07_accepted_mutation_must_be_logged(self) -> None:
        running = SimulationEngine(weighted_world(), 0, information_quality=1.0)
        running.run(1)
        running.intervene_preference("I01", "security", 0.25)
        self.assertTrue(any(event.event_type == "belief_updated" for event in running.event_log))
        self.assertTrue(
            any(event.event_type == "experiment_intervention" for event in running.event_log)
        )

        class _Accepts(ActionResolver):
            def _apply(self, world: WorldState, action: object) -> bool:
                del world, action
                return True

        from political_sim.core.actions import Action

        log = EventLog()
        with self.assertRaises(RuntimeError) as raised:
            _Accepts().resolve(
                weighted_world(),
                Action("vote", "R1", ("G1",)),
                tick=1,
                events=log,
                rng=SeededRandom(0),
            )
        self.assertIn("EventLog", str(raised.exception))
        self.assertEqual(len(log), 0)

    def test_08_conflicting_signals_are_not_averaged(self) -> None:
        agreed, agreed_conflicts = deliver(
            (
                _observation("R1", 0.8),
                _observation("R2", 0.8),
            ),
            1.0,
            (_link("R1", "C"), _link("R2", "C")),
        )
        self.assertEqual(agreed_conflicts, ())
        agreed_for_c = [signal for signal, _cause in agreed if signal.observer_id == "C"]
        self.assertEqual(len(agreed_for_c), 1)
        self.assertEqual(agreed_for_c[0].preference.power, 0.8)
        _disagreed, conflicts = deliver(
            (
                _observation("R1", 1.0),
                _observation("R2", 0.0),
            ),
            1.0,
            (_link("R1", "C"), _link("R2", "C")),
        )
        self.assertEqual(conflicts, (("C", "G1"),))
        self.assertFalse(any(signal.observer_id == "C" for signal, _cause in _disagreed))

    def test_09_multiple_beliefs_are_not_averaged(self) -> None:
        link = NetworkLink("R2", "R1", INFORMATION_FORWARD)
        world = WorldState(
            individuals={
                "I01": Individual("I01", Preferences(1, 1, 1, 1, 1), Capabilities(0, 0, 0, 0, 0)),
                "I02": Individual("I02", Preferences(0, 0, 0, 0, 0), Capabilities(0, 0, 0, 0, 0)),
            },
            groups={"G1": Group("G1", ("I01",)), "G2": Group("G2", ("I02",))},
            organizations={},
            representatives={"R1": Representative("R1"), "R2": Representative("R2")},
            factions={},
            coalitions={},
            institutions={},
            representation_edges={
                ("R1", "G1"): _edge("R1", "G1"),
                ("R2", "G2"): _edge("R2", "G2"),
            },
            resources={},
            networks={network_link_key(link): link},
            beliefs={},
            environment=Environment(0, 0, 0, 0),
        )
        running = SimulationEngine(world, 0, information_quality=1.0)
        running.run(1)
        self.assertEqual(running.world.beliefs[("R1", "G1")].estimated_preference.power, 1.0)
        self.assertEqual(running.world.beliefs[("R1", "G2")].estimated_preference.power, 0.0)
        self.assertEqual(_cause(running, "R1"), "ambiguous_beliefs")

    def test_10_forwarding_is_explicit(self) -> None:
        membership = NetworkLink("R1", "R2", "organization_membership")
        source = chain_world(2)
        world = WorldState(
            individuals=dict(source.individuals),
            groups=dict(source.groups),
            organizations={},
            representatives=dict(source.representatives),
            factions={},
            coalitions={},
            institutions={},
            representation_edges=dict(source.representation_edges),
            resources={},
            networks={network_link_key(membership): membership},
            beliefs={},
            environment=Environment(0, 0, 0, 0),
        )
        running = SimulationEngine(world, 0, information_quality=1.0)
        running.run(1)
        self.assertEqual(set(running.world.beliefs), {("R1", "G1")})

    def test_11_hop_count_does_not_attenuate(self) -> None:
        shallow = SimulationEngine(chain_world(1), 0, information_quality=0.5)
        deep = SimulationEngine(chain_world(4), 0, information_quality=0.5)
        shallow.run(1)
        deep.run(1)
        self.assertEqual(shallow.world.beliefs[("R1", "G1")].estimated_preference.power, 0.5)
        for observer_id in ("R1", "R2", "R3", "R4"):
            self.assertEqual(
                deep.world.beliefs[(observer_id, "G1")].estimated_preference.power,
                0.5,
            )
        self.assertNotEqual(deep.world.beliefs[("R4", "G1")].estimated_preference.power, 0.0625)

    def test_12_constraint_precedence_is_a_policy(self) -> None:
        early = ConstraintPolicy("early-seek", ("seek_information", "delay", "abstain"))
        early_delay = ConstraintPolicy("early-delay", ("delay", "seek_information", "abstain"))
        constraints = {"R1": ("delay", "seek_information")}
        first = SimulationEngine(
            weighted_world(),
            0,
            information_quality=1.0,
            decision_constraints=constraints,
            constraint_policy=early,
        )
        second = SimulationEngine(
            weighted_world(),
            0,
            information_quality=1.0,
            decision_constraints=constraints,
            constraint_policy=early_delay,
        )
        first.run(1)
        second.run(1)
        self.assertEqual(belief_snapshot(first.world), belief_snapshot(second.world))
        self.assertEqual(preference_snapshot(first.world), preference_snapshot(second.world))
        self.assertEqual(_cause(first, "R1"), "constraint:seek_information")
        self.assertEqual(_cause(second, "R1"), "constraint:delay")

    def test_every_representative_emits_one_intent_each_tick(self) -> None:
        source = chain_world(1)
        representatives = dict(source.representatives)
        representatives["R2"] = Representative("R2")
        world = WorldState(
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
            beliefs={},
            environment=Environment(0, 0, 0, 0),
        )
        running = SimulationEngine(world, 0, information_quality=1.0)
        running.run(3)
        for tick in (1, 2, 3):
            for observer_id in ("R1", "R2"):
                matches = [
                    event
                    for event in running.event_log
                    if event.event_type == "action_intent"
                    and event.tick == tick
                    and event.actors == (observer_id,)
                ]
                self.assertEqual(len(matches), 1)
        self.assertEqual(_cause(running, "R2"), "no_belief")


def _cause(engine: SimulationEngine, observer_id: str) -> str:
    matches = [
        event
        for event in engine.event_log
        if event.event_type == "action_intent" and event.actors == (observer_id,)
    ]
    return matches[-1].cause


def _information(engine: SimulationEngine, observer_id: str) -> str:
    matches = [
        event
        for event in engine.event_log
        if event.event_type == "action_intent" and event.actors == (observer_id,)
    ]
    return " ".join(matches[-1].available_information)


def _observation(observer_id: str, power: float) -> GroupObservation:
    preference = Preferences(power, power, power, power, power)
    return GroupObservation(observer_id, "G1", preference, Capabilities(0, 0, 0, 0, 0))


def _link(source_id: str, target_id: str) -> NetworkLink:
    return NetworkLink(source_id, target_id, INFORMATION_FORWARD)


def _edge(representative_id: str, group_id: str) -> RepresentationEdge:
    return RepresentationEdge(representative_id, group_id, 0, 0, 0, 0, 0, 0, 0)


if __name__ == "__main__":
    unittest.main()
