命令：

```bash
python scripts/run_benchmark.py run --model-id mock.default --max-samples 3 --run-id smoke-test --no-resume
```

实际走的是一条完整的“小样本评测链路”：加载配置 -> 解析数据注册表 -> 取前 3 条样本 -> 用 mock 模型生成回答 -> judge 判分 -> 写 raw/judged/log/summary 输出。

**1. 脚本入口**
入口是 [scripts/run_benchmark.py](/Users/l/klee_code/git_repos/ELBench/scripts/run_benchmark.py):1。

这个文件只做两件事：

- 把仓库的 `src/` 加到 `sys.path`
- 调用 `elbench.cli.main()`

核心位置：

- [scripts/run_benchmark.py](/Users/l/klee_code/git_repos/ELBench/scripts/run_benchmark.py):4 定位项目根目录
- [scripts/run_benchmark.py](/Users/l/klee_code/git_repos/ELBench/scripts/run_benchmark.py):5 定位 `src`
- [scripts/run_benchmark.py](/Users/l/klee_code/git_repos/ELBench/scripts/run_benchmark.py):9 导入 CLI
- [scripts/run_benchmark.py](/Users/l/klee_code/git_repos/ELBench/scripts/run_benchmark.py):13 执行 `main()`

**2. CLI 参数解析**
参数定义在 [src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):12。

这条命令对应的参数在这里定义：

- `run` 子命令：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):19
- `--model-id`：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):21
- `--run-id`：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):22
- `--max-samples`：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):27
- `--no-resume`：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):29

然后 CLI 会加载配置并构造 `RunOptions`：

- 加载配置：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):37
- 创建 runner：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):49
- 调用 `runner.run(...)`：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):50
- `model_id=args.model_id`：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):53
- `run_id=run_id`：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):54
- `max_samples=args.max_samples`：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):59
- `resume=not args.no_resume`：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):61

所以 `--no-resume` 的直接效果是：`RunOptions.resume = False`。

**3. 配置加载**
配置加载入口是 [src/elbench/config/loader.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/config/loader.py):20。

它会读取这些配置：

- `configs/app.yaml`
- `configs/module_registry.yaml`
- `configs/providers.yaml`
- `configs/models.yaml`
- `configs/judges.yaml`
- `configs/file_registry.yaml`
- `configs/field_mappings.yaml`

关键逻辑：

- 读取 YAML：[src/elbench/config/loader.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/config/loader.py):13
- 加载项目配置：[src/elbench/config/loader.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/config/loader.py):20
- 解析 `data_root` 和 `output_root`：[src/elbench/config/loader.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/config/loader.py):33
- 建立 `models` 字典：[src/elbench/config/loader.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/config/loader.py):37
- 建立 `file_registry` 字典：[src/elbench/config/loader.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/config/loader.py):39
- 建立 `field_mappings` 字典：[src/elbench/config/loader.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/config/loader.py):42

**4. model-id mock.default 对应配置**
`--model-id mock.default` 会在 [configs/models.yaml](/Users/l/klee_code/git_repos/ELBench/configs/models.yaml):2 找到模型配置。

关键配置：

- `model_id: mock.default`：[configs/models.yaml](/Users/l/klee_code/git_repos/ELBench/configs/models.yaml):2
- `provider_name: mock`：[configs/models.yaml](/Users/l/klee_code/git_repos/ELBench/configs/models.yaml):3
- `model_name: mock-echo`：[configs/models.yaml](/Users/l/klee_code/git_repos/ELBench/configs/models.yaml):4
- `max_tokens: 512`：[configs/models.yaml](/Users/l/klee_code/git_repos/ELBench/configs/models.yaml):6
- `retry.max_attempts: 1`：[configs/models.yaml](/Users/l/klee_code/git_repos/ELBench/configs/models.yaml):9
- `provider_kwargs.prefix: "[MOCK]"`：[configs/models.yaml](/Users/l/klee_code/git_repos/ELBench/configs/models.yaml):17

`provider_name: mock` 又会对应到 [configs/providers.yaml](/Users/l/klee_code/git_repos/ELBench/configs/providers.yaml):2：

- `provider_name: mock`：[configs/providers.yaml](/Users/l/klee_code/git_repos/ELBench/configs/providers.yaml):2
- `adapter: mock`：[configs/providers.yaml](/Users/l/klee_code/git_repos/ELBench/configs/providers.yaml):3

**5. Runner 主流程**
核心执行在 [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):42。

