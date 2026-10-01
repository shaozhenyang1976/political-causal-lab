"""WorldState：模拟器的真实状态（规范第 24 节）。"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import as_finite_float, require_non_empty_str, require_non_negative
from political_sim.core.models.belief import Belief, belief_key
from political_sim.core.models.coalition import Coalition
from political_sim.core.models.faction import Faction
from political_sim.core.models.group import Group
from political_sim.core.models.individual import Individual
from political_sim.core.models.institution import Institution
from political_sim.core.models.organization import Organization
from political_sim.core.models.representation import RepresentationEdge, representation_edge_key
from political_sim.core.models.representative import Representative
from political_sim.core.mutation import GuardedDict, SealedModel

ACTOR_COLLECTIONS = (
    "individuals",
    "groups",
    "organizations",
    "representatives",
    "factions",
    "coalitions",
    "institutions",
)

COLLECTION_FIELDS = ACTOR_COLLECTIONS + (
    "representation_edges",
    "resources",
    "networks",
    "beliefs",
)


def network_link_key(link: NetworkLink) -> tuple[str, str, str]:
    return (link.kind, link.source_id, link.target_id)


@dataclass
class Environment(SealedModel):
    """Tick 01 列出的环境状态。

    规范没有给出量纲。这里只要求有限实数。
    random events 是过程产物，不作为初始字段。
    """

    economic_conditions: float
    resource_availability: float
    external_threats: float
    institutional_conditions: float

    def __post_init__(self) -> None:
        for field in (
            "economic_conditions",
            "resource_availability",
            "external_threats",
            "institutional_conditions",
        ):
            setattr(self, field, as_finite_float(f"environment.{field}", getattr(self, field)))
        self._seal()

    def check_invariants(self) -> None:
        for field in (
            "economic_conditions",
            "resource_availability",
            "external_threats",
            "institutional_conditions",
        ):
            as_finite_float(f"environment.{field}", getattr(self, field))


@dataclass
class NetworkLink(SealedModel):
    """结构链接。kind 是开放字符串，核心不规定政治关系枚举。"""

    source_id: str
    target_id: str
    kind: str

    def __post_init__(self) -> None:
        self.source_id = require_non_empty_str("network.source_id", self.source_id)
        self.target_id = require_non_empty_str("network.target_id", self.target_id)
        self.kind = require_non_empty_str("network.kind", self.kind)
        self._seal()

    def check_invariants(self) -> None:
        require_non_empty_str("network.source_id", self.source_id)
        require_non_empty_str("network.target_id", self.target_id)
        require_non_empty_str("network.kind", self.kind)


@dataclass
class WorldState(SealedModel):
    individuals: dict[str, Individual]
    groups: dict[str, Group]
    organizations: dict[str, Organization]
    representatives: dict[str, Representative]
    factions: dict[str, Faction]
    coalitions: dict[str, Coalition]
    institutions: dict[str, Institution]
    representation_edges: dict[tuple[str, str], RepresentationEdge]
    resources: dict[str, float]
    networks: dict[tuple[str, str, str], NetworkLink]
    beliefs: dict[tuple[str, str], Belief]
    environment: Environment

    def __post_init__(self) -> None:
        self.resources = {
            owner_id: require_non_negative(f"resources[{owner_id}]", amount)
            for owner_id, amount in self.resources.items()
        }
        self.validate()
        for name in COLLECTION_FIELDS:
            setattr(self, name, GuardedDict(getattr(self, name)))
        self._seal()

    def known_actor_ids(self) -> set[str]:
        return set(self._actor_ids())

    def validate(self) -> None:
        """只读检查范围、标识和引用。"""

        if not isinstance(self.environment, Environment):
            raise TypeError("environment must be Environment")
        self.environment.check_invariants()

        self._require_entities("individuals", self.individuals, Individual, lambda item: item.id)
        self._require_entities("groups", self.groups, Group, lambda item: item.id)
        self._require_entities(
            "organizations", self.organizations, Organization, lambda item: item.id
        )
        self._require_entities(
            "representatives", self.representatives, Representative, lambda item: item.id
        )
        self._require_entities("factions", self.factions, Faction, lambda item: item.id)
        self._require_entities("coalitions", self.coalitions, Coalition, lambda item: item.id)
        self._require_entities(
            "institutions", self.institutions, Institution, lambda item: item.id
        )
        self._require_entities(
            "representation_edges",
            self.representation_edges,
            RepresentationEdge,
            representation_edge_key,
        )
        self._require_entities("networks", self.networks, NetworkLink, network_link_key)
        self._require_entities("beliefs", self.beliefs, Belief, belief_key)

        actor_ids = self._actor_ids()
        self._require_member_refs()
        self._require_edge_refs(actor_ids)
        self._require_endpoint_refs(actor_ids)
        self._require_belief_refs(actor_ids)
        self._require_resources(actor_ids)

    def _require_entities(self, name: str, mapping: object, cls: type, key_of) -> None:
        if not isinstance(mapping, dict):
            raise TypeError(f"{name} must be a dict")
        for key, item in mapping.items():
            if not isinstance(item, cls):
                raise TypeError(f"{name}[{key!r}] must be {cls.__name__}")
            item.check_invariants()
            expected = key_of(item)
            if key != expected:
                raise ValueError(f"{name} key {key!r} does not match {expected!r}")

    def _actor_ids(self) -> dict[str, str]:
        seen: dict[str, str] = {}
        for name in ACTOR_COLLECTIONS:
            for entity_id in getattr(self, name):
                if entity_id in seen:
                    raise ValueError(f"duplicate id {entity_id!r} in {seen[entity_id]} and {name}")
                seen[entity_id] = name
        return seen

    def _require_member_refs(self) -> None:
        for group in self.groups.values():
            for member_id in group.member_ids:
                if member_id not in self.individuals:
                    raise ValueError(
                        f"group {group.id} member {member_id!r} is not an individual"
                    )
        actor_ids = set(self._actor_ids())
        for organization in self.organizations.values():
            for member_id in organization.membership:
                if member_id not in actor_ids:
                    raise ValueError(
                        f"organization {organization.id} member {member_id!r} does not exist"
                    )
        for faction in self.factions.values():
            for member_id in faction.member_ids:
                if member_id not in actor_ids:
                    raise ValueError(f"faction {faction.id} member {member_id!r} does not exist")
        for coalition in self.coalitions.values():
            for member_id in coalition.member_ids:
                if member_id not in actor_ids:
                    raise ValueError(
                        f"coalition {coalition.id} member {member_id!r} does not exist"
                    )

    def _require_edge_refs(self, actor_ids: dict[str, str]) -> None:
        for edge in self.representation_edges.values():
            if edge.representative_id not in self.representatives:
                raise ValueError(
                    f"representation representative {edge.representative_id!r} does not exist"
                )
            if edge.represented_entity_id not in actor_ids:
                raise ValueError(
                    f"represented entity {edge.represented_entity_id!r} does not exist"
                )

    def _require_endpoint_refs(self, actor_ids: dict[str, str]) -> None:
        for link in self.networks.values():
            if link.source_id not in actor_ids or link.target_id not in actor_ids:
                raise ValueError(
                    f"network link {(link.kind, link.source_id, link.target_id)!r} "
                    "has an unknown endpoint"
                )

    def _require_belief_refs(self, actor_ids: dict[str, str]) -> None:
        for belief in self.beliefs.values():
            if belief.observer_id not in actor_ids or belief.subject_id not in actor_ids:
                raise ValueError(
                    f"belief {(belief.observer_id, belief.subject_id)!r} has an unknown actor"
                )

    def _require_resources(self, actor_ids: dict[str, str]) -> None:
        if not isinstance(self.resources, dict):
            raise TypeError("resources must be a dict")
        for owner_id, amount in self.resources.items():
            if owner_id not in actor_ids:
                raise ValueError(f"resource owner {owner_id!r} does not exist")
            require_non_negative(f"resources[{owner_id}]", amount)
