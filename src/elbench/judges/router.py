from __future__ import annotations

from elbench.judges.base import BaseJudge
from elbench.judges.judge_highlevel import HighLevelJudge
from elbench.judges.judge_ifeval import IFEvalJudge
from elbench.judges.judge_math import AIMEJudge, Math500Judge
from elbench.judges.judge_mmlu import MMLUProJudge
from elbench.judges.judge_safety import SafetyJudge
from elbench.judges.judge_teaching_harm import TeachingHarmJudge
from elbench.judges.llm_judge import LLMJudge
from elbench.judges.placeholder import PlaceholderJudge
from elbench.schemas.config import ProjectConfig
from elbench.schemas.evaluation import Sample


class JudgeRouter:
    def __init__(self, project_config: ProjectConfig) -> None:
        self._project_config = project_config
        self._cache: dict[str, BaseJudge] = {}

    def get_judge(self, sample: Sample) -> BaseJudge:
        task = sample.task or ""
        task_config = self._project_config.judges.tasks.get(task)
        mode = task_config.mode if task_config else "placeholder"
        cache_key = f"{mode}:{task}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        if mode == "llm" and task_config is not None:
            judge = LLMJudge(self._project_config, task_config)
        elif mode == "rule":
            judge = self._get_rule_judge(sample)
        else:
            judge = PlaceholderJudge(judge_name=f"{sample.module}_placeholder_judge")
        self._cache[cache_key] = judge
        return judge

    async def aclose(self) -> None:
        for judge in self._cache.values():
            aclose = getattr(judge, "aclose", None)
            if callable(aclose):
                await aclose()

    def _get_rule_judge(self, sample: Sample) -> BaseJudge:
        if sample.module == "安全可信" and sample.task == "teaching_harm":
            return TeachingHarmJudge()
        if sample.module == "高阶育人" and sample.task == "highlevel_omni":
            return HighLevelJudge()
        if sample.module == "通用模型" and sample.task in {"mmlu_pro", "ceval"}:
            return MMLUProJudge()
        if sample.module == "通用模型" and sample.task == "ifeval":
            return IFEvalJudge()
        if sample.module == "通用模型" and sample.task == "math_500":
            return Math500Judge()
        if sample.module == "通用模型" and sample.task in {"aime24", "aime25", "aime26"}:
            return AIMEJudge()
        return PlaceholderJudge(judge_name=f"{sample.module}_placeholder_judge")
