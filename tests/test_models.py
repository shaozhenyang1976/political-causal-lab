"""Fields of the core data classes and the ranges stated in the specification."""

from __future__ import annotations

import unittest

from political_sim.core.mutation import DirectMutationError
from political_sim.core.models import (
    CAPABILITY_FIELDS,
    EDGE_QUALITY_FIELDS,
    ORGANIZATION_STATE_FIELDS,
    PREFERENCE_FIELDS,
    Belief,
    Capabilities,
    Coalition,
    Environment,
    Faction,
    Group,
    Individual,
    Institution,
    NetworkLink,
    Organization,
    Preferences,
    RepresentationEdge,
    Representative,
    WorldState,
)


def preferences(**overrides: float) -> Preferences:
    values = {field: 0.0 for field in PREFERENCE_FIELDS}
    values.update(overrides)
    return Preferences(**values)


def capabilities(**overrides: float) -> Capabilities:
    values = {field: 0.0 for field in CAPABILITY_FIELDS}
    values.update(overrides)
    return Capabilities(**values)


def organization(**overrides: object) -> Organization:
    values: dict[str, object] = {field: 0.0 for field in ORGANIZATION_STATE_FIELDS}
    values.update(id="OrgA", membership=("R1",))
    values.update(overrides)
    return Organization(**values)


def edge(**overrides: object) -> RepresentationEdge:
    values: dict[str, object] = {field: 0.5 for field in EDGE_QUALITY_FIELDS}
    values.update(representative_id="R1", represented_entity_id="G1", duration=0)
    values.update(overrides)
    return RepresentationEdge(**values)


class SchemaTests(unittest.TestCase):
    def test_field_names_match_the_spec_lists(self) -> None:
        self.assertEqual(
            PREFERENCE_FIELDS, ("power", "wealth", "ideology", "security", "status")
        )
        self.assertEqual(
            CAPABILITY_FIELDS,
            ("information", "organization", "influence", "coercion", "wealth"),
        )
        self.assertEqual(
            tuple(Individual.__dataclass_fields__),
            ("id", "preferences", "capabilities"),
        )
        self.assertEqual(tuple(Group.__dataclass_fields__), ("id", "member_ids"))
        self.assertEqual(tuple(Representative.__dataclass_fields__), ("id",))
        self.assertEqual(tuple(Faction.__dataclass_fields__), ("id", "member_ids"))
        self.assertEqual(tuple(Coalition.__dataclass_fields__), ("id", "member_ids"))
        self.assertEqual(tuple(Institution.__dataclass_fields__), ("id",))
        self.assertEqual(
            tuple(Organization.__dataclass_fields__),
            ("id", "membership", *ORGANIZATION_STATE_FIELDS),
        )
        self.assertEqual(
            ORGANIZATION_STATE_FIELDS,
            (
                "hierarchy",
                "discipline",
                "communication",
                "recruitment",
                "retention",
                "sanction",
                "resource_pool",
                "internal_cohesion",
                "organizational_capacity",
                "organizational_power",
                "legitimacy",
            ),
        )
        self.assertEqual(
            tuple(RepresentationEdge.__dataclass_fields__),
            (
                "representative_id",
                "represented_entity_id",
                *EDGE_QUALITY_FIELDS,
                "duration",
            ),
        )
        self.assertEqual(
            EDGE_QUALITY_FIELDS,
            (
                "fidelity",
                "accountability",
                "information_up",
                "information_down",
                "trust",
                "dependency",
            ),
        )
        self.assertEqual(
            tuple(Belief.__dataclass_fields__),
            (
                "observer_id",
                "subject_id",
                "estimated_preference",
                "estimated_capability",
                "estimated_loyalty",
                "estimated_information",
            ),
        )
        self.assertEqual(
            tuple(WorldState.__dataclass_fields__),
            (
                "individuals",
                "groups",
                "organizations",
                "representatives",
                "factions",
                "coalitions",
                "institutions",
                "representation_edges",
                "resources",
                "networks",
                "beliefs",
                "environment",
            ),
        )
        self.assertEqual(
            tuple(Environment.__dataclass_fields__),
            (
                "economic_conditions",
                "resource_availability",
                "external_threats",
                "institutional_conditions",
            ),
        )
        self.assertEqual(
            tuple(NetworkLink.__dataclass_fields__),
            ("source_id", "target_id", "kind"),
        )

    def test_models_have_no_builtin_value_labels(self) -> None:
        classes = (
            Individual,
            Group,
            Organization,
            Representative,
            Faction,
            Coalition,
            Institution,
            RepresentationEdge,
            Belief,
            WorldState,
        )
        banned = {"good", "evil", "hero", "villain"}
        for cls in classes:
            self.assertTrue(banned.isdisjoint(cls.__dataclass_fields__))


