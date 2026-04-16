import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from elbench.execution.basic_education import (  # noqa: E402
    aggregate_numeric_score,
    count_elmes_tasks,
    load_basic_education_config,
)


class BasicEducationBridgeTest(unittest.TestCase):
    def test_count_iter_tasks(self) -> None:
        cfg = {
            "tasks": {
                "mode": "iter",
                "content": [{"q": 1}, {"q": 2}, {"q": 3}],
            }
        }
        self.assertEqual(count_elmes_tasks(cfg), 3)

    def test_count_union_tasks(self) -> None:
        cfg = {
            "tasks": {
                "mode": "union",
                "content": {
                    "image": ["a", "b", "c"],
                    "question": ["q1", "q2", "q3", "q4", "q5"],
                },
            }
        }
        self.assertEqual(count_elmes_tasks(cfg), 15)

    def test_numeric_score_aggregation(self) -> None:
        score, details = aggregate_numeric_score(
            {
                "a": 4,
                "b": {"x": 2.0, "y": 3},
                "c": [1, {"z": 5}],
                "d": "skip",
            }
        )
        self.assertIsNotNone(score)
        self.assertAlmostEqual(score or 0, (4 + 2 + 3 + 1 + 5) / 5)
        self.assertEqual(details["a"], 4.0)
        self.assertEqual(details["b.x"], 2.0)
        self.assertEqual(details["b.y"], 3.0)
        self.assertEqual(details["c[0]"], 1.0)
        self.assertEqual(details["c[1].z"], 5.0)

    def test_basic_education_config_declares_45_tasks(self) -> None:
        config = load_basic_education_config(
            config_root=ROOT / "configs",
            project_root=ROOT,
        )
        self.assertTrue(config.enabled)
        expected = sum(
            int(s.expected_tasks or 0)
            for s in config.scenarios
            if s.enabled
        )
        self.assertEqual(expected, 45)


if __name__ == "__main__":
    unittest.main()
