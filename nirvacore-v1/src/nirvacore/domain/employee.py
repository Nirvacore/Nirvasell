"""Employee aggregate.

For a cleaning & facility-management business the employee is the heart of
operations: cleaners and supervisors assigned to client sites. The MVP keeps
the model deliberately small (Rule 5) — identity, name, role, employment
status — and grows later (pay rate, contract type, documents…).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from .errors import DomainError
from .ids import EmployeeId
from .money import Money


class EmploymentStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Role(StrEnum):
    CLEANER = "cleaner"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"


@dataclass(slots=True)
class Employee:
    id: EmployeeId
    full_name: str
    role: Role
    hired_on: date
    hourly_rate: Money = field(default_factory=Money.zero)
    status: EmploymentStatus = field(default=EmploymentStatus.ACTIVE)

    def __post_init__(self) -> None:
        if not self.full_name.strip():
            raise DomainError("Employee full_name must not be empty")
        if self.hourly_rate.amount < 0:
            raise DomainError("Employee hourly_rate must not be negative")

    @property
    def is_active(self) -> bool:
        return self.status is EmploymentStatus.ACTIVE

    def deactivate(self) -> None:
        """Idempotent: deactivating an inactive employee is a no-op."""
        self.status = EmploymentStatus.INACTIVE

    def reactivate(self) -> None:
        self.status = EmploymentStatus.ACTIVE
