# Political Simulation Platform — Model & Implementation Specification v0.2

本文件是设计规格，不是当前可运行模型的能力声明。可执行部分只有已冻结的开环基线：PR-1～PR-12。空 Tick 槽位没有执行体。联盟、制度、权力、界面、可替换理论和玩家实验都还不是机制。读者应先看 `README.md`、`docs/BASELINE_EXPERIMENT_SPEC.md` 和 `docs/EXPERIMENT_BOUNDARY.md`。

## 1. Purpose

本文件定义 Political Simulation Platform v0.2 的核心政治模拟模型、数据结构、因果顺序、实验机制、可重复性要求与第一阶段实现边界。

目标不是制作一个特定历史人物或历史事件的游戏，而是建立一个可替换理论、可复现实验、可观察解释的政治模拟基础平台。

核心问题：

> 在个体偏好、群体利益、组织能力、代表关系、信息不完全、联盟、制度与网络共同作用下，政治权力、政治行动与政治结果如何产生？

---

## 2. Project Positioning

平台采用以下分层结构：

```text
Political Simulation Platform
 ├── Simulation Core
 ├── Theory Layer
 ├── Scenario Layer
 ├── Experiment Engine
 └── Interfaces
      ├── Game
      ├── Lab
      └── Research
```

设计原则：

1. Simulation Core 与历史内容解耦。
2. Theory Module 可插拔、可替换。
3. Scenario 是数据，而不是核心逻辑。
4. 所有实验具有 seed、版本与参数记录。
5. 模拟过程必须可观察、可解释。
6. 玩家和研究者可以创建、复制、修改实验。
7. 不把任何政治结果写死为必然结果。
8. LLM 不作为权威政治物理规则引擎。

---

## 3. Design Philosophy

### 3.1 Individual ≠ Group

个体具有自己的偏好与能力。

群体利益是个体利益的聚合结果。

### 3.2 Group ≠ Organization

Group 表示利益共同体。

Organization 表示协调结构。

### 3.3 Representative ≠ Represented Group

代表者可能同时受到：

- 被代表群体利益
- 个人利益
- 组织利益
- 上级利益
- 联盟利益
- 生存利益

影响。

因此代表关系不是简单的：

```text
Group Preference → Representative Action
```

而是：

```text
Group
   ↓
Representation Edge
   ↓
Representative
   ↓
Organization / Coalition / Institution
   ↓
Political Action
```

### 3.4 Information Loss ≠ Lying

信息在层级传播过程中可能产生：

- 随机噪声
- 选择性报告
- 战略性隐瞒
- 误解
- 利益过滤
- 能力限制

所有参与者都可以是理性的，但整个系统仍可能产生信息失真。

---

# 4. Core Entities

核心实体：

```text
Individual
Group
Organization
PoliticalActor
Representative
Faction
Coalition
Institution
RepresentationEdge
PoliticalAction
Belief
WorldState
TheoryModule
ExperimentConfig
ExperimentResult
EventLog
```

---

# 5. Individual

Individual 是最基本的政治行为单位。

## 5.1 Preferences

```text
P_i = (
    Power_i,
    Wealth_i,
    Ideology_i,
    Security_i,
    Status_i
)
```

每一维归一化到：

```text
[0, 1]
```

偏好与能力必须严格分离。

## 5.2 Capabilities

```text
C_i = (
    Information_i,
    Organization_i,
    Influence_i,
    Coercion_i,
    Wealth_i
)
```

原则：

```text
Preference ≠ Capability
```

一个人可以高度重视权力，但实际政治能力很低。

---

# 6. Group

Group 是利益聚合单位。

一个 Group 包含若干 Individual。

---

# 7. Group Interest

群体利益由成员偏好加权聚合。

对于维度 k：

\[
G_g^k =
\frac{\sum_{i\in M_g} w_i P_i^k}
{\sum_{i\in M_g} w_i}
\]

初始版本：

\[
w_i = 0.5 + 0.5\times influence_i
\]

其中：

```text
M_g = Group members
P_i^k = Individual preference
w_i = influence weight
```

后续可以由 Theory Module 替换。

---

