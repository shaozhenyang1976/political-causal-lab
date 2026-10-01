"""带种子的随机数。禁止在模拟中使用全局 random。"""

from political_sim.core.random.seeded_random import SeededRandom

__all__ = ["SeededRandom"]
