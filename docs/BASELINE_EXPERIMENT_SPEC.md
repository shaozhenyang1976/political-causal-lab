# Baseline Experiment Specification

Status: **CORE BASELINE — FROZEN**

The PR-8 admission gate is frozen separately as **PR-8 TRUST GATE — FROZEN**. Later forwarding is frozen as **PR-9 FIDELITY — FROZEN**. Both sit on top of the control conditions and do not rewrite the PR-7 meanings below. Explicit actions added after that treat resource as a terminal outcome and do not rewrite those meanings. Trust learning and relationship networks have not entered.

Frozen scope:

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

This freeze does not count trust as belief error. When `fidelity = 1`, later forwarding matches PR-8, so `transmission_gap` remains 0. The PR-7 control list above does not include dynamic trust, accountability, or concealment. Explicitly submitted actions and the resource consequence are specified in PR-10 and PR-11. They do not rewrite the information-to-intent meanings here. The PR-8 gate was added later. When it passes by default, the control conditions stay as they were.

## Control conditions

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

Causal relations already established:

```text
generation error  → belief error
q                  → belief error
hop count          → no additional error
constraint         → intent
Reality change     → next-Tick belief
Belief change      → same-Tick intent
```

## Information quality

information_quality = 1 does not mean the signal is true. It means the system does not further reduce an already generated signal.

`q = 1` means only that the system does not further reduce a signal that has already been generated. It does not mean that belief equals true preference. With `P = 0.8`, `e = 0.2`, and `q = 1`, the generated signal, the received signal, and the belief all remain at `G(p, e)`. True preference remains `0.8`.

## Generation error

G(p, e) = clamp(p - e, 0, 1)

`e` is a system experiment parameter of signal generation. The default is `0`. It applies only to the five preference components. It draws no random number, does not modify true preference, and does not modify the capability signal.

`e` is not actor bias, intentional distortion, or trust. `e < 0` is rejected.

Input domain:

```text
p = 0, e > 0 → 0
p = 1, e = 1 → 0
p = 0.2, e = 0.5 → 0
e = 0 → p
```

## Error decomposition

For the direct observer:

```text
belief_gap = generation_gap + quality_gap + transmission_gap
```

When `fidelity = 1`, `transmission_gap = 0`. Belief error is then attributed to generation error and the first-hop quality reduction. Hop count determines who receives the signal. It does not change the payload. Only an explicit `fidelity < 1` reduces later hops.

`generation_gap` is the distance from the true group signal to `signal_generated`. `quality_gap` is the distance from the generated signal to the first-hop received value. When `fidelity = 1`, later hops copy that received value.

## Baselines

True preference is fixed at `P = 1`. One factor moves at a time.

- Generation error: `e = 0, 0.1, 0.25, 0.5`, `q = 1`, one hop
- Information quality: `q = 1, 0.75, 0.5, 0`, `e = 0`, one hop
- Hops: 1 through 4, `e = 0.25`, `q = 0.5`
- Constraints: belief held fixed, `ConstraintPolicy` changed

## Time scale

| Causal path | Current implementation | Basis |
| --- | --- | --- |
| Reality → Belief | After a true-preference intervention, the next generation uses the new preference. Within a tick, intent sees the belief written by that tick's `belief_update` | Code: `information_generation` precedes `political_action`; `intervene_preference` is recorded on the current tick |
| Belief → Intent | Same tick | Code: `representative_decision` follows `belief_update` |
| Intent → Action | Explicit-submission boundary. No submission means no `action_accepted` | Code, and Experiment 4 |
| Action → Consequence | `action_accepted` does not change WorldState. The following `action_consequence` adds 1 to the actor's resource | Code, and PR-11 |

Within one tick the order is `signal_generated`, transmission, `belief_updated` or `trust_rejected`, `action_intent`, and only then a submitted action. Intent sees the belief already updated in that tick. On trust rejection, intent is not computed by reading the stored belief.

The Reality → Belief delay is this: after true preference is written by an intervention event, the old belief remains until the next belief update. `Constraint = delay` is a decision constraint, not that delay. The two are recorded separately.

## PR-8 trust gate

Status: **PR-8 TRUST GATE — FROZEN**

