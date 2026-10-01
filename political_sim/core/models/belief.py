"""Belief_i(j) = (P̂, Ĉ, L̂, Î) (specification section 17).

Loyalty and information estimates are not written as vectors and have no stated interval, so they are stored as finite real numbers.
The preference estimate reuses Preferences and therefore remains constrained to [0, 1].
"""

from __future__ import annotations

from dataclasses import dataclass

from political_sim.core.bounds import as_finite_float, require_non_empty_str
from political_sim.core.models.individual import Capabilities, Preferences
from political_sim.core.mutation import SealedModel


def belief_key(belief: Belief) -> tuple[str, str]:
    return (belief.observer_id, belief.subject_id)


@dataclass
class Belief(SealedModel):
    observer_id: str
    subject_id: str
    estimated_preference: Preferences
    estimated_capability: Capabilities
    estimated_loyalty: float
    estimated_information: float

    def __post_init__(self) -> None:
        self.observer_id = require_non_empty_str("belief.observer_id", self.observer_id)
        self.subject_id = require_non_empty_str("belief.subject_id", self.subject_id)
        if not isinstance(self.estimated_preference, Preferences):
            raise TypeError("belief.estimated_preference must be Preferences")
        if not isinstance(self.estimated_capability, Capabilities):
            raise TypeError("belief.estimated_capability must be Capabilities")
        self.estimated_preference.check_invariants()
        self.estimated_capability.check_invariants()
        self.estimated_loyalty = as_finite_float("belief.estimated_loyalty", self.estimated_loyalty)
        self.estimated_information = as_finite_float(
            "belief.estimated_information", self.estimated_information
        )
        self._seal()

    def check_invariants(self) -> None:
        require_non_empty_str("belief.observer_id", self.observer_id)
        require_non_empty_str("belief.subject_id", self.subject_id)
        if not isinstance(self.estimated_preference, Preferences):
            raise TypeError("belief.estimated_preference must be Preferences")
        if not isinstance(self.estimated_capability, Capabilities):
            raise TypeError("belief.estimated_capability must be Capabilities")
        self.estimated_preference.check_invariants()
        self.estimated_capability.check_invariants()
        as_finite_float("belief.estimated_loyalty", self.estimated_loyalty)
        as_finite_float("belief.estimated_information", self.estimated_information)
