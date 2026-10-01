# 基线实验规范

状态：**CORE BASELINE — FROZEN**

PR-8 采信门槛单独冻结为 **PR-8 TRUST GATE — FROZEN**。PR-9 后续转发冻结为 **PR-9 FIDELITY — FROZEN**。二者都加在控制条件之上，不改写下面这些 PR-7 含义。其后的显式行动只把资源作为终端结果，不改写这些含义。信任学习和关系网络仍未进入。

冻结范围：

- Reality / Belief separation
- Actor information boundary
- DecisionContext
- Intent semantics
- Intent / Action separation
- State mutation boundary
- Event boundary
- Explicit forwarding
- No automatic hop attenuation
- ConstraintPolicy abstraction
- Generation error semantics
- Tick ordering
- Event-based measurement

本冻结不把 trust 算进信念误差。`fidelity = 1` 时后续转发与 PR-8 相同，因此那时 `transmission_gap` 仍为 0。上面这份 PR-7 控制清单不包含动态 trust、accountability 或 concealment。显式提交的行动和资源后果在 PR-10、PR-11，不改写这里的信息—意图含义。PR-8 的门槛是后来加上的一层，默认通过时控制条件保持原样。

## 控制条件

```text
P
 ↓
G(p, e) = clamp(p - e, 0, 1)
 ↓
q × G(p, e)
 ↓
explicit forward
 ↓
Belief
 ↓
ConstraintPolicy
 ↓
Intent
```

已经确认的因果：

```text
generation error  → belief error
q                  → belief error
hop count          → no additional error
constraint         → intent
Reality change     → next-Tick belief
Belief change      → same-Tick intent
```

## 信息质量

information_quality = 1 does not mean the signal is true. It means the system does not further reduce an already generated signal.

`q = 1` 只表示系统不再降低已经生成的信号。它不表示信念等于真实偏好。因此 `P = 0.8`、`e = 0.2`、`q = 1` 时，生成信号、收到的信号和信念都停留在 `G(p, e)`，真实偏好仍是 `0.8`。

## 生成误差

G(p, e) = clamp(p - e, 0, 1)

`e` 是信号生成过程的系统实验参数，默认 `0`。它只作用于偏好的五个分量，不抽随机数，不修改真实偏好，也不修改能力信号。

`e` 不是行动者偏见，不是有意扭曲，也不是 trust。`e < 0` 直接拒绝。

输入域：

```text
p = 0, e > 0 → 0
p = 1, e = 1 → 0
p = 0.2, e = 0.5 → 0
e = 0 → p
```

## 误差分解

直接观察者：

```text
belief_gap = generation_gap + quality_gap + transmission_gap
```

`fidelity = 1` 时 `transmission_gap = 0`。信念误差归因于生成误差和第一跳质量缩减。跳数本身只决定信号到达谁，不改变载荷。只有显式 `fidelity < 1` 才让后续跳变小。

`generation_gap` 是真实群体信号到 `signal_generated` 的距离。`quality_gap` 是生成信号到第一跳收到值的距离。`fidelity = 1` 时，后续跳复制该收到值。

## 基线

固定真实偏好 `P = 1`，一次只动一个因素。

- 生成误差：`e = 0, 0.1, 0.25, 0.5`，`q = 1`，一跳
- 信息质量：`q = 1, 0.75, 0.5, 0`，`e = 0`，一跳
- 跳数：1 到 4 跳，`e = 0.25`，`q = 0.5`
- 约束：信念不变，只更换 `ConstraintPolicy`

## 时间尺度

| 因果路径 | 当前实现 | 依据 |
| --- | --- | --- |
| Reality → Belief | 干预真实偏好后，下一次生成才使用新偏好。同一拍内，意图看到的是本拍 `belief_update` 之后的信念 | 代码：`information_generation` 先于 `political_action`；`intervene_preference` 记在当前 tick |
| Belief → Intent | 同一 Tick | 代码：`representative_decision` 在 `belief_update` 之后 |
| Intent → Action | 显式提交边界。没有提交就没有 `action_accepted` | 代码，以及实验 4 |
| Action → Consequence | `action_accepted` 不改 WorldState；随后 `action_consequence` 给行动者资源 +1 | 代码，以及 PR-11 |

同一 Tick 的顺序是 `signal_generated`、传输、`belief_updated` 或 `trust_rejected`、`action_intent`，然后才是被提交的行动。意图看到的是本 Tick 已经更新的信念；信任拒绝时不读取信念来决定意图。

`Reality → Belief` 的延迟是：真实偏好写入干预事件之后，旧信念保持到下一次信念更新。`Constraint = delay` 是决策约束，不是这个延迟。两者分开记录。

## PR-8 trust gate

