"""Payroll use case.

Composes the attendance timesheet (worked hours per employee) with each
employee's hourly rate to produce a :class:`Payroll`. Computing pay is a pure
read over existing data — it never mutates attendance — so it can be re-run
safely for any period.
"""
from __future__ import annotations

from datetime import datetime

from nirvacore.domain.money import DEFAULT_CURRENCY
from nirvacore.domain.payroll import Payroll, Payslip

from .attendance_service import AttendanceService
from .ports import EmployeeRepository


class PayrollService:
    def __init__(
        self,
        attendance: AttendanceService,
        employees: EmployeeRepository,
        currency: str = DEFAULT_CURRENCY,
    ) -> None:
        self._attendance = attendance
        self._employees = employees
        self._currency = currency

    def run(self, start: datetime, end: datetime) -> Payroll:
        timesheet = self._attendance.timesheet(start, end)
        slips: list[Payslip] = []
        for line in timesheet.lines:
            employee = self._employees.get(line.employee_id)
            if employee is None:
                continue
            slips.append(
                Payslip.compute(
                    employee_id=line.employee_id,
                    employee_name=line.employee_name,
                    hours=line.hours,
                    hourly_rate=employee.hourly_rate,
                )
            )
        return Payroll(
            start=start,
            end=end,
            currency=self._currency,
            slips=tuple(slips),
        )
