# Nirvacore-v1 — Ops MVP

ERP platform for a real **cleaning & facility-management** business. This is
the first vertical slice: the minimum to run daily operations for the **first
20 employees** — *employees · sites · attendance (clock in/out) · timesheets ·
payroll (gross pay) · scheduling (planned shifts & roster)*.

> ⚠️ **Separate system.** This project is self-contained and has **no coupling**
> to `nirva.sell` (the reseller app it currently shares a git branch with for
> transport only). It must live in its **own repository, `Nirvacore-v1`**. See
> [Extraction](#extraction-to-the-nirvacore-v1-repo).

## Why this slice

A cleaning business lives or dies on *who worked where, for how long*. That
single fact feeds payroll **and** client billing. Nailing attendance →
timesheets first delivers real value on day one and creates the data backbone
the rest of the ERP (payroll, invoicing, scheduling) plugs into.

## Architecture (Clean Architecture + DDD-lite)

Dependencies point **inward** only — the domain knows nothing about the
database or the CLI.

```
src/nirvacore/
├── domain/          # Entities, value objects, invariants. Pure Python, no I/O.
│   ├── employee.py  # Employee aggregate (status, role)
│   ├── site.py      # Site aggregate (client location)
│   ├── attendance.py# AttendanceRecord aggregate — shift invariants live here
│   ├── ids.py       # Typed IDs (NewType) — no mixing EmployeeId/SiteId
│   └── errors.py    # DomainError hierarchy
├── application/     # Use cases + ports (interfaces). Depends on domain only.
│   ├── ports.py     # Repository + Clock Protocols (Dependency Inversion)
│   ├── *_service.py # hire / register / clock-in / clock-out / timesheet
│   └── clock.py     # SystemClock
├── infrastructure/  # Adapters implementing the ports.
│   ├── memory.py    # In-memory repos (tests / reference)
│   └── sqlite.py    # stdlib sqlite3 repos + versioned migrations
└── interface/       # Delivery mechanisms.
    ├── container.py # Composition root — the only place wiring concretes
    └── cli.py       # Thin CLI; an HTTP/FastAPI adapter can sit beside it
```

**Principles applied:** SOLID (esp. DIP via `Protocol` ports + SRP per
service), explicit type safety (`mypy --strict`, typed IDs, `Decimal` for
hours), testability (fake clock + in-memory repos), and *smallest thing that
works* — stdlib only, zero runtime dependencies.

## Quickstart

```bash
cd nirvacore-v1
python -m pip install -e ".[dev]"

# run the checks
ruff check . && mypy && pytest

# use it
nirvacore hire "Somchai P." cleaner 60       # 60 = hourly rate (THB)
nirvacore sites add "ABC Tower" "123 Sukhumvit"
nirvacore clock-in <employee_id> <site_id>
nirvacore clock-out <employee_id>
nirvacore timesheet 2026-06-01 2026-06-30
nirvacore payroll 2026-06-01 2026-07-01      # gross pay = hours × rate
nirvacore schedule <employee_id> <site_id> 2026-06-15T08:00 2026-06-15T17:00
nirvacore roster 2026-06-15 2026-06-16       # planned shifts in a range
```

State persists to `./nirvacore.db` (override with `--db`).

## Testing & CI

- `pytest` — domain invariants, use cases (in-memory + fake clock), SQLite
  round-trip, migration idempotency, full persistence flow.
- `.github/workflows/ci.yml` runs ruff + mypy + pytest on Python 3.11 & 3.12.

## Migration & backward-compatibility considerations

- **Schema migrations** are append-only entries in `infrastructure/sqlite.py`
  (`MIGRATIONS`), tracked in a `schema_migrations` table and applied
  idempotently on startup. Never edit a shipped migration — add a new one.
- **Times are UTC, timezone-aware.** Naive datetimes are rejected at the
  aggregate boundary. Presentation converts to Asia/Bangkok.
- **Money/hours use `Decimal`**, never float — payroll-safe from day one.
- **Postgres path:** the ports isolate persistence. Moving to SQLAlchemy +
  Postgres for scale is a new adapter behind the same interfaces; the domain
  and application layers don't change.

## Roadmap (next slices, in priority order)

1. ~~**Payroll run** — turn timesheets into pay.~~ ✅ gross pay shipped
   (hours × hourly rate, `Money` value object, schema migration v2). Next:
   overtime rules, deductions, and persisted payslips.
2. ~~**Scheduling/assignments** — plan who works where.~~ ✅ planned shifts +
   roster shipped (overlap guard, schema migration v3). Next: **plan-vs-actual
   variance** (roster vs attendance → no-shows / coverage gaps).
3. **Client invoicing** — bill contracted/worked hours per site.
4. **HTTP API (FastAPI)** + auth, so mobile clock-in becomes possible.

## Extraction to the `Nirvacore-v1` repo

This folder is a complete project rooted at `nirvacore-v1/`. To move it into
its own repository (honoring "never merge systems into one repo"):

```bash
# from a clone of the branch
git subtree split --prefix=nirvacore-v1 -b nirvacore-extract
# then push that branch to the Nirvacore-v1 repo, or simply:
cp -r nirvacore-v1 /path/to/Nirvacore-v1 && cd /path/to/Nirvacore-v1 && git init
```
