from __future__ import annotations

import asyncio
import random

from elbench.schemas.config import RetryConfig


def is_retryable_exception(exc: Exception, retryable_status_codes: set[int]) -> bool:
    response = getattr(exc, "response", None)
    if response is None:
        return True
    status_code = getattr(response, "status_code", None)
    if status_code is None:
        return True
    return status_code in retryable_status_codes


async def sleep_before_retry(policy: RetryConfig, attempt_index: int) -> float:
    base = policy.initial_delay_seconds * (policy.backoff_multiplier ** max(0, attempt_index - 1))
    delay = min(base, policy.max_delay_seconds)
    jitter = delay * policy.jitter_ratio * random.random()
    final_delay = delay + jitter
    await asyncio.sleep(final_delay)
    return final_delay

