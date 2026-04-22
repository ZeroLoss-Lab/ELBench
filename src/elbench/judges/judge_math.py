from __future__ import annotations

import math
import re
from fractions import Fraction
from typing import Any

from elbench.judges.base import BaseJudge
from elbench.schemas.evaluation import JudgeResult, ModelResponse, Sample

try:
    from latex2sympy2_extended import latex2sympy
    from sympy import N, simplify
    from sympy.parsing.latex import parse_latex
    from sympy.parsing.sympy_parser import parse_expr
except Exception:
    latex2sympy = None
    N = None
    simplify = None
    parse_latex = None
    parse_expr = None


class Math500Judge(BaseJudge):
    async def judge(self, sample: Sample, response: ModelResponse) -> JudgeResult:
        expected_answer = self._expected_answer(sample)
        predicted_answer = self.extract_answer(response.text or "")
        normalized_prediction = self.strip_answer_string(predicted_answer)
        normalized_expected = self.strip_answer_string(expected_answer)
        passed = self.math_equal(normalized_prediction, normalized_expected)
        return JudgeResult(
            judge_name="math_500_acc",
            judge_result="pass" if passed else "fail",
            score=1.0 if passed else 0.0,
            judge_reason="Math answer matched reference." if passed else "Math answer did not match reference.",
            judge_metadata={
                "predicted_answer": predicted_answer,
                "expected_answer": expected_answer,
                "normalized_prediction": normalized_prediction,
                "normalized_expected": normalized_expected,
                "question_id": sample.metadata.get("question_id"),
                "level": sample.dimension or sample.metadata.get("subset_key"),
            },
        )

    def extract_answer(self, prediction: str, use_last_number: bool = True) -> str:
        pred_str = str(prediction).replace("\u043a\u0438", "")
        if "final answer is $" in pred_str and "$. I hope" in pred_str:
            pred = pred_str.split("final answer is $", 1)[1].split("$. I hope", 1)[0].strip()
        elif "boxed" in pred_str:
            pred = self._extract_boxed(pred_str)
        elif "he answer is" in pred_str:
            pred = pred_str.split("he answer is")[-1].strip()
        elif "final answer is" in pred_str:
            pred = pred_str.split("final answer is")[-1].strip()
        elif "答案是" in pred_str:
            pred = pred_str.split("答案是", 1)[1].strip().split("\n\n", 1)[0].strip()
        elif "ANSWER:" in pred_str:
            pred = pred_str.split("ANSWER:")[-1].strip()
        elif use_last_number:
            matches = re.findall(r"-?\d*\.?\d+", pred_str.replace(",", ""))
            pred = matches[-1] if matches else ""
        else:
            pred = ""

        pred = re.sub(r"\n\s*", "", pred)
        pred = pred.lstrip(":").rstrip(".").rstrip("/")
        return self.strip_answer_string(pred)

    def strip_answer_string(self, value: Any) -> str:
        string = str(value or "").strip().replace("\n", "").rstrip(".")
        string = string.replace("\\!", "")
        string = re.sub(r"\\begin\{array\}\{.*?\}", r"\\begin{pmatrix}", string)
        string = re.sub(r"\\end\{array\}", r"\\end{pmatrix}", string)
        string = string.replace("bmatrix", "pmatrix")
        string = string.replace("tfrac", "frac").replace("dfrac", "frac")
        string = string.replace("\\neq", "\\ne").replace("\\leq", "\\le").replace("\\geq", "\\ge")
        string = string.replace("\\left", "").replace("\\right", "")
        string = string.replace("\\{", "{").replace("\\}", "}")
        string = re.sub(r"\\text\{(.*?)\}", r"\1", string)
        string = re.sub(r"\\mbox\{.*?\}", "", string)
        string = string.replace("^{\\circ}", "").replace("^\\circ", "")
        string = string.replace("\\$", "").replace("$", "")
        string = string.replace("\\(", "").replace("\\)", "")
        string = string.replace("\\%", "").replace("\\%", "").replace("%", "")
        string = string.replace("\\emptyset", "{}")
        string = string.replace("infinity", "\\infty").replace("+\\inity", "\\infty")
        if "\\infty" not in string:
            string = string.replace("inf", "\\infty")
        for key in ["x=", "y=", "z=", "x\\in", "y\\in", "z\\in", "x\\to", "y\\to", "z\\to"]:
            string = string.replace(key, "")
        string = string.replace("and", "").replace("\\mathbf", "")
        string = re.sub(r"(\d+)\.0*([^\d])", r"\1\2", string)
        string = re.sub(r"(\d+)\.0*$", r"\1", string)
        if string.startswith("."):
            string = "0" + string
        if len(string.split("=")) == 2 and len(string.split("=")[0]) <= 2:
            string = string.split("=")[1]
        string = self._fix_sqrt(string)
        string = string.replace(" ", "")
        string = self._fix_fracs(string)
        string = self._fix_a_slash_b(string)
        string = re.sub(r"\\(?=\-?\d+(\\|\)|,|\]|$))", "", string)
        string = re.sub(r"thgrade$", "", string)
        if re.fullmatch(r"\s*-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\s*", string):
            string = string.replace(",", "")
        if re.fullmatch(r"(\s*-?\d+\s*,)*\s*-?\d+\s*", string):
            try:
                string = ",".join(str(item) for item in sorted(map(int, string.split(","))))
            except ValueError:
                pass
        return string

    def math_equal(self, prediction: str, reference: str) -> bool:
        if prediction is None or reference is None:
            return False
        pred = str(prediction).strip()
        ref = str(reference).strip()
        if pred.lower() == ref.lower():
            return True
        pred_number = self._parse_number(pred)
        ref_number = self._parse_number(ref)
        if pred_number is not None and ref_number is not None:
            return math.isclose(pred_number, ref_number, rel_tol=1e-4, abs_tol=1e-8)
        pred_compact = self._strip_wrappers(pred).lower()
        ref_compact = self._strip_wrappers(ref).lower()
        if pred_compact == ref_compact:
            return True
        pred_parts = self._split_tuple(pred)
        ref_parts = self._split_tuple(ref)
        if pred_parts is not None and ref_parts is not None and len(pred_parts) == len(ref_parts):
            return all(self.math_equal(left, right) for left, right in zip(pred_parts, ref_parts))
        if self._symbolic_equal(pred, ref):
            return True
        return False

    def _expected_answer(self, sample: Sample) -> str:
        reference = sample.reference or {}
        if isinstance(reference, dict):
            value = reference.get("target")
        else:
            value = reference
        return "" if value in (None, "") else str(value)

    def _extract_boxed(self, value: str) -> str:
        ans = value.split("boxed")[-1]
        if not ans:
            return ""
        if ans[0] == "{":
            stack = 1
            collected = ""
            for char in ans[1:]:
                if char == "{":
                    stack += 1
                    collected += char
                elif char == "}":
                    stack -= 1
                    if stack == 0:
                        break
                    collected += char
                else:
                    collected += char
            return collected
        return ans.split("$", 1)[0].strip()

    def _fix_fracs(self, value: str) -> str:
        parts = value.split("\\frac")
        if len(parts) == 1:
            return value
        output = parts[0]
        for part in parts[1:]:
            output += "\\frac"
            if part.startswith("{"):
                output += part
                continue
            if len(part) < 2:
                return value
            numerator = part[0]
            denominator = part[1]
            rest = part[2:]
            if denominator != "{":
                output += "{" + numerator + "}{" + denominator + "}" + rest
            else:
                output += "{" + numerator + "}" + denominator + rest
        return output

    def _fix_a_slash_b(self, value: str) -> str:
        if len(value.split("/")) != 2:
            return value
        left, right = value.split("/")
        try:
            if "sqrt" not in left:
                left_int = int(left)
                left = str(left_int)
            if "sqrt" not in right:
                right_int = int(right)
                right = str(right_int)
        except ValueError:
            return value
        return f"\\frac{{{left}}}{{{right}}}"

    def _fix_sqrt(self, value: str) -> str:
        return re.sub(r"\\sqrt(\w+)", r"\\sqrt{\1}", value)

    def _parse_number(self, value: str) -> float | None:
        value = value.replace(",", "")
        fraction = re.fullmatch(r"\\frac\{(-?\d+(?:\.\d+)?)\}\{(-?\d+(?:\.\d+)?)\}", value)
        if fraction:
            denominator = float(fraction.group(2))
            if denominator == 0:
                return None
            return float(fraction.group(1)) / denominator
        try:
            return float(value)
        except ValueError:
            pass
        if re.fullmatch(r"-?\d+/-?\d+", value):
            try:
                return float(Fraction(value))
            except (ValueError, ZeroDivisionError):
                return None
        return None

    def _strip_wrappers(self, value: str) -> str:
        stripped = value.strip()
        if (
            (stripped.startswith("[") and stripped.endswith("]"))
            or (stripped.startswith("(") and stripped.endswith(")"))
            or (stripped.startswith("{") and stripped.endswith("}"))
        ):
            return stripped[1:-1]
        return stripped

    def _split_tuple(self, value: str) -> list[str] | None:
        stripped = value.strip()
        if not ((stripped.startswith("(") and stripped.endswith(")")) or (stripped.startswith("[") and stripped.endswith("]"))):
            return None
        inner = stripped[1:-1]
        parts: list[str] = []
        current = ""
        depth = 0
        for char in inner:
            if char in "({[":
                depth += 1
            elif char in ")}]":
                depth -= 1
            if char == "," and depth == 0:
                parts.append(current)
                current = ""
            else:
                current += char
        parts.append(current)
        return [part.strip() for part in parts]

    def _symbolic_equal(self, left: str, right: str) -> bool:
        if any(parser is None for parser in (parse_latex, parse_expr, latex2sympy)):
            return False
        left_expr = self._parse_symbolic(left)
        right_expr = self._parse_symbolic(right)
        try:
            if str(left_expr) == str(right_expr) or left_expr == right_expr:
                return True
        except Exception:
            pass
        try:
            if left_expr.equals(right_expr) or simplify(left_expr - right_expr) == 0:
                return True
        except Exception:
            pass
        try:
            if (abs(left_expr.lhs - left_expr.rhs)).equals(abs(right_expr.lhs - right_expr.rhs)):
                return True
        except Exception:
            pass
        try:
            return math.isclose(float(N(left_expr)), float(N(right_expr)), rel_tol=1e-4, abs_tol=1e-8)
        except Exception:
            return False

    def _parse_symbolic(self, value: str) -> Any:
        for parser in (parse_latex, parse_expr, latex2sympy):
            try:
                return parser(value.replace("\\\\", "\\"))
            except Exception:
                try:
                    return parser(value)
                except Exception:
                    pass
        return value


