"""Regression coverage for canonical, fail-closed sales-goal actuals."""
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

import db

if "streamlit" not in sys.modules:
    fake_streamlit = types.ModuleType("streamlit")
    fake_streamlit.session_state = {}
    sys.modules["streamlit"] = fake_streamlit

import goals


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_goals_") as temp:
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            goals.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def _insert_order(connection, values):
    connection.execute(
        "INSERT INTO orders "
        "(order_id,sku,platform,qty,unit_price,total_price,order_date,status,"
        "buyer_name,buyer_phone) VALUES (?,?,?,?,?,?,?,?,?,?)",
        values,
    )


def test_actuals_use_canonical_totals_dates_order_grain_and_costs() -> None:
    with isolated_database():
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                [
                    ("SKU-A", "A", 10.0, 50, 10),
                    ("SKU-B", "B", 20.0, 80, 10),
                ],
            )
            for order in [
                ("ORDER-1", "SKU-A", "web", 1, 50.0, 40.0,
                 "2026-09-03", "paid", "Alice", "0801"),
                ("ORDER-1", "SKU-B", "web", 1, 80.0, 60.0,
                 "2026-09-03", "paid", "Alice", "0801"),
                ("ORDER-2", "SKU-B", "web", 1, 80.0, 80.0,
                 "2026-09-04", "PAID", "Bob", "0802"),
                ("CANCELLED", "SKU-A", "web", 99, 50.0, 4950.0,
                 "2026-09-05", " Cancelled ", "Ignored", "0999"),
                ("RETURNED", "SKU-A", "web", 99, 50.0, 4950.0,
                 "2026-09-05", "RETURNED", "Ignored", "0998"),
                ("OTHER-MONTH", "SKU-A", "web", 1, 50.0, 50.0,
                 "2026-08-31", "paid", "Older", "0700"),
            ]:
                _insert_order(connection, order)

        expected = {
            "revenue": 180.0,
            "orders": 2,
            "profit": 130.0,
            "new_customers": 2,
            "avg_order": 90.0,
        }
        for metric, value in expected.items():
            evidence = goals._actual_evidence(metric, "2026-09")
            assert evidence == {
                "value": value,
                "complete": True,
                "missing_evidence_rows": 0,
            }

        assert goals._actual_evidence("revenue", "2026-07") == {
            "value": 0.0,
            "complete": True,
            "missing_evidence_rows": 0,
        }


def test_incomplete_or_blank_order_evidence_suppresses_exact_actuals() -> None:
    cases = [
        ("blank-order", "   ", "SKU-GOOD", "web", 1, 20.0,
         "2026-09-01", "paid", "Buyer", "0811", "revenue"),
        ("blank-platform", "ORDER", "SKU-GOOD", "   ", 1, 20.0,
         "2026-09-01", "paid", "Buyer", "0811", "orders"),
        ("blank-status", "ORDER", "SKU-GOOD", "web", 1, 20.0,
         "2026-09-01", "   ", "Buyer", "0811", "revenue"),
        ("blank-sku", "ORDER", "   ", "web", 1, 20.0,
         "2026-09-01", "paid", "Buyer", "0811", "profit"),
        ("missing-qty", "ORDER", "SKU-GOOD", "web", None, 20.0,
         "2026-09-01", "paid", "Buyer", "0811", "profit"),
        ("missing-total", "ORDER", "SKU-GOOD", "web", 1, None,
         "2026-09-01", "paid", "Buyer", "0811", "avg_order"),
        ("blank-total", "ORDER", "SKU-GOOD", "web", 1, "   ",
         "2026-09-01", "paid", "Buyer", "0811", "revenue"),
        ("blank-qty", "ORDER", "SKU-GOOD", "web", "   ", 20.0,
         "2026-09-01", "paid", "Buyer", "0811", "profit"),
        ("bad-date", "ORDER", "SKU-GOOD", "web", 1, 20.0,
         "2026-9-1", "paid", "Buyer", "0811", "revenue"),
        ("blank-buyer", "ORDER", "SKU-GOOD", "web", 1, 20.0,
         "2026-09-01", "paid", "   ", "", "new_customers"),
    ]

    for label, order_id, sku, platform, qty, total, order_date, status, name, phone, metric in cases:
        with isolated_database():
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                    "VALUES (?,?,?,?,?)",
                    ("SKU-GOOD", "Good", 10.0, 20, 3),
                )
                _insert_order(
                    connection,
                    (order_id, sku, platform, qty, 20.0, total, order_date,
                     status, name, phone),
                )

            evidence = goals._actual_evidence(metric, "2026-09")
            assert evidence["complete"] is False, label
            assert evidence["value"] is None, label
            assert evidence["missing_evidence_rows"] == 1, label


