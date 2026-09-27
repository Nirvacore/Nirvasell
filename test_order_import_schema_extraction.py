"""Regression coverage for the bounded PR #19 order-import extraction."""
from __future__ import annotations

import math
import sqlite3
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
        fake_pandas.isna = lambda value: value is None or (
            isinstance(value, float) and math.isnan(value)
        )
        fake_pandas.notna = lambda value: not fake_pandas.isna(value)
        sys.modules["pandas"] = fake_pandas

import db
import order_import
import pick_pack


class _Rows:
    """Small DataFrame boundary double; row persistence remains real SQLite."""

    def __init__(self, rows: list[tuple[object, dict]]):
        self._rows = rows

    @property
    def empty(self) -> bool:
        return not self._rows

    def iterrows(self):
        return iter(self._rows)


def _legacy_orders_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                sku TEXT,
                product_id INTEGER,
                platform TEXT,
                qty INTEGER DEFAULT 1,
                unit_price REAL,
                total_price REAL,
                currency TEXT DEFAULT 'THB',
                order_date TEXT,
                status TEXT DEFAULT 'paid',
                imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform, order_id, sku)
            )
            """
        )
        connection.execute(
            "INSERT INTO orders (order_id, sku, platform, status) VALUES (?,?,?,?)",
            ("legacy-1", "SKU-1", "shopee", "paid"),
        )


def test_db_init_migrates_legacy_orders_idempotently_and_preserves_rows() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-order-schema-") as temp:
        path = Path(temp) / "fixture.db"
        _legacy_orders_database(path)
        original_resolver = db._resolve_path
        db._resolve_path = lambda: path
        try:
            db.init()
            db.init()
            with db.conn() as connection:
                columns = {
                    row["name"] for row in connection.execute("PRAGMA table_info(orders)")
                }
                count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            assert {
                "tracking_number",
                "carrier",
                "shipped_at",
                "buyer_name",
                "buyer_address",
                "buyer_phone",
            }.issubset(columns)
            assert count == 1
        finally:
            db._resolve_path = original_resolver


def test_marketplace_mapping_includes_shipping_address() -> None:
    mapping = order_import.map_columns(
        ["Name", "Lineitem SKU", "Shipping Address", "Shipping Phone"],
        "shopify",
    )
    assert mapping["buyer_address"] == "Shipping Address"


def test_normalize_preserves_source_indexes_when_no_columns_map() -> None:
    class Source:
        index = [4, 8]
        columns = []

    class Frame:
        def __init__(self, index=None):
            self.index = list(index or [])
            self._columns = {}

        @property
        def columns(self):
            return list(self._columns)

        def __setitem__(self, key, value):
            self._columns[key] = [value] * len(self.index)

    original_frame = order_import.pd.DataFrame
    order_import.pd.DataFrame = Frame
    try:
        normalized = order_import.normalize(
            Source(), "shopee", mapping={"order_id": None, "sku": None}
        )
    finally:
        order_import.pd.DataFrame = original_frame

    assert normalized.index == [4, 8]


def test_save_orders_reports_invalid_rows_and_never_persists_nan() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-order-import-") as temp:
        path = Path(temp) / "fixture.db"
        original_resolver = db._resolve_path
        db._resolve_path = lambda: path
        try:
            rows = _Rows([
                (7, {
                    "order_id": "bad-1",
                    "sku": float("nan"),
                    "platform": "shopee",
                }),
                (9, {
                    "order_id": "good-1",
                    "sku": "SKU-1",
                    "platform": "shopee",
                    "qty": float("nan"),
                    "unit_price": float("nan"),
                    "total_price": float("nan"),
                    "currency": "   ",
                    "order_date": float("nan"),
                    "status": "",
                    "buyer_name": float("nan"),
                    "buyer_phone": float("nan"),
                    "buyer_address": "123 Main Road",
                }),
            ])

            result = order_import.save_orders_report(rows)

            assert result.inserted == 1
            assert result.skipped == 0
            assert [error.as_dict() for error in result.errors] == [{
                "row_index": 7,
                "order_id": "bad-1",
                "sku": "",
                "code": "missing_required",
                "message": "sku is required",
            }]
            with db.conn() as connection:
                saved = dict(connection.execute(
                    "SELECT * FROM orders WHERE order_id = ?", ("good-1",)
                ).fetchone())
            assert saved["qty"] == 1
            assert saved["unit_price"] == 0
            assert saved["total_price"] == 0
            assert saved["currency"] == "THB"
            assert saved["status"] == "paid"
            assert saved["buyer_name"] == ""
            assert saved["buyer_phone"] == ""
            assert saved["buyer_address"] == "123 Main Road"
            assert saved["order_date"] == ""
            assert "nan" not in {str(value).lower() for value in saved.values()}
        finally:
            db._resolve_path = original_resolver


def test_save_orders_rejects_nonblank_invalid_or_unsafe_numbers() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-order-number-") as temp:
        path = Path(temp) / "fixture.db"
        original_resolver = db._resolve_path
        db._resolve_path = lambda: path
        try:
            rows = _Rows([
                (2, {"order_id": "bad-qty", "sku": "SKU-1", "platform": "shopee", "qty": -2}),
                (4, {"order_id": "bad-unit", "sku": "SKU-2", "platform": "shopee", "unit_price": "oops"}),
                (6, {"order_id": "bad-total", "sku": "SKU-3", "platform": "shopee", "total_price": float("inf")}),
                (8, {"order_id": "good-formatted", "sku": "SKU-4", "platform": "shopee", "qty": "2.0", "unit_price": "฿ 1,200", "total_price": "2,400"}),
                (10, {"order_id": "good-blank", "sku": "SKU-5", "platform": "shopee", "qty": "   ", "unit_price": "", "total_price": "  "}),
            ])

            result = order_import.save_orders_report(rows)

            assert result.inserted == 2
            assert [error.as_dict() for error in result.errors] == [
                {"row_index": 2, "order_id": "bad-qty", "sku": "SKU-1", "code": "invalid_numeric", "message": "qty must be a positive whole number"},
                {"row_index": 4, "order_id": "bad-unit", "sku": "SKU-2", "code": "invalid_numeric", "message": "unit_price must be a finite non-negative number"},
                {"row_index": 6, "order_id": "bad-total", "sku": "SKU-3", "code": "invalid_numeric", "message": "total_price must be a finite non-negative number"},
            ]
            with db.conn() as connection:
                saved = dict(connection.execute(
                    "SELECT * FROM orders WHERE order_id = ?", ("good-formatted",)
                ).fetchone())
            assert saved["qty"] == 2
            assert saved["unit_price"] == 1200
            assert saved["total_price"] == 2400
            with db.conn() as connection:
                blank = dict(connection.execute(
                    "SELECT * FROM orders WHERE order_id = ?", ("good-blank",)
                ).fetchone())
            assert blank["qty"] == 1
            assert blank["unit_price"] == 0
            assert blank["total_price"] == 0
        finally:
            db._resolve_path = original_resolver


def test_save_orders_rolls_back_order_when_stock_update_fails() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-order-atomic-") as temp:
        path = Path(temp) / "fixture.db"
        original_resolver = db._resolve_path
        db._resolve_path = lambda: path
        try:
            db.init()
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO products (sku, name, stock) VALUES (?,?,?)",
                    ("SKU-1", "Fixture", 10),
                )
                connection.execute(
                    """
                    CREATE TRIGGER fail_stock_update
                    BEFORE UPDATE OF stock ON products
                    BEGIN
                        SELECT RAISE(ABORT, 'fixture stock failure');
                    END
                    """
                )
            rows = _Rows([
                (3, {"order_id": "atomic-1", "sku": "SKU-1", "platform": "shopee", "qty": 2}),
            ])

            result = order_import.save_orders_report(rows)

            assert result.inserted == 0
            assert len(result.errors) == 1
            assert result.errors[0].row_index == 3
            assert result.errors[0].code == "database_error"
            with db.conn() as connection:
                assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
                assert connection.execute(
                    "SELECT stock FROM products WHERE sku = ?", ("SKU-1",)
                ).fetchone()[0] == 10
        finally:
            db._resolve_path = original_resolver


def test_save_orders_reports_customer_sync_failure() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-order-customer-") as temp:
        path = Path(temp) / "fixture.db"
        original_resolver = db._resolve_path
        db._resolve_path = lambda: path
        original_customers = sys.modules.get("customers")
        recovering_customers = types.ModuleType("customers")
        customer_attempts = []
        recorded_orders = []
        recovering_customers.init = lambda: None

        def find_or_create(**kwargs):
            customer_attempts.append(kwargs)
            if len(customer_attempts) == 1:
                raise RuntimeError("fixture customer sync failure")
            return 42

        recovering_customers.find_or_create = find_or_create
        recovering_customers.record_order = lambda **kwargs: recorded_orders.append(kwargs)
        sys.modules["customers"] = recovering_customers
        try:
            rows = _Rows([
                (11, {
                    "order_id": "customer-1",
                    "sku": "SKU-1",
                    "platform": "shopee",
                    "buyer_name": "Fixture Buyer",
                    "buyer_phone": "0812345678",
                }),
            ])

            result = order_import.save_orders_report(rows)

            assert result.inserted == 1
            assert len(result.errors) == 1
            assert result.errors[0].row_index == 11
            assert result.errors[0].code == "customer_sync_error"
            assert result.import_errors == ()
            assert result.warnings == result.errors
            with db.conn() as connection:
                assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 1

            retry = order_import.save_orders_report(rows)
            assert retry.inserted == 0
            assert retry.skipped == 1
            assert retry.errors == ()
            assert len(customer_attempts) == 2
            assert recorded_orders == [{
                "customer_id": 42,
                "order_id": "customer-1",
                "platform": "shopee",
                "amount": 0,
                "order_date": "",
                "product": "SKU-1",
            }]

            conflict = _Rows([
                (12, {
                    "order_id": "customer-1",
                    "sku": "SKU-1",
                    "platform": "shopee",
                    "buyer_name": "Different Buyer",
                    "buyer_phone": "0899999999",
                    "total_price": 999,
                }),
            ])
            conflict_result = order_import.save_orders_report(conflict)
            assert conflict_result.inserted == 0
            assert conflict_result.skipped == 1
            assert conflict_result.errors == ()
            assert customer_attempts[-1] == {
                "name": "Fixture Buyer",
                "phone": "0812345678",
                "platform": "shopee",
            }
        finally:
            if original_customers is None:
                sys.modules.pop("customers", None)
            else:
                sys.modules["customers"] = original_customers
            db._resolve_path = original_resolver


def test_legacy_save_orders_does_not_label_customer_warning_as_import_failure() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-order-legacy-api-") as temp:
        path = Path(temp) / "fixture.db"
        original_resolver = db._resolve_path
        db._resolve_path = lambda: path
        original_customers = sys.modules.get("customers")
        failing_customers = types.ModuleType("customers")
        failing_customers.init = lambda: None
        failing_customers.find_or_create = lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("fixture customer sync failure")
        )
        sys.modules["customers"] = failing_customers
        try:
            rows = _Rows([
                (13, {
                    "order_id": "legacy-warning-1",
                    "sku": "SKU-1",
                    "platform": "shopee",
                    "buyer_name": "Fixture Buyer",
                }),
            ])
            assert order_import.save_orders(rows) == 1
        finally:
            if original_customers is None:
                sys.modules.pop("customers", None)
            else:
                sys.modules["customers"] = original_customers
            db._resolve_path = original_resolver


def test_line_notification_uses_sanitized_inserted_totals() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-order-notify-") as temp:
        path = Path(temp) / "fixture.db"
        original_resolver = db._resolve_path
        db._resolve_path = lambda: path
        original_settings = sys.modules.get("user_settings")
        original_notify = sys.modules.get("line_notify")
        settings = types.ModuleType("user_settings")
        settings.init = lambda: None
        settings.get = lambda key, default=None: "fixture-token" if key == "line_notify_token" else True
        sent = []
        notify = types.ModuleType("line_notify")
        notify.send = lambda token, message: sent.append((token, message))
        sys.modules["user_settings"] = settings
        sys.modules["line_notify"] = notify
        try:
            rows = _Rows([
                (20, {"order_id": "notify-1", "sku": "SKU-1", "platform": "shopee", "total_price": "฿1,200"}),
                (21, {"order_id": "notify-2", "sku": "SKU-2", "platform": "lazada", "total_price": "2,400"}),
            ])

            result = order_import.save_orders_report(rows)

            assert result.inserted == 2
            assert result.errors == ()
            assert len(sent) == 1
            assert sent[0][0] == "fixture-token"
            assert "รวม ฿3,600" in sent[0][1]
            assert "lazada, shopee" in sent[0][1]
        finally:
            if original_settings is None:
                sys.modules.pop("user_settings", None)
            else:
                sys.modules["user_settings"] = original_settings
            if original_notify is None:
                sys.modules.pop("line_notify", None)
            else:
                sys.modules["line_notify"] = original_notify
            db._resolve_path = original_resolver


def test_pick_pack_uses_canonical_migration_and_excludes_tracked_orders() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-pick-pack-") as temp:
        path = Path(temp) / "fixture.db"
        _legacy_orders_database(path)
        original_resolver = db._resolve_path
        db._resolve_path = lambda: path
        try:
            assert [row["order_id"] for row in pick_pack.pending_orders()] == ["legacy-1"]
            with db.conn() as connection:
                connection.execute(
                    "UPDATE orders SET tracking_number = ? WHERE order_id = ?",
                    ("TH123", "legacy-1"),
                )
            assert pick_pack.pending_orders() == []
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_db_init_migrates_legacy_orders_idempotently_and_preserves_rows()
    test_marketplace_mapping_includes_shipping_address()
    test_normalize_preserves_source_indexes_when_no_columns_map()
    test_save_orders_reports_invalid_rows_and_never_persists_nan()
    test_save_orders_rejects_nonblank_invalid_or_unsafe_numbers()
    test_save_orders_rolls_back_order_when_stock_update_fails()
    test_save_orders_reports_customer_sync_failure()
    test_legacy_save_orders_does_not_label_customer_warning_as_import_failure()
    test_line_notification_uses_sanitized_inserted_totals()
    test_pick_pack_uses_canonical_migration_and_excludes_tracked_orders()
    print("order import schema extraction: 10 passed")
