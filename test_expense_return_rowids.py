"""Regression tests for expense/return insert identifiers.

These tests use the real SQLite helpers against a uniquely-owned temporary
database. They catch returning ``Connection.lastrowid`` (which does not exist)
instead of the insert cursor's row id.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import types
from contextlib import contextmanager
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        fake_pandas.notna = lambda value: value is not None
        sys.modules["pandas"] = fake_pandas

import db
import expenses
import returns


@contextmanager
def isolated_db():
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_rowids_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path
    try:
        db.init()
        expenses.init()
        returns.init()
        yield temp_dir
    finally:
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_expense_add_returns_inserted_row_id_and_increments():
    with isolated_db():
        first = expenses.add(date="2026-09-06", category="shipping", amount=10)
        second = expenses.add(date="2026-09-06", category="packaging", amount=20)
        assert first == 1
        assert second == 2
        with db.conn() as connection:
            rows = connection.execute("SELECT id, amount FROM expenses ORDER BY id").fetchall()
        assert [(row["id"], row["amount"]) for row in rows] == [(1, 10), (2, 20)]


def test_return_add_returns_inserted_row_id_and_increments():
    with isolated_db():
        first = returns.add(order_id="order-1", refund_amount=10, return_date="2026-09-06")
        second = returns.add(order_id="order-2", refund_amount=20, return_date="2026-09-06")
        assert first == 1
        assert second == 2
        with db.conn() as connection:
            rows = connection.execute("SELECT id, refund_amount FROM returns ORDER BY id").fetchall()
        assert [(row["id"], row["refund_amount"]) for row in rows] == [(1, 10), (2, 20)]


def _run() -> int:
    tests = [
        test_expense_add_returns_inserted_row_id_and_increments,
        test_return_add_returns_inserted_row_id_and_increments,
    ]
    for test in tests:
        test()
        print(f"  ✅ {test.__name__}")
    print(f"\nexpense/return row-id tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
