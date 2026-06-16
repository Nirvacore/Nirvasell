"""Shift (planned assignment) aggregate.

Scheduling answers "who is *expected* to work where, and when". A
:class:`Shift` is a planned window for one employee at one site. Compared
later against attendance, it powers coverage and no-show reporting, and the
billable-hours basis for invoicing.

Invariants (enforced here):
  * planned end is strictly after planned start;
  * a cancelled shift cannot be cancelled again.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

from .errors import DomainError
from .ids import EmployeeId, ShiftId, SiteId
from .timeutil import ensure_utc

_HOURS = Decimal("0.01")


class ShiftStatus(StrEnum):
    PLANNED = "planned"
    CANCELLED = "cancelled"


class AlreadyCancelled(DomainError):
    """The shift is already cancelled."""


@dataclass(slots=True)
class Shift:
    id: ShiftId
    employee_id: EmployeeId
    site_id: SiteId
    start: datetime
    end: datetime
    status: ShiftStatus = ShiftStatus.PLANNED

    def __post_init__(self) -> None:
        self.start = ensure_utc(self.start)
        self.end = ensure_utc(self.end)
        if self.end <= self.start:
            raise DomainError("Shift end must be after start")

    @property
    def is_active(self) -> bool:
        return self.status is ShiftStatus.PLANNED

    @property
    def planned_hours(self) -> Decimal:
        seconds = Decimal((self.end - self.start).total_seconds())
        return (seconds / Decimal(3600)).quantize(_HOURS, rounding=ROUND_HALF_UP)

    def cancel(self) -> None:
        if self.status is ShiftStatus.CANCELLED:
            raise AlreadyCancelled(f"shift {self.id} already cancelled")
        self.status = ShiftStatus.CANCELLED

    def overlaps(self, start: datetime, end: datetime) -> bool:
        """Half-open interval overlap [start, end)."""
        return self.start < end and start < self.end
