"""Characterization tests for tax_report — VALID-quarter behavior only.

Scope (ME-02 / IMP-A-P1-004): this harness locks in current behavior of
quarterly(), annual() and vat_check() for valid quarters (1-4) and valid
years, against a temporary, isolated SQLite database — never the shared
data/listo.db or any per-user database.

It does NOT decide or implement the invalid-quarter policy tracked in
Nirvasell issue #22 ("DRAFT: tax_report quarterly invalid-quarter policy").
That issue is explicitly non-binding pending an owner decision (A/B/C) and
is out of scope here.

It also does NOT fix the expenses-table defect this harness discovered
(see test_quarterly_with_real_expenses_schema_raises_missing_expense_date_
column below) — that is a separate, previously undocumented correctness
bug, unrelated to #22, and fixing it is a behavior change outside this
slice's authorization. The tests below characterize it as-is so a future
intentional fix has a baseline to diff against.

Runs with the plain interpreter (no pytest required)::

    python3 test_tax_report_quarterly.py

...and is also pytest-discoverable (def test_*).
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import types
from contextlib import contextmanager
from pathlib import Path

# db.py hard-imports pandas for CSV/dataframe helpers (upsert_products,
# fetch_products, fetch_content) that this harness never touches. Stub it
# only when pandas isn't installed, so the harness adds no new hard
# dependency beyond what the module under test already needs to import.
if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        _fake_pandas = types.ModuleType("pandas")
        _fake_pandas.DataFrame = type("DataFrame", (), {})
        _fake_pandas.notna = lambda x: x is not None
        sys.modules["pandas"] = _fake_pandas

sys.path.insert(0, str(Path(__file__).parent))

import db  # noqa: E402
import tax_report as tr  # noqa: E402


@contextmanager
def isolated_db():
    """Point db.conn() at a throw-away SQLite file for the duration of the
    block, then restore the original path. Never touches real user data."""
    tmpdir = Path(tempfile.mkdtemp(prefix="nirvasell_tax_report_test_"))
    orig_data, orig_path = db.DATA, db.DB_PATH
    db.DATA, db.DB_PATH = tmpdir, tmpdir / "test.db"
    try:
        db.init()
        yield
    finally:
        db.DATA, db.DB_PATH = orig_data, orig_path
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---- synthetic fixtures ----------------------------------------------------
# Table DDL below is copied verbatim from returns.py/expenses.py (not from
# tax_report.py's assumptions) so the harness proves what the REAL schema
# looks like, not what tax_report.py hopes it looks like. Rows are inserted
# with raw SQL rather than expenses.add()/returns.add() because those helpers
# have their own unrelated bug (`Connection.lastrowid` does not exist in
# Python's sqlite3 module) — out of scope for this slice.

def _init_returns_table():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id    TEXT DEFAULT '',
                sku         TEXT DEFAULT '',
                platform    TEXT DEFAULT '',
                reason      TEXT DEFAULT 'other',
                refund_amount REAL DEFAULT 0,
                shipping_cost REAL DEFAULT 0,
                note        TEXT DEFAULT '',
                return_date TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)


def _init_expenses_table():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                category    TEXT NOT NULL DEFAULT 'other',
                amount      REAL NOT NULL DEFAULT 0,
                note        TEXT DEFAULT '',
                platform    TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)


def _insert_order(order_id, sku, platform, unit_price, qty, total, order_date, status="paid"):
    with db.conn() as c:
        c.execute(
            "INSERT INTO orders (order_id, sku, platform, qty, unit_price, total_price, "
            "order_date, status) VALUES (?,?,?,?,?,?,?,?)",
            (order_id, sku, platform, qty, unit_price, total, order_date, status),
        )


def _insert_return(order_id, sku, platform, refund_amount, return_date):
    with db.conn() as c:
        c.execute(
            "INSERT INTO returns (order_id, sku, platform, reason, refund_amount, "
            "shipping_cost, note, return_date) VALUES (?,?,?,?,?,0,'',?)",
            (order_id, sku, platform, "other", refund_amount, return_date),
        )


def _insert_expense(date, category, amount):
    with db.conn() as c:
        c.execute(
            "INSERT INTO expenses (date, category, amount) VALUES (?,?,?)",
            (date, category, amount),
        )


# ---- vat_check() / stats(): the entry points that currently work ----------
# quarterly()/annual() never reach a `return` in any reachable DB state (see
# below) — vat_check() only touches `orders`, whose real columns match its
# query, so it is characterized here as correct, working current behavior.

def test_vat_check_sums_only_non_cancelled_non_returned_orders():
    with isolated_db():
        _insert_order("O1", "SKU1", "shopee", 500, 2, 1000, "2026-01-05", "paid")
        _insert_order("O2", "SKU2", "lazada", 300, 1, 300, "2026-02-10", "shipped")
        _insert_order("O3", "SKU3", "shopee", 999, 1, 999, "2026-03-01", "cancelled")
        _insert_order("O4", "SKU4", "tiktok", 100, 1, 100, "2026-03-02", "returned")
        result = tr.vat_check(2026)
        assert result["revenue"] == 1300.0, result


def test_vat_check_requires_vat_at_threshold():
    with isolated_db():
        _insert_order("O1", "SKU1", "shopee", 1_800_000, 1, 1_800_000, "2026-05-01")
        result = tr.vat_check(2026)
        assert result["requires_vat"] is True, result
        assert result["remaining_headroom"] == 0.0, result
        assert result["pct_of_threshold"] == 100.0, result


def test_vat_check_headroom_below_threshold():
    with isolated_db():
        _insert_order("O1", "SKU1", "shopee", 900_000, 1, 900_000, "2026-05-01")
        result = tr.vat_check(2026)
        assert result["requires_vat"] is False, result
        assert result["remaining_headroom"] == 900_000.0, result
        assert result["pct_of_threshold"] == 50.0, result


def test_vat_check_ignores_other_years():
    with isolated_db():
        _insert_order("O1", "SKU1", "shopee", 500, 1, 500, "2025-12-31")
        _insert_order("O2", "SKU2", "shopee", 700, 1, 700, "2027-01-01")
        result = tr.vat_check(2026)
        assert result["revenue"] == 0.0, result


def test_stats_wraps_vat_check_for_current_year():
    from datetime import datetime
    with isolated_db():
        _insert_order("O1", "SKU1", "shopee", 400, 1, 400, f"{datetime.now().year}-01-01")
        result = tr.stats()
        assert result["ytd_revenue"] == 400.0, result
        assert result["vat_required"] is False, result


# ---- quarterly() / annual(): characterizes the CURRENT (broken) state -----
# Every case below is deterministic and data-independent: the failure comes
# from table/column shape, not from the quarter number or the row contents.
# Reproduced 2026-09-05 against synthetic data with the real returns.py /
# expenses.py schema (see _init_returns_table / _init_expenses_table above).

VALID_QUARTERS = (1, 2, 3, 4)


def test_quarterly_fresh_db_raises_missing_returns_table():
    # Realistic state: only db.init() has ever run — a brand-new workspace
    # that opens Tax Report before ever visiting Expenses/Returns pages.
    with isolated_db():
        for q in VALID_QUARTERS:
            try:
                tr.quarterly(2026, q)
                raise AssertionError(f"quarter {q}: expected OperationalError, got a result")
            except AssertionError:
                raise
            except Exception as e:
                assert type(e).__name__ == "OperationalError", (q, e)
                assert "no such table: returns" in str(e), (q, e)


def test_quarterly_without_expenses_table_raises_missing_expenses_table():
    # Realistic state: seller has recorded returns but never opened the
    # Expenses page, so expenses.init() has never run.
    with isolated_db():
        _init_returns_table()
        for q in VALID_QUARTERS:
            try:
                tr.quarterly(2026, q)
                raise AssertionError(f"quarter {q}: expected OperationalError, got a result")
            except AssertionError:
                raise
            except Exception as e:
                assert type(e).__name__ == "OperationalError", (q, e)
                assert "no such table: expenses" in str(e), (q, e)


def test_quarterly_with_real_expenses_schema_raises_missing_expense_date_column():
    # Realistic steady state: returns AND expenses tables both exist with the
    # actual production schema. expenses.py's `expenses` table has column
    # `date`; tax_report.py's expense query filters on `expense_date`, which
    # has never existed on this table (confirmed back to the commit that
    # introduced both tax_report.py and expenses.py together). This branch
    # fires for EVERY valid quarter and any year, regardless of data —
    # quarterly()/annual() have no reachable success path once a seller has
    # ever used the Expenses page.
    with isolated_db():
        _init_returns_table()
        _init_expenses_table()
        _insert_order("O1", "SKU1", "shopee", 500, 1, 500, "2026-02-14")
        _insert_return("O1", "SKU1", "shopee", 50, "2026-02-20")
        _insert_expense("2026-02-01", "shipping", 30)
        for q in VALID_QUARTERS:
            try:
                tr.quarterly(2026, q)
                raise AssertionError(f"quarter {q}: expected OperationalError, got a result")
            except AssertionError:
                raise
            except Exception as e:
                assert type(e).__name__ == "OperationalError", (q, e)
                assert "no such column: expense_date" in str(e), (q, e)


def test_annual_inherits_first_quarter_failure():
    # annual() calls quarterly(year, 1..4) in a loop with no error handling,
    # so it fails identically to quarterly(year, 1) — nothing is returned.
    with isolated_db():
        _init_returns_table()
        _init_expenses_table()
        try:
            tr.annual(2026)
            raise AssertionError("expected OperationalError, got a result")
        except AssertionError:
            raise
        except Exception as e:
            assert type(e).__name__ == "OperationalError", e
            assert "no such column: expense_date" in str(e), e


# ---- runner -----------------------------------------------------------------
def _run() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  ✅ {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  \U0001F4A5 {t.__name__}: {type(e).__name__}: {e}")
    print(f"\ntax_report characterization tests: {passed} passed, {failed} failed ({len(tests)} total)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
