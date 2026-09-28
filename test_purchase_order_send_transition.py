"""Regression coverage for the atomic draft-to-sent PO transition."""

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
import purchase_orders


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_po_send_") as temp:
        db._resolve_path = lambda: Path(temp) / "user.db"
        try:
            db.init()
            purchase_orders.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def insert_po(connection, number: str, status: str) -> int:
    cursor = connection.execute(
        "INSERT INTO purchase_orders (po_number,supplier,status) VALUES (?,?,?)",
        (number, "Supplier", status),
    )
    return cursor.lastrowid


def status_of(po_id: int) -> str:
    with db.conn() as connection:
        return connection.execute(
            "SELECT status FROM purchase_orders WHERE id = ?", (po_id,)
        ).fetchone()[0]


def test_send_changes_only_one_draft_and_returns_explicit_outcome() -> None:
    with isolated_database():
        with db.conn() as connection:
            draft_id = insert_po(connection, "PO-DRAFT", "draft")

        assert purchase_orders.send(999999) is False
        assert purchase_orders.send(draft_id) is True
        assert status_of(draft_id) == "sent"
        assert purchase_orders.send(draft_id) is False
        assert status_of(draft_id) == "sent"


def test_send_rejects_cancelled_partial_and_received_without_mutation() -> None:
    with isolated_database():
        ids = {}
        with db.conn() as connection:
            for status in ("cancelled", "partial", "received"):
                ids[status] = insert_po(connection, "PO-" + status.upper(), status)

        for status, po_id in ids.items():
            assert purchase_orders.send(po_id) is False, status
            assert status_of(po_id) == status


def test_send_uses_only_the_active_per_user_database() -> None:
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_po_users_") as temp:
        active = {"path": Path(temp) / "user-a.db"}
        db._resolve_path = lambda: active["path"]
        try:
            db.init()
            purchase_orders.init()
            with db.conn() as connection:
                user_a_id = insert_po(connection, "PO-A", "draft")

            active["path"] = Path(temp) / "user-b.db"
            db.init()
            purchase_orders.init()
            with db.conn() as connection:
                user_b_id = insert_po(connection, "PO-B", "draft")

            active["path"] = Path(temp) / "user-a.db"
            assert purchase_orders.send(user_a_id) is True
            assert status_of(user_a_id) == "sent"

            active["path"] = Path(temp) / "user-b.db"
            assert user_b_id == user_a_id
            assert status_of(user_b_id) == "draft"
        finally:
            db._resolve_path = original_resolve_path


if __name__ == "__main__":
    test_send_changes_only_one_draft_and_returns_explicit_outcome()
    test_send_rejects_cancelled_partial_and_received_without_mutation()
    test_send_uses_only_the_active_per_user_database()
    print("purchase order send transition: 3 passed")
