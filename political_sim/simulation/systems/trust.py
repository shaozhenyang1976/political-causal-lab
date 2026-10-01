"""Admission threshold. It runs before DecisionContext and does not change a signal that has already been generated or received."""

from __future__ import annotations

from political_sim.core.bounds import require_unit_interval

TRUST_GATE_RULE = (
    "Trust rejection is an admission failure before DecisionContext. "
    "t >= trust_threshold admits the received signal unchanged. "
    "t < trust_threshold leaves any existing belief in place and seeks information."
)


def admits(trust: float, trust_threshold: float) -> bool:
    trust_value = require_unit_interval("trust", trust)
    threshold_value = require_unit_interval("trust_threshold", trust_threshold)
    return trust_value >= threshold_value