# 8. Group Cohesion

群体内部一致程度：

\[
Cohesion_g =
1 - MeanDistance(P_i,G_g)
\]

结果归一化：

```text
[0, 1]
```

解释：

- 0 = 内部分歧极大
- 1 = 高度一致

注意：

> Cohesion 是描述变量，不是价值判断。

---

# 9. Effective Collective Power

群体潜在能力不等于有效政治能力。

基准公式：

\[
EffectivePower_g =
PotentialPower_g
\times Organization_g
\times Cohesion_g
\times Mobilization_g
\]

其中：

```text
PotentialPower
Organization
Cohesion
Mobilization
```

均为：

```text
[0,1]
```

这一结构用于测试：

> 为什么拥有大量资源的群体，有时仍无法形成有效政治行动？

---

# 10. Organization

Organization 是将个人或群体转化为持续协调能力的结构。

核心变量：

```text
membership
hierarchy
discipline
communication
recruitment
retention
sanction
resource_pool
internal_cohesion
organizational_capacity
organizational_power
legitimacy
```

组织不是单纯的人群集合。

---

# 11. RepresentationEdge

代表关系必须建模为独立实体。

```text
RepresentationEdge
```

核心字段：

```text
representative_id
represented_entity_id
fidelity
accountability
information_up
information_down
trust
dependency
duration
```

其中：

```text
fidelity
accountability
information_up
information_down
trust
dependency
```

均可以归一化到：

```text
[0,1]
```

---

# 12. Representation Fidelity

定义：

\[
RF_{rg}\in[0,1]
\]

RF 越高：

> 代表者越能准确获取并反映被代表群体的利益。

注意：

RF 不等于道德评价。

---

# 13. Representation Utility

代表者不是只最大化群体利益。

基准：

\[
U_r =
w_GU_G+
w_PU_P+
w_OU_O+
w_SU_S+
w_IU_I
\]

其中：

```text
U_G = Group utility
U_P = Personal utility
U_O = Organization utility
U_S = Survival / security utility
U_I = Institutional utility
```

群体权重：

\[
w_G =
RF_{rg}\times Accountability_r
\]

所有权重归一化。

这允许系统产生：

```text
代表者仍然认为自己是理性的
```

但其行动已经偏离群体偏好。

---

# 14. Representation Drift

定义：

\[
RD =
Distance(GroupPreference, RepresentativeAction)
\]

归一化：

```text
[0,1]
```

解释：

```text
0 = 没有可测量偏离
1 = 最大偏离
```

Representation Drift 是实验指标，不是道德判断。

---

# 15. Information System

系统必须严格区分：

```text
True State
```

与：

```text
Belief State
```

一个 Actor 可以拥有错误信息，但模拟器知道真实状态。

---

# 16. Information Transmission

最简单的信息传递：

\[
I_{up}=qI_{down}
\]

其中：

```text
q ∈ [0,1]
```

多层传播：

\[
I_C=q_{BC}q_{AB}I_A
\]

因此：

```text
A → B → C
```

的信息质量可能逐层降低。

---

# 17. Belief

每个 Actor 对其他 Actor 的状态形成自己的信念。

：

\[
Belief_i(j)=
(\hat P_{ij},\hat C_{ij},\hat L_{ij},\hat I_{ij})
\]

其中：

```text
P̂ = estimated preference
Ĉ = estimated capability
L̂ = estimated loyalty
Î = estimated information
```

必须保证：

```text
Belief ≠ True State
```

---

# 18. PoliticalActor

PoliticalActor 是一种动态状态，而不是固定角色。

一个 Individual、Representative、Organization、Faction 或 Coalition 都可能在特定时刻成为 PoliticalActor。

PoliticalActor 的核心能力来自：

```text
information
coordination
resources
network position
institutional access
legitimacy
coercion
representation
```

---

# 19. Political Power

基准：

\[
PP_i =
Normalize(
Personal+
Represented+
Organizational+
Network+
Institutional
)
\]

政治权力不是单一属性。

---

# 20. Faction

Faction 是政治行动集团。

Faction 与 Organization 不同：

