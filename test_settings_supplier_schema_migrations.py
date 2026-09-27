"""Regression tests for settings and supplier schema separation.

Each test uses a uniquely owned temporary SQLite database and starts from the
legacy table shape that shipped before the schemas were separated.
"""
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
import shop_settings
import supplier_directory
import supplier_mgmt


@contextmanager
def isolated_db():
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_schema_migrations_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path
    try:
        yield
    finally:
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_shop_settings_migrates_only_known_keys_from_shared_settings():
    with isolated_db():
        with db.conn() as connection:
            connection.execute(
                """
                CREATE TABLE settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.executemany(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                [
                    ("shop_name", "Legacy Shop"),
                    ("default_carrier", "flash"),
                    ("line_notify_token", "shared-setting-must-stay"),
                ],
            )

        shop_settings.init()
        shop_settings.set("shop_phone", "0800000000")
        shop_settings.init()

        assert shop_settings.get("shop_name") == "Legacy Shop"
        assert shop_settings.get("default_carrier") == "flash"
        assert shop_settings.get("shop_phone") == "0800000000"
        with db.conn() as connection:
            migrated = connection.execute(
                "SELECT key, value FROM shop_settings ORDER BY key"
            ).fetchall()
            legacy = connection.execute(
                "SELECT key, value FROM settings ORDER BY key"
            ).fetchall()

        migrated_values = {row["key"]: row["value"] for row in migrated}
        legacy_values = {row["key"]: row["value"] for row in legacy}
        assert "line_notify_token" not in migrated_values
        assert legacy_values == {
            "default_carrier": "flash",
            "line_notify_token": "shared-setting-must-stay",
            "shop_name": "Legacy Shop",
        }


def test_supplier_orders_migrate_and_release_canonical_purchase_order_name():
    with isolated_db():
        with db.conn() as connection:
            connection.execute(
                """
                CREATE TABLE supplier_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT INTO supplier_contacts (id, name) VALUES (7, 'Legacy Supplier')"
            )
            connection.execute(
                """
                CREATE TABLE purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    order_date TEXT DEFAULT (date('now','localtime')),
                    total_amount REAL DEFAULT 0,
                    items_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'ordered',
                    received_at TEXT,
                    note TEXT DEFAULT '',
                    FOREIGN KEY (supplier_id) REFERENCES supplier_contacts(id)
                )
                """
            )
            connection.execute(
                """
                INSERT INTO purchase_orders
                    (id, supplier_id, order_date, total_amount, items_count,
                     status, received_at, note)
                VALUES (11, 7, '2026-09-01', 1250, 3,
                        'received', '2026-09-03', 'legacy order')
                """
            )
            connection.execute(
                """
                CREATE TABLE po_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_id INTEGER REFERENCES purchase_orders(id) ON DELETE CASCADE,
                    sku TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX idx_po_status ON purchase_orders(status)"
            )

        supplier_directory.init()
        supplier_directory.add("Directory Supplier")
        directory_rows = supplier_directory.all_suppliers()

        with db.conn() as connection:
            migrated = connection.execute(
                "SELECT * FROM supplier_orders WHERE id = 11"
            ).fetchone()
            canonical_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='purchase_orders'"
            ).fetchone()
        assert dict(migrated) == {
            "id": 11,
            "supplier_id": 7,
            "order_date": "2026-09-01",
            "total_amount": 1250.0,
            "items_count": 3,
            "status": "received",
            "received_at": "2026-09-03",
            "note": "legacy order",
        }
        assert canonical_table is not None

        new_order_id = supplier_mgmt.add_order(
            7, total_amount=250, items_count=1, note="new order"
        )
        assert new_order_id == 12
        assert [row["id"] for row in supplier_mgmt.supplier_order_history(7)] == [
            12, 11,
        ]
        assert supplier_mgmt.total_spend() == {
            "total_spent": 1500.0,
            "total_orders": 2,
        }

        with db.conn() as connection:
            canonical_columns = {
                row["name"] for row in connection.execute(
                    "PRAGMA table_info(purchase_orders)"
                )
            }
            preserved = connection.execute(
                "SELECT total_amount FROM supplier_orders WHERE id = 11"
            ).fetchone()
            item_foreign_keys = connection.execute(
                "PRAGMA foreign_key_list(po_items)"
            ).fetchall()
            status_index = connection.execute(
                "SELECT tbl_name FROM sqlite_master "
                "WHERE type='index' AND name='idx_po_status'"
            ).fetchone()
        assert {"po_number", "supplier", "expected_date"} <= canonical_columns
        assert preserved["total_amount"] == 1250
        assert directory_rows[0]["po_count"] == 0
        assert [row["table"] for row in item_foreign_keys] == ["purchase_orders"]
        assert status_index["tbl_name"] == "purchase_orders"


def test_supplier_order_migration_fails_closed_when_hybrid_items_have_data():
    with isolated_db():
        with db.conn() as connection:
            connection.execute(
                "CREATE TABLE supplier_contacts "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT INTO supplier_contacts (id, name) VALUES (1, 'Supplier')"
            )
            connection.execute(
                """
                CREATE TABLE purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    order_date TEXT,
                    total_amount REAL,
                    items_count INTEGER,
                    status TEXT,
                    received_at TEXT,
                    note TEXT
                )
                """
            )
            connection.execute(
                "INSERT INTO purchase_orders "
                "(id, supplier_id, order_date, total_amount, items_count, status, note) "
                "VALUES (1, 1, '2026-09-01', 100, 1, 'ordered', '')"
            )
            connection.execute(
                "CREATE TABLE po_items "
                "(id INTEGER PRIMARY KEY, po_id INTEGER REFERENCES purchase_orders(id), "
                "sku TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT INTO po_items (id, po_id, sku) VALUES (1, 1, 'SKU-1')"
            )

        try:
            supplier_mgmt.init()
        except RuntimeError as exc:
            assert "po_items contains data" in str(exc)
        else:
            raise AssertionError("migration must fail closed for non-empty hybrid po_items")

        with db.conn() as connection:
            legacy_order = connection.execute(
                "SELECT id, supplier_id FROM purchase_orders"
            ).fetchone()
            item = connection.execute("SELECT id, po_id FROM po_items").fetchone()
        assert dict(legacy_order) == {"id": 1, "supplier_id": 1}
        assert dict(item) == {"id": 1, "po_id": 1}


def test_supplier_order_migration_rejects_an_incomplete_target_schema():
    with isolated_db():
        with db.conn() as connection:
            connection.execute(
                "CREATE TABLE supplier_orders "
                "(id INTEGER PRIMARY KEY, supplier_id INTEGER NOT NULL)"
            )

        try:
            supplier_mgmt.init()
        except RuntimeError as exc:
            assert "supplier_orders has an incompatible schema" in str(exc)
        else:
            raise AssertionError("migration must reject an incomplete target schema")


if __name__ == "__main__":
    tests = [
        test_shop_settings_migrates_only_known_keys_from_shared_settings,
        test_supplier_orders_migrate_and_release_canonical_purchase_order_name,
        test_supplier_order_migration_fails_closed_when_hybrid_items_have_data,
        test_supplier_order_migration_rejects_an_incomplete_target_schema,
    ]
    for test in tests:
        test()
    print(f"settings/supplier schema migration tests: {len(tests)} passed")
