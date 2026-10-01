"""Reproducibility of SeededRandom and its isolation from the global random module."""

from __future__ import annotations

import random
import unittest
from pathlib import Path

from political_sim.core.random import SeededRandom

ROOT = Path(__file__).resolve().parents[1]


class SeededRandomTests(unittest.TestCase):
    def test_same_seed_replays_the_same_stream(self) -> None:
        first = SeededRandom(42)
        second = SeededRandom(42)
        first_draws = [(first.random(), first.uniform(0.0, 1.0)) for _ in range(50)]
        second_draws = [(second.random(), second.uniform(0.0, 1.0)) for _ in range(50)]
        self.assertEqual(first_draws, second_draws)
        self.assertEqual(first.seed, 42)
        self.assertEqual(SeededRandom.STREAM_VERSION, "cpython-random-mt19937-v1")

    def test_different_seeds_diverge(self) -> None:
        left = [SeededRandom(1).random() for _ in range(20)]
        right = [SeededRandom(2).random() for _ in range(20)]
        self.assertNotEqual(left, right)

    def test_negative_seed_is_stable(self) -> None:
        self.assertEqual(SeededRandom(-7).random(), SeededRandom(-7).random())

    def test_seed_must_be_an_int(self) -> None:
        with self.assertRaises(TypeError):
            SeededRandom(True)
        with self.assertRaises(TypeError):
            SeededRandom(1.0)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            SeededRandom("1")  # type: ignore[arg-type]

    def test_uniform_bounds(self) -> None:
        rng = SeededRandom(0)
        for _ in range(200):
            value = rng.uniform(-2, 3)
            self.assertGreaterEqual(value, -2)
            self.assertLess(value, 3)
        with self.assertRaises(ValueError):
            rng.uniform(1, 0)
        with self.assertRaises(TypeError):
            rng.uniform(True, 1)

    def test_draws_do_not_use_or_change_global_random(self) -> None:
        random.seed(1234)
        before = random.getstate()

        def fail_if_called() -> float:
            raise AssertionError("global random was used")

        original = random.random
        random.random = fail_if_called
        try:
            rng = SeededRandom(5)
            for _ in range(10):
                rng.random()
                rng.uniform(0, 1)
        finally:
            random.random = original
        self.assertEqual(random.getstate(), before)

    def test_model_and_scenario_modules_do_not_import_random(self) -> None:
        roots = (
            ROOT / "political_sim" / "core" / "models",
            ROOT / "political_sim" / "core" / "actions",
            ROOT / "political_sim" / "core" / "events",
            ROOT / "political_sim" / "scenarios",
            ROOT / "political_sim" / "simulation",
        )
        for root in roots:
            for path in root.rglob("*.py"):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("import random", text, path)
                self.assertNotIn("from random", text, path)


if __name__ == "__main__":
    unittest.main()
