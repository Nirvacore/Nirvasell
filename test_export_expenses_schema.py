"""Exercise the actual expense CSV exporter using only owned SQLite fixtures."""
from __future__ import annotations

import csv
import io
import sys
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from test_goals_order_schema import db, isolated_db

with patch.dict(sys.modules, {"db": db}):
    import expenses
    import export_center


class ExportExpensesSchemaTests(unittest.TestCase):
    def setUp(self):
        self.fixture = isolated_db()
        self.fixture.__enter__()
        self.addCleanup(self.fixture.__exit__, None, None, None)
        expenses.init()
        # Use SQLite's own UTC clock, matching the export's existing semantics.
        with db.conn() as connection:
            self.today = connection.execute("SELECT date('now')").fetchone()[0]

    def rows(self, months=3):
        text = export_center.export_expenses(months)
        self.assertTrue(text.startswith("\ufeff"))
        return list(csv.reader(io.StringIO(text.removeprefix("\ufeff"))))

    def test_empty_export_keeps_bom_and_existing_four_column_header(self):
        self.assertEqual(self.rows(), [["วันที่", "หมวดหมู่", "จำนวนเงิน", "รายละเอียด"]])

    def test_note_round_trips_thai_commas_quotes_newlines_and_zero_amount(self):
        note = 'ค่าส่ง, "พัสดุ"\nสองชิ้น'
        expenses.add(date=self.today, category="shipping", amount=0.0, note=note)
        self.assertEqual(self.rows()[1:], [[self.today, "shipping", "0.0", note]])

    def test_filter_and_sort_use_expense_date_not_created_at(self):
        with db.conn() as connection:
            cutoff = connection.execute("SELECT date('now', '-3 months')").fetchone()[0]
            before = (date.fromisoformat(cutoff) - timedelta(days=1)).isoformat()
            connection.executemany(
                "INSERT INTO expenses (date, category, amount, note, created_at) VALUES (?, ?, ?, ?, ?)",
                [(cutoff, "shipping", 1.0, "at boundary", "2000-01-01"),
                 (before, "packaging", 999.0, "excluded despite recent creation", self.today),
                 (self.today, "supplies", 3.0, "today", "2000-01-01")],
            )
        self.assertEqual(self.rows()[1:], [
            [self.today, "supplies", "3.0", "today"],
            [cutoff, "shipping", "1.0", "at boundary"],
        ])

    def test_month_parameter_preserves_narrow_and_wide_windows(self):
        with db.conn() as connection:
            earlier = connection.execute("SELECT date('now', '-2 months')").fetchone()[0]
        expenses.add(date=earlier, category="shipping", amount=2.0, note="earlier")
        expenses.add(date=self.today, category="shipping", amount=1.0, note="today")
        self.assertEqual([row[3] for row in self.rows(1)[1:]], ["today"])
        self.assertEqual([row[3] for row in self.rows(3)[1:]], ["today", "earlier"])
        self.assertEqual([row[3] for row in self.rows(0)[1:]], ["today"])

    def test_null_and_empty_notes_remain_blank_in_csv(self):
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO expenses (date, amount, note) VALUES (?, ?, ?)",
                [(self.today, 0.0, None), (self.today, 1.0, "")],
            )
        self.assertEqual(len(self.rows()), 3)
        self.assertEqual([row[3] for row in self.rows()[1:]], ["", ""])

    def test_export_uses_current_user_route_and_restores_outer_fixture(self):
        expenses.add(date=self.today, category="shipping", amount=10.0, note="first user")
        with isolated_db():
            expenses.init()
            self.assertEqual(len(self.rows()), 1)
            expenses.add(date=self.today, category="shipping", amount=20.0, note="second user")
            self.assertEqual([row[3] for row in self.rows()[1:]], ["second user"])
        self.assertEqual([row[3] for row in self.rows()[1:]], ["first user"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
