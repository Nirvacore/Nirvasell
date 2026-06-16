"""Scheduling use cases — plan who works where, and when.

Guards: the employee and site must be active, and an employee may not have two
overlapping planned shifts. The roster lists the plan for a period (the basis
for coverage and, later, plan-vs-actual variance against attendance).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from nirvacore.domain.errors import (
    DomainError,
    EmployeeNotActive,
    NotFound,
    SiteNotActive,
)
from nirvacore.domain.ids import EmployeeId, ShiftId, SiteId, new_shift_id
from nirvacore.domain.shift import Shift

from .ports import (
    EmployeeRepository,
    ShiftRepository,
    SiteRepository,
)


class ShiftOverlap(DomainError):
    """The employee already has a planned shift overlapping this window."""


@dataclass(frozen=True, slots=True)
class RosterLine:
    shift: Shift
    employee_name: str
    site_name: str


@dataclass(frozen=True, slots=True)
class Roster:
    start: datetime
    end: datetime
    lines: tuple[RosterLine, ...]

    @property
    def planned_hours(self) -> Decimal:
        return sum(
            (line.shift.planned_hours for line in self.lines), Decimal("0.00")
        )


class ScheduleService:
    def __init__(
        self,
        shifts: ShiftRepository,
        employees: EmployeeRepository,
        sites: SiteRepository,
    ) -> None:
        self._shifts = shifts
        self._employees = employees
        self._sites = sites

    def schedule(
        self,
        employee_id: EmployeeId,
        site_id: SiteId,
        start: datetime,
        end: datetime,
    ) -> Shift:
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

        # Construct first so domain invariants (end > start, UTC) run early.
        shift = Shift(
            id=new_shift_id(),
            employee_id=employee_id,
            site_id=site_id,
            start=start,
            end=end,
        )

        existing = self._shifts.list_active_for_employee(
            employee_id, shift.start, shift.end
        )
        for other in existing:
            if other.overlaps(shift.start, shift.end):
                raise ShiftOverlap(
                    f"employee {employee_id} already scheduled "
                    f"{other.start.isoformat()}–{other.end.isoformat()}"
                )

        self._shifts.add(shift)
        return shift

    def cancel(self, shift_id: ShiftId) -> Shift:
        shift = self._shifts.get(shift_id)
        if shift is None:
            raise NotFound(f"shift {shift_id} not found")
        shift.cancel()
        self._shifts.save(shift)
        return shift

    def roster(self, start: datetime, end: datetime) -> Roster:
        lines: list[RosterLine] = []
        for shift in self._shifts.list_between(start, end):
            if not shift.is_active:
                continue
            employee = self._employees.get(shift.employee_id)
            site = self._sites.get(shift.site_id)
            lines.append(
                RosterLine(
                    shift=shift,
                    employee_name=(
                        employee.full_name if employee else str(shift.employee_id)
                    ),
                    site_name=site.name if site else str(shift.site_id),
                )
            )
        lines.sort(key=lambda line: (line.shift.start, line.employee_name.lower()))
        return Roster(start=start, end=end, lines=tuple(lines))
