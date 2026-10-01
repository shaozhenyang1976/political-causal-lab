"""从事件日志核对资源守恒。不运行模拟，也不写世界。"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from political_sim.core.events.event_log import EventLog

CONSERVATION_RULE = "resources_before + accepted_actions = resources_after"
RESOURCE_OUTCOMES = (
    "rejected_action adds 0 resources.",
    "no_action adds 0 resources.",
    "support adds 1 resource.",
    "oppose adds 1 resource.",
)


@dataclass(frozen=True)
class ResourceAccount:
    resources_before: float
    accepted_actions: int
    rejected_actions: int
    resources_after: float
    predicted: tuple[tuple[str, float], ...]


def resource_account(
    before: Mapping[str, float],
    event_log: EventLog,
    after: Mapping[str, float],
) -> ResourceAccount:
    predicted = dict(before)
    accepted = 0
    rejected = 0
    consequences = 0
    for event in event_log:
        if event.event_type == "action_rejected":
            rejected += 1
            continue
        if event.event_type == "action_consequence":
            consequences += 1
            continue
        if event.event_type != "action_accepted":
            continue
        if len(event.actors) != 1:
            raise ValueError("accepted action records one actor")
        actor_id = event.actors[0]
        predicted[actor_id] = predicted.get(actor_id, 0.0) + 1.0
        accepted += 1
    if consequences != accepted:
        raise ValueError("each accepted action has one consequence")
    return ResourceAccount(
        resources_before=sum(before.values()),
        accepted_actions=accepted,
        rejected_actions=rejected,
        resources_after=sum(after.values()),
        predicted=tuple(sorted(predicted.items())),
    )
