"""Regression coverage for ABC analysis against the canonical orders schema."""
from __future__ import annotations

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

import abc_analysis
import db


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory() as tmpdir:
        database = Path(tmpdir) / "abc.db"
        db._resolve_path = lambda: database
        try:
            db.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def test_classify_reads_quantity_and_revenue_from_canonical_orders() -> None:
    with isolated_database():
        with db.conn() as connection:
            connection.execute(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                ("SKU-ABC", "ABC product", 30.0, 75, 4),
            )
            connection.execute(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                ("SKU-RETURN", "Returned-only product", 10.0, 25, 3),
            )
            connection.execute(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
                "VALUES (?,?,?,?,?,?,?,?)",
                ("ORDER-1", "SKU-ABC", "direct", 2, 75.0, 120.0,
                 "2026-09-28", "paid"),
            )
            connection.execute(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
                "VALUES (?,?,?,?,?,?,?,?)",
                ("ORDER-CANCELLED", "SKU-ABC", "direct", 100, 75.0, 7500.0,
                 "2026-09-28", "cancelled"),
            )
            connection.execute(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
                "VALUES (?,?,?,?,?,?,?,?)",
                ("ORDER-RETURNED", "SKU-RETURN", "direct", 5, 25.0, 125.0,
                 "2026-09-28", "returned"),
            )

        items = abc_analysis.classify()
        by_sku = {item["sku"]: item for item in items}

        assert len(items) == 2
        assert by_sku["SKU-ABC"]["total_qty"] == 2
        assert by_sku["SKU-ABC"]["total_revenue"] == 120.0
        assert by_sku["SKU-RETURN"]["total_qty"] == 0
        assert by_sku["SKU-RETURN"]["total_revenue"] == 0


if __name__ == "__main__":
    test_classify_reads_quantity_and_revenue_from_canonical_orders()
    print("ABC canonical order schema: 1 passed")
