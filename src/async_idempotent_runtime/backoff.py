"""Bounded exponential jitter backoff honoring 429 Retry-After headers."""
from __future__ import annotations

import asyncio
import random
from typing import Optional


class RateLimitExceededError(Exception):
    """Raised when maximum retry budget is exhausted."""


class BoundedBackoff:
    """Calculates backoff delays with full jitter and bounds."""

    def __init__(
        self,
        base_seconds: float = 0.5,
        max_seconds: float = 30.0,
        max_retries: int = 4
    ) -> None:
        self.base = base_seconds
        self.max_sec = max_seconds
        self.max_retries = max_retries

    def compute_delay(self, attempt: int, retry_after_header: Optional[float] = None) -> float:
        if retry_after_header is not None and retry_after_header > 0:
            return min(retry_after_header, self.max_sec)

        # Exponential backoff with full jitter: Uniform(0, min(max_sec, base * 2^attempt))
        upper = min(self.max_sec, self.base * (2 ** attempt))
        return random.uniform(0.1, upper)

    async def sleep_delay(self, attempt: int, retry_after_header: Optional[float] = None) -> float:
        if attempt >= self.max_retries:
            raise RateLimitExceededError(f"Exhausted maximum retry budget of {self.max_retries} attempts.")

        delay = self.compute_delay(attempt, retry_after_header)
        await asyncio.sleep(delay)
        return delay
