# 资源契约

状态：**PR-12 RESOURCE CONSERVATION — FROZEN**

信息—认知—行动链已经闭合到“行动产生资源”，但尚未形成资源反馈闭环。

`Resource` 目前是终点变量。它的变化只由已接纳行动解释：

```text
ΔResource(actor) = number_of_accepted_actions(actor)
```

1. A resource unit is a non-negative finite number. One admitted action adds 1.
2. The opening ledger comes from the scenario. A missing actor starts at 0.
3. Resource belongs to the admitted action's actor, not to the action target.
4. +1 counts one admitted action. support and oppose add the same unit.
5. The current rule does not decrease, transfer, or decay resource across ticks.
6. Only ActionResolver changes resource at runtime, and only in action_consequence.
7. Resource does not enter action, decision, information, preference, or trust.
8. Resource has no causal layer yet, so it connects to no existing mechanism.

第 8 条改写之前，不把资源接到行动可用性、决策、信息、信任、偏好或世界状态的其他部分。

## 当前骨架

PR-1 through PR-12 form the core causal skeleton. No feedback loop is established.

```text
Reality
  ↓
Generation        e
  ↓
First hop         q
  ↓
Propagation       fidelity
  ↓
Acceptance        trust
  ↓
Decision          ConstraintPolicy
  ↓
Execution         Action
  ↓
Consequence       Resource
```

`Intent ≠ Action ≠ Consequence`。`Action → Resource` 是单向的。`Resource → ?` 刻意断开。

Resource 是一个由已接纳行动产生的、按行动者归属的可守恒抽象账本变量。

Resource is an abstract conserved ledger, owned by an actor and produced by admitted actions.

它目前不是权力、财富或政治影响力。操作性定义只有 `accepted action → +1`。

A stored field does not gain causal meaning merely by existing.

因此 `RepresentationEdge.trust`、`RepresentationEdge.fidelity` 和这份资源账本都可以先存放，但不因为字段存在就进入因果模型。

## 阶段状态

PR-1 through PR-12 complete a one-way causal skeleton without feedback. PR-13 stays closed until a Resource causal contract is defined.

PR-1～PR-12：无反馈的单向因果骨架已经完成；PR-13 暂不启动，等待 Resource 的因果语义先被独立定义。

三个冻结区：

1. `e`、`q`、`fidelity`、`trust` 各自只作用在生成、第一跳、后续转发和采信。
2. `Intent ≠ Action ≠ Consequence`。
3. Resource counts admitted actions. It does not measure power, wealth, information, organization, or influence.

`Resource → ?` 继续断开。打开下一条机制之前，先写 Resource causal contract，回答它代表什么、为什么有这种作用、影响哪一个既有层、发生在 tick 的哪一步、以及是否产生反馈。然后再写测试。

A Resource causal contract must name its meaning, why that effect exists, which existing layer it changes, where in the tick the change happens, and whether it feeds back.

当前 132 项测试是这条无反馈骨架的回归底座。正式名称是 **PR-1~PR-12: OPEN-LOOP BASELINE — FROZEN**。

- PR-13: not started
- Regression baseline: 132 tests
- Resource: Outcome Variable Only
- Resource → ?: Disconnected
- Resource semantic: UNDECIDED

PR-13 只有同时满足 Resource Causal Admission Test 才允许进入实现：

1. Semantic: Resource has one decided meaning.
2. Operational: that meaning is computable or observable, not only a concept.
3. Justification: accepted_action_count is sufficient for that meaning.
4. Target: it changes exactly one existing layer.
5. Timing: the change happens in one named tick phase.
6. Isolation: it does not change the definitions of e, q, fidelity, or trust.
7. One-edge rule: the first change adds only one causal arrow.
8. Counterfactual: an on/off contrast isolates the Resource effect.
9. Regression: the 132 existing tests still pass.
10. No hidden feedback: EventLog, DecisionContext, and ActionResolver do not create a second feedback edge.

对照实验要证明：只改变 `Resource → X` 这一条边时，结果才发生预期变化；其他既有变量保持不变。不满足以上十条时，不启动 PR-13。

The first causal meaning of Resource may add only one directed edge.

语义选择先写在 `docs/RESOURCE_SEMANTIC_ADR.md`。五问的答案目前是 UNDECIDED。因果合同和引擎改动都排在唯一操作性定义之后。

下面五种资源语义都还没有选择，也不进入引擎：

- 行动能力
- 信息获取能力
- 组织动员能力
- 物质或经济资源
- 纯粹实验观测量

