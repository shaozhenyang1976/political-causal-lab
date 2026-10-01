"""Sandbox scenario generator (specification sections 52–55).

The scenario seed feeds only the scenario stream here.
SimulationEngine builds a separate simulation stream from the same seed and
does not continue the numbers already consumed here.
Changing how many draws the generator makes therefore does not shift the
random sequence of a later tick as a whole.

Draw order belongs to SCENARIO_VERSION. A change of order requires a version bump.

Draw order:
1. I01..I20. Each person draws preferences in the order power, wealth,
   ideology, security, status, then capabilities in the order information,
   organization, influence, coercion, wealth.
2. OrgA and OrgB. Scalars are drawn in ORGANIZATION_STATE_FIELDS order,
   including resource_pool.
3. (R1, G1) through (R4, G4). Qualities are drawn from EDGE_QUALITY_FIELDS.
   duration is fixed at 0.
4. Resource stocks for I01..I20. Organizational resources reuse the
   resource_pool drawn in step 2 and are not drawn again.
5. Environment: economic_conditions, resource_availability, external_threats,
   institutional_conditions.

An initial scalar that is not otherwise specified uses SeededRandom.uniform(0, 1),
on the interval [0, 1).
Section 53's "relatively high" states no threshold. The current assumption is
that an emphasized preference component is drawn from [0.55, 1) and every other
preference component from [0, 0.45).
Topology does not vary with the seed. The four representatives are entities
in addition to the twenty individuals.
Factions have no initial members. Coalitions and beliefs start empty.
"""

from __future__ import annotations

from political_sim.core.models.faction import Faction
from political_sim.core.models.group import Group
from political_sim.core.models.individual import (
    CAPABILITY_FIELDS,
    PREFERENCE_FIELDS,
    Capabilities,
    Individual,
    Preferences,
)
from political_sim.core.models.institution import Institution
from political_sim.core.models.organization import ORGANIZATION_STATE_FIELDS, Organization
from political_sim.core.models.representation import (
    EDGE_QUALITY_FIELDS,
    RepresentationEdge,
    representation_edge_key,
)
from political_sim.core.models.representative import Representative
from political_sim.core.models.world_state import (
    Environment,
    NetworkLink,
    WorldState,
    network_link_key,
)
from political_sim.core.random.seeded_random import SeededRandom

EMPHASIZED_PREFERENCE_LOW = 0.55
EMPHASIZED_PREFERENCE_HIGH = 1.0
OTHER_PREFERENCE_LOW = 0.0
OTHER_PREFERENCE_HIGH = 0.45
UNIT_LOW = 0.0
UNIT_HIGH = 1.0

GROUP_EMPHASIS = {
    "G1": "security",
    "G2": "wealth",
    "G3": "status",
    "G4": "ideology",
}

KIND_GROUP_MEMBERSHIP = "group_membership"
KIND_REPRESENTATION = "representation"
KIND_ORGANIZATION_MEMBERSHIP = "organization_membership"


