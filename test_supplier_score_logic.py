"""Regression coverage for supplier scorecard queries and field mappings."""
from __future__ import annotations

import shutil
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

import db
import supplier_mgmt
import supplier_score


@contextmanager
def isolated_db():
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_supplier_score_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path
    try:
        supplier_mgmt.init()
        yield
    finally:
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_scorecard_uses_supplier_schema_fields_and_orders():
    with isolated_db():
        fast_id = supplier_mgmt.add_supplier(
            "Fast Supply", contact="Alice", lead_days=2
        )
        slow_id = supplier_mgmt.add_supplier(
            "Slow Supply", contact="Bob", lead_days=5
        )
        supplier_mgmt.set_price(fast_id, "SKU-1", 100)
        supplier_mgmt.set_price(slow_id, "SKU-1", 110)
        order_id = supplier_mgmt.add_order(
            fast_id, total_amount=1000, items_count=2
        )
        with db.conn() as connection:
            connection.execute(
                """
                UPDATE supplier_orders
                SET order_date = '2026-09-01'
                WHERE id = ?
                """,
                (order_id,),
            )
        supplier_mgmt.receive_order(order_id, received_at="2026-09-03")

        with db.conn() as connection:
            received_order = dict(connection.execute(
                "SELECT status, received_at FROM supplier_orders WHERE id = ?",
                (order_id,),
            ).fetchone())
        assert received_order == {
            "status": "received",
            "received_at": "2026-09-03",
        }

        scores = supplier_score.score_all()

        assert scores == [
            {
                "id": fast_id,
                "name": "Fast Supply",
                "contact": "Alice",
                "lead_days": 2,
                "price_score": 100.0,
                "delivery_score": 100.0,
                "avg_lead_actual": 2.0,
                "sku_count": 1,
                "total_volume": 1000.0,
                "overall": 73,
                "grade": "B",
            },
            {
                "id": slow_id,
                "name": "Slow Supply",
                "contact": "Bob",
                "lead_days": 5,
                "price_score": 0.0,
                "delivery_score": 50,
                "avg_lead_actual": 0,
                "sku_count": 1,
                "total_volume": 0,
                "overall": 18,
                "grade": "D",
            },
        ]
        assert supplier_score.summary() == {
            "total": 2,
            "avg_score": 46,
            "grades": {"A": 0, "B": 1, "C": 0, "D": 1},
            "top_supplier": "Fast Supply",
        }


def test_receive_order_fails_closed_for_invalid_transitions():
    with isolated_db():
        supplier_id = supplier_mgmt.add_supplier("Safe Supply")
        order_id = supplier_mgmt.add_order(supplier_id, total_amount=100)
        with db.conn() as connection:
            connection.execute(
                "UPDATE supplier_orders SET order_date = '2026-09-01' WHERE id = ?",
                (order_id,),
            )

        for received_at in (
            "", "2026-02-30", "not-a-date", "2026-9-3", "2026-08-31",
            "2099-01-01",
        ):
            try:
                supplier_mgmt.receive_order(order_id, received_at=received_at)
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid received_at accepted: {received_at!r}")

        try:
            supplier_mgmt.receive_order(999999, received_at="2026-09-03")
        except ValueError:
            pass
        else:
            raise AssertionError("missing supplier order accepted")

        supplier_mgmt.receive_order(order_id, received_at="2026-09-03")
        try:
            supplier_mgmt.receive_order(order_id, received_at="2026-09-04")
        except ValueError:
            pass
        else:
            raise AssertionError("received supplier order accepted twice")


if __name__ == "__main__":
    test_scorecard_uses_supplier_schema_fields_and_orders()
    test_receive_order_fails_closed_for_invalid_transitions()
    print("supplier score logic tests: 2 passed")
