from __future__ import annotations

import re
from typing import Any, Callable

from elbench.judges.base import BaseJudge
from elbench.schemas.evaluation import JudgeResult, ModelResponse, Sample


class IFEvalJudge(BaseJudge):
    async def judge(self, sample: Sample, response: ModelResponse) -> JudgeResult:
        text = response.text or ""
        instruction_ids = self._instruction_ids(sample)
        kwargs_list = self._kwargs(sample)
        strict_results = self._evaluate_instructions(instruction_ids, kwargs_list, text, loose=False)
        loose_results = self._evaluate_instructions(instruction_ids, kwargs_list, text, loose=True)
        unsupported = [
            result["instruction_id"]
            for result in strict_results
            if result.get("unsupported")
        ]

        prompt_level_strict = self._prompt_level(strict_results)
        inst_level_strict = self._inst_level(strict_results)
        prompt_level_loose = self._prompt_level(loose_results)
        inst_level_loose = self._inst_level(loose_results)
        passed = prompt_level_strict == 1.0

        return JudgeResult(
            judge_name="ifeval_rule",
            judge_result="pass" if passed else "fail",
            score=prompt_level_strict,
            judge_reason=(
                "All instructions passed strict checks."
                if passed
                else "One or more instructions failed strict checks."
            ),
            judge_metadata={
                "prompt_level_strict": prompt_level_strict,
                "inst_level_strict": inst_level_strict,
                "prompt_level_loose": prompt_level_loose,
                "inst_level_loose": inst_level_loose,
                "instruction_id_list": instruction_ids,
                "kwargs": kwargs_list,
                "prompt_key": sample.metadata.get("key"),
                "strict_results": strict_results,
                "loose_results": loose_results,
                "unsupported_instructions": unsupported,
            },
        )

    def _evaluate_instructions(
        self,
        instruction_ids: list[str],
        kwargs_list: list[dict[str, Any]],
        response_text: str,
        *,
        loose: bool,
    ) -> list[dict[str, Any]]:
        variants = self._loose_variants(response_text) if loose else [response_text]
        results = []
        for index, instruction_id in enumerate(instruction_ids):
            kwargs = kwargs_list[index] if index < len(kwargs_list) else {}
            checker = self._checker(instruction_id)
            if checker is None:
                results.append(
                    {
                        "instruction_id": instruction_id,
                        "passed": False,
                        "unsupported": True,
                    }
                )
                continue
            passed = any(checker(variant, kwargs) for variant in variants)
            results.append(
                {
                    "instruction_id": instruction_id,
                    "passed": passed,
                    "unsupported": False,
                }
            )
        return results

    def _checker(self, instruction_id: str) -> Callable[[str, dict[str, Any]], bool] | None:
        checkers: dict[str, Callable[[str, dict[str, Any]], bool]] = {
            "punctuation:no_comma": self._check_no_comma,
            "detectable_format:number_highlighted_sections": self._check_highlighted_sections,
            "length_constraints:number_words": self._check_number_words,
            "detectable_content:number_placeholders": self._check_number_placeholders,
        }
        return checkers.get(instruction_id)

    def _check_no_comma(self, value: str, _: dict[str, Any]) -> bool:
        return re.search(r"\,", value) is None

    def _check_highlighted_sections(self, value: str, kwargs: dict[str, Any]) -> bool:
        expected = self._int_arg(kwargs.get("num_highlights"), default=1)
        num_highlights = 0
        highlights = re.findall(r"\*[^\n\*]*\*", value)
        double_highlights = re.findall(r"\*\*[^\n\*]*\*\*", value)
        for highlight in highlights:
            if highlight.strip("*").strip():
                num_highlights += 1
        for highlight in double_highlights:
            if highlight.removeprefix("**").removesuffix("**").strip():
                num_highlights += 1
        return num_highlights >= expected

    def _check_number_words(self, value: str, kwargs: dict[str, Any]) -> bool:
        expected = self._int_arg(kwargs.get("num_words"), default=0)
        relation = str(kwargs.get("relation") or "at least")
        num_words = len(re.findall(r"\w+", value))
        if relation == "less than":
            return num_words < expected
        if relation == "at least":
            return num_words >= expected
        return False

    def _check_number_placeholders(self, value: str, kwargs: dict[str, Any]) -> bool:
        expected = self._int_arg(kwargs.get("num_placeholders"), default=1)
        return len(re.findall(r"\[.*?\]", value)) >= expected

    def _loose_variants(self, value: str) -> list[str]:
        lines = value.splitlines()
        variants = [
            value,
            "\n".join(lines[1:]) if lines else "",
            "\n".join(lines[:-1]) if lines else "",
            "\n".join(lines[1:-1]) if len(lines) > 1 else "",
        ]
        variants.extend(variant.replace("*", "") for variant in list(variants))
        return variants

    def _prompt_level(self, results: list[dict[str, Any]]) -> float:
        if not results:
            return 0.0
        return 1.0 if all(bool(result.get("passed")) for result in results) else 0.0

    def _inst_level(self, results: list[dict[str, Any]]) -> float:
        if not results:
            return 0.0
        return sum(1.0 for result in results if result.get("passed")) / len(results)

    def _instruction_ids(self, sample: Sample) -> list[str]:
        value = sample.metadata.get("instruction_id_list")
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    def _kwargs(self, sample: Sample) -> list[dict[str, Any]]:
        value = sample.metadata.get("kwargs")
        if not isinstance(value, list):
            return []
        return [item if isinstance(item, dict) else {} for item in value]

    def _int_arg(self, value: Any, *, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
