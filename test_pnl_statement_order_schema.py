"""Regression coverage for P&L queries against the canonical orders schema."""
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

# The report only needs a display label, so keep this regression harness
# independent of Streamlit's optional UI dependency.
fake_i18n_inline = types.ModuleType("i18n_inline")
fake_i18n_inline.pnl_period_label = lambda **kwargs: "fixture-period"
sys.modules["i18n_inline"] = fake_i18n_inline

import db
import expenses
import pnl_statement


def test_monthly_and_quarterly_pnl_use_total_price() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-pnl-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            expenses.init()
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO orders (order_id, sku, qty, total_price, order_date, status) VALUES (?,?,?,?,?,?)",
                    ("paid-order", "SKU-1", 2, 1000.0, "2026-09-06", "paid"),
                )
                connection.execute(
                    "INSERT INTO orders (order_id, sku, qty, total_price, order_date, status) VALUES (?,?,?,?,?,?)",
                    ("returned-order", "SKU-2", 1, 250.0, "2026-09-06", "returned"),
                )
            expenses.add(date="2026-09-06", category="shipping", amount=100.0)

            monthly = pnl_statement.monthly(2026, 9)
            quarterly = pnl_statement.quarterly(2026, 3)
            for report in (monthly, quarterly):
                assert report["revenue"] == 1000.0
                assert report["returns"] == 250.0
                assert report["net_revenue"] == 750.0
                assert report["total_expenses"] == 100.0
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_monthly_and_quarterly_pnl_use_total_price()
    print("P&L order schema: 1 passed")
