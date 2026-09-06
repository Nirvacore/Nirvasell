"""Regression coverage for Product Score's canonical order amount field."""
from __future__ import annotations

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
import product_score


def test_product_score_reads_orders_total_price() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-product-score-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO products (sku, name, cost_price, sell_price, stock) VALUES (?,?,?,?,?)",
                    ("SKU-1", "Fixture product", 40.0, 100.0, 10),
                )
                connection.execute(
                    "INSERT INTO orders (order_id, sku, qty, total_price, order_date, status) VALUES (?,?,?,?,?,?)",
                    ("order-1", "SKU-1", 2, 200.0, date.today().isoformat(), "paid"),
                )

            result = product_score.calculate(days=30)
            assert len(result) == 1
            assert result[0]["sku"] == "SKU-1"
            assert result[0]["revenue"] == 200.0
            assert result[0]["quadrant"] == "star"
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_product_score_reads_orders_total_price()
    print("product score order schema: 1 passed")
