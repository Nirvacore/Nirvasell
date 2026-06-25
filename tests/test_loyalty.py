"""Tests for loyalty.py — points, tiers, redemption, and leaderboard."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from unittest.mock import patch

import pytest

# In-memory SQLite wired through db.conn()
_mem_db: sqlite3.Connection | None = None


@contextmanager
def _mem_conn():
    global _mem_db
    if _mem_db is None:
        _mem_db = sqlite3.connect(":memory:")
        _mem_db.row_factory = sqlite3.Row
        _mem_db.execute("PRAGMA foreign_keys = ON")
    try:
        yield _mem_db
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
        import loyalty
        loyalty.init()
        yield


# ---------------------------------------------------------------------------
# _determine_tier
# ---------------------------------------------------------------------------

class TestDetermineTier:
    def test_zero_points_is_bronze(self):
        from loyalty import _determine_tier
        assert _determine_tier(0) == "bronze"

    def test_499_is_bronze(self):
        from loyalty import _determine_tier
        assert _determine_tier(499) == "bronze"

    def test_500_is_silver(self):
        from loyalty import _determine_tier
        assert _determine_tier(500) == "silver"

    def test_1999_is_silver(self):
        from loyalty import _determine_tier
        assert _determine_tier(1999) == "silver"

    def test_2000_is_gold(self):
        from loyalty import _determine_tier
        assert _determine_tier(2000) == "gold"

    def test_5000_is_platinum(self):
        from loyalty import _determine_tier
        assert _determine_tier(5000) == "platinum"

    def test_15000_is_diamond(self):
        from loyalty import _determine_tier
        assert _determine_tier(15000) == "diamond"

    def test_huge_points_is_diamond(self):
        from loyalty import _determine_tier
        assert _determine_tier(999999) == "diamond"


# ---------------------------------------------------------------------------
# earn_points
# ---------------------------------------------------------------------------

class TestEarnPoints:
    def test_earn_from_purchase(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            result = loyalty.earn_points("cust-001", 250.0)
        assert result["earned"] == 250
        assert result["balance"] == 250
        assert result["tier"] == "bronze"

    def test_earn_zero_amount_returns_zero(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            result = loyalty.earn_points("cust-001", 0)
        assert result == {"earned": 0}

    def test_earn_negative_amount_returns_zero(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            result = loyalty.earn_points("cust-001", -50)
        assert result == {"earned": 0}

    def test_earn_accumulates_points(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 300)
            result = loyalty.earn_points("cust-001", 250)
        assert result["balance"] == 550
        assert result["tier"] == "silver"

    def test_earn_promotes_tier_to_gold(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 2000)
            result = loyalty.earn_points("cust-001", 100)
        assert result["tier"] == "gold"

    def test_earn_creates_history_record(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 100)
            info = loyalty.customer_loyalty("cust-001")
        assert len(info["history"]) == 1
        assert info["history"][0]["action"] == "earn"
        assert info["history"][0]["points"] == 100

    def test_earn_fractional_amount_truncates(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            result = loyalty.earn_points("cust-001", 99.9)
        assert result["earned"] == 99

    def test_custom_description_recorded(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 100, description="โปรโมชั่น")
            info = loyalty.customer_loyalty("cust-001")
        assert info["history"][0]["description"] == "โปรโมชั่น"

    def test_default_description_is_purchase(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 100)
            info = loyalty.customer_loyalty("cust-001")
        assert info["history"][0]["description"] == "ซื้อสินค้า"


# ---------------------------------------------------------------------------
# redeem_points
# ---------------------------------------------------------------------------

class TestRedeemPoints:
    def test_redeem_free_shipping(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 500)
            result = loyalty.redeem_points("cust-001", "free_ship")
        assert result["success"] is True
        assert result["balance"] == 400
        assert result["reward"] == "ส่งฟรี"

    def test_redeem_insufficient_points(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 50)
            result = loyalty.redeem_points("cust-001", "free_ship")
        assert result["success"] is False
        assert "แต้มไม่พอ" in result["error"]

    def test_redeem_unknown_reward(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            result = loyalty.redeem_points("cust-001", "nonexistent")
        assert result["success"] is False
        assert "ไม่พบรางวัลนี้" in result["error"]

    def test_redeem_unenrolled_customer(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            result = loyalty.redeem_points("cust-new", "free_ship")
        assert result["success"] is False

    def test_redeem_deducts_correct_amount(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 1000)
            loyalty.redeem_points("cust-001", "discount_10")  # costs 500
            info = loyalty.customer_loyalty("cust-001")
        assert info["points"] == 500

    def test_redeem_records_history(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 500)
            loyalty.redeem_points("cust-001", "free_ship")
            info = loyalty.customer_loyalty("cust-001")
        actions = [h["action"] for h in info["history"]]
        assert "redeem" in actions
        redeem_entry = next(h for h in info["history"] if h["action"] == "redeem")
        assert redeem_entry["points"] == -100
        assert redeem_entry["balance_after"] == 400


# ---------------------------------------------------------------------------
# customer_loyalty
# ---------------------------------------------------------------------------

class TestCustomerLoyalty:
    def test_unenrolled_customer(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            info = loyalty.customer_loyalty("nobody")
        assert info["enrolled"] is False
        assert info["customer_key"] == "nobody"

    def test_enrolled_customer_has_full_info(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 600)
            info = loyalty.customer_loyalty("cust-001")
        assert info["enrolled"] is True
        assert info["points"] == 600
        assert info["tier"] == "silver"
        assert info["discount_pct"] == 3
        assert "tier_icon" in info
        assert "tier_label" in info

    def test_next_tier_info_present(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 600)
            info = loyalty.customer_loyalty("cust-001")
        assert info["next_tier"] is not None
        assert info["next_tier"]["name"] == "gold"
        assert info["next_tier"]["points_needed"] == 1400

    def test_diamond_has_no_next_tier(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 20000)
            info = loyalty.customer_loyalty("cust-001")
        assert info["tier"] == "diamond"
        assert info["next_tier"] is None

    def test_history_limited_to_20(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            for i in range(25):
                loyalty.earn_points("cust-001", 10)
            info = loyalty.customer_loyalty("cust-001")
        assert len(info["history"]) == 20


# ---------------------------------------------------------------------------
# leaderboard
# ---------------------------------------------------------------------------

class TestLeaderboard:
    def test_empty_leaderboard(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            board = loyalty.leaderboard()
        assert board == []

    def test_leaderboard_sorted_by_lifetime(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("low", 100)
            loyalty.earn_points("high", 5000)
            loyalty.earn_points("mid", 1000)
            board = loyalty.leaderboard()
        assert board[0]["customer_key"] == "high"
        assert board[1]["customer_key"] == "mid"
        assert board[2]["customer_key"] == "low"
        assert board[0]["rank"] == 1

    def test_leaderboard_limit(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            for i in range(10):
                loyalty.earn_points(f"cust-{i}", 100)
            board = loyalty.leaderboard(limit=3)
        assert len(board) == 3

    def test_leaderboard_includes_tier_icon(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 500)
            board = loyalty.leaderboard()
        assert "tier_icon" in board[0]


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_empty_stats(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            s = loyalty.stats()
        assert s["members"] == 0
        assert s["total_points_outstanding"] == 0
        assert s["total_redeemed"] == 0

    def test_stats_after_activity(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("cust-001", 1000)
            loyalty.earn_points("cust-002", 500)
            loyalty.redeem_points("cust-001", "discount_5")  # 200 pts
            s = loyalty.stats()
        assert s["members"] == 2
        assert s["total_points_outstanding"] == 1300  # 800 + 500
        assert s["total_redeemed"] == 200

    def test_stats_tier_counts(self):
        import loyalty
        with patch("db.conn", _mem_conn):
            loyalty.earn_points("bronze-cust", 100)
            loyalty.earn_points("silver-cust", 600)
            s = loyalty.stats()
        assert s["tiers"]["bronze"] == 1
        assert s["tiers"]["silver"] == 1


# ---------------------------------------------------------------------------
# TIERS / REWARDS constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_tiers_ordered_by_min_points(self):
        from loyalty import TIERS
        prev = -1
        for info in TIERS.values():
            assert info["min_points"] >= prev
            prev = info["min_points"]

    def test_all_rewards_have_required_fields(self):
        from loyalty import REWARDS
        for r in REWARDS:
            assert "id" in r
            assert "name" in r
            assert "points" in r
            assert r["points"] > 0
