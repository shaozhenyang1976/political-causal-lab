"""Representative. The specification defines no preference or capability fields for this entity."""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import require_non_empty_str
from political_sim.core.mutation import SealedModel


@dataclass
class Representative(SealedModel):
    id: str

    def __post_init__(self) -> None:
        self.id = require_non_empty_str("representative.id", self.id)
        self._seal()

    def check_invariants(self) -> None:
        require_non_empty_str("representative.id", self.id)