```text
Organization = coordination structure
Faction = political action bloc
```

Faction 可以跨越多个 Organization。

---

# 21. Coalition

Coalition 是动态合作关系。

Coalition 不等于 Faction。

它可以是：

```text
temporary
conditional
issue-specific
strategic
```

---

# 22. Institution

Institution 定义可重复的政治规则。

例如：

```text
decision rules
appointment rules
voting rules
resource allocation rules
succession rules
sanction rules
```

Institution 不直接决定政治结果，而是改变行动空间与收益结构。

---

# 23. PoliticalAction

所有政治行动必须通过：

```text
ActionResolver
```

执行。

示例：

```text
form_coalition
leave_coalition
appoint
remove
vote
allocate
sanction
negotiate
support
oppose
recruit
defect
```

禁止绕过 ActionResolver 直接修改核心状态。

---

# 24. WorldState

WorldState 保存模拟器真实状态：

```text
individuals
groups
organizations
representatives
factions
coalitions
institutions
representation_edges
resources
networks
beliefs
environment
```

---

# 25. True State / Belief State Separation

这是 v0.2 的硬性要求。

模拟器内部：

```text
True State
```

是唯一真实状态。

Actor 决策只能访问：

```text
Actor Belief State
```

不能直接读取真实状态。

否则信息不完全模型将失效。

---

# 26. Simulation Architecture

推荐：

```text
SimulationEngine
 ├── WorldState
 ├── TickProcessor
 ├── SeededRandom
 ├── ActionResolver
 ├── InformationSystem
 ├── BeliefSystem
 ├── CoalitionSystem
 ├── PowerSystem
 ├── RepresentationSystem
 ├── NetworkSystem
 ├── MetricsSystem
 └── EventSystem
```

---

# 27. TheoryModule

理论模块必须可插拔。

接口概念：

```text
TheoryModule
 ├── update_belief()
 ├── evaluate_incentive()
 ├── evaluate_coalition()
 ├── select_action()
 ├── calculate_power()
 └── update_representation()
```

不同理论可以实现不同规则。

---

# 28. Theory Module Rules

理论模块必须满足：

1. 不直接修改不可授权状态。
2. 不绕过 ActionResolver。
3. 所有随机行为使用 SeededRandom。
4. 所有核心计算可记录。
5. 版本号必须记录。
6. 可以被实验引擎替换。

---

# 29. Layered Causality

模型因果层级：

```text
Individual
    ↓
Group
    ↓
Representation
    ↓
Organization
    ↓
Faction
    ↓
Coalition
    ↓
Institution
    ↓
Political Action
    ↓
World State
    ↓
Power / Representation / Network
    ↓
下一 Tick
```

---

# 30. Tick Protocol

每个 Tick 严格按照以下顺序：

```text
01 Environment Update
02 Information Generation
03 Information Transmission
04 Belief Update
05 Incentive Update
06 Coalition Evaluation
07 Representative Decision
08 Organization Decision
09 Political Action
10 Conflict / Bargaining
11 Resource Allocation
12 Power Recalculation
13 Representation Update
14 Network Update
15 Survival / Replacement
16 Metrics
17 Event Log
```

顺序必须固定。

---

# 31. Tick 01 — Environment Update

更新：

```text
economic conditions
resource availability
external threats
institutional conditions
random events
```

---

# 32. Tick 02 — Information Generation

生成：

```text
observations
signals
reports
rumors
events
```

---

# 33. Tick 03 — Information Transmission

信息通过：

```text
individual → representative
representative → organization
organization → faction
faction → coalition
```

传播。

每条边都有：

```text
transmission_quality
```

---

# 34. Tick 04 — Belief Update

Actor 根据：

```text
previous belief
new information
trust
prior belief
```

更新信念。

---

# 35. Tick 05 — Incentive Update

计算：

```text
personal utility
group utility
organizational utility
survival utility
institutional utility
```

---

# 36. Tick 06 — Coalition Evaluation

计算：

```text
cohesion
trust
expected payoff compatibility
defection cost
common threat
```

---

# 37. Tick 07 — Representative Decision

代表者根据：

