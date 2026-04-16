# ELBench 团队维护指南

本指南面向后续维护 `ELBench` 的团队成员，目标不是解释“这个项目做什么”，而是规定“后续应该如何安全、统一地维护这个项目”。  
本指南尤其适用于使用大模型进行 `vibe coding` 的协作场景，避免不同成员各自按个人习惯改动，导致目录、配置、judge、输出结构和主流程逐渐失控。

## 0. 核心原则
- 第一性原理：从原始需求出发，动机不清立即停止，路径非最优则直接纠正。
- 极简沟通：用简单直白的中文一次性输出，把用户当高中生，拒绝使用过多的语言混杂、术语堆砌。
- Let it crash: 发现问题尽早暴露，严禁使用任何降级、兜底、启发式补丁或非严谨通用算法的后处理补救。
- 自检与精简：每次改动后，严格执行【Review查bug然后第一性原理分析】流程，思考是否有更简单、更稳健的实现。

## 1. 维护目标

团队维护 ELBench 时，必须优先保证以下几点：

1. 配置驱动，不把数据集、模型、judge、字段名写死在主流程里。
2. 主流程稳定，新增数据、模型、judge 时尽量不改 runner 主骨架。
3. 输出结构稳定，不能因为某次重构随意改结果字段名和目录层级。
4. 可恢复、可复现，中断后能断点续跑，重复实验输出口径一致。
5. 代码边界清晰，加载、调用、判分、汇总、日志不要混写。

一句话原则：**新增能力优先走注册表、配置和适配层，不直接入侵主流程。**

## 2. 维护红线

以下做法默认禁止：

- 禁止在 `runner.py` 里直接写死某个数据文件的字段名。
- 禁止在主流程里用 `if model_name == ...` 处理某个模型特例。
- 禁止把某个 provider 的 API 参数命名泄漏到通用执行层。
- 禁止为了“先跑通”把 judge 逻辑散落到 loader、provider 或 summary 里。
- 禁止修改已有输出目录结构，例如把 `outputs/raw_responses/` 改成别的层级。
- 禁止直接改原始 benchmark 数据文件内容，除非是数据本身确有错误并已达成团队共识。
- 禁止把 `outputs/`、缓存文件、临时实验结果提交到 git。

## 3. 标准维护流程

团队成员做任何改动时，建议统一按以下顺序操作：

1. 先看 `README.md` 和本指南，确认当前架构约束。
2. 明确本次变更属于哪一类：
   - 新增评测数据
   - 调整字段映射
   - 新增模型/provider
   - 调整 judge
   - 调整执行/并发/日志
   - 改 summary 或输出格式
3. 优先检查是否可以只改配置。
4. 如果必须改代码，优先改最靠边界的层，不直接改主流程。
5. 改动后至少执行一次单测和一次 smoke run。
6. 提交前确认输出格式没有被意外破坏。

## 4. 目录与文件职责表

下表是后续维护最常用的定位表。看到需求后，先用这张表确定应该改哪里。

