"""沙盘场景生成器（规范第 52–55 节）。

场景种子在这里只喂给场景随机流。
SimulationEngine 会用同一个种子另建一条模拟随机流，不接续这里已经消耗的数字。
因此以后改生成器的抽样次数，不会把后续 Tick 的随机序列整体错位。

随机抽取顺序属于 SCENARIO_VERSION。顺序变化时要升级版本号。

抽取顺序：
1. I01..I20。每人先按 power, wealth, ideology, security, status 抽偏好，
   再按 information, organization, influence, coercion, wealth 抽能力。
2. OrgA、OrgB。按 ORGANIZATION_STATE_FIELDS 的顺序抽标量，含 resource_pool。
3. (R1, G1) .. (R4, G4)。按 EDGE_QUALITY_FIELDS 抽质量。duration 固定为 0。
4. I01..I20 的资源存量。组织资源复用第 2 步的 resource_pool，不再抽一次。
5. 环境：economic_conditions, resource_availability, external_threats,
   institutional_conditions。

未写明的初始标量使用 SeededRandom.uniform(0, 1)，区间是 [0, 1)。
规范第 53 节的 “relatively high” 没有给阈值。当前假设是：
被强调的偏好维度来自 [0.55, 1)，其余偏好维度来自 [0, 0.45)。
拓扑不随 seed 变化。代表者是 20 名个体之外的 4 个实体。
派系没有初始成员，联盟和信念初始为空。
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
    """生成规范第 52 节的初始沙盘。历史场景不在这里。"""

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
