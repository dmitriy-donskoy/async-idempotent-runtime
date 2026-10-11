"""Financial correctness: minor integer units (cents) and canonical UTC timestamps."""
from __future__ import annotations

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class MoneyMinorUnits:
    """Stores monetary values strictly as integers to eliminate floating point rounding errors."""
    amount_minor: int
    currency: str = "USD"

    def __post_init__(self):
        if not isinstance(self.amount_minor, int):
            raise TypeError(f"amount_minor must be int, got {type(self.amount_minor)}")
        if len(self.currency) != 3:
            raise ValueError(f"Invalid currency code: {self.currency}")

    def format_decimal(self) -> str:
        major = self.amount_minor // 100
        minor = abs(self.amount_minor % 100)
        return f"{major}.{minor:02d} {self.currency.upper()}"


class CanonicalTimestamp:
    """Standardizes all timestamps to canonical ISO-8601 UTC with microsecond precision."""

    @staticmethod
    def now_utc_iso() -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    @staticmethod
    def parse_to_utc(iso_str: str) -> datetime.datetime:
        dt = datetime.datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)
