"""Domain errors for Nirvacore.

A single hierarchy rooted at :class:`DomainError` so the application and
interface layers can catch domain-rule violations distinctly from
infrastructure failures (DB, network). Never leak infrastructure exceptions
as domain errors and vice-versa.
"""
from __future__ import annotations


class DomainError(Exception):
    """Base class for every business-rule violation."""


class NotFound(DomainError):
    """A referenced aggregate does not exist."""


class EmployeeNotActive(DomainError):
    """Operation requires an active employee."""


class SiteNotActive(DomainError):
    """Operation requires an active site."""


class AlreadyClockedIn(DomainError):
    """Employee already has an open attendance record."""


class NoOpenAttendance(DomainError):
    """Employee has no open attendance record to close."""


class AlreadyClockedOut(DomainError):
    """Attendance record is already closed."""


class ClockOutBeforeClockIn(DomainError):
    """Clock-out time must be strictly after clock-in time."""
