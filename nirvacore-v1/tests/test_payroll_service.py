"""Payroll use-case tests — hours × rate, with in-memory adapters."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from nirvacore.application.attendance_service import AttendanceService
from nirvacore.application.employee_service import EmployeeService
from nirvacore.application.payroll_service import PayrollService
from nirvacore.application.site_service import SiteService
from nirvacore.domain.employee import Role
from nirvacore.domain.money import Money
from nirvacore.infrastructure.memory import (
    InMemoryAttendanceRepository,
    InMemoryEmployeeRepository,
    InMemorySiteRepository,
)
from tests.conftest import FakeClock


def test_payroll_computes_gross_per_employee() -> None:
    clock = FakeClock()
    employees_repo = InMemoryEmployeeRepository()
    sites_repo = InMemorySiteRepository()
    attendance_repo = InMemoryAttendanceRepository()

    attendance = AttendanceService(
        attendance_repo, employees_repo, sites_repo, clock
    )
    employees = EmployeeService(employees_repo, clock)
    sites = SiteService(sites_repo)
    payroll = PayrollService(attendance, employees_repo)

    anan = employees.hire("Anan", Role.CLEANER, Money.of("60"))
    busaba = employees.hire("Busaba", Role.SUPERVISOR, Money.of("90"))
    site = sites.register("ABC Tower")

    attendance.clock_in(anan.id, site.id)
    clock.advance(hours=8)
    attendance.clock_out(anan.id)

    attendance.clock_in(busaba.id, site.id)
    clock.advance(hours=5)
    attendance.clock_out(busaba.id)

    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)
    run = payroll.run(start, end)

    by_name = {slip.employee_name: slip.gross_pay.amount for slip in run.slips}
    assert by_name == {
        "Anan": Decimal("480.00"),   # 8h * 60
        "Busaba": Decimal("450.00"),  # 5h * 90
    }
    assert run.total_gross.amount == Decimal("930.00")
    assert run.total_gross.currency == "THB"


def test_payroll_empty_period_is_zero() -> None:
    clock = FakeClock()
    employees_repo = InMemoryEmployeeRepository()
    attendance = AttendanceService(
        InMemoryAttendanceRepository(),
        employees_repo,
        InMemorySiteRepository(),
        clock,
    )
    payroll = PayrollService(attendance, employees_repo)

    run = payroll.run(
        datetime(2026, 6, 1, tzinfo=UTC), datetime(2026, 6, 2, tzinfo=UTC)
    )
    assert run.slips == ()
    assert run.total_gross.amount == Decimal("0.00")
