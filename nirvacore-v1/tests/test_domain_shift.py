"""Shift aggregate invariants."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from nirvacore.domain.errors import DomainError
from nirvacore.domain.ids import EmployeeId, ShiftId, SiteId
from nirvacore.domain.shift import AlreadyCancelled, Shift, ShiftStatus


def _shift(start_h: int = 8, end_h: int = 17) -> Shift:
    return Shift(
        id=ShiftId("sh1"),
        employee_id=EmployeeId("e1"),
        site_id=SiteId("s1"),
        start=datetime(2026, 6, 15, start_h, 0, tzinfo=UTC),
        end=datetime(2026, 6, 15, end_h, 0, tzinfo=UTC),
    )


def test_planned_hours() -> None:
    assert _shift(8, 17).planned_hours == Decimal("9.00")


def test_end_must_be_after_start() -> None:
    with pytest.raises(DomainError):
        _shift(17, 8)


def test_naive_datetime_rejected() -> None:
    with pytest.raises(ValueError):
        Shift(
            id=ShiftId("sh2"),
            employee_id=EmployeeId("e1"),
            site_id=SiteId("s1"),
            start=datetime(2026, 6, 15, 8, 0),  # naive
            end=datetime(2026, 6, 15, 17, 0, tzinfo=UTC),
        )


def test_cancel_is_not_repeatable() -> None:
    shift = _shift()
    shift.cancel()
    assert shift.status is ShiftStatus.CANCELLED
    assert not shift.is_active
    with pytest.raises(AlreadyCancelled):
        shift.cancel()


def test_overlap_detection() -> None:
    shift = _shift(8, 12)
    assert shift.overlaps(
        datetime(2026, 6, 15, 11, 0, tzinfo=UTC),
        datetime(2026, 6, 15, 13, 0, tzinfo=UTC),
    )
    # adjacent (touching) windows do not overlap
    assert not shift.overlaps(
        datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
        datetime(2026, 6, 15, 14, 0, tzinfo=UTC),
    )
