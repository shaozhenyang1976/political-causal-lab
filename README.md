# Deterministic Causal Laboratory

A deterministic causal laboratory for controlled social experiments.

This repository publishes an auditable research prototype. It is not a social-simulation platform, and it is not a completed artificial society. A small set of explicit causal edges runs inside a fixed tick order and writes a complete event log. The log is used to test whether one intervention changes belief, intent, an explicitly submitted action, or resource.

There is no feature roadmap. A question that the current model can answer is recorded as a result. A question that it cannot answer is not, by itself, a reason to add a mechanism.

## What actually runs

The frozen open-loop baseline is PR-1 through PR-12. One hundred thirty-two tests lock this Python implementation. Experiments 1 through 4 are closed.

The automatic chain ends at intent. An action occurs only when it is submitted explicitly. An admitted `support` or `oppose` adds one resource unit to its actor. Resource is not read by generation, transmission, belief, or intent.

The operative documents are:

- `docs/BASELINE_EXPERIMENT_SPEC.md` — parameters, tick slots, read and write sets, and the reproduction procedure
- `docs/EXPERIMENT_BOUNDARY.md` — experimental results, causal boundaries, identifiability boundaries, and the admission rule
- `docs/NEXT_MECHANISM_AUDIT.md` — candidate edges that have not been admitted. Listing an edge does not schedule it
- `docs/RESOURCE_SEMANTICS.md` — resource as a ledger of admitted actions

## The design specification is not the running model

`POLITICAL_SIMULATION_MODEL_SPEC_V0.2.md` is a design document. Coalitions, institutions, power, interfaces, replaceable theories, and player-facing experiments described there have no execution body. Empty tick slots remain in the code as empty functions. Organization, faction, and institution objects may appear in a scenario. Information transmission, admission, belief update, intent, and resource settlement do not read them.

The PR labels in Appendix B of that specification are the original design sequence. They are not the implemented PR-1 through PR-12 freeze.

## Running the tests

There are no third-party dependencies. The suite passed on Python 3.14.3. `pyproject.toml` requires Python 3.11 or newer.

```text
python -m unittest discover -s tests -t .
```

## Two standards of reproduction

Research reproduction aligns the intervention, the causal trace, and the conclusion. Event strings need not match character for character.

Engineering regression is the 132 tests. They lock the event, field, and string contract of this Python implementation.

## License

MIT. See `LICENSE`.
