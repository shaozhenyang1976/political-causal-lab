"""Faction：政治行动集团（规范第 20 节）。"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import require_id_sequence, require_non_empty_str
from political_sim.core.mutation import SealedModel


@dataclass
class Faction(SealedModel):
    id: str
    member_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.id = require_non_empty_str("faction.id", self.id)
        self.member_ids = require_id_sequence("faction.member_ids", self.member_ids)
        self._seal()

    def check_invariants(self) -> None:
        require_non_empty_str("faction.id", self.id)
        require_id_sequence("faction.member_ids", self.member_ids)
