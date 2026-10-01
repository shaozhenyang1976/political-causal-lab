# Experiments 1–4: Questions the Current Model Can Answer

Status: FROZEN. PR-1 through PR-12 are frozen. The 132 tests are frozen. The event log is frozen. Experiments 1 through 4 are closed. The model specification, the causal boundary, the identifiability boundary, and the mechanism-admission rule are frozen. The documents now correspond to the implementation. Read and write order, and the reproduction standard, are recorded in `docs/BASELINE_EXPERIMENT_SPEC.md`. There is no competitive moat. Originality is not established. A competitive barrier is not established. PR-13 has not started. Experiment 5 does not exist. The next task is not preset. The documentation audit is closed. Production code was not changed by that audit.

## Where automatic propagation stops

```text
Reality
  ↓
Generation
  │
  │ e
  ↓
signal_generated
  │
  │ q: first hop only
  ↓
first-hop received
  │
  │ fidelity: later information_forward hops only,
  │           accumulated hop by hop within the same tick
  ↓
Trust Gate
  ├─ reject
  │    ↓
  │  no belief_updated
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
       ╳  the only explicit-submission break
       ↓
     Action
       ↓
  action_accepted          consequence=none
       ↓
  action_consequence
       ↓
   Resource +1             does not read belief or intent, and there is no feedback
```

Three boundaries confirmed by experiment:

1. Information loss can change belief and does not guarantee a change in intent. Intent changes discretely at the decision threshold: a mean above `0.5` is `support`, below `0.5` is `oppose`, and exactly `0.5` is `abstain`. From `1.0` to `0.5625`, intent remains `baseline:support`.
2. Trust and ConstraintPolicy are both inside the automatic chain. Trust rejection cuts off the later belief write and the constraint. ConstraintPolicy handles only a belief that has already been written.
3. Intent to Action is the only explicit-submission break. After `support` or `oppose` is admitted, `Resource +1` follows automatically. The admission event itself is `consequence=none`. The +1 is written by the subsequent `action_consequence`. Other submissions, such as `abstain`, are rejected and leave resource unchanged. Resource settlement does not read belief or intent. There is currently no feedback.

The mark `╳` is not an unimplemented feature. It is a model boundary that has been measured and confirmed.

## Verified properties

1. `e`, `q`, and `fidelity` are not one loss rate, and they are not added before they act. The generative mechanism multiplies by causal position. For `e=0.25`, `q=0.75`, and `fidelity=0.5`, the signal is `0.75 × 0.75 × 0.5 × 0.5 × 0.5`. Fidelity accumulates on later forwards within the same tick. The telescoping gap account decomposes a difference in results. It is not the generative mechanism.
2. The same final belief can have different sources. `e=0.25, q=1` and `e=0, q=0.75` both yield belief `0.75` and intent `support`. The generated signals are `0.75` and `1.0`.
3. `q` changes the received number. `trust` decides whether that number is written into belief. With `q=0` and admission, the stored belief is `0` and the intent is `baseline:oppose`. With `q=0` and rejection, received is also `0`, no belief record exists, and the cause is `trust_rejected`. A numeric value of 0 and the absence of a belief record are two states.
4. Trust rejection precedes ConstraintPolicy. At `trust=0`, the event signatures for `seek_information` and `delay` are identical, because the constraint does not run. After admission, belief can be `1.0` in both cases while the intent causes are `constraint:seek_information` and `constraint:delay`.
5. Intent type and cause are separate. Rejection and “admitted, then constrained by `seek_information`” both carry a seek-information record. The first has no belief and cause `trust_rejected`. The second has belief `1.0` and cause `constraint:seek_information`. Unconstrained admission is belief `1.0` and `baseline:support`.
6. A change in belief or intent does not itself produce resource. Along the path from `support` to `abstain` to `oppose`, there is no `action_accepted` and resource remains `{}` unless an admissible action is submitted explicitly.
7. Explicit action is a second gate. Submitting `oppose` while intent is `support` is still admitted, and resource becomes `R1=1.0`. The same submission yields the same admission and the same resource on both sides of the threshold.
8. The set of intent types and the set of admissible action types are not in one-to-one correspondence. At `belief=0.5`, intent is `abstain`. Submitting `abstain` is rejected with reason `unknown action type`, and resource remains `{}`. The only admissible actions are `support` and `oppose`.

