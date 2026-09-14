"""Goals regressions against db.init()'s real schema, using synthetic data only.

Run with: PYTHONDONTWRITEBYTECODE=1 python3 test_goals_order_schema.py
Only optional dataframe and display-label imports are stubbed; SQL, connection
routing, schema initialization and Goals behavior are the actual modules.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

try:
    import pandas  # noqa: F401
except ImportError:
    pandas_stub = types.ModuleType("pandas")
    with patch.dict(sys.modules, {"pandas": pandas_stub}):
        import db
else:
    import db

# Load the actual module without installing a fake translation module globally.
labels = types.ModuleType("i18n_inline")
labels.goal_type_label = lambda metric: metric
labels.goal_type_unit = lambda metric: ""
spec = importlib.util.spec_from_file_location("goals_under_test", Path(__file__).with_name("goals.py"))
goals = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"db": db, "i18n_inline": labels}):
    spec.loader.exec_module(goals)


@contextmanager
def isolated_db():
    with tempfile.TemporaryDirectory(prefix="nirvasell-goals-") as temp:
        path = Path(temp) / "fixture.db"
        with patch.object(db, "_resolve_path", return_value=path):
            db.init()
            goals.init()
            yield path


def add_order(order_id, *, total=100.0, qty=2, unit_price=50.0,
              when="2026-09-14", sku="SKU-1"):
    with db.conn() as connection:
        connection.execute(
            "INSERT INTO orders (order_id, sku, qty, unit_price, total_price, order_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, sku, qty, unit_price, total, when),
        )


class GoalsOrderSchemaTests(unittest.TestCase):
    def setUp(self):
        self.fixture = isolated_db()
        self.path = self.fixture.__enter__()
        self.addCleanup(self.fixture.__exit__, None, None, None)

    def test_schema_is_flat_without_invented_total_or_item_columns(self):
        with db.conn() as connection:
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(orders)")}
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn("total_price", columns)
        self.assertNotIn("total_amount", columns)
        self.assertNotIn("order_items", tables)

    def test_revenue_reads_total_price_once_not_quantity_times_total(self):
        add_order("line", total=90.0)
        self.assertEqual(goals._get_actual("revenue", "2026-09"), 90.0)

    def test_orders_counts_flat_rows_not_units(self):
        add_order("line", qty=7)
        self.assertEqual(goals._get_actual("orders", "2026-09"), 1)

    def test_average_reads_actual_total_price_and_includes_zero(self):
        add_order("paid", total=90.0)
        add_order("free", total=0.0)
        self.assertEqual(goals._get_actual("avg_order", "2026-09"), 45.0)

    def test_profit_uses_flat_order_total_quantity_and_product_cost(self):
        with db.conn() as connection:
            connection.execute("INSERT INTO products (sku, cost_price) VALUES (?, ?)", ("SKU-1", 15.0))
        add_order("line", qty=3, unit_price=50.0, total=150.0)
        self.assertEqual(goals._get_actual("profit", "2026-09"), 105.0)

    def test_discounted_profit_matches_existing_pnl_revenue_minus_cost(self):
        # Both main's P&L and SKU profit use total_price revenue minus qty*cost.
        # The importer preserves supplied total_price independently of unit_price.
        with patch.dict(sys.modules, {"db": db, "i18n_inline": labels}):
            labels.pnl_period_label = lambda **kwargs: "fixture-period"
            import expenses
            import pnl_statement
        expenses.init()
        with db.conn() as connection:
            connection.execute("INSERT INTO products (sku, cost_price) VALUES (?, ?)", ("SKU-1", 15.0))
        add_order("discounted", qty=2, unit_price=50.0, total=90.0)
        reference = pnl_statement.monthly(2026, 9)
        self.assertEqual(reference["revenue"], 90.0)
        self.assertEqual(reference["cogs"], 30.0)
        self.assertEqual(reference["gross_profit"], 60.0)
        self.assertEqual(goals._get_actual("profit", "2026-09"), reference["gross_profit"])

    def test_profit_uses_zero_actual_total_without_falling_back_to_unit_price(self):
        with db.conn() as connection:
            connection.execute("INSERT INTO products (sku, cost_price) VALUES (?, ?)", ("SKU-1", 15.0))
        add_order("free", qty=2, unit_price=50.0, total=0.0)
        self.assertEqual(goals._get_actual("profit", "2026-09"), -30.0)

    def test_profit_uses_actual_total_when_unit_price_is_missing(self):
        with db.conn() as connection:
            connection.execute("INSERT INTO products (sku, cost_price) VALUES (?, ?)", ("SKU-1", 15.0))
        add_order("missing-unit", qty=2, unit_price=None, total=90.0)
        self.assertEqual(goals._get_actual("profit", "2026-09"), 60.0)

    def test_profit_preserves_existing_missing_product_and_null_cost_fallback(self):
        with db.conn() as connection:
            connection.execute("INSERT INTO products (sku, cost_price) VALUES (?, ?)", ("NULL-COST", None))
        add_order("missing", sku="NO-PRODUCT", qty=2, unit_price=12.0, total=24.0)
        add_order("null", sku="NULL-COST", qty=3, unit_price=5.0, total=15.0)
        self.assertEqual(goals._get_actual("profit", "2026-09"), 39.0)

    def test_profit_preserves_zero_cost_zero_price_and_zero_quantity(self):
        with db.conn() as connection:
            connection.execute("INSERT INTO products (sku, cost_price) VALUES (?, ?)", ("FREE-COST", 0.0))
        add_order("zero-cost", sku="FREE-COST", qty=2, unit_price=10.0, total=20.0)
        add_order("zero-price", qty=2, unit_price=0.0, total=0.0)
        add_order("zero-qty", qty=0, unit_price=999.0, total=0.0)
        self.assertEqual(goals._get_actual("profit", "2026-09"), 20.0)

    def test_period_excludes_other_months_years_and_missing_dates(self):
        add_order("selected-start", total=10.0, qty=1, unit_price=10.0, when="2026-09-01")
        add_order("selected-end", total=30.0, qty=1, unit_price=30.0, when="2026-09-30 23:59:59")
        for index, when in enumerate(("2025-09-14", "2026-08-31", "2026-10-01", None, "not-a-date")):
            add_order(f"excluded-{index}", total=1000.0, qty=1, unit_price=1000.0, when=when)
        for metric, expected in {"revenue": 40.0, "orders": 2, "avg_order": 20.0, "profit": 40.0}.items():
            with self.subTest(metric=metric):
                self.assertEqual(goals._get_actual(metric, "2026-09"), expected)

    def test_empty_period_returns_zero_for_supported_financial_metrics(self):
        for metric in ("revenue", "orders", "avg_order", "profit"):
            with self.subTest(metric=metric):
                self.assertEqual(goals._get_actual(metric, "2026-09"), 0)

    def test_goal_progress_and_summary_use_actual_metrics(self):
        add_order("line")
        goals.set_goal("2026-09", "revenue", 100.0)
        goals.set_goal("2026-09", "orders", 1)
        goals.set_goal("2026-08", "revenue", 1000.0)
        rows = goals.goals_for_period("2026-09")
        self.assertEqual({row["metric"]: row["actual"] for row in rows}, {"revenue": 100.0, "orders": 1})
        self.assertTrue(all(row["pct"] == 100 and row["status"] == "achieved" for row in rows))
        self.assertEqual(goals.summary("2026-09"), {"total": 2, "achieved": 2, "on_track": 0, "behind": 0, "at_risk": 0})

    def test_new_customers_uses_only_real_initialized_buyer_columns(self):
        # No ALTER TABLE in this test: buyer columns must come from real db.init().
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO orders (order_id, order_date, buyer_phone, buyer_name) VALUES (?, ?, ?, ?)",
                [("a", "2026-09-01", "phone-a", "Alice"),
                 ("a-repeat", "2026-09-02", "phone-a", "Alice"),
                 ("b", "2026-09-30", None, "Bob"),
                 ("anonymous", "2026-09-14", None, None),
                 ("older", "2025-09-01", "phone-old", "Old")],
            )
        self.assertEqual(goals._get_actual("new_customers", "2026-09"), 2)
        self.assertEqual(goals._get_actual("new_customers", "2026-08"), 0)

    def test_connection_routes_to_fixture_and_restores_nested_user_route(self):
        outer_resolver = db._resolve_path
        add_order("first-user", total=100.0)
        with db.conn() as connection:
            self.assertEqual(Path(connection.execute("PRAGMA database_list").fetchone()[2]).resolve(), self.path.resolve())
        with isolated_db():
            self.assertEqual(goals._get_actual("orders", "2026-09"), 0)
            add_order("second-user", total=250.0)
            self.assertEqual(goals._get_actual("revenue", "2026-09"), 250.0)
        self.assertIs(db._resolve_path, outer_resolver)
        self.assertEqual(goals._get_actual("revenue", "2026-09"), 100.0)

    def test_isolation_never_invokes_auth_and_restores_resolver_after_error(self):
        original_resolver = db._resolve_path
        auth = types.ModuleType("auth")
        def unexpected_auth_route():
            self.fail("test reached a real-user resolver")
        auth.user_db_path = unexpected_auth_route
        with patch.dict(sys.modules, {"auth": auth}):
            with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                with isolated_db():
                    with db.conn() as connection:
                        self.assertEqual(connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 0)
                    raise RuntimeError("fixture failure")
        self.assertIs(db._resolve_path, original_resolver)


if __name__ == "__main__":
    unittest.main(verbosity=2)
