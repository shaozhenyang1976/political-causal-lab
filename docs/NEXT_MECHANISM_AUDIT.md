# Next Mechanism Audit

Status: **NEXT MECHANISM AUDIT — CLOSED**

Preparation only — PR-13 NOT STARTED. This stage is closed. The next step is to wait for a research question the current model cannot answer, not to change code.

This file exists to stop causal edges that have not been justified by a research question. It does not exist to find missing features. The baseline remains **PR-1~PR-12: OPEN-LOOP BASELINE — FROZEN**. The engine is unchanged, production code is unchanged, and the tests remain 132 / 132. Resource remains a disconnected outcome variable. All six candidates remain **UNDECIDED**. No mechanism has been selected.

## 0. The audit question

A gap is not found by asking what would make a more complete social-behavior simulator. The existence of a relation in real society does not require the simulator to implement it.

A candidate edge enters implementation only after a research question has been stated and three further questions have been answered together:

1. Can the current model answer that question without the edge?
2. If the edge is added, can one operational variable be defined?
3. Can exactly one experimentally checkable causal edge be added?

Until the research question is stated, those three answers remain **UNDECIDED**. The candidates below are not confirmed gaps.

## A. Causal edges already covered

```text
Reality P
  ↓  e          Generation          G(p, e) = clamp(p - e, 0, 1)
  ↓  q          First hop           received₁ = q × G
  ↓  fidelity   Forwarding          each later information_forward hop multiplies by fidelity
  ↓  trust      Admission           received is written to belief only if t ≥ τ
  ↓             ConstraintPolicy    intent is produced only from an admitted belief
  ↓             Intent              one record per representative per tick; WorldState is unchanged
  ↓             Explicit Action     submitted explicitly; not the same as intent
  ↓             ActionResolver      only support / oppose may be admitted
  ↓             Consequence         the actor's resource increases by 1
  ↓             Resource            initial_resource + accepted_action_count
  ↓
  X             disconnected
```

The following are also fixed and must not be quietly rewritten by a new edge:

- `e`, `q`, `fidelity`, and `trust` each act only on their own layer.
- `Intent ≠ Action ≠ Consequence`.
- `accepted_action_count` and `initial_resource` have separate origins.
- Hop count does not attenuate. Only an explicit `fidelity < 1` changes later payloads.
- Conflicting signals are not averaged. Multiple beliefs are not averaged.
- `RepresentationEdge.trust` and `RepresentationEdge.fidelity` are stored fields, not mechanisms.
- The direct observer's `transmission_gap` is 0. `estimated_information` remains `q`.
- A new mechanism must neither write Resource nor read Resource.

## B. Candidate edges still under review

All are **UNDECIDED**. Listing them means they may be reviewed. It does not mean they are missing, and it does not mean they should be implemented.

| Candidate edge | Status |
| --- | --- |
| Action → Information | UNDECIDED |
| Action → Reality | UNDECIDED |
| Action → Relationship | UNDECIDED |
| Action → Organization | UNDECIDED |
| Belief → Belief | UNDECIDED |
| Action → Trust | UNDECIDED |

The following are not added early, before they pass the three questions above on their own. Each can pull in several feedback edges at once: resource feedback, trust learning, reputation, power, an influence mechanism, organizational hierarchy, charisma, popularity, and action probability. The existing `capabilities.influence` participates only in the weight of a true observation. It is none of those mechanisms.

## C. Necessity review

No research question has been stated, so the table below draws no conclusion.

| Candidate edge | Can the target question be answered without it? | Can one operational variable be defined? | Can one verifiable edge be added? |
| --- | --- | --- | --- |
| Action → Information | UNDECIDED | UNDECIDED | UNDECIDED |
| Action → Reality | UNDECIDED | UNDECIDED | UNDECIDED |
| Action → Relationship | UNDECIDED | UNDECIDED | UNDECIDED |
| Action → Organization | UNDECIDED | UNDECIDED | UNDECIDED |
| Belief → Belief | UNDECIDED | UNDECIDED | UNDECIDED |
| Action → Trust | UNDECIDED | UNDECIDED | UNDECIDED |

A single-edge card is not filled until a row leaves UNDECIDED. The card format is:

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

### Confusions already visible at review