```text
belief
preferences
representation fidelity
accountability
organization
survival
institution
```

选择行动。

---

# 38. Tick 08 — Organization Decision

组织根据：

```text
membership
discipline
resources
leadership
internal cohesion
external threat
```

形成组织行动。

---

# 39. Tick 09 — Political Action

所有行动进入：

```text
ActionResolver
```

由 ActionResolver 验证：

```text
permission
resource requirement
institutional constraint
actor capability
target validity
```

---

# 40. Tick 10 — Conflict / Bargaining

处理：

```text
conflict
negotiation
bargaining
defection
sanction
coalition formation
```

---

# 41. Tick 11 — Resource Allocation

资源按照：

```text
institutional rules
political actions
coalition agreements
organization rules
```

进行重新分配。

---

# 42. Tick 12 — Power Recalculation

重新计算：

```text
individual power
group power
organization power
faction power
coalition power
institutional power
network power
```

---

# 43. Tick 13 — Representation Update

更新：

```text
fidelity
accountability
trust
dependency
information quality
representation duration
```

---

# 44. Tick 14 — Network Update

更新：

```text
alliances
communication links
dependency links
influence links
organizational links
```

---

# 45. Tick 15 — Survival / Replacement

可能发生：

```text
leadership replacement
representative replacement
organizational exit
coalition collapse
faction transformation
```

Leader 不是永久角色。

---

# 46. Tick 16 — Metrics

每 Tick 计算：

```text
Representation Drift
Information Distortion
Political Power Concentration
Coalition Stability
```

---

# 47. Representation Drift Metric

：

\[
RD=
Distance(GroupPreference, RepresentativeAction)
\]

记录：

```text
mean
median
max
distribution
time series
```

---

# 48. Information Distortion Metric

可以定义：

\[
ID =
Distance(TrueInformation, BelievedInformation)
\]

需要明确区分：

```text
generation error
transmission error
interpretation error
strategic concealment
```

---

# 49. Political Power Concentration

使用 HHI：

\[
HHI=\sum_i s_i^2
\]

其中：

\[
s_i=
\frac{Power_i}{\sum_j Power_j}
\]

用于描述权力集中程度。

---

# 50. Coalition Stability

基准：

\[
S=
0.25C+
0.20T+
0.20E+
0.15D+
0.20H
\]

其中：

```text
C = Cohesion
T = Trust
E = Expected payoff compatibility
D = Defection cost
H = Common threat
```

此公式只是 baseline。

正式研究中必须允许 Theory Module 替换。

---

# 51. Leader Emergence

Leader 不应作为固定字段直接指定。

领导地位可以由：

```text
network centrality
organizational control
resource control
information access
coalition coordination
institutional position
```

共同产生。

---

# 52. Initial Sandbox

v0.2 初始实验：

```text
20 Individuals
4 Groups
4 Representatives
2 Organizations
2 Factions
1 Institution
```

每个 Group：

```text
5 Individuals
```

代表关系：

```text
G1 → R1
G2 → R2
G3 → R3
G4 → R4
```

组织：

```text
Organization A: R1, R2
Organization B: R3, R4
```

Faction：

```text
Faction A
Faction B
```

---

# 53. Group Initial Preferences

为了控制实验变量，初始群体可以存在不同偏好：

```text
G1 → relatively high Security
G2 → relatively high Wealth
G3 → relatively high Status
G4 → relatively high Ideology
```

这只是实验变量，不代表任何历史群体。

---

# 54. Scenario Generator

Scenario Generator 负责：

```text
create population
create groups
create organizations
create representatives
create factions
create institution
create networks
create initial resources
```

必须使用：

```text
seeded random
```

---

# 55. Randomness

所有随机行为统一通过：

```text
SeededRandom
```

禁止：

```text
global random
untracked random
```

---

# 56. Reproducibility

每个实验必须记录：

```text
experiment_id
model_version
scenario_version
theory_versions
parameters
seed
initial_state
random_stream_version
event_log
final_state
metrics
```

相同：

```text
model_version
scenario_version
theory_versions
parameters
seed
initial_state
```

必须产生：

```text
identical results
```

---

