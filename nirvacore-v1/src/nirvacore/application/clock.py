"""Concrete clocks. The system clock for production; a fake one lives in
tests for deterministic time-travel."""
from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)
