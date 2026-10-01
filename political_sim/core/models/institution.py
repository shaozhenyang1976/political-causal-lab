"""Institution.

Specification section 22 lists kinds of rules by example and defines no rule language.
This type stores only an id. It adds no rule field and writes no rule.
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