| 路径 | 作用 | 什么时候改 | 注意事项 |
|---|---|---|---|
| `README.md` | 英文默认首页说明 | 项目能力、结构、使用方法变化时 | 保持对外描述准确，不夸大未完成能力 |
| `README.zh-CN.md` | 中文说明 | 与英文 README 同步更新时 | 与英文版保持口径一致 |
| `docs/TEAM_MAINTENANCE_GUIDE.zh-CN.md` | 团队维护规范 | 团队流程、约束、协作方式变化时 | 属于团队内规范文档 |
| `pyproject.toml` | 包名、依赖、命令入口 | 增加依赖、改 CLI 命令、改包名时 | 变更后要重新验证 `pip install -e .` |
| `.gitignore` | 忽略规则 | 新增缓存目录、实验输出目录时 | 不要把数据目录误忽略 |
| `configs/app.yaml` | 全局项目配置 | 改 data root、output root、默认并发、默认 retry 时 | 是全局默认值，不放 task 特化逻辑 |
| `configs/module_registry.yaml` | 模块注册表 | 新增一级 benchmark 模块时 | 模块名应稳定，避免频繁改名 |
| `configs/file_registry.yaml` | 文件注册表 | 新增 benchmark 文件、调整文件归属时 | 文件到 module/subset/task 的映射在这里维护 |
| `configs/field_mappings.yaml` | 字段映射配置 | 原始数据 schema 变化，或新增数据文件时 | 原始字段变化优先改这里，不改主流程 |
| `configs/providers.yaml` | provider 注册表 | 新增 provider adapter 时 | 描述 provider 能力和默认限制，不写具体模型实例 |
| `configs/models.yaml` | 模型注册表 | 新增被测模型或 judge 模型时 | 单模型的 timeout/retry/rate limit 在这里配 |
| `configs/judges.yaml` | judge 路由配置 | 调整 task 用 rule 还是 llm judge 时 | task 到 judge 策略的唯一入口 |
| `configs/basic_education.yaml` | 基本教育（ELMES）桥接配置 | 调整 45 题场景、ELMES 路径、模板映射时 | 基本教育模块走外部桥接，不走 `file_registry` |
| `third_party/elmes/` | 内置 ELMES 源码 | 升级 ELMES 版本、修复 ELMES 兼容问题时 | 这是 vendored 依赖，默认由基本教育桥接器调用 |
| `data/benchmark_root/` | benchmark 数据根目录 | 新增或整理数据文件时 | 必须按模块和子集分类，不要散落在根目录 |
| `data/benchmark_root/安全可信/` | 安全可信模块数据 | 安全可信数据更新时 | 目录名与注册表保持一致 |
| `data/benchmark_root/高阶育人/` | 高阶育人模块数据 | 高阶育人数据更新时 | `edu/` 与 `omni/` 子目录要稳定 |
| `scripts/run_benchmark.py` | 脚本入口 | 很少需要改 | 通常只作为入口代理，不放业务逻辑 |
| `src/elbench/cli.py` | CLI 参数入口 | 新增命令或参数时 | CLI 只做参数转发，不写业务实现 |
| `src/elbench/config/loader.py` | 配置加载器 | 新增配置文件或配置 schema 时 | 所有 yaml 配置统一从这里装载 |
| `src/elbench/schemas/config.py` | 配置 schema | 新配置项、新注册表结构时 | 这里定义配置的数据契约 |
| `src/elbench/schemas/evaluation.py` | Sample/Result/Judge schema | 改内部 sample/result 结构时 | 输出字段改动会影响全链路，慎改 |
| `src/elbench/registry/file_registry.py` | 文件解析与路径定位 | 文件发现逻辑变化时 | 不要把业务字段解析写进 registry |
| `src/elbench/loaders/base.py` | loader 抽象基类 | 一般不常改 | 改这里通常意味着 loader 接口变更 |
| `src/elbench/loaders/jsonl_loader.py` | JSONL 解析 | JSONL 读取策略变化时 | 只负责解析，不负责 task 业务 |
| `src/elbench/loaders/xlsx_loader.py` | XLSX 解析 | Excel 读取逻辑变化时 | 只负责表格读取 |
| `src/elbench/loaders/normalizer.py` | 统一 sample 归一化 | sample 构造规则变化时 | 字段映射最终在这里落地 |
| `src/elbench/loaders/resolvers.py` | 特殊字段解析 | `dimension` 等派生字段需要特化时 | 优先在这里扩展 resolver |
| `src/elbench/providers/base.py` | 模型客户端抽象 | provider 接口设计调整时 | 主流程依赖这里的统一接口 |
| `src/elbench/providers/factory.py` | provider 工厂 | 新增 provider class 时 | 新 provider 要在这里注册 |
| `src/elbench/providers/openai_compatible.py` | OpenAI 兼容 provider | 新增 OpenAI-compatible 模型时 | 封装 provider 差异，不污染 runner |
| `src/elbench/providers/mock.py` | mock provider | 本地 smoke、judge 回放、占位验证时 | 不要把 mock 逻辑扩展成正式 provider 主逻辑 |
| `src/elbench/execution/runner.py` | 评测主执行器 | 执行调度、结果落盘、judge 串联变更时 | 尽量少改，是主骨架文件 |
| `src/elbench/execution/basic_education.py` | 基本教育桥接执行器 | 调整 ELMES 调用、结果解析、桥接恢复策略时 | 只负责基本教育，不要混入通用单轮逻辑 |
| `src/elbench/execution/rate_limit.py` | 限流器 | 并发、QPS、RPM、TPM 策略变化时 | 改动会影响所有 provider |
| `src/elbench/execution/retry.py` | 重试与退避 | retry 规则变化时 | 避免把 task 特例写进这里 |
| `src/elbench/judges/router.py` | judge 路由器 | task 到 rule/llm judge 的映射变化时 | judge 分流统一在这里处理 |
| `src/elbench/judges/base.py` | judge 抽象基类 | judge 接口变化时 | 所有 judge 都依赖这个接口 |
| `src/elbench/judges/llm_judge.py` | LLM-as-a-Judge 执行器 | 主观题 judge 链路升级时 | judge model 与被测模型要保持解耦 |
| `src/elbench/judges/llm_prompting.py` | judge prompt 模板生成 | 调整主观题 rubric 时 | 主观题 prompt 优化优先改这里 |
| `src/elbench/judges/judge_safety.py` | 安全可信 judge | 调整安全可信判分规则时 | 当前既有 rule judge，也有 llm judge 路由 |
| `src/elbench/judges/judge_teaching_harm.py` | 教学安全 judge | 调整 SATAs / adversarial 规则判分时 | 客观题优先保持规则判分 |
| `src/elbench/judges/judge_highlevel.py` | 高阶育人 judge | 调整 `highlevel_edu` / `highlevel_omni` 判分时 | `omni` 是客观题，`edu` 偏主观 |
| `src/elbench/judges/placeholder.py` | 占位 judge | 框架预留、尚未实现的新 task 时 | 不能长期作为正式 judge 使用 |
| `src/elbench/persistence/writers.py` | 输出文件写入器 | 调整结果落盘格式时 | 不要随意改输出目录层级 |
| `src/elbench/persistence/checkpoint.py` | checkpoint 持久化 | 调整断点续跑策略时 | 与 resume 行为强相关 |
| `src/elbench/persistence/logging.py` | 日志初始化 | 调整日志格式和级别时 | 要保证日志可读且稳定 |
| `src/elbench/summary/aggregator.py` | 汇总统计 | 需要新增 summary 维度时 | 尽量只在 summary 层做聚合，不回写主结果 |
| `src/elbench/utils/parsing.py` | 通用解析工具 | 文本提取、JSON 提取、答案解析扩展时 | 只放通用工具，不放 task 逻辑 |
| `tests/test_registry_and_loaders.py` | 注册表和 loader smoke test | 新增 benchmark 文件或 loader 逻辑时 | 新数据接入后应补这类测试 |
| `tests/test_judges.py` | judge smoke test | 新增 judge 或改 judge 行为时 | judge 改动必须补测试 |

