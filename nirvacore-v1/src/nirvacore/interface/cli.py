"""A small, real CLI — the first usable interface for supervisors.

    nirvacore hire "Somchai P." cleaner
    nirvacore sites add "ABC Tower" "123 Sukhumvit"
    nirvacore clock-in <employee_id> <site_id>
    nirvacore clock-out <employee_id>
    nirvacore timesheet 2026-06-01 2026-06-30

Kept intentionally thin: it parses args and delegates to use cases. An HTTP
(FastAPI) adapter can be added later alongside it without touching the core.
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime

from nirvacore.domain.employee import Role
from nirvacore.domain.errors import DomainError
from nirvacore.domain.ids import EmployeeId, SiteId

from .container import build_container


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nirvacore")
    parser.add_argument("--db", default="nirvacore.db", help="SQLite file path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_hire = sub.add_parser("hire", help="Hire an employee")
    p_hire.add_argument("full_name")
    p_hire.add_argument("role", choices=[r.value for r in Role])

    sub.add_parser("employees", help="List active employees")

    p_site = sub.add_parser("sites", help="Manage sites")
    site_sub = p_site.add_subparsers(dest="site_command", required=True)
    p_site_add = site_sub.add_parser("add", help="Register a site")
    p_site_add.add_argument("name")
    p_site_add.add_argument("address", nargs="?", default="")
    site_sub.add_parser("list", help="List active sites")

    p_in = sub.add_parser("clock-in", help="Clock an employee in at a site")
    p_in.add_argument("employee_id")
    p_in.add_argument("site_id")

    p_out = sub.add_parser("clock-out", help="Clock an employee out")
    p_out.add_argument("employee_id")

    p_ts = sub.add_parser("timesheet", help="Hours per employee in a range")
    p_ts.add_argument("start", help="YYYY-MM-DD (inclusive)")
    p_ts.add_argument("end", help="YYYY-MM-DD (exclusive)")

    return parser


def _day(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    c = build_container(args.db)

    try:
        if args.command == "hire":
            emp = c.employees.hire(args.full_name, Role(args.role))
            print(f"{emp.id}\t{emp.full_name}\t{emp.role.value}")
        elif args.command == "employees":
            for emp in c.employees.list_active():
                print(f"{emp.id}\t{emp.full_name}\t{emp.role.value}")
        elif args.command == "sites":
            if args.site_command == "add":
                site = c.sites.register(args.name, args.address)
                print(f"{site.id}\t{site.name}")
            else:
                for site in c.sites.list_active():
                    print(f"{site.id}\t{site.name}\t{site.address}")
        elif args.command == "clock-in":
            rec = c.attendance.clock_in(
                EmployeeId(args.employee_id), SiteId(args.site_id)
            )
            print(f"clocked in: {rec.id} at {rec.clock_in.isoformat()}")
        elif args.command == "clock-out":
            rec = c.attendance.clock_out(EmployeeId(args.employee_id))
            print(
                f"clocked out: {rec.id} "
                f"({rec.worked_hours} h at {rec.clock_out})"
            )
        elif args.command == "timesheet":
            ts = c.attendance.timesheet(_day(args.start), _day(args.end))
            for line in ts.lines:
                print(f"{line.employee_name}\t{line.hours} h")
            print(f"TOTAL\t{ts.total_hours} h")
    except DomainError as exc:
        print(f"error: {exc}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
