from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def _group_key(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    return " | ".join(str(record.get(key)) for key in keys)


def build_summary(judged_path: Path, failures_path: Path) -> dict[str, Any]:
    judged_records = _load_jsonl(judged_path)
    failure_records = _active_failures(
        failures=_load_jsonl(failures_path),
        judged=judged_records,
    )
    scene_records = []
    for record in judged_records:
        metadata = record.get("metadata")
        if isinstance(metadata, dict) and metadata.get("_scene"):
            scene_record = dict(record)
            scene_record["scene"] = metadata["_scene"]
            scene_records.append(scene_record)

    def summarize(records: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, Any]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            grouped[_group_key(record, keys)].append(record)
        output = {}
        for group_key, group_records in grouped.items():
            scores = [record.get("score") for record in group_records if record.get("score") is not None]
            judge_counts: dict[str, int] = defaultdict(int)
            for record in group_records:
                judge_counts[str(record.get("judge_result"))] += 1
            pass_count = sum(1 for record in group_records if str(record.get("judge_result")) in {"pass", "safe", "guide", "answer"})
            output[group_key] = {
                "count": len(group_records),
                "avg_score": (sum(scores) / len(scores)) if scores else None,
                "pass_rate": (pass_count / len(group_records)) if group_records else None,
                "judge_result_distribution": dict(judge_counts),
            }
        return output

    return {
        "total_judged": len(judged_records),
        "total_failures": len(failure_records),
        "by_source_file": summarize(judged_records, ("source_file",)),
        "by_module": summarize(judged_records, ("module",)),
        "by_task": summarize(judged_records, ("task",)),
        "by_subset": summarize(judged_records, ("module", "subset")),
        "by_dimension": summarize(judged_records, ("dimension",)),
        "by_scene": summarize(scene_records, ("scene",)),
        "failure_examples": failure_records[:20],
    }


def _active_failures(
    *,
    failures: list[dict[str, Any]],
    judged: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    successful_keys = {_record_key(record) for record in judged}
    active: dict[tuple[str, str], dict[str, Any]] = {}
    for failure in failures:
        key = _record_key(failure)
        if key in successful_keys:
            active.pop(key, None)
            continue
        active[key] = failure
    return list(active.values())


def _record_key(record: dict[str, Any]) -> tuple[str, str]:
    return (str(record.get("source_file") or ""), str(record.get("sample_id") or ""))
