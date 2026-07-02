"""Promotion Engine — plan flash sales, track coupons, measure ROI.

Thai reseller promos:
  - Flash sales (12.12, 9.9, etc.)
  - Coupon codes (LINE, live stream giveaways)
  - Bundle deals
  - Free shipping threshold

Track what works, kill what doesn't."""
from __future__ import annotations

import json
from datetime import datetime, date

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                promo_type TEXT NOT NULL,
                platform TEXT DEFAULT 'all',
                start_date TEXT,
                end_date TEXT,
                discount_type TEXT DEFAULT 'percent',
                discount_value REAL DEFAULT 0,
                min_order REAL DEFAULT 0,
                max_discount REAL DEFAULT 0,
                coupon_code TEXT DEFAULT '',
                budget REAL DEFAULT 0,
                spent REAL DEFAULT 0,
                redemptions INTEGER DEFAULT 0,
                revenue_generated REAL DEFAULT 0,
                status TEXT DEFAULT 'draft',
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


PROMO_TYPES = {
    "flash_sale":    {"icon": "⚡"},
    "coupon":        {"icon": "🎟️"},
    "free_shipping": {"icon": "🚚"},
    "bundle":        {"icon": "🎁"},
    "threshold":     {"icon": "💰"},
    "bogo":          {"icon": "🤝"},
}

DISCOUNT_TYPES = ["percent", "fixed", "free_ship"]

STATUSES = ["draft", "active", "ended", "cancelled"]


def add(name: str, promo_type: str, platform: str = "all",
        start_date: str = "", end_date: str = "",
        discount_type: str = "percent", discount_value: float = 0,
        min_order: float = 0, max_discount: float = 0,
        coupon_code: str = "", budget: float = 0, note: str = "") -> int:
    with db.conn() as c:
        c.execute(
            "INSERT INTO promotions "
            "(name, promo_type, platform, start_date, end_date, "
            "discount_type, discount_value, min_order, max_discount, "
            "coupon_code, budget, note) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (name, promo_type, platform, start_date, end_date,
             discount_type, discount_value, min_order, max_discount,
             coupon_code, budget, note),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_status(promo_id: int, status: str):
    with db.conn() as c:
        c.execute("UPDATE promotions SET status=? WHERE id=?",
                  (status, promo_id))


def record_redemption(promo_id: int, discount_given: float, order_revenue: float):
    """Record a coupon/promo redemption."""
    with db.conn() as c:
        c.execute(
            "UPDATE promotions SET "
            "redemptions=redemptions+1, "
            "spent=spent+?, "
            "revenue_generated=revenue_generated+? "
            "WHERE id=?",
            (discount_given, order_revenue, promo_id),
        )


def delete(promo_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM promotions WHERE id=?", (promo_id,))


def all_promos() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM promotions ORDER BY created_at DESC"
        ).fetchall()
    results = []
    for r in rows:
        d = dict(r)
        # Calculate ROI
        spent = d.get("spent") or 0
        revenue = d.get("revenue_generated") or 0
        d["roi"] = round((revenue - spent) / spent * 100, 1) if spent > 0 else 0
        d["budget_used_pct"] = round(spent / d["budget"] * 100, 1) if d.get("budget") else 0
        results.append(d)
    return results


def active_promos() -> list[dict]:
    return [p for p in all_promos() if p["status"] == "active"]


def stats() -> dict:
    promos = all_promos()
    active = [p for p in promos if p["status"] == "active"]
    total_budget = sum(p.get("budget") or 0 for p in promos)
    total_spent = sum(p.get("spent") or 0 for p in promos)
    total_revenue = sum(p.get("revenue_generated") or 0 for p in promos)
    total_redemptions = sum(p.get("redemptions") or 0 for p in promos)

    return {
        "total": len(promos),
        "active": len(active),
        "total_budget": total_budget,
        "total_spent": total_spent,
        "total_revenue": total_revenue,
        "total_redemptions": total_redemptions,
        "overall_roi": round((total_revenue - total_spent) / total_spent * 100, 1) if total_spent > 0 else 0,
    }
