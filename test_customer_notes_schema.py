"""Regression coverage for the shared customer-notes schema."""
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

import customer_crm
import customer_segments
import db


@contextmanager
def isolated_db():
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_customer_notes_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path
    try:
        db.init()
        yield
    finally:
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_segments_first_keeps_typed_crm_notes_usable() -> None:
    with isolated_db():
        customer_segments.init()

        note_id = customer_crm.add_note(
            "buyer-1", "Prefers morning delivery", "preference"
        )

        assert note_id == 1
        assert customer_crm.notes_for("buyer-1")[0]["note_type"] == "preference"


def test_segments_init_upgrades_existing_untyped_notes() -> None:
    with isolated_db():
        with db.conn() as connection:
            connection.execute(
                """
                CREATE TABLE customer_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_key TEXT NOT NULL,
                    note TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                )
                """
            )
            connection.execute(
                "INSERT INTO customer_notes (customer_key, note) VALUES (?, ?)",
                ("buyer-legacy", "Existing note"),
            )

        customer_crm.init()

        notes = customer_crm.notes_for("buyer-legacy")
        assert notes[0]["note_type"] == "general"


if __name__ == "__main__":
    test_segments_first_keeps_typed_crm_notes_usable()
    test_segments_init_upgrades_existing_untyped_notes()
    print("customer notes schema: 2 passed")
