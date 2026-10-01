"""Organization: a coordination structure (specification section 10)."""

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

# State variables listed in specification section 10. membership is stored separately.
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
    """Organizational state.

    internal_cohesion uses the specification's [0, 1] constraint on cohesion.
    resource_pool and organizational_power are required only to be >= 0.
    The specification states no range for the remaining variables. They must be finite real numbers.
    hierarchy is not defined as a tree or a level graph, so it is stored as a scalar.
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
