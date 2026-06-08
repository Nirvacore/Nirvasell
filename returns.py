"""Return/Refund tracker — understand what's coming back and why.

Thai marketplace sellers get penalized for high return rates:
  - Shopee: >5% return rate → lower search ranking
  - Lazada: frequent returns → seller score drops
  - TikTok: "late ship" returns counted against shop

This module tracks returns, calculates rates per platform/SKU, and
shows the financial impact on true profit."""
from __future__ import annotations

from datetime import datetime

import db


RETURN_REASONS = [
    "wrong_item",      # ส่งผิดชิ้น
    "damaged",         # เสียหาย/ชำรุด
    "not_as_described",# ไม่ตรงปก
    "changed_mind",    # เปลี่ยนใจ
    "late_delivery",   # ส่งช้า
    "size_wrong",      # ไซส์ไม่ตรง
    "duplicate",       # สั่งซ้ำ
    "other",           # อื่นๆ
]

REASON_ICONS = {
    "wrong_item": "📦",
    "damaged": "💔",
    "not_as_described": "🖼",
    "changed_mind": "🔄",
    "late_delivery": "🕐",
    "size_wrong": "📏",
    "duplicate": "👯",
    "other": "📝",
}


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id    TEXT DEFAULT '',
                sku         TEXT DEFAULT '',
                platform    TEXT DEFAULT '',
                reason      TEXT DEFAULT 'other',
                refund_amount REAL DEFAULT 0,
                shipping_cost REAL DEFAULT 0,
                note        TEXT DEFAULT '',
                return_date TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)


def add(*, order_id: str = "", sku: str = "", platform: str = "",
        reason: str = "other", refund_amount: float = 0,
        shipping_cost: float = 0, note: str = "",
        return_date: str = "") -> int:
    r = reason if reason in RETURN_REASONS else "other"
    if not return_date:
        return_date = datetime.now().strftime("%Y-%m-%d")
    with db.conn() as c:
        c.execute(
            "INSERT INTO returns (order_id, sku, platform, reason, refund_amount, "
            "shipping_cost, note, return_date) VALUES (?,?,?,?,?,?,?,?)",
            (order_id, sku, platform, r, abs(refund_amount),
             abs(shipping_cost), note, return_date),
        )
        return c.lastrowid


def delete(return_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM returns WHERE id = ?", (return_id,))


def all_returns(limit: int = 200) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM returns ORDER BY return_date DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def stats() -> dict:
    with db.conn() as c:
        total_returns = c.execute("SELECT COUNT(*) FROM returns").fetchone()[0]
        total_refund = c.execute("SELECT COALESCE(SUM(refund_amount),0) FROM returns").fetchone()[0]
        total_ship = c.execute("SELECT COALESCE(SUM(shipping_cost),0) FROM returns").fetchone()[0]
        total_orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    return_rate = (total_returns / total_orders * 100) if total_orders else 0
    return {
        "total_returns": total_returns,
        "total_refund": total_refund,
        "total_shipping_cost": total_ship,
        "total_loss": total_refund + total_ship,
        "total_orders": total_orders,
        "return_rate": round(return_rate, 1),
    }


def by_platform() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT platform, COUNT(*) as count, SUM(refund_amount) as refund, "
            "SUM(shipping_cost) as ship FROM returns GROUP BY platform "
            "ORDER BY count DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def by_reason() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT reason, COUNT(*) as count, SUM(refund_amount) as refund "
            "FROM returns GROUP BY reason ORDER BY count DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def by_sku(limit: int = 20) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT sku, COUNT(*) as count, SUM(refund_amount) as refund "
            "FROM returns WHERE sku != '' GROUP BY sku ORDER BY count DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
