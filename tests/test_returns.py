"""Tests for returns.py — return/refund tracking, rates, and analytics."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from unittest.mock import patch

import pytest

import returns


# ---------------------------------------------------------------------------
# Helpers — in-memory SQLite
# ---------------------------------------------------------------------------

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


def _create_orders_table(conn):
    """Create the orders table that returns.stats() depends on."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            sku TEXT,
            platform TEXT,
            qty INTEGER DEFAULT 1,
            unit_price REAL,
            total_price REAL,
            order_date TEXT,
            status TEXT DEFAULT 'paid'
        )
    """)
    conn.commit()


def _seed_orders(count: int):
    """Insert N dummy orders."""
    global _mem_db
    for i in range(count):
        _mem_db.execute(
            "INSERT INTO orders (order_id, sku, platform, total_price, order_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"ORD-{i:03d}", f"SKU-{i:03d}", "shopee", 100.0 + i, "2026-06-01"),
        )
    _mem_db.commit()


@pytest.fixture(autouse=True)
def _fresh_db():
    """Provide a clean in-memory database for every test."""
    global _mem_db
    _mem_db = None
    with patch("db.conn", _mem_conn):
        # Trigger _mem_conn to initialize _mem_db
        with _mem_conn() as c:
            pass
        _create_orders_table(_mem_db)
        returns.init()
        yield


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_return_reasons_is_list(self):
        assert isinstance(returns.RETURN_REASONS, list)

    def test_return_reasons_nonempty(self):
        assert len(returns.RETURN_REASONS) > 0

    def test_expected_reasons(self):
        expected = {"wrong_item", "damaged", "not_as_described", "changed_mind",
                    "late_delivery", "size_wrong", "duplicate", "other"}
        assert set(returns.RETURN_REASONS) == expected

    def test_reason_icons_cover_all_reasons(self):
        for reason in returns.RETURN_REASONS:
            assert reason in returns.REASON_ICONS, f"Missing icon for reason: {reason}"


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

class TestInit:
    def test_creates_table(self):
        global _mem_db
        with patch("db.conn", _mem_conn):
            tables = {r[0] for r in _mem_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
        assert "returns" in tables

    def test_idempotent(self):
        with patch("db.conn", _mem_conn):
            returns.init()  # second call should not raise


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

class TestAdd:
    def test_add_basic_return(self):
        with patch("db.conn", _mem_conn):
            rid = returns.add(order_id="ORD-001", sku="SKU-001", reason="damaged")
        assert isinstance(rid, int)
        assert rid >= 1

    def test_add_stores_values(self):
        with patch("db.conn", _mem_conn):
            returns.add(
                order_id="ORD-001", sku="SKU-001", platform="shopee",
                reason="wrong_item", refund_amount=250.0,
                shipping_cost=40.0, note="Sent wrong color",
                return_date="2026-06-15",
            )
            rows = returns.all_returns()
        assert len(rows) == 1
        r = rows[0]
        assert r["order_id"] == "ORD-001"
        assert r["sku"] == "SKU-001"
        assert r["platform"] == "shopee"
        assert r["reason"] == "wrong_item"
        assert r["refund_amount"] == 250.0
        assert r["shipping_cost"] == 40.0
        assert r["note"] == "Sent wrong color"
        assert r["return_date"] == "2026-06-15"

    def test_add_invalid_reason_defaults_to_other(self):
        with patch("db.conn", _mem_conn):
            returns.add(reason="nonexistent_reason")
            rows = returns.all_returns()
        assert rows[0]["reason"] == "other"

    def test_add_defaults(self):
        with patch("db.conn", _mem_conn):
            returns.add()
            rows = returns.all_returns()
        r = rows[0]
        assert r["order_id"] == ""
        assert r["sku"] == ""
        assert r["platform"] == ""
        assert r["reason"] == "other"
        assert r["refund_amount"] == 0
        assert r["shipping_cost"] == 0
        assert r["note"] == ""

    def test_add_negative_refund_stored_as_absolute(self):
        with patch("db.conn", _mem_conn):
            returns.add(refund_amount=-500.0)
            rows = returns.all_returns()
        assert rows[0]["refund_amount"] == 500.0

    def test_add_negative_shipping_stored_as_absolute(self):
        with patch("db.conn", _mem_conn):
            returns.add(shipping_cost=-30.0)
            rows = returns.all_returns()
        assert rows[0]["shipping_cost"] == 30.0

    def test_add_auto_sets_return_date_if_empty(self):
        with patch("db.conn", _mem_conn):
            returns.add()
            rows = returns.all_returns()
        assert rows[0]["return_date"] != ""

    def test_add_explicit_return_date(self):
        with patch("db.conn", _mem_conn):
            returns.add(return_date="2025-01-15")
            rows = returns.all_returns()
        assert rows[0]["return_date"] == "2025-01-15"

    def test_add_multiple_returns(self):
        with patch("db.conn", _mem_conn):
            returns.add(order_id="ORD-001")
            returns.add(order_id="ORD-002")
            returns.add(order_id="ORD-003")
            rows = returns.all_returns()
        assert len(rows) == 3

    def test_add_all_valid_reasons(self):
        with patch("db.conn", _mem_conn):
            for reason in returns.RETURN_REASONS:
                returns.add(reason=reason)
            rows = returns.all_returns()
        reasons = [r["reason"] for r in rows]
        for expected_reason in returns.RETURN_REASONS:
            assert expected_reason in reasons


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_removes_return(self):
        with patch("db.conn", _mem_conn):
            rid = returns.add(order_id="ORD-001")
            returns.delete(rid)
            rows = returns.all_returns()
        assert len(rows) == 0

    def test_delete_nonexistent_is_noop(self):
        with patch("db.conn", _mem_conn):
            returns.delete(99999)  # Should not raise

    def test_delete_specific_return_only(self):
        with patch("db.conn", _mem_conn):
            r1 = returns.add(order_id="ORD-001")
            r2 = returns.add(order_id="ORD-002")
            returns.delete(r1)
            rows = returns.all_returns()
        assert len(rows) == 1
        assert rows[0]["order_id"] == "ORD-002"


# ---------------------------------------------------------------------------
# all_returns
# ---------------------------------------------------------------------------

class TestAllReturns:
    def test_returns_empty_list_initially(self):
        with patch("db.conn", _mem_conn):
            result = returns.all_returns()
        assert result == []

    def test_returns_list_of_dicts(self):
        with patch("db.conn", _mem_conn):
            returns.add(order_id="ORD-001")
            result = returns.all_returns()
        assert isinstance(result, list)
        assert isinstance(result[0], dict)

    def test_limit_parameter(self):
        with patch("db.conn", _mem_conn):
            for i in range(10):
                returns.add(order_id=f"ORD-{i:03d}", return_date=f"2026-06-{i+1:02d}")
            result = returns.all_returns(limit=3)
        assert len(result) == 3

    def test_ordered_by_return_date_desc(self):
        with patch("db.conn", _mem_conn):
            returns.add(order_id="ORD-001", return_date="2026-06-01")
            returns.add(order_id="ORD-002", return_date="2026-06-15")
            returns.add(order_id="ORD-003", return_date="2026-06-10")
            result = returns.all_returns()
        dates = [r["return_date"] for r in result]
        assert dates == sorted(dates, reverse=True)


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_empty_stats(self):
        with patch("db.conn", _mem_conn):
            s = returns.stats()
        assert s["total_returns"] == 0
        assert s["total_refund"] == 0
        assert s["total_shipping_cost"] == 0
        assert s["total_loss"] == 0
        assert s["return_rate"] == 0

    def test_stats_with_returns(self):
        with patch("db.conn", _mem_conn):
            _seed_orders(10)
            returns.add(order_id="ORD-001", refund_amount=100.0, shipping_cost=20.0)
            returns.add(order_id="ORD-002", refund_amount=200.0, shipping_cost=30.0)
            s = returns.stats()
        assert s["total_returns"] == 2
        assert s["total_refund"] == 300.0
        assert s["total_shipping_cost"] == 50.0
        assert s["total_loss"] == 350.0
        assert s["total_orders"] == 10

    def test_return_rate_calculation(self):
        with patch("db.conn", _mem_conn):
            _seed_orders(20)
            returns.add(order_id="ORD-001")
            returns.add(order_id="ORD-002")
            s = returns.stats()
        # 2/20 = 10%
        assert s["return_rate"] == 10.0

    def test_return_rate_zero_orders(self):
        with patch("db.conn", _mem_conn):
            returns.add(order_id="ORD-001")
            s = returns.stats()
        assert s["return_rate"] == 0  # Division by zero handled

    def test_stats_returns_dict(self):
        with patch("db.conn", _mem_conn):
            s = returns.stats()
        assert isinstance(s, dict)
        expected_keys = {"total_returns", "total_refund", "total_shipping_cost",
                         "total_loss", "total_orders", "return_rate"}
        assert expected_keys == set(s.keys())


# ---------------------------------------------------------------------------
# by_platform
# ---------------------------------------------------------------------------

class TestByPlatform:
    def test_empty(self):
        with patch("db.conn", _mem_conn):
            result = returns.by_platform()
        assert result == []

    def test_groups_by_platform(self):
        with patch("db.conn", _mem_conn):
            returns.add(platform="shopee", refund_amount=100, shipping_cost=10)
            returns.add(platform="shopee", refund_amount=200, shipping_cost=20)
            returns.add(platform="lazada", refund_amount=50, shipping_cost=5)
            result = returns.by_platform()
        assert len(result) == 2
        shopee = [r for r in result if r["platform"] == "shopee"][0]
        lazada = [r for r in result if r["platform"] == "lazada"][0]
        assert shopee["count"] == 2
        assert shopee["refund"] == 300
        assert shopee["ship"] == 30
        assert lazada["count"] == 1
        assert lazada["refund"] == 50
        assert lazada["ship"] == 5

    def test_ordered_by_count_desc(self):
        with patch("db.conn", _mem_conn):
            returns.add(platform="tiktok")
            returns.add(platform="shopee")
            returns.add(platform="shopee")
            returns.add(platform="shopee")
            returns.add(platform="lazada")
            returns.add(platform="lazada")
            result = returns.by_platform()
        counts = [r["count"] for r in result]
        assert counts == sorted(counts, reverse=True)


# ---------------------------------------------------------------------------
# by_reason
# ---------------------------------------------------------------------------

class TestByReason:
    def test_empty(self):
        with patch("db.conn", _mem_conn):
            result = returns.by_reason()
        assert result == []

    def test_groups_by_reason(self):
        with patch("db.conn", _mem_conn):
            returns.add(reason="damaged", refund_amount=100)
            returns.add(reason="damaged", refund_amount=200)
            returns.add(reason="wrong_item", refund_amount=50)
            result = returns.by_reason()
        assert len(result) == 2
        damaged = [r for r in result if r["reason"] == "damaged"][0]
        wrong = [r for r in result if r["reason"] == "wrong_item"][0]
        assert damaged["count"] == 2
        assert damaged["refund"] == 300
        assert wrong["count"] == 1
        assert wrong["refund"] == 50

    def test_ordered_by_count_desc(self):
        with patch("db.conn", _mem_conn):
            returns.add(reason="damaged")
            returns.add(reason="damaged")
            returns.add(reason="damaged")
            returns.add(reason="wrong_item")
            returns.add(reason="wrong_item")
            returns.add(reason="changed_mind")
            result = returns.by_reason()
        counts = [r["count"] for r in result]
        assert counts == sorted(counts, reverse=True)


# ---------------------------------------------------------------------------
# by_sku
# ---------------------------------------------------------------------------

class TestBySku:
    def test_empty(self):
        with patch("db.conn", _mem_conn):
            result = returns.by_sku()
        assert result == []

    def test_groups_by_sku(self):
        with patch("db.conn", _mem_conn):
            returns.add(sku="SKU-A", refund_amount=100)
            returns.add(sku="SKU-A", refund_amount=200)
            returns.add(sku="SKU-B", refund_amount=50)
            result = returns.by_sku()
        assert len(result) == 2
        sku_a = [r for r in result if r["sku"] == "SKU-A"][0]
        sku_b = [r for r in result if r["sku"] == "SKU-B"][0]
        assert sku_a["count"] == 2
        assert sku_a["refund"] == 300
        assert sku_b["count"] == 1

    def test_excludes_empty_sku(self):
        with patch("db.conn", _mem_conn):
            returns.add(sku="", refund_amount=100)
            returns.add(sku="SKU-A", refund_amount=50)
            result = returns.by_sku()
        assert len(result) == 1
        assert result[0]["sku"] == "SKU-A"

    def test_limit_parameter(self):
        with patch("db.conn", _mem_conn):
            for i in range(10):
                returns.add(sku=f"SKU-{i:03d}")
            result = returns.by_sku(limit=3)
        assert len(result) == 3

    def test_ordered_by_count_desc(self):
        with patch("db.conn", _mem_conn):
            for _ in range(5):
                returns.add(sku="SKU-TOP")
            for _ in range(3):
                returns.add(sku="SKU-MID")
            returns.add(sku="SKU-LOW")
            result = returns.by_sku()
        counts = [r["count"] for r in result]
        assert counts == sorted(counts, reverse=True)
