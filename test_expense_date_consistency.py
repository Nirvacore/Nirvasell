"""Regression coverage for the canonical expenses.date column."""
from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path
import sys
import types

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        fake_pandas.notna = lambda value: value is not None
        sys.modules["pandas"] = fake_pandas

import db
import expenses
import budget_tracker
import cash_flow
import biz_health


def test_reporting_modules_read_the_real_expense_date_column() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-expense-date-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            expenses.init()
            budget_tracker.init()
            today = date.today().isoformat()
            month = today[:7]
            db_path = Path(temp) / "fixture.db"
            with db.conn() as connection:
                # biz_health uses the legacy total_amount order alias; provide
                # only that fixture column without changing production schema.
                connection.execute("ALTER TABLE orders ADD COLUMN total_amount REAL")
                connection.execute(
                    "INSERT INTO orders (order_id, sku, total_price, total_amount, order_date, status) "
                    "VALUES (?,?,?,?,?,?)",
                    ("order-1", "SKU-1", 100.0, 100.0, today, "paid"),
                )
            inserted_id = expenses.add(date=today, category="shipping", amount=25.0)
            assert inserted_id == 1

            daily = cash_flow.daily(days=30)
            assert daily and daily[-1]["expenses"] == 25.0
            monthly = cash_flow.monthly(months=1)
            assert monthly and monthly[-1]["expenses"] == 25.0
            forecast = cash_flow.current_month_forecast()
            assert forecast["this_month_expenses"] == 25.0

            budget_tracker.set_budget("shipping", 100.0)
            budget = budget_tracker.budget_vs_actual(month)
            shipping = next(item for item in budget if item["category"] == "shipping")
            assert shipping["spent"] == 25.0

            score = biz_health._expense_score()
            assert score < 100
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_reporting_modules_read_the_real_expense_date_column()
    print("expense date consistency: 1 passed")
