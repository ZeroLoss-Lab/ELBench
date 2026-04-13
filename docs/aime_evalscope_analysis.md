当 [run_evalscope1_4_2.py](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py):355 附近把 dataset 改成 `'aime25'` 时，主流程仍然是：

```text
__main__
-> main()
-> TaskConfig
-> run_task()
-> EvalScope evaluator
-> AIME25Adapter
-> model.generate()
-> calculate_metrics()
-> report JSON
-> driver.parse_results()
-> update_csv()
```

但 `aime25` 和 `math_500` 在“抽取答案”和“判分”上有一个关键差别：`aime25` 覆盖了 `match_score()`，所以最终判分走 AIME 自己的 `grade_answer()`，不是通用 `acc numeric=True -> math_equal()` 那条路。

**入口配置差别**
`aime25` 命中 subset 映射，位置在 [run_evalscope1_4_2.py](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py):362：

```python
"aime25": "AIME2025-I"
```

所以传给 EvalScope 的是：

```python
datasets=["aime25"]
dataset_args={
    "aime25": {
        "subset_list": ["AIME2025-I"]
    }
}
```

同时 [run_evalscope1_4_2.py](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py):254 里有：

```python
limit=1
```

所以当前配置下不是跑完整 AIME2025，而是：

```text
AIME2025-I 子集中的 1 条样本
```

**AIME25 Adapter**
adapter 在 [aime25_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/aime25_adapter.py):87。

关键配置：

```python
dataset_id='opencompass/AIME2025'
subset_list=['AIME2025-I', 'AIME2025-II']
metric_list=[{'acc': {'numeric': True}}]
few_shot_num=0
eval_split='test'
prompt_template=PROMPT_TEMPLATE
```

prompt 模板是 [aime25_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/aime25_adapter.py):79：

```text
Solve the following math problem step by step. Put your answer inside \boxed{}.

{question}

Remember to put your answer inside \boxed{}.
```

样本转换在 [aime25_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/aime25_adapter.py):112：

```python
return Sample(
    input=record['question'],
    target=record['answer'],
)
```

所以 AIME25 没有多选项，也没有 instruction metadata。它就是数学题 question + 标准 answer。

**抽取答案**
EvalScope 通用流程会先从模型原始输出里计算 `filtered_prediction`，见 [default_data_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/api/benchmark/adapters/default_data_adapter.py):578：

```python
prediction = task_state.output.completion
filtered_prediction = self.filter_prediction(prediction, task_state)
```

`filter_prediction()` 会调用 adapter 的 `extract_answer()`，见 [default_data_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/api/benchmark/adapters/default_data_adapter.py):490。

AIME25 的 `extract_answer()` 在 [aime25_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/aime25_adapter.py):118：

```python
extracted_pred = extract_answer(prediction)
filtered_pred = normalize_answer(extracted_pred)
return filtered_pred
```

这里分两步：

1. `evalscope.metrics.math_parser.extract_answer()` 从完整回复中抽最终答案。
2. `aime.math_normalize.normalize_answer()` 再归一化格式。

`extract_answer()` 的主要优先级和 `math_500` 一样：

```text
boxed{...}
-> The answer is / final answer is / 答案是 / ANSWER:
-> fallback 到全文最后一个数字
```

所以如果模型输出：

```text
After computation, the answer is \boxed{137}.
```

先抽出：

```text
137
```

然后 `normalize_answer()` 做进一步清洗，比如去空格、去 `\left` / `\right`、修正 `\frac12`、修正 `sqrt3`、去单位/百分号等。相关逻辑在 [math_normalize.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/math_normalize.py):36 和 [math_normalize.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/math_normalize.py):122。

**但判分不是用 filtered_prediction**
这是 AIME25 最容易看错的点。

虽然通用流程已经算出了 `filtered_prediction`，但 AIME25 自己覆盖了 `match_score()`，位置在 [aime25_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/aime25_adapter.py):134：

```python
is_correct = grade_answer(extract_answer(original_prediction), reference)
accuracy_score = 1.0 if is_correct else 0.0
score.value['acc'] = accuracy_score
```

也就是说，真正判分时它重新从 `original_prediction` 抽一次答案：

```text
extract_answer(original_prediction)
```

然后交给：

```text
grade_answer(given_answer, reference)
```

