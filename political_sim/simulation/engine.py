"""SimulationEngine。推进 Tick 的唯一公开入口。

同一个整数种子分成两条互不接续的随机流：

    Scenario Seed
         ├── Scenario Generator → 场景随机流
         └── SimulationEngine   → 模拟随机流

修改场景抽样不会把 Tick 里的随机序列整体错位。
当前信息传递和生成误差都是确定性的，模拟随机流还不会被消耗。
"""

from __future__ import annotations

from political_sim.core.actions.action_resolver import Action, ActionResolver
from political_sim.core.bounds import require_unit_interval
from political_sim.core.events.event_log import EventLog
from political_sim.core.models.individual import PREFERENCE_FIELDS
from political_sim.core.models.world_state import WorldState
from political_sim.core.random.seeded_random import SeededRandom
from political_sim.simulation.systems.decision import (
    EXPERIMENTAL_CONSTRAINT_POLICY,
    ConstraintPolicy,
)
from political_sim.simulation.tick_processor import TickProcessor


def _decision_constraints(
    decision_constraints: dict[str, tuple[str, ...]] | None,
    policy: ConstraintPolicy,
) -> dict[str, tuple[str, ...]]:
    if decision_constraints is None:
        return {}
    normalized: dict[str, tuple[str, ...]] = {}
    for observer_id, constraints in decision_constraints.items():
        if not isinstance(observer_id, str) or observer_id == "":
            raise ValueError("decision constraint actor id must be a non-empty string")
        if not isinstance(constraints, tuple):
            raise TypeError("decision constraints must be a tuple")
        for name in constraints:
            if name not in policy.precedence:
                raise ValueError(f"unknown decision constraint {name!r}")
        if len(constraints) != len(set(constraints)):
            raise ValueError("duplicate decision constraint")
        normalized[observer_id] = constraints
    return normalized


class SimulationEngine:
    def __init__(
        self,
        world: WorldState,
        seed: int,
        information_quality: float = 1.0,
        generation_error: float = 0.0,
        trust: float = 1.0,
        trust_threshold: float = 0.5,
        fidelity: float = 1.0,
        decision_constraints: dict[str, tuple[str, ...]] | None = None,
        constraint_policy: ConstraintPolicy | None = None,
    ) -> None:
        if not isinstance(world, WorldState):
            raise TypeError("world must be WorldState")
        if constraint_policy is None:
            constraint_policy = EXPERIMENTAL_CONSTRAINT_POLICY
        if not isinstance(constraint_policy, ConstraintPolicy):
            raise TypeError("constraint_policy must be ConstraintPolicy")
        self.world = world
        self.seed = seed
        self.information_quality = require_unit_interval("information_quality", information_quality)
        self.generation_error = require_unit_interval("generation_error", generation_error)
        self.trust = require_unit_interval("trust", trust)
        self.trust_threshold = require_unit_interval("trust_threshold", trust_threshold)
        self.fidelity = require_unit_interval("fidelity", fidelity)
        self.constraint_policy = constraint_policy
        self.decision_constraints = _decision_constraints(decision_constraints, constraint_policy)
        self.rng = SeededRandom(seed)
        self.event_log = EventLog()
        self.resolver = ActionResolver()
        self.processor = TickProcessor()
        self.tick = 0
        self._queue: list[Action] = []

    def submit(self, action: Action) -> None:
        if not isinstance(action, Action):
            raise TypeError("action must be Action")
        self._queue.append(action)

    def intervene_preference(self, individual_id: str, field: str, value: float) -> None:
        """实验者改变真实偏好。这不是政治行动，仍然必须经过 ActionResolver 并留下事件。"""

        if field not in PREFERENCE_FIELDS:
            raise ValueError(f"unknown preference field {field!r}")
        self.resolver.commit_preference(
            self.world,
            individual_id=individual_id,
            field=field,
            value=value,
            tick=self.tick,
            events=self.event_log,
        )

    def run(self, steps: int = 1) -> None:
        if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
            raise ValueError("steps must be a non-negative int")
        for _ in range(steps):
            queued = tuple(self._queue)
            self._queue.clear()
            self.tick = self.processor.step(
                tick=self.tick,
                world=self.world,
                actions=queued,
                resolver=self.resolver,
                events=self.event_log,
                rng=self.rng,
                information_quality=self.information_quality,
                generation_error=self.generation_error,
                trust=self.trust,
                trust_threshold=self.trust_threshold,
                fidelity=self.fidelity,
                decision_constraints=self.decision_constraints,
                constraint_policy=self.constraint_policy,
            )
