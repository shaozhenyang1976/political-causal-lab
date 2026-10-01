"""SeededRandom。所有随机数都从这里取出（规范第 55 节）。"""

from __future__ import annotations

import random


class SeededRandom:
    """CPython random.Random 的固定入口。

    STREAM_VERSION 标识这条随机流的算法。更换生成器或调用约定时要改版本号。
    seed 只接受 int，避免同一实验种子因类型不同而走不同的哈希。
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
