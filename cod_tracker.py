"""COD (Cash on Delivery) Tracker — the hidden profit killer.

60%+ of Thai e-commerce is COD. The problem:
- Seller pays shipping TO buyer
- Buyer refuses → seller pays return shipping too
- Platform holds COD cash 7-14 days
- COD return rate is 2-5x prepaid return rate

This module tracks COD vs prepaid split, COD returns, and
estimated cash collection timeline."""
from __future__ import annotations

from datetime import datetime, timedelta

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS cod_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                platform TEXT DEFAULT '',
                amount REAL DEFAULT 0,
                shipping_cost REAL DEFAULT 0,
                payment_type TEXT DEFAULT 'cod',
                status TEXT DEFAULT 'pending',
                buyer_name TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                delivered_at TEXT,
                collected_at TEXT,
                note TEXT DEFAULT ''
            )
        """)


COD_STATUSES = ["pending", "shipped", "delivered", "collected", "returned", "cancelled"]

STATUS_ICONS = {
    "pending": "⏳",
    "shipped": "🚚",
    "delivered": "✅",
    "collected": "💰",
    "returned": "↩️",
    "cancelled": "❌",
}


def add(order_id: str, platform: str, amount: float,
        shipping_cost: float = 0, payment_type: str = "cod",
        buyer_name: str = "", note: str = "") -> int:
    with db.conn() as c:
        c.execute(
            "INSERT INTO cod_orders (order_id, platform, amount, shipping_cost, "
            "payment_type, buyer_name, note) VALUES (?,?,?,?,?,?,?)",
            (order_id, platform, amount, shipping_cost, payment_type,
             buyer_name, note),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_status(cod_id: int, status: str):
    now = datetime.now().isoformat(timespec="seconds")
    with db.conn() as c:
        if status == "delivered":
            c.execute(
                "UPDATE cod_orders SET status=?, delivered_at=? WHERE id=?",
                (status, now, cod_id),
            )
        elif status == "collected":
            c.execute(
                "UPDATE cod_orders SET status=?, collected_at=? WHERE id=?",
                (status, now, cod_id),
            )
        else:
            c.execute(
                "UPDATE cod_orders SET status=? WHERE id=?",
                (status, cod_id),
            )


def delete(cod_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM cod_orders WHERE id=?", (cod_id,))


def all_orders(limit: int = 100) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM cod_orders ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM cod_orders").fetchone()[0]
        cod = c.execute(
            "SELECT COUNT(*) FROM cod_orders WHERE payment_type='cod'"
        ).fetchone()[0]
        prepaid = total - cod

        cod_returned = c.execute(
            "SELECT COUNT(*) FROM cod_orders "
            "WHERE payment_type='cod' AND status='returned'"
        ).fetchone()[0]
        cod_delivered = c.execute(
            "SELECT COUNT(*) FROM cod_orders "
            "WHERE payment_type='cod' AND status IN ('delivered','collected')"
        ).fetchone()[0]

        pending_amount = c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM cod_orders "
            "WHERE payment_type='cod' AND status IN ('pending','shipped','delivered')"
        ).fetchone()[0]
        collected_amount = c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM cod_orders "
            "WHERE payment_type='cod' AND status='collected'"
        ).fetchone()[0]
        lost_shipping = c.execute(
            "SELECT COALESCE(SUM(shipping_cost),0)*2 FROM cod_orders "
            "WHERE payment_type='cod' AND status='returned'"
        ).fetchone()[0]

    cod_total = cod_delivered + cod_returned
    cod_return_rate = round(cod_returned / cod_total * 100, 1) if cod_total else 0

    return {
        "total": total,
        "cod_count": cod,
        "prepaid_count": prepaid,
        "cod_pct": round(cod / total * 100, 1) if total else 0,
        "cod_return_rate": cod_return_rate,
        "pending_amount": float(pending_amount),
        "collected_amount": float(collected_amount),
        "lost_shipping": float(lost_shipping),
    }


def pending_collection() -> list[dict]:
    """Orders delivered but not yet collected (platform holding cash)."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM cod_orders "
            "WHERE payment_type='cod' AND status='delivered' "
            "ORDER BY delivered_at ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def by_platform() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT platform, payment_type, COUNT(*) as count, "
            "SUM(amount) as revenue, "
            "SUM(CASE WHEN status='returned' THEN 1 ELSE 0 END) as returns "
            "FROM cod_orders GROUP BY platform, payment_type "
            "ORDER BY platform, payment_type"
        ).fetchall()
    return [dict(r) for r in rows]
