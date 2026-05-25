# InnoSpark-235B Standard Benchmark

- `run_id`: `full-standard-innospark-235b-20260424`
- `model_id`: `innospark-235b`
- `scope`: standard benchmarks only, not `basic_education`
- `finished_at`: `2026-04-27 10:48:59`

## Final Counts

- `total_judged`: `2524`
- `total_failures`: `72`
- `note`: historical failure records from the first run remain in `outputs/logs/.../innospark-235b.failures.jsonl`; after installing missing judge dependencies, the resume run only added `2` new failures, both `ResponseFormatError`

## Validity Warning

- `ceval_sampled.jsonl` and `mmlu_pro_sampled.jsonl` are not reliable in this snapshot.
- Root cause: the pre-fix loader generated colliding `sample_id` values across subjects, so checkpoint resume skipped distinct questions as if they were duplicates.
- Impact: `ceval` shows `11/208` judged and `mmlu_pro` shows `22/196` judged in `summary.json`; do not cite these two subsets until the benchmark is rerun with the fixed loader.

## Key Metrics

- `安全可信`: `1000` judged, `pass_rate=0.342`
- `高阶育人`: `998` judged, `pass_rate=0.7545`
- `通用模型`: `526` judged, `pass_rate=0.5228`
- `ifeval_sampled.jsonl`: `200` judged, `pass_rate=0.795`
- `highlevel_edu`: `500/500` pass

## Canonical Artifact

- Machine-readable manifest: `manifest.json`
- Machine-readable summary: `summary.json`
- Source outputs: `outputs/{summaries,judged_results,logs}/full-standard-innospark-235b-20260424/`
- Full local outputs remain under `outputs/` and are intentionally Git-ignored