# 57. Counterfactual Replay

允许保持：

```text
same seed
same initial state
same random stream
```

只修改：

```text
one mechanism
```

例如：

```text
Representation ON
vs
Representation OFF
```

用于机制识别。

---

# 58. Mechanism Ablation

初始对照组：

```text
Full Model
Full - Representation
Full - Information
Full - Organization
Full - Coalition
Full - Network
```

比较：

```text
Δ Representation Drift
Δ Information Distortion
Δ Power Concentration
Δ Coalition Stability
```

---

# 59. Initial Experiment Set

### Experiment A

Information Quality vs Representation Drift

### Experiment B

Accountability vs Representation Drift

### Experiment C

Organization Capacity vs Effective Political Power

### Experiment D

Hierarchy Depth vs Information Distortion

### Experiment E

Coalition Size vs Coalition Stability

### Experiment F

Network Centrality vs Political Power Concentration

---

# 60. Batch Experiment

初始批量实验：

```text
100 ticks
1000 seeds
```

例如 5×5 参数扫描：

```text
information_quality:
0.2
0.4
0.6
0.8
1.0
```

```text
accountability:
0.2
0.4
0.6
0.8
1.0
```

总实验数量：

```text
25,000 simulations
```

---

# 61. Experiment Output

每个实验至少输出：

```text
final_state.json
timeseries.csv
event_log.json
metrics.json
experiment_config.json
```

---

# 62. Event Log

重大政治事件必须记录：

```text
tick
event_type
actors
targets
cause
available_information
incentives
state_change
```

系统必须可以回答：

> What happened?

> Who acted?

> Against whom?

> What information was available?

> What incentives existed?

> What changed?

---

# 63. No Hard-Coded Political Outcome

禁止：

```text
leader must emerge
faction A must win
democracy must collapse
dictatorship must emerge
coalition must succeed
```

系统只能定义：

```text
rules
constraints
preferences
resources
information
institutions
```

结果必须由模拟过程产生。

---

# 64. Historical Scenario Boundary

历史人物、历史事件、历史制度只能属于：

```text
Scenario Layer
```

不能进入：

```text
Simulation Core
```

例如：

```text
Young Stalin
```

应被实现为 Scenario，而不是 Core Actor 类型。

---

# 65. No Intrinsically Good or Bad Actors

模型中：

```text
Individual
Organization
Faction
Coalition
Institution
```

都不带：

```text
good
evil
hero
villain
```

等内置价值标签。

---

# 66. LLM Boundary

v0.2 不将 LLM 接入权威模拟循环。

LLM 未来可以负责：

```text
reasoning
dialogue
negotiation language
belief interpretation
scenario generation
explanation
theory-to-model translation
```

但不能直接决定：

```text
true state
resource quantity
institutional rule
political outcome
```

---

# 67. Project Architecture

推荐目录：

```text
political_sim/
├── core/
├── theories/
├── simulation/
├── experiments/
├── scenarios/
├── output/
└── docs/
```

建议：

```text
core/
    models/
    actions/
    state/
    random/

simulation/
    engine/
    ticks/
    systems/

theories/
    base/
    representation/
    coalition/
    information/

experiments/
    configs/
    runners/
    analysis/

scenarios/
    sandbox/
    historical/

output/
    runs/
    metrics/
    logs/

docs/
```

---

# 68. Implementation Rules for Cursor

第一阶段必须：

```text
headless
deterministic
testable
observable
```

禁止第一阶段加入：

```text
UI
LLM
historical characters
warfare
complex economics
propaganda simulation
```

除非其对核心机制验证必要。

---

# 69. UI Boundary

UI 不允许直接修改：

```text
WorldState
```

所有修改必须通过：

```text
SimulationEngine
ActionResolver
```

---

# 70. Acceptance Criteria

v0.3 最低要求：

- 20 agents
- 4 groups
- 4 representatives
- 2 organizations
- 2 factions
- 1 institution
- 100 ticks
- deterministic same seed
- true state / belief separation
- all political actions through ActionResolver
- major transitions logged
- four core metrics
- JSON final state
- CSV time series
- headless
- no historical characters required
- no hard-coded political outcome

