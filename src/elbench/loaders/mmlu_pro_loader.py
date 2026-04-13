from __future__ import annotations

import json
import re
from typing import Any, Iterator

from elbench.loaders.base import BaseLoader
from elbench.registry import ResolvedRegistryItem
from elbench.schemas.evaluation import RawRecord, Sample


class MMLUProJsonlLoader(BaseLoader):
    def iter_raw_records(self, item: ResolvedRegistryItem) -> Iterator[RawRecord]:
        with item.path.open("r", encoding="utf-8") as handle:
            for row_index, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                yield RawRecord(
                    source_path=str(item.path),
                    source_file=item.entry.canonical_name,
                    row_index=row_index,
                    record=json.loads(line),
                )

    def iter_samples(self, item: ResolvedRegistryItem) -> Iterator[Sample]:
        for raw_record in self.iter_raw_records(item):
            record = raw_record.record
            target = self._string_or_none(record.get("target"))
            choices = self._choices(record.get("choices"))
            dimension = self._string_or_none(record.get("subset_key"))
            metadata = self._metadata(record, raw_record.row_index)
            yield Sample(
                sample_id=self._sample_id(item.entry.canonical_name, record, raw_record.row_index),
                source_file=item.entry.canonical_name,
                source_path=str(item.path),
                module=item.entry.module,
                subset=item.entry.subset,
                task=item.entry.task,
                dimension=dimension,
                prompt=self._build_zero_shot_prompt(record, choices),
                reference={"target": target},
                metadata=metadata,
                raw_record=record,
            )

    def _build_zero_shot_prompt(self, record: dict[str, Any], choices: list[str]) -> str:
        question = self._extract_question(record)
        option_lines = [f"{chr(65 + index)}) {choice}" for index, choice in enumerate(choices)]
        letters = ",".join(chr(65 + index) for index in range(len(choices)))
        return "\n".join(
            [
                "Answer the following multiple choice question.",
                "Think step by step before answering.",
                f"The last line of your response must be exactly: ANSWER: [LETTER], where [LETTER] is one of {letters}.",
                "",
                "Question:",
                question,
                "Options:",
                *option_lines,
            ]
        )

    def _extract_question(self, record: dict[str, Any]) -> str:
        input_messages = record.get("input")
        if isinstance(input_messages, list):
            for message in reversed(input_messages):
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                if not isinstance(content, str):
                    continue
                matches = re.findall(r"Question:\n(.*?)\nOptions:", content, flags=re.S)
                if matches:
                    return matches[-1].strip()
        raise ValueError("Cannot extract MMLU-Pro question from input messages.")

    def _metadata(self, record: dict[str, Any], row_index: int) -> dict[str, Any]:
        metadata = {}
        raw_metadata = record.get("metadata")
        if isinstance(raw_metadata, dict):
            metadata.update(raw_metadata)
        metadata["choices"] = self._choices(record.get("choices"))
        metadata["subset_key"] = self._string_or_none(record.get("subset_key"))
        metadata["row_index"] = row_index
        return metadata

    def _sample_id(self, canonical_name: str, record: dict[str, Any], row_index: int) -> str:
        value = record.get("id")
        if value in (None, ""):
            value = row_index
        return f"{canonical_name.replace('.', '_')}-{value}"

    def _choices(self, value: Any) -> list[str]:
        if not isinstance(value, list) or not value:
            raise ValueError("MMLU-Pro record must contain a non-empty choices list.")
        return [str(choice) for choice in value]

    def _string_or_none(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        return str(value)
