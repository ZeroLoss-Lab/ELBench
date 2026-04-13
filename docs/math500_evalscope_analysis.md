当 `dataset` 改成 `'math_500'` 时，主干调用链不变：

`__main__ -> main() -> TaskConfig -> run_task() -> EvalScope evaluator -> math_500 adapter -> model.generate() -> calculate_metrics() -> report JSON -> driver.parse_results() -> update_csv()`

差别集中在 dataset adapter、prompt、答案抽取、metric 聚合和 driver 最后取分。

**入口配置**
在 [run_evalscope1_4_2.py](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py):362，`math_500` 命中 subset 映射：

```python
"math_500": "Level 1"
```

所以传给 EvalScope 的参数是：

```python
datasets=["math_500"]
dataset_args={
    "math_500": {
        "subset_list": ["Level 1"]
    }
}
```

因此这次不是跑 MATH-500 全部 5 个 level，而是只跑 `Level 1`。另外 [run_evalscope1_4_2.py](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py):256 里 `limit=1`，所以实际只评 `Level 1` 中的 1 条样本。

**MATH-500 adapter 行为**
`math_500` 的 adapter 在 [math_500_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/math_500/math_500_adapter.py):14。

关键配置：

```python
dataset_id='AI-ModelScope/MATH-500'
subset_list=['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5']
metric_list=[{'acc': {'numeric': True}}]
few_shot_num=0
eval_split='test'
prompt_template='{question}\nPlease reason step by step, and put your final answer within \\boxed{{}}.'
```

样本转换在 [math_500_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/math_500/math_500_adapter.py):41：

```python
input=record['problem']
target=record['answer']
subset_key=f"Level {record['level']}"
metadata={
    'question_id': record['unique_id'],
    'solution': record['solution'],
}
```

也就是说，MATH-500 不是多选题，也不是 IFEval 那种规则检查。它让模型解数学题，并要求最终答案放到 `\boxed{}` 里。

**答案抽取**
MATH-500 重写了 `extract_answer()`，见 [math_500_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/math_500/math_500_adapter.py):52：

```python
return extract_answer(prediction)
```

实际抽取逻辑在 [math_parser.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/metrics/math_parser.py):236，大致顺序是：

1. 如果回复里有 `boxed`，取最后一个 `boxed` 后面的内容；如果是 `{...}`，会按括号栈取出完整答案。
2. 否则如果有 `The answer is` / `final answer is` / `答案是` / `ANSWER:`，取这些标记后面的内容。
3. 否则 fallback：从全文里抽最后一个数字。
4. 最后去掉换行、开头冒号、末尾句点 `/`，再做 `strip_answer_string()` 归一化。

所以模型完整推理不会直接拿来比对，真正参与判分的是抽出来的 final answer。

**判分**
metric 是 `acc` 且 `numeric=True`，见 [math_500_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/math_500/math_500_adapter.py):23。

`Accuracy.apply()` 的 numeric 分支在 [metric.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/metrics/metric.py):42：

```python
ref_answer = strip_answer_string(reference)
results.append(float(math_equal(prediction, ref_answer)))
```

所以每条样本分数是：

```text
1.0 if math_equal(extracted_prediction, normalized_reference)
0.0 otherwise
```

`math_equal()` 支持的不只是纯字符串相等，还包括：

- 数值相等，比如 `0.5`、`1/2`、百分比相关处理
- 去括号/集合/矩阵等部分格式差异
- 简单符号等价，底层会尝试 symbolic equal

这和 `mmlu_pro` 的选项字母准确率不同，也和 `ifeval` 的 instruction-following 规则检查完全不同。

**聚合到 report**
EvalScope 默认用 `mean` 聚合单样本分数。因为 metric 名是 `acc`，聚合后 report 里的 metric 名会变成：

```text
mean_acc
```

report 生成逻辑在 [generator.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/report/generator.py):79，会把 aggregation name 拼到 metric name 前面：

```python
metric_name = f'{agg_score_item.aggregation_name}_{agg_score_item.metric_name}'
```

所以 `math_500.json` 大概是这种结构：

```json
{
  "dataset_name": "math_500",
  "score": 1.0,
  "metrics": [
    {
      "name": "mean_acc",
      "score": 1.0,
      "categories": [
        {
          "name": ["default"],
          "subsets": [
            {
              "name": "Level 1",
              "score": 1.0,
              "num": 1
            }
          ]
        }
      ]
    }
  ]
}
```

顶层 `"score"` 来自 [report.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/report/report.py):121：

```python
self.score = self.metrics[0].score
```

也就是说，MATH-500 的顶层 score 就是第一个 metric `mean_acc` 的分数。当前只跑 `Level 1` 且 `limit=1`，所以它实际就是这一条 Level 1 样本的 `acc`。

**driver 抽取分数**
你的 driver 抽分函数在 [run_evalscope1_4_2.py](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py):109。

它扫描：

```text
/tmp/evalscope/outputs/{safe_model_name}/reports/**/*.json
```

对 `gemini-2.5-flash` 来说 work_dir 是：

```text
/tmp/evalscope/outputs/gemini_2_5_flash
```

解析逻辑在 [run_evalscope1_4_2.py](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py):136：

```python
if "score" in data:
    score = data["score"]
elif "accuracy" in data:
    score = data["accuracy"]
elif "metrics" in data and isinstance(data["metrics"], dict):
    ...
```

`math_500.json` 顶层有 `"score"`，所以 driver 不会深入解析 `metrics`，而是直接：

```python
results["math_500"] = data["score"]
```

最终写进 `model_leaderboard.csv` 的 `math_500` 列就是：

```text
mean_acc
```

在当前配置下更具体地说是：

```text
Level 1 子集上，被 limit=1 截断后的 mean_acc
```

**容易误解的点**
`no_timestamp=1` 导致 work_dir 固定。`parse_results()` 又是扫描整个 `reports/**/*.json`，不是只扫描本次运行的 `math_500.json`。所以如果同一个 work_dir 里之前残留了 `ifeval.json`、`gsm8k.json`、`mmlu_pro.json`，这次只跑 `math_500`，CSV 仍可能把旧报告也一起解析进去。  
`math_500` 自己的分数列是 `math_500 = 顶层 score = mean_acc`，但 CSV 里出现的其他列可能来自旧 report。
