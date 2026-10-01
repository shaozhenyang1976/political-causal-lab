"""目录是否按本步边界建立。"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DIRECTORIES = (
    "political_sim/core/models",
    "political_sim/core/actions",
    "political_sim/core/random",
    "political_sim/core/events",
    "political_sim/simulation/systems",
    "political_sim/theories/base",
    "political_sim/theories/representation",
    "political_sim/theories/coalition",
    "political_sim/theories/information",
    "political_sim/experiments/configs",
    "political_sim/experiments/runners",
    "political_sim/experiments/analysis",
    "political_sim/scenarios/sandbox",
    "political_sim/scenarios/historical",
    "political_sim/output/runs",
    "political_sim/output/metrics",
    "political_sim/output/logs",
    "docs",
)


class LayoutTests(unittest.TestCase):
    def test_expected_directories_exist(self) -> None:
        missing = [path for path in EXPECTED_DIRECTORIES if not (ROOT / path).is_dir()]
        self.assertEqual(missing, [])

    def test_appendix_a_is_the_only_simulation_layout(self) -> None:
        simulation = ROOT / "political_sim" / "simulation"
        self.assertTrue((simulation / "engine.py").is_file())
        self.assertTrue((simulation / "tick_processor.py").is_file())
        self.assertTrue((ROOT / "political_sim" / "core" / "models" / "world_state.py").is_file())
        self.assertFalse((simulation / "engine").exists())
        self.assertFalse((simulation / "ticks").exists())
        self.assertFalse((ROOT / "political_sim" / "core" / "state").exists())

    def test_historical_scenarios_are_not_implemented(self) -> None:
        historical = ROOT / "political_sim" / "scenarios" / "historical"
        self.assertEqual(sorted(path.name for path in historical.iterdir()), ["__init__.py"])

    def test_core_source_has_no_stalin_scenario(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "political_sim").rglob("*.py")
        )
        self.assertNotIn("Stalin", text)


if __name__ == "__main__":
    unittest.main()
