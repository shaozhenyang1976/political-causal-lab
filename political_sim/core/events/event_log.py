"""EventLog. The event record required by specification section 62, and the EventSystem of this stage.

available_information records only what the actor has already received. It does not record True State.
An action intent is written to the log and is not written to WorldState.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    tick: int
    event_type: str
    actors: tuple[str, ...]
    targets: tuple[str, ...]
    cause: str
    available_information: tuple[str, ...]
    incentives: tuple[str, ...]
    state_change: tuple[str, ...]


class EventLog:
    def __init__(self) -> None:
        self._events: list[Event] = []

    def record(self, event: Event) -> None:
        if not isinstance(event, Event):
            raise TypeError("event must be Event")
        self._events.append(event)

    def __len__(self) -> int:
        return len(self._events)

    def __getitem__(self, index: int) -> Event:
        return self._events[index]

    def __iter__(self):
        return iter(self._events)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EventLog):
            return NotImplemented
        return self._events == other._events

    def as_tuple(self) -> tuple[Event, ...]:
        return tuple(self._events)
