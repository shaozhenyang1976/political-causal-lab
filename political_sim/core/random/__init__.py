"""Seeded randomness. The global random module must not be used inside a simulation."""

from political_sim.core.random.seeded_random import SeededRandom

__all__ = ["SeededRandom"]