Trust is an admission gate before DecisionContext. It is not a fourth kind of belief error, and it is not another scaling of `q` or `e`. `RepresentationEdge.trust` is stored only. It does not enter generation, the first hop, or forwarding. The experiment parameter `t` and the edge field `trust` are not the same mechanism.

```text
received = q × G(p, e)
forward copies received

t ≥ τ: belief = received, and only then ConstraintPolicy
t < τ: received is not written into belief, and an existing belief is not deleted
       intent = seek_information
       cause = trust_rejected
```

The defaults are `t = 1` and `τ = 0.5`, so `t ≥ τ` and the control conditions match PR-7. `t = τ` also admits.

Three rejection distinctions:

- trust rejection ≠ belief error
- trust rejection ≠ constraint delay
- trust rejection ≠ no information

Later mechanisms must not break these six clauses:

1. Trust does not change signal_generated.
2. Trust does not change received.
3. t >= trust_threshold reproduces the baseline.
4. t < trust_threshold does not overwrite an existing belief.
5. trust_rejected is not part of belief_gap.
6. trust_rejected is not constraint:delay or no_belief.

`trust_rejected` is not `constraint:delay` and not `no_belief`. Rejection occurs before the decision policy. Even if `delay` is also set, the cause remains `trust_rejected`. After the gate is passed, `delay` takes effect under the original decision policy. When no signal is received, the cause remains `no_belief`.

An existing belief keeps its value after rejection. Non-admission does not write the belief as `0` and does not write it as the received signal. The `trust_rejected` event carries received, and `state_change` is empty.

Trust is not added to `belief_gap`. `belief_gap = generation_gap + quality_gap + transmission_gap` still describes only the numeric belief after admission. Measurement keeps three facts separate: the signal was generated, the signal was received, and whether this receipt replaced the belief.

## PR-9 fidelity

Status: **PR-9 FIDELITY — FROZEN**

Fidelity is an explicit experiment parameter on later `information_forward` hops. It is not `RepresentationEdge.fidelity`, and it does not change trust.

Each information_forward hop multiplies the already received payload by fidelity. The first hop does not. fidelity = 1 leaves that payload unchanged.

When `fidelity = 1`, the generated signal, the first-hop received value, later payloads, belief, intent, the rejection reason, and event order all match PR-8. Hop count still does not attenuate. Only `fidelity < 1` reduces the payload of later hops and permits `transmission_gap > 0` downstream. The first hop, generation error, the admission gate, and `ConstraintPolicy` are unchanged. The direct observer does not pass through forwarding, so that observer's `transmission_gap` remains 0. `estimated_information` stays equal to `q`. It does not fall as later fidelity factors accumulate.

Each mechanism acts only on its own causal layer:

1. e does not modify q, fidelity, or trust.
2. q does not modify fidelity or trust.
3. fidelity does not modify q or trust.
4. trust does not modify signal or received values.

Trust change and trust learning are not added in this step.

## PR-10 action boundary

Status: **PR-10 ACTION BOUNDARY — FROZEN**

This step answers three questions. It adds no political institution and produces no consequence.

1. Only `support` and `oppose` may pass from intent into action. `abstain`, `delay`, and `seek_information` remain intents.
2. An action must be submitted explicitly. `ActionResolver` admits it when the references are valid and records `action_accepted`. An intent event does not become an action by itself.
3. `action_accepted` does not change `WorldState`. That event's `state_change` is empty. The resource write is not in this section. See PR-11.

Therefore:

- Intent ≠ Action
- Action ≠ Consequence

`vote` and other action types whose consequences are not defined continue to be rejected with the reason `action effect is not implemented`. With no submitted action, event order matches PR-9.

## PR-11 consequence

Status: **PR-11 CONSEQUENCE — FROZEN**

This step opens one arrow: an admitted action produces one consequence.

An admitted action adds one resource unit to its actor. The addition does not change preferences, beliefs, information, fidelity, or trust.

The admission event stays as it was. `action_accepted` still has an empty `state_change`, and `available_information` is still `consequence=none`. A separate `action_consequence` event then adds 1 to the actor's resource. `support` and `oppose` share that consequence. The target, preferences, beliefs, generation, forwarding, and admission are unchanged by it.

An action that is not admitted produces no consequence. With no submitted action, the world and the event log match PR-10.

Trust change, relationship change, information change, reputation, and organizational consequences are not added in this step.

