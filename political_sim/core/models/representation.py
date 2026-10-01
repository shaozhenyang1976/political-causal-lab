"""RepresentationEdge (specification section 11)."""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import (
    require_non_empty_str,
    require_non_negative_int,
    require_unit_interval,
)
from political_sim.core.mutation import SealedModel

EDGE_QUALITY_FIELDS = (
    "fidelity",
    "accountability",
    "information_up",
    "information_down",
    "trust",
    "dependency",
)


def representation_edge_key(edge: RepresentationEdge) -> tuple[str, str]:
    """The specification defines no edge id. The dictionary key is (representative_id, represented_entity_id)."""

    return (edge.representative_id, edge.represented_entity_id)


@dataclass
class RepresentationEdge(SealedModel):
    representative_id: str
    represented_entity_id: str
    fidelity: float
    accountability: float
    information_up: float
    information_down: float
    trust: float
    dependency: float
    duration: int

    def __post_init__(self) -> None:
        self.representative_id = require_non_empty_str(
            "representation.representative_id", self.representative_id
        )
        self.represented_entity_id = require_non_empty_str(
            "representation.represented_entity_id", self.represented_entity_id
        )
        for field in EDGE_QUALITY_FIELDS:
            setattr(
                self,
                field,
                require_unit_interval(f"representation.{field}", getattr(self, field)),
            )
        self.duration = require_non_negative_int("representation.duration", self.duration)
        self._seal()

    def check_invariants(self) -> None:
        require_non_empty_str("representation.representative_id", self.representative_id)
        require_non_empty_str("representation.represented_entity_id", self.represented_entity_id)
        for field in EDGE_QUALITY_FIELDS:
            require_unit_interval(f"representation.{field}", getattr(self, field))
        require_non_negative_int("representation.duration", self.duration)
