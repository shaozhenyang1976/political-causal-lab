"""Coalition：动态合作关系（规范第 21 节）。"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import require_id_sequence, require_non_empty_str
from political_sim.core.mutation import SealedModel


@dataclass
class Coalition(SealedModel):
    id: str
    member_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.id = require_non_empty_str("coalition.id", self.id)
        self.member_ids = require_id_sequence("coalition.member_ids", self.member_ids)
        self._seal()

    def check_invariants(self) -> None:
        require_non_empty_str("coalition.id", self.id)
        require_id_sequence("coalition.member_ids", self.member_ids)
