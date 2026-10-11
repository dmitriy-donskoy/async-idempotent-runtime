"""Unit tests for async-idempotent-runtime (Idempotency, Money, Backoff)."""
import asyncio
import pytest

from async_idempotent_runtime.idempotency import IdempotencyGuard, IdempotencyConflictError
from async_idempotent_runtime.money import MoneyMinorUnits, CanonicalTimestamp
from async_idempotent_runtime.backoff import BoundedBackoff, RateLimitExceededError


@pytest.mark.asyncio
async def test_idempotency_executes_once():
    guard = IdempotencyGuard()
    call_count = 0

    async def worker():
        nonlocal call_count
        call_count += 1
        return {"status": "ok", "count": call_count}

    payload = {"account_id": "acc_123", "amount": 1000}
    res1 = await guard.execute_idempotent("tx_1", payload, worker)
    res2 = await guard.execute_idempotent("tx_1", payload, worker)

    assert call_count == 1
    assert res1 == {"status": "ok", "count": 1}
    assert res2 == res1


@pytest.mark.asyncio
async def test_idempotency_detects_payload_mutation_conflict():
    guard = IdempotencyGuard()

    async def worker():
        return "ok"

    await guard.execute_idempotent("key_abc", {"foo": "bar"}, worker)

    with pytest.raises(IdempotencyConflictError):
        # Same key, different payload
        await guard.execute_idempotent("key_abc", {"foo": "MUTATED"}, worker)


def test_money_minor_units_precision():
    m = MoneyMinorUnits(amount_minor=12550, currency="USD")
    assert m.format_decimal() == "125.50 USD"

    m_zero = MoneyMinorUnits(amount_minor=5, currency="EUR")
    assert m_zero.format_decimal() == "0.05 EUR"

    with pytest.raises(TypeError):
        MoneyMinorUnits(amount_minor=12.50)  # Must be integer


def test_canonical_timestamp_iso():
    iso_str = CanonicalTimestamp.now_utc_iso()
    dt = CanonicalTimestamp.parse_to_utc(iso_str)
    assert dt.tzinfo is not None


@pytest.mark.asyncio
async def test_bounded_backoff_exhaustion():
    backoff = BoundedBackoff(base_seconds=0.01, max_seconds=0.1, max_retries=2)

    await backoff.sleep_delay(0)
    await backoff.sleep_delay(1)

    with pytest.raises(RateLimitExceededError):
        await backoff.sleep_delay(2)
