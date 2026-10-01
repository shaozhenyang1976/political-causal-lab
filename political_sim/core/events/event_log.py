"""EventLog。规范第 62 节要求的事件记录，也是本阶段的 EventSystem。

available_information 只记录行动者已经收到的内容，不记录 True State。
行动意图写入日志，但不写入 WorldState。
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