因此 `filtered_prediction` 会被写入 review 里的 `extracted_prediction` 字段，但最终 `acc` 实际来自 `grade_answer(extract_answer(original_prediction), reference)`。

**grade_answer 判分逻辑**
`grade_answer()` 在 [grader.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/grader.py):255。

它的判断逻辑大致是：

1. 如果模型答案是 `None`，直接 False。
2. 先用 `math_normalize.normalize_answer()` 分别归一化标准答案和模型答案。
3. 如果归一化字符串完全相等，直接 True。
4. 再用 `grader._normalize()` 做更强的归一化。
5. 如果字符串相等，True。
6. 如果是 tuple/list 类答案，会拆元素逐个比较。
7. 对分数有一个严格点：如果标准答案和模型答案都是分数，但分数未化简，不一定用 sympy 放宽，要求字符串一致。
8. 如果标准答案是整数而模型答案不是严格整数形式，则判 False。
9. 其他情况尝试 sympy：构造 `(ground_truth)-(given)`，如果 `sympy.simplify(...) == 0`，判 True。

关键代码在 [grader.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/grader.py):265 到 [grader.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/grader.py):307。

所以 AIME25 的单题分数是：

```text
acc = 1.0 if grade_answer(extract_answer(original_prediction), reference) else 0.0
```

不是：

```text
acc = math_equal(filtered_prediction, reference)
```

这点和 `math_500` 不同。

**LLM Judge 分支**
AIME25 还实现了 `llm_match_score()`，在 [aime25_adapter.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/benchmarks/aime/aime25_adapter.py):156，会让 judge 判断两个表达式是否等价。

但你的 `TaskConfig` 里没有启用 `use_llm_judge`，所以当前运行走的是 rule-based `match_score()`，不会走这个 LLM judge 分支。

**聚合得到 report 分数**
每条样本得到：

```python
score.value['acc'] = 0.0 or 1.0
```

EvalScope 默认 mean 聚合，所以 report metric 名会变成：

```text
mean_acc
```

metric 名拼接逻辑在 [generator.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/report/generator.py):79：

```python
metric_name = f'{agg_score_item.aggregation_name}_{agg_score_item.metric_name}'
```

report 顶层 `score` 来自 [report.py](/Users/l/klee_code/git_repos/evalscope_driver/evalscope_1_4_2/evalscope/report/report.py):121：

```python
self.score = self.metrics[0].score
```

所以 `aime25.json` 的结构大概是：

```json
{
  "dataset_name": "aime25",
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
              "name": "AIME2025-I",
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

在当前 `limit=1` 下，`score` 就是 `AIME2025-I` 中这 1 条样本的 acc。

**driver 最后怎么抽分**
你的 driver 抽分函数在 [run_evalscope1_4_2.py](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py):109。

它扫描：

```text
work_dir/reports/**/*.json
```

然后对每个 JSON：

```python
dataset_name = os.path.basename(json_file).replace(".json", "")
```

如果文件是：

```text
.../reports/gemini-2.5-flash/aime25.json
```

那么 key 就是：

```python
"aime25"
```

抽分逻辑在 [run_evalscope1_4_2.py](/Users/l/klee_code/git_repos/evalscope_driver/run_evalscope1_4_2.py):136：

```python
if "score" in data:
    score = data["score"]
```

`aime25.json` 顶层有 `"score"`，所以 driver 直接取：

```python
results["aime25"] = data["score"]
```

最终写入 `model_leaderboard.csv` 的 `aime25` 列就是：

```text
aime25 report 顶层 score = mean_acc
```

更具体到当前配置：

```text
aime25 列 = AIME2025-I 子集 limit=1 后的 mean_acc
```

**和 math_500 的关键差别**
`math_500`：

```text
extract_answer(prediction)
-> acc numeric=True
-> math_equal(extracted_prediction, normalized_reference)
-> mean_acc
```

`aime25`：

```text
extract_answer(prediction) + normalize_answer() 生成 filtered_prediction
-> 但 match_score 里重新 extract_answer(original_prediction)
-> grade_answer(extracted_answer, reference)
-> acc
-> mean_acc
```

所以 AIME25 更像：

```text
完整回复 -> 抽最终答案 -> AIME grader 归一化/符号判等 -> 0/1 -> mean_acc
```

而不是单纯走 EvalScope 通用 numeric accuracy。
