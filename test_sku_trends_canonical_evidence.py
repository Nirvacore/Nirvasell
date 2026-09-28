"""Regression coverage for canonical, fail-closed SKU trend evidence."""
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
import sku_trends


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_sku_trends_") as temp:
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def insert_product(connection, sku="SKU-1", created_at=None):
    connection.execute(
        "INSERT INTO products (sku,name,cost_price,sell_price,stock,created_at) "
        "VALUES (?,?,?,?,?,?)",
        (sku, "Product", 10.0, 30.0, 10,
         created_at or date.today().isoformat()),
    )


def insert_order(connection, row_label, **overrides):
    values = {
        "order_id": row_label,
        "sku": "SKU-1",
        "platform": "direct",
        "qty": 3,
        "unit_price": 999.0,
        "total_price": 60.0,
        "order_date": date.today().isoformat(),
        "status": "paid",
    }
    values.update(overrides)
    connection.execute(
        "INSERT INTO orders "
        "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
        "VALUES (?,?,?,?,?,?,?,?)",
        tuple(values[key] for key in (
            "order_id", "sku", "platform", "qty", "unit_price",
            "total_price", "order_date", "status",
        )),
    )


def test_weekly_trend_uses_canonical_totals_includes_today_and_excludes_voided():
    with isolated_database():
        today = date.today()
        with db.conn() as connection:
            insert_product(connection)
            insert_order(connection, "current")
            insert_order(connection, "previous", qty=2, total_price=20,
                         order_date=(today - timedelta(days=8)).isoformat())
            insert_order(connection, "cancelled", qty=100, total_price=3000,
                         status="Cancelled")
            insert_order(connection, "returned", qty=100, total_price=3000,
                         status="RETURNED")
            insert_order(connection, "old-blank", status="   ",
                         order_date=(today - timedelta(days=30)).isoformat())

        result = sku_trends.trend_summary(weeks=2)
        item = result["items"][0]

        assert result["evidence_complete"] is True
        assert item["sku"] == "SKU-1"
        assert item["qty_this_week"] == 3
        assert item["qty_last_week"] == 2
        assert item["qty_change_pct"] == 50.0
        assert item["rev_this_week"] == 60.0
        assert item["rev_last_week"] == 20.0
        assert item["rev_change_pct"] == 200.0
        assert item["trend"] == "rising"


def test_in_window_blank_invalid_or_negative_order_evidence_fails_closed():
    cases = [
        ("blank-status", {"status": "   "}),
        ("blank-order", {"order_id": "   "}),
        ("blank-platform", {"platform": "   "}),
        ("blank-sku", {"sku": "   "}),
        ("missing-qty", {"qty": None}),
        ("negative-qty", {"qty": -1}),
        ("infinite-qty", {"qty": math.inf}),
        ("missing-total", {"total_price": None}),
        ("negative-total", {"total_price": -1}),
        ("infinite-total", {"total_price": math.inf}),
    ]
    for name, overrides in cases:
        with isolated_database():
            with db.conn() as connection:
                insert_product(connection)
                insert_order(connection, name, **overrides)

            result = sku_trends.trend_summary(weeks=2)
            assert result["evidence_complete"] is False, name
            assert result["missing_order_evidence_rows"] == 1, name
            assert result["items"] == [], name
            summary = sku_trends.summary()
            assert summary["total_skus"] is None, name
            assert summary["rising"] is None, name


def test_unparseable_order_date_has_unknown_membership_and_fails_closed():
    for value in (None, "not-a-date", date.today().isoformat() + " 00:00"):
        with isolated_database():
            with db.conn() as connection:
                insert_product(connection)
                insert_order(connection, "bad-date", order_date=value)

            result = sku_trends.trend_summary(weeks=2)
            assert result["evidence_complete"] is False, value
            assert result["missing_order_evidence_rows"] == 1, value
            assert result["items"] == [], value


