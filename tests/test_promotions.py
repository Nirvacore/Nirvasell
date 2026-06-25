"""Tests for promotions.py — flash sales, coupons, discounts, and promo lifecycle."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from unittest.mock import patch

import pytest

import promotions


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


@pytest.fixture(autouse=True)
def _fresh_db():
    """Provide a clean in-memory database for every test."""
    global _mem_db
    _mem_db = None
    with patch("db.conn", _mem_conn):
        promotions.init()
        yield


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_promo_types_has_expected_keys(self):
        expected = {"percentage_off", "fixed_off", "flash_sale", "buy_x_get_y", "free_shipping", "bundle_deal"}
        assert set(promotions.PROMO_TYPES.keys()) == expected

    def test_promo_types_have_labels_and_icons(self):
        for key, val in promotions.PROMO_TYPES.items():
            assert "label" in val, f"Missing label for {key}"
            assert "icon" in val, f"Missing icon for {key}"

    def test_statuses_has_expected_keys(self):
        expected = {"draft", "active", "paused", "ended"}
        assert set(promotions.STATUSES.keys()) == expected

    def test_statuses_have_labels_and_colors(self):
        for key, val in promotions.STATUSES.items():
            assert "label" in val, f"Missing label for {key}"
            assert "color" in val, f"Missing color for {key}"
            assert "icon" in val, f"Missing icon for {key}"


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
        assert "promotions" in tables

    def test_idempotent(self):
        with patch("db.conn", _mem_conn):
            promotions.init()  # second call should not raise


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

class TestCreate:
    def test_create_basic_promotion(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Summer Sale", discount_value=10)
        assert isinstance(pid, int)
        assert pid >= 1

    def test_create_sets_draft_status(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Draft Promo")
            promos = promotions.all_promos()
        assert len(promos) == 1
        assert promos[0]["status"] == "draft"

    def test_create_stores_all_fields(self):
        with patch("db.conn", _mem_conn):
            promotions.create(
                "fixed_off", "Fixed Discount",
                discount_value=50, min_order=500, min_qty=2,
                max_uses=100, coupon_code="SAVE50",
                sku_filter="SKU-001", start_dt="2026-06-01",
                end_dt="2026-06-30", notes="Test notes",
            )
            promos = promotions.all_promos()
        p = promos[0]
        assert p["promo_type"] == "fixed_off"
        assert p["title"] == "Fixed Discount"
        assert p["discount_value"] == 50
        assert p["min_order_amount"] == 500
        assert p["min_qty"] == 2
        assert p["max_uses"] == 100
        assert p["coupon_code"] == "SAVE50"
        assert p["sku_filter"] == "SKU-001"
        assert p["start_dt"] == "2026-06-01"
        assert p["end_dt"] == "2026-06-30"
        assert p["notes"] == "Test notes"

    def test_create_defaults(self):
        with patch("db.conn", _mem_conn):
            promotions.create("percentage_off", "Minimal Promo")
            promos = promotions.all_promos()
        p = promos[0]
        assert p["discount_value"] == 0
        assert p["min_order_amount"] == 0
        assert p["min_qty"] == 1
        assert p["max_uses"] == 0
        assert p["use_count"] == 0
        assert p["coupon_code"] == ""

    def test_create_multiple(self):
        with patch("db.conn", _mem_conn):
            id1 = promotions.create("percentage_off", "Promo 1")
            id2 = promotions.create("fixed_off", "Promo 2")
            assert id1 != id2
            promos = promotions.all_promos()
        assert len(promos) == 2


# ---------------------------------------------------------------------------
# Status transitions: activate / pause / end
# ---------------------------------------------------------------------------

class TestStatusTransitions:
    def test_activate(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Activatable")
            promotions.activate(pid)
            promos = promotions.all_promos()
        assert promos[0]["status"] == "active"

    def test_pause(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Pausable")
            promotions.activate(pid)
            promotions.pause(pid)
            promos = promotions.all_promos()
        assert promos[0]["status"] == "paused"

    def test_end(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Endable")
            promotions.activate(pid)
            promotions.end(pid)
            promos = promotions.all_promos()
        assert promos[0]["status"] == "ended"

    def test_full_lifecycle(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("flash_sale", "Lifecycle Test")
            promos = promotions.all_promos()
            assert promos[0]["status"] == "draft"

            promotions.activate(pid)
            promos = promotions.all_promos()
            assert promos[0]["status"] == "active"

            promotions.pause(pid)
            promos = promotions.all_promos()
            assert promos[0]["status"] == "paused"

            promotions.activate(pid)
            promos = promotions.all_promos()
            assert promos[0]["status"] == "active"

            promotions.end(pid)
            promos = promotions.all_promos()
            assert promos[0]["status"] == "ended"


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_draft_promotion(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Delete Me")
            promotions.delete(pid)
            promos = promotions.all_promos()
        assert len(promos) == 0

    def test_delete_only_works_on_draft(self):
        """Active promotions cannot be deleted."""
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Active Promo")
            promotions.activate(pid)
            promotions.delete(pid)
            promos = promotions.all_promos()
        assert len(promos) == 1  # Still there

    def test_delete_nonexistent_is_noop(self):
        with patch("db.conn", _mem_conn):
            promotions.delete(99999)  # Should not raise


# ---------------------------------------------------------------------------
# all_promos
# ---------------------------------------------------------------------------

class TestAllPromos:
    def test_returns_empty_list_initially(self):
        with patch("db.conn", _mem_conn):
            result = promotions.all_promos()
        assert result == []

    def test_returns_list_of_dicts(self):
        with patch("db.conn", _mem_conn):
            promotions.create("percentage_off", "Test")
            result = promotions.all_promos()
        assert isinstance(result, list)
        assert isinstance(result[0], dict)

    def test_filter_by_status(self):
        with patch("db.conn", _mem_conn):
            p1 = promotions.create("percentage_off", "Draft Promo")
            p2 = promotions.create("fixed_off", "Active Promo")
            promotions.activate(p2)

            drafts = promotions.all_promos(status="draft")
            actives = promotions.all_promos(status="active")
        assert len(drafts) == 1
        assert drafts[0]["title"] == "Draft Promo"
        assert len(actives) == 1
        assert actives[0]["title"] == "Active Promo"

    def test_limit(self):
        with patch("db.conn", _mem_conn):
            for i in range(10):
                promotions.create("percentage_off", f"Promo {i}")
            result = promotions.all_promos(limit=3)
        assert len(result) == 3

    def test_includes_promo_info(self):
        with patch("db.conn", _mem_conn):
            promotions.create("flash_sale", "Flash!")
            result = promotions.all_promos()
        assert "promo_info" in result[0]
        assert result[0]["promo_info"]["label"] == "Flash Sale"

    def test_includes_status_info(self):
        with patch("db.conn", _mem_conn):
            promotions.create("percentage_off", "Draft Status")
            result = promotions.all_promos()
        assert "status_info" in result[0]
        assert result[0]["status_info"]["label"] == promotions.STATUSES["draft"]["label"]


# ---------------------------------------------------------------------------
# active_promos
# ---------------------------------------------------------------------------

class TestActivePromos:
    def test_returns_only_active_promos(self):
        with patch("db.conn", _mem_conn):
            p1 = promotions.create("percentage_off", "Active One")
            p2 = promotions.create("percentage_off", "Still Draft")
            promotions.activate(p1)
            result = promotions.active_promos()
        assert len(result) == 1
        assert result[0]["title"] == "Active One"

    def test_returns_empty_when_none_active(self):
        with patch("db.conn", _mem_conn):
            promotions.create("percentage_off", "Just a Draft")
            result = promotions.active_promos()
        assert result == []

    def test_excludes_ended_promos(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Was Active")
            promotions.activate(pid)
            promotions.end(pid)
            result = promotions.active_promos()
        assert result == []

    def test_includes_promo_info_and_status_info(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("bundle_deal", "Bundle")
            promotions.activate(pid)
            result = promotions.active_promos()
        assert result[0]["promo_info"]["label"] == "ซื้อเป็นชุด"
        assert result[0]["status_info"]["label"] == "กำลังใช้"


# ---------------------------------------------------------------------------
# apply_to_order
# ---------------------------------------------------------------------------

class TestApplyToOrder:
    def test_percentage_off(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "10% Off", discount_value=10)
            promotions.activate(pid)
            result = promotions.apply_to_order(1000.0, pid)
        assert result["discount"] == 100.0
        assert result["final"] == 900.0
        assert result["promo_type"] == "percentage_off"

    def test_fixed_off(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("fixed_off", "50 Baht Off", discount_value=50)
            promotions.activate(pid)
            result = promotions.apply_to_order(200.0, pid)
        assert result["discount"] == 50
        assert result["final"] == 150.0

    def test_fixed_off_capped_at_order_total(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("fixed_off", "Huge Discount", discount_value=500)
            promotions.activate(pid)
            result = promotions.apply_to_order(100.0, pid)
        assert result["discount"] == 100.0
        assert result["final"] == 0.0

    def test_flash_sale_uses_percentage(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("flash_sale", "Flash 20%", discount_value=20)
            promotions.activate(pid)
            result = promotions.apply_to_order(500.0, pid)
        assert result["discount"] == 100.0
        assert result["final"] == 400.0

    def test_free_shipping_discount_is_zero(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("free_shipping", "Free Ship")
            promotions.activate(pid)
            result = promotions.apply_to_order(300.0, pid)
        assert result["discount"] == 0
        assert result["final"] == 300.0

    def test_promo_not_found(self):
        with patch("db.conn", _mem_conn):
            result = promotions.apply_to_order(100.0, 99999)
        assert result["error"] == "promo_not_found"
        assert result["discount"] == 0
        assert result["final"] == 100.0

    def test_draft_promo_not_applied(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Still Draft", discount_value=10)
            result = promotions.apply_to_order(100.0, pid)
        assert result["error"] == "promo_not_found"

    def test_min_order_not_met(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Min Order", discount_value=10, min_order=500)
            promotions.activate(pid)
            result = promotions.apply_to_order(100.0, pid)
        assert result["discount"] == 0
        assert result["final"] == 100.0
        assert "min_order" in result["error"]

    def test_min_order_met(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Min Order OK", discount_value=10, min_order=500)
            promotions.activate(pid)
            result = promotions.apply_to_order(600.0, pid)
        assert result["discount"] == 60.0
        assert result["final"] == 540.0

    def test_use_count_increments(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Counter", discount_value=5)
            promotions.activate(pid)
            promotions.apply_to_order(100.0, pid)
            promotions.apply_to_order(200.0, pid)
            promos = promotions.all_promos()
        promo = [p for p in promos if p["id"] == pid][0]
        assert promo["use_count"] == 2

    def test_buy_x_get_y_discount_is_zero(self):
        """buy_x_get_y falls into the else branch -> discount=0."""
        with patch("db.conn", _mem_conn):
            pid = promotions.create("buy_x_get_y", "BOGO", discount_value=1)
            promotions.activate(pid)
            result = promotions.apply_to_order(500.0, pid)
        assert result["discount"] == 0
        assert result["final"] == 500.0

    def test_percentage_off_rounding(self):
        with patch("db.conn", _mem_conn):
            pid = promotions.create("percentage_off", "Odd %", discount_value=33.33)
            promotions.activate(pid)
            result = promotions.apply_to_order(100.0, pid)
        assert result["discount"] == 33.33
        assert result["final"] == 66.67


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_empty_stats(self):
        with patch("db.conn", _mem_conn):
            s = promotions.stats()
        assert s["total"] == 0
        assert s["active"] == 0
        assert s["total_uses"] == 0

    def test_stats_with_data(self):
        with patch("db.conn", _mem_conn):
            p1 = promotions.create("percentage_off", "Active", discount_value=10)
            p2 = promotions.create("fixed_off", "Draft")
            promotions.activate(p1)
            promotions.apply_to_order(100.0, p1)
            promotions.apply_to_order(200.0, p1)
            s = promotions.stats()
        assert s["total"] == 2
        assert s["active"] == 1
        assert s["total_uses"] == 2

    def test_stats_returns_dict(self):
        with patch("db.conn", _mem_conn):
            s = promotions.stats()
        assert isinstance(s, dict)
        assert "total" in s
        assert "active" in s
        assert "total_uses" in s
