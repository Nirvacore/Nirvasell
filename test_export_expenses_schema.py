"""Regression coverage for expense CSV export against the canonical schema."""
from __future__ import annotations

import csv
import io
import sys
import tempfile
import types
from datetime import date
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        fake_pandas.notna = lambda value: value is not None
        sys.modules["pandas"] = fake_pandas

import db
import expenses
import export_center


def test_export_expenses_reads_note_without_legacy_description() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-export-expenses-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            expenses.init()
            note = 'ค่าส่ง, "พัสดุ"\nสองชิ้น'
            expenses.add(
                date=date.today().isoformat(),
                category="shipping",
                amount=25.0,
                note=note,
            )

            text = export_center.export_expenses(months=1)
            assert text.startswith("\ufeff")
            rows = list(csv.reader(io.StringIO(text.removeprefix("\ufeff"))))
            assert rows == [
                ["วันที่", "หมวดหมู่", "จำนวนเงิน", "รายละเอียด"],
                [date.today().isoformat(), "shipping", "25.0", note],
            ]
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_export_expenses_reads_note_without_legacy_description()
    print("export expenses schema: 1 passed")
