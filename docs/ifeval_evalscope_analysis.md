如果把 [/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:355](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:355) 的 dataset 改成或启用 `'ifeval'`，主干流程仍然是：

`__main__ -> main() -> TaskConfig -> run_task() -> DefaultEvaluator -> benchmark.load_dataset() -> model.generate() -> calculate_metrics() -> report -> driver.parse_results() -> update_csv()`

差别主要在 benchmark adapter、样本格式、指标类型和 driver 最终抽分方式。

**入口配置差别**
`ifeval` 不在这段 subset 映射里：[/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:362](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:362)

所以：

```python
subset = None
evalscope_dataset_args_value = {}
dataset_args = {"ifeval": {}}
```

不像 `mmlu_pro` 会得到：

```python
dataset_args = {"mmlu_pro": {"subset_list": ["physics"]}}
```

因此 `ifeval` 走它 adapter 默认配置：`subset_list=['default']`，`eval_split='train'`，`few_shot_num=0`。

IFEval adapter 在这里注册：[/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/ifeval_adapter.py:15](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/ifeval_adapter.py:15)

关键配置是：

- `dataset_id='opencompass/ifeval'`
- `subset_list=['default']`
- `metric_list=['prompt_level_strict', 'inst_level_strict', 'prompt_level_loose', 'inst_level_loose']`
- `few_shot_num=0`
- `eval_split='train'`

位置：[/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/ifeval_adapter.py:22](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/ifeval_adapter.py:22)

**样本和 Prompt 差别**
`mmlu_pro` 是多选题，会构造带 choices 的 Sample，并要求模型输出 `ANSWER: [LETTER]`。  
`ifeval` 是指令跟随评测，`record_to_sample()` 直接把数据集里的 `prompt` 包成一个 user message，target 为空，原始 record 放进 metadata：

[/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/ifeval_adapter.py:41](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/ifeval_adapter.py:41)

```python
prompt = record.get('prompt', '')
message_list = [ChatMessageUser(content=prompt)]
return Sample(input=message_list, target='', metadata=record)
```

所以它不会走多选题的答案抽取逻辑，也没有 `ANSWER: A` 这种解析要求。

**打分差别**
`ifeval` 重写了 `match_score()`：[/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/ifeval_adapter.py:56](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/ifeval_adapter.py:56)

核心是：

```python
results = process_results(doc, [filtered_prediction])
score.value.update(results)
score.main_score_name = 'prompt_level_strict'
```

`process_results()` 在 [/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/utils.py:111](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/utils.py:111)，会返回四个分数：

```python
{
    'prompt_level_strict': ...,
    'inst_level_strict': ...,
    'prompt_level_loose': ...,
    'inst_level_loose': ...,
}
```

含义大致是：

- `prompt_level_strict`：严格模式下，这条 prompt 的所有指令是否全部满足，满足为 `1.0`，否则 `0.0`
- `inst_level_strict`：严格模式下，单条 prompt 内各 instruction 的平均满足率
- `prompt_level_loose`：宽松模式下，所有指令是否全部满足
- `inst_level_loose`：宽松模式下，各 instruction 的平均满足率

具体计算位置：[/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/utils.py:123](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/ifeval/utils.py:123)

之后 EvalScope 默认聚合器 `mean` 会对每个 metric 分别求平均，位置：[/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/metrics/metric.py:360](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/metrics/metric.py:360)

所以 report 里会有四个 metric：

```json
"metrics": [
  {"name": "mean_prompt_level_strict", "score": ...},
  {"name": "mean_inst_level_strict", "score": ...},
  {"name": "mean_prompt_level_loose", "score": ...},
  {"name": "mean_inst_level_loose", "score": ...}
]
```

我看到本机已有一次真实输出：

[/tmp/evalscope/outputs/gemini_2_5_flash/reports/gemini-2.5-flash/ifeval.json](/tmp/evalscope/outputs/gemini_2_5_flash/reports/gemini-2.5-flash/ifeval.json)

结构是：

```json
{
  "dataset_name": "ifeval",
  "score": 1.0,
  "metrics": [
    {"name": "mean_prompt_level_strict", "score": 1.0},
    {"name": "mean_inst_level_strict", "score": 1.0},
    {"name": "mean_prompt_level_loose", "score": 1.0},
    {"name": "mean_inst_level_loose", "score": 1.0}
  ]
}
```

**抽取分数的关键差别**
driver 的抽分函数是 [/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:109](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:109)。

关键逻辑：

[/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:136](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:136)

```python
if "score" in data:
    score = data["score"]
elif "accuracy" in data:
    score = data["accuracy"]
elif "metrics" in data and isinstance(data["metrics"], dict):
    ...
```

对 `ifeval.json` 来说，顶层有 `"score"`，所以它会直接抽：

```python
results["ifeval"] = data["score"]
```

而这个顶层 `score` 来自 EvalScope `Report.__post_init__()`：

[/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/report/report.py:121](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/report/report.py:121)

```python
self.score = self.metrics[0].score
```

也就是说：`ifeval` 被 driver 写进 CSV 的分数不是四个指标的平均值，而是第一个 metric 的分数。按 IFEval adapter 的 metric 顺序，第一个是：

```text
mean_prompt_level_strict
```

所以最终 `model_leaderboard.csv` 里的 `ifeval` 列表示：

```text
mean_prompt_level_strict
```

不是 `inst_level_strict`，也不是 loose 指标，也不是四项综合平均。

**一个容易踩的点**
因为 [/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:256](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:256) 设置了 `no_timestamp=1`，work_dir 固定是：

```text
/tmp/evalscope/outputs/gemini_2_5_flash
```

`parse_results()` 会扫描整个：

```text
/tmp/evalscope/outputs/gemini_2_5_flash/reports/**/*.json
```

见 [/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:118](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:118)

所以如果这个目录里以前跑过 `mmlu_pro`、`math_500`、`gsm8k` 等报告，那么你这次只跑 `ifeval`，CSV 里仍可能同时更新这些旧报告的列。它不是只解析本次 dataset 的 report。

同理，reviews 后处理也会扫描整个：

```text
work_dir/reviews/**/*.jsonl
```

位置：[/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:268](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:268)

`ifeval` 不在 `VLM_BENCHMARKS`，所以会走普通 jsonl 转 CSV 分支，调用：

[/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:297](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py:297)

输出类似：

```text
/tmp/evalscope/outputs/gemini_2_5_flash/ifeval_default.csv
```

**结论**
把 dataset 改成 `'ifeval'` 后，最大的差别是：评测不再是“抽取多选题字母并算 acc”，而是对模型完整回复做 instruction-following 规则检查，生成四个指标。当前 driver 的 `parse_results()` 最终只会抽顶层 `score`，也就是 `mean_prompt_level_strict`，并写成 CSV 中的 `ifeval` 列。它不会自动把 `mean_inst_level_strict`、`mean_prompt_level_loose`、`mean_inst_level_loose` 分别写入 CSV。
