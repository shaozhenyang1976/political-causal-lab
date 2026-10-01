# 实验 1～4：当前模型可回答的问题边界

状态：FROZEN。PR-1～PR-12 冻结。132 项测试冻结。EventLog 冻结。实验 1～4 已关闭。模型规范、因果边界、可辨识边界、机制准入纪律冻结。文档规范已与实现对照。读写顺序和复现标准已写入 `docs/BASELINE_EXPERIMENT_SPEC.md`。护城河：无。原创性：未证明。竞争壁垒：未形成。PR-13 未开始。实验 5 不存在。下一项工作不预设。文档审计已收口，生产代码未改。

## 自动传播停在哪里

```text
Reality
  ↓
Generation
  │
  │ e
  ↓
signal_generated
  │
  │ q：仅第一跳
  ↓
first-hop received
  │
  │ fidelity：仅后续 information_forward，
  │            在同一拍逐跳累积
  ↓
Trust Gate
  ├─ reject
  │    ↓
  │  无 belief_updated
  │    ↓
  │  intent = seek_information
  │  reason = trust_rejected
  │
  └─ admit
       ↓
   belief_updated
       ↓
   ConstraintPolicy
       ↓
      Intent
       │
       ╳  唯一显式提交断点
       ↓
     Action
       ↓
  action_accepted          consequence=none
       ↓
  action_consequence
       ↓
   Resource +1             不回读 belief、intent，也没有反馈
```

三个已经实验确认的边界：

1. 信息损失可以改变 belief，但不保证改变 Intent。Intent 的离散变化发生在决策阈值上：均值大于 `0.5` 为 `support`，小于 `0.5` 为 `oppose`，等于 `0.5` 为 `abstain`。`1.0` 到 `0.5625` 时意图仍是 `baseline:support`。
2. Trust 与 ConstraintPolicy 都在自动链内。Trust rejection 截断后续的信念写入和约束。ConstraintPolicy 只处理已经写入的 belief。
3. Intent 到 Action 是唯一的显式提交断点。`support` 或 `oppose` 被接纳后，才自动产生 `Resource +1`。接纳事件本身是 `consequence=none`；`+1` 写在随后的 `action_consequence`。其他提交，例如 `abstain`，被拒绝，资源不变。Resource 结算不回读 belief 或 intent，目前没有反馈。

`╳` 不是尚未实现。它是已经测量并确认的模型边界。

## 已验证性质

1. `e`、`q`、`fidelity` 不是同一个损失率，也不先加总再作用。生成机制是按阶段相乘。`e=0.25, q=0.75, fidelity=0.5` 的信号是 `0.75 × 0.75 × 0.5 × 0.5 × 0.5`。`fidelity` 的累积发生在同一拍的后续转发上。缺口的 telescoping 记账是结果差的分解，不是生成机制。
2. 同一个最终信念可以有不同来源。`e=0.25, q=1` 与 `e=0, q=0.75` 的信念都是 `0.75`、意图都是 `support`，生成信号分别是 `0.75` 和 `1.0`。
3. `q` 改变收到的数。`trust` 决定这个数是否写入信念。`q=0` 且采信，是已写入的信念 `0`，意图 `baseline:oppose`。`q=0` 且拒绝，received 也是 `0`，信念不存在，原因是 `trust_rejected`。数值为 0 和没有信念记录是两个状态。
4. 信任拒绝先于 ConstraintPolicy。`trust=0` 时，`seek_information` 与 `delay` 的事件签名相同，因为约束没有执行。采信后，信念可以同为 `1.0`，意图原因分别是 `constraint:seek_information` 与 `constraint:delay`。
5. 意图类型和原因分开。拒绝与“采信后受 `seek_information` 约束”都带有寻求信息的记录。前者没有信念，原因是 `trust_rejected`。后者信念为 `1.0`，原因是 `constraint:seek_information`。无约束采信则是信念 `1.0`、`baseline:support`。
6. 信念或意图的变化本身不产生资源。上列从 `support` 到 `abstain` 再到 `oppose`，只要没有显式提交可接纳行动，就没有 `action_accepted`，资源保持 `{}`。
7. 显式行动是另一道门。意图为 `support` 时提交 `oppose`，仍然接纳，资源 `R1=1.0`。同一份提交在阈值两侧得到相同的接纳和相同的资源。
8. Intent 类型与可接纳 Action 类型不是一一对应。`belief=0.5` 时意图是 `abstain`；提交 `abstain` 被拒绝，原因是 `unknown action type`，资源仍是 `{}`。当前可接纳行动只有 `support` 和 `oppose`。

