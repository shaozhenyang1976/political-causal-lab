# Resource Contract

Status: **PR-12 RESOURCE CONSERVATION — FROZEN**

The information–cognition–action chain closes at “an action produces resource.” No resource-feedback loop has been formed.

`Resource` is currently a terminal variable. Its change is fully accounted for by admitted actions:

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

Until clause 8 is rewritten, resource is not connected to action availability, decision, information, trust, preference, or any other part of world state.

## Current skeleton

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

`Intent ≠ Action ≠ Consequence`. `Action → Resource` is one-directional. `Resource → ?` is deliberately disconnected.

Resource is an abstract conserved ledger, owned by an actor and produced by admitted actions.

It is not power, wealth, or political influence. The only operational definition is `accepted action → +1`.

A stored field does not gain causal meaning merely by existing.

`RepresentationEdge.trust`, `RepresentationEdge.fidelity`, and this resource ledger may therefore be stored without entering the causal model merely because the fields exist.

## Stage status

PR-1 through PR-12 complete a one-way causal skeleton without feedback. PR-13 stays closed until a Resource causal contract is defined.

PR-13 is not started until Resource's causal meaning is defined independently.

Three frozen regions:

1. `e`, `q`, `fidelity`, and `trust` act only on generation, the first hop, later forwarding, and admission.
2. `Intent ≠ Action ≠ Consequence`.
3. Resource counts admitted actions. It does not measure power, wealth, information, organization, or influence.

`Resource → ?` remains disconnected. Before the next mechanism is opened, a Resource causal contract must name what it represents, why it has that effect, which existing layer it changes, where in the tick the change occurs, and whether it feeds back. Tests come after that contract.

A Resource causal contract must name its meaning, why that effect exists, which existing layer it changes, where in the tick the change happens, and whether it feeds back.

The current 132 tests are the regression base of this open-loop skeleton. The official name is **PR-1~PR-12: OPEN-LOOP BASELINE — FROZEN**.

- PR-13: not started
- Regression baseline: 132 tests
- Resource: Outcome Variable Only
- Resource → ?: Disconnected
- Resource semantic: UNDECIDED

PR-13 may enter implementation only when the Resource Causal Admission Test is satisfied in full:

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

A control experiment must show that the expected change occurs only when the single edge `Resource → X` is changed, and that the other existing variables stay unchanged. If the ten conditions are not met, PR-13 is not started.

The first causal meaning of Resource may add only one directed edge.

The semantic choice is recorded first in `docs/RESOURCE_SEMANTIC_ADR.md`. All five answers are currently UNDECIDED. The causal contract and any engine change come after one operational definition.

None of the following resource interpretations has been selected, and none enters the engine:

- action capacity
- information access
- organizational mobilization
- material or economic resources
- a pure experimental observable
