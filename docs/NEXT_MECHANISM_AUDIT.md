# Next Mechanism Audit

状态：**NEXT MECHANISM AUDIT — CLOSED**

Preparation only — PR-13 NOT STARTED。本阶段正式收口。下一步是等待一个现有模型无法回答的研究问题，不是改代码。

本文件的职责是防止未经研究问题证明的因果边被引入，不是寻找缺失功能。基线仍是 **PR-1~PR-12: OPEN-LOOP BASELINE — FROZEN**。引擎不变，生产代码不变，测试保持 132 / 132。Resource 仍是断开的结果变量。六个候选全部保持 **UNDECIDED**，没有选中任何机制。

## 0. 审计问题

缺口不能从“怎样才更像一个完整的社会行为模拟器”里找。现实社会里存在某种关系，并不使模拟器必须实现它。

一条候选边要进入实现，先要有一个已经写明的研究问题，并且同时回答：

1. 没有它，当前模型能否回答该问题？
2. 如果加入它，能否定义唯一的操作性变量？
3. 能否只增加一条可实验验证的因果边？

这三个问题在研究问题写明之前保持 **UNDECIDED**。下面的候选都不是已经确认的缺口。

## A. 已经覆盖的因果边

```text
Reality P
  ↓  e          Generation          G(p, e) = clamp(p - e, 0, 1)
  ↓  q          First hop           received₁ = q × G
  ↓  fidelity   Forwarding          后续 information_forward 再乘 fidelity
  ↓  trust      Admission           t ≥ τ 才把 received 写入 belief
  ↓             ConstraintPolicy    只在已采信的信念上产生意图
  ↓             Intent              每个代表每拍一条；不改 WorldState
  ↓             Explicit Action     显式提交；不等于意图
  ↓             ActionResolver      只有 support / oppose 可被接纳
  ↓             Consequence         行动者资源 +1
  ↓             Resource            initial_resource + accepted_action_count
  ↓
  X             断开
```

同时已经固定、不得被新边悄悄改写的还有：

- `e`、`q`、`fidelity`、`trust` 各自只作用在自己的层。
- `Intent ≠ Action ≠ Consequence`。
- `accepted_action_count` 与 `initial_resource` 来源分离。
- 跳数本身不造成衰减。只有显式 `fidelity < 1` 才改变后续载荷。
- 冲突信号不平均。多个信念不平均。
- `RepresentationEdge.trust` 与 `RepresentationEdge.fidelity` 只是存放字段，不是机制。
- 直接观察者的 `transmission_gap` 为 0。`estimated_information` 保持为 `q`。
- 新机制不得写入 Resource，也不得读取 Resource。

## B. 待审查的候选边

全部是 **UNDECIDED**。列出它们只表示可以审查，不表示它们缺失，也不表示应当实现。

| 候选边 | 状态 |
| --- | --- |
| Action → Information | UNDECIDED |
| Action → Reality | UNDECIDED |
| Action → Relationship | UNDECIDED |
| Action → Organization | UNDECIDED |
| Belief → Belief | UNDECIDED |
| Action → Trust | UNDECIDED |

以下方向在单独通过上面三个问题之前，不提前加入。它们很容易一次带出多条反馈边：Resource 反馈、信任学习、声誉、权力、影响力机制、组织等级、魅力、人气、行动概率。已有的 `capabilities.influence` 只参与真实观察的权重，不是这些机制中的任何一个。

## C. 必要性审查

研究问题尚未写明，所以下表不填结论。

| 候选边 | 没有它能否回答目标问题 | 能否定义唯一操作性变量 | 能否只加一条可验证的边 |
| --- | --- | --- | --- |
| Action → Information | UNDECIDED | UNDECIDED | UNDECIDED |
| Action → Reality | UNDECIDED | UNDECIDED | UNDECIDED |
| Action → Relationship | UNDECIDED | UNDECIDED | UNDECIDED |
| Action → Organization | UNDECIDED | UNDECIDED | UNDECIDED |
| Belief → Belief | UNDECIDED | UNDECIDED | UNDECIDED |
| Action → Trust | UNDECIDED | UNDECIDED | UNDECIDED |

单箭头卡片在某一行离开 UNDECIDED 之前不填写。卡片格式是：

```text
Mechanism
Source:
Target:
Operational definition:
Tick position:
Existing variables affected:
New information introduced:
Feedback:
Confounders:
Control condition:
```

### 审查时已经能看到的混淆

