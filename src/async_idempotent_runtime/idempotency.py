"""Idempotency guard enforcing single-execution invariant across distributed workers."""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


class IdempotencyConflictError(Exception):
    """Raised when an operation with the same key is already running or completed with conflicting data."""


@dataclass
class IdempotencyRecord:
    key: str
    payload_hash: str
    status: str  # "IN_FLIGHT" | "COMPLETED"
    result: Optional[Any] = None
    created_at: float = 0.0


class IdempotencyGuard:
    """In-memory advisory locking & idempotency registry simulating PostgreSQL advisory lock semantics."""

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self.ttl = ttl_seconds
        self._registry: Dict[str, IdempotencyRecord] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def compute_payload_hash(self, payload: Any) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    async def execute_idempotent(self, key: str, payload: Any, coroutine_func) -> Any:
        """Executes coroutine_func once per key. Concurrent or repeated calls return cached result."""
        payload_hash = self.compute_payload_hash(payload)

        # Get or create lock for this specific key
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            record = self._registry.get(key)
            if record is not None:
                if record.payload_hash != payload_hash:
                    raise IdempotencyConflictError(
                        f"Idempotency key '{key}' was already executed with different payload hash."
                    )
                if record.status == "COMPLETED":
                    return record.result
                if record.status == "IN_FLIGHT":
                    raise IdempotencyConflictError(
                        f"Operation with key '{key}' is currently IN_FLIGHT in another worker."
                    )

            # Mark IN_FLIGHT
            self._registry[key] = IdempotencyRecord(
                key=key,
                payload_hash=payload_hash,
                status="IN_FLIGHT",
                created_at=time.time()
            )

        # Execute target function outside lock
        try:
            result = await coroutine_func()
        except Exception:
            # Clear in-flight status on failure to allow retry
            async with self._locks[key]:
                self._registry.pop(key, None)
            raise

        # Commit COMPLETED
        async with self._locks[key]:
            self._registry[key] = IdempotencyRecord(
                key=key,
                payload_hash=payload_hash,
                status="COMPLETED",
                result=result,
                created_at=time.time()
            )

        return result
