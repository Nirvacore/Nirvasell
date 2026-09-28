"""Regression coverage for canonical, fail-closed profit-calendar evidence."""
from __future__ import annotations

import math
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
import profit_calendar


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_profit_calendar_") as temp:
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def insert_product(connection, sku="SKU-1", cost_price=10.0):
    connection.execute(
        "INSERT INTO products (sku,name,cost_price,sell_price,stock) VALUES (?,?,?,?,?)",
        (sku, "Product", cost_price, 30.0, 10),
    )


def insert_order(connection, row_label, **overrides):
    values = {
        "sku": "SKU-1",
        "platform": "direct",
        "qty": 2,
        "unit_price": 999.0,
        "total_price": 50.0,
        "order_date": date.today().isoformat(),
        "status": "paid",
        "order_id": row_label,
    }
    values.update(overrides)
    connection.execute(
        "INSERT INTO orders "
        "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (
            values["order_id"],
            values["sku"],
            values["platform"],
            values["qty"],
            values["unit_price"],
            values["total_price"],
            values["order_date"],
            values["status"],
        ),
    )


def test_daily_summary_uses_canonical_totals_and_preserves_provable_zero_days():
    with isolated_database():
        today = date.today()
        outside = (today - timedelta(days=40)).isoformat()
        with db.conn() as connection:
            insert_product(connection)
            insert_order(connection, "paid")
            insert_order(connection, "cancelled", qty=100, total_price=3000,
                         status="Cancelled")
            insert_order(connection, "returned", qty=100, total_price=3000,
                         status="RETURNED")
            # The row is provably outside this 30-day analysis window, so its
            # incomplete status must not suppress current evidence.
            insert_order(connection, "old-blank-status", order_date=outside,
                         status="   ")

        result = profit_calendar.daily_summary(days=30)
        by_date = {item["date"]: item for item in result["days"]}
        current = by_date[today.isoformat()]

        assert result["evidence_complete"] is True
        assert result["missing_order_evidence_rows"] == 0
        assert result["missing_product_evidence_rows"] == 0
        assert current["revenue"] == 50.0
        assert current["cogs"] == 20.0
        assert current["profit"] == 30.0
        assert current["orders"] == 1
        assert current["has_data"] is True
        assert any(
            item["revenue"] == 0
            and item["cogs"] == 0
            and item["profit"] == 0
            and item["orders"] == 0
            and item["has_data"] is False
            for item in result["days"]
        )


def test_in_window_incomplete_order_or_product_evidence_fails_closed():
    cases = [
        ("blank-status", {"status": "   "}, False),
        ("blank-order", {"order_id": "   "}, False),
        ("blank-platform", {"platform": "   "}, False),
        ("blank-sku", {"sku": "   "}, False),
        ("missing-qty", {"qty": None}, False),
        ("negative-qty", {"qty": -1}, False),
        ("infinite-qty", {"qty": math.inf}, False),
        ("missing-total", {"total_price": None}, False),
        ("negative-total", {"total_price": -1}, False),
        ("infinite-total", {"total_price": math.inf}, False),
        ("missing-product", {"sku": "SKU-MISSING"}, True),
    ]

    for name, overrides, product_failure in cases:
        with isolated_database():
            with db.conn() as connection:
                insert_product(connection)
                insert_order(connection, name, **overrides)

            result = profit_calendar.daily_summary(days=30)
            assert result["evidence_complete"] is False, name
            assert result["days"] == [], name
            assert result["missing_product_evidence_rows"] == int(product_failure), name
            assert result["missing_order_evidence_rows"] == int(not product_failure), name
            assert profit_calendar.daily_profits(days=30) == [], name


def test_invalid_date_is_unknown_membership_and_cost_must_be_finite_nonnegative():
    for name, order_date, cost in [
        ("bad-date", "not-a-date", 10.0),
        ("noncanonical-date", date.today().isoformat() + " 00:00:00", 10.0),
        ("missing-date", None, 10.0),
        ("missing-cost", date.today().isoformat(), None),
        ("negative-cost", date.today().isoformat(), -1.0),
        ("nan-cost", date.today().isoformat(), math.nan),
    ]:
        with isolated_database():
            with db.conn() as connection:
                insert_product(connection, cost_price=cost)
                insert_order(connection, name, order_date=order_date)

            result = profit_calendar.daily_summary(days=30)
            assert result["evidence_complete"] is False, name
            assert result["days"] == [], name
            assert result["missing_order_evidence_rows"] == int("date" in name), name
            assert result["missing_product_evidence_rows"] == int("cost" in name), name


if __name__ == "__main__":
    test_daily_summary_uses_canonical_totals_and_preserves_provable_zero_days()
    test_in_window_incomplete_order_or_product_evidence_fails_closed()
    test_invalid_date_is_unknown_membership_and_cost_must_be_finite_nonnegative()
    print("profit calendar canonical evidence: 3 passed")