状态：**PR-8 TRUST GATE — FROZEN**

Trust 是进入 DecisionContext 之前的采信门槛，不是第四种信念误差，也不是 `q` 或 `e` 的另一种缩放。`RepresentationEdge.trust` 仍然只被保存，不参与生成、第一跳或转发。实验参数 `t` 与边上的 `trust` 字段不是同一个机制。

```text
received = q × G(p, e)
forward 复制 received

t ≥ τ：belief = received，然后才进入 ConstraintPolicy
t < τ：不把 received 写入 belief，也不删除已有 belief
        intent = seek_information
        cause = trust_rejected
```

默认 `t = 1`、`τ = 0.5`，因此 `t ≥ τ`，控制条件与 PR-7 相同。`t = τ` 也采信。

三条拒绝语义：

- trust rejection ≠ belief error
- trust rejection ≠ constraint delay
- trust rejection ≠ no information

以后的机制不能破坏这六条：

1. Trust does not change signal_generated.
2. Trust does not change received.
3. t >= trust_threshold reproduces the baseline.
4. t < trust_threshold does not overwrite an existing belief.
5. trust_rejected is not part of belief_gap.
6. trust_rejected is not constraint:delay or no_belief.

`trust_rejected` 不是 `constraint:delay`，也不是 `no_belief`。拒绝发生在决策政策之前：即使同时设了 `delay`，原因仍是 `trust_rejected`。通过门槛之后，`delay` 才按原来的决策政策生效。没有收到信号时，原因仍是 `no_belief`。

已有信念在拒绝后保持原值。不采信不会把信念写成 `0`，也不会写成收到的信号。日志里的 `trust_rejected` 事件带有 received，`state_change` 为空。

不把 trust 加进 `belief_gap`。`belief_gap = generation_gap + quality_gap + transmission_gap` 仍然只描述被采信之后的信念数值。测量上分开三件事：信号已经生成、信号已经收到、信念有没有被这次收到的信号替换。

## PR-9 fidelity

状态：**PR-9 FIDELITY — FROZEN**

Fidelity 是后续 `information_forward` 上的显式实验参数，不是 `RepresentationEdge.fidelity`，也不改变 trust。

Each information_forward hop multiplies the already received payload by fidelity. The first hop does not. fidelity = 1 leaves that payload unchanged.

`fidelity = 1` 时，生成信号、第一跳 received、后续载荷、信念、意图、拒绝原因和事件顺序都与 PR-8 相同。跳数本身仍然不造成衰减。只有 `fidelity < 1` 才让后续跳的载荷变小，并允许下游的 `transmission_gap > 0`。第一跳、生成误差、采信门槛和 `ConstraintPolicy` 都不变。直接观察者没有经过 forwarding，因此其 `transmission_gap` 仍为 0。`estimated_information` 保持为 `q`，不随后续 fidelity 连乘下降。

每个机制只作用在自己的因果层：

1. e does not modify q, fidelity, or trust.
2. q does not modify fidelity or trust.
3. fidelity does not modify q or trust.
4. trust does not modify signal or received values.

不在这一步加入信任变化或信任学习。

## PR-10 action boundary

状态：**PR-10 ACTION BOUNDARY — FROZEN**

这一步只回答三件事，不加入政治制度，也不产生后果。

1. 只有 `support` 和 `oppose` 可以从意图进入行动。`abstain`、`delay`、`seek_information` 仍只是意图。
2. 行动必须被显式提交。`ActionResolver` 在引用有效时接纳它，并记下 `action_accepted`。意图事件不会自动变成行动。
3. `action_accepted` 不改变 `WorldState`。该事件的 `state_change` 为空。资源写入不在本节，见 PR-11。

因此仍然是：

- Intent ≠ Action
- Action ≠ Consequence

`vote` 及其他尚未定义后果的行动类型继续被拒绝，原因仍是 `action effect is not implemented`。没有提交行动时，事件顺序与 PR-9 相同。

## PR-11 consequence

状态：**PR-11 CONSEQUENCE — FROZEN**

这一步只打开一条箭头：被接纳的行动产生一个后果。

An admitted action adds one resource unit to its actor. The addition does not change preferences, beliefs, information, fidelity, or trust.

接纳事件保持原样：`action_accepted` 的 `state_change` 仍为空，`available_information` 仍是 `consequence=none`。随后单独写下 `action_consequence`，才把行动者的资源增加 1。`support` 和 `oppose` 使用同一条后果。目标、偏好、信念、生成、转发和采信都不因这条后果改变。

没有被接纳的行动不产生后果。没有提交行动时，世界和事件都与 PR-10 相同。

不在这一步加入信任变化、关系变化、信息变化、声誉或组织后果。

