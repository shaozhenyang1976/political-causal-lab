"""Group：利益聚合单位（规范第 6 节）。"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import require_id_sequence, require_non_empty_str
from political_sim.core.mutation import SealedModel


@dataclass
class Group(SealedModel):
    """成员是 Individual 的 id。

    群体利益和凝聚力是后续计算，不存放在这个类里。
    规范中的“若干”没有给出下限，因此允许空成员列表。
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
