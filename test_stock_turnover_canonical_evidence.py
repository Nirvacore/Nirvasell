"""Regression coverage for canonical, fail-closed stock-turnover evidence."""
from __future__ import annotations

import sys
import tempfile
import types
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import db
import stock_turnover


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_turnover_") as temp:
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def _insert_order(connection, values):
    connection.execute(
        "INSERT INTO orders "
        "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
        "VALUES (?,?,?,?,?,?,?,?)",
        values,
    )


def test_turnover_uses_canonical_orders_and_preserves_provable_zero_sales() -> None:
    with isolated_database():
        today = date.today().isoformat()
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                [
                    ("SKU-SOLD", "Selling", 10.0, 30, 20),
                    ("SKU-ZERO", "No sales", 12.0, 35, 8),
                ],
            )
            for order in [
                ("PAID", "SKU-SOLD", "web", 2, 30.0, 60.0, today, "paid"),
                ("CANCELLED", "SKU-SOLD", "web", 100, 30.0, 3000.0,
                 today, " Cancelled "),
                ("RETURNED", "SKU-SOLD", "web", 100, 30.0, 3000.0,
                 today, "RETURNED"),
            ]:
                _insert_order(connection, order)

        result = stock_turnover.summary()
        by_sku = {item["sku"]: item for item in result["items"]}

        assert result["evidence_complete"] is True
        assert result["missing_order_evidence_rows"] == 0
        assert result["missing_product_evidence_rows"] == 0
        assert by_sku["SKU-SOLD"]["total_sold"] == 2
        assert by_sku["SKU-SOLD"]["order_count"] == 1
        assert by_sku["SKU-ZERO"]["total_sold"] == 0
        assert by_sku["SKU-ZERO"]["order_count"] == 0
        assert by_sku["SKU-ZERO"]["stock_value"] == 96.0


def test_incomplete_order_evidence_suppresses_turnover_claims() -> None:
    cases = [
        ("blank-status", "ORDER", "SKU", "web", 1, date.today().isoformat(), "   "),
        ("blank-order", "   ", "SKU", "web", 1, date.today().isoformat(), "paid"),
        ("blank-platform", "ORDER", "SKU", "   ", 1, date.today().isoformat(), "paid"),
        ("blank-sku", "ORDER", "   ", "web", 1, date.today().isoformat(), "paid"),
        ("missing-qty", "ORDER", "SKU", "web", None, date.today().isoformat(), "paid"),
        ("missing-date", "ORDER", "SKU", "web", 1, None, "paid"),
        ("malformed-date", "ORDER", "SKU", "web", 1, "2026-9-1", "paid"),
        ("future-date", "ORDER", "SKU", "web", 1,
         (date.today() + timedelta(days=1)).isoformat(), "paid"),
        ("missing-product", "ORDER", "UNKNOWN", "web", 1,
         date.today().isoformat(), "paid"),
    ]

    for label, order_id, sku, platform, qty, order_date, status in cases:
        with isolated_database():
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                    "VALUES (?,?,?,?,?)",
                    ("SKU", "Complete", 10.0, 20, 4),
                )
                _insert_order(
                    connection,
                    (order_id, sku, platform, qty, 20.0, 20.0,
                     order_date, status),
                )

            result = stock_turnover.summary()
            assert result["evidence_complete"] is False, label
            assert result["missing_order_evidence_rows"] == 1, label
            assert result["items"] == [], label
            assert result["avg_turnover"] is None, label
            assert stock_turnover.calculate() == [], label


def test_incomplete_product_evidence_suppresses_turnover_claims() -> None:
    cases = [
        ("blank-sku", "   ", 10.0, 4),
        ("missing-cost", "SKU", None, 4),
        ("missing-stock", "SKU", 10.0, None),
        ("negative-cost", "SKU", -1.0, 4),
        ("negative-stock", "SKU", 10.0, -1),
    ]

    for label, sku, cost, stock in cases:
        with isolated_database():
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                    "VALUES (?,?,?,?,?)",
                    (sku, "Incomplete", cost, 20, stock),
                )

            result = stock_turnover.summary()
            assert result["evidence_complete"] is False, label
            assert result["missing_product_evidence_rows"] == 1, label
            assert result["items"] == [], label
            assert result["total_stock_value"] is None, label


if __name__ == "__main__":
    test_turnover_uses_canonical_orders_and_preserves_provable_zero_sales()
    test_incomplete_order_evidence_suppresses_turnover_claims()
    test_incomplete_product_evidence_suppresses_turnover_claims()
    print("stock turnover canonical evidence: 3 passed")
