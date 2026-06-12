"""Attendance aggregate — the core of the Ops MVP.

An :class:`AttendanceRecord` is a single shift: one employee, at one site,
clocked in at a point in time and (eventually) clocked out. The invariants
live here, not in the service layer, so they can never be bypassed:

  * a record opens with a clock-in and is "open" until closed;
  * it cannot be closed twice;
  * clock-out must be strictly after clock-in.

All times are timezone-aware UTC. Presentation layers convert to local time.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from .errors import AlreadyClockedOut, ClockOutBeforeClockIn
from .ids import AttendanceId, EmployeeId, SiteId

_HOURS = Decimal("0.01")


def _ensure_utc(value: datetime) -> datetime:
    """Reject naive datetimes — a whole class of bugs in time tracking."""
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware (UTC)")
    return value.astimezone(UTC)


@dataclass(slots=True)
class AttendanceRecord:
    id: AttendanceId
    employee_id: EmployeeId
    site_id: SiteId
    clock_in: datetime
    clock_out: datetime | None = None

    def __post_init__(self) -> None:
        self.clock_in = _ensure_utc(self.clock_in)
        if self.clock_out is not None:
            self.clock_out = _ensure_utc(self.clock_out)
            self._validate_window(self.clock_out)

    @property
    def is_open(self) -> bool:
        return self.clock_out is None

    def close(self, when: datetime) -> None:
        """Record the clock-out, enforcing the shift invariants."""
        if self.clock_out is not None:
            raise AlreadyClockedOut(f"attendance {self.id} already closed")
        when = _ensure_utc(when)
        self._validate_window(when)
        self.clock_out = when

    def _validate_window(self, end: datetime) -> None:
        if end <= self.clock_in:
            raise ClockOutBeforeClockIn(
                f"clock_out {end.isoformat()} must be after "
                f"clock_in {self.clock_in.isoformat()}"
            )

    @property
    def duration(self) -> timedelta | None:
        if self.clock_out is None:
            return None
        return self.clock_out - self.clock_in

    @property
    def worked_hours(self) -> Decimal:
        """Worked hours rounded to 2 dp. Open records count as 0 (not yet
        billable). Decimal — never float — because these feed payroll."""
        span = self.duration
        if span is None:
            return Decimal("0.00")
        hours = Decimal(span.total_seconds()) / Decimal(3600)
        return hours.quantize(_HOURS, rounding=ROUND_HALF_UP)