**Action → Information.** Existing information comes only from reality and explicit forwarding. An action is not yet an information source. A review must first answer which already-occurred action, observed by whom, produces which signal. An admitted action must not be written directly as the next signal.

Two claims have to stay separate: an action can carry information, and an action therefore changes belief. In the current pipeline, a signal that enters transmission is admitted on the next tick and may be written as belief. If the new signal uses the existing Information → Belief path, the wording “carrier only” still opens a second edge. To keep one edge, the observable event must stop before it enters `belief_update`, unless the research question explicitly requires the signal as a belief input and counts that as the single edge.

**Action → Reality.** The current consequence deliberately does not change preferences, beliefs, or information. Reality is unchanged by action because the loop was left open, not because a hole remains to be patched. A review must first name which `WorldState` variable Y is changed by action X. If the next tick’s generation reads Y, the edge is feedback, not a terminal consequence.

**Belief → Belief.** The rule that multiple beliefs are not averaged automatically is frozen. A transmission between beliefs must not be implemented as averaging or as mutual overwrite.

**Action → Trust.** Trust is currently only the admission gate `t`, `τ`. An action that changes trust connects the execution layer back to admission and immediately forms Action → Trust → Belief → Intent → Action. That is not an isolated edge.

## D. Result of this stage

No new causal edge has been shown to be necessary. All six candidates remain **UNDECIDED**, and the three necessity questions remain blank. That is the result of this stage. It is not an empty form waiting to be filled.

Two review principles are frozen together:

1. Ease of attachment is not necessity. `Action → Information` is not adopted merely because it can be wired into the existing pipeline. If it is studied later, the observable event must stop before `belief_update`. Otherwise the signal follows Information → Belief, and a nominal “information carrier” is already Action → Belief.
2. `Action → Reality` is not next merely because it sits later in the chain. The present `Action → Consequence → Resource` is a terminal outcome. If a WorldState variable rewritten by action enters the next tick’s generation, the result is Action → Reality → Information → Belief → Intent → Action, not a bare consequence.

The model is not incomplete because a real-world mechanism is absent. A mechanism is necessary only when a stated research question cannot be answered by the existing causal structure.

The six candidates are hypotheses awaiting audit, not features awaiting implementation. Feedback is judged on later causal outputs, not on a change in one intermediate number. The formal test follows this path:

```text
Action
  ↓
a variable changes, or information is produced
  ↓
a later tick
  ↓
does it enter an existing read or process path?
  ├─ No → not feedback
  └─ Yes
       ↓
     does a causal output change?
       ├─ No → not feedback
       └─ Yes → Level 3 feedback
```

Causal outputs are generation, transmission, belief, intent, and action. `ΔBelief = 0` and `ΔIntent ≠ 0` is still Level 3. `ΔWorldState ≠ 0` or `ΔEventLog ≠ 0` is not, by itself, feedback. If the changed variable never enters a later read path, a later change in output is not feedback from that action.

Level 3 identifies feedback. It is not a license that says only feedback edges may be added. Without a research question and a necessity proof, a new Level 1 edge is also forbidden. Existing state changes do not qualify any candidate for PR-13. No existing feedback needs repair.

Only Level 3 is called feedback:

```text
Level 1 — State Change
Action → Consequence → WorldState

Level 2 — Observation
State Change → EventLog

Level 3 — Causal Feedback
Changed state or derived information
        ↓
   later read or process
        ↓
a downstream causal output changes
```

Level 3 requires the whole path, not a single output change. A variable changed by an action, or information derived from an action, must enter an existing read or process path on a later tick, and at least one later causal output must change because of that. Later causal outputs are generation, transmission, belief, intent, and action. A new value in the event log, the `state_change` of `action_consequence`, a modified WorldState, and the mere existence of a next tick all stop at Level 1 or Level 2.

An unchanged belief value can still be Level 3. If an action-derived signal enters the next tick’s information pipeline and is handled by `belief_update`, the trust gate may refuse admission: the stored belief keeps its value and intent becomes `seek_information`. Then `ΔBelief = 0` and `ΔIntent ≠ 0`. Defining feedback as “the belief number changed” misses that path. `trust_rejected` is still not absence of information, not belief error, and not `constraint:delay`.

Both tests use this Level 3 standard:

