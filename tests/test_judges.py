import asyncio
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from elbench.judges.judge_highlevel import HighLevelJudge
from elbench.judges.judge_mmlu import MMLUProJudge
from elbench.judges.judge_teaching_harm import TeachingHarmJudge
from elbench.judges.llm_judge import LLMJudge
from elbench.judges.router import JudgeRouter
from elbench.config import load_project_config
from elbench.schemas.config import JudgeTaskConfig
from elbench.schemas.evaluation import ModelResponse, Sample


class JudgeSmokeTest(unittest.TestCase):
    def test_llm_judge_returns_structured_result(self) -> None:
        config = load_project_config(Path("configs"))
        judge = LLMJudge(
            config,
            JudgeTaskConfig(mode="llm", template="highlevel_edu", judge_model_id="mock.judge"),
        )
        sample = Sample(
            sample_id="l1",
            source_file="高阶育人-edu.jsonl",
            source_path="高阶育人-edu.jsonl",
            module="高阶育人",
            subset="edu",
            task="highlevel_edu",
            prompt='Please provide "Score", "Scoring Details", and "Personalized Feedback" in JSON format.',
            metadata={"_scene": "AG"},
        )
        response = ModelResponse(text='{"Score": "4/5", "Scoring Details": "ok", "Personalized Feedback": "ok"}')
        result = asyncio.run(judge.judge(sample, response))
        self.assertEqual(result.judge_result, "pass")
        self.assertEqual(result.score, 1.0)

    def test_router_uses_llm_judge_for_subjective_tasks(self) -> None:
        config = load_project_config(Path("configs"))
        router = JudgeRouter(config)
        sample = Sample(
            sample_id="r1",
            source_file="安全拒答.jsonl",
            source_path="安全拒答.jsonl",
            module="安全可信",
            subset="通用-应拒答",
            task="safety_refusal",
            prompt="dummy",
        )
        judge = router.get_judge(sample)
        self.assertIsInstance(judge, LLMJudge)

    def test_satas_exact_match(self) -> None:
        judge = TeachingHarmJudge()
        sample = Sample(
            sample_id="s1",
            source_file="SATAs.xlsx",
            source_path="SATAs.xlsx",
            module="安全可信",
            subset="教育-教学安全",
            task="teaching_harm",
            prompt="dummy",
            reference={"Answer": "A,B,E"},
        )
        response = ModelResponse(text="A, B, E")
        result = asyncio.run(judge.judge(sample, response))
        self.assertEqual(result.judge_result, "pass")
        self.assertEqual(result.score, 1.0)

    def test_highlevel_omni_exact_match(self) -> None:
        judge = HighLevelJudge()
        sample = Sample(
            sample_id="o1",
            source_file="高阶育人-omni.jsonl",
            source_path="高阶育人-omni.jsonl",
            module="高阶育人",
            subset="omni",
            task="highlevel_omni",
            prompt="dummy",
            reference={"answer": "C", "reasonableness": 1},
        )
        response = ModelResponse(text="C")
        result = asyncio.run(judge.judge(sample, response))
        self.assertEqual(result.judge_result, "pass")
        self.assertEqual(result.score, 1.0)

    def test_highlevel_edu_ag_json_scoring(self) -> None:
        judge = HighLevelJudge()
        sample = Sample(
            sample_id="ag1",
            source_file="高阶育人-edu.jsonl",
            source_path="高阶育人-edu.jsonl",
            module="高阶育人",
            subset="edu",
            task="highlevel_edu",
            prompt='Please provide "Score", "Scoring Details", and "Personalized Feedback" in JSON format.',
            reference={
                "Score": "4/5",
                "Scoring Details": "The answer is mostly correct but could be more specific.",
                "Personalized Feedback": "Good work. Add one concrete example next time.",
            },
            metadata={"_scene": "AG"},
        )
        response = ModelResponse(
            text='{"Score": "4/5", "Scoring Details": "The answer is mostly correct but could be more specific.", "Personalized Feedback": "Good work. Add one concrete example next time."}'
        )
        result = asyncio.run(judge.judge(sample, response))
        self.assertEqual(result.judge_result, "pass")
        self.assertGreaterEqual(result.score or 0, 0.99)

    def test_mmlu_pro_explicit_answer_match(self) -> None:
        judge = MMLUProJudge()
        sample = self._mmlu_sample("D")
        response = ModelResponse(text="After considering the options, ANSWER: D")
        result = asyncio.run(judge.judge(sample, response))
        self.assertEqual(result.judge_result, "pass")
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.judge_metadata["predicted_answer"], "D")

    def test_mmlu_pro_uses_last_explicit_answer(self) -> None:
        judge = MMLUProJudge()
        sample = self._mmlu_sample("B")
        response = ModelResponse(text="A seems tempting at first.\nBut the final line is ANSWER: B")
        result = asyncio.run(judge.judge(sample, response))
        self.assertEqual(result.judge_result, "pass")
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.judge_metadata["predicted_answer"], "B")

    def test_mmlu_pro_wrong_answer_fails(self) -> None:
        judge = MMLUProJudge()
        sample = self._mmlu_sample("D")
        response = ModelResponse(text="ANSWER: E")
        result = asyncio.run(judge.judge(sample, response))
        self.assertEqual(result.judge_result, "fail")
        self.assertEqual(result.score, 0.0)

    def test_mmlu_pro_supports_j_option(self) -> None:
        judge = MMLUProJudge()
        sample = self._mmlu_sample("J")
        response = ModelResponse(text="The correct choice is J.")
        result = asyncio.run(judge.judge(sample, response))
        self.assertEqual(result.judge_result, "pass")
        self.assertEqual(result.score, 1.0)

    def _mmlu_sample(self, target: str) -> Sample:
        return Sample(
            sample_id="mmlu1",
            source_file="mmlu_pro_sampled.jsonl",
            source_path="mmlu_pro_sampled.jsonl",
            module="通用模型",
            subset="mmlu_pro",
            task="mmlu_pro",
            dimension="law",
            prompt="dummy",
            reference={"target": target},
            metadata={"choices": [f"choice {letter}" for letter in "ABCDEFGHIJ"]},
        )


if __name__ == "__main__":
    unittest.main()
