"""SQLite-backed repositories.

stdlib ``sqlite3`` only — zero external dependencies for the MVP, which is the
right call for the first 20 employees (Rule 5/6). The mapping layer is
explicit (rows <-> domain objects) so a later swap to SQLAlchemy + Postgres is
a contained change behind the same ports.

Migrations: a tiny ``schema_migrations`` table records applied versions so the
schema can evolve without data loss (see :func:`apply_migrations`).
"""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from nirvacore.domain.attendance import AttendanceRecord
from nirvacore.domain.employee import Employee, EmploymentStatus, Role
from nirvacore.domain.ids import (
    AttendanceId,
    EmployeeId,
    ShiftId,
    SiteId,
)
from nirvacore.domain.money import Money
from nirvacore.domain.shift import Shift, ShiftStatus
from nirvacore.domain.site import Site, SiteStatus

# Ordered list of (version, SQL). Append-only; never edit a shipped migration.
MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE employees (
            id         TEXT PRIMARY KEY,
            full_name  TEXT NOT NULL,
            role       TEXT NOT NULL,
            hired_on   TEXT NOT NULL,
            status     TEXT NOT NULL
        );
        CREATE TABLE sites (
            id       TEXT PRIMARY KEY,
            name     TEXT NOT NULL,
            address  TEXT NOT NULL DEFAULT '',
            status   TEXT NOT NULL
        );
        CREATE TABLE attendance (
            id           TEXT PRIMARY KEY,
            employee_id  TEXT NOT NULL REFERENCES employees(id),
            site_id      TEXT NOT NULL REFERENCES sites(id),
            clock_in     TEXT NOT NULL,
            clock_out    TEXT
        );
        CREATE INDEX idx_attendance_employee ON attendance(employee_id);
        CREATE INDEX idx_attendance_clock_in ON attendance(clock_in);
        """,
    ),
    (
        2,
        """
        ALTER TABLE employees ADD COLUMN hourly_rate TEXT NOT NULL DEFAULT '0';
        ALTER TABLE employees ADD COLUMN pay_currency TEXT NOT NULL DEFAULT 'THB';
        """,
    ),
    (
        3,
        """
        CREATE TABLE shifts (
            id           TEXT PRIMARY KEY,
            employee_id  TEXT NOT NULL REFERENCES employees(id),
            site_id      TEXT NOT NULL REFERENCES sites(id),
            start        TEXT NOT NULL,
            end          TEXT NOT NULL,
            status       TEXT NOT NULL
        );
        CREATE INDEX idx_shifts_employee ON shifts(employee_id);
        CREATE INDEX idx_shifts_start ON shifts(start);
        """,
    ),
]


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    applied = {
        row["version"]
        for row in conn.execute("SELECT version FROM schema_migrations")
    }
    for version, sql in MIGRATIONS:
        if version in applied:
            continue
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (version, datetime.now(UTC).isoformat()),
        )
    conn.commit()


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


class SqliteEmployeeRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, employee: Employee) -> None:
        self._conn.execute(
            "INSERT INTO employees (id, full_name, role, hired_on, status, "
            "hourly_rate, pay_currency) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                employee.id,
                employee.full_name,
                employee.role.value,
                employee.hired_on.isoformat(),
                employee.status.value,
                str(employee.hourly_rate.amount),
                employee.hourly_rate.currency,
            ),
        )
        self._conn.commit()

    def save(self, employee: Employee) -> None:
        self._conn.execute(
            "UPDATE employees SET full_name=?, role=?, hired_on=?, status=?, "
            "hourly_rate=?, pay_currency=? WHERE id=?",
            (
                employee.full_name,
                employee.role.value,
                employee.hired_on.isoformat(),
                employee.status.value,
                str(employee.hourly_rate.amount),
                employee.hourly_rate.currency,
                employee.id,
            ),
        )
        self._conn.commit()

    def get(self, employee_id: EmployeeId) -> Employee | None:
        row = self._conn.execute(
            "SELECT * FROM employees WHERE id=?", (employee_id,)
        ).fetchone()
        return self._to_entity(row) if row else None

    def list_active(self) -> list[Employee]:
        rows = self._conn.execute(
            "SELECT * FROM employees WHERE status=? ORDER BY full_name",
            (EmploymentStatus.ACTIVE.value,),
        ).fetchall()
        return [self._to_entity(r) for r in rows]

    @staticmethod
    def _to_entity(row: sqlite3.Row) -> Employee:
        from datetime import date

        return Employee(
            id=EmployeeId(row["id"]),
            full_name=row["full_name"],
            role=Role(row["role"]),
            hired_on=date.fromisoformat(row["hired_on"]),
            hourly_rate=Money.of(row["hourly_rate"], row["pay_currency"]),
            status=EmploymentStatus(row["status"]),
        )


class SqliteSiteRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, site: Site) -> None:
        self._conn.execute(
            "INSERT INTO sites (id, name, address, status) VALUES (?, ?, ?, ?)",
            (site.id, site.name, site.address, site.status.value),
        )
        self._conn.commit()

    def save(self, site: Site) -> None:
        self._conn.execute(
            "UPDATE sites SET name=?, address=?, status=? WHERE id=?",
            (site.name, site.address, site.status.value, site.id),
        )
        self._conn.commit()

    def get(self, site_id: SiteId) -> Site | None:
        row = self._conn.execute(
            "SELECT * FROM sites WHERE id=?", (site_id,)
        ).fetchone()
        return self._to_entity(row) if row else None

    def list_active(self) -> list[Site]:
        rows = self._conn.execute(
            "SELECT * FROM sites WHERE status=? ORDER BY name",
            (SiteStatus.ACTIVE.value,),
        ).fetchall()
        return [self._to_entity(r) for r in rows]

    @staticmethod
    def _to_entity(row: sqlite3.Row) -> Site:
        return Site(
            id=SiteId(row["id"]),
            name=row["name"],
            address=row["address"],
            status=SiteStatus(row["status"]),
        )


class SqliteAttendanceRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, record: AttendanceRecord) -> None:
        self._conn.execute(
            "INSERT INTO attendance (id, employee_id, site_id, clock_in, "
            "clock_out) VALUES (?, ?, ?, ?, ?)",
            (
                record.id,
                record.employee_id,
                record.site_id,
                record.clock_in.isoformat(),
                record.clock_out.isoformat() if record.clock_out else None,
            ),
        )
        self._conn.commit()

    def save(self, record: AttendanceRecord) -> None:
        self._conn.execute(
            "UPDATE attendance SET employee_id=?, site_id=?, clock_in=?, "
            "clock_out=? WHERE id=?",
            (
                record.employee_id,
                record.site_id,
                record.clock_in.isoformat(),
                record.clock_out.isoformat() if record.clock_out else None,
                record.id,
            ),
        )
        self._conn.commit()

    def get(self, record_id: AttendanceId) -> AttendanceRecord | None:
        row = self._conn.execute(
            "SELECT * FROM attendance WHERE id=?", (record_id,)
        ).fetchone()
        return self._to_entity(row) if row else None

    def find_open_for_employee(
        self, employee_id: EmployeeId
    ) -> AttendanceRecord | None:
        row = self._conn.execute(
            "SELECT * FROM attendance WHERE employee_id=? AND clock_out IS NULL "
            "ORDER BY clock_in LIMIT 1",
            (employee_id,),
        ).fetchone()
        return self._to_entity(row) if row else None

    def list_between(
        self, start: datetime, end: datetime
    ) -> list[AttendanceRecord]:
        rows = self._conn.execute(
            "SELECT * FROM attendance WHERE clock_in >= ? AND clock_in < ? "
            "ORDER BY clock_in",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [self._to_entity(r) for r in rows]

    @staticmethod
    def _to_entity(row: sqlite3.Row) -> AttendanceRecord:
        return AttendanceRecord(
            id=AttendanceId(row["id"]),
            employee_id=EmployeeId(row["employee_id"]),
            site_id=SiteId(row["site_id"]),
            clock_in=datetime.fromisoformat(row["clock_in"]),
            clock_out=_parse_dt(row["clock_out"]),
        )


class SqliteShiftRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, shift: Shift) -> None:
        self._conn.execute(
            "INSERT INTO shifts (id, employee_id, site_id, start, end, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                shift.id,
                shift.employee_id,
                shift.site_id,
                shift.start.isoformat(),
                shift.end.isoformat(),
                shift.status.value,
            ),
        )
        self._conn.commit()

    def save(self, shift: Shift) -> None:
        self._conn.execute(
            "UPDATE shifts SET employee_id=?, site_id=?, start=?, end=?, "
            "status=? WHERE id=?",
            (
                shift.employee_id,
                shift.site_id,
                shift.start.isoformat(),
                shift.end.isoformat(),
                shift.status.value,
                shift.id,
            ),
        )
        self._conn.commit()

    def get(self, shift_id: ShiftId) -> Shift | None:
        row = self._conn.execute(
            "SELECT * FROM shifts WHERE id=?", (shift_id,)
        ).fetchone()
        return self._to_entity(row) if row else None

    def list_between(self, start: datetime, end: datetime) -> list[Shift]:
        rows = self._conn.execute(
            "SELECT * FROM shifts WHERE start < ? AND end > ? ORDER BY start",
            (end.isoformat(), start.isoformat()),
        ).fetchall()
        return [self._to_entity(r) for r in rows]

    def list_active_for_employee(
        self, employee_id: EmployeeId, start: datetime, end: datetime
    ) -> list[Shift]:
        rows = self._conn.execute(
            "SELECT * FROM shifts WHERE employee_id=? AND status=? "
            "AND start < ? AND end > ? ORDER BY start",
            (employee_id, ShiftStatus.PLANNED.value, end.isoformat(),
             start.isoformat()),
        ).fetchall()
        return [self._to_entity(r) for r in rows]

    @staticmethod
    def _to_entity(row: sqlite3.Row) -> Shift:
        return Shift(
            id=ShiftId(row["id"]),
            employee_id=EmployeeId(row["employee_id"]),
            site_id=SiteId(row["site_id"]),
            start=datetime.fromisoformat(row["start"]),
            end=datetime.fromisoformat(row["end"]),
            status=ShiftStatus(row["status"]),
        )