class AIMEJudge(Math500Judge):
    async def judge(self, sample: Sample, response: ModelResponse) -> JudgeResult:
        expected_raw = self._expected_answer(sample)
        expected_answer = self.extract_answer(expected_raw, use_last_number=False) or self.strip_answer_string(expected_raw)
        predicted_answer = self.extract_answer(response.text or "")
        normalized_prediction = self.strip_answer_string(predicted_answer)
        normalized_expected = self.strip_answer_string(expected_answer)
        passed = self.math_equal(normalized_prediction, normalized_expected)
        return JudgeResult(
            judge_name="aime_acc",
            judge_result="pass" if passed else "fail",
            score=1.0 if passed else 0.0,
            judge_reason="AIME answer matched reference." if passed else "AIME answer did not match reference.",
            judge_metadata={
                "predicted_answer": predicted_answer,
                "expected_answer": expected_answer,
                "raw_expected_answer": expected_raw,
                "normalized_prediction": normalized_prediction,
                "normalized_expected": normalized_expected,
            },
        )


class GSM8KJudge(Math500Judge):
    async def judge(self, sample: Sample, response: ModelResponse) -> JudgeResult:
        expected_answer = self._expected_answer(sample)
        predicted_answer = self.extract_answer(response.text or "")
        normalized_prediction = self.strip_answer_string(predicted_answer)
        normalized_expected = self.strip_answer_string(expected_answer)
        passed = self.math_equal(normalized_prediction, normalized_expected)
        return JudgeResult(
            judge_name="gsm8k_exact_match",
            judge_result="pass" if passed else "fail",
            score=1.0 if passed else 0.0,
            judge_reason="GSM8K answer matched reference." if passed else "GSM8K answer did not match reference.",
            judge_metadata={
                "predicted_answer": predicted_answer,
                "expected_answer": expected_answer,
                "normalized_prediction": normalized_prediction,
                "normalized_expected": normalized_expected,
            },
        )
