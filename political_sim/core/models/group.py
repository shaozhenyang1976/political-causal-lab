"""Group: a unit of interest aggregation (specification section 6)."""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import require_id_sequence, require_non_empty_str
from political_sim.core.mutation import SealedModel


@dataclass
class Group(SealedModel):
    """Members are individual ids.

    Group interest and cohesion are later calculations and are not stored on this class.
    The specification's "some number" states no lower bound, so an empty member list is allowed.
    """

    id: str
    member_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.id = require_non_empty_str("group.id", self.id)
        self.member_ids = require_id_sequence("group.member_ids", self.member_ids)
        self._seal()

    def check_invariants(self) -> None:
        require_non_empty_str("group.id", self.id)
        require_id_sequence("group.member_ids", self.member_ids)