**Action → Information。** 现有信息只来自现实与显式转发，行动本身还不是信息来源。若要审查，先回答“哪一种已经发生、且被谁观察到的行动，产生哪一种信号”。不能把“被接纳的行动”直接写成下一条信号。

还要把两件事分开：行动可以成为信息载体；行动因此改变信念。在当前管线里，一个进入传输的信号会在下一拍经过采信并写入信念。若新信号走现有的 Information → Belief 路径，那么“只是载体”会连带打开第二条边。要保持一条边，可观察事件必须停在进入 `belief_update` 之前，除非研究问题明确要求它成为信念输入，并把它算作那唯一的一条边。

**Action → Reality。** 当前后果故意不改变偏好、信念和信息。现实没有因行动改变，是这条开放环的设计，不是尚未修补的漏洞。若要审查，先写明 `Action X` 改变哪一个 `WorldState` 变量 Y。Y 若会被下一拍的生成读到，这条边就是反馈，而不是终端后果。

**Belief → Belief。** 多个信念不自动平均已经冻结。把信念之间的传递列进来时，不能把它实现成平均或互相覆盖。

**Action → Trust。** 信任目前只是采信门槛 `t`、`τ`。行动改变信任会把执行层接回采信层，并立刻形成 Action → Trust → Belief → Intent → Action。这不是一条孤立的边。

## D. 本阶段的审计结果

目前没有被证明必须增加任何新因果边。六个候选全部保持 **UNDECIDED**，三个必要性问题保持空白。这就是本阶段的结果，不是待补的空栏。

两条审查原则同时冻结：

1. 好接入不是有必要。`Action → Information` 即使能接上现有管线，也不能因此被采用。若以后研究它，可观察事件必须先停在 `belief_update` 之前。否则信号会沿 Information → Belief 进入信念，名义上的“信息载体”在因果上已经是 Action → Belief。
2. `Action → Reality` 不因排在链条后面而成为下一步。现在的 `Action → Consequence → Resource` 是终端结果。若行动改写的 WorldState 变量进入下一拍生成，得到的是 Action → Reality → Information → Belief → Intent → Action，而不再是单纯的后果。

模型不是因为缺少现实世界中的机制而不完整；只有当某个明确研究问题无法由现有因果结构回答时，模型才具有增加机制的必要性。

因此六个候选只是待审计假设，不是待办功能。Feedback 的判定对象是后续因果输出，不是某一个中间变量的数值变化。正式判定按这条路径机械执行：

```text
Action
  ↓
变量改变 / 信息产生
  ↓
后续 Tick
  ↓
进入既有读取或处理路径？
  ├─ No → 不是 feedback
  └─ Yes
       ↓
     因果输出改变？
       ├─ No → 不是 feedback
       └─ Yes → Level 3 feedback
```

因果输出只包括生成、传输、信念、意图和行动。`ΔBelief = 0` 且 `ΔIntent ≠ 0` 仍是 Level 3。`ΔWorldState ≠ 0` 或 `ΔEventLog ≠ 0` 本身不能判定为 feedback。没有进入后续读取路径时，后面的输出即使变化，也不算这条 Action 的 feedback。

Level 3 只负责认定反馈。它不是“只有反馈边才可以加入模型”的许可证。没有研究问题和必要性证明时，新的 Level 1 边同样不能加。已有的状态变化也不使任何候选获得 PR-13 资格。目前不存在需要修复的反馈。

只有 Level 3 叫 feedback：

```text
Level 1 — State Change
Action → Consequence → WorldState

Level 2 — Observation
State Change → EventLog

Level 3 — Causal Feedback
Changed state / derived information
        ↓
later read / processed
        ↓
downstream causal output changes
```

Level 3 的必要条件是整条路径，不是单独的输出变化：被 Action 改变的变量或 Action 派生的信息，进入后续拍的既有读取或处理路径，并且至少一个后续因果输出因此改变。后续因果输出包括生成、传输、信念、意图和行动。`EventLog` 中的新值、`action_consequence` 的 `state_change`、`WorldState` 被修改、以及下一拍存在，都停在 Level 1 或 Level 2。

信念数值保持不变，也可以是 Level 3。行动派生信号若进入下一拍的 Information 管线并被 `belief_update` 处理，信任门槛可以拒绝采信：库存信念保持原值，意图变为 `seek_information`。`ΔBelief = 0` 且 `ΔIntent ≠ 0`。把 feedback 定义成“信念数值改变”会漏掉这条路径。`trust_rejected` 仍然不是无信息、不是信念误差、也不是 `constraint:delay`。

