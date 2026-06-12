"""In-memory repositories — used by the fast unit-test suite and as a
reference implementation of the ports. No persistence.
"""
from __future__ import annotations

from datetime import datetime

from nirvacore.domain.attendance import AttendanceRecord
from nirvacore.domain.employee import Employee
from nirvacore.domain.ids import AttendanceId, EmployeeId, SiteId
from nirvacore.domain.site import Site


class InMemoryEmployeeRepository:
    def __init__(self) -> None:
        self._items: dict[EmployeeId, Employee] = {}

    def add(self, employee: Employee) -> None:
        self._items[employee.id] = employee

    def get(self, employee_id: EmployeeId) -> Employee | None:
        return self._items.get(employee_id)

    def save(self, employee: Employee) -> None:
        self._items[employee.id] = employee

    def list_active(self) -> list[Employee]:
        return [e for e in self._items.values() if e.is_active]


class InMemorySiteRepository:
    def __init__(self) -> None:
        self._items: dict[SiteId, Site] = {}

    def add(self, site: Site) -> None:
        self._items[site.id] = site

    def get(self, site_id: SiteId) -> Site | None:
        return self._items.get(site_id)

    def save(self, site: Site) -> None:
        self._items[site.id] = site

    def list_active(self) -> list[Site]:
        return [s for s in self._items.values() if s.is_active]


class InMemoryAttendanceRepository:
    def __init__(self) -> None:
        self._items: dict[AttendanceId, AttendanceRecord] = {}

    def add(self, record: AttendanceRecord) -> None:
        self._items[record.id] = record

    def get(self, record_id: AttendanceId) -> AttendanceRecord | None:
        return self._items.get(record_id)

    def save(self, record: AttendanceRecord) -> None:
        self._items[record.id] = record

    def find_open_for_employee(
        self, employee_id: EmployeeId
    ) -> AttendanceRecord | None:
        for rec in self._items.values():
            if rec.employee_id == employee_id and rec.is_open:
                return rec
        return None

    def list_between(
        self, start: datetime, end: datetime
    ) -> list[AttendanceRecord]:
        return [
            rec
            for rec in self._items.values()
            if start <= rec.clock_in < end
        ]
