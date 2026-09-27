"""Regression coverage for order CSV export against the canonical schema."""
from __future__ import annotations

import csv
import io
import sys
import tempfile
import types
from datetime import date
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
import export_center


def test_export_orders_reads_total_price_without_legacy_total_amount() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-export-orders-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO products (sku, name, stock) VALUES (?,?,?)",
                    ("SKU-1", "สินค้า", 1),
                )
                connection.execute(
                    "INSERT INTO orders "
                    "(order_id, sku, platform, qty, unit_price, total_price, order_date, status, buyer_name, buyer_phone) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    ("order-1", "SKU-1", "shopee", 2, 120.0, 240.0, date.today().isoformat(), "paid", "Nirva buyer", "0812345678"),
                )

            rows = list(csv.reader(io.StringIO(export_center.export_orders(days=1))))
            assert rows[1] == [
                "order-1", "SKU-1", "สินค้า", "shopee", "2", "120.0",
                "240.0", "240.0", date.today().isoformat(), "paid",
                "Nirva buyer", "0812345678",
            ]
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_export_orders_reads_total_price_without_legacy_total_amount()
    print("export orders schema: 1 passed")
