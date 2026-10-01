"""行动必须经过 ActionResolver，才能写回 WorldState。"""

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