## 5. 后续新增评测数据的标准流程

这是最常见的维护动作。必须按顺序做。

### 场景 A：新增一个文件，但仍属于现有模块

例如新增一个 `安全可信` 子集文件。

操作顺序：

1. 将原始数据放入 `data/benchmark_root/` 下正确的模块目录。
2. 在 `configs/file_registry.yaml` 新增一条文件注册表项。
3. 在 `configs/field_mappings.yaml` 新增字段映射。
4. 如果需要新 task，在 `configs/judges.yaml` 增加 judge 配置。
5. 如果该数据的 `dimension` 需要特殊解析，在 `src/elbench/loaders/resolvers.py` 增加 resolver。
6. 如果是客观题，优先补 rule judge；如果是主观题，优先补 llm judge template 或 task-specific judge。
7. 在 `tests/` 增加最少一条 smoke test。
8. 运行：
   - `python scripts/run_benchmark.py inspect`
   - `python -m unittest tests.test_registry_and_loaders tests.test_judges`

### 场景 B：新增一个全新模块

例如未来新增 `通用模型` 或 `基本教育`。

操作顺序：

1. 在 `configs/module_registry.yaml` 中启用或新增模块。
2. 在 `data/benchmark_root/` 下建立规范目录。
3. 为每个文件补 `file_registry.yaml`。
4. 为每个文件补 `field_mappings.yaml`。
5. 为该模块的 task 补 `judges.yaml` 路由。
6. 如需新增 judge，实现 judge 类或 llm judge template。
7. 只在必要时改 `runner.py`，优先不动主流程。