class PreferenceAndCapabilityTests(unittest.TestCase):
    def test_preferences_accept_unit_interval_endpoints(self) -> None:
        prefs = preferences(power=0, wealth=1, ideology=0, security=1, status=0)
        self.assertEqual(prefs.power, 0.0)
        self.assertEqual(prefs.wealth, 1.0)

    def test_preferences_reject_values_outside_unit_interval(self) -> None:
        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            preferences(power=1.1)
        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            preferences(security=-0.01)
        with self.assertRaises(ValueError):
            preferences(ideology=float("nan"))
        with self.assertRaises(ValueError):
            preferences(status=float("inf"))

    def test_preferences_reject_bool(self) -> None:
        with self.assertRaises(TypeError):
            preferences(power=True)

    def test_capabilities_are_not_forced_into_unit_interval(self) -> None:
        caps = Capabilities(information=2.0, organization=-3.0, influence=0.0, coercion=4.0, wealth=0.0)
        self.assertEqual(caps.information, 2.0)
        self.assertEqual(caps.organization, -3.0)
        with self.assertRaises(ValueError):
            Capabilities(
                information=float("nan"),
                organization=0,
                influence=0,
                coercion=0,
                wealth=0,
            )

    def test_preference_and_capability_are_different_objects(self) -> None:
        individual = Individual(id="I01", preferences=preferences(wealth=0.25), capabilities=capabilities(wealth=0.75))
        self.assertEqual(individual.preferences.wealth, 0.25)
        self.assertEqual(individual.capabilities.wealth, 0.75)
        with self.assertRaises(DirectMutationError):
            individual.preferences.wealth = 0.1
        self.assertEqual(individual.capabilities.wealth, 0.75)
        self.assertFalse(hasattr(individual.preferences, "coercion"))
        self.assertFalse(hasattr(individual.capabilities, "ideology"))


class MembershipTests(unittest.TestCase):
    def test_group_allows_empty_membership_and_rejects_duplicates(self) -> None:
        self.assertEqual(Group(id="G1").member_ids, ())
        with self.assertRaisesRegex(ValueError, "duplicate"):
            Group(id="G1", member_ids=("I01", "I01"))

    def test_ids_must_be_non_empty_strings(self) -> None:
        with self.assertRaises(ValueError):
            Representative(id=" ")
        with self.assertRaises(ValueError):
            Faction(id="")


class OrganizationBoundTests(unittest.TestCase):
    def test_cohesion_power_and_resources_follow_spec_bounds(self) -> None:
        organization(internal_cohesion=0, resource_pool=0, organizational_power=50)
        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            organization(internal_cohesion=1.01)
        with self.assertRaisesRegex(ValueError, ">="):
            organization(resource_pool=-0.1)
        with self.assertRaisesRegex(ValueError, ">="):
            organization(organizational_power=-0.1)

    def test_unspecified_organization_fields_stay_unbounded(self) -> None:
        org = organization(hierarchy=-3, discipline=1.2, sanction=8)
        self.assertEqual(org.hierarchy, -3.0)
        self.assertEqual(org.discipline, 1.2)
        self.assertEqual(org.sanction, 8.0)
        with self.assertRaises(ValueError):
            organization(communication=float("nan"))


class RepresentationAndBeliefTests(unittest.TestCase):
    def test_edge_qualities_are_unit_interval_and_duration_is_a_count(self) -> None:
        created = edge(fidelity=0, dependency=1, duration=0)
        self.assertEqual(created.duration, 0)
        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            edge(fidelity=1.01)
        with self.assertRaises(TypeError):
            edge(duration=0.0)
        with self.assertRaises(TypeError):
            edge(duration=True)
        with self.assertRaisesRegex(ValueError, ">="):
            edge(duration=-1)

    def test_belief_reuses_preference_bounds_and_leaves_loyalty_unbounded(self) -> None:
        belief = Belief(
            observer_id="I01",
            subject_id="I02",
            estimated_preference=preferences(),
            estimated_capability=Capabilities(
                information=2, organization=0, influence=0, coercion=0, wealth=0
            ),
            estimated_loyalty=1.5,
            estimated_information=-1,
        )
        self.assertEqual(belief.estimated_loyalty, 1.5)
        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            Belief(
                observer_id="I01",
                subject_id="I02",
                estimated_preference=preferences(power=2),
                estimated_capability=capabilities(),
                estimated_loyalty=0,
                estimated_information=0,
            )
        with self.assertRaises(TypeError):
            Belief(
                observer_id="I01",
                subject_id="I02",
                estimated_preference=preferences(),
                estimated_capability={"influence": 0},
                estimated_loyalty=0,
                estimated_information=0,
            )

    def test_network_kind_is_an_open_string(self) -> None:
        link = NetworkLink(source_id="I01", target_id="G1", kind="alliance")
        self.assertEqual(link.kind, "alliance")
        with self.assertRaises(ValueError):
            NetworkLink(source_id="I01", target_id="G1", kind="")

    def test_environment_requires_finite_numbers_only(self) -> None:
        environment = Environment(
            economic_conditions=3,
            resource_availability=-2,
            external_threats=0,
            institutional_conditions=1,
        )
        self.assertEqual(environment.economic_conditions, 3.0)
        with self.assertRaises(ValueError):
            Environment(
                economic_conditions=float("nan"),
                resource_availability=0,
                external_threats=0,
                institutional_conditions=0,
            )


if __name__ == "__main__":
    unittest.main()