命令进入后，主要流程是：

1. 查找 `mock.default` 模型配置  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):43

2. 找到它对应的 provider 配置  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):44

3. 根据 `run-id=smoke-test` 和 `model-id=mock.default` 构造输出路径  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):45

4. 创建 checkpoint，但因为 `--no-resume`，不会调用 `checkpoint.load()`  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):47  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):48

5. 解析文件注册表  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):51

6. 加载样本，并受 `--max-samples 3` 限制  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):57  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):140

7. 创建 writer、judge router、provider client  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):60  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):64  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):65

8. 并发 worker 处理样本  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):88

9. 汇总 summary  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):112

**6. 数据文件解析**
因为命令没有指定 `--module`、`--subset`、`--source-file`，所以会解析 `configs/file_registry.yaml` 中全部注册文件。

文件注册表在 [configs/file_registry.yaml](/Users/l/klee_code/git_repos/ELBench/configs/file_registry.yaml):1。

当前前几个文件是：

- `安全拒答.jsonl`：[configs/file_registry.yaml](/Users/l/klee_code/git_repos/ELBench/configs/file_registry.yaml):2
- `安全引导.jsonl`：[configs/file_registry.yaml](/Users/l/klee_code/git_repos/ELBench/configs/file_registry.yaml):15
- `安全回答.jsonl`：[configs/file_registry.yaml](/Users/l/klee_code/git_repos/ELBench/configs/file_registry.yaml):28
- `SATAs.xlsx`：[configs/file_registry.yaml](/Users/l/klee_code/git_repos/ELBench/configs/file_registry.yaml):41
- `adversarial_prompts.xlsx`：[configs/file_registry.yaml](/Users/l/klee_code/git_repos/ELBench/configs/file_registry.yaml):57
- `高阶育人-edu.jsonl`：[configs/file_registry.yaml](/Users/l/klee_code/git_repos/ELBench/configs/file_registry.yaml):73
- `高阶育人-omni.jsonl`：[configs/file_registry.yaml](/Users/l/klee_code/git_repos/ELBench/configs/file_registry.yaml):86

注册表解析代码在 [src/elbench/registry/file_registry.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/registry/file_registry.py):16。它根据 `path_hints`、文件名、pattern 去 `data/benchmark_root/` 下找真实文件。

样本加载在 runner 的 `_load_samples`：

- 创建 loader：[src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):134
- 遍历样本：[src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):135
- 达到 `max_samples=3` 后停止：[src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):140

loader 工厂在 [src/elbench/loaders/factory.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/loaders/factory.py):8，支持 `jsonl` 和 `xlsx`。

**7. mock 模型如何生成回答**
provider 创建在 [src/elbench/providers/factory.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/providers/factory.py):16。

因为 `mock.default` 的 provider adapter 是 `mock`，所以会实例化：

- [src/elbench/providers/mock.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/providers/mock.py):11

mock 生成逻辑：

- 如果 `provider_kwargs.mode == "judge_json"`，走 judge mock  
  [src/elbench/providers/mock.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/providers/mock.py):15
- 否则走普通 mock echo  
  [src/elbench/providers/mock.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/providers/mock.py):18

`mock.default` 是普通被测模型，所以会生成类似：

```text
[MOCK] module=... subset=... sample_id=...
<原始 prompt 前 200 字>
```

对应代码在 [src/elbench/providers/mock.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/providers/mock.py):19。

**8. 每条样本如何处理**
单条样本处理在 [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):226。

主要步骤：

1. 用 sample prompt 构造 `GenerationRequest`  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):237

2. 调用 `_generate_with_retry`  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):244

3. 实际调用 provider 的 `client.generate(...)`  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):297

4. 找 judge  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):253

5. 执行 judge  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):254

6. 构造 `EvalResult`  
   [src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):255

**9. judge 路由**
judge 配置在 [configs/judges.yaml](/Users/l/klee_code/git_repos/ELBench/configs/judges.yaml):1。

默认 judge 模型是：

- `default_judge_model_id: mock.judge`：[configs/judges.yaml](/Users/l/klee_code/git_repos/ELBench/configs/judges.yaml):1

task 到 judge 的映射：