补充：`基本教育` 当前是桥接模式例外。  
它通过 `configs/basic_education.yaml` 调用外部 `elmes` pipeline，再将结果转回 ELBench 标准输出。  
维护 `基本教育` 时优先改桥接配置和 `src/elbench/execution/basic_education.py`，不要强行塞进 `file_registry`。  
当前默认 ELMES 路径是仓库内置的 `third_party/elmes`。

## 6. 调整已有评测脚本的规范

### 可以直接改配置的情况

以下场景优先改配置，不要改 Python 代码：

- 文件路径变化
- 文件归属模块/子集变化
- 原始字段名变化
- 某个 task 要从 `rule` 切到 `llm`
- 模型参数、timeout、retry、限流参数变化

### 必须改代码的情况

只有在以下场景才应改 Python 代码：

- 新数据格式不是 JSONL/XLSX，必须新增 loader
- 字段解析逻辑不能靠映射表达，必须新增 resolver
- provider API 形态不同，必须新增 adapter
- judge 逻辑是全新的，配置无法表达
- summary 需要新增全新聚合逻辑

### 改主流程的要求

如果必须改 `src/elbench/execution/runner.py`，请满足：

1. 先说明为什么不能通过配置、adapter 或 judge 解决。
2. 改动前确认不会影响已有 task。
3. 改动后至少做一次全链路 smoke run。

## 7. 改进现有 judge 的规范

### 客观题

客观题优先规则判分，不要默认换成 LLM judge。

适用：

- 单选题
- 多选题
- 判断题
- 有稳定标准答案的结构化任务

优先修改位置：

- `judge_teaching_harm.py`
- `judge_highlevel.py`
- `utils/parsing.py`

### 主观题

主观题优先 `LLM-as-a-Judge`，且 judge model 必须与被测模型解耦。

优先修改位置：

- `configs/judges.yaml`
- `judges/llm_prompting.py`
- `judges/llm_judge.py`

不要做的事情：

- 不要让被测模型直接给自己打分。
- 不要把 judge prompt 写死在 runner 里。
- 不要让主观题的 rubric 分散在多个无关文件里。

## 8. 模型与 provider 接入规范

### 新增模型

如果只是新增某个 provider 下的新模型：

1. 先确认现有 adapter 是否已经支持。
2. 只改 `configs/models.yaml`。
3. 如需新的限流或 timeout，也只在该模型配置里加。

### 新增 provider

如果是全新 provider：

1. 在 `src/elbench/providers/` 新增 adapter
2. 在 `factory.py` 注册
3. 在 `configs/providers.yaml` 新增 provider
4. 在 `configs/models.yaml` 新增具体模型实例

规范要求：

- provider 差异必须封装在 adapter 内部。
- 不允许在 runner 或 judge 里写 provider-specific 参数名。

## 9. 团队使用大模型进行 vibe coding 的协作规范

这是本指南最重要的部分之一。

### 每次开始前必须给大模型的上下文

至少明确告诉模型：

