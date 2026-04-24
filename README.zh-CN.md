# ELBench

[![English](https://img.shields.io/badge/Language-English-blue.svg)](./README.md)
[![简体中文](https://img.shields.io/badge/Language-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-red.svg)](./README.zh-CN.md)

一个面向教育大模型长期评测的配置驱动 benchmark 框架。

ELBench 不是临时脚本，而是按正式工程维护的评测系统。当前仓库统一承载四个模块：

- `安全可信`
- `高阶育人`
- `基本教育`
- `通用模型`

当前已正式注册进框架的 benchmark 资产规模是：

- `安全可信`：5 个文件
- `高阶育人`：2 个文件
- `基本教育`：4 个 YAML 场景，共 `45` 题
- `通用模型`：8 个单轮 benchmark 文件

`基本教育` 已作为 ELBench 的正式模块接入。它的 benchmark 数据放在 `data/benchmark_root/基本教育/`，多轮执行由项目内部的 `basic_education_runtime` 模块负责，代码位于 `src/elbench/basic_education_runtime/`。

这个内部运行时来源于 ELMES 项目，但现在已经按 ELBench 的内部模块方式接管和维护。

## 设计原则

- 评测流程由注册表和配置驱动，不在主流程里写死文件逻辑
- 模型调用统一走 provider adapter，不让厂商差异污染主 runner
- 客观题优先规则判分
- 主观开放题走 `LLM-as-a-Judge`
- 输出、日志、checkpoint、summary 保持稳定结构
- 中断后支持断点续跑
- 并发可配置，默认全局最大并发为 `100`

## 当前真正接上的内容

### 当前已注册的 benchmark 文件

`configs/file_registry.yaml` 当前会解析这些文件：

- `安全拒答.jsonl`
- `安全引导.jsonl`
- `安全回答.jsonl`
- `SATAs.xlsx`
- `adversarial_prompts.xlsx`
- `高阶育人-edu.jsonl`
- `高阶育人-omni.jsonl`
- `knowledge.yaml`
- `question.yaml`
- `cross.yaml`
- `config_guided_task.yaml`
- `mmlu_pro_sampled.jsonl`
- `ceval_sampled.jsonl`
- `ifeval_sampled.jsonl`
- `math_500_sampled.jsonl`
- `aime24_sampled.jsonl`
- `aime25.jsonl`
- `aime26.jsonl`
- `gsm8k_sampled.jsonl`

只有进入 `configs/file_registry.yaml` 的文件，才算 ELBench 当前正式可运行的 benchmark 数据。

### 当前判分策略

客观题走规则或参考答案判分：

- `SATAs.xlsx`
- `高阶育人-omni.jsonl`
- `mmlu_pro_sampled.jsonl`
- `ceval_sampled.jsonl`
- `ifeval_sampled.jsonl`
- `math_500_sampled.jsonl`
- `aime24_sampled.jsonl`
- `aime25.jsonl`
- `aime26.jsonl`
- `gsm8k_sampled.jsonl`

主观开放题走 `LLM-as-a-Judge`：

- `安全拒答.jsonl`
- `安全引导.jsonl`
- `安全回答.jsonl`
- `adversarial_prompts.xlsx`
- `高阶育人-edu.jsonl`

当前阶段，外部模型接入仍保持可插拔设计。仓库内提供了 `mock.default` 和 `mock.judge`，用于本地验证整条评测链路。

## 仓库结构

```text
.
├── configs/
│   ├── app.yaml
│   ├── basic_education.yaml
│   ├── field_mappings.yaml
│   ├── file_registry.yaml
│   ├── judges.yaml
│   ├── models.yaml
│   ├── module_registry.yaml
│   └── providers.yaml
├── data/
│   └── benchmark_root/
│       ├── 安全可信/
│       ├── 高阶育人/
│       ├── 基本教育/
│       └── 通用/
├── docs/
│   └── TEAM_MAINTENANCE_GUIDE.zh-CN.md
├── scripts/
│   └── run_benchmark.py
├── src/
│   └── elbench/
│       ├── basic_education_runtime/
│       ├── cli.py
│       ├── config/
│       ├── execution/
│       ├── judges/
│       ├── loaders/
│       ├── persistence/
│       ├── providers/
│       ├── registry/
│       ├── schemas/
│       ├── summary/
│       └── utils/
└── tests/
```

`scripts/run_benchmark.py` 只是薄入口。真正的评测逻辑都在 `src/elbench/` 下面。

## 核心架构

### 注册表与 schema 适配

- `configs/file_registry.yaml` 负责把 benchmark 文件映射到 module、subset、task、loader 和 canonical name
- `configs/field_mappings.yaml` 负责把原始字段映射到 ELBench 统一内部 schema
- JSONL、XLSX、基本教育 YAML 都会被归一化为统一 `Sample`

### 统一 sample/result 结构

统一 sample 核心字段包括：

- `sample_id`
- `source_file`
- `module`
- `subset`
- `task`
- `dimension`
- `prompt`
- `reference`
- `metadata`

执行结果会额外记录：

- `provider_name`
- `model_id`
- `model_name`
- `model_response`
- `judge_result`
- `score`
- `judge_reason`
- `judge_metadata`
- `latency_ms`
- `retry_count`
- `timestamp`

### 模型适配层

- `ModelClient` 是统一接口
- 各 provider 差异封装在 `src/elbench/providers/`
- 主 runner 不需要知道模型来自哪家厂商

### 执行、并发与恢复

runner 当前支持：

- 全局并发控制
- provider/model 级并发限制
- 指数退避重试
- 失败日志
- checkpoint 断点续跑
- 原始回答持久化
- 判分结果持久化
- summary 生成

默认全局最大并发在 `configs/app.yaml` 中配置为 `100`。

### 基本教育运行时

`基本教育` 与其他模块的区别只在执行方式，不在数据治理方式：

- benchmark 数据仍然放在 `data/benchmark_root/基本教育/`
- 文件发现仍走 `configs/file_registry.yaml`
- 多轮执行由 `src/elbench/execution/basic_education.py` 负责
- 内部运行时代码位于 `src/elbench/basic_education_runtime/`

## 输出目录

```text
outputs/
├── raw_responses/
├── judged_results/
├── summaries/
└── logs/
```

这些目录是运行时产物，默认不纳入 Git 管理。

## 安装方式

### 仅安装核心框架

```bash
pip install -e .
```

### 安装基本教育运行时依赖

```bash
pip install -e .[basic-education]
```

### 团队开发环境

```bash
pip install -e .[basic-education,dev]
```

## 快速开始

### 查看当前已注册的 benchmark 文件

```bash
python scripts/run_benchmark.py inspect
```

### 跑一轮本地 smoke test

```bash
python scripts/run_benchmark.py run --model-id mock.default --max-samples 3 --run-id smoke-test --no-resume
```

或者在可编辑安装后：

```bash
elbench inspect
elbench run --model-id mock.default --max-samples 3 --run-id smoke-test --no-resume
```

### 运行基本教育

当前内置场景是：

- `data/benchmark_root/基本教育/知识点讲解/knowledge.yaml`（`10`）
- `data/benchmark_root/基本教育/情景化出题/question.yaml`（`10`）
- `data/benchmark_root/基本教育/跨学科教案生成/cross.yaml`（`10`）
- `data/benchmark_root/基本教育/引导式讲题/config_guided_task.yaml`（`15`）

`configs/basic_education.yaml` 负责把这些正式 benchmark 文件绑定到内部运行时：

- `runtime_python: python`
- `runtime_cli_module: elbench.basic_education_runtime.cli.main`
- 被测模型和可选 judge 模型从 `configs/models.yaml` 获取

执行：

```bash
python scripts/run_benchmark.py run --model-id <你的模型ID> --module 基本教育 --run-id basic-education-run
```

注意：`基本教育` 需要真实 API 模型配置。`mock.*` 仅用于单轮链路和 judge 路径的本地验证，不适用于内部多轮运行时。

## 测试

```bash
python -m unittest tests.test_basic_education_bridge tests.test_registry_and_loaders tests.test_judges tests.test_response_format_retry
```

`tests/` 是需要长期保留的正式目录，不是临时目录。

## 配置面

### `configs/models.yaml`

定义被测模型和 judge 模型实例，包括 timeout、retry、rate limit 和 provider kwargs。

### `configs/providers.yaml`

定义 provider adapter 注册表和默认能力。

当前内置：

- `mock`
- `openai_compatible`

### `configs/judges.yaml`

定义 task 到判分方式的路由：

- `rule`
- `llm`

### `configs/basic_education.yaml`

定义内部 `basic_education_runtime` 的场景级执行配置。它是补充配置，不替代注册表。

## 如何扩展

### 新增 provider

1. 在 `src/elbench/providers/` 下实现 adapter
2. 在 `configs/providers.yaml` 注册
3. 在 `configs/models.yaml` 中补具体模型

### 新增 benchmark 文件

1. 把数据放到 `data/benchmark_root/`
2. 在 `configs/file_registry.yaml` 注册
3. 在 `configs/field_mappings.yaml` 补字段映射
4. 在 `configs/judges.yaml` 补判分路由
5. 增加或复用测试

### 新增未来模块

ELBench 已经为后续模块预留了空间。标准路径仍然是：

1. 增加模块注册
2. 增加文件注册
3. 增加字段映射
4. 增加 judge 路由
5. 只有配置表达不了时，才补任务级代码

原则上不需要重写主 runner。

## 团队维护

团队维护规范统一见：

- `docs/TEAM_MAINTENANCE_GUIDE.zh-CN.md`

其中会明确每个保留目录的职责、哪些路径属于运行时产物、哪些内容不该提交进仓库。

## 当前状态

已完成：

- 配置系统
- 文件注册表
- JSONL / XLSX / YAML loader
- 统一 sample/result schema
- provider 抽象层
- 并发 runner
- 重试与断点续跑
- 原始输出 / 判分结果 / 汇总 / 日志
- 客观题规则 judge
- 主观题 `LLM-as-a-Judge`
- 基于内部运行时模块的基本教育桥接

仍然刻意保留为未定稿状态的部分：

- 面向所有厂商的生产级 adapter
- 主观题 judge rubric 和 prompt 的最终版本
- 当前已注册文件之外的未来模块完整接入

## License

发布前请补充你希望使用的许可证。