def test_missing_product_cost_or_blank_product_identity_suppresses_profit() -> None:
    with isolated_database():
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                [
                    ("SKU-NO-COST", "Unknown", None, 20, 2),
                    ("   ", "Blank", 10.0, 20, 2),
                ],
            )
            for order in [
                ("NO-PRODUCT", "MISSING", "web", 1, 20.0, 20.0,
                 "2026-09-01", "paid", "A", "1"),
                ("NO-COST", "SKU-NO-COST", "web", 1, 20.0, 20.0,
                 "2026-09-01", "paid", "B", "2"),
                ("BLANK-PRODUCT", "   ", "web", 1, 20.0, 20.0,
                 "2026-09-01", "paid", "C", "3"),
            ]:
                _insert_order(connection, order)

        evidence = goals._actual_evidence("profit", "2026-09")
        assert evidence == {
            "value": None,
            "complete": False,
            "missing_evidence_rows": 3,
        }


def test_goal_progress_marks_incomplete_actual_as_unavailable() -> None:
    with isolated_database():
        goals.set_goal("2026-09", "profit", 100.0)
        with db.conn() as connection:
            connection.execute(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                ("SKU-NO-COST", "Unknown", None, 50, 5),
            )
            _insert_order(
                connection,
                ("ORDER", "SKU-NO-COST", "web", 1, 50.0, 50.0,
                 "2026-09-01", "paid", "Buyer", "0811"),
            )

        progress = goals.goals_for_period("2026-09")
        assert len(progress) == 1
        assert progress[0]["actual"] is None
        assert progress[0]["pct"] is None
        assert progress[0]["status"] == "unavailable"
        assert progress[0]["evidence_complete"] is False
        assert progress[0]["missing_evidence_rows"] == 1
        assert goals.summary("2026-09")["unavailable"] == 1
        assert goals.summary("2026-09")["at_risk"] == 0


def test_blank_status_only_suppresses_the_period_it_belongs_to() -> None:
    with isolated_database():
        with db.conn() as connection:
            connection.execute(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                ("SKU-GOOD", "Good", 10.0, 20, 3),
            )
            _insert_order(
                connection,
                ("SEPTEMBER", "SKU-GOOD", "web", 1, 20.0, 20.0,
                 "2026-09-01", "paid", "Buyer", "0811"),
            )
            _insert_order(
                connection,
                ("AUGUST-BLANK", "SKU-GOOD", "web", 1, 20.0, 20.0,
                 "2026-08-31", "   ", "Older", "0822"),
            )

        assert goals._actual_evidence("revenue", "2026-09") == {
            "value": 20.0,
            "complete": True,
            "missing_evidence_rows": 0,
        }
        assert goals._actual_evidence("revenue", "2026-08") == {
            "value": None,
            "complete": False,
            "missing_evidence_rows": 1,
        }


if __name__ == "__main__":
    test_actuals_use_canonical_totals_dates_order_grain_and_costs()
    test_incomplete_or_blank_order_evidence_suppresses_exact_actuals()
    test_missing_product_cost_or_blank_product_identity_suppresses_profit()
    test_goal_progress_marks_incomplete_actual_as_unavailable()
    test_blank_status_only_suppresses_the_period_it_belongs_to()
    print("goals actual metric evidence: 5 passed")
