"""Tests for order_analytics.py — hourly/daily distribution, peak hours,
AOV trends, repeat purchase rate, and product combos."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from unittest.mock import patch

import pytest

import order_analytics


# ---------------------------------------------------------------------------
# Helpers — in-memory SQLite with the orders table
# ---------------------------------------------------------------------------

def _make_db(rows: list[tuple]):
    """Create an in-memory DB with an orders table and return a context-manager
    that yields the connection (matching the signature of db.conn())."""
    mem = sqlite3.connect(":memory:")
    mem.row_factory = sqlite3.Row
    mem.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            sku TEXT,
            buyer_name TEXT,
            buyer_phone TEXT,
            platform TEXT,
            qty INTEGER DEFAULT 1,
            unit_price REAL,
            total_price REAL,
            total_amount REAL,
            order_date TEXT,
            status TEXT DEFAULT 'paid'
        )
    """)
    for r in rows:
        mem.execute(
            "INSERT INTO orders (order_id, sku, buyer_name, platform, qty, "
            "unit_price, total_price, total_amount, order_date) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            r,
        )
    mem.commit()

    @contextmanager
    def _conn():
        yield mem
        mem.commit()

    return _conn, mem


# ---------------------------------------------------------------------------
# hourly_distribution
# ---------------------------------------------------------------------------