两个测试都使用这条 Level 3 标准：

1. **Information feedback test。** 行动派生的信息是否进入后续拍中被 `belief_update` 消费的 Information 管线，并因此改变信念阶段或其下游意图、行动的输出？同一拍的 `political_action` 到不了已经完成的 `belief_update`。在它之前多记一个观察事件，也不能靠位置阻断这条路径。
2. **State feedback test。** 行动造成的状态变量变化，是否被后续拍的上游机制重新读取，并因此改变该机制或其下游的生成、传输、信念、意图或行动输出？

`Action → Resource` 停在 Level 1，其事件记录停在 Level 2。生成不读取 Resource。`Action → Preference'` 若进入下一拍生成，并改变信息、信念、意图和之后的行动，才进入 Level 3。

EventLog 记录了一个事实，并不等于模型已经建立了那条因果关系。已有的状态变化本身不构成启动 PR-13 的理由。

## E. 两个独立门槛

Level 3 回答“这是不是 feedback”。机制准入回答“这条边有没有资格存在”。两者不互相代替。

**A. Feedback 判定。** 只有三项同时成立才是 Level 3：Action 改变变量或产生信息；该变化进入后续拍的既有读取或处理路径；生成、传输、信念、意图或行动中至少一个因果输出因此改变。`ΔBelief = 0` 且 `ΔIntent ≠ 0` 仍然成立。`ΔWorldState ≠ 0` 或 `ΔEventLog ≠ 0` 单独都不成立。

**B. 新机制准入。** 顺序是：明确研究问题，现有模型是否无法回答，确定所需变量，操作性定义，证明必要性，确定最小因果边，设计隔离对照实验，然后才有资格进入 PR。这里不要求新边必须产生 Level 3 feedback。一个不被后续机制读取的 `Action → NewOutcome` 可以是合法的 Level 1 终端边，但必须先走完这套准入。反过来，`Action → X → Generation → … → Action` 即使天然是反馈环，没有研究问题证明需要它，也不能因此启动 PR-13。

Feedback 是分类标准，不是准入标准。因果闭环不是新增机制的理由；研究问题才是。

因此：Feedback 不等于机制准入资格。终端边不自动合法。反馈环不自动合法。能够启动下一阶段的，只有一个现有模型无法回答的明确研究问题。在那之前保持冻结，是研究流程，不是停滞。

在两道门槛都未通过之前，132 项测试、生产代码、引擎和 PR-1～PR-12 保持冻结。没有 PR-13。

## F. 实验阶段 — FROZEN

工作循环是：实验，观察，解释，然后问现有模型是否足够。足够，就记为模型结论。只有严格的不可判别才进入机制准入。不是：实验，找到缺口，加机制。

否定性结果是模型结论。被接纳的行动不改变下一拍信念，这是现有开环已经回答的结果，不是缺少 `Action → Information`。

已经闭合的识别：

- 只看首跳信念时，`e` 和 `q` 都可以把它降到同一个数。EventLog 仍能分开：`e` 改变 `signal_generated`，`q` 不改变生成信号，只改变第一跳 received。
- `fidelity` 不改变直接观察者。第一跳仍是 `q × G`。它只改变后续转发。直接观察者与下游观察者可以从事件链区分。
- `trust < τ` 在 `ConstraintPolicy` 之前决定本拍意图。组合里出现 `trust_rejected`，不是 `delay` 失效，而是执行顺序使信任拒绝先决定了当前意图。信念可以保持原值。约束要等采信并且信念写入之后才作用。

因果可辨识性结论：最终状态相同，不等于因果路径不可辨识。`e=0.25, q=1` 与 `e=0, q=0.75` 的首跳信念都是 `0.75`，意图都是 `baseline:support`；`signal_generated` 分别是 `0.75` 和 `1.0`，received 都是 `0.75`。`q=0.5, fidelity=1` 与 `q=1, fidelity=0.5` 的第二跳信念都可以是 `0.5`，第一跳分别是 `0.5` 和 `1.0`。只看最终下游会混淆；完整事件链加上网络位置可以恢复来源。事件不需要把最终因果来源写成一个标签。`trust_rejected` 没有 `belief_updated`；`constraint:seek_information` 先写入信念。阶段是否发生本身就提供辨识。`q=0` 时，`fidelity=1` 与 `fidelity=0.5` 的整份 EventLog 相同，因为 `0 × fidelity` 仍是 0。再记一条结果事件也不会产生新的可观测差异。把参数名抄进日志只是复述输入，不是新的轨迹差异。这是信息完全坍缩边界上的不可辨识，不是模型缺陷，也不产生 PR-13 候选。

