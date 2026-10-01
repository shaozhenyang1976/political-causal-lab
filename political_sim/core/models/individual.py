"""Individual：最基本的政治行为单位（规范第 5 节）。"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import as_finite_float, require_non_empty_str, require_unit_interval
from political_sim.core.mutation import SealedModel

PREFERENCE_FIELDS = ("power", "wealth", "ideology", "security", "status")
CAPABILITY_FIELDS = ("information", "organization", "influence", "coercion", "wealth")


@dataclass
class Preferences(SealedModel):
    """P_i。规范 5.1 要求每一维都在 [0, 1]。"""

    power: float
    wealth: float
    ideology: float
    security: float
    status: float

    def __post_init__(self) -> None:
        for field in PREFERENCE_FIELDS:
            setattr(self, field, require_unit_interval(f"preferences.{field}", getattr(self, field)))
        self._seal()

    def check_invariants(self) -> None:
        for field in PREFERENCE_FIELDS:
            require_unit_interval(f"preferences.{field}", getattr(self, field))


@dataclass
class Capabilities(SealedModel):
    """C_i。

    规范 5.2 只列出维度，没有写明取值区间。
    此处只要求有限实数。influence 的权重公式暗示它应落在 [0, 1]，
    但该公式尚未实现，因此不把这个区间写成能力约束。
    """

    information: float
    organization: float
    influence: float
    coercion: float
    wealth: float

    def __post_init__(self) -> None:
        for field in CAPABILITY_FIELDS:
            setattr(self, field, as_finite_float(f"capabilities.{field}", getattr(self, field)))
        self._seal()

    def check_invariants(self) -> None:
        for field in CAPABILITY_FIELDS:
            as_finite_float(f"capabilities.{field}", getattr(self, field))


@dataclass
class Individual(SealedModel):
    id: str
    preferences: Preferences
    capabilities: Capabilities

    def __post_init__(self) -> None:
        self.id = require_non_empty_str("individual.id", self.id)
        if not isinstance(self.preferences, Preferences):
            raise TypeError("individual.preferences must be Preferences")
        if not isinstance(self.capabilities, Capabilities):
            raise TypeError("individual.capabilities must be Capabilities")
        self.preferences.check_invariants()
        self.capabilities.check_invariants()
        self._seal()

    def check_invariants(self) -> None:
        require_non_empty_str("individual.id", self.id)
        if not isinstance(self.preferences, Preferences):
            raise TypeError("individual.preferences must be Preferences")
        if not isinstance(self.capabilities, Capabilities):
            raise TypeError("individual.capabilities must be Capabilities")
        self.preferences.check_invariants()
        self.capabilities.check_invariants()
