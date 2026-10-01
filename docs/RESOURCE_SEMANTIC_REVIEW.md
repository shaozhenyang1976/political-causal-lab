# Resource Semantic Review

Status: **RESOURCE SEMANTIC REVIEW — FROZEN**

The baseline remains **PR-1~PR-12: OPEN-LOOP BASELINE — FROZEN**. The engine is unchanged, production code is unchanged, the suite remains 132 / 132, and PR-13 has not started. The five questions in `docs/RESOURCE_SEMANTIC_ADR.md` remain **UNDECIDED**. `Resource → ?` stays disconnected.

## 1. Current definition

`Resource` is a ledger stock, not the action count itself.

```text
ending Resource(actor) = initial_resource(actor) + accepted_action_count(actor)
```

- `initial_resource` is written by the scenario. An actor absent from the ledger is treated as 0 when an entry is opened.
- `accepted_action_count` is the number of actions by that actor that were explicitly submitted, passed reference checks, and had type `support` or `oppose`. Each such admission adds 1 to the ledger.
- `oppose` and `support` add the same amount. The action target does not receive that 1.
- A rejected action and a missing submission add 0.
- Intent may differ from the submitted action. The ledger records the admitted submission, not the intent.
- At runtime only `ActionResolver` performs this +1, and only inside `action_consequence`. It does not change preferences, beliefs, information, `fidelity`, or `trust`.

`accepted_action_count` is therefore a count of behavioral events. `Resource` is a ledger variable that also carries an opening stock. The two must not be collapsed into one meaning. `Resource = 20` does not mean twenty admitted actions unless the opening stock is 0.

## 2. Candidates and conclusions

| Candidate meaning | Current conclusion |
| --- | --- |
| Pure outcome indicator | Passes |
| Action capacity / action capital | Rejected |
| Organizational mobilization resource | Rejected |
| Political-influence proxy | Rejected |
| Material resource | Rejected |
| Information-access resource | Rejected |

“Passes” means only this: under the operational definition already frozen, a pure outcome indicator is the only reading that needs no extra assumption and agrees with the existing causal structure. It is not a decision that Resource can never be anything but an outcome variable.

The other five readings re-enter the candidate set only with a new operational definition or a new mechanistic basis. Renaming the existing +1 is not enough.

## 3. Reasons for rejection

**Action capacity / action capital.** The count is a product of admission. Admission does not read the balance, so the number does not state a capacity to act further. Treating the product as the capacity that produced it still lacks a separate mechanistic basis.

**Organizational mobilization.** The +1 is booked to the submitter. It does not change organizational membership, cohesion, or the organization’s own resource pool.

**Political-influence proxy.** Influence, if it were real, would appear in someone else’s belief, intent, or action. This increment changes none of those quantities and does not distinguish `support` from `oppose`.

**Material resource.** The existing +1 has no consumption, transfer, price, or scarcity. An opening stock may be written separately by the scenario. That does not turn the action count into a material stock.

**Information-access resource.** The information path is determined only by `e`, `q`, `fidelity`, and `trust`. The action count does not enter that path.

A difference in stocks, for example 2 versus 20, also does not imply who receives more information, who is trusted more readily, who can act again more easily, who influences others more, or who has greater organizational capacity.

## 4. Why the pure outcome indicator closes

The increment is defined as the number of admitted actions. Reading it as “how many actions by this actor were admitted” requires no further assumption about capacity, organization, influence, material stocks, or information. It has no target layer, no extra tick position, and no feedback. That agrees with the frozen one-way chain:

```text
Explicit Action → ActionResolver → Consequence → Resource
```

`Resource → ?` remains disconnected.

## 5. What this review did not do

- It created no new causal arrow.
- It did not fill in a Resource causal contract.
- The five-question ADR remains `UNDECIDED`.
- The 132 tests remain the regression base of the open-loop skeleton.
- Production code was left unchanged.

## 6. Observation rule after the freeze

The meaning of `accepted_action_count` is fixed: for a given `actor_id`, the number of explicitly submitted, reference-valid actions of type `support` or `oppose` that were admitted. It does not need to be reinterpreted as something else.

`Resource` currently has only a ledger meaning: `initial_resource + accepted_action_count`. It is an outcome variable. That fact does not imply capacity, power, influence, an organizational resource, or an information resource.

An independent mechanism must first have its own operational need. Only then is Resource checked to see whether it happens to meet that need. Resource is never assigned a purpose for which a mechanism is then invented.

A mechanism unrelated to Resource may proceed only if both of the following hold:

```text
New Mechanism ──X──→ Resource
New Mechanism ──X──→ reads Resource
```

The existing boundaries of `e`, `q`, `fidelity`, and `trust` remain. So do `Intent ≠ Action ≠ Consequence`, the separate origins of `accepted_action_count` and `initial_resource`, the 132 tests as the regression base, and the exclusion of Resource from every current decision, information, and transmission mechanism.

`docs/RESOURCE_SEMANTIC_ADR.md` is reopened only when a new mechanism has first stated its own operational need and the existing ledger is then found to meet that definition exactly. The causal contract and the control experiment are written from scratch. Until then there is no PR-13 and no pending Resource feature.

## 7. Hard constraint on later development

Define the semantics, then the causal edge, then the control experiment, and only then implement. Resource has left the current development line.

Any new independent mechanism is checked on four points:

1. What is its own operational definition?
2. Which existing variables does it read or change?
3. Does it accidentally cross an existing causal boundary?
4. Does it stand without reading Resource?

If point 4 holds, the mechanism continues independently, one edge at a time, on the invariant base of the existing 132 tests. If point 4 does not hold, the Resource ADR is reopened. The next search is for an independent, falsifiable, separately measurable mechanism, not for a use to assign to Resource.
