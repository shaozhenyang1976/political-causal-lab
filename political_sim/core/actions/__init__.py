"""An action changes WorldState only by passing through ActionResolver."""

from political_sim.core.actions.action_resolver import (
    ACTION_ADMISSION_RULE,
    ADMISSIBLE_ACTION_TYPES,
    SPEC_ACTION_TYPES,
    Action,
    ActionResolver,
)

__all__ = [
    "ACTION_ADMISSION_RULE",
    "ADMISSIBLE_ACTION_TYPES",
    "SPEC_ACTION_TYPES",
    "Action",
    "ActionResolver",
]
