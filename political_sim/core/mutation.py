"""Write gate for WorldState.

Project constraint:

    WorldState is mutable only through authorized state transitions.

The causal chain is:

    Entity → Decision → PoliticalAction → ActionResolver → State Mutation → EventLog

After construction, ordinary assignment is rejected.
An information system, an economic system, or any other system must not
change WorldState directly. It may only propose a state change. ActionResolver
writes that change inside mutation_scope() and records it in the EventLog.
"""

from __future__ import annotations

CONSTITUTION = "WorldState is mutable only through authorized state transitions."
INFORMATION_BOUNDARY = "No actor may directly observe WorldState."
DECISION_BOUNDARY = (
    "Actor decisions must be based only on permitted ActorView / DecisionContext."
)
STATE_MUTATION_BOUNDARY = "WorldState may only be mutated through ActionResolver."
EVENT_BOUNDARY = "Every accepted state mutation must produce an EventLog entry."

from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_mutation_depth: ContextVar[int] = ContextVar("political_sim_mutation_depth", default=0)


class DirectMutationError(RuntimeError):
    """The caller changed constructed state directly, bypassing ActionResolver."""


def ensure_can_mutate(name: str) -> None:
    if _mutation_depth.get() <= 0:
        raise DirectMutationError(
            f"{name} cannot be changed directly; submit an Action through SimulationEngine"
        )


@contextmanager
def mutation_scope() -> Iterator[None]:
    token = _mutation_depth.set(_mutation_depth.get() + 1)
    try:
        yield
    finally:
        _mutation_depth.reset(token)


class SealedModel:
    """Rejects ordinary assignment after construction. The dataclass fields themselves are unchanged."""

    def __setattr__(self, name: str, value: object) -> None:
        if name != "_sealed" and self.__dict__.get("_sealed", False):
            ensure_can_mutate(f"{type(self).__name__}.{name}")
        object.__setattr__(self, name, value)

    def _seal(self) -> None:
        object.__setattr__(self, "_sealed", True)


class GuardedDict(dict):
    """Mapping stored in WorldState. The copy made during construction is not gated. Later insertion, deletion, and replacement must enter mutation_scope."""

    def __init__(self, mapping: Mapping[object, object] | None = None) -> None:
        super().__init__()
        if mapping is not None:
            super().update(mapping)
        self._guard = True

    def _require(self) -> None:
        if getattr(self, "_guard", False):
            ensure_can_mutate("WorldState collection")

    def __setitem__(self, key: object, value: object) -> None:
        self._require()
        super().__setitem__(key, value)

    def __delitem__(self, key: object) -> None:
        self._require()
        super().__delitem__(key)

    def pop(self, key: object, *args: object) -> object:
        self._require()
        return super().pop(key, *args)

    def popitem(self) -> tuple[object, object]:
        self._require()
        return super().popitem()

    def clear(self) -> None:
        self._require()
        super().clear()

    def update(self, *args: object, **kwargs: object) -> None:
        self._require()
        super().update(*args, **kwargs)

    def setdefault(self, key: object, default: object = None) -> object:
        self._require()
        return super().setdefault(key, default)

    def __ior__(self, other: object) -> GuardedDict:
        self._require()
        return super().__ior__(other)
