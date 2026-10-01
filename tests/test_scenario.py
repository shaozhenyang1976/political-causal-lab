"""Sandbox generator: the structure of specification sections 52–55, and the sampling assumptions stated for this step."""

from __future__ import annotations

import random
import unittest
from unittest.mock import patch

from political_sim import MODEL_VERSION
from political_sim.core.mutation import DirectMutationError
from political_sim.core.models import (
    CAPABILITY_FIELDS,
    EDGE_QUALITY_FIELDS,
    ORGANIZATION_STATE_FIELDS,
    PREFERENCE_FIELDS,
    NetworkLink,
    network_link_key,
)
from political_sim.core.random import SeededRandom
from political_sim.scenarios.sandbox import ScenarioGenerator


def topology(world: object) -> object:
    return (
        tuple(world.individuals),
        {group_id: group.member_ids for group_id, group in world.groups.items()},
        {org_id: org.membership for org_id, org in world.organizations.items()},
        tuple(world.representatives),
        {faction_id: faction.member_ids for faction_id, faction in world.factions.items()},
        tuple(world.coalitions),
        tuple(world.institutions),
        tuple(world.representation_edges),
        tuple(world.networks),
        tuple(world.beliefs),
    )


class ScenarioTests(unittest.TestCase):
    def test_seed_zero_stream_is_pinned(self) -> None:
        world = ScenarioGenerator().generate(0)
        individual = world.individuals["I01"]
        self.assertEqual(individual.preferences.power, 0.37998983318627166)
        self.assertEqual(individual.preferences.security, 0.6665125376318335)
        self.assertEqual(world.organizations["OrgA"].hierarchy, 0.44535218971882984)
        self.assertEqual(
            world.representation_edges[("R1", "G1")].fidelity, 0.31617713722134233
        )
        self.assertEqual(world.resources["I01"], 0.8718638357105861)
        self.assertEqual(world.environment.economic_conditions, 0.008897082049078797)

    def test_versions(self) -> None:
        self.assertEqual(MODEL_VERSION, "0.2")
        self.assertEqual(ScenarioGenerator.SCENARIO_VERSION, "sandbox-0.2")

    def test_sandbox_counts_and_relations(self) -> None:
        world = ScenarioGenerator().generate(0)
        world.validate()
        self.assertEqual(tuple(world.individuals), tuple(f"I{index:02d}" for index in range(1, 21)))
        self.assertEqual(tuple(world.groups), ("G1", "G2", "G3", "G4"))
        self.assertEqual(tuple(world.representatives), ("R1", "R2", "R3", "R4"))
        self.assertEqual(tuple(world.organizations), ("OrgA", "OrgB"))
        self.assertEqual(tuple(world.factions), ("FactionA", "FactionB"))
        self.assertEqual(tuple(world.institutions), ("Inst1",))
        self.assertEqual(world.coalitions, {})
        self.assertEqual(world.beliefs, {})
        self.assertTrue(set(world.representatives).isdisjoint(world.individuals))

        members: list[str] = []
        for group_number, group_id in enumerate(("G1", "G2", "G3", "G4"), start=1):
            expected = tuple(f"I{index:02d}" for index in range((group_number - 1) * 5 + 1, group_number * 5 + 1))
            self.assertEqual(world.groups[group_id].member_ids, expected)
            members.extend(expected)
        self.assertEqual(members, list(world.individuals))

        self.assertEqual(world.organizations["OrgA"].membership, ("R1", "R2"))
        self.assertEqual(world.organizations["OrgB"].membership, ("R3", "R4"))
        for index in range(1, 5):
            edge = world.representation_edges[(f"R{index}", f"G{index}")]
            self.assertEqual(edge.representative_id, f"R{index}")
            self.assertEqual(edge.represented_entity_id, f"G{index}")
            self.assertEqual(edge.duration, 0)
        for faction in world.factions.values():
            self.assertEqual(faction.member_ids, ())

    def test_group_preference_emphasis(self) -> None:
        world = ScenarioGenerator().generate(0)
        emphasis = {"G1": "security", "G2": "wealth", "G3": "status", "G4": "ideology"}
        for group_id, field in emphasis.items():
            for member_id in world.groups[group_id].member_ids:
                prefs = world.individuals[member_id].preferences
                emphasized = getattr(prefs, field)
                others = [getattr(prefs, name) for name in PREFERENCE_FIELDS if name != field]
                self.assertGreaterEqual(emphasized, 0.55)
                self.assertLess(emphasized, 1.0)
                for other in others:
                    self.assertGreaterEqual(other, 0.0)
                    self.assertLess(other, 0.45)
                self.assertGreater(emphasized, max(others))
                caps = world.individuals[member_id].capabilities
                for name in CAPABILITY_FIELDS:
                    value = getattr(caps, name)
                    self.assertGreaterEqual(value, 0.0)
                    self.assertLess(value, 1.0)

    def test_preference_wealth_is_not_capability_wealth(self) -> None:
        individual = ScenarioGenerator().generate(0).individuals["I01"]
        original = individual.capabilities.wealth
        with self.assertRaises(DirectMutationError):
            individual.preferences.wealth = 0.0 if individual.preferences.wealth != 0.0 else 1.0
        self.assertEqual(individual.capabilities.wealth, original)

    def test_initial_scalars_use_the_documented_ranges(self) -> None:
        world = ScenarioGenerator().generate(1)
        for organization in world.organizations.values():
            for field in ORGANIZATION_STATE_FIELDS:
                value = getattr(organization, field)
                self.assertGreaterEqual(value, 0.0)
                self.assertLess(value, 1.0)
        for edge in world.representation_edges.values():
            for field in EDGE_QUALITY_FIELDS:
                value = getattr(edge, field)
                self.assertGreaterEqual(value, 0.0)
                self.assertLess(value, 1.0)
        for amount in world.resources.values():
            self.assertGreaterEqual(amount, 0.0)
            self.assertLess(amount, 1.0)
        self.assertEqual(
            set(world.resources),
            set(world.individuals) | set(world.organizations),
        )
        for org_id, organization in world.organizations.items():
            self.assertEqual(world.resources[org_id], organization.resource_pool)
        for field in world.environment.__dataclass_fields__:
            value = getattr(world.environment, field)
            self.assertGreaterEqual(value, 0.0)
            self.assertLess(value, 1.0)

    def test_network_copies_only_specified_relations(self) -> None:
        world = ScenarioGenerator().generate(0)
        self.assertEqual(len(world.networks), 28)
        self.assertEqual(
            {link.kind for link in world.networks.values()},
            {"group_membership", "representation", "organization_membership"},
        )
        membership = NetworkLink(source_id="I01", target_id="G1", kind="group_membership")
        representation = NetworkLink(source_id="R1", target_id="G1", kind="representation")
        organization = NetworkLink(source_id="R1", target_id="OrgA", kind="organization_membership")
        self.assertEqual(world.networks[network_link_key(membership)], membership)
        self.assertEqual(world.networks[network_link_key(representation)], representation)
        self.assertEqual(world.networks[network_link_key(organization)], organization)

    def test_same_seed_is_identical_and_independent(self) -> None:
        first = ScenarioGenerator().generate(1)
        second = ScenarioGenerator().generate(1)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first.individuals["I01"], second.individuals["I01"])
        self.assertEqual(ScenarioGenerator().generate(-3), ScenarioGenerator().generate(-3))

    def test_different_seeds_keep_topology_and_change_values(self) -> None:
        left = ScenarioGenerator().generate(1)
        right = ScenarioGenerator().generate(2)
        self.assertEqual(topology(left), topology(right))
        self.assertNotEqual(left, right)

    def test_rng_draw_order_is_part_of_the_scenario_version(self) -> None:
        calls: list[tuple[float, float]] = []
        original = SeededRandom.uniform

        def spy(rng: SeededRandom, low: float, high: float) -> float:
            calls.append((low, high))
            return original(rng, low, high)

        with patch.object(SeededRandom, "uniform", spy):
            ScenarioGenerator().generate(0)

        expected: list[tuple[float, float]] = []
        emphasis = {"G1": "security", "G2": "wealth", "G3": "status", "G4": "ideology"}
        for group_number in range(1, 5):
            emphasized = emphasis[f"G{group_number}"]
            for _member in range(5):
                for field in PREFERENCE_FIELDS:
                    if field == emphasized:
                        expected.append((0.55, 1.0))
                    else:
                        expected.append((0.0, 0.45))
                expected.extend([(0.0, 1.0)] * len(CAPABILITY_FIELDS))
        expected.extend([(0.0, 1.0)] * len(ORGANIZATION_STATE_FIELDS) * 2)
        expected.extend([(0.0, 1.0)] * len(EDGE_QUALITY_FIELDS) * 4)
        expected.extend([(0.0, 1.0)] * 20)
        expected.extend([(0.0, 1.0)] * 4)
        self.assertEqual(calls, expected)

    def test_generation_does_not_change_global_random(self) -> None:
        random.seed(99)
        before = random.getstate()
        ScenarioGenerator().generate(99)
        self.assertEqual(random.getstate(), before)

    def test_seed_type_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            ScenarioGenerator().generate(True)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