---

# 71. Unit Tests

必须至少测试：

```text
Group aggregation
Group cohesion
Representation fidelity
Representation drift
Information transmission
Belief update
Coalition stability
Power calculation
Seed reproducibility
Action validation
Event logging
```

---

# 72. Debug Assertions

运行时必须检查：

```text
probability ∈ [0,1]
fidelity ∈ [0,1]
cohesion ∈ [0,1]
power >= 0
resources >= 0
valid actor references
valid group references
valid representation edges
```

---

# 73. Versioning

每次实验必须记录：

```text
model_version
scenario_version
theory_version
random_stream_version
```

模型变化不能覆盖旧实验。

---

# 74. Future Theory Modules

未来可加入：

```text
Selectorate Theory
Coalition Formation Theory
Principal-Agent Theory
Spatial Preference Models
Bureaucratic Politics
Network Theory
Institutional Theory
Collective Action Theory
Elite Competition Models
```

这些都是候选模块，而不是 v0.2 的硬编码政治真理。

---

# 75. Model Arena

未来平台可以支持：

```text
same scenario
same initial state
same seed
different theory modules
```

例如：

```text
Model A
Model B
Model C
```

比较：

```text
power concentration
coalition stability
representation drift
information distortion
```

目的：

> 比较模型，而不是宣布某一理论“正确”。

---

# 76. Experiment Repository

未来允许用户：

```text
create experiment
fork experiment
modify parameters
run experiment
share experiment
compare results
```

实验应包含：

```text
scenario
theory
parameters
seed
model version
results
```

---

# 77. Scenario Builder

普通用户可以：

```text
create groups
create organizations
create institutions
set preferences
set resources
set information quality
set representation
```

高级用户可以：

```text
edit formulas
select theory modules
modify rules
```

---

# 78. Research Reproducibility

每个公开实验必须允许：

```text
download configuration
download seed
download model version
download theory version
replay experiment
```

目标：

> Another researcher should be able to reproduce the same simulation.

---

# 79. Model Limitations

v0.2 明确不声称：

```text
real politics = this model
```

它只是：

```text
formal experimental environment
```

因此：

- 参数不是现实世界常数。
- 指标不是现实政治价值判断。
- 模型结果不是历史事实。
- 模型不能自动证明政治理论正确。
- Scenario 与 empirical evidence 必须分开。

---

# 80. First Research Hypotheses

初始实验可以测试：

### H1

信息质量下降是否导致 Representation Drift 上升？

### H2

Accountability 是否降低 Representation Drift？

### H3

组织能力是否放大群体的 Effective Political Power？

### H4

层级越深，Information Distortion 是否越高？

### H5

Coalition Size 是否存在稳定性临界点？

### H6

Network Centrality 是否导致 Political Power Concentration 上升？

这些都是待验证假设，不是预设结论。

---

# 81. Core Six Equations

v0.2 最核心的六组关系：

### Group Interest

\[
G_g^k =
\frac{\sum_i w_iP_i^k}
{\sum_iw_i}
\]

### Group Cohesion

\[
Cohesion_g=
1-MeanDistance(P_i,G_g)
\]

### Effective Collective Power

\[
EffectivePower_g=
PotentialPower_g
\times Organization_g
\times Cohesion_g
\times Mobilization_g
\]

### Representation Drift

\[
RD=
Distance(GroupPreference,RepresentativeAction)
\]

### Information Transmission

\[
I_{up}=qI_{down}
\]

### Political Power

\[
PP_i=
Normalize(
Personal+
Represented+
Organizational+
Network+
Institutional
)
\]

---

# 82. Non-Goals for v0.3

以下暂不进入核心：

```text
full historical simulation
warfare
economic macro-model
mass media simulation
social media
LLM autonomous agents
complex ideology ontology
elections
constitutional design editor
```

除非某一项成为核心机制实验所必需。

---

# 83. Cursor Instruction

Cursor 开发时必须遵守：

