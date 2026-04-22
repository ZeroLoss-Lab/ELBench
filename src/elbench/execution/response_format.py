from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from elbench.schemas.evaluation import ModelResponse, Sample
from elbench.utils import extract_single_choice_answer


class ResponseFormatError(ValueError):
    def __init__(self, message: str, *, metadata: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.metadata = metadata or {}


@dataclass(slots=True)
class ResponseFormatSpec:
    name: str
    instruction: str
    reminder_template: str
    valid_letters: list[str] = field(default_factory=list)
    answer_prefixes: list[str] = field(default_factory=list)
    require_last_line_exact: bool = True

    def validate(self, response_text: str | None) -> dict[str, Any]:
        text = (response_text or "").strip()
        if not text:
            raise ResponseFormatError(
                "Model response is empty.",
                metadata={"format_name": self.name, "expected_format": self.instruction},
            )
        answer = self._extract_answer(text)
        if answer is None:
            raise ResponseFormatError(
                "Model response does not follow the required answer format.",
                metadata={
                    "format_name": self.name,
                    "expected_format": self.instruction,
                    "response_preview": text[:200],
                },
            )
        return {
            "format_name": self.name,
            "expected_format": self.instruction,
            "parsed_answer": answer,
        }

    def _extract_answer(self, text: str) -> str | None:
        if not self.require_last_line_exact:
            return None
        return extract_single_choice_answer(
            text,
            self.valid_letters,
            answer_prefixes=self.answer_prefixes,
        )

    def build_reminder(self, response_text: str | None) -> str:
        preview = (response_text or "").strip()
        preview = re.sub(r"\s+", " ", preview)[:200]
        return self.reminder_template.format(
            expected_format=self.instruction,
            response_preview=preview,
        ).strip()


def get_response_format_spec(sample: Sample) -> ResponseFormatSpec | None:
    if sample.task == "mmlu_pro":
        return ResponseFormatSpec(
            name="single_choice_en",
            instruction="The last line must be exactly: ANSWER: [LETTER], where [LETTER] is a valid option letter.",
            reminder_template=(
                "Your previous response did not follow the required answer format. "
                "Reply again. The last line must be exactly: ANSWER: [LETTER]."
            ),
            valid_letters=_choice_letters_from_sample(sample),
            answer_prefixes=["ANSWER", "FINAL ANSWER"],
        )
    if sample.task == "ceval":
        return ResponseFormatSpec(
            name="single_choice_cn",
            instruction="最后一行必须严格是：答案：[LETTER]，其中 [LETTER] 是合法选项字母。",
            reminder_template=(
                "你上一轮回复没有遵守规定格式。请重新回答，最后一行必须严格是：答案：[LETTER]。"
            ),
            valid_letters=_choice_letters_from_sample(sample),
            answer_prefixes=["答案", "最终答案", "ANSWER"],
        )
    if sample.task == "highlevel_omni":
        return ResponseFormatSpec(
            name="single_choice_omni",
            instruction="最后一行必须严格是：答案：[LETTER]，其中 [LETTER] 是合法选项字母。",
            reminder_template=(
                "你上一轮回复没有遵守规定格式。请重新回答，最后一行必须严格是：答案：[LETTER]。"
            ),
            valid_letters=list("ABCD"),
            answer_prefixes=["答案", "最终答案", "ANSWER"],
        )
    return None


def augment_prompt_for_format(sample: Sample, prompt: str) -> str:
    spec = get_response_format_spec(sample)
    if spec is None:
        return prompt
    if spec.instruction in prompt:
        return prompt
    if sample.task == "mmlu_pro" and "ANSWER: [LETTER]" in prompt:
        return prompt
    if sample.task == "ceval" and "答案：[LETTER]" in prompt:
        return prompt
    return f"{prompt.rstrip()}\n\n[Answer Format]\n{spec.instruction}"


def attach_format_metadata(response: ModelResponse, spec: ResponseFormatSpec | None) -> ModelResponse:
    if spec is None:
        response.format_valid = None
        return response
    metadata = spec.validate(response.text)
    response.format_valid = True
    response.format_metadata = metadata
    return response


def _choice_letters_from_sample(sample: Sample) -> list[str]:
    choices = sample.metadata.get("choices")
    if isinstance(choices, list) and choices:
        return [chr(65 + index) for index in range(len(choices))]
    return list("ABCDEFGHIJ")
