"""SQLite adapter round-trip + migration tests."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from nirvacore.application.clock import SystemClock
from nirvacore.domain.employee import Role
from nirvacore.infrastructure import sqlite as sql
from nirvacore.interface.container import build_container


@pytest.fixture
def conn():  # type: ignore[no-untyped-def]
    c = sql.connect(":memory:")
    sql.apply_migrations(c)
    yield c
    c.close()


def test_migrations_are_idempotent() -> None:
    c = sql.connect(":memory:")
    sql.apply_migrations(c)
    sql.apply_migrations(c)  # second run must be a no-op, not an error
    versions = [
        row["version"] for row in c.execute("SELECT version FROM schema_migrations")
    ]
    assert versions == [v for v, _ in sql.MIGRATIONS]
    c.close()


def test_employee_round_trip(conn) -> None:  # type: ignore[no-untyped-def]
    repo = sql.SqliteEmployeeRepository(conn)
    from nirvacore.domain.employee import Employee
    from nirvacore.domain.ids import new_employee_id

    emp = Employee(
        id=new_employee_id(),
        full_name="Somchai P.",
        role=Role.SUPERVISOR,
        hired_on=datetime(2026, 6, 1, tzinfo=UTC).date(),
    )
    repo.add(emp)
    loaded = repo.get(emp.id)
    assert loaded is not None
    assert loaded.full_name == "Somchai P."
    assert loaded.role is Role.SUPERVISOR


def test_full_flow_through_container(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db = str(tmp_path / "ops.db")
    c = build_container(db, clock=SystemClock())
    emp = c.employees.hire("Somchai P.", Role.CLEANER)
    site = c.sites.register("ABC Tower", "123 Sukhumvit")

    rec = c.attendance.clock_in(emp.id, site.id)
    assert rec.is_open
    closed = c.attendance.clock_out(emp.id)
    assert not closed.is_open
    assert closed.worked_hours >= Decimal("0.00")

    # Persistence survives a fresh container on the same file.
    c2 = build_container(db, clock=SystemClock())
    assert any(e.id == emp.id for e in c2.employees.list_active())