1. **Information feedback test.** Does action-derived information enter the information pipeline consumed by `belief_update` on a later tick, and therefore change the belief stage or the downstream intent or action? `political_action` in the same tick cannot reach the `belief_update` that has already finished. An extra observation event placed before `belief_update` does not, by its position, cut that path.
2. **State feedback test.** Is a state variable changed by an action read again by an upstream mechanism on a later tick, and does that change the mechanism’s output or the downstream generation, transmission, belief, intent, or action? 

`Action → Resource` stops at Level 1. Its event record stops at Level 2. Generation does not read Resource. `Action → Preference'` reaches Level 3 only if the rewritten preference enters the next tick’s generation and changes information, belief, intent, and a later action.

An event log can record a fact without the model having established that causal relation. Existing state changes are not a reason to start PR-13.

## E. Two independent gates

Level 3 answers “is this feedback?” Admission answers “may this edge exist?” Neither substitutes for the other.

**A. Feedback classification.** Level 3 holds only when all three are true: an action changes a variable or produces information; that change enters an existing read or process path on a later tick; and at least one of generation, transmission, belief, intent, or action therefore changes. `ΔBelief = 0` and `ΔIntent ≠ 0` still counts. `ΔWorldState ≠ 0` or `ΔEventLog ≠ 0` alone does not.

**B. Admission of a new mechanism.** The order is: a stated research question; whether the current model cannot answer it; the required variables; an operational definition; a necessity proof; the minimal causal edge; an isolated control experiment; and only then eligibility for a PR. The new edge is not required to be Level 3 feedback. An unread `Action → NewOutcome` can be a legitimate Level 1 terminal edge, but only after this admission sequence. Conversely, `Action → X → Generation → … → Action` is a feedback loop by nature and still cannot start PR-13 without a research question that requires it.

Feedback is a classification standard, not an admission standard. A closed causal loop is not a reason to add a mechanism. The research question is.

Therefore feedback is not admission. A terminal edge is not automatically legitimate. A feedback loop is not automatically legitimate. The only thing that can start the next stage is a stated research question that the current model cannot answer. Remaining frozen until then is the research procedure, not a stall.

Until both gates have been passed, the 132 tests, the production code, the engine, and PR-1 through PR-12 stay frozen. There is no PR-13.

## F. Experimental stage — FROZEN

The work cycle is: experiment, observe, interpret, then ask whether the current model is sufficient. If it is, record a model conclusion. Only strict non-identifiability enters mechanism admission. The cycle is not: experiment, find a gap, add a mechanism.

A negative result is a model conclusion. An admitted action does not change the next tick’s belief. That is an answer already given by the open loop. It is not a missing `Action → Information` edge.

Identifications already closed:

- Looking only at first-hop belief, both `e` and `q` can reduce it to the same number. The event log still separates them: `e` changes `signal_generated`; `q` does not change the generated signal and changes only the first-hop received value.
- `fidelity` does not change the direct observer. The first hop remains `q × G`. Fidelity changes only later forwarding. The direct observer and a downstream observer can be separated in the event chain.
- `trust < τ` decides the current tick’s intent before `ConstraintPolicy`. A combined run that shows `trust_rejected` does not mean `delay` failed. Execution order let trust rejection decide the current intent first. Belief may keep its previous value. A constraint applies only after admission and after the belief has been written.

Identifiability conclusion: the same final state is not the same as a non-identifiable causal path. For `e=0.25, q=1` and `e=0, q=0.75`, first-hop belief is `0.75` and intent is `baseline:support` in both cases. `signal_generated` is `0.75` and `1.0` respectively, and received is `0.75` in both. For `q=0.5, fidelity=1` and `q=1, fidelity=0.5`, second-hop belief can be `0.5` in both cases, while the first hop is `0.5` and `1.0`. A downstream slice alone confounds the paths. The full event chain plus network position recovers the source. The event does not need a label that names the final cause. `trust_rejected` has no `belief_updated`. `constraint:seek_information` writes the belief first. Whether a stage occurred is itself identifying. When `q=0`, the full event logs for `fidelity=1` and `fidelity=0.5` are identical, because `0 × fidelity` is still 0. Another result event would not create a new observable difference. Copying the parameter name into the log only restates the input. This is non-identifiability on an information-collapse boundary. It is not a model defect, and it is not a PR-13 candidate.

