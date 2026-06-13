"""Composition root — the ONE place that wires concrete adapters to use cases.

Everything above this point depends only on abstractions; here we choose the
SQLite implementations and the system clock. Swapping persistence (Postgres)
or time source is a single-file change.
"""
from __future__ import annotations

from dataclasses import dataclass

from nirvacore.application.attendance_service import AttendanceService
from nirvacore.application.clock import SystemClock
from nirvacore.application.employee_service import EmployeeService
from nirvacore.application.payroll_service import PayrollService
from nirvacore.application.ports import Clock
from nirvacore.application.site_service import SiteService
from nirvacore.infrastructure import sqlite as sql


@dataclass(slots=True)
class Container:
    employees: EmployeeService
    sites: SiteService
    attendance: AttendanceService
    payroll: PayrollService


def build_container(db_path: str, clock: Clock | None = None) -> Container:
    conn = sql.connect(db_path)
    sql.apply_migrations(conn)
    the_clock: Clock = clock or SystemClock()

    employee_repo = sql.SqliteEmployeeRepository(conn)
    site_repo = sql.SqliteSiteRepository(conn)
    attendance_repo = sql.SqliteAttendanceRepository(conn)

    attendance = AttendanceService(
        attendance_repo, employee_repo, site_repo, the_clock
    )
    return Container(
        employees=EmployeeService(employee_repo, the_clock),
        sites=SiteService(site_repo),
        attendance=attendance,
        payroll=PayrollService(attendance, employee_repo),
    )
