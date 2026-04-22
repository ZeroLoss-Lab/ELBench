from __future__ import annotations

import re

from elbench.judges.base import BaseJudge
from elbench.loaders.general_capability_loader import MMLUProJsonlLoader
from elbench.schemas.evaluation import JudgeResult, ModelResponse, Sample


class MMLUProJudge(BaseJudge):
    _loader = MMLUProJsonlLoader()

    async def judge(self, sample: Sample, response: ModelResponse) -> JudgeResult:
        expected_answer = self._loader.expected_answer_from_sample(sample)
        valid_letters = self._loader.valid_letters_from_sample(sample)
        predicted_answer = self._extract_answer(response.text, valid_letters)
        passed = predicted_answer is not None and predicted_answer == expected_answer
        return JudgeResult(
            judge_name=f"{sample.task}_exact_match",
            judge_result="pass" if passed else "fail",
            score=1.0 if passed else 0.0,
            judge_reason="Exact answer match." if passed else "Predicted answer does not match reference.",
            judge_metadata={
                "predicted_answer": predicted_answer,
                "expected_answer": expected_answer,
                "valid_letters": valid_letters,
                "subject": sample.dimension or sample.metadata.get("subject"),
            },
        )

    def _extract_answer(self, text: str | None, valid_letters: list[str]) -> str | None:
        if not text:
            return None
        valid_pattern = "".join(re.escape(letter) for letter in valid_letters)
        explicit_matches = re.findall(
            rf"(?:ANSWER|答案)\s*[：:]\s*\(?\s*([{valid_pattern}])\s*\)?",
            str(text),
            flags=re.I,
        )
        if explicit_matches:
            return explicit_matches[-1].upper()

        standalone_matches = re.findall(rf"\b([{valid_pattern}])\b", str(text), flags=re.I)
        if standalone_matches:
            return standalone_matches[-1].upper()
        return None
