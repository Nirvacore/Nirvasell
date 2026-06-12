"""Site aggregate.

A *site* is a client location that must be cleaned/serviced (an office, a
mall, a hospital wing). Attendance is always recorded against a site so we
can later answer "how many labour-hours did contract X consume?".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .errors import DomainError
from .ids import SiteId


class SiteStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass(slots=True)
class Site:
    id: SiteId
    name: str
    address: str = ""
    status: SiteStatus = field(default=SiteStatus.ACTIVE)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainError("Site name must not be empty")

    @property
    def is_active(self) -> bool:
        return self.status is SiteStatus.ACTIVE

    def deactivate(self) -> None:
        self.status = SiteStatus.INACTIVE

    def reactivate(self) -> None:
        self.status = SiteStatus.ACTIVE
