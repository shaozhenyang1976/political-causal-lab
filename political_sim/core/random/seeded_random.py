"""SeededRandom. Every random draw is taken from here (specification section 55)."""

from __future__ import annotations

import random


class SeededRandom:
    """Fixed entry to CPython's random.Random.

    STREAM_VERSION identifies the algorithm of this stream. Change the version
    when the generator or the calling convention changes.
    seed accepts only int, so one experimental seed cannot take a different
    hash path because of its type.
    """

    STREAM_VERSION = "cpython-random-mt19937-v1"

    def __init__(self, seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise TypeError("seed must be an int")
        self._seed = seed
        self._rng = random.Random(seed)

    @property
    def seed(self) -> int:
        return self._seed

    def random(self) -> float:
        return self._rng.random()

    def uniform(self, low: float, high: float) -> float:
        if (
            isinstance(low, bool)
            or isinstance(high, bool)
            or not isinstance(low, (int, float))
            or not isinstance(high, (int, float))
        ):
            raise TypeError("uniform bounds must be real numbers")
        if low > high:
            raise ValueError("uniform low must be <= high")
        return self._rng.uniform(low, high)
