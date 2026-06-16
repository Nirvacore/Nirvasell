"""Shift persistence through the SQLite-backed container (migration v3)."""
from __future__ import annotations

from datetime import UTC, datetime

from nirvacore.application.clock import SystemClock
from nirvacore.domain.employee import Role
from nirvacore.interface.container import build_container


def test_scheduled_shift_survives_new_container(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db = str(tmp_path / "ops.db")
    c = build_container(db, clock=SystemClock())
    emp = c.employees.hire("Somchai P.", Role.CLEANER)
    site = c.sites.register("ABC Tower")
    shift = c.schedule.schedule(
        emp.id,
        site.id,
        datetime(2026, 6, 15, 8, 0, tzinfo=UTC),
        datetime(2026, 6, 15, 17, 0, tzinfo=UTC),
    )

    # Fresh container on the same file must read the shift back.
    c2 = build_container(db, clock=SystemClock())
    roster = c2.schedule.roster(
        datetime(2026, 6, 15, tzinfo=UTC), datetime(2026, 6, 16, tzinfo=UTC)
    )
    assert [line.shift.id for line in roster.lines] == [shift.id]
