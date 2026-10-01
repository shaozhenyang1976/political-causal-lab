"""核心契约。

PR-7 起，下面这些句子的既有含义冻结。
新机制只能加在它们之上。模拟器和测量层可以读取 WorldState。行动者不可以。
"""

from __future__ import annotations

CORE_CONTRACT = (
    "Reality ≠ Belief",
    "Actor cannot observe WorldState",
    "Actor only decides from permitted information",
    "Intent ≠ Action",
    "Intent does not mutate WorldState",
    "WorldState mutation → ActionResolver",
    "Accepted mutation → EventLog",
    "Multiple conflicting signals ≠ automatic averaging",
    "Multiple beliefs ≠ automatic averaging",
    "Information forwarding is explicit",
    "Hop count does not imply attenuation",
    "Constraint precedence is experimental policy",
)

INTENT_TRACE = "Every representative records one action_intent on every tick."

CORE_BASELINE_STATUS = "CORE BASELINE — FROZEN"

FROZEN_CLAUSES = (
    "Reality / Belief separation",
    "Actor information boundary",
    "DecisionContext",
    "Intent semantics",
    "Intent / Action separation",
    "State mutation boundary",
    "Event boundary",
    "Explicit forwarding",
    "No automatic hop attenuation",
    "ConstraintPolicy abstraction",
    "Generation error semantics",
    "Tick ordering",
    "Event-based measurement",
)

TRUST_STATUS = "acceptance gate"
TRUST_GATE_STATUS = "PR-8 TRUST GATE — FROZEN"
FIDELITY_STATUS = "PR-9 FIDELITY — FROZEN"
LAYER_RULES = (
    "e does not modify q, fidelity, or trust.",
    "q does not modify fidelity or trust.",
    "fidelity does not modify q or trust.",
    "trust does not modify signal or received values.",
)
ACTION_BOUNDARY_STATUS = "PR-10 ACTION BOUNDARY — FROZEN"
CONSEQUENCE_STATUS = "PR-11 CONSEQUENCE — FROZEN"
CONSERVATION_STATUS = "PR-12 RESOURCE CONSERVATION — FROZEN"
SKELETON_STATUS = "PR-1 through PR-12 form the core causal skeleton. No feedback loop is established."
STAGE_STATUS = (
    "PR-1 through PR-12 complete a one-way causal skeleton without feedback. "
    "PR-13 stays closed until a Resource causal contract is defined."
)
OPEN_LOOP_STATUS = "PR-1~PR-12: OPEN-LOOP BASELINE — FROZEN"
OPEN_LOOP_FACTS = (
    "PR-13: not started",
    "Regression baseline: 132 tests",
    "Resource: Outcome Variable Only",
    "Resource → ?: Disconnected",
    "Resource semantic: UNDECIDED",
)
RESOURCE_ADMISSION = (
    "Semantic: Resource has one decided meaning.",
    "Operational: that meaning is computable or observable, not only a concept.",
    "Justification: accepted_action_count is sufficient for that meaning.",
    "Target: it changes exactly one existing layer.",
    "Timing: the change happens in one named tick phase.",
    "Isolation: it does not change the definitions of e, q, fidelity, or trust.",
    "One-edge rule: the first change adds only one causal arrow.",
    "Counterfactual: an on/off contrast isolates the Resource effect.",
    "Regression: the 132 existing tests still pass.",
    "No hidden feedback: EventLog, DecisionContext, and ActionResolver do not create a second feedback edge.",
)
RESOURCE_ONE_EDGE_RULE = "The first causal meaning of Resource may add only one directed edge."
RESOURCE_ADR_STATUS = "UNDECIDED"
RESOURCE_ADR_QUESTIONS = (
    "What single meaning does Resource have?",
    "Why can admitted-action counts stand for that meaning?",
    "Which one existing layer does it change?",
    "Where in the tick order does that change happen?",
    "Does it create feedback, and if so through exactly one new edge?",
)
RESOURCE_DEFINITION = (
    "Resource is an abstract conserved ledger, owned by an actor and produced by admitted actions."
)
FIELD_PRESENCE_RULE = "A stored field does not gain causal meaning merely by existing."
RESOURCE_LEDGER_LIMIT = (
    "Resource counts admitted actions. It does not measure power, wealth, information, "
    "organization, or influence."
)
RESOURCE_CAUSAL_GATE = (
    "A Resource causal contract must name its meaning, why that effect exists, "
    "which existing layer it changes, where in the tick the change happens, and whether it feeds back."
)
RESOURCE_CLAUSES = (
    "A resource unit is a non-negative finite number. One admitted action adds 1.",
    "The opening ledger comes from the scenario. A missing actor starts at 0.",
    "Resource belongs to the admitted action's actor, not to the action target.",
    "+1 counts one admitted action. support and oppose add the same unit.",
    "The current rule does not decrease, transfer, or decay resource across ticks.",
    "Only ActionResolver changes resource at runtime, and only in action_consequence.",
    "Resource does not enter action, decision, information, preference, or trust.",
    "Resource has no causal layer yet, so it connects to no existing mechanism.",
)
TRUST_REJECTION_CLAUSES = (
    "trust rejection ≠ belief error",
    "trust rejection ≠ constraint delay",
    "trust rejection ≠ no information",
)
TRUST_INVARIANTS = (
    "Trust does not change signal_generated.",
    "Trust does not change received.",
    "t >= trust_threshold reproduces the baseline.",
    "t < trust_threshold does not overwrite an existing belief.",
    "trust_rejected is not part of belief_gap.",
    "trust_rejected is not constraint:delay or no_belief.",
)
