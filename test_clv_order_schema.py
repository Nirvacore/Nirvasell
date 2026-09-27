"""Regression coverage for CLV against the canonical orders schema."""
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

import clv
import db


@contextmanager
def isolated_db():
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_clv_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path
    try:
        db.init()
        yield
    finally:
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_clv_aggregates_canonical_order_total_price():
    with isolated_db():
        with db.conn() as connection:
            connection.executemany(
                """
                INSERT INTO orders
                    (order_id, sku, qty, total_price, order_date, status,
                     buyer_name, buyer_phone)
                VALUES (?, ?, ?, ?, date('now','localtime'), ?, ?, ?)
                """,
                [
                    ("order-1", "SKU-1", 1, 100.0, "paid", "Nirva buyer", "0812345678"),
                    ("order-1", "SKU-2", 1, 200.0, "paid", "Nirva buyer", "0812345678"),
                    ("order-2", "SKU-3", 1, 300.0, "paid", "Nirva buyer", "0812345678"),
                ],
            )

        customers = clv.calculate_clv()

        assert len(customers) == 1
        assert customers[0]["buyer_name"] == "Nirva buyer"
        assert customers[0]["order_count"] == 2
        assert customers[0]["total_spent"] == 600.0
        assert customers[0]["avg_order_value"] == 300.0


if __name__ == "__main__":
    test_clv_aggregates_canonical_order_total_price()
    print("clv order schema tests: 1 passed")
