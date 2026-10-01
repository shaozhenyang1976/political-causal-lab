"""真实状态到信念的传递。

代表者观察其所代表的群体。群体的真实信号使用规范第 7 节的基线权重：

    w_i = 0.5 + 0.5 * influence_i

这只用来定义“群体此刻的真实偏好/能力”，不是代表漂移，也不使用 fidelity、
accountability 或 trust。

生成误差是当前实验规范，不是随机噪声：

    G(p, e) = clamp(p - e, 0, 1)

它只作用在偏好信号上，不改真实偏好，也不改能力信号。
e = 0 时，生成信号等于真实群体信号。

第一跳使用 I_up = q * I_generated。
q 是本次模拟的 information_quality，不是 RepresentationEdge 上的字段。
q 不会把生成信号拉回真实值。

以后的跳沿 information_forward 复制。fidelity 为 1 时原样复制；小于 1 时，每一跳把已经收到的载荷再乘一次 fidelity。第一跳不乘 fidelity。
不读取边的 fidelity、trust、information_up 或 information_down。
只有 kind 为 information_forward 的网络链接才会转发。
成员关系、代表关系、组织成员关系都不是传播通道。
两条内容不同的信号到达同一个 (观察者, 对象) 时不平均，这一对不写入信念。

忠诚没有真实信号，估计值固定为 0。
模拟器在生成观察时可以读取 True State。
传出的 TransmittedSignal 和 ActorView 不再携带真实状态。
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from political_sim.core.bounds import require_unit_interval
from political_sim.core.models.belief import Belief
from political_sim.core.models.group import Group
from political_sim.core.models.individual import (
    CAPABILITY_FIELDS,
    PREFERENCE_FIELDS,
    Capabilities,
    Individual,
    Preferences,
)
from political_sim.core.models.world_state import NetworkLink, WorldState

INFORMATION_FORWARD = "information_forward"
DIRECT_TRANSMISSION = "information_transmission"
FORWARDED_TRANSMISSION = "information_forward"
GENERATION_RULE = "G(p, e) = clamp(p - e, 0, 1)"
GENERATION_ERROR_ROLE = (
    "generation_error is a system experiment parameter for signal generation, "
    "not actor bias, intentional distortion, or trust."
)
QUALITY_RULE = (
    "information_quality = 1 does not mean the signal is true. "
    "It means the system does not further reduce an already generated signal."
)
FIDELITY_RULE = (
    "Each information_forward hop multiplies the already received payload by fidelity. "
    "The first hop does not. fidelity = 1 leaves that payload unchanged."
)


@dataclass(frozen=True)
class GroupObservation:
    """模拟器内部的真实信号。不能交给行动者。"""

    observer_id: str
    subject_id: str
    preference: Preferences
    capability: Capabilities


@dataclass(frozen=True)
class TransmittedSignal:
    """行动者实际收到的信号。里面没有真实状态。"""

    observer_id: str
    subject_id: str
    preference: Preferences
    capability: Capabilities
    information_quality: float


@dataclass(frozen=True)
class ActorView:
    """行动者可读的信念。没有 WorldState，也没有群体成员的真实偏好。"""

    observer_id: str
    beliefs: tuple[Belief, ...]


def influence_weight(influence: float) -> float:
    return 0.5 + 0.5 * influence


def aggregate_preferences(world: WorldState, group: Group) -> Preferences:
    return Preferences(**_aggregate(world, group, PREFERENCE_FIELDS, _read_preference))


def aggregate_capabilities(world: WorldState, group: Group) -> Capabilities:
    return Capabilities(**_aggregate(world, group, CAPABILITY_FIELDS, _read_capability))


def generate_observations(world: WorldState) -> tuple[GroupObservation, ...]:
    observations: list[GroupObservation] = []
    for edge in world.representation_edges.values():
        group = world.groups.get(edge.represented_entity_id)
        if group is None:
            continue
        observations.append(
            GroupObservation(
                observer_id=edge.representative_id,
                subject_id=group.id,
                preference=aggregate_preferences(world, group),
                capability=aggregate_capabilities(world, group),
            )
        )
    return tuple(observations)


def apply_generation_error(
    observation: GroupObservation, generation_error: float
) -> GroupObservation:
    """把真实群体信号变成生成信号。不读取 q，也不写回 WorldState。"""

    error = require_unit_interval("generation_error", generation_error)
    return GroupObservation(
        observer_id=observation.observer_id,
        subject_id=observation.subject_id,
        preference=_displace_preferences(observation.preference, error),
        capability=observation.capability,
    )


def generation_record(observation: GroupObservation, generation_error: float) -> tuple[str, ...]:
    """事件里只写生成后的偏好和误差参数，不写真实值。"""

    error = require_unit_interval("generation_error", generation_error)
    generated = tuple(
        f"generated_preference.{field}={getattr(observation.preference, field)!r}"
        for field in PREFERENCE_FIELDS
    )
    return (f"generation_error={error!r}",) + generated


def transmit(observation: GroupObservation, information_quality: float) -> TransmittedSignal:
    quality = require_unit_interval("information_quality", information_quality)
    return TransmittedSignal(
        observer_id=observation.observer_id,
        subject_id=observation.subject_id,
        preference=_scale_preferences(observation.preference, quality),
        capability=_scale_capabilities(observation.capability, quality),
        information_quality=quality,
    )


def deliver(
    observations: tuple[GroupObservation, ...],
    information_quality: float,
    links: tuple[NetworkLink, ...],
    fidelity: float = 1.0,
) -> tuple[tuple[tuple[TransmittedSignal, str], ...], tuple[tuple[str, str], ...]]:
    """第一跳只乘 q。之后每一跳 information_forward 再乘一次 fidelity。

    fidelity 为 1 时，后续跳原样复制。不读取 RepresentationEdge。
    """

    fidelity_value = require_unit_interval("fidelity", fidelity)
    direct = tuple(transmit(observation, information_quality) for observation in observations)
    adjacency = _forward_adjacency(links)
    delivered: dict[tuple[str, str], TransmittedSignal] = {}
    ambiguous: set[tuple[str, str]] = set()
    queue: list[TransmittedSignal] = []
    for signal in direct:
        key = (signal.observer_id, signal.subject_id)
        current = delivered.get(key)
        if current is None:
            delivered[key] = signal
            queue.append(signal)
        elif not _same_payload(current, signal):
            ambiguous.add(key)
            delivered.pop(key, None)
    direct_keys = set(delivered)
    head = 0
    while head < len(queue):
        signal = queue[head]
        head += 1
        key = (signal.observer_id, signal.subject_id)
        if key in ambiguous or delivered.get(key) is not signal:
            continue
        for target_id in adjacency.get(signal.observer_id, ()):
            downstream = (target_id, signal.subject_id)
            if downstream in ambiguous:
                continue
            copy = _forward_payload(signal, target_id, fidelity_value)
            current = delivered.get(downstream)
            if current is None:
                delivered[downstream] = copy
                queue.append(copy)
            elif not _same_payload(current, copy):
                ambiguous.add(downstream)
                delivered.pop(downstream, None)
    ordered: list[tuple[TransmittedSignal, str]] = []
    for signal in queue:
        key = (signal.observer_id, signal.subject_id)
        if key in ambiguous or delivered.get(key) is not signal:
            continue
        cause = DIRECT_TRANSMISSION if key in direct_keys else FORWARDED_TRANSMISSION
        ordered.append((signal, cause))
    return tuple(ordered), tuple(sorted(ambiguous))


def belief_from_signal(signal: TransmittedSignal) -> Belief:
    return Belief(
        observer_id=signal.observer_id,
        subject_id=signal.subject_id,
        estimated_preference=signal.preference,
        estimated_capability=signal.capability,
        estimated_loyalty=0.0,
        estimated_information=signal.information_quality,
    )


def preference_distance(true_preference: Preferences, estimated: Preferences) -> float:
    total = sum(
        abs(getattr(true_preference, field) - getattr(estimated, field))
        for field in PREFERENCE_FIELDS
    )
    return total / len(PREFERENCE_FIELDS)


def signal_record(signal: TransmittedSignal) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """事件里只写收到的信号，不写真实值。"""

    received = tuple(
        f"received_preference.{field}={getattr(signal.preference, field)!r}"
        for field in PREFERENCE_FIELDS
    )
    changed = tuple(
        f"belief.estimated_preference.{field}={getattr(signal.preference, field)!r}"
        for field in PREFERENCE_FIELDS
    )
    return received, changed


def actor_view(world: WorldState, observer_id: str) -> ActorView:
    beliefs = tuple(
        belief for belief in world.beliefs.values() if belief.observer_id == observer_id
    )
    return ActorView(observer_id=observer_id, beliefs=beliefs)


def require_actor_view(value: object) -> ActorView:
    if not isinstance(value, ActorView):
        raise TypeError("actors can read ActorView only, not True State")
    return value


def _aggregate(world: WorldState, group: Group, fields: tuple[str, ...], read) -> dict[str, float]:
    totals = {field: 0.0 for field in fields}
    weight_sum = 0.0
    for member_id in group.member_ids:
        member = world.individuals[member_id]
        weight = influence_weight(member.capabilities.influence)
        weight_sum += weight
        for field in fields:
            totals[field] += weight * read(member, field)
    if weight_sum == 0.0:
        raise ValueError(f"group {group.id} has zero influence weight")
    return {field: totals[field] / weight_sum for field in fields}


def _read_preference(member: Individual, field: str) -> float:
    return getattr(member.preferences, field)


def _read_capability(member: Individual, field: str) -> float:
    return getattr(member.capabilities, field)


def _scale_preferences(preference: Preferences, quality: float) -> Preferences:
    return Preferences(
        **{field: quality * getattr(preference, field) for field in PREFERENCE_FIELDS}
    )


def _displace_preferences(preference: Preferences, error: float) -> Preferences:
    return Preferences(
        **{
            field: _clamp_unit(getattr(preference, field) - error)
            for field in PREFERENCE_FIELDS
        }
    )


def _clamp_unit(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _scale_capabilities(capability: Capabilities, quality: float) -> Capabilities:
    return Capabilities(
        **{field: quality * getattr(capability, field) for field in CAPABILITY_FIELDS}
    )


def _forward_adjacency(links: tuple[NetworkLink, ...]) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, set[str]] = {}
    for link in links:
        if not isinstance(link, NetworkLink):
            raise TypeError("transmission links must be NetworkLink")
        if link.kind != INFORMATION_FORWARD:
            continue
        grouped.setdefault(link.source_id, set()).add(link.target_id)
    return {source: tuple(sorted(targets)) for source, targets in grouped.items()}


def _forward_payload(
    signal: TransmittedSignal, target_id: str, fidelity: float
) -> TransmittedSignal:
    if fidelity == 1.0:
        return replace(signal, observer_id=target_id)
    return TransmittedSignal(
        observer_id=target_id,
        subject_id=signal.subject_id,
        preference=_scale_preferences(signal.preference, fidelity),
        capability=_scale_capabilities(signal.capability, fidelity),
        information_quality=signal.information_quality,
    )


def _same_payload(left: TransmittedSignal, right: TransmittedSignal) -> bool:
    return (
        left.subject_id == right.subject_id
        and left.preference == right.preference
        and left.capability == right.capability
        and left.information_quality == right.information_quality
    )
