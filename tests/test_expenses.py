"""Tests for expenses.py — expense tracking and monthly summaries."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

import pytest

# In-memory SQLite wired through db.conn()
_mem_db: sqlite3.Connection | None = None


class _ConnWrapper:
    """Thin proxy that forwards lastrowid from the most recent cursor."""

    def __init__(self, real_conn: sqlite3.Connection):
        self._conn = real_conn
        self.lastrowid: int | None = None

    def execute(self, sql, params=()):
        cur = self._conn.execute(sql, params)
        self.lastrowid = cur.lastrowid
        return cur

    def executescript(self, sql):
        return self._conn.executescript(sql)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    @property
    def row_factory(self):
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, value):
        self._conn.row_factory = value


@contextmanager
def _mem_conn():
    global _mem_db
    if _mem_db is None:
        _mem_db = sqlite3.connect(":memory:")
        _mem_db.row_factory = sqlite3.Row
        _mem_db.execute("PRAGMA foreign_keys = ON")
    wrapper = _ConnWrapper(_mem_db)
    try:
        yield wrapper
        _mem_db.commit()
    except Exception:
        _mem_db.rollback()
        raise


@pytest.fixture(autouse=True)
def _fresh_db():
    """Provide a clean in-memory database for every test."""
    global _mem_db
    _mem_db = None
    with patch("db.conn", _mem_conn):
        import expenses
        expenses.init()
        yield


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

class TestAdd:
    def test_add_basic_expense(self):
        import expenses
        with patch("db.conn", _mem_conn):
            row_id = expenses.add(
                date="2026-06-01", category="shipping", amount=150.0,
            )
        assert isinstance(row_id, int)
        assert row_id >= 1

    def test_add_stores_correct_values(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.add(
                date="2026-06-01", category="advertising",
                amount=500, note="FB Ads", platform="facebook",
            )
            rows = expenses.all_expenses()
        assert len(rows) == 1
        assert rows[0]["category"] == "advertising"
        assert rows[0]["amount"] == 500.0
        assert rows[0]["note"] == "FB Ads"
        assert rows[0]["platform"] == "facebook"

    def test_add_invalid_category_defaults_to_other(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.add(
                date="2026-06-01", category="magic", amount=100,
            )
            rows = expenses.all_expenses()
        assert rows[0]["category"] == "other"

    def test_add_negative_amount_stored_as_absolute(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.add(date="2026-06-01", category="refund", amount=-200)
            rows = expenses.all_expenses()
        assert rows[0]["amount"] == 200.0

    def test_add_strips_whitespace_from_note(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.add(
                date="2026-06-01", category="other",
                amount=50, note="  test note  ",
            )
            rows = expenses.all_expenses()
        assert rows[0]["note"] == "test note"

    def test_add_strips_whitespace_from_platform(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.add(
                date="2026-06-01", category="platform_fee",
                amount=30, platform="  shopee  ",
            )
            rows = expenses.all_expenses()
        assert rows[0]["platform"] == "shopee"

    def test_add_all_valid_categories(self):
        import expenses
        with patch("db.conn", _mem_conn):
            for i, cat in enumerate(expenses.CATEGORIES):
                expenses.add(date="2026-06-01", category=cat, amount=10)
            rows = expenses.all_expenses()
        assert len(rows) == len(expenses.CATEGORIES)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUpdate:
    def test_update_amount(self):
        import expenses
        with patch("db.conn", _mem_conn):
            eid = expenses.add(date="2026-06-01", category="shipping", amount=100)
            expenses.update(eid, amount=250)
            rows = expenses.all_expenses()
        assert rows[0]["amount"] == 250.0

    def test_update_category(self):
        import expenses
        with patch("db.conn", _mem_conn):
            eid = expenses.add(date="2026-06-01", category="shipping", amount=100)
            expenses.update(eid, category="packaging")
            rows = expenses.all_expenses()
        assert rows[0]["category"] == "packaging"

    def test_update_invalid_category_defaults_to_other(self):
        import expenses
        with patch("db.conn", _mem_conn):
            eid = expenses.add(date="2026-06-01", category="shipping", amount=100)
            expenses.update(eid, category="invalid_cat")
            rows = expenses.all_expenses()
        assert rows[0]["category"] == "other"

    def test_update_negative_amount_stored_as_absolute(self):
        import expenses
        with patch("db.conn", _mem_conn):
            eid = expenses.add(date="2026-06-01", category="shipping", amount=100)
            expenses.update(eid, amount=-300)
            rows = expenses.all_expenses()
        assert rows[0]["amount"] == 300.0

    def test_update_ignores_disallowed_fields(self):
        import expenses
        with patch("db.conn", _mem_conn):
            eid = expenses.add(date="2026-06-01", category="shipping", amount=100)
            expenses.update(eid, id=999, created_at="hacked")
            rows = expenses.all_expenses()
        assert rows[0]["id"] == eid

    def test_update_with_no_valid_fields_is_noop(self):
        import expenses
        with patch("db.conn", _mem_conn):
            eid = expenses.add(date="2026-06-01", category="shipping", amount=100)
            expenses.update(eid, foo="bar", baz=42)
            rows = expenses.all_expenses()
        assert rows[0]["amount"] == 100.0

    def test_update_multiple_fields(self):
        import expenses
        with patch("db.conn", _mem_conn):
            eid = expenses.add(date="2026-06-01", category="shipping", amount=100)
            expenses.update(eid, date="2026-07-15", note="Updated", amount=999)
            rows = expenses.all_expenses()
        assert rows[0]["date"] == "2026-07-15"
        assert rows[0]["note"] == "Updated"
        assert rows[0]["amount"] == 999.0


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_removes_expense(self):
        import expenses
        with patch("db.conn", _mem_conn):
            eid = expenses.add(date="2026-06-01", category="shipping", amount=100)
            expenses.delete(eid)
            rows = expenses.all_expenses()
        assert len(rows) == 0

    def test_delete_nonexistent_is_noop(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.delete(99999)  # should not raise


# ---------------------------------------------------------------------------
# all_expenses
# ---------------------------------------------------------------------------

class TestAllExpenses:
    def test_returns_empty_list_initially(self):
        import expenses
        with patch("db.conn", _mem_conn):
            rows = expenses.all_expenses()
        assert rows == []

    def test_returns_list_of_dicts(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.add(date="2026-06-01", category="shipping", amount=50)
            rows = expenses.all_expenses()
        assert isinstance(rows, list)
        assert isinstance(rows[0], dict)

    def test_filter_by_month(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.add(date="2026-06-01", category="shipping", amount=10)
            expenses.add(date="2026-06-15", category="shipping", amount=20)
            expenses.add(date="2026-07-01", category="shipping", amount=30)
            rows = expenses.all_expenses(month="2026-06")
        assert len(rows) == 2

    def test_limit_parameter(self):
        import expenses
        with patch("db.conn", _mem_conn):
            for i in range(10):
                expenses.add(date="2026-06-01", category="other", amount=i)
            rows = expenses.all_expenses(limit=3)
        assert len(rows) == 3

    def test_ordered_by_date_descending(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.add(date="2026-06-01", category="other", amount=1)
            expenses.add(date="2026-06-15", category="other", amount=2)
            expenses.add(date="2026-06-10", category="other", amount=3)
            rows = expenses.all_expenses()
        dates = [r["date"] for r in rows]
        assert dates == sorted(dates, reverse=True)


# ---------------------------------------------------------------------------
# monthly_summary
# ---------------------------------------------------------------------------

class TestMonthlySummary:
    def test_empty_month(self):
        import expenses
        with patch("db.conn", _mem_conn):
            s = expenses.monthly_summary("2026-06")
        assert s["total"] == 0
        assert s["breakdown"] == {}

    def test_summary_with_data(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.add(date="2026-06-01", category="shipping", amount=100)
            expenses.add(date="2026-06-05", category="shipping", amount=50)
            expenses.add(date="2026-06-10", category="advertising", amount=200)
            s = expenses.monthly_summary("2026-06")
        assert s["total"] == 350
        assert s["breakdown"]["shipping"] == 150
        assert s["breakdown"]["advertising"] == 200

    def test_summary_excludes_other_months(self):
        import expenses
        with patch("db.conn", _mem_conn):
            expenses.add(date="2026-06-01", category="shipping", amount=100)
            expenses.add(date="2026-07-01", category="shipping", amount=999)
            s = expenses.monthly_summary("2026-06")
        assert s["total"] == 100


# ---------------------------------------------------------------------------
# monthly_totals
# ---------------------------------------------------------------------------

class TestMonthlyTotals:
    def test_returns_list(self):
        import expenses
        with patch("db.conn", _mem_conn):
            result = expenses.monthly_totals(months=3)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_each_entry_has_month_and_total(self):
        import expenses
        with patch("db.conn", _mem_conn):
            result = expenses.monthly_totals(months=2)
        for entry in result:
            assert "month" in entry
            assert "total" in entry

    def test_oldest_first(self):
        import expenses
        with patch("db.conn", _mem_conn):
            result = expenses.monthly_totals(months=3)
        months = [e["month"] for e in result]
        assert months == sorted(months)


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_empty_stats(self):
        import expenses
        with patch("db.conn", _mem_conn):
            s = expenses.stats()
        assert s["this_month"] == 0
        assert s["last_month"] == 0
        assert s["all_time"] == 0
        assert s["count"] == 0
        assert s["change_pct"] == 0

    def test_stats_with_current_month_data(self):
        import expenses
        today = datetime.now().strftime("%Y-%m-%d")
        with patch("db.conn", _mem_conn):
            expenses.add(date=today, category="shipping", amount=100)
            expenses.add(date=today, category="advertising", amount=200)
            s = expenses.stats()
        assert s["this_month"] == 300
        assert s["count"] == 2
        assert s["all_time"] == 300

    def test_stats_change_pct_calculation(self):
        import expenses
        now = datetime.now()
        this_month = now.strftime("%Y-%m")
        # Compute last month
        if now.month == 1:
            last_month = f"{now.year - 1}-12"
        else:
            last_month = f"{now.year}-{now.month - 1:02d}"

        with patch("db.conn", _mem_conn):
            expenses.add(date=f"{last_month}-15", category="shipping", amount=200)
            expenses.add(date=f"{this_month}-15", category="shipping", amount=300)
            s = expenses.stats()
        assert s["last_month"] == 200
        assert s["this_month"] == 300
        # (300 - 200) / 200 * 100 = 50.0
        assert s["change_pct"] == 50.0


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_categories_not_empty(self):
        from expenses import CATEGORIES
        assert len(CATEGORIES) > 0

    def test_all_categories_have_icons(self):
        from expenses import CATEGORIES, CATEGORY_ICONS
        for cat in CATEGORIES:
            assert cat in CATEGORY_ICONS, f"Missing icon for category: {cat}"

    def test_no_duplicate_categories(self):
        from expenses import CATEGORIES
        assert len(CATEGORIES) == len(set(CATEGORIES))
