"""Attendance use cases — clock in/out and timesheets.

This is the business value of the Ops MVP: a supervisor can record who worked
where, and at week's end produce hours per employee (the input to payroll and
to client billing).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from nirvacore.domain.attendance import AttendanceRecord
from nirvacore.domain.errors import (
    AlreadyClockedIn,
    EmployeeNotActive,
    NoOpenAttendance,
    NotFound,
    SiteNotActive,
)
from nirvacore.domain.ids import EmployeeId, SiteId, new_attendance_id

from .ports import (
    AttendanceRepository,
    Clock,
    EmployeeRepository,
    SiteRepository,
)


@dataclass(frozen=True, slots=True)
class TimesheetLine:
    employee_id: EmployeeId
    employee_name: str
    hours: Decimal


@dataclass(frozen=True, slots=True)
class Timesheet:
    start: datetime
    end: datetime
    lines: tuple[TimesheetLine, ...]

    @property
    def total_hours(self) -> Decimal:
        return sum((line.hours for line in self.lines), Decimal("0.00"))


class AttendanceService:
    def __init__(
        self,
        attendance: AttendanceRepository,
        employees: EmployeeRepository,
        sites: SiteRepository,
        clock: Clock,
    ) -> None:
        self._attendance = attendance
        self._employees = employees
        self._sites = sites
        self._clock = clock

    def clock_in(
        self, employee_id: EmployeeId, site_id: SiteId
    ) -> AttendanceRecord:
        employee = self._employees.get(employee_id)
        if employee is None:
            raise NotFound(f"employee {employee_id} not found")
        if not employee.is_active:
            raise EmployeeNotActive(f"employee {employee_id} is not active")

        site = self._sites.get(site_id)
        if site is None:
            raise NotFound(f"site {site_id} not found")
        if not site.is_active:
            raise SiteNotActive(f"site {site_id} is not active")

        if self._attendance.find_open_for_employee(employee_id) is not None:
            raise AlreadyClockedIn(
                f"employee {employee_id} already has an open shift"
            )

        record = AttendanceRecord(
            id=new_attendance_id(),
            employee_id=employee_id,
            site_id=site_id,
            clock_in=self._clock.now(),
        )
        self._attendance.add(record)
        return record

    def clock_out(self, employee_id: EmployeeId) -> AttendanceRecord:
        record = self._attendance.find_open_for_employee(employee_id)
        if record is None:
            raise NoOpenAttendance(
                f"employee {employee_id} has no open shift"
            )
        record.close(self._clock.now())
        self._attendance.save(record)
        return record

    def timesheet(self, start: datetime, end: datetime) -> Timesheet:
        """Aggregate worked hours per employee over [start, end)."""
        records = self._attendance.list_between(start, end)
        totals: dict[EmployeeId, Decimal] = {}
        for rec in records:
            totals[rec.employee_id] = (
                totals.get(rec.employee_id, Decimal("0.00")) + rec.worked_hours
            )
        lines: list[TimesheetLine] = []
        for employee_id, hours in totals.items():
            employee = self._employees.get(employee_id)
            name = employee.full_name if employee else str(employee_id)
            lines.append(TimesheetLine(employee_id, name, hours))
        lines.sort(key=lambda line: line.employee_name.lower())
        return Timesheet(start=start, end=end, lines=tuple(lines))
