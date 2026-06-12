"""Domain invariants for the attendance aggregate."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from nirvacore.domain.attendance import AttendanceRecord
from nirvacore.domain.errors import AlreadyClockedOut, ClockOutBeforeClockIn
from nirvacore.domain.ids import AttendanceId, EmployeeId, SiteId


def _record() -> AttendanceRecord:
    return AttendanceRecord(
        id=AttendanceId("a1"),
        employee_id=EmployeeId("e1"),
        site_id=SiteId("s1"),
        clock_in=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
    )


def test_new_record_is_open() -> None:
    rec = _record()
    assert rec.is_open
    assert rec.worked_hours == Decimal("0.00")


def test_close_computes_hours() -> None:
    rec = _record()
    rec.close(datetime(2026, 6, 1, 16, 30, tzinfo=UTC))
    assert not rec.is_open
    assert rec.worked_hours == Decimal("8.50")


def test_cannot_close_twice() -> None:
    rec = _record()
    rec.close(datetime(2026, 6, 1, 16, 0, tzinfo=UTC))
    with pytest.raises(AlreadyClockedOut):
        rec.close(datetime(2026, 6, 1, 17, 0, tzinfo=UTC))


def test_clock_out_must_be_after_clock_in() -> None:
    rec = _record()
    with pytest.raises(ClockOutBeforeClockIn):
        rec.close(datetime(2026, 6, 1, 7, 0, tzinfo=UTC))


def test_naive_datetime_rejected() -> None:
    with pytest.raises(ValueError):
        AttendanceRecord(
            id=AttendanceId("a2"),
            employee_id=EmployeeId("e1"),
            site_id=SiteId("s1"),
            clock_in=datetime(2026, 6, 1, 8, 0),  # naive
        )
