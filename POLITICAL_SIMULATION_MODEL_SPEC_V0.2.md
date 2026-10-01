# Political Simulation Platform — Model & Implementation Specification v0.2

This file is a design specification. It is not a statement of what the running model can do. The executable portion is only the frozen open-loop baseline, PR-1 through PR-12. Empty tick slots have no execution body. Coalitions, institutions, power, interfaces, replaceable theories, and player-facing experiments are not mechanisms. Read `README.md`, `docs/BASELINE_EXPERIMENT_SPEC.md`, and `docs/EXPERIMENT_BOUNDARY.md` first.

The PR-1 through PR-7 labels in Appendix B are the original design sequence in this document. They are not the implemented freeze recorded in the baseline and boundary documents.

## 1. Purpose

This document defines the core political model, data structures, causal order, experimental mechanism, reproducibility requirements, and first-stage implementation boundary of Political Simulation Platform v0.2.

The objective is not to produce a game about one historical person or one historical event. The objective is a political-simulation foundation on which theories can be replaced, experiments can be reproduced, and explanations can be inspected.

Core question:

> Given individual preferences, group interests, organizational capacity, representation, incomplete information, coalitions, institutions, and networks, how do political power, political action, and political outcomes arise?

---

## 2. Project Positioning

The platform is organized in the following layers:

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

Design principles:

1. The simulation core is decoupled from historical content.
2. A theory module is pluggable and replaceable.
3. A scenario is data, not core logic.
4. Every experiment records a seed, a version, and its parameters.
5. A simulation must be observable and explainable.
6. A player or a researcher can create, copy, and modify an experiment.
7. No political outcome is written in as inevitable.
8. A language model is not the authoritative engine of political rules.

---

## 3. Design Philosophy

### 3.1 Individual ≠ Group

An individual has preferences and capabilities of their own.

A group interest is an aggregate of individual interests.

### 3.2 Group ≠ Organization

A group denotes a community of interest.

An organization denotes a coordination structure.

### 3.3 Representative ≠ Represented Group

A representative may be influenced at the same time by:

- the interest of the represented group
- a personal interest
- an organizational interest
- a superior's interest
- a coalition interest
- a survival interest

A representation relation is therefore not simply:

```text
Group Preference → Representative Action
```

It is:

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

Information may be distorted as it moves through a hierarchy by:

- random noise
- selective reporting
- strategic concealment
- misunderstanding
- interest filtering
- limited capability

Every participant can be rational, and the system can still distort information.

---

# 4. Core Entities

Core entities:

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

An individual is the basic unit of political behavior.

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

Each component is normalized to:

```text
[0, 1]
```

Preferences and capabilities must be kept strictly separate.

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

Principle:

```text
Preference ≠ Capability
```

A person may place a high value on power and still have little political capability.

---

# 6. Group

A group is a unit of interest aggregation.

A group contains some number of individuals.

---

# 7. Group Interest

Group interest is a weighted aggregate of member preferences.

For dimension k:

\[
G_g^k =
\frac{\sum_{i\in M_g} w_i P_i^k}
{\sum_{i\in M_g} w_i}
\]

Initial version:

\[
w_i = 0.5 + 0.5\times influence_i
\]

where:

```text
M_g = Group members
P_i^k = Individual preference
w_i = influence weight
```

A later theory module may replace this rule.

---

# 8. Group Cohesion

Internal agreement of a group:

\[
Cohesion_g =
1 - MeanDistance(P_i,G_g)
\]

The result is normalized to:

```text
[0, 1]
```

Interpretation:

- 0 = extreme internal disagreement
- 1 = high agreement

Note:

> Cohesion is a descriptive variable, not a value judgment.

---

# 9. Effective Collective Power

Potential group capability is not the same as effective political capability.

Baseline formula:

\[
EffectivePower_g =
PotentialPower_g
\times Organization_g
\times Cohesion_g
\times Mobilization_g
\]

where:

```text
PotentialPower
Organization
Cohesion
Mobilization
```

are each in:

```text
[0,1]
```

This structure is used to test:

> Why can a group that holds substantial resources still fail to produce effective political action?

---

# 10. Organization

An organization is a structure that turns persons or groups into a sustained capacity to coordinate.

Core variables:

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

An organization is not merely a collection of people.

---

# 11. RepresentationEdge

A representation relation must be modeled as an entity of its own.

```text
RepresentationEdge
```

Core fields:

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

Of these:

```text
fidelity
accountability
information_up
information_down
trust
dependency
```

may each be normalized to:

```text
[0,1]
```

---

# 12. Representation Fidelity

Definition:

\[
RF_{rg}\in[0,1]
\]

A higher RF means:

> The representative more accurately acquires and reflects the interest of the represented group.

Note:

RF is not a moral evaluation.

---

# 13. Representation Utility

A representative does not maximize only the group's interest.

Baseline:

\[
U_r =
w_GU_G+
w_PU_P+
w_OU_O+
w_SU_S+
w_IU_I
\]

where:

```text
U_G = Group utility
U_P = Personal utility
U_O = Organization utility
U_S = Survival / security utility
U_I = Institutional utility
```

The group weight is:

\[
w_G =
RF_{rg}\times Accountability_r
\]

All weights are normalized.

This allows the system to produce the following situation:

```text
the representative still regards the action as rational
```

while the action has already departed from the group's preference.

---

# 14. Representation Drift

Definition:

\[
RD =
Distance(GroupPreference, RepresentativeAction)
\]

Normalized to:

```text
[0,1]
```

Interpretation:

```text
0 = no measurable departure
1 = maximum departure
```

Representation drift is an experimental indicator, not a moral judgment.

---

# 15. Information System

The system must distinguish strictly between:

```text
True State
```

and:

```text
Belief State
```

An actor may hold incorrect information. The simulator still knows the true state.

---

# 16. Information Transmission

The simplest transmission rule:

\[
I_{up}=qI_{down}
\]

where:

```text
q ∈ [0,1]
```

Multi-level propagation:

\[
I_C=q_{BC}q_{AB}I_A
\]

Therefore the information quality along:

```text
A → B → C
```

may decline from level to level.

---

# 17. Belief

Each actor forms a belief about the state of other actors.

\[
Belief_i(j)=
(\hat P_{ij},\hat C_{ij},\hat L_{ij},\hat I_{ij})
\]

where:

```text
P̂ = estimated preference
Ĉ = estimated capability
L̂ = estimated loyalty
Î = estimated information
```

The following must hold:

```text
Belief ≠ True State
```

---

# 18. PoliticalActor

PoliticalActor is a dynamic state, not a fixed role.

An individual, a representative, an organization, a faction, or a coalition may become a political actor at a particular moment.

The core capacities of a political actor come from:

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

Baseline:

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

Political power is not a single attribute.

---

# 20. Faction

A faction is a bloc of political action.

A faction is not an organization:

```text
Organization = coordination structure
Faction = political action bloc
```

A faction may span several organizations.

---

# 21. Coalition

A coalition is a dynamic cooperative relation.

A coalition is not a faction.

It may be:

```text
temporary
conditional
issue-specific
strategic
```

---

# 22. Institution

An institution defines political rules that can be applied repeatedly.

Examples:

```text
decision rules
appointment rules
voting rules
resource allocation rules
succession rules
sanction rules
```

An institution does not decide a political outcome directly. It changes the action space and the payoff structure.

---

# 23. PoliticalAction

Every political action must be executed through:

```text
ActionResolver
```

Examples:

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

Core state must not be modified by bypassing ActionResolver.

---

# 24. WorldState

WorldState stores the simulator's true state:

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

This is a hard requirement of v0.2.

Inside the simulator:

```text
True State
```

is the only true state.

An actor's decision may access only:

```text
Actor Belief State
```

An actor must not read the true state directly.

Otherwise a model of incomplete information fails.

---

# 26. Simulation Architecture

Recommended structure:

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

Theory modules must be pluggable.

Interface concept:

```text
TheoryModule
 ├── update_belief()
 ├── evaluate_incentive()
 ├── evaluate_coalition()
 ├── select_action()
 ├── calculate_power()
 └── update_representation()
```