可辨识性原则：相同最终结果不等于相同因果路径。先检查完整 EventLog。只有完整轨迹也相同，才检查是否处于信息坍缩边界。研究问题是实验的前提，不再单独作为闸门。要判断的是：当前不可辨识是否妨碍回答这个研究问题。相同的完整 EventLog 不表示日志不够详细，也不因此增加日志或机制。

两道闸门：

1. 反直觉不等于模型缺陷。先判断它是不是现有模型产生的有效结论。是，就记录，不改模型。不是，就继续分析，而不是直接改代码。
2. 不可辨识不等于需要增加机制。先判断这种不可辨识是否妨碍回答当前研究问题。不妨碍，就记录边界结论。只有当前问题本身要求区分这些无法分开的参数，才进入机制审查。

`q=0` 时，`fidelity=0.5` 与 `fidelity=1` 的完整事件链都显示首跳和后续传播为 0。若问题是“`q=0` 时首跳是否变为 0”，模型已经回答，到此结束。只有问题改成“在 `q=0` 时必须区分这两种 fidelity 的行为”，才有资格重新打开机制审查。

指向扩展的条件是同时成立：该结果不是现有模型已经给出的结论，并且这种不可辨识阻碍了当前研究问题。两个“是”并不都指向 PR。在那之前继续实验，不开发。

因果系统分成三层。第一层是机制：`e` 生成，`q` 第一跳，`fidelity` 后续转发，`trust` 采信，`ConstraintPolicy` 意图。第二层是 EventLog 上的可观测轨迹，用来区分这些路径。第三层是不可辨识边界：输入信号坍缩后，不同参数产生完全相同的轨迹。`q=0` 时首跳 received 为 0，后续传播仍为 0，不同 `fidelity` 不再产生可观测差异。第三层是当前观测条件下的信息边界，不是模型错误。

这一轮到此收束，不再围绕 EventLog 做扩展。下一步仍是：用现有模型提出研究问题，跑实验，观察，解释，判断现有模型是否足够。

机制准入只剩一个触发条件：明确的研究问题，在穷尽现有可观测输出之后仍然无法判别。以下情况都不触发：现实世界存在该机制，模型目前没有该变量，容易接入，能形成反馈环，这样会更真实，某个变量看起来应该有更多用途，以及当前结果与现实直觉不同。

在这个触发出现之前，132 项测试、生产代码、引擎和 PR-1～PR-12 保持冻结。没有 PR-13。继续用现有模型做实验。

### 实验 1 — CLOSED

`e × q × fidelity`。模型能够回答。没有现有模型无法解释的现象。不新增机制，不改代码。

1. `e`、`q`、`fidelity` 不是同一个信息损失率。它们停在不同阶段：`e` 只改 `signal_generated`；`q` 只改第一跳，并因此按比例缩小后面各跳；`fidelity` 不改第一跳，只在后续 `information_forward` 上逐跳相乘。`e=0.25, q=1` 与 `e=0, q=0.75` 的各跳信念都是 `0.75`、意图都是 `support`，只靠生成信号分开。
2. `fidelity` 沿后续跳累积，不是把所有人静态打同一个折扣。`e=0, q=1, fidelity=0.5` 时四跳为 `1, 0.5, 0.25, 0.125`，意图为 `support, abstain, oppose, oppose`。累积发生在同一拍的后续跳上，不是延后到后面几拍。
3. 信念连续，意图离散。`e=0.25, q=0.75, fidelity=0.5` 时直接观察者信念为 `0.5625`，意图仍是 `support`；第二跳 `0.28125` 才变成 `oppose`。信念可以明显下降而不跨过 `0.5`。这是当前 DecisionPolicy 的结果，不是异常。
4. 三种损失按因果位置依次相乘，不是 `1 - 0.25 - 0.25 - 0.5`，也不能压成一个总损失率。上例的信号是 `0.75 × 0.75 × 0.5 × 0.5 × 0.5`。缺口的 telescoping 记账仍然成立，那是结果差的分解，不是生成机制。

### 实验 2 — CLOSED

`trust × q`。固定 `e=0`、`fidelity=1`、`τ=0.5`，只看直接观察者。`q ∈ {1, 0.75, 0.5, 0}`，采信用 `trust=1`，拒绝用 `trust=0`。模型能够回答。不新增机制，不改代码。

