"""Institution。

规范第 22 节用例子列出规则种类，没有定义规则语言。
本步只保存 id，不增设规则字段，也不写入任何规则。
"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import require_non_empty_str
from political_sim.core.mutation import SealedModel


@dataclass
class Institution(SealedModel):
    id: str

    def __post_init__(self) -> None:
        self.id = require_non_empty_str("institution.id", self.id)
        self._seal()

    def check_invariants(self) -> None:
        require_non_empty_str("institution.id", self.id)
