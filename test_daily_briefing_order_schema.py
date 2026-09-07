"""Regression coverage for Daily Briefing's order amount queries."""
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

import daily_briefing
import db
import fulfillment


def test_daily_briefing_reads_orders_total_price() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-daily-briefing-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            fulfillment.init()
            yesterday = date.today() - timedelta(days=1)
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO orders (order_id, sku, qty, total_price, order_date, status, buyer_name, buyer_phone) VALUES (?,?,?,?,?,?,?,?)",
                    ("order-1", "SKU-1", 2, 360.0, yesterday.isoformat(), "paid", "Nirva buyer", "0812345678"),
                )

            report = daily_briefing._yesterday_summary(yesterday.isoformat())
            assert report == {"orders": 1, "revenue": 360.0, "new_customers": 1}
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_daily_briefing_reads_orders_total_price()
    print("daily briefing order schema: 1 passed")