class ScenarioGenerator:
    """Builds the initial sandbox of specification section 52. Historical scenarios are not built here."""

    SCENARIO_VERSION = "sandbox-0.2"

    def generate(self, seed: int) -> WorldState:
        rng = SeededRandom(seed)
        individuals = self._individuals(rng)
        organizations = self._organizations(rng)
        edges = self._edges(rng)
        resources = self._resources(rng, individuals, organizations)
        environment = self._environment(rng)
        groups = self._groups()
        return WorldState(
            individuals=individuals,
            groups=groups,
            organizations=organizations,
            representatives=self._representatives(),
            factions=self._factions(),
            coalitions={},
            institutions=self._institutions(),
            representation_edges=edges,
            resources=resources,
            networks=self._networks(groups, edges, organizations),
            beliefs={},
            environment=environment,
        )

    def _individuals(self, rng: SeededRandom) -> dict[str, Individual]:
        individuals: dict[str, Individual] = {}
        for index in range(1, 21):
            group_id = f"G{(index - 1) // 5 + 1}"
            individual_id = f"I{index:02d}"
            individuals[individual_id] = Individual(
                id=individual_id,
                preferences=self._preferences(rng, GROUP_EMPHASIS[group_id]),
                capabilities=self._capabilities(rng),
            )
        return individuals

    def _preferences(self, rng: SeededRandom, emphasized: str) -> Preferences:
        values = {
            field: rng.uniform(
                EMPHASIZED_PREFERENCE_LOW if field == emphasized else OTHER_PREFERENCE_LOW,
                EMPHASIZED_PREFERENCE_HIGH if field == emphasized else OTHER_PREFERENCE_HIGH,
            )
            for field in PREFERENCE_FIELDS
        }
        return Preferences(**values)

    def _capabilities(self, rng: SeededRandom) -> Capabilities:
        values = {field: rng.uniform(UNIT_LOW, UNIT_HIGH) for field in CAPABILITY_FIELDS}
        return Capabilities(**values)

    def _groups(self) -> dict[str, Group]:
        groups: dict[str, Group] = {}
        for group_number in range(1, 5):
            start = (group_number - 1) * 5 + 1
            member_ids = tuple(f"I{index:02d}" for index in range(start, start + 5))
            group_id = f"G{group_number}"
            groups[group_id] = Group(id=group_id, member_ids=member_ids)
        return groups

    def _representatives(self) -> dict[str, Representative]:
        return {f"R{index}": Representative(id=f"R{index}") for index in range(1, 5)}

    def _organizations(self, rng: SeededRandom) -> dict[str, Organization]:
        return {
            "OrgA": self._organization(rng, "OrgA", ("R1", "R2")),
            "OrgB": self._organization(rng, "OrgB", ("R3", "R4")),
        }

    def _organization(
        self, rng: SeededRandom, organization_id: str, membership: tuple[str, ...]
    ) -> Organization:
        values = {
            field: rng.uniform(UNIT_LOW, UNIT_HIGH) for field in ORGANIZATION_STATE_FIELDS
        }
        return Organization(id=organization_id, membership=membership, **values)

    def _factions(self) -> dict[str, Faction]:
        return {
            "FactionA": Faction(id="FactionA"),
            "FactionB": Faction(id="FactionB"),
        }

    def _institutions(self) -> dict[str, Institution]:
        return {"Inst1": Institution(id="Inst1")}

    def _edges(self, rng: SeededRandom) -> dict[tuple[str, str], RepresentationEdge]:
        edges: dict[tuple[str, str], RepresentationEdge] = {}
        for index in range(1, 5):
            edge = RepresentationEdge(
                representative_id=f"R{index}",
                represented_entity_id=f"G{index}",
                duration=0,
                **{field: rng.uniform(UNIT_LOW, UNIT_HIGH) for field in EDGE_QUALITY_FIELDS},
            )
            edges[representation_edge_key(edge)] = edge
        return edges

    def _resources(
        self,
        rng: SeededRandom,
        individuals: dict[str, Individual],
        organizations: dict[str, Organization],
    ) -> dict[str, float]:
        resources = {
            individual_id: rng.uniform(UNIT_LOW, UNIT_HIGH) for individual_id in individuals
        }
        for organization_id, organization in organizations.items():
            resources[organization_id] = organization.resource_pool
        return resources

    def _environment(self, rng: SeededRandom) -> Environment:
        return Environment(
            economic_conditions=rng.uniform(UNIT_LOW, UNIT_HIGH),
            resource_availability=rng.uniform(UNIT_LOW, UNIT_HIGH),
            external_threats=rng.uniform(UNIT_LOW, UNIT_HIGH),
            institutional_conditions=rng.uniform(UNIT_LOW, UNIT_HIGH),
        )

    def _networks(
        self,
        groups: dict[str, Group],
        edges: dict[tuple[str, str], RepresentationEdge],
        organizations: dict[str, Organization],
    ) -> dict[tuple[str, str, str], NetworkLink]:
        links: dict[tuple[str, str, str], NetworkLink] = {}
        for group in groups.values():
            for member_id in group.member_ids:
                link = NetworkLink(
                    source_id=member_id,
                    target_id=group.id,
                    kind=KIND_GROUP_MEMBERSHIP,
                )
                links[network_link_key(link)] = link
        for edge in edges.values():
            link = NetworkLink(
                source_id=edge.representative_id,
                target_id=edge.represented_entity_id,
                kind=KIND_REPRESENTATION,
            )
            links[network_link_key(link)] = link
        for organization in organizations.values():
            for member_id in organization.membership:
                link = NetworkLink(
                    source_id=member_id,
                    target_id=organization.id,
                    kind=KIND_ORGANIZATION_MEMBERSHIP,
                )
                links[network_link_key(link)] = link
        return links
