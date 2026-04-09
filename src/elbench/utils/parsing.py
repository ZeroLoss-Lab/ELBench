from __future__ import annotations

import ast
import json
import re
from difflib import SequenceMatcher
from typing import Any


def normalize_text(text: str | None) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def extract_choice_letters(text: str | None) -> list[str]:
    if not text:
        return []
    upper = str(text).upper()
    letters = re.findall(r"\b([A-Z])\b", upper)
    filtered = [letter for letter in letters if letter in {"A", "B", "C", "D", "E", "F", "G"}]
    deduped = []
    for letter in filtered:
        if letter not in deduped:
            deduped.append(letter)
    return deduped


def parse_score_value(value: Any) -> tuple[float | None, float | None]:
    if value is None:
        return None, None
    text = str(value).strip()
    if not text:
        return None, None
    if "/" in text:
        left, right = text.split("/", 1)
        try:
            score = float(left.strip())
            total = float(right.strip())
            return score, total
        except ValueError:
            return None, None
    try:
        score = float(text)
        return score, None
    except ValueError:
        return None, None


def text_similarity(left: str | None, right: str | None) -> float:
    a = normalize_text(left)
    b = normalize_text(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(a=a, b=b).ratio()


def extract_json_object(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    candidate = str(text).strip()
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, flags=re.S | re.I)
    if fenced:
        candidate = fenced[0]
    else:
        match = re.search(r"\{.*\}", candidate, flags=re.S)
        if match:
            candidate = match.group(0)
    for parser in (_try_json, _try_literal_eval):
        parsed = parser(candidate)
        if isinstance(parsed, dict):
            return parsed
    return None


def extract_required_json_keys(prompt: str) -> list[str]:
    matches = re.findall(r'["\']([^"\']{1,80})["\']', prompt)
    keys: list[str] = []
    for match in matches:
        normalized = match.strip()
        if not normalized:
            continue
        if "\n" in normalized:
            continue
        if len(normalized) > 60:
            continue
        if normalized not in keys:
            keys.append(normalized)
    return keys


def _try_json(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _try_literal_eval(text: str) -> dict[str, Any] | None:
    try:
        parsed = ast.literal_eval(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None