1. `q` 与 `trust` 不在同一阶段。生成信号在八组里都是 `1.0`。`q` 只改变 received。`trust` 不改变 received，只决定这个 received 是否写入信念。
2. 相同 received 可以走出两条路径。`q=0.5` 时 received 都是 `0.5`：采信写入信念 `0.5`，意图 `baseline:abstain`；拒绝不写信念，`action_intent` 的原因是 `trust_rejected`。只看 received 不能判断路径。
3. `q=0` 把“数值为 0”和“没有信念记录”分开。采信写入信念 `0`，意图 `baseline:oppose`。拒绝的 received 也是 `0`，信念不存在，原因是 `trust_rejected`。拒绝事件的 `available_information` 另记 `intent=seek_information`。原因是 `trust_rejected`，意图类型是 `seek_information`。这与“已写入的零值信念”不是同一个状态。数值坍缩和是否写入信念是两层问题。

低质量与低信任通过不同路径影响决策。现有模型可以完整区分。EventLog 的阶段信息足够。

### 实验 3 — CLOSED

`trust × ConstraintPolicy`。固定 `e=0`、`q=1`、`fidelity=1`、`τ=0.5`，只看直接观察者。模型能够回答。不新增机制，不改代码。

1. Trust rejection 先于 ConstraintPolicy。`trust=0` 加 `seek_information` 与 `trust=0` 加 `delay` 的 R1 事件签名完全相同。约束没有失效，它没有执行。
2. `seek_information` 要分开意图类型和原因。拒绝时意图类型是 `seek_information`，原因是 `trust_rejected`。采信后再加该约束，意图类型仍是 `seek_information`，原因是 `constraint:seek_information`。
3. ConstraintPolicy 只在信念写入之后作用。采信时信念为 `1.0`，原因分别是 `constraint:seek_information` 与 `constraint:delay`。拒绝时没有 `belief_updated`。这个顺序写在事件里。
4. 三种相近结果可以分开。无约束采信是信念 `1.0`、`baseline:support`。约束后寻求信息是信念 `1.0`、`constraint:seek_information`。信任拒绝后寻求信息是信念不存在、`trust_rejected`。意图与信念是否形成、以及原因，一起构成轨迹。

Trust 与 ConstraintPolicy 同时存在时，执行顺序能够区分这两条路径。EventLog 足够。

### 实验 4 — CLOSED

信息损失是否会自动传导到 Action 或 Resource。固定 `fidelity=1`、`trust=1`、`τ=0.5`，无约束，只看直接观察者。资源初值是空账本。显式提交的是 `support`、`oppose` 或 `abstain`，目标 `G1`。模型能够回答。不新增机制，不改代码。四轮合在一起的边界见 `docs/EXPERIMENT_BOUNDARY.md`。

| 条件 | 信念 | 意图原因 | 不提交 | 提交 `support` 或 `oppose` |
|---|---:|---|---|---|
| `e=0, q=1` | `1.0` | `baseline:support` | 无接纳，资源 `{}` | `action_accepted`，资源 `R1=1.0` |
| `e=0.25, q=0.75` | `0.5625` | `baseline:support` | 无接纳，资源 `{}` | `action_accepted`，资源 `R1=1.0` |
| `e=0, q=0.5` | `0.5` | `baseline:abstain` | 无接纳，资源 `{}` | `action_accepted`，资源 `R1=1.0` |
| `e=0, q=0.25` | `0.25` | `baseline:oppose` | 无接纳，资源 `{}` | `action_accepted`，资源 `R1=1.0` |
| `e=0, q=0` | `0.0` | `baseline:oppose` | 无接纳，资源 `{}` | 提交 `support` 后资源 `R1=1.0` |

`q=0.5` 时提交 `abstain`：意图原因仍是 `baseline:abstain`，行动被拒绝，原因 `unknown action type`，没有 `action_accepted`，资源仍是 `{}`。

`support` 与 `oppose` 的接纳原因都是 `admitted (chosen)`。接纳事件的 `available_information` 仍是 `consequence=none`。资源 `+1` 写在随后的 `action_consequence`。两边的资源增量相同，并且不读取信念或意图。意图为 `support` 时提交 `oppose`，仍然接纳并得到 `R1=1.0`。

因此，信息损失改变信念；跨过 `0.5` 才改变意图。它不产生行动，也不改变资源。行动记录和资源变化只出现在显式提交的 `support` 或 `oppose` 被接纳之后。同一份提交，在阈值两侧得到相同的接纳和相同的资源。