- 当前项目名：`ELBench`
- 项目定位：长期维护的 benchmark 框架，不是一次性 demo
- 目录根：`data/benchmark_root/`
- 修改原则：配置驱动、不要写死 provider、不要改输出结构
- 当前 judge 策略：客观题 rule，主观题 llm judge
- 要求先看：
  - `README.md`
  - 本指南
  - 相关配置文件
  - 相关源码模块

### 对大模型的明确要求

建议每次都要求：

1. 先阅读相关配置和代码，再修改。
2. 优先改配置，不要直接侵入主流程。
3. 新增数据时同步补 `file_registry`、`field_mappings`、`judges`。
4. 改 judge 时补测试。
5. 提交前跑最小验证命令。

### 不要让大模型做的事情

- 不要让它直接重写整个框架
- 不要让它为了一个新文件重构所有目录
- 不要让它把配置合并回代码硬编码
- 不要让它随意改 README 中对外承诺
- 不要让它直接删除已有文件或覆盖数据

## 10. 每类需求的推荐修改入口

| 需求 | 优先查看/修改 |
|---|---|
| 新增 benchmark 文件 | `configs/file_registry.yaml`, `configs/field_mappings.yaml` |
| 新增模块 | `configs/module_registry.yaml`, `data/benchmark_root/`, `configs/file_registry.yaml` |
| 原始字段名变了 | `configs/field_mappings.yaml` |
| 某 task 从规则改为 llm judge | `configs/judges.yaml` |
| 新增 judge prompt | `src/elbench/judges/llm_prompting.py` |
| 新增客观题 judge | `src/elbench/judges/judge_*.py` |
| 新增 provider | `src/elbench/providers/` + `configs/providers.yaml` |
| 新增模型 | `configs/models.yaml` |
| 改并发/重试 | `configs/app.yaml`, `configs/models.yaml`, `src/elbench/execution/` |
| 改 summary 统计维度 | `src/elbench/summary/aggregator.py` |
| 改输出结构 | `src/elbench/schemas/evaluation.py`, `src/elbench/persistence/writers.py` |

## 11. 提交前检查清单

任何成员在提交前至少检查：

- [ ] 新数据是否放在 `data/benchmark_root/` 正确目录下
- [ ] `file_registry.yaml` 是否同步更新
- [ ] `field_mappings.yaml` 是否同步更新
- [ ] `judges.yaml` 是否同步更新
- [ ] 是否误改了 `outputs/` 结构
- [ ] 是否新增或更新了测试
- [ ] 是否执行了：
  - `python -m unittest tests.test_registry_and_loaders tests.test_judges`
  - `python scripts/run_benchmark.py inspect`
  - 至少一次小样本 `run`

## 12. 推荐 smoke 命令

```bash
python -m unittest tests.test_registry_and_loaders tests.test_judges
python scripts/run_benchmark.py inspect
python scripts/run_benchmark.py run --model-id mock.default --max-samples 3 --run-id smoke-test --no-resume
```

## 13. 常见错误

### 错误 1：新增数据后只改了代码，没改注册表

后果：
- 文件不会被主流程识别
- `inspect` 看不到

### 错误 2：字段名变了，直接去改 loader

正确做法：
- 先看能不能只改 `field_mappings.yaml`

### 错误 3：新增模型时去改 runner

正确做法：
- 优先改 `models.yaml`
- 必要时才新增 provider adapter

### 错误 4：主观题 judge 散落在多个文件

正确做法：
- 统一通过 `judges.yaml` 路由
- rubric 集中在 `llm_prompting.py`

### 错误 5：把实验输出提交到仓库

正确做法：
- 确保 `outputs/` 仍被 `.gitignore` 忽略

## 14. 结论

团队维护 ELBench 时，最重要的不是“谁写得快”，而是所有人都按同一套工程边界工作。  
后续无论是新增数据、增加模型、改 judge、补模块，默认都应该优先走：

**数据目录 -> 文件注册表 -> 字段映射 -> judge 配置 -> 边界层代码 -> 测试验证**

只要所有维护者都按这条路径操作，项目就能长期保持可扩展、可复现、可维护。