`resources + 1` 不进入生成、信念或意图。下一拍的 `signal_generated` 和 `belief_updated` 仍与没有提交行动时相同。因此这条箭头是 `Action → Resource`，还不是 `Action → Resource → future behavior`。

## PR-12 resource conservation

状态：**PR-12 RESOURCE CONSERVATION — FROZEN**

这一步只测量资源守恒，不选择资源进入哪一个因果层。

resources_before + accepted_actions = resources_after

四种结果固定为：

1. rejected_action adds 0 resources.
2. no_action adds 0 resources.
3. support adds 1 resource.
4. oppose adds 1 resource.

资源仍然不影响行动可用性、决策约束、信息获取、偏好、信任或组织位置。账本定义见 `docs/RESOURCE_SEMANTICS.md`。当前正式名称是 **PR-1~PR-12: OPEN-LOOP BASELINE — FROZEN**。`Resource → ?` 保持断开。PR-13 暂不启动。语义决策记录见 `docs/RESOURCE_SEMANTIC_ADR.md`，答案尚未作出。

## 当前实现对照

本节只记录代码里已经执行的路径。空槽位表示该阶段存在但函数为空。实验 1～4 没有逐槽位重测空阶段。

Tick 顺序来自 `political_sim/simulation/tick_processor.py` 的 `TICK_PHASES`。17 个槽位依次是：`environment_update`、`information_generation`、`information_transmission`、`belief_update`、`incentive_update`、`coalition_evaluation`、`representative_decision`、`organization_decision`、`political_action`、`conflict_bargaining`、`resource_allocation`、`power_recalculation`、`representation_update`、`network_update`、`survival_replacement`、`metrics`、`event_log`。

有执行体的只有六段：

| 阶段 | 读取 | 写入 |
| --- | --- | --- |
| `information_generation` | 代表边、群体成员的偏好与能力；`capabilities.influence` 只进入聚合权重 `0.5 + 0.5 * influence` | 事件 `signal_generated`。不改真实偏好，不读信念、资源、组织、派系、制度 |
| `information_transmission` | 本拍生成信号、`information_quality`、`fidelity`、`kind = information_forward` 的链接 | 不改 WorldState。内容冲突时记 `transmission_ambiguous`，该对不进入本拍交付。不读边上的 `fidelity` 或 `trust` |
| `belief_update` | 本拍交付、全局 `trust` 与 `trust_threshold` | `t ≥ τ` 时写入信念并记 `belief_updated`。`t < τ` 时记 `trust_rejected`，不覆盖已有信念 |
| `representative_decision` | 本拍拒绝表；未拒绝时读取该代表当前存储的信念、约束和 `ConstraintPolicy` | 只记 `action_intent`。不读资源，不改 WorldState |
| `political_action` | 本拍开始前已经 `submit` 的行动，以及行动者、目标是否存在 | `support` / `oppose`：先 `action_accepted`（`consequence=none`，`state_change` 空），再 `action_consequence`（该行动者资源 +1）。其余已知类型拒绝，原因 `action effect is not implemented`。未知类型拒绝，原因 `unknown action type` |
| `event_log` | 无 | 只记 `tick_completed` |

其余 11 个槽位是空函数。资源 +1 发生在 `political_action`，不发生在 `resource_allocation`。

参数是一次运行的全局数：`generation_error`、`information_quality`、`fidelity`、`trust`、`trust_threshold`，都要求落在 `[0, 1]`。`decision_constraints` 按行动者给出。信息、采信、意图和资源结算不消耗随机流。

复现同一次干预：使用同一 `WorldState`、同一上述参数、同一提交序列，调用 `SimulationEngine.run`。比较因果轨迹时对齐事件类型、原因、信念是否写入、意图原因和资源差额。跨实现不要求事件字符串逐字相同。当前 132 项测试锁定的是这一份 Python 实现的回归契约，包括它自己的事件文本。

以下事项是当前模型的能力边界，不是待实现功能，也不是待办：按行动者或按边的信任、网络在运行中改写自己、没有显式提交时的行动分布、长运行产生路径依赖、在 `q = 0` 时再区分 `fidelity`。边上的 `fidelity` 与 `trust`、组织、派系、制度同样不被运行读取。只有一个明确研究问题被这些边界挡住时，才重新审查机制。

已知两处代码注释与实现不一致，本次不改生产代码。`action_resolver.py` 的模块说明仍写后果尚未实现，而 `action_consequence` 已经会给行动者资源 +1。`Capabilities` 的说明仍写影响力权重公式尚未实现，而群体聚合已经使用 `0.5 + 0.5 * influence`。这两句不改变当前执行路径，也不改变实验 1～4 的结论。
