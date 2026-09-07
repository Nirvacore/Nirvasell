"""Regression coverage for global search against the canonical orders schema."""
from __future__ import annotations

import sys
import tempfile
import types
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
import fulfillment
import global_search


def test_search_reads_order_total_price() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-global-search-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            fulfillment.init()
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO orders (order_id, sku, platform, qty, total_price, order_date, status, buyer_name, buyer_phone) VALUES (?,?,?,?,?,?,?,?,?)",
                    ("order-1", "SKU-1", "fixture", 2, 240.0, "2026-09-07", "paid", "Nirva buyer", "0812345678"),
                )

            result = global_search.search("order-1")
            assert result["orders"] == [
                {
                    "order_id": "order-1",
                    "sku": "SKU-1",
                    "platform": "fixture",
                    "qty": 2,
                    "total_price": 240.0,
                    "order_date": "2026-09-07",
                    "status": "paid",
                    "buyer_name": "Nirva buyer",
                    "buyer_phone": "0812345678",
                }
            ]
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_search_reads_order_total_price()
    print("global search order schema: 1 passed")
