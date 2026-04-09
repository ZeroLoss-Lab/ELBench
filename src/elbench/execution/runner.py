from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from elbench.config import load_project_config
from elbench.judges import JudgeRouter
from elbench.loaders import LoaderFactory
from elbench.persistence import CheckpointStore, JsonlWriter, OutputPaths, configure_run_logger
from elbench.providers import ProviderFactory
from elbench.registry import FileRegistry
from elbench.schemas.config import ModelConfig, ProjectConfig, RateLimitConfig, RetryConfig
from elbench.schemas.evaluation import EvalResult, FailureRecord, GenerationRequest, ModelResponse, Sample
from elbench.summary import build_summary

from .rate_limit import SlidingWindowRateLimiter
from .retry import is_retryable_exception, sleep_before_retry


@dataclass(slots=True)
class RunOptions:
    model_id: str
    run_id: str
    modules: set[str] | None = None
    subsets: set[str] | None = None
    source_files: set[str] | None = None
    dimensions: set[str] | None = None
    max_samples: int | None = None
    max_concurrency: int | None = None
    resume: bool = True
    judge_enabled: bool = True


class BenchmarkRunner:
    def __init__(self, config: ProjectConfig | None = None) -> None:
        self.config = config or load_project_config()

    async def run(self, options: RunOptions) -> dict[str, object]:
        model_config = self._get_model_config(options.model_id)
        provider_config = self.config.providers[model_config.provider_name]
        output_paths = OutputPaths.build(self.config.app.output_root, options.run_id, options.model_id)
        logger = configure_run_logger(output_paths.log_path)
        checkpoint = CheckpointStore(output_paths.checkpoint_path)
        if options.resume:
            checkpoint.load()

        registry = FileRegistry(self.config)
        resolved_items = registry.resolve(
            modules=options.modules,
            subsets=options.subsets,
            source_files=options.source_files,
        )
        samples = list(self._load_samples(resolved_items, options.dimensions, options.max_samples))
        logger.info("Resolved %s samples from %s files.", len(samples), len(resolved_items))

        raw_writer = JsonlWriter(output_paths.raw_path)
        judged_writer = JsonlWriter(output_paths.judged_path)
        failure_writer = JsonlWriter(output_paths.failures_path)
        retry_writer = JsonlWriter(output_paths.retries_path)
        judge_router = JudgeRouter(self.config)
        client = ProviderFactory.create(provider_config, model_config)

        merged_rate_limits = self._merge_rate_limits(
            self.config.app.default_run.provider_rate_limits.get(provider_config.provider_name)
            or self.config.app.default_run.provider_rate_limits.get("default")
            or RateLimitConfig(),
            provider_config.rate_limits,
            model_config.rate_limits,
        )
        if options.max_concurrency is not None:
            merged_rate_limits.max_concurrency = options.max_concurrency

        limiter = SlidingWindowRateLimiter(merged_rate_limits)
        queue: asyncio.Queue[Sample | None] = asyncio.Queue()
        for sample in samples:
            await queue.put(sample)

        worker_count = options.max_concurrency or merged_rate_limits.max_concurrency or 100
        worker_count = min(worker_count, max(1, len(samples)))
        for _ in range(worker_count):
            await queue.put(None)

        progress = {"done": 0, "failed": 0}
        tasks = [
            asyncio.create_task(
                self._worker(
                    queue=queue,
                    logger=logger,
                    checkpoint=checkpoint,
                    raw_writer=raw_writer,
                    judged_writer=judged_writer,
                    failure_writer=failure_writer,
                    retry_writer=retry_writer,
                    client=client,
                    model_config=model_config,
                    limiter=limiter,
                    judge_router=judge_router,
                    judge_enabled=options.judge_enabled,
                    progress=progress,
                )
            )
            for _ in range(worker_count)
        ]
        await asyncio.gather(*tasks)
        await client.aclose()
        await judge_router.aclose()

        summary = build_summary(output_paths.judged_path, output_paths.failures_path)
        output_paths.summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Run finished. summary_path=%s", output_paths.summary_path)
        return {
            "run_id": options.run_id,
            "summary_path": str(output_paths.summary_path),
            "raw_path": str(output_paths.raw_path),
            "judged_path": str(output_paths.judged_path),
            "failures_path": str(output_paths.failures_path),
        }

    def _load_samples(
        self,
        resolved_items: Iterable,
        dimensions: set[str] | None,
        max_samples: int | None,
    ) -> Iterable[Sample]:
        loaded = 0
        for item in resolved_items:
            loader = LoaderFactory.create(item.entry.loader_name)
            for sample in loader.iter_samples(item):
                if dimensions and sample.dimension not in dimensions:
                    continue
                yield sample
                loaded += 1
                if max_samples is not None and loaded >= max_samples:
                    return

    async def _worker(
        self,
        queue: asyncio.Queue[Sample | None],
        logger: logging.Logger,
        checkpoint: CheckpointStore,
        raw_writer: JsonlWriter,
        judged_writer: JsonlWriter,
        failure_writer: JsonlWriter,
        retry_writer: JsonlWriter,
        client,
        model_config: ModelConfig,
        limiter: SlidingWindowRateLimiter,
        judge_router: JudgeRouter,
        judge_enabled: bool,
        progress: dict[str, int],
    ) -> None:
        while True:
            sample = await queue.get()
            if sample is None:
                queue.task_done()
                return
            sample_key = self._sample_key(sample)
            if checkpoint.is_completed(sample_key):
                queue.task_done()
                continue
            try:
                result = await self._process_sample(
                    sample=sample,
                    client=client,
                    model_config=model_config,
                    limiter=limiter,
                    judge_router=judge_router,
                    judge_enabled=judge_enabled,
                    retry_writer=retry_writer,
                    checkpoint=checkpoint,
                )
                await raw_writer.write(
                    {
                        "sample_id": result.sample_id,
                        "source_file": result.source_file,
                        "module": result.module,
                        "subset": result.subset,
                        "task": result.task,
                        "dimension": result.dimension,
                        "reference": result.reference,
                        "provider_name": result.provider_name,
                        "model_id": result.model_id,
                        "model_name": result.model_name,
                        "model_response": result.model_response,
                        "latency_ms": result.latency_ms,
                        "retry_count": result.retry_count,
                        "timestamp": result.timestamp.isoformat(),
                        "judge_metadata": result.judge_metadata,
                        "raw_response": result.raw_response,
                        "metadata": result.metadata,
                    }
                )
                await judged_writer.write(result.model_dump(mode="json"))
                await checkpoint.mark_completed(sample_key)
                progress["done"] += 1
                if progress["done"] % self.config.app.default_run.log_every_n == 0:
                    logger.info("Progress: completed=%s failed=%s", progress["done"], progress["failed"])
            except Exception as exc:  # noqa: BLE001
                progress["failed"] += 1
                failure = FailureRecord(
                    sample_id=sample.sample_id,
                    source_file=sample.source_file,
                    module=sample.module,
                    subset=sample.subset,
                    provider_name=model_config.provider_name,
                    model_id=model_config.model_id,
                    retry_count=checkpoint.retry_counts.get(sample_key, 0),
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    timestamp=datetime.now(timezone.utc),
                    metadata={"dimension": sample.dimension},
                )
                await failure_writer.write(failure.model_dump(mode="json"))
                await checkpoint.mark_failed(sample_key)
                logger.exception("Sample failed: %s", sample_key)
            finally:
                queue.task_done()

    async def _process_sample(
        self,
        sample: Sample,
        client,
        model_config: ModelConfig,
        limiter: SlidingWindowRateLimiter,
        judge_router: JudgeRouter,
        judge_enabled: bool,
        retry_writer: JsonlWriter,
        checkpoint: CheckpointStore,
    ) -> EvalResult:
        request = GenerationRequest(
            prompt=sample.prompt,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            stream=bool(model_config.supports_stream),
            provider_kwargs={},
        )
        response, retry_count = await self._generate_with_retry(
            sample=sample,
            client=client,
            request=request,
            retry_policy=model_config.retry or self.config.app.default_run.retry,
            limiter=limiter,
            retry_writer=retry_writer,
            checkpoint=checkpoint,
        )
        judge = judge_router.get_judge(sample)
        judged = await judge.judge(sample, response) if judge_enabled else None
        return EvalResult(
            sample_id=sample.sample_id,
            source_file=sample.source_file,
            source_path=sample.source_path,
            module=sample.module,
            subset=sample.subset,
            task=sample.task,
            dimension=sample.dimension,
            prompt=sample.prompt,
            reference=sample.reference,
            provider_name=model_config.provider_name,
            model_id=model_config.model_id,
            model_name=model_config.model_name,
            model_response=response.text,
            judge_result=judged.judge_result if judged else None,
            score=judged.score if judged else None,
            judge_reason=judged.judge_reason if judged else None,
            latency_ms=response.latency_ms,
            retry_count=retry_count,
            timestamp=datetime.now(timezone.utc),
            metadata=sample.metadata,
            judge_metadata=judged.judge_metadata if judged else {},
            raw_response=response.raw_payload,
        )

    async def _generate_with_retry(
        self,
        sample: Sample,
        client,
        request: GenerationRequest,
        retry_policy: RetryConfig,
        limiter: SlidingWindowRateLimiter,
        retry_writer: JsonlWriter,
        checkpoint: CheckpointStore,
    ) -> tuple[ModelResponse, int]:
        attempts = retry_policy.max_attempts
        retryable_codes = set(retry_policy.retryable_status_codes)
        sample_key = self._sample_key(sample)
        for attempt in range(1, attempts + 1):
            estimated_tokens = self._estimate_tokens(request.prompt, request.max_tokens)
            await limiter.acquire(estimated_tokens=estimated_tokens)
            try:
                response = await client.generate(sample=sample, request=request)
                response.retry_count = attempt - 1
                await checkpoint.set_retry_count(sample_key, attempt - 1)
                return response, attempt - 1
            except Exception as exc:  # noqa: BLE001
                await checkpoint.set_retry_count(sample_key, attempt)
                if attempt >= attempts or not is_retryable_exception(exc, retryable_codes):
                    raise
                delay = await sleep_before_retry(retry_policy, attempt)
                await retry_writer.write(
                    {
                        "sample_id": sample.sample_id,
                        "source_file": sample.source_file,
                        "attempt": attempt,
                        "next_delay_seconds": delay,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    }
                )
            finally:
                limiter.release()
        raise RuntimeError("Retry loop exited unexpectedly")

    def _get_model_config(self, model_id: str) -> ModelConfig:
        if model_id not in self.config.models:
            available = ", ".join(sorted(self.config.models))
            raise KeyError(f"Unknown model_id={model_id!r}. Available: {available}")
        return self.config.models[model_id]

    def _merge_rate_limits(self, *configs: RateLimitConfig) -> RateLimitConfig:
        merged = RateLimitConfig()
        for config in configs:
            if config.rpm is not None:
                merged.rpm = config.rpm
            if config.tpm is not None:
                merged.tpm = config.tpm
            if config.qps is not None:
                merged.qps = config.qps
            if config.max_concurrency is not None:
                merged.max_concurrency = config.max_concurrency
        return merged

    def _sample_key(self, sample: Sample) -> str:
        return f"{sample.source_file}::{sample.sample_id}"

    def _estimate_tokens(self, prompt: str, max_tokens: int | None) -> int:
        prompt_tokens = max(1, len(prompt) // 4)
        return prompt_tokens + (max_tokens or 0)