Different theories may implement different rules.

---

# 28. Theory Module Rules

A theory module must:

1. Not modify state it is not authorized to modify.
2. Not bypass ActionResolver.
3. Draw every random value from SeededRandom.
4. Make every core calculation recordable.
5. Record its version number.
6. Be replaceable by the experiment engine.

---

# 29. Layered Causality

Causal layers of the model:

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
next Tick
```

---

# 30. Tick Protocol

Each tick follows this order exactly:

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

The order is fixed.

---

# 31. Tick 01 — Environment Update

Updates:

```text
economic conditions
resource availability
external threats
institutional conditions
random events
```

---

# 32. Tick 02 — Information Generation

Generates:

```text
observations
signals
reports
rumors
events
```

---

# 33. Tick 03 — Information Transmission

Information propagates along:

```text
individual → representative
representative → organization
organization → faction
faction → coalition
```

Each edge has:

```text
transmission_quality
```

---

# 34. Tick 04 — Belief Update

An actor updates belief from:

```text
previous belief
new information
trust
prior belief
```

---

# 35. Tick 05 — Incentive Update

Computes:

```text
personal utility
group utility
organizational utility
survival utility
institutional utility
```

---

# 36. Tick 06 — Coalition Evaluation

Computes:

```text
cohesion
trust
expected payoff compatibility
defection cost
common threat
```

---

# 37. Tick 07 — Representative Decision

A representative selects an action from:

```text
belief
preferences
representation fidelity
accountability
organization
survival
institution
```

---

# 38. Tick 08 — Organization Decision

An organization forms an organizational action from:

```text
membership
discipline
resources
leadership
internal cohesion
external threat
```

---

# 39. Tick 09 — Political Action

Every action enters:

```text
ActionResolver
```

ActionResolver checks:

```text
permission
resource requirement
institutional constraint
actor capability
target validity
```

---

# 40. Tick 10 — Conflict / Bargaining

Handles:

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

Resources are reallocated according to:

```text
institutional rules
political actions
coalition agreements
organization rules
```

---

# 42. Tick 12 — Power Recalculation

Recalculates:

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

Updates:

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

Updates:

```text
alliances
communication links
dependency links
influence links
organizational links
```

---

# 45. Tick 15 — Survival / Replacement

The following may occur:

```text
leadership replacement
representative replacement
organizational exit
coalition collapse
faction transformation
```

Leader is not a permanent role.

---

# 46. Tick 16 — Metrics

Each tick computes:

```text
Representation Drift
Information Distortion
Political Power Concentration
Coalition Stability
```

---

# 47. Representation Drift Metric

\[
RD=
Distance(GroupPreference, RepresentativeAction)
\]

Record:

```text
mean
median
max
distribution
time series
```

---

# 48. Information Distortion Metric

One possible definition:

\[
ID =
Distance(TrueInformation, BelievedInformation)
\]

The following must be distinguished:

```text
generation error
transmission error
interpretation error
strategic concealment
```

---

# 49. Political Power Concentration

Using the Herfindahl–Hirschman index:

\[
HHI=\sum_i s_i^2
\]

where:

\[
s_i=
\frac{Power_i}{\sum_j Power_j}
\]

The index describes the degree of power concentration.

---

# 50. Coalition Stability

Baseline:

\[
S=
0.25C+
0.20T+
0.20E+
0.15D+
0.20H
\]

where:

```text
C = Cohesion
T = Trust
E = Expected payoff compatibility
D = Defection cost
H = Common threat
```

This formula is only a baseline.

Formal research must allow a theory module to replace it.

---

# 51. Leader Emergence

Leader should not be assigned directly as a fixed field.

Leadership can arise jointly from:

```text
network centrality
organizational control
resource control
information access
coalition coordination
institutional position
```

---

# 52. Initial Sandbox

The initial v0.2 experiment contains:

```text
20 Individuals
4 Groups
4 Representatives
2 Organizations
2 Factions
1 Institution
```

Each group contains:

```text
5 Individuals
```

Representation:

```text
G1 → R1
G2 → R2
G3 → R3
G4 → R4
```

Organizations:

```text
Organization A: R1, R2
Organization B: R3, R4
```

Factions:

```text
Faction A
Faction B
```

---

# 53. Group Initial Preferences

To control experimental variables, the initial groups may differ in preference:

```text
G1 → relatively high Security
G2 → relatively high Wealth
G3 → relatively high Status
G4 → relatively high Ideology
```

These are experimental variables. They do not represent any historical group.

---

# 54. Scenario Generator

The scenario generator is responsible for:

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

It must use:

```text
seeded random
```

---

# 55. Randomness

Every random draw passes through:

```text
SeededRandom
```

The following are forbidden:

```text
global random
untracked random
```

---

# 56. Reproducibility

Every experiment must record:

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

The same:

```text
model_version
scenario_version
theory_versions
parameters
seed
initial_state
```

must produce:

```text
identical results
```

---

# 57. Counterfactual Replay

It is permitted to hold fixed:

```text
same seed
same initial state
same random stream
```

and change only:

```text
one mechanism
```

For example:

```text
Representation ON
vs
Representation OFF
```

The comparison is used to identify a mechanism.

---

# 58. Mechanism Ablation

Initial control set:

```text
Full Model
Full - Representation
Full - Information
Full - Organization
Full - Coalition
Full - Network
```

Compare:

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

The initial batch design is:

```text
100 ticks
1000 seeds
```

For example, a 5×5 parameter sweep:

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

Total:

```text
25,000 simulations
```

---

# 61. Experiment Output

Each experiment writes at least:

```text
final_state.json
timeseries.csv
event_log.json
metrics.json
experiment_config.json
```

---

# 62. Event Log

A major political event must record:

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

The system must be able to answer:

> What happened?

> Who acted?

> Against whom?

> What information was available?

> What incentives existed?

> What changed?

---

# 63. No Hard-Coded Political Outcome

The following are forbidden:

```text
leader must emerge
faction A must win
democracy must collapse
dictatorship must emerge
coalition must succeed
```

The system may define only:

```text
rules
constraints
preferences
resources
information
institutions
```

Outcomes must be produced by the simulation.

---

# 64. Historical Scenario Boundary

Historical persons, historical events, and historical institutions belong only in:

```text
Scenario Layer
```

They must not enter:

```text
Simulation Core
```

For example:

```text
Young Stalin
```

is implemented as a scenario, not as a core actor type.

---

# 65. No Intrinsically Good or Bad Actors

In the model:

```text
Individual
Organization
Faction
Coalition
Institution
```

carry none of the built-in value labels:

```text
good
evil
hero
villain
```

---

# 66. LLM Boundary

v0.2 does not place a language model inside the authoritative simulation loop.

A language model may later be responsible for:

```text
reasoning
dialogue
negotiation language
belief interpretation
scenario generation
explanation
theory-to-model translation
```

It must not directly decide:

```text
true state
resource quantity
institutional rule
political outcome
```

---

# 67. Project Architecture

Recommended directories:

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

Suggested layout:

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

The first stage must be:

```text
headless
deterministic
testable
observable
```

The first stage must not add:

```text
UI
LLM
historical characters
warfare
complex economics
propaganda simulation
```

unless an item is necessary to validate a core mechanism.

---

# 69. UI Boundary

A user interface must not modify:

```text
WorldState
```

directly. Every modification passes through:

```text
SimulationEngine
ActionResolver
```

---

# 70. Acceptance Criteria

The minimum requirements stated for v0.3 are:

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

These are design acceptance criteria. They are not a claim that the running prototype meets them.

---

# 71. Unit Tests

At least the following must be tested:

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

Runtime checks must cover:

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

Every experiment must record:

```text
model_version
scenario_version
theory_version
random_stream_version
```

A model change must not overwrite an older experiment.

---

# 74. Future Theory Modules

Candidates that may be added later:

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

These are candidate modules. They are not political truths hard-coded into v0.2, and listing them does not schedule their implementation.

---

# 75. Model Arena

A later platform could support:

```text
same scenario
same initial state
same seed
different theory modules
```

For example:

```text
Model A
Model B
Model C
```

and compare:

```text
power concentration
coalition stability
representation drift
information distortion
```

The purpose is:

> to compare models, not to declare one theory correct.

---

# 76. Experiment Repository

A later system could allow a user to:

```text
create experiment
fork experiment
modify parameters
run experiment
share experiment
compare results
```

An experiment would contain:

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

An ordinary user could:

```text
create groups
create organizations
create institutions
set preferences
set resources
set information quality
set representation
```

An advanced user could:

```text
edit formulas
select theory modules
modify rules
```

---

# 78. Research Reproducibility

Every published experiment must allow:

```text
download configuration
download seed
download model version
download theory version
replay experiment
```

The objective is:

> Another researcher should be able to reproduce the same simulation.

---

# 79. Model Limitations

v0.2 does not claim:

```text
real politics = this model
```

It is only:

```text
formal experimental environment
```

Therefore:

- Parameters are not constants of the real world.
- Indicators are not value judgments about real politics.
- Model results are not historical facts.
- The model cannot by itself prove a political theory correct.
- A scenario and empirical evidence must be kept separate.

---

# 80. First Research Hypotheses

The initial experiments could test:

### H1

Does lower information quality raise representation drift?

### H2

Does accountability reduce representation drift?

### H3

Does organizational capacity amplify a group's effective political power?

### H4

Does a deeper hierarchy raise information distortion?

### H5

Does coalition size have a stability threshold?

### H6

Does network centrality raise political power concentration?

These are hypotheses to be tested. They are not preset conclusions, and they are not scheduled experiments of the frozen prototype.

---

# 81. Core Six Equations

The six central relations of v0.2:

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

The following do not enter the core at this stage:

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

unless one of them becomes necessary for a core-mechanism experiment.

---

# 83. Cursor Instruction

Development must observe:

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

The design checklist for a v0.3 core loop is:

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

Satisfying every item would complete the v0.3 core loop as defined here. `MODEL_VERSION = "0.2"` in the package does not mean this checklist is complete. Several items above have no execution body in the frozen prototype.

---

# 85. Development Principle

Development keeps this order:

```text
Model first
Experiment second
UI third
Presentation last
```

A user-interface request must not break the core model.

A historical narrative must not break reproducibility.

Gameplay must not break the replaceability of theory.

---

# 86. Final Principle

The project is not, finally:

> “a simulation of one political figure.”

It is:

> “an experimental platform on which political mechanisms can be simulated, compared, reproduced, and explained.”

The core value of the platform is not to tell a user:

```text
What politics is.
```

It is to let a user experiment with:

```text
What happens if...
```

The sentence above is the design aim of this specification. The published prototype is the frozen causal laboratory described in `README.md`, not this platform.

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

These labels are the original design sequence. They are not the implemented PR-1 through PR-12 freeze. Do not read a design item below as a claim that the corresponding mechanism runs.

## PR-1

Data model:

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

Simulation infrastructure:

```text
SimulationEngine
TickProcessor
SeededRandom
ActionResolver
EventSystem
```

## PR-3

Information:

```text
InformationSystem
BeliefSystem
```

## PR-4

Representation:

```text
Group aggregation
RepresentationEdge
Representation Fidelity
Representation Drift
```

## PR-5

Political organization:

```text
Faction
Coalition
```

## PR-6

Power and metrics:

```text
PowerSystem
MetricsSystem
EventLog
JSON output
CSV output
```

## PR-7

Experiments:

```text
ExperimentConfig
ExperimentRunner
BatchRunner
```

---

# Appendix C — First Milestone

The first design stage needs only:

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

If that loop runs stably, the design then has:

```text
Political Simulation Core
```

Only after that would the design add, in order:

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

and not the reverse. That sequence is a design note. It is not a development schedule for the frozen prototype.

---

## Final Development Rule

> **First make a simple political system run in a stable, repeatable, and explainable way. Only then make it more complex.**