- `safety_refusal` -> `llm`：[configs/judges.yaml](/Users/l/klee_code/git_repos/ELBench/configs/judges.yaml):3
- `safety_guidance` -> `llm`：[configs/judges.yaml](/Users/l/klee_code/git_repos/ELBench/configs/judges.yaml):6
- `safety_answer` -> `llm`：[configs/judges.yaml](/Users/l/klee_code/git_repos/ELBench/configs/judges.yaml):9
- `teaching_harm` -> `rule`：[configs/judges.yaml](/Users/l/klee_code/git_repos/ELBench/configs/judges.yaml):12
- `adversarial_safety` -> `llm`：[configs/judges.yaml](/Users/l/klee_code/git_repos/ELBench/configs/judges.yaml):14
- `highlevel_edu` -> `llm`：[configs/judges.yaml](/Users/l/klee_code/git_repos/ELBench/configs/judges.yaml):17
- `highlevel_omni` -> `rule`：[configs/judges.yaml](/Users/l/klee_code/git_repos/ELBench/configs/judges.yaml):20

路由代码在 [src/elbench/judges/router.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/judges/router.py):18。

- 如果 mode 是 `llm`，创建 `LLMJudge`：[src/elbench/judges/router.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/judges/router.py):27
- 如果 mode 是 `rule`，进入 `_get_rule_judge`：[src/elbench/judges/router.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/judges/router.py):29
- rule judge 当前只显式处理 `teaching_harm` 和 `highlevel_omni`：[src/elbench/judges/router.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/judges/router.py):42

LLM judge 在 [src/elbench/judges/llm_judge.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/judges/llm_judge.py):11。

它会：

- 生成 judge prompt：[src/elbench/judges/llm_judge.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/judges/llm_judge.py):19
- 用 `mock.judge` 再调用一次 provider：[src/elbench/judges/llm_judge.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/judges/llm_judge.py):20
- 从 judge response 中提取 JSON：[src/elbench/judges/llm_judge.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/judges/llm_judge.py):29
- 转成 `JudgeResult`：[src/elbench/judges/llm_judge.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/judges/llm_judge.py):42

**10. --no-resume 的具体影响**
`--no-resume` 只控制是否读取已有 checkpoint。

代码在：

- CLI 设置 `resume=not args.no_resume`：[src/elbench/cli.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/cli.py):61
- runner 只有 `options.resume` 为 true 才 `checkpoint.load()`：[src/elbench/execution/runner.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/execution/runner.py):48

所以这条命令会忽略旧的 checkpoint，不会跳过之前已完成的样本。

注意：当前 writer 是 append 模式：

- [src/elbench/persistence/writers.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/persistence/writers.py):49

因此 `--no-resume` 不等于自动清空旧输出。如果同一个 `--run-id smoke-test` 反复跑，可能会往同一个 JSONL 里追加记录。

**11. 输出文件位置**
输出路径由 [src/elbench/persistence/writers.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/persistence/writers.py):21 构造。

对于这条命令：

```text
run_id = smoke-test
model_id = mock.default
```

会写到：

```text
outputs/raw_responses/smoke-test/mock.default.jsonl
outputs/judged_results/smoke-test/mock.default.jsonl
outputs/logs/smoke-test/mock.default.failures.jsonl
outputs/logs/smoke-test/mock.default.retries.jsonl
outputs/logs/smoke-test/mock.default.checkpoint.json
outputs/logs/smoke-test/mock.default.log
outputs/summaries/smoke-test/mock.default.summary.json
```

对应代码：

- raw：[src/elbench/persistence/writers.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/persistence/writers.py):30
- judged：[src/elbench/persistence/writers.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/persistence/writers.py):31
- failures：[src/elbench/persistence/writers.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/persistence/writers.py):32
- retries：[src/elbench/persistence/writers.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/persistence/writers.py):33
- summary：[src/elbench/persistence/writers.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/persistence/writers.py):34
- checkpoint：[src/elbench/persistence/writers.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/persistence/writers.py):35
- log：[src/elbench/persistence/writers.py](/Users/l/klee_code/git_repos/ELBench/src/elbench/persistence/writers.py):36

**一句话调用链**
```text
scripts/run_benchmark.py
-> elbench.cli.main()
-> load_project_config("configs")
-> BenchmarkRunner.run(RunOptions(...))
-> FileRegistry.resolve()
-> LoaderFactory + JsonlLoader/XlsxLoader + RecordNormalizer
-> ProviderFactory.create(mock)
-> MockModelClient.generate()
-> JudgeRouter.get_judge()
-> LLMJudge 或 rule judge
-> JsonlWriter 写 raw/judged/failures/retries
-> CheckpointStore 写 checkpoint
-> build_summary 写 summary
```
