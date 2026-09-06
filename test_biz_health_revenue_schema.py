"""Regression coverage for Business Health's canonical order amount field."""
from __future__ import annotations

import sys
import tempfile
import types
from datetime import date, timedelta
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        fake_pandas.notna = lambda value: value is not None
        sys.modules["pandas"] = fake_pandas

import biz_health
import db
import expenses


def test_health_scores_use_orders_total_price_and_expenses_date() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-health-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            expenses.init()
            today = date.today()
            previous = today - timedelta(days=20)
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO orders (order_id, sku, total_price, order_date, status) VALUES (?,?,?,?,?)",
                    ("current", "SKU-1", 1000.0, today.isoformat(), "paid"),
                )
                connection.execute(
                    "INSERT INTO orders (order_id, sku, total_price, order_date, status) VALUES (?,?,?,?,?)",
                    ("previous", "SKU-2", 500.0, previous.isoformat(), "paid"),
                )
            expenses.add(date=today.isoformat(), category="shipping", amount=50.0)

            assert biz_health._revenue_score() == 100
            assert biz_health._expense_score() == 100
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_health_scores_use_orders_total_price_and_expenses_date()
    print("business health order schema: 1 passed")
