# ELBench

[![English](https://img.shields.io/badge/Language-English-blue.svg)](./README.md)
[![简体中文](https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-red.svg)](./README.zh-CN.md)

一个面向教育大模型评测的配置驱动 benchmark 框架。

ELBench 不是一次性脚本，而是按长期维护的正式工程来设计的。目前重点覆盖两个模块：

- `安全可信`
- `高阶育人`

同时已经预留后续扩展空间：

- `通用模型`
- `基本教育`

## 项目概览

这套框架遵循以下几个核心原则：

- 评测流程由注册表和配置驱动，而不是靠脚本里硬编码文件逻辑。
- 模型调用统一走 provider adapter 抽象层。
- 客观题使用规则或标准答案判分。
- 主观开放题使用 `LLM-as-a-Judge`。
- 输出、日志、checkpoint、summary 使用稳定的数据结构。
- 中断后支持断点续跑。

## 当前支持范围

### 已接入的数据文件

当前已接入以下 benchmark 文件：

- `安全拒答.jsonl`
- `安全引导.jsonl`
- `安全回答.jsonl`
- `SATAs.xlsx`
- `adversarial_prompts.xlsx`
- `高阶育人-edu.jsonl`
- `高阶育人-omni.jsonl`

### 当前判分策略

客观题走规则或参考答案判分：

- `SATAs.xlsx`：多选精确集合匹配
- `高阶育人-omni.jsonl`：标准答案精确匹配

主观开放题走 `LLM-as-a-Judge`：

- `安全拒答.jsonl`
- `安全引导.jsonl`
- `安全回答.jsonl`
- `adversarial_prompts.xlsx`
- `高阶育人-edu.jsonl`

当前阶段，外部模型 API 仍然保持可插拔占位设计。仓库内提供了 `mock` provider，因此即使不接外部 API，也能在本地把整条评测链路跑通。

## 仓库结构

```text
.
├── configs/
│   ├── app.yaml
│   ├── file_registry.yaml
│   ├── field_mappings.yaml
│   ├── judges.yaml
│   ├── models.yaml
│   ├── module_registry.yaml
│   └── providers.yaml
├── data/
│   └── benchmark_root/
│       ├── 安全可信/
│       └── 高阶育人/
├── outputs/
├── scripts/
│   └── run_benchmark.py
├── src/
│   └── elbench/
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

## 核心设计

### 1. 基于注册表的数据加载

评测系统不会在主流程里写死具体文件逻辑。

- `configs/file_registry.yaml` 负责把 benchmark 文件映射到 module、subset、task、loader
- `configs/field_mappings.yaml` 负责把原始字段映射到统一内部 sample schema
- JSONL 和 XLSX loader 都会输出统一的 `Sample`

### 2. 统一 sample 数据结构

所有样本都会被归一化为统一结构，核心字段包括：

- `sample_id`
- `source_file`
- `module`
- `subset`
- `task`
- `dimension`
- `prompt`
- `reference`
- `metadata`

### 3. 模型适配层抽象

主流程不依赖某一家 API 形态。

- `ModelClient` 是统一抽象基类
- provider adapter 位于 `src/elbench/providers/`
- 后续新增 provider 时，原则上只需要补配置和 adapter，不需要改 runner

### 4. Judge 抽象

判分分成两类：

- 客观题：规则 judge
- 主观题：`LLM-as-a-Judge`

judge 策略统一在 `configs/judges.yaml` 配置。

### 5. 并发、恢复与可观测性

当前 runner 支持：

- 可配置全局并发
- provider/model 级并发限制
- 指数退避重试
- 失败日志
- 重试日志
- checkpoint 断点续跑
- 原始回答持久化
- 判分结果持久化
- 汇总统计输出

默认最大并发为 `100`。

## 输出目录

```text
outputs/
├── raw_responses/
├── judged_results/
├── summaries/
└── logs/
```

每条样本结果至少包含以下字段：

- `sample_id`
- `source_file`
- `module`
- `subset`
- `task`
- `dimension`
- `prompt`
- `reference`
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
- `metadata`

## 快速开始

### 1. 环境要求

- Python `>= 3.11`

### 2. 安装

```bash
pip install -e .
```

### 3. 查看当前 bench 文件解析结果

```bash
python scripts/run_benchmark.py inspect
```

### 4. 使用 mock provider 做本地 smoke test

```bash
python scripts/run_benchmark.py run --model-id mock.default --max-samples 3 --run-id smoke-test
```

或者在可编辑安装后：

```bash
elbench inspect
elbench run --model-id mock.default --max-samples 3 --run-id smoke-test
```

### 5. 运行单元测试

```bash
python -m unittest tests.test_registry_and_loaders tests.test_judges
```

## 配置说明

### `configs/models.yaml`

用于定义被测模型和 judge 模型。

当前示例包括：

- `mock.default`：被测 mock 模型
- `mock.judge`：judge mock 模型

### `configs/providers.yaml`

用于定义 provider adapter 与默认能力。

当前内置：

- `mock`
- `openai_compatible`

### `configs/judges.yaml`

用于定义每个 task 的判分方式：

- `rule`
- `llm`

以及对应的 judge template / judge model。

## 如何扩展

### 新增一个模型 provider

1. 在 `src/elbench/providers/` 下新增 adapter
2. 在 `configs/providers.yaml` 注册 provider
3. 在 `configs/models.yaml` 增加具体模型配置

### 新增一个 benchmark 文件

1. 在 `configs/file_registry.yaml` 增加文件注册表项
2. 在 `configs/field_mappings.yaml` 增加字段映射
3. 如有需要，在 `configs/judges.yaml` 增加 judge 配置
4. 复用或新增 judge 实现

### 新增未来模块

框架已经通过 `configs/module_registry.yaml` 为 `通用模型` 和 `基本教育` 预留位置。后续新增时，正常路径应为：

1. 增加 file registry
2. 增加 field mapping
3. 增加 judge config
4. 如有必要，增加任务级 judge 逻辑

原则上不需要重写主 runner。

## 当前状态

已完成：

- 配置系统
- 文件注册表
- JSONL/XLSX loader
- 统一 sample schema
- provider 抽象层
- 并发 runner
- 重试与断点续跑
- 原始输出/判分结果/汇总/日志
- 客观题规则 judge
- 主观题 `LLM-as-a-Judge` 执行链路

尚未最终定稿：

- 面向所有目标厂商的真实 API 接入
- 生产级 judge prompt 与 rubric
- 各主观子集更细的判分标准

## License

发布到 GitHub 前请补充你希望使用的许可证。

