"""Customer CRM — know who buys from you, who comes back, who's gone quiet.

Thai home sellers handle 50-200 orders/month across 3 platforms but have ZERO
visibility into repeat buyers. This module extracts customer data from order
imports and tracks purchase patterns across platforms.

VIP tiers:
  Bronze  = 1-2 orders
  Silver  = 3-5 orders
  Gold    = 6-10 orders
  Diamond = 11+ orders

Dormant = no order in 30+ days."""
from __future__ import annotations

from datetime import datetime, timedelta

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL DEFAULT '',
                phone       TEXT DEFAULT '',
                email       TEXT DEFAULT '',
                line_id     TEXT DEFAULT '',
                platforms   TEXT DEFAULT '',
                note        TEXT DEFAULT '',
                first_order TEXT DEFAULT '',
                last_order  TEXT DEFAULT '',
                order_count INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS customer_orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_id    TEXT DEFAULT '',
                platform    TEXT DEFAULT '',
                amount      REAL DEFAULT 0,
                order_date  TEXT DEFAULT '',
                product     TEXT DEFAULT '',
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)


def _normalize_name(name: str) -> str:
    return " ".join((name or "").strip().split()).lower()


def find_or_create(*, name: str, phone: str = "", email: str = "",
                   platform: str = "") -> int:
    norm = _normalize_name(name)
    if not norm:
        norm = "(unknown)"

    with db.conn() as c:
        # Match by phone first (most reliable in TH), then name
        row = None
        if phone and phone.strip():
            row = c.execute(
                "SELECT id FROM customers WHERE phone = ? AND phone != ''",
                (phone.strip(),)
            ).fetchone()
        if not row and email and email.strip():
            row = c.execute(
                "SELECT id FROM customers WHERE email = ? AND email != ''",
                (email.strip(),)
            ).fetchone()
        if not row:
            row = c.execute(
                "SELECT id FROM customers WHERE LOWER(name) = ?",
                (norm,)
            ).fetchone()

        if row:
            cid = row[0]
            if platform:
                cur_plats = (c.execute(
                    "SELECT platforms FROM customers WHERE id = ?", (cid,)
                ).fetchone() or ("",))[0]
                plats = set(p for p in (cur_plats or "").split(",") if p)
                if platform.lower() not in plats:
                    plats.add(platform.lower())
                    c.execute("UPDATE customers SET platforms = ? WHERE id = ?",
                              (",".join(sorted(plats)), cid))
            return cid

        c.execute(
            "INSERT INTO customers (name, phone, email, platforms) VALUES (?,?,?,?)",
            (name.strip() or "(unknown)", phone.strip(), email.strip(),
             platform.lower() if platform else ""),
        )
        return c.lastrowid


def record_order(*, customer_id: int, order_id: str = "",
                 platform: str = "", amount: float = 0,
                 order_date: str = "", product: str = ""):
    with db.conn() as c:
        existing = c.execute(
            "SELECT id FROM customer_orders WHERE customer_id = ? AND order_id = ? AND order_id != ''",
            (customer_id, order_id)
        ).fetchone()
        if existing:
            return

        c.execute(
            "INSERT INTO customer_orders (customer_id, order_id, platform, amount, order_date, product) "
            "VALUES (?,?,?,?,?,?)",
            (customer_id, order_id, platform, amount, order_date, product),
        )

        stats = c.execute(
            "SELECT COUNT(*), SUM(amount), MIN(order_date), MAX(order_date) "
            "FROM customer_orders WHERE customer_id = ?",
            (customer_id,)
        ).fetchone()
        c.execute(
            "UPDATE customers SET order_count = ?, total_spent = ?, "
            "first_order = ?, last_order = ? WHERE id = ?",
            (stats[0], stats[1] or 0, stats[2] or "", stats[3] or "", customer_id),
        )


def tier(order_count: int) -> str:
    if order_count >= 11:
        return "diamond"
    if order_count >= 6:
        return "gold"
    if order_count >= 3:
        return "silver"
    return "bronze"


TIER_ICONS = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "diamond": "💎"}
TIER_COLORS = {
    "bronze": "#a0856e", "silver": "#8d8d8d",
    "gold": "#c5963d", "diamond": "#4d6cb0",
}


def all_customers(*, sort: str = "total_spent", direction: str = "DESC",
                  limit: int = 200) -> list[dict]:
    safe_cols = {"total_spent", "order_count", "last_order", "name", "created_at"}
    col = sort if sort in safe_cols else "total_spent"
    d = "DESC" if direction.upper() == "DESC" else "ASC"

    with db.conn() as c:
        rows = c.execute(
            f"SELECT * FROM customers ORDER BY {col} {d} LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get(customer_id: int) -> dict | None:
    with db.conn() as c:
        r = c.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    return dict(r) if r else None


def orders_for(customer_id: int) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM customer_orders WHERE customer_id = ? ORDER BY order_date DESC",
            (customer_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def update(customer_id: int, **fields):
    allowed = {"name", "phone", "email", "line_id", "note"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return
    clause = ", ".join(f"{k} = ?" for k in sets)
    with db.conn() as c:
        c.execute(
            f"UPDATE customers SET {clause} WHERE id = ?",
            (*sets.values(), customer_id),
        )


def vip_customers(min_orders: int = 3) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM customers WHERE order_count >= ? ORDER BY total_spent DESC",
            (min_orders,)
        ).fetchall()
    return [dict(r) for r in rows]


def dormant_customers(days: int = 30) -> list[dict]:
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM customers WHERE last_order < ? AND last_order != '' "
            "ORDER BY last_order ASC",
            (cutoff,)
        ).fetchall()
    return [dict(r) for r in rows]


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        repeat = c.execute("SELECT COUNT(*) FROM customers WHERE order_count >= 2").fetchone()[0]
        vip = c.execute("SELECT COUNT(*) FROM customers WHERE order_count >= 6").fetchone()[0]
        top = c.execute(
            "SELECT name, total_spent FROM customers ORDER BY total_spent DESC LIMIT 1"
        ).fetchone()
        avg_spent = c.execute("SELECT AVG(total_spent) FROM customers WHERE order_count > 0").fetchone()[0]
    return {
        "total": total,
        "repeat": repeat,
        "repeat_pct": round(repeat / total * 100, 1) if total else 0,
        "vip": vip,
        "top_name": top[0] if top else "",
        "top_spent": top[1] if top else 0,
        "avg_spent": round(avg_spent or 0, 0),
    }


def search(query: str, limit: int = 50) -> list[dict]:
    q = f"%{query.strip()}%"
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? OR email LIKE ? "
            "ORDER BY total_spent DESC LIMIT ?",
            (q, q, q, limit),
        ).fetchall()
    return [dict(r) for r in rows]