def test_imported_iso_datetime_uses_its_bangkok_business_date():
    with isolated_database():
        represented_today = (
            date.today() - timedelta(days=1)
        ).isoformat() + "T17:30:00Z"
        with db.conn() as connection:
            insert_product(connection)
            insert_order(connection, "timestamped", order_date=represented_today,
                         qty=1, total_price=25.0)

        result = sku_trends.trend_summary(weeks=2)
        assert result["evidence_complete"] is True
        assert result["items"][0]["qty_this_week"] == 1
        assert result["items"][0]["rev_this_week"] == 25.0


def test_new_products_use_canonical_orders_and_fail_closed_only_for_relevant_rows():
    with isolated_database():
        today = date.today()
        with db.conn() as connection:
            insert_product(connection, "SKU-NEW")
            insert_product(connection, "   ",
                           created_at=(today - timedelta(days=40)).isoformat())
            insert_order(connection, "new-paid", sku="SKU-NEW", qty=2,
                         total_price=45.0)
            insert_order(connection, "new-cancelled", sku="SKU-NEW", qty=50,
                         total_price=1000.0, status="cancelled")
            insert_order(connection, "cancelled-unknown-sku", sku=None, qty=None,
                         total_price=None, status="RETURNED")
            insert_order(connection, "old-unknown-sku", sku=None, status="paid",
                         order_date=(today - timedelta(days=30)).isoformat())
            # Membership is known to be unrelated to the selected new SKU.
            insert_order(connection, "old-product-bad", sku="SKU-OLD",
                         status="   ", qty=None, total_price=None)

        result = sku_trends.new_products_summary(days=14)
        assert result["evidence_complete"] is True
        assert result["missing_order_evidence_rows"] == 0
        assert result["missing_product_evidence_rows"] == 0
        assert len(result["items"]) == 1
        assert result["items"][0]["sku"] == "SKU-NEW"
        assert result["items"][0]["total_sold"] == 2
        assert result["items"][0]["total_revenue"] == 45.0

    with isolated_database():
        with db.conn() as connection:
            insert_product(connection, "SKU-NEW")
            insert_order(connection, "new-bad-date", sku="SKU-NEW",
                         order_date="not-a-date")
        result = sku_trends.new_products_summary(days=14)
        assert result["evidence_complete"] is False
        assert result["missing_order_evidence_rows"] == 1
        assert result["items"] == []

    with isolated_database():
        with db.conn() as connection:
            insert_product(connection, "SKU-NEW")
            insert_order(connection, "new-bad", sku="SKU-NEW", total_price=None)
        result = sku_trends.new_products_summary(days=14)
        assert result["evidence_complete"] is False
        assert result["missing_order_evidence_rows"] == 1
        assert result["items"] == []

    with isolated_database():
        with db.conn() as connection:
            insert_product(connection, "SKU-BAD-DATE", created_at="not-a-date")
        result = sku_trends.new_products_summary(days=14)
        assert result["evidence_complete"] is False
        assert result["missing_product_evidence_rows"] == 1
        assert result["items"] == []

    with isolated_database():
        with db.conn() as connection:
            insert_product(connection, "SKU-OLD",
                           created_at=(date.today() - timedelta(days=40)).isoformat())
            insert_order(connection, "unknown-but-irrelevant", sku=None, status="paid")
        result = sku_trends.new_products_summary(days=14)
        assert result["evidence_complete"] is True
        assert result["items"] == []


if __name__ == "__main__":
    test_weekly_trend_uses_canonical_totals_includes_today_and_excludes_voided()
    test_in_window_blank_invalid_or_negative_order_evidence_fails_closed()
    test_unparseable_order_date_has_unknown_membership_and_fails_closed()
    test_imported_iso_datetime_uses_its_bangkok_business_date()
    test_new_products_use_canonical_orders_and_fail_closed_only_for_relevant_rows()
    print("sku trends canonical evidence: 5 passed")
