"""Regression test for the customer helper's inserted row identifier.

The test uses the real customer helper and SQLite connection against a uniquely
owned temporary database. It catches reading ``lastrowid`` from the connection
instead of from the insert cursor.
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
        sys.modules["pandas"] = fake_pandas

import customers
import db


@contextmanager
def isolated_db():
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_customer_rowid_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path
    try:
        db.init()
        customers.init()
        yield
    finally:
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_find_or_create_returns_insert_cursor_row_id():
    with isolated_db():
        customer_id = customers.find_or_create(
            name="Buyer One",
            phone="0800000001",
            email="buyer@example.test",
            platform="shopee",
        )

        assert customer_id == 1
        with db.conn() as connection:
            row = connection.execute(
                "SELECT id, name, phone, email, platforms FROM customers"
            ).fetchone()
        assert dict(row) == {
            "id": 1,
            "name": "Buyer One",
            "phone": "0800000001",
            "email": "buyer@example.test",
            "platforms": "shopee",
        }


if __name__ == "__main__":
    test_find_or_create_returns_insert_cursor_row_id()
    print("customer helper row-id tests: 1 passed")
