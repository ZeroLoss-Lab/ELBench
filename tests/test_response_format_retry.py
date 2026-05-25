import asyncio
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from elbench.config import load_project_config  # noqa: E402
from elbench.execution import BenchmarkRunner, RunOptions  # noqa: E402
from elbench.execution.response_format import (  # noqa: E402
    ResponseFormatSpec,
    build_retry_followup,
    should_force_concise_retry,
)
from elbench.schemas.evaluation import ModelResponse  # noqa: E402


class ResponseFormatRetryTest(unittest.TestCase):
    def test_empty_length_response_with_reasoning_tokens_uses_concise_retry(self) -> None:
        response = ModelResponse(
            text="",
            raw_payload={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": ""},
                        "finish_reason": "length",
                    }
                ]
            },
            usage={
                "completion_tokens": 8188,
                "completion_tokens_details": {"reasoning_tokens": 7861},
            },
        )
        spec = ResponseFormatSpec(
            name="single_choice_en",
            instruction="The last line must be exactly: ANSWER: [LETTER].",
            reminder_template="unused",
            valid_letters=list("ABCD"),
            answer_prefixes=["ANSWER"],
        )

        self.assertTrue(should_force_concise_retry(response))

        followup = build_retry_followup(spec, response)
        self.assertEqual(followup["retry_reason"], "format_empty_after_reasoning")
        self.assertEqual(followup["max_tokens"], 64)
        self.assertIsNone(followup["assistant_content"])
        self.assertIn("Do not include any reasoning", followup["user_reminder"])
        self.assertIn("ANSWER: [LETTER]", followup["user_reminder"])

    def test_nonempty_response_keeps_normal_format_retry(self) -> None:
        response = ModelResponse(
            text="I think the answer is A.",
            raw_payload={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "I think the answer is A."},
                        "finish_reason": "stop",
                    }
                ]
            },
            usage={"completion_tokens": 12},
        )
        spec = ResponseFormatSpec(
            name="single_choice_en",
            instruction="The last line must be exactly: ANSWER: [LETTER].",
            reminder_template="Your previous response did not follow the required answer format.",
            valid_letters=list("ABCD"),
            answer_prefixes=["ANSWER"],
        )

        self.assertFalse(should_force_concise_retry(response))

        followup = build_retry_followup(spec, response)
        self.assertEqual(followup["retry_reason"], "format_invalid")
        self.assertEqual(followup["assistant_content"], "I think the answer is A.")
        self.assertIn("did not follow the required answer format", followup["user_reminder"])

    def test_single_choice_invalid_format_triggers_retry_and_recovers(self) -> None:
        temp_dir = ROOT / "tmp_test_artifacts" / "elbench_format_retry"
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        try:
            config = load_project_config(ROOT / "configs")
            config.app.output_root = temp_dir / "outputs"
            model = config.models["mock.default"].model_copy(deep=True)
            model.provider_kwargs["mode"] = "format_retry_probe"
            model.retry.max_attempts = 2
            config.models["mock.default"] = model

            runner = BenchmarkRunner(config)
            result = asyncio.run(
                runner.run(
                    RunOptions(
                        model_id="mock.default",
                        run_id="format-retry-probe",
                        modules={"通用模型"},
                        source_files={"mmlu_pro_sampled.jsonl"},
                        max_samples=1,
                    )
                )
            )

            output_root = temp_dir / "outputs"
            retries_path = output_root / "logs" / "format-retry-probe" / "mock.default.retries.jsonl"
            judged_path = Path(result["judged_path"])

            retries = [
                json.loads(line)
                for line in retries_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            judged = [
                json.loads(line)
                for line in judged_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertEqual(len(retries), 1)
            self.assertEqual(retries[0]["retry_reason"], "format_invalid")
            self.assertEqual(len(judged), 1)
            self.assertEqual(judged[0]["retry_count"], 1)
            self.assertEqual(judged[0]["judge_result"], "fail")
            self.assertEqual(judged[0]["model_response"], "ANSWER: A")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
