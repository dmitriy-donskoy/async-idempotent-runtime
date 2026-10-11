# ⚡ Async Idempotent Runtime

[![CI](https://github.com/dmitriy-donskoy/async-idempotent-runtime/actions/workflows/ci.yml/badge.svg)](https://github.com/dmitriy-donskoy/async-idempotent-runtime/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AsyncIO: Native](https://img.shields.io/badge/asyncio-native-purple.svg)]()
[![Tests: 100% Green](https://img.shields.io/badge/tests-100%25%20passed-brightgreen.svg)]()

> **High-assurance async execution engine designed for financial systems, third-party ingestion, and zero-duplicate transaction processing.**  
> Features distributed advisory lock semantics, payload hashing, integer minor-unit financial precision, and bounded jitter backoff honoring 429 `Retry-After`.

---

## 🚀 Core Features

1. **Idempotency Guard & Advisory Locks:**
   * Eliminates race conditions across concurrent workers.
   * Deterministic SHA-256 payload hashing ensures that replayed requests with identical keys never duplicate mutations.
   * Detects payload mutation conflicts when a caller reuses an existing key with altered parameters.
2. **Financial Minor-Unit Precision:**
   * Eradicates floating-point rounding bugs (`0.1 + 0.2 != 0.3`) by enforcing integer minor units (`amount_minor = 12550` for `$125.50`).
3. **Canonical Timezone Standardization:**
   * All timestamps are automatically parsed and normalized to UTC ISO-8601 with microsecond precision.
4. **Bounded Exponential Backoff with Jitter:**
   * Full jitter calculation preventing thundering herds against external APIs.
   * Native adherence to HTTP `Retry-After` headers and strict retry budget ceilings.

---

## 📦 Quickstart

```python
import asyncio
from async_idempotent_runtime import IdempotencyGuard, MoneyMinorUnits

async def process_payout(account_id: str, amount_cents: int):
    # Simulated critical payment execution
    return {"status": "PAID", "account": account_id, "minor": amount_cents}

async def main():
    guard = IdempotencyGuard()
    payload = {"account_id": "acc_99", "amount": 5000}

    # Worker 1 executes
    res1 = await guard.execute_idempotent("tx_key_001", payload, lambda: process_payout("acc_99", 5000))

    # Worker 2 retries with same key -> returns cached result without running process_payout again!
    res2 = await guard.execute_idempotent("tx_key_001", payload, lambda: process_payout("acc_99", 5000))

    assert res1 == res2

asyncio.run(main())
```

---

## 🧪 Testing

```bash
pytest tests -v
```

---

## 📄 License

MIT License. Authored by **Dmitriy Donskoy**.