Identifiability principle: the same final result is not the same causal path. Inspect the full event log first. Only when the full traces are also identical is an information-collapse boundary considered. A research question is the premise of an experiment. It is not a separate gate. The judgment is whether the present non-identifiability blocks that research question. An identical full event log does not mean the log is too coarse, and it is not a reason to add log fields or mechanisms.

Two gates:

1. A counterintuitive result is not a model defect. First decide whether it is a valid conclusion of the current model. If it is, record it and do not change the model. If it is not, continue the analysis. Do not go straight to code.
2. Non-identifiability is not a reason to add a mechanism. First decide whether it blocks the current research question. If it does not, record the boundary. Mechanism review reopens only when the question itself requires those parameters to be distinguished.

When `q=0`, the full event chains for `fidelity=0.5` and `fidelity=1` both show a first hop of 0 and later propagation of 0. If the question is whether the first hop becomes 0, the model has answered it and the inquiry stops. Mechanism review may reopen only if the question becomes: under `q=0`, these two fidelity values must be distinguished.

Expansion requires both of the following: the result is not a conclusion the current model has already given, and the non-identifiability blocks the current research question. Two affirmative answers do not both point to a PR. Until then, continue to experiment and do not develop.

The causal system has three layers. The first is mechanism: `e` at generation, `q` at the first hop, `fidelity` on later forwarding, `trust` at admission, and `ConstraintPolicy` at intent. The second is the observable trace on the event log, which separates those paths. The third is the non-identifiability boundary: after the input signal collapses, different parameters produce identical traces. When `q=0`, first-hop received is 0 and later propagation remains 0, so different `fidelity` values no longer differ observably. The third layer is an information boundary under the current observations. It is not a model error.

That round stops here. The event log is not extended further. The next step remains: pose a research question to the current model, run it, observe, interpret, and judge whether the current model is sufficient.

Mechanism admission has one remaining trigger: a stated research question that is still not decidable after the existing observable outputs have been exhausted. None of the following is a trigger: the real world has the mechanism; the model does not yet have the variable; the edge would be easy to attach; it would form a feedback loop; it would be more realistic; a variable looks as though it should do more; the result differs from intuition.

Until that trigger appears, the 132 tests, the production code, the engine, and PR-1 through PR-12 stay frozen. There is no PR-13. Continue to use the current model experimentally.

### Experiment 1 — CLOSED

`e × q × fidelity`. The model can answer. No phenomenon appeared that the current model cannot explain. No mechanism is added, and no code is changed.

1. `e`, `q`, and `fidelity` are not one information-loss rate. They stop at different stages. `e` changes only `signal_generated`. `q` changes only the first hop and therefore scales later hops in proportion. `fidelity` does not change the first hop. It multiplies on each later `information_forward`. For `e=0.25, q=1` and `e=0, q=0.75`, every hop has belief `0.75` and intent `support`. Only the generated signal separates them.
2. `fidelity` accumulates along later hops. It does not apply one static discount to every person. For `e=0`, `q=1`, and `fidelity=0.5`, the four hops are `1`, `0.5`, `0.25`, and `0.125`, with intents `support`, `abstain`, `oppose`, and `oppose`. Accumulation occurs on later hops of the same tick. It is not deferred to later ticks.
3. Belief is continuous and intent is discrete. For `e=0.25`, `q=0.75`, and `fidelity=0.5`, the direct observer’s belief is `0.5625` and intent remains `support`. The second hop, `0.28125`, becomes `oppose`. Belief can fall substantially without crossing `0.5`. That is a result of the current decision policy, not an anomaly.
4. The three losses multiply in causal order. They are not `1 - 0.25 - 0.25 - 0.5`, and they are not collapsed into one total loss rate. The signal in the example is `0.75 × 0.75 × 0.5 × 0.5 × 0.5`. The telescoping gap identity still holds. It decomposes a difference in results. It is not the generative mechanism.

### Experiment 2 — CLOSED

`trust × q`. Fixed `e=0`, `fidelity=1`, and `τ=0.5`. Only the direct observer is observed. `q` is in `{1, 0.75, 0.5, 0}`. Admission uses `trust=1`. Rejection uses `trust=0`. The model can answer. No mechanism is added, and no code is changed.

