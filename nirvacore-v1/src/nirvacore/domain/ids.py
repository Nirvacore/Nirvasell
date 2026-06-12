"""Typed identifiers.

Using :func:`typing.NewType` gives us compile-time (mypy) protection against
passing, say, a ``SiteId`` where an ``EmployeeId`` is expected, with zero
runtime overhead. IDs are opaque strings (uuid4 hex) — the domain never
depends on the database's auto-increment keys.
"""
from __future__ import annotations

from typing import NewType
from uuid import uuid4

EmployeeId = NewType("EmployeeId", str)
SiteId = NewType("SiteId", str)
AttendanceId = NewType("AttendanceId", str)


def new_employee_id() -> EmployeeId:
    return EmployeeId(uuid4().hex)


def new_site_id() -> SiteId:
    return SiteId(uuid4().hex)


def new_attendance_id() -> AttendanceId:
    return AttendanceId(uuid4().hex)
