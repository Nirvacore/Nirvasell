"""Use-case tests with in-memory adapters + a fake clock."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from nirvacore.application.attendance_service import AttendanceService
from nirvacore.application.employee_service import EmployeeService
from nirvacore.application.site_service import SiteService
from nirvacore.domain.employee import Role
from nirvacore.domain.errors import (
    AlreadyClockedIn,
    EmployeeNotActive,
    NoOpenAttendance,
)
from nirvacore.infrastructure.memory import (
    InMemoryAttendanceRepository,
    InMemoryEmployeeRepository,
    InMemorySiteRepository,
)
from tests.conftest import FakeClock


@pytest.fixture
def ctx() -> tuple[AttendanceService, EmployeeService, SiteService, FakeClock]:
    clock = FakeClock()
    employees_repo = InMemoryEmployeeRepository()
    sites_repo = InMemorySiteRepository()
    attendance_repo = InMemoryAttendanceRepository()
    return (
        AttendanceService(attendance_repo, employees_repo, sites_repo, clock),
        EmployeeService(employees_repo, clock),
        SiteService(sites_repo),
        clock,
    )


def test_clock_in_then_out_records_hours(ctx) -> None:  # type: ignore[no-untyped-def]
    attendance, employees, sites, clock = ctx
    emp = employees.hire("Somchai P.", Role.CLEANER)
    site = sites.register("ABC Tower")

    attendance.clock_in(emp.id, site.id)
    clock.advance(hours=8)
    rec = attendance.clock_out(emp.id)

    assert rec.worked_hours == Decimal("8.00")


def test_double_clock_in_blocked(ctx) -> None:  # type: ignore[no-untyped-def]
    attendance, employees, sites, _ = ctx
    emp = employees.hire("Somchai P.", Role.CLEANER)
    site = sites.register("ABC Tower")
    attendance.clock_in(emp.id, site.id)
    with pytest.raises(AlreadyClockedIn):
        attendance.clock_in(emp.id, site.id)


def test_clock_out_without_open_shift(ctx) -> None:  # type: ignore[no-untyped-def]
    attendance, employees, _, _ = ctx
    emp = employees.hire("Somchai P.", Role.CLEANER)
    with pytest.raises(NoOpenAttendance):
        attendance.clock_out(emp.id)


def test_inactive_employee_cannot_clock_in(ctx) -> None:  # type: ignore[no-untyped-def]
    attendance, employees, sites, _ = ctx
    emp = employees.hire("Somchai P.", Role.CLEANER)
    employees.deactivate(emp.id)
    site = sites.register("ABC Tower")
    with pytest.raises(EmployeeNotActive):
        attendance.clock_in(emp.id, site.id)


def test_timesheet_aggregates_per_employee(ctx) -> None:  # type: ignore[no-untyped-def]
    attendance, employees, sites, clock = ctx
    a = employees.hire("Anan", Role.CLEANER)
    b = employees.hire("Busaba", Role.CLEANER)
    site = sites.register("ABC Tower")

    attendance.clock_in(a.id, site.id)
    clock.advance(hours=4)
    attendance.clock_out(a.id)

    attendance.clock_in(b.id, site.id)
    clock.advance(hours=6)
    attendance.clock_out(b.id)

    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)
    ts = attendance.timesheet(start, end)

    assert ts.total_hours == Decimal("10.00")
    by_name = {line.employee_name: line.hours for line in ts.lines}
    assert by_name == {"Anan": Decimal("4.00"), "Busaba": Decimal("6.00")}
