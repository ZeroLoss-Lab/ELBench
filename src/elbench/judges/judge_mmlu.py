from __future__ import annotations

import re

from elbench.judges.base import BaseJudge
from elbench.schemas.evaluation import JudgeResult, ModelResponse, Sample


class MMLUProJudge(BaseJudge):
    async def judge(self, sample: Sample, response: ModelResponse) -> JudgeResult:
        expected_answer = self._expected_answer(sample)
        valid_letters = self._valid_letters(sample)
        predicted_answer = self._extract_answer(response.text, valid_letters)
        passed = predicted_answer is not None and predicted_answer == expected_answer
        return JudgeResult(
            judge_name="mmlu_pro_exact_match",
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

    def _expected_answer(self, sample: Sample) -> str | None:
        reference = sample.reference or {}
        if isinstance(reference, dict):
            value = reference.get("target")
        else:
            value = reference
        if value in (None, ""):
            return None
        normalized = str(value).strip().upper()
        return normalized[0] if normalized else None

    def _valid_letters(self, sample: Sample) -> list[str]:
        choices = sample.metadata.get("choices")
        if isinstance(choices, list) and choices:
            return [chr(65 + index) for index in range(len(choices))]
        return list("ABCDEFGHIJ")

    def _extract_answer(self, text: str | None, valid_letters: list[str]) -> str | None:
        if not text:
            return None
        valid_pattern = "".join(re.escape(letter) for letter in valid_letters)
        explicit_matches = re.findall(
            rf"ANSWER\s*:\s*\(?\s*([{valid_pattern}])\s*\)?",
            str(text),
            flags=re.I,
        )
        if explicit_matches:
            return explicit_matches[-1].upper()

        standalone_matches = re.findall(rf"\b([{valid_pattern}])\b", str(text), flags=re.I)
        if standalone_matches:
            return standalone_matches[-1].upper()
        return None
