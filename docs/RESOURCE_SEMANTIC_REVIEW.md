# Resource Semantic Review

状态：**RESOURCE SEMANTIC REVIEW — FROZEN**

基线仍是 **PR-1~PR-12: OPEN-LOOP BASELINE — FROZEN**。引擎不变，生产代码不变，测试保持 132 / 132，PR-13 未启动。`docs/RESOURCE_SEMANTIC_ADR.md` 的五问仍为 **UNDECIDED**。`Resource → ?` 保持断开。

## 1. 当前定义

`Resource` 是账本存量，不是行为次数本身。

```text
期末 Resource(actor) = initial_resource(actor) + accepted_action_count(actor)
```

- `initial_resource` 由场景写入。账本里没有的行动者，入账时按 0 计。
- `accepted_action_count` 是该行动者被显式提交、通过引用检查、且类型为 `support` 或 `oppose` 的次数。每一次这样的接纳使账本 `+1`。
- `oppose` 与 `support` 的增量相同。行动目标不加这 1。
- 被拒绝的行动和没有提交的行动记 0。
- 意图可以与提交的行动不同。账本记的是被接纳的提交，不是意图。
- 运行中只有 `ActionResolver` 在 `action_consequence` 里做这个 `+1`。它不改变偏好、信念、信息、`fidelity` 或 `trust`。

因此 `accepted_action_count` 是行为事件的计数，`Resource` 是带期初存量的账本变量。二者不能混成一个语义。`Resource = 20` 并不表示做了 20 次被接纳的行动，除非期初存量为 0。

## 2. 候选与结论

| 候选语义 | 当前结论 |
| --- | --- |
| 纯结果指标 | 通过 |
| 行动能力 / 行动资本 | 淘汰 |
| 组织动员资源 | 淘汰 |
| 政治影响代理 | 淘汰 |
| 物质资源 | 淘汰 |
| 信息获取资源 | 淘汰 |

这里的“通过”只表示：在当前已经冻结的操作性定义下，纯结果指标是唯一不需要额外假设、且与现有因果结构一致的语义。它不是“Resource 永远只能是结果变量”的决定。

其余五项若要重新进入候选集，必须提供新的操作性定义或新的机制依据，而不是给现有的 `+1` 换一个名称。

## 3. 淘汰原因

**行动能力 / 行动资本。** 次数是接纳之后的产物。当前接纳不读取余额，所以这个数字并没有表示“因此更能行动”的能力。用产物代表产生它的能力，还缺少单独的机制依据。

**组织动员资源。** `+1` 记在提交者名下。它不改变组织成员、凝聚力或组织自己的资源池。

**政治影响代理。** 影响若要成立，应出现在他人的信念、意图或行动上。这条增量不改变那些量，也区分不了 `support` 与 `oppose`。

**物质资源。** 现有 `+1` 没有消耗、转移、价格或稀缺。期初存量可以另行由场景写入，但不能因此把行动计数解释成物质存量。

**信息获取资源。** 信息路径只由 `e`、`q`、`fidelity` 和 `trust` 决定。行动计数不进入这条路径。

仅凭两个行动者的存量差，例如 2 与 20，也推不出谁获取的信息更多、谁更容易被信任、谁更容易再行动、谁对他人影响更大、或谁的组织能力更强。

## 4. 纯结果指标为何闭合

增量的定义就是被接纳的行动次数。把它读作“该行动者有多少次被接纳的行动”，不需要再假设能力、组织、影响、物质或信息。它没有目标层，没有额外的 tick 位置，也不形成反馈。这与已经冻结的单向链一致：

```text
Explicit Action → ActionResolver → Consequence → Resource
```

`Resource → ?` 仍然断开。

## 5. 本审查没有做的事

- 没有产生新的因果箭头。
- 没有填写 Resource causal contract。
- 五问 ADR 仍为 `UNDECIDED`。
- 132 项测试保持为无反馈骨架的回归底座。
- 生产代码保持不动。

## 6. 冻结后的观察规则

`accepted_action_count` 的语义已经确定：某个 `actor_id` 上，显式提交、通过引用检查、类型为 `support` 或 `oppose` 的被接纳次数。它不需要再被解释成另一种东西。

`Resource` 目前只有账本语义：`initial_resource + accepted_action_count`。它是结果变量。这个事实不能推出它是能力、权力、影响力、组织资源或信息资源。

先有独立机制的操作性需求，再检查 Resource 是否恰好满足；绝不先赋予 Resource 一个用途，再反过来制造机制。

与 Resource 无关的机制可以继续做，但必须同时满足：

```text
New Mechanism ──X──→ Resource
New Mechanism ──X──→ reads Resource
```

同时保留：`e` / `q` / `fidelity` / `trust` 的既有边界，`Intent ≠ Action ≠ Consequence`，`accepted_action_count` 与 `initial_resource` 的来源分离，132 项测试作为回归底座，以及 Resource 不参与任何现有决策、信息或传播机制。

只有当某个新机制先独立提出自己的操作性需要，并且检查后确认现有账本正好满足该定义时，才重新打开 `docs/RESOURCE_SEMANTIC_ADR.md`，并从零写因果合同与对照实验。在那之前没有 PR-13，也没有待实现的 Resource 功能。

## 7. 后续开发的硬约束

先定义语义，再定义因果边，再做对照实验，最后实现。Resource 已经退出当前开发主线。

任何新的独立机制先检查四件事：

1. 它自己的操作性定义是什么？
2. 它需要读取或改变哪些既有变量？
3. 是否意外穿过现有因果边界？
4. 能否在不读取 Resource 的情况下独立成立？

第 4 点成立，就按独立机制继续，一条边一条边接入，并用现有 132 项测试作为不变量底座。第 4 点不成立，才重新打开 Resource ADR。下一步要找的是下一个独立、可证伪、可单独测量的机制，而不是给 Resource 找用途。