## The four questions are answered

| Experiment | Question | Answer |
|---|---|---|
| 1 | When the three information losses are combined, do they still act by causal position? | Yes |
| 2 | Do low quality and low trust follow different paths? | Yes |
| 3 | When trust and ConstraintPolicy are both present, can execution order separate “not admitted” from “belief formed, then constrained”? | Yes |
| 4 | Does information loss propagate automatically to Action or Resource? | No |

The current model answers all four. No phenomenon appeared that the model cannot explain, and the event log was sufficient for each question. PR-13 is not started on that account.

## Project discipline

This is an experimental causal laboratory. One research question is posed at a time. If the current model can answer it, run the experiment and record the conclusion. If it cannot, check whether the obstacle is non-identifiability for that question. If the non-identifiability does not block the question, record the boundary and add no mechanism. If it does, review the smallest necessary new causal edge. The model’s backlog is not “what the real world still lacks.” The backlog is “what the current research question still cannot answer.” No next stage is planned. The next task is not preset.

`information_forward` is a topological parameter of information transmission. It is not a social layer.

Group is a structure that the existing Reality-generation mechanism may read. On a representation edge, the preferences and capabilities of the group’s members may enter the aggregate and form the generated signal. That read belongs to the existing Reality → Generation path. The signal must still pass transmission and trust admission before it can be written as belief. This is not a `Group → Belief` edge, a `Group → Intent` edge, or any other new social causal edge. Organizations, factions, and institutions do not currently enter information transmission, trust admission, belief update, intent, or resource settlement.

Three formal boundaries:

1. Group is not a group mechanism. Group enters through Reality → Generation, then Transmission, Trust, and Belief, and only then Intent. That is the existing path. It is not social feedback from the group onto Belief, Intent, or Action.
2. State persistence is not feedback. Generation does not read belief, intent, action, or resource. Decision does not read resource. When this tick did not reject on trust, decision may read the belief currently stored for the observer. If this tick admitted a signal, the belief just written in this tick is what is read, and that is Belief → Intent inside one tick. If this tick did not replace the belief, intent may still be computed from the stored belief. That read does not return to Generation, so it does not create cross-tick feedback or path dependence. When parameters are constant and the signal is rewritten every tick, a long run repeats the same result.
3. An identical trajectory is not an automatic mechanism gap. An identical trajectory means the paths may be non-identifiable. If that does not block the current research question, record the boundary. If it does, review the smallest necessary new edge.

A later development proposal is asked one question: why can the current model not answer this stated research question? If that cannot be answered, development does not start. If it can, run the experiment and record the result. There is no next task. Having no next task is the correct state of this stage.

Reproducibility and a competitive moat are not the same objective. A causal laboratory succeeds when someone else can repeat the same intervention from the public specification and obtain the same causal trace and the same conclusion. Cross-implementation reproduction does not require event strings to match character for character. The 132 tests lock the regression contract of this implementation. The procedure is in the implementation correspondence section of `docs/BASELINE_EXPERIMENT_SPEC.md`. A commercial moat aims at value that others cannot readily copy. That tension is not resolved here. There is no moat, and the model is not changed in order to build one. What is maintained is a small edge set, deterministic execution, traceability, an identifiability audit, and edge-by-edge admission. The experimental record is not yet a barrier to copying. Experiments are not manufactured in order to accumulate assets. A researcher platform, a benchmark program, and a hosted service are not the route of this kernel. Agent-based modeling, counterfactual experiments, reproducibility, and causal inference are not original selling points. Originality of this combination of disciplines is not established, and a competitive barrier is not established.