class TestHourlyDistribution:

    def test_returns_list_of_dicts(self):
        rows = [
            ("O1", "SKU1", "Alice", "shopee", 1, 100, 100, 100, "2025-06-10 09:30:00"),
            ("O2", "SKU2", "Bob",   "lazada", 1, 200, 200, 200, "2025-06-10 09:45:00"),
            ("O3", "SKU3", "Carol", "shopee", 1, 300, 300, 300, "2025-06-10 14:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.hourly_distribution()

        assert isinstance(result, list)
        assert all(isinstance(r, dict) for r in result)

    def test_groups_by_hour(self):
        rows = [
            ("O1", "A", "Alice", "shopee", 1, 100, 100, 100, "2025-06-10 09:30:00"),
            ("O2", "B", "Bob",   "lazada", 1, 200, 200, 200, "2025-06-10 09:59:00"),
            ("O3", "C", "Carol", "shopee", 1, 50,  50,  50,  "2025-06-10 14:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.hourly_distribution()

        hour_map = {r["hour"]: r for r in result}
        assert hour_map[9]["count"] == 2
        assert hour_map[9]["revenue"] == 300
        assert hour_map[14]["count"] == 1

    def test_empty_table_returns_empty_list(self):
        fake_conn, mem = _make_db([])
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.hourly_distribution()
        assert result == []


# ---------------------------------------------------------------------------
# daily_distribution
# ---------------------------------------------------------------------------

class TestDailyDistribution:

    def test_groups_by_day_of_week(self):
        # 2025-06-09 is a Monday (strftime %w = 1), 2025-06-10 is Tuesday (%w = 2)
        rows = [
            ("O1", "A", "Alice", "shopee", 1, 100, 100, 100, "2025-06-09 10:00:00"),
            ("O2", "B", "Bob",   "lazada", 1, 200, 200, 200, "2025-06-10 10:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.daily_distribution()

        dow_map = {r["dow"]: r for r in result}
        assert 1 in dow_map  # Monday
        assert 2 in dow_map  # Tuesday
        assert dow_map[1]["count"] == 1
        assert dow_map[2]["revenue"] == 200

    def test_empty_returns_empty(self):
        fake_conn, mem = _make_db([])
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.daily_distribution()
        assert result == []


# ---------------------------------------------------------------------------
# peak_hours
# ---------------------------------------------------------------------------

class TestPeakHours:

    def test_returns_top_n(self):
        rows = [
            ("O1", "A", "A", "s", 1, 10,  10,  10,  "2025-06-10 08:00:00"),
            ("O2", "B", "B", "s", 1, 50,  50,  50,  "2025-06-10 12:00:00"),
            ("O3", "C", "C", "s", 1, 100, 100, 100, "2025-06-10 18:00:00"),
            ("O4", "D", "D", "s", 1, 30,  30,  30,  "2025-06-10 20:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.peak_hours(top_n=2)

        assert len(result) == 2
        # Sorted by revenue desc: hour 18 (100), hour 12 (50)
        assert result[0]["hour"] == 18
        assert result[1]["hour"] == 12

    def test_top_n_exceeding_data(self):
        rows = [
            ("O1", "A", "A", "s", 1, 100, 100, 100, "2025-06-10 08:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.peak_hours(top_n=5)
        assert len(result) == 1

    def test_empty_data(self):
        fake_conn, mem = _make_db([])
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.peak_hours()
        assert result == []


# ---------------------------------------------------------------------------
# best_day
# ---------------------------------------------------------------------------

class TestBestDay:

    def test_returns_highest_revenue_day(self):
        rows = [
            ("O1", "A", "A", "s", 1, 100, 100, 100, "2025-06-09 10:00:00"),  # Mon
            ("O2", "B", "B", "s", 1, 500, 500, 500, "2025-06-10 10:00:00"),  # Tue
            ("O3", "C", "C", "s", 1, 200, 200, 200, "2025-06-11 10:00:00"),  # Wed
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.best_day()

        assert result is not None
        assert result["revenue"] == 500

    def test_no_data_returns_none(self):
        fake_conn, mem = _make_db([])
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.best_day()
        assert result is None


# ---------------------------------------------------------------------------
# platform_trend
# ---------------------------------------------------------------------------

class TestPlatformTrend:

    def test_groups_by_month_and_platform(self):
        rows = [
            ("O1", "A", "A", "shopee", 1, 100, 100, 100, "2026-05-01 10:00:00"),
            ("O2", "B", "B", "lazada", 1, 200, 200, 200, "2026-05-15 10:00:00"),
            ("O3", "C", "C", "shopee", 1, 300, 300, 300, "2026-06-01 10:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.platform_trend(months=6)

        assert isinstance(result, list)
        assert all("platform" in r and "month" in r for r in result)

    def test_respects_months_cutoff(self):
        rows = [
            # Very old order — should be excluded with months=1
            ("O1", "A", "A", "shopee", 1, 100, 100, 100, "2020-01-01 10:00:00"),
            ("O2", "B", "B", "shopee", 1, 200, 200, 200, "2026-06-20 10:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.platform_trend(months=1)

        # Only the recent order should appear
        assert len(result) == 1
        assert result[0]["revenue"] == 200


# ---------------------------------------------------------------------------
# aov_trend
# ---------------------------------------------------------------------------

class TestAovTrend:

    def test_calculates_average_order_value(self):
        rows = [
            ("O1", "A", "A", "s", 1, 100, 100, 100, "2026-06-01 10:00:00"),
            ("O2", "B", "B", "s", 1, 300, 300, 300, "2026-06-15 10:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.aov_trend(months=6)

        assert len(result) == 1
        assert result[0]["aov"] == pytest.approx(200.0)
        assert result[0]["orders"] == 2

    def test_empty_returns_empty(self):
        fake_conn, mem = _make_db([])
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.aov_trend()
        assert result == []


# ---------------------------------------------------------------------------
# repeat_purchase_rate
# ---------------------------------------------------------------------------

class TestRepeatPurchaseRate:

    def test_counts_repeat_buyers(self):
        rows = [
            ("O1", "A", "Alice", "s", 1, 100, 100, 100, "2025-06-10 10:00:00"),
            ("O2", "B", "Alice", "s", 1, 200, 200, 200, "2025-06-11 10:00:00"),
            ("O3", "C", "Bob",   "s", 1, 300, 300, 300, "2025-06-12 10:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.repeat_purchase_rate()

        assert result["total_buyers"] == 2
        assert result["repeat_buyers"] == 1
        assert result["repeat_rate"] == pytest.approx(50.0)

    def test_no_repeat_buyers(self):
        rows = [
            ("O1", "A", "Alice", "s", 1, 100, 100, 100, "2025-06-10 10:00:00"),
            ("O2", "B", "Bob",   "s", 1, 200, 200, 200, "2025-06-11 10:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.repeat_purchase_rate()

        assert result["repeat_buyers"] == 0
        assert result["repeat_rate"] == 0.0

    def test_no_orders_returns_zero_rate(self):
        fake_conn, mem = _make_db([])
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.repeat_purchase_rate()

        assert result["total_buyers"] == 0
        assert result["repeat_rate"] == 0

    def test_ignores_blank_buyer_names(self):
        rows = [
            ("O1", "A", "",    "s", 1, 100, 100, 100, "2025-06-10 10:00:00"),
            ("O2", "B", None,  "s", 1, 200, 200, 200, "2025-06-11 10:00:00"),
            ("O3", "C", "Bob", "s", 1, 300, 300, 300, "2025-06-12 10:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.repeat_purchase_rate()

        assert result["total_buyers"] == 1  # Only Bob


# ---------------------------------------------------------------------------
# top_combos
# ---------------------------------------------------------------------------

class TestTopCombos:

    def test_finds_product_pairs(self):
        rows = [
            # Two orders with same order_id, different SKUs — bought together
            ("ORD1", "SKU-A", "A", "s", 1, 100, 100, 100, "2025-06-10 10:00:00"),
            ("ORD1", "SKU-B", "A", "s", 1, 200, 200, 200, "2025-06-10 10:00:00"),
            # Same combo again in a different order
            ("ORD2", "SKU-A", "B", "s", 1, 100, 100, 100, "2025-06-11 10:00:00"),
            ("ORD2", "SKU-B", "B", "s", 1, 200, 200, 200, "2025-06-11 10:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.top_combos(limit=5)

        assert len(result) == 1
        assert result[0]["freq"] == 2
        # sku_a < sku_b alphabetically
        assert result[0]["sku_a"] == "SKU-A"
        assert result[0]["sku_b"] == "SKU-B"

    def test_no_combos_returns_empty(self):
        rows = [
            ("O1", "A", "X", "s", 1, 100, 100, 100, "2025-06-10 10:00:00"),
            ("O2", "B", "Y", "s", 1, 200, 200, 200, "2025-06-11 10:00:00"),
        ]
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.top_combos()
        assert result == []

    def test_respects_limit(self):
        # Create 3 different combos with freq >= 2
        rows = []
        for i, (a, b) in enumerate([("A", "B"), ("C", "D"), ("E", "F")]):
            for j in range(2):
                oid = f"ORD-{i}-{j}"
                rows.append((oid, a, "X", "s", 1, 100, 100, 100, "2025-06-10 10:00:00"))
                rows.append((oid, b, "X", "s", 1, 100, 100, 100, "2025-06-10 10:00:00"))
        fake_conn, mem = _make_db(rows)
        with patch("order_analytics.db") as mock_db:
            mock_db.conn = fake_conn
            result = order_analytics.top_combos(limit=2)
        assert len(result) == 2
