"""Application ports (interfaces).

Following the Dependency Inversion Principle, the application layer depends on
these abstractions, never on concrete infrastructure. Adapters (in-memory,
SQLite, later Postgres) implement them. We use ``typing.Protocol`` for
structural typing so adapters need not inherit anything.
"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol

from nirvacore.domain.attendance import AttendanceRecord
from nirvacore.domain.employee import Employee
from nirvacore.domain.ids import AttendanceId, EmployeeId, SiteId
from nirvacore.domain.site import Site


class Clock(Protocol):
    """Abstracts 'now' so use cases are deterministic under test."""

    def now(self) -> datetime: ...


class EmployeeRepository(Protocol):
    def add(self, employee: Employee) -> None: ...
    def get(self, employee_id: EmployeeId) -> Employee | None: ...
    def save(self, employee: Employee) -> None: ...
    def list_active(self) -> list[Employee]: ...


class SiteRepository(Protocol):
    def add(self, site: Site) -> None: ...
    def get(self, site_id: SiteId) -> Site | None: ...
    def save(self, site: Site) -> None: ...
    def list_active(self) -> list[Site]: ...


class AttendanceRepository(Protocol):
    def add(self, record: AttendanceRecord) -> None: ...
    def get(self, record_id: AttendanceId) -> AttendanceRecord | None: ...
    def save(self, record: AttendanceRecord) -> None: ...
    def find_open_for_employee(
        self, employee_id: EmployeeId
    ) -> AttendanceRecord | None: ...
    def list_between(
        self, start: datetime, end: datetime
    ) -> list[AttendanceRecord]: ...
