"""Regression coverage for canonical, fail-closed dead-stock evidence."""
from __future__ import annotations

import sys
import tempfile
import types
from contextlib import contextmanager
from datetime import date
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import db
import dead_stock


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_dead_stock_") as temp:
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def test_detect_uses_canonical_orders_and_preserves_genuine_zero_sales() -> None:
    with isolated_database():
        today = date.today().isoformat()
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                [
                    ("SKU-SOLD", "Selling", 10.0, 30.0, 5),
                    ("SKU-ZERO", "Never sold", 20.0, 50.0, 4),
                    ("SKU-RETURN", "Returned only", 15.0, 40.0, 3),
                ],
            )
            connection.executemany(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
                "VALUES (?,?,?,?,?,?,?,?)",
                [
                    ("paid", "SKU-SOLD", "direct", 3, 30.0, 90.0, today, "paid"),
                    ("cancelled", "SKU-SOLD", "direct", 100, 30.0, 3000.0,
                     today, "Cancelled"),
                    ("returned", "SKU-RETURN", "direct", 5, 40.0, 200.0,
                     today, "RETURNED"),
                ],
            )

        items = dead_stock.detect(days=30)
        by_sku = {item["sku"]: item for item in items}

        assert "SKU-SOLD" not in by_sku
        assert by_sku["SKU-ZERO"]["recent_qty"] == 0
        assert by_sku["SKU-ZERO"]["total_qty"] == 0
        assert by_sku["SKU-ZERO"]["severity"] == "dead"
        assert by_sku["SKU-ZERO"]["trapped_cash"] == 80.0
        assert by_sku["SKU-RETURN"]["recent_qty"] == 0
        assert by_sku["SKU-RETURN"]["severity"] == "dead"


def test_missing_order_or_cost_fields_make_dead_stock_claims_unavailable() -> None:
    with isolated_database():
        today = date.today().isoformat()
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                [
                    ("SKU-GOOD", "Complete", 10.0, 30.0, 5),
                    ("SKU-NO-COST", "No cost", None, 30.0, 5),
                    ("   ", "Blank SKU", 10.0, 30.0, 5),
                ],
            )
            connection.executemany(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
                "VALUES (?,?,?,?,?,?,?,?)",
                [
                    ("missing-sku", None, "direct", 1, 30.0, 30.0, today, "paid"),
                    ("missing-product", "SKU-MISSING", "direct", 1, 30.0, 30.0,
                     today, "paid"),
                    ("missing-cost", "SKU-NO-COST", "direct", 1, 30.0, 30.0,
                     today, "paid"),
                    ("missing-qty", "SKU-GOOD", "direct", None, 30.0, 30.0,
                     today, "paid"),
                    ("missing-date", "SKU-GOOD", "direct", 1, 30.0, 30.0,
                     None, "paid"),
                    ("missing-total", "SKU-GOOD", "direct", 1, 30.0, None,
                     today, "paid"),
                    ("blank-status", "SKU-GOOD", "direct", 1, 30.0, 30.0,
                     today, "   "),
                    ("blank-sku", "   ", "direct", 1, 30.0, 30.0,
                     today, "paid"),
                ],
            )

        result = dead_stock.summary(days=30)

        assert result["evidence_complete"] is False
        assert result["missing_order_evidence_rows"] == 8
        assert result["missing_product_evidence_rows"] == 2
        assert result["items"] == []
        assert result["total_items"] is None
        assert result["dead"] is None
        assert result["trapped_cash"] is None
        assert dead_stock.detect(days=30) == []


if __name__ == "__main__":
    test_detect_uses_canonical_orders_and_preserves_genuine_zero_sales()
    test_missing_order_or_cost_fields_make_dead_stock_claims_unavailable()
    print("dead stock canonical evidence: 2 passed")
