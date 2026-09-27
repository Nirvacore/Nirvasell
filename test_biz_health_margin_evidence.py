"""Regression coverage for canonical and fail-closed business margin evidence."""
from __future__ import annotations

import sys
import tempfile
import types
from contextlib import contextmanager
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import biz_health
import db
import expenses


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory() as tmpdir:
        database = Path(tmpdir) / "business-health.db"
        db._resolve_path = lambda: database
        try:
            db.init()
            expenses.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def _insert_order(connection, *, order_id: str, sku: str | None,
                  qty: int | None, unit_price: float,
                  total_price: float | None, status: str = "paid") -> None:
    connection.execute(
        "INSERT INTO orders "
        "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
        "VALUES (?,?,?,?,?,?,date('now'),?)",
        (order_id, sku, "direct", qty, unit_price, total_price,
         status),
    )


def test_margin_score_uses_canonical_paid_order_totals_and_costs() -> None:
    with isolated_database():
        with db.conn() as connection:
            connection.execute(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                ("SKU-GOOD", "Complete cost", 30.0, 75, 5),
            )
            _insert_order(
                connection, order_id="PAID", sku="SKU-GOOD", qty=2,
                unit_price=75.0, total_price=100.0,
            )
            _insert_order(
                connection, order_id="CANCELLED", sku="SKU-GOOD", qty=100,
                unit_price=75.0, total_price=7500.0, status="cancelled",
            )

        assert biz_health._margin_score() == 100


def test_missing_margin_evidence_makes_margin_and_overall_health_unavailable() -> None:
    with isolated_database():
        with db.conn() as connection:
            connection.execute(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                ("SKU-NULL", "Unknown cost", None, 50, 5),
            )
            connection.execute(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                ("SKU-GOOD", "Complete cost", 20.0, 50, 5),
            )
            _insert_order(
                connection, order_id="NULL-COST", sku="SKU-NULL", qty=1,
                unit_price=50.0, total_price=50.0,
            )
            _insert_order(
                connection, order_id="MISSING-PRODUCT", sku="SKU-MISSING", qty=1,
                unit_price=80.0, total_price=80.0,
            )
            _insert_order(
                connection, order_id="MISSING-SKU", sku=None, qty=1,
                unit_price=25.0, total_price=25.0,
            )
            _insert_order(
                connection, order_id="MISSING-QTY", sku="SKU-GOOD", qty=None,
                unit_price=50.0, total_price=50.0,
            )
            _insert_order(
                connection, order_id="MISSING-TOTAL", sku="SKU-GOOD", qty=1,
                unit_price=50.0, total_price=None,
            )

        result = biz_health.calculate()

        assert result["dimensions"]["margin"] is None
        assert result["overall"] is None
        assert result["grade"] == "—"
        assert result["status"] == "incomplete"
        assert result["evidence"]["margin"] == {
            "complete": False,
            "missing_evidence_rows": 5,
        }


if __name__ == "__main__":
    test_margin_score_uses_canonical_paid_order_totals_and_costs()
    test_missing_margin_evidence_makes_margin_and_overall_health_unavailable()
    print("business health margin evidence: 2 passed")
