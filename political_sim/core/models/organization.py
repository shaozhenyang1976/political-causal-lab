"""Organization：协调结构（规范第 10 节）。"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import (
    as_finite_float,
    require_id_sequence,
    require_non_empty_str,
    require_non_negative,
    require_unit_interval,
)
from political_sim.core.mutation import SealedModel

# 规范第 10 节列出的状态变量。membership 单独存放。
ORGANIZATION_STATE_FIELDS = (
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
)

_UNIT_INTERVAL_FIELDS = frozenset({"internal_cohesion"})
_NON_NEGATIVE_FIELDS = frozenset({"resource_pool", "organizational_power"})


@dataclass
class Organization(SealedModel):
    """组织状态。

    internal_cohesion 使用规范对 cohesion 的 [0, 1] 约束。
    resource_pool 与 organizational_power 只要求 >= 0。
    其余变量规范没有给出范围，只要求是有限实数。
    hierarchy 没有定义成树或层级图，因此只保存标量。
    """

    id: str
    membership: tuple[str, ...]
    hierarchy: float
    discipline: float
    communication: float
    recruitment: float
    retention: float
    sanction: float
    resource_pool: float
    internal_cohesion: float
    organizational_capacity: float
    organizational_power: float
    legitimacy: float

    def __post_init__(self) -> None:
        self.id = require_non_empty_str("organization.id", self.id)
        self.membership = require_id_sequence("organization.membership", self.membership)
        for field in ORGANIZATION_STATE_FIELDS:
            setattr(self, field, self._coerce(field, getattr(self, field)))
        self._seal()

    def check_invariants(self) -> None:
        require_non_empty_str("organization.id", self.id)
        require_id_sequence("organization.membership", self.membership)
        for field in ORGANIZATION_STATE_FIELDS:
            self._coerce(field, getattr(self, field))

    def _coerce(self, field: str, value: object) -> float:
        label = f"organization.{field}"
        if field in _UNIT_INTERVAL_FIELDS:
            return require_unit_interval(label, value)
        if field in _NON_NEGATIVE_FIELDS:
            return require_non_negative(label, value)
        return as_finite_float(label, value)
