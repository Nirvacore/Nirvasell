"""Scheduling use-case tests with in-memory adapters."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from nirvacore.application.employee_service import EmployeeService
from nirvacore.application.schedule_service import ScheduleService, ShiftOverlap
from nirvacore.application.site_service import SiteService
from nirvacore.domain.employee import Role
from nirvacore.domain.errors import EmployeeNotActive
from nirvacore.infrastructure.memory import (
    InMemoryEmployeeRepository,
    InMemoryShiftRepository,
    InMemorySiteRepository,
)
from tests.conftest import FakeClock


@pytest.fixture
def ctx() -> tuple[ScheduleService, EmployeeService, SiteService]:
    clock = FakeClock()
    employees_repo = InMemoryEmployeeRepository()
    sites_repo = InMemorySiteRepository()
    shifts_repo = InMemoryShiftRepository()
    return (
        ScheduleService(shifts_repo, employees_repo, sites_repo),
        EmployeeService(employees_repo, clock),
        SiteService(sites_repo),
    )


def _at(h: int) -> datetime:
    return datetime(2026, 6, 15, h, 0, tzinfo=UTC)


def test_schedule_creates_planned_shift(ctx) -> None:  # type: ignore[no-untyped-def]
    schedule, employees, sites = ctx
    emp = employees.hire("Somchai P.", Role.CLEANER)
    site = sites.register("ABC Tower")
    shift = schedule.schedule(emp.id, site.id, _at(8), _at(17))
    assert shift.is_active
    assert shift.planned_hours == Decimal("9.00")


def test_overlapping_shift_rejected(ctx) -> None:  # type: ignore[no-untyped-def]
    schedule, employees, sites = ctx
    emp = employees.hire("Somchai P.", Role.CLEANER)
    site = sites.register("ABC Tower")
    schedule.schedule(emp.id, site.id, _at(8), _at(12))
    with pytest.raises(ShiftOverlap):
        schedule.schedule(emp.id, site.id, _at(11), _at(15))


def test_adjacent_shift_allowed(ctx) -> None:  # type: ignore[no-untyped-def]
    schedule, employees, sites = ctx
    emp = employees.hire("Somchai P.", Role.CLEANER)
    site = sites.register("ABC Tower")
    schedule.schedule(emp.id, site.id, _at(8), _at(12))
    second = schedule.schedule(emp.id, site.id, _at(12), _at(16))
    assert second.is_active


def test_cancelled_shift_frees_the_slot(ctx) -> None:  # type: ignore[no-untyped-def]
    schedule, employees, sites = ctx
    emp = employees.hire("Somchai P.", Role.CLEANER)
    site = sites.register("ABC Tower")
    first = schedule.schedule(emp.id, site.id, _at(8), _at(12))
    schedule.cancel(first.id)
    # Same window can now be re-scheduled.
    again = schedule.schedule(emp.id, site.id, _at(8), _at(12))
    assert again.is_active


def test_inactive_employee_cannot_be_scheduled(ctx) -> None:  # type: ignore[no-untyped-def]
    schedule, employees, sites = ctx
    emp = employees.hire("Somchai P.", Role.CLEANER)
    employees.deactivate(emp.id)
    site = sites.register("ABC Tower")
    with pytest.raises(EmployeeNotActive):
        schedule.schedule(emp.id, site.id, _at(8), _at(12))


def test_roster_lists_and_totals(ctx) -> None:  # type: ignore[no-untyped-def]
    schedule, employees, sites = ctx
    a = employees.hire("Anan", Role.CLEANER)
    b = employees.hire("Busaba", Role.CLEANER)
    site = sites.register("ABC Tower")
    schedule.schedule(a.id, site.id, _at(8), _at(12))   # 4h
    schedule.schedule(b.id, site.id, _at(9), _at(17))   # 8h

    roster = schedule.roster(
        datetime(2026, 6, 15, tzinfo=UTC), datetime(2026, 6, 16, tzinfo=UTC)
    )
    assert roster.planned_hours == Decimal("12.00")
    assert [line.employee_name for line in roster.lines] == ["Anan", "Busaba"]
    assert roster.lines[0].site_name == "ABC Tower"
