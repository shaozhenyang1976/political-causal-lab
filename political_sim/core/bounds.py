"""Runtime checks stated in specification section 72.

Only ranges the specification already gives are enforced. Sampling intervals used by the generator are assumptions about initial conditions and are not promoted to model constraints here.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def as_finite_float(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def require_unit_interval(name: str, value: object) -> float:
    number = as_finite_float(name, value)
    if number < 0.0 or number > 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return number


def require_non_negative(name: str, value: object) -> float:
    number = as_finite_float(name, value)
    if number < 0.0:
        raise ValueError(f"{name} must be >= 0")
    return number


def require_non_negative_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value


def require_non_empty_str(name: str, value: object) -> str:
    if not isinstance(value, str) or value == "" or value != value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def require_id_sequence(name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence of ids")
    cleaned = tuple(
        require_non_empty_str(f"{name}[{index}]", item) for index, item in enumerate(value)
    )
    if len(cleaned) != len(set(cleaned)):
        raise ValueError(f"{name} contains duplicate ids")
    return cleaned
