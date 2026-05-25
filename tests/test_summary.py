import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from elbench.summary import build_summary  # noqa: E402


class SummaryAggregationTest(unittest.TestCase):
    def test_failures_are_active_only_after_successful_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            judged_path = root / "judged.jsonl"
            failures_path = root / "failures.jsonl"

            judged_path.write_text(
                json.dumps(
                    {
                        "sample_id": "sample-a",
                        "source_file": "example.jsonl",
                        "module": "module",
                        "task": "task",
                        "subset": "subset",
                        "dimension": "default",
                        "judge_result": "pass",
                        "score": 1,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            failures_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "sample_id": "sample-a",
                                "source_file": "example.jsonl",
                                "error_type": "ReadTimeout",
                            }
                        ),
                        json.dumps(
                            {
                                "sample_id": "sample-b",
                                "source_file": "example.jsonl",
                                "error_type": "ResponseFormatError",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_summary(judged_path, failures_path)

            self.assertEqual(summary["total_judged"], 1)
            self.assertEqual(summary["total_failures"], 1)
            self.assertEqual(summary["failure_examples"][0]["sample_id"], "sample-b")


if __name__ == "__main__":
    unittest.main()