## 这四问已经回答

| 实验 | 问题 | 答案 |
|---|---|---|
| 1 | 三种信息损失合并后，是否仍按因果位置分阶段？ | 是 |
| 2 | 低质量与低信任是否走不同路径？ | 是 |
| 3 | Trust 与 ConstraintPolicy 同时存在时，执行顺序能否分开“未采信”和“已形成信念但受约束”？ | 能 |
| 4 | 信息损失是否自动传到 Action 或 Resource？ | 否 |

四问都由现有模型回答。没有出现机制缺口，也没有出现 EventLog 不足以回答该问的情况。不因此启动 PR-13。

## 项目纪律

这是一个可实验的因果实验室。一次只提出一个研究问题。现有模型能回答，就做实验并记录结论。不能回答，就检查这是不是当前问题的不可辨识。不阻碍，就记录边界，不加机制。阻碍，才审查最小必要的新因果边。模型不以“现实世界还缺什么”为待办。模型只以“当前研究问题还无法回答什么”为待办。不规划下一阶段。下一步不预设。

`information_forward` 是信息传递的拓扑参数，不是社会层。

Group 是现有 Reality 生成机制可以读取的结构。代表边上的群体，其成员的偏好与能力可以参与聚合，并形成生成信号。该读取属于 Reality → Generation 的既有路径。信号此后仍要经过传输和信任采信，才可能写入信念。这不构成 `Group → Belief`、`Group → Intent` 或其他新的社会因果边。组织、派系、制度目前不进入信息传递、信任采信、信念更新、意图生成或资源结算路径。

三条正式边界：

1. Group 不等于群体机制。Group 进入 Reality → Generation，再经 Transmission、Trust、Belief，才到 Intent。这是既有路径，不是群体对 Belief、Intent 或 Action 的社会反馈。
2. State persistence 不等于 feedback。生成不读取信念、意图、行动或资源；决策不读取资源。本拍未发生信任拒绝时，决策可以读取观察者当前存储的信念；若本拍已经采信，则读取的是本拍刚写入的信念，形成同一 Tick 内的 Belief → Intent。若本拍没有替换该信念，意图仍可依据留存信念计算。该读取不会回到 Generation，因此不形成跨 Tick 的反馈或路径依赖。参数不变且信号每拍被重写时，长期运行仍只是同一结果的重复。
3. 轨迹相同不等于自动的机制缺口。轨迹相同只说明可能不可辨识。不阻碍当前研究问题，就记录边界。阻碍，才审查最小必要的新边。

以后的开发提案只问一句：当前明确的研究问题，现有模型为什么回答不了？回答不出来，就不进入开发。回答得出来，就做实验并记录结果。当前没有下一项工作。没有下一项工作，是这一阶段的正确状态。

可复制性和护城河不是同一个目标。因果实验室的成功是别人能按公开规范重做同一个干预，并得到相同的因果轨迹和结论。跨实现不要求事件字符串逐字相同。132 项测试锁定的是当前这份实现的回归契约。操作步骤见 `docs/BASELINE_EXPERIMENT_SPEC.md` 的当前实现对照。商业护城河追求的是别人难以复制价值。目前不解决这两者的张力。现在没有护城河，也不为建立护城河而改变模型。要守住的是少边、确定性、可追踪、可辨识性审计和逐边准入。实验记录尚不足以构成复制壁垒。不为了积累资产而生产实验。研究者生态、benchmark 和平台不是当前内核的路线。ABM、反事实实验、可复现和因果推断都不是原创卖点。上述纪律组合的原创性尚未证明，竞争壁垒尚未形成。