1. `q` and `trust` are not at the same stage. The generated signal is `1.0` in all eight runs. `q` changes only received. `trust` does not change received. It decides whether that received value is written into belief.
2. The same received value can take two paths. At `q=0.5`, received is `0.5` in both cases. Admission writes belief `0.5` and intent `baseline:abstain`. Rejection writes no belief, and the `action_intent` cause is `trust_rejected`. Received alone does not determine the path.
3. `q=0` separates “the value is 0” from “no belief record exists.” Admission writes belief `0` and intent `baseline:oppose`. Rejection also has received `0`, no belief exists, and the cause is `trust_rejected`. The rejection event’s `available_information` additionally records `intent=seek_information`. The cause is `trust_rejected`. The intent type is `seek_information`. That is not the same state as a written zero belief. Numeric collapse and whether a belief is written are two layers.

Low quality and low trust affect the decision by different paths. The current model separates them completely. The event log’s stage information is sufficient.

### Experiment 3 — CLOSED

`trust × ConstraintPolicy`. Fixed `e=0`, `q=1`, `fidelity=1`, and `τ=0.5`. Only the direct observer is observed. The model can answer. No mechanism is added, and no code is changed.

1. Trust rejection precedes ConstraintPolicy. At `trust=0`, the R1 event signatures for `seek_information` and `delay` are identical. The constraint did not fail. It did not run.
2. `seek_information` must separate intent type from cause. On rejection, the intent type is `seek_information` and the cause is `trust_rejected`. After admission, the same constraint still has intent type `seek_information` and cause `constraint:seek_information`.
3. ConstraintPolicy acts only after a belief has been written. On admission, belief is `1.0` and the causes are `constraint:seek_information` and `constraint:delay`. On rejection there is no `belief_updated`. That order is in the events.
4. Three similar-looking results can be separated. Unconstrained admission is belief `1.0` and `baseline:support`. Seeking information after a constraint is belief `1.0` and `constraint:seek_information`. Seeking information after trust rejection is no belief and `trust_rejected`. Intent, whether a belief was formed, and the cause together make the trace.

When trust and ConstraintPolicy are both present, execution order separates the two paths. The event log is sufficient.

### Experiment 4 — CLOSED

Whether information loss propagates automatically to Action or Resource. Fixed `fidelity=1`, `trust=1`, and `τ=0.5`, with no constraint. Only the direct observer is observed. The opening resource ledger is empty. The explicit submissions are `support`, `oppose`, or `abstain`, with target `G1`. The model can answer. No mechanism is added, and no code is changed. The combined boundary of the four experiments is in `docs/EXPERIMENT_BOUNDARY.md`.

| Condition | Belief | Intent cause | No submission | Submit `support` or `oppose` |
|---|---:|---|---|---|
| `e=0, q=1` | `1.0` | `baseline:support` | No admission; resource `{}` | `action_accepted`; resource `R1=1.0` |
| `e=0.25, q=0.75` | `0.5625` | `baseline:support` | No admission; resource `{}` | `action_accepted`; resource `R1=1.0` |
| `e=0, q=0.5` | `0.5` | `baseline:abstain` | No admission; resource `{}` | `action_accepted`; resource `R1=1.0` |
| `e=0, q=0.25` | `0.25` | `baseline:oppose` | No admission; resource `{}` | `action_accepted`; resource `R1=1.0` |
| `e=0, q=0` | `0.0` | `baseline:oppose` | No admission; resource `{}` | After submitting `support`, resource `R1=1.0` |

Submitting `abstain` at `q=0.5`: the intent cause remains `baseline:abstain`, the action is rejected with reason `unknown action type`, there is no `action_accepted`, and resource remains `{}`.

The admission cause for both `support` and `oppose` is `admitted (chosen)`. The admission event’s `available_information` remains `consequence=none`. The resource +1 is written by the following `action_consequence`. The resource increment is the same in both cases and does not read belief or intent. Submitting `oppose` while intent is `support` is still admitted and yields `R1=1.0`.

Information loss therefore changes belief. It changes intent only when the value crosses `0.5`. It does not produce an action and does not change resource. An action record and a resource change appear only after an explicitly submitted `support` or `oppose` is admitted. The same submission yields the same admission and the same resource on both sides of the threshold.
