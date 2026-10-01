"""WorldState 引用完整性。沙盘人数不是 WorldState 的不变量。"""

from __future__ import annotations

import unittest

from political_sim.core.models import (
    ORGANIZATION_STATE_FIELDS,
    PREFERENCE_FIELDS,
    Belief,
    Capabilities,
    Coalition,
    Environment,
    Faction,
    Group,
    Individual,
    NetworkLink,
    Organization,
    Preferences,
    RepresentationEdge,
    Representative,
    WorldState,
    belief_key,
    network_link_key,
)
from political_sim.core.mutation import DirectMutationError
from political_sim.scenarios.sandbox import ScenarioGenerator


def _individual(individual_id: str) -> Individual:
    return Individual(
        id=individual_id,
        preferences=Preferences(**{field: 0.0 for field in PREFERENCE_FIELDS}),
        capabilities=Capabilities(0, 0, 0, 0, 0),
    )


def empty_world(**overrides: object) -> WorldState:
    data: dict[str, object] = {
        "individuals": {},
        "groups": {},
        "organizations": {},
        "representatives": {},
        "factions": {},
        "coalitions": {},
        "institutions": {},
        "representation_edges": {},
        "resources": {},
        "networks": {},
        "beliefs": {},
        "environment": Environment(0, 0, 0, 0),
    }
    data.update(overrides)
    return WorldState(**data)


class WorldStateTests(unittest.TestCase):
    def test_empty_world_is_referentially_valid(self) -> None:
        world = empty_world()
        world.validate()
        self.assertEqual(world.individuals, {})

    def test_direct_mutation_is_rejected(self) -> None:
        world = ScenarioGenerator().generate(0)
        with self.assertRaises(DirectMutationError):
            world.individuals["I01"].preferences.power = 2
        with self.assertRaises(DirectMutationError):
            world.representation_edges[("R1", "G1")].fidelity = -0.01
        with self.assertRaises(DirectMutationError):
            world.groups["G1"].member_ids = ("R1",)
        with self.assertRaises(DirectMutationError):
            world.resources["ghost"] = 1.0
        with self.assertRaises(DirectMutationError):
            world.resources["I01"] = -1
        with self.assertRaises(DirectMutationError):
            world.representation_edges.pop(("R1", "G1"))
        with self.assertRaises(DirectMutationError):
            world.organizations["OrgA"].discipline = 1.2
        with self.assertRaises(DirectMutationError):
            world.environment.economic_conditions = 3
        world.validate()

    def test_invalid_references_fail_at_construction(self) -> None:
        individual = _individual("I01")
        with self.assertRaisesRegex(ValueError, "does not exist"):
            empty_world(resources={"ghost": 1.0})
        with self.assertRaisesRegex(ValueError, ">="):
            empty_world(individuals={"I01": individual}, resources={"I01": -1})
        edge = RepresentationEdge(
            representative_id="R1",
            represented_entity_id="G1",
            fidelity=0.5,
            accountability=0.5,
            information_up=0.5,
            information_down=0.5,
            trust=0.5,
            dependency=0.5,
            duration=0,
        )
        with self.assertRaisesRegex(ValueError, "does not match"):
            empty_world(representation_edges={("wrong", "G1"): edge})
        with self.assertRaisesRegex(ValueError, "duplicate id"):
            empty_world(
                individuals={"I01": individual},
                representatives={"I01": Representative(id="I01")},
            )
        belief = Belief(
            observer_id="I01",
            subject_id="missing",
            estimated_preference=Preferences(**{field: 0.0 for field in PREFERENCE_FIELDS}),
            estimated_capability=Capabilities(0, 0, 0, 0, 0),
            estimated_loyalty=0,
            estimated_information=0,
        )
        with self.assertRaisesRegex(ValueError, "unknown actor"):
            empty_world(beliefs={belief_key(belief): belief})

    def test_faction_coalition_and_open_network_kind_can_be_constructed(self) -> None:
        individual = _individual("I01")
        organization = Organization(
            id="OrgA",
            membership=("R1",),
            **{field: 0.0 for field in ORGANIZATION_STATE_FIELDS},
        )
        link = NetworkLink(source_id="I01", target_id="R1", kind="alliance")
        world = empty_world(
            individuals={"I01": individual},
            groups={"G2": Group(id="G2", member_ids=("I01",))},
            representatives={"R1": Representative(id="R1")},
            organizations={"OrgA": organization},
            factions={"FactionA": Faction(id="FactionA", member_ids=("I01", "OrgA"))},
            coalitions={"C1": Coalition(id="C1", member_ids=("R1", "G2"))},
            networks={network_link_key(link): link},
        )
        world.validate()
        self.assertEqual(world.factions["FactionA"].member_ids, ("I01", "OrgA"))
        self.assertEqual(world.networks[network_link_key(link)].kind, "alliance")

    def test_group_member_must_exist_at_construction(self) -> None:
        with self.assertRaisesRegex(ValueError, "not an individual"):
            empty_world(groups={"G1": Group(id="G1", member_ids=("I01",))})

    def test_individual_requires_typed_components(self) -> None:
        with self.assertRaises(TypeError):
            Individual(id="I01", preferences={"power": 0}, capabilities=Capabilities(0, 0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
