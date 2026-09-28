"""Product Score canonical date, status, numeric, and isolation regressions."""

from __future__ import annotations

import math
import sys
import tempfile
import types
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import db
from order_dates import order_business_date
import product_score


TODAY = order_business_date(datetime.now(timezone.utc))


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_product_score_") as temp:
        db._resolve_path = lambda: Path(temp) / "user.db"
        try:
            db.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


_DEFAULT_NAME = object()


def add_product(connection, sku: str, *, name=_DEFAULT_NAME, cost=40.0,
                sell=100.0, stock=10):
    connection.execute(
        """INSERT INTO products (sku,name,cost_price,sell_price,stock)
           VALUES (?,?,?,?,?)""",
        (sku, sku if name is _DEFAULT_NAME else name, cost, sell, stock),
    )


def add_order(connection, order_id: str, sku: str, *, total=100.0, qty=1,
              order_date=None, status="paid", platform="shopee"):
    connection.execute(
        """INSERT INTO orders
           (order_id,sku,platform,qty,total_price,order_date,status)
           VALUES (?,?,?,?,?,?,?)""",
        (order_id, sku, platform, qty, total,
         order_date or TODAY.isoformat(), status),
    )


def test_window_uses_bangkok_dates_and_excludes_non_revenue_statuses() -> None:
    with isolated_database():
        with db.conn() as connection:
            add_product(connection, "SKU-1")
            add_order(connection, "paid", "SKU-1", total=100,
                      order_date=f"{TODAY.isoformat()}T00:00:00")
            add_order(connection, "cancelled", "SKU-1", total=900,
                      order_date="not-a-date", status="cancelled")
            add_order(connection, "refunded", "SKU-1", total=800,
                      order_date=(TODAY + timedelta(days=5)).isoformat(),
                      status=" refunded ")
            add_order(connection, "unknown", "SKU-1", total=700, status="mystery")
            add_order(connection, "old", "SKU-1", total=600,
                      order_date=(TODAY - timedelta(days=7)).isoformat())

        summary = product_score.summary(days=7)
        assert summary["evidence_complete"] is True
        assert summary["missing_order_evidence_rows"] == 0
        assert summary["items"] == product_score.calculate(days=7)
        assert summary["items"][0]["revenue"] == 100.0
        assert summary["items"][0]["velocity"] == round(1 / 7, 2)
        assert summary["total_skus"] == 1


def test_future_and_malformed_dates_fail_closed_without_scores() -> None:
    with isolated_database():
        with db.conn() as connection:
            add_product(connection, "SKU-1")
            add_order(connection, "future", "SKU-1",
                      order_date=(TODAY + timedelta(days=1)).isoformat())
            add_order(connection, "malformed", "SKU-1", order_date="09/28/2026")

        summary = product_score.summary(days=30)
        assert summary["evidence_complete"] is False
        assert summary["missing_order_evidence_rows"] == 2
        assert summary["items"] == []
        assert summary["avg_score"] is None
        assert summary["quadrants"] is None
        assert product_score.calculate(days=30) == []


def test_nonfinite_negative_or_unavailable_financial_evidence_fails_closed() -> None:
    with isolated_database():
        with db.conn() as connection:
            add_product(connection, "GOOD")
            add_product(connection, "BAD-COST", cost=math.inf)
            add_product(connection, "BAD-STOCK", stock=-1)
            add_product(connection, "BAD-MARGIN", cost=120, sell=100)
            add_order(connection, "negative-revenue", "GOOD", total=-1)
            add_order(connection, "infinite-revenue", "GOOD", total=math.inf)
            add_order(connection, "huge-revenue-1", "GOOD", total=1e308)
            add_order(connection, "huge-revenue-2", "GOOD", total=1e308)

        summary = product_score.summary(days=30)
        assert summary["evidence_complete"] is False
        assert summary["missing_product_evidence_rows"] == 3
        assert summary["missing_order_evidence_rows"] == 3
        assert summary["items"] == []
        assert product_score.calculate(days=30) == []


def test_null_or_blank_product_names_fail_closed_without_scores() -> None:
    with isolated_database():
        with db.conn() as connection:
            add_product(connection, "NULL-NAME", name=None)
            add_product(connection, "BLANK-NAME", name="   ")

        summary = product_score.summary(days=30)
        assert summary["evidence_complete"] is False
        assert summary["missing_product_evidence_rows"] == 2
        assert summary["items"] == []
        assert product_score.calculate(days=30) == []


def test_null_or_blank_order_platforms_fail_closed_without_scores() -> None:
    with isolated_database():
        with db.conn() as connection:
            add_product(connection, "GOOD")
            add_order(connection, "null-platform", "GOOD", platform=None)
            add_order(connection, "blank-platform", "GOOD", platform="   ")

        summary = product_score.summary(days=30)
        assert summary["evidence_complete"] is False
        assert summary["missing_order_evidence_rows"] == 2
        assert summary["items"] == []
        assert product_score.calculate(days=30) == []


def test_zero_revenue_and_zero_stock_remain_valid_when_evidence_is_complete() -> None:
    with isolated_database():
        with db.conn() as connection:
            add_product(connection, "ZERO", cost=0, sell=100, stock=0)

        summary = product_score.summary(days=14)
        assert summary["evidence_complete"] is True
        assert summary["total_skus"] == 1
        item = summary["items"][0]
        assert item["revenue"] == 0
        assert item["stock"] == 0
        assert item["margin_pct"] == 100.0
        assert all(math.isfinite(item[key]) for key in (
            "revenue", "stock", "margin_pct", "velocity", "score"
        ))


def test_product_score_uses_only_the_active_per_user_database() -> None:
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_product_score_users_") as temp:
        active = {"path": Path(temp) / "user-a.db"}
        db._resolve_path = lambda: active["path"]
        try:
            db.init()
            with db.conn() as connection:
                add_product(connection, "USER-A")
                add_order(connection, "order-a", "USER-A", total=250)

            active["path"] = Path(temp) / "user-b.db"
            db.init()
            assert product_score.summary(days=30)["total_skus"] == 0

            active["path"] = Path(temp) / "user-a.db"
            assert product_score.summary(days=30)["items"][0]["revenue"] == 250
        finally:
            db._resolve_path = original_resolve_path


if __name__ == "__main__":
    test_window_uses_bangkok_dates_and_excludes_non_revenue_statuses()
    test_future_and_malformed_dates_fail_closed_without_scores()
    test_nonfinite_negative_or_unavailable_financial_evidence_fails_closed()
    test_null_or_blank_product_names_fail_closed_without_scores()
    test_null_or_blank_order_platforms_fail_closed_without_scores()
    test_zero_revenue_and_zero_stock_remain_valid_when_evidence_is_complete()
    test_product_score_uses_only_the_active_per_user_database()
    print("product score canonical evidence: 7 passed")