```text
Do not bypass SimulationEngine.

Do not mutate WorldState directly from UI.

Do not use unseeded randomness.

Do not let actors read True State.

Do not hard-code political outcomes.

Do not mix Scenario data into Core rules.

Do not put Theory-specific assumptions into Core unless explicitly declared.

Every major state transition must be observable through EventLog.

Every experiment must be reproducible.
```

---

# 84. Definition of Done — v0.3

当以下条件全部满足：

```text
[ ] Core entities implemented
[ ] WorldState implemented
[ ] SeededRandom implemented
[ ] SimulationEngine implemented
[ ] 17-step Tick protocol implemented
[ ] Information system implemented
[ ] Belief system implemented
[ ] Representation system implemented
[ ] Coalition system implemented
[ ] Power system implemented
[ ] Metrics implemented
[ ] EventLog implemented
[ ] ExperimentConfig implemented
[ ] BatchRunner implemented
[ ] deterministic replay verified
[ ] unit tests pass
[ ] headless experiment runs
```

即完成 v0.3 核心闭环。

---

# 85. Development Principle

开发过程中始终保持：

```text
Model first
Experiment second
UI third
Presentation last
```

不要因为 UI 需求破坏核心模型。

不要因为历史叙事破坏可重复性。

不要因为游戏性破坏理论可替换性。

---

# 86. Final Principle

本项目最终不是：

> “模拟某一个政治人物。”

而是：

> “建立一个可以模拟、比较、复现和解释政治机制的实验平台。”

平台的核心价值不是告诉用户：

```text
What politics is.
```

而是允许用户实验：

```text
What happens if...
```

---

# Appendix A — Initial Repository Structure

```text
political_sim/
├── core/
│   ├── models/
│   │   ├── individual.py
│   │   ├── group.py
│   │   ├── organization.py
│   │   ├── representative.py
│   │   ├── faction.py
│   │   ├── coalition.py
│   │   ├── institution.py
│   │   ├── representation.py
│   │   ├── belief.py
│   │   └── world_state.py
│   │
│   ├── actions/
│   │   └── action_resolver.py
│   │
│   ├── random/
│   │   └── seeded_random.py
│   │
│   └── events/
│       └── event_log.py
│
├── simulation/
│   ├── engine.py
│   ├── tick_processor.py
│   └── systems/
│
├── theories/
│   ├── base/
│   ├── representation/
│   ├── coalition/
│   └── information/
│
├── experiments/
│   ├── configs/
│   ├── runners/
│   └── analysis/
│
├── scenarios/
│   ├── sandbox/
│   └── historical/
│
├── output/
│   ├── runs/
│   ├── metrics/
│   └── logs/
│
└── docs/
    └── POLITICAL_SIMULATION_MODEL_SPEC_V0.2.md
```

---

# Appendix B — Immediate Implementation Order

## PR-1

Data model：

```text
Individual
Group
Organization
Representative
Faction
Coalition
Institution
RepresentationEdge
Belief
WorldState
```

## PR-2

Simulation infrastructure：

```text
SimulationEngine
TickProcessor
SeededRandom
ActionResolver
EventSystem
```

## PR-3

Information：

```text
InformationSystem
BeliefSystem
```

## PR-4

Representation：

```text
Group aggregation
RepresentationEdge
Representation Fidelity
Representation Drift
```

## PR-5

Political organization：

```text
Faction
Coalition
```

## PR-6

Power and metrics：

```text
PowerSystem
MetricsSystem
EventLog
JSON output
CSV output
```

## PR-7

Experiments：

```text
ExperimentConfig
ExperimentRunner
BatchRunner
```

---

# Appendix C — First Milestone

第一阶段只需要做到：

```text
20 individuals
↓
4 groups
↓
4 representatives
↓
2 organizations
↓
2 factions
↓
1 institution
↓
100 ticks
↓
deterministic output
↓
metrics
↓
event log
```

如果这个闭环能够稳定运行，就已经具备：

```text
Political Simulation Core
```

之后再逐步增加：

```text
network
bureaucracy
elections
media
ideology
economics
war
LLM agents
historical scenarios
```

而不是反过来。

---

## Final Development Rule

> **先让一个简单政治系统能够稳定、可重复、可解释地运行，再让它变复杂。**

