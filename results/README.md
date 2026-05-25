# 正式结果目录

`results/` 只保存审核后、适合提交进 Git 的正式结果包。

- 全量运行产物仍然留在本地 `outputs/`。
- 结果包命名规则：`<model_id>-<scope>-<YYYYMMDD>[-revN]`
- 详细规范见 `../docs/RESULT_STORAGE_SPEC.zh-CN.md`

## 当前结果包

- `innospark-235b-standard-20260424/`
  - 来源 `run_id`: `full-standard-innospark-235b-20260424`
  - 范围：标准 benchmark，不含 `basic_education`
  - 规范文件：`README.md`、`manifest.json`、`summary.json`
