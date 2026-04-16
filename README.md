# ELBench

[![English](https://img.shields.io/badge/Language-English-blue.svg)](./README.md)
[![简体中文](https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-red.svg)](./README.zh-CN.md)

Config-driven benchmark framework for education-focused large language model evaluation.

ELBench is designed as a long-lived engineering system rather than a one-off script. It currently focuses on two benchmark modules:

- `安全可信` / `Safety & Trustworthiness`
- `高阶育人` / `Advanced Educational Capacity`

It already reserves extension space for future modules:

- `通用模型` / `General Models`
- `基本教育` / `Basic Education`

`Basic Education` is now integrated through an external ELMES bridge runner:

- `knowledge.yaml` (10 tasks)
- `question.yaml` (10 tasks)
- `cross.yaml` (10 tasks)
- `config_guided_task.yaml` (15 tasks)

Total: `45` tasks.

ELMES is vendored inside this repository at `third_party/elmes`, so users do not need a separate ELMES repo checkout.

## Overview

The framework is built around a few stable principles:

- Benchmark execution is driven by registry and configuration, not hardcoded file logic.
- Model providers are abstracted behind a unified adapter layer.
- Objective tasks use rule-based judging.
- Subjective and open-ended tasks use `LLM-as-a-Judge`.
- Outputs, logs, checkpoints, and summaries follow stable machine-readable formats.
- Interrupted runs can resume from checkpoints.

## Current Scope

### Implemented benchmark data support

Current datasets wired into the framework:

- `安全拒答.jsonl`
- `安全引导.jsonl`
- `安全回答.jsonl`
- `SATAs.xlsx`
- `adversarial_prompts.xlsx`
- `高阶育人-edu.jsonl`
- `高阶育人-omni.jsonl`

### Current judge strategy

Objective tasks use rule-based or reference-based judging:

- `SATAs.xlsx`: exact set match
- `高阶育人-omni.jsonl`: exact answer match

Subjective or open-ended tasks use `LLM-as-a-Judge`:

- `安全拒答.jsonl`
- `安全引导.jsonl`
- `安全回答.jsonl`
- `adversarial_prompts.xlsx`
- `高阶育人-edu.jsonl`

At this stage, external API integration for judge models and evaluated models is still intentionally left pluggable. The repository includes a `mock` provider so the full pipeline can be tested locally without external API access.

## Repository Structure

```text
.
├── configs/
│   ├── app.yaml
│   ├── basic_education.yaml
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

## Core Design

### 1. Registry-driven data loading

The benchmark does not rely on ad hoc script logic for specific files.

- `configs/file_registry.yaml` maps benchmark files to module, subset, task, and loader.
- `configs/field_mappings.yaml` maps raw dataset fields into the unified internal sample schema.
- JSONL and XLSX loaders both normalize records into one internal `Sample` format.

### 2. Unified sample schema

Every loaded record is normalized into a shared structure containing:

- `sample_id`
- `source_file`
- `module`
- `subset`
- `task`
- `dimension`
- `prompt`
- `reference`
- `metadata`

### 3. Provider abstraction

The main execution flow does not depend on any specific API style.

- `ModelClient` is the abstract base interface.
- Providers live under `src/elbench/providers/`.
- New providers should be added through config plus a provider adapter, without changing the runner.

### 4. Judge abstraction

The framework separates objective and subjective evaluation:

- Rule judges for objective tasks
- `LLM-as-a-Judge` for subjective tasks

Judge behavior is configured in `configs/judges.yaml`.

### 5. Concurrency, resilience, and observability

The runner supports:

- configurable global concurrency
- provider/model-level concurrency limits
- retry with exponential backoff
- failure logging
- retry logging
- checkpoint-based resume
- raw response persistence
- judged result persistence
- summary generation

Default max concurrency is `100`.

## Output Layout

```text
outputs/
├── raw_responses/
├── judged_results/
├── summaries/
└── logs/
```

Each evaluated sample records fields such as:

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

## Quick Start

### 1. Requirements

- Python `>= 3.11`

### 2. Install

```bash
pip install -e .
```

### 3. Inspect resolved benchmark files

```bash
python scripts/run_benchmark.py inspect
```

### 4. Run a local smoke test with the mock provider

```bash
python scripts/run_benchmark.py run --model-id mock.default --max-samples 3 --run-id smoke-test
```

Or, after editable install:

```bash
elbench inspect
elbench run --model-id mock.default --max-samples 3 --run-id smoke-test
```

### 5. Run Basic Education (ELMES bridge)

Default setup already points to the vendored ELMES path in `configs/basic_education.yaml`:

- `elmes_repo_path: third_party/elmes`
- tested model and optional judge model should be configured in `configs/models.yaml`.

If you want to use a different ELMES fork, update `elmes_repo_path` accordingly.

Then run:

```bash
python scripts/run_benchmark.py run --model-id <your_model_id> --module 基本教育 --run-id basic-education-run
```

Note: the Basic Education bridge requires a real API-backed model config (`api_base` + `api_key_env`). `mock.*` models are not valid for this module.

### 6. Run unit tests

```bash
python -m unittest tests.test_basic_education_bridge tests.test_registry_and_loaders tests.test_judges
```

## Configuration Guide

### `configs/models.yaml`

Defines evaluated models and judge models.

Examples:

- `mock.default`: mock evaluated model
- `mock.judge`: mock judge model

### `configs/providers.yaml`

Defines provider adapters and default capabilities.

Current built-in adapters:

- `mock`
- `openai_compatible`

### `configs/judges.yaml`

Defines whether a task uses:

- `rule`
- `llm`

and which judge template / judge model to use.

## Extending the Framework

### Add a new model provider

1. Add a provider adapter under `src/elbench/providers/`
2. Register it in `configs/providers.yaml`
3. Add concrete model entries in `configs/models.yaml`

### Add a new benchmark file

1. Add a file registry entry in `configs/file_registry.yaml`
2. Add field mapping in `configs/field_mappings.yaml`
3. Add judge routing config in `configs/judges.yaml` if needed
4. Implement or reuse a judge

### Add a future benchmark module

The framework already reserves module space through `configs/module_registry.yaml`. To add `通用模型` or `基本教育`, the intended path is:

1. add file registry entries
2. add field mappings
3. add judge configs
4. optionally add task-specific judge logic

No main runner rewrite should be required.

## Status

Implemented:

- config system
- file registry
- JSONL/XLSX loaders
- unified sample schema
- provider abstraction
- concurrent runner
- retries and checkpoint resume
- raw/judged/summary/log outputs
- rule judges for objective tasks
- LLM-as-a-Judge execution path for subjective tasks

Not finalized yet:

- real external provider integration for all target vendors
- production judge prompts and rubrics
- full task-specific rubric refinement for all subjective subsets

## License

Add your preferred license before publishing.

