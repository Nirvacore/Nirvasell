"""Shared time helpers.

All domain timestamps are timezone-aware UTC. Naive datetimes are a common
source of off-by-hours bugs in scheduling/attendance, so we reject them at the
boundary.
"""
from __future__ import annotations

from datetime import UTC, datetime


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware (UTC)")
    return value.astimezone(UTC)