`resources + 1` does not enter generation, belief, or intent. The next tick's `signal_generated` and `belief_updated` match the run that submitted no action. The arrow is therefore `Action → Resource`, not `Action → Resource → future behavior`.

## PR-12 resource conservation

Status: **PR-12 RESOURCE CONSERVATION — FROZEN**

This step measures resource conservation. It does not assign resource to a causal layer.

resources_before + accepted_actions = resources_after

The four outcomes are fixed:

1. rejected_action adds 0 resources.
2. no_action adds 0 resources.
3. support adds 1 resource.
4. oppose adds 1 resource.

Resource still does not affect action availability, decision constraints, information access, preference, trust, or organizational position. The ledger definition is in `docs/RESOURCE_SEMANTICS.md`. The official name is **PR-1~PR-12: OPEN-LOOP BASELINE — FROZEN**. `Resource → ?` stays disconnected. PR-13 is not started. The semantic decision record is `docs/RESOURCE_SEMANTIC_ADR.md`. Its answers have not been made.

## Implementation correspondence

This section records only paths that the code executes. An empty slot means the phase exists and its function is empty. Experiments 1 through 4 did not retest each empty phase.

Tick order is `TICK_PHASES` in `political_sim/simulation/tick_processor.py`. The seventeen slots, in order, are `environment_update`, `information_generation`, `information_transmission`, `belief_update`, `incentive_update`, `coalition_evaluation`, `representative_decision`, `organization_decision`, `political_action`, `conflict_bargaining`, `resource_allocation`, `power_recalculation`, `representation_update`, `network_update`, `survival_replacement`, `metrics`, and `event_log`.

Only six phases have an execution body:

| Phase | Reads | Writes |
| --- | --- | --- |
| `information_generation` | Representation edges and the preferences and capabilities of group members. `capabilities.influence` enters only the aggregation weight `0.5 + 0.5 * influence` | The `signal_generated` event. True preferences are not modified. Beliefs, resources, organizations, factions, and institutions are not read |
| `information_transmission` | This tick's generated signals, `information_quality`, `fidelity`, and links whose `kind` is `information_forward` | WorldState is not modified. Conflicting payloads record `transmission_ambiguous`, and that pair is not delivered this tick. Edge `fidelity` and edge `trust` are not read |
| `belief_update` | This tick's deliveries and the global `trust` and `trust_threshold` | When `t ≥ τ`, the belief is written and `belief_updated` is recorded. When `t < τ`, `trust_rejected` is recorded and an existing belief is not overwritten |
| `representative_decision` | This tick's rejection table. If the observer was not rejected, the belief currently stored for that representative, the constraints, and `ConstraintPolicy` | An `action_intent` event only. Resources are not read. WorldState is not modified |
| `political_action` | Actions already `submit`ted before the tick, and whether the actor and targets exist | For `support` and `oppose`: `action_accepted` first (`consequence=none`, empty `state_change`), then `action_consequence` (the actor's resource increases by 1). Other known types are rejected with `action effect is not implemented`. Unknown types are rejected with `unknown action type` |
| `event_log` | Nothing | A `tick_completed` event only |

The other eleven slots are empty functions. The resource increment of 1 occurs in `political_action`, not in `resource_allocation`.

The run-level parameters are `generation_error`, `information_quality`, `fidelity`, `trust`, and `trust_threshold`. Each must lie in `[0, 1]`. `decision_constraints` are supplied per actor. Information, admission, intent, and resource settlement do not consume the random stream.

To reproduce an intervention, use the same `WorldState`, the same parameters, and the same submission sequence, and call `SimulationEngine.run`. A causal-trace comparison aligns event types, causes, whether a belief was written, the intent cause, and the resource delta. Cross-implementation reproduction does not require event strings to match character for character. The 132 tests lock the regression contract of this Python implementation, including its own event text.

The following are limits of what the current model can answer. They are not unimplemented features and they are not a backlog: per-actor or per-edge trust, a network that rewrites itself during a run, an action distribution when nothing is submitted, path dependence from a long run, and distinguishing `fidelity` when `q = 0`. Edge `fidelity`, edge `trust`, organizations, factions, and institutions are likewise unread at runtime. Mechanism review reopens only when a stated research question is blocked by one of these limits.
