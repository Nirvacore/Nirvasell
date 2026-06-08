"""Price History — track cost and sell price changes over time per SKU.

When did you raise prices? Did COGS go up? Shows historical trend
so you can justify price changes to customers or suppliers."""
from __future__ import annotations
from datetime import datetime
import db


def init():
    with db.conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS price_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                change_date TEXT DEFAULT CURRENT_DATE,
                old_cost REAL,
                new_cost REAL,
                old_sell REAL,
                new_sell REAL,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_pc_sku
                ON price_changes(sku);
            CREATE INDEX IF NOT EXISTS idx_pc_date
                ON price_changes(change_date);
        """)


def record_change(sku: str, old_cost: float = None, new_cost: float = None,
                  old_sell: float = None, new_sell: float = None,
                  reason: str = "") -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    with db.conn() as c:
        c.execute("""
            INSERT INTO price_changes
                (sku, change_date, old_cost, new_cost, old_sell, new_sell, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (sku, today, old_cost, new_cost, old_sell, new_sell, reason))
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def sku_history(sku: str, limit: int = 50) -> list:
    with db.conn() as c:
        rows = c.execute("""
            SELECT * FROM price_changes
            WHERE sku = ?
            ORDER BY change_date DESC, id DESC
            LIMIT ?
        """, (sku, limit)).fetchall()

    result = []
    for r in rows:
        item = dict(r)
        item["cost_delta"] = round(
            (r["new_cost"] or 0) - (r["old_cost"] or 0), 2
        ) if r["new_cost"] and r["old_cost"] else None
        item["sell_delta"] = round(
            (r["new_sell"] or 0) - (r["old_sell"] or 0), 2
        ) if r["new_sell"] and r["old_sell"] else None
        if item["cost_delta"]:
            item["cost_delta_pct"] = round(
                item["cost_delta"] / r["old_cost"] * 100, 1
            ) if r["old_cost"] else 0
        else:
            item["cost_delta_pct"] = 0
        if item["sell_delta"]:
            item["sell_delta_pct"] = round(
                item["sell_delta"] / r["old_sell"] * 100, 1
            ) if r["old_sell"] else 0
        else:
            item["sell_delta_pct"] = 0
        result.append(item)
    return result


def update_price_with_record(sku: str, new_cost: float = None,
                              new_sell: float = None, reason: str = "") -> dict:
    with db.conn() as c:
        current = c.execute(
            "SELECT cost_price, sell_price FROM products WHERE sku = ?",
            (sku,)
        ).fetchone()

        if not current:
            return {"success": False, "error": "SKU not found"}

        old_cost = current["cost_price"]
        old_sell = current["sell_price"]

        updates = []
        params = []
        if new_cost is not None:
            updates.append("cost_price = ?")
            params.append(new_cost)
        if new_sell is not None:
            updates.append("sell_price = ?")
            params.append(new_sell)

        if updates:
            params.append(sku)
            c.execute(
                "UPDATE products SET " + ", ".join(updates) + " WHERE sku = ?",
                params
            )

        record_id = record_change(sku, old_cost, new_cost or old_cost,
                                  old_sell, new_sell or old_sell, reason)

    return {
        "success": True,
        "record_id": record_id,
        "old_cost": old_cost,
        "new_cost": new_cost,
        "old_sell": old_sell,
        "new_sell": new_sell,
    }


def recent_changes(days: int = 30, limit: int = 50) -> list:
    with db.conn() as c:
        rows = c.execute("""
            SELECT pc.*, p.name AS product_name
            FROM price_changes pc
            LEFT JOIN products p ON pc.sku = p.sku
            WHERE pc.change_date >= date('now', ? || ' days')
            ORDER BY pc.change_date DESC, pc.id DESC
            LIMIT ?
        """, (str(-days), limit)).fetchall()
    return [dict(r) for r in rows]


def price_trend(sku: str) -> dict:
    history = sku_history(sku, limit=20)
    if not history:
        with db.conn() as c:
            cur = c.execute(
                "SELECT cost_price, sell_price FROM products WHERE sku = ?",
                (sku,)
            ).fetchone()
        if cur:
            return {
                "sku": sku,
                "has_history": False,
                "current_cost": cur["cost_price"],
                "current_sell": cur["sell_price"],
                "changes": [],
            }
        return {"sku": sku, "has_history": False, "changes": []}

    cost_points = []
    sell_points = []
    for h in reversed(history):
        if h["new_cost"] is not None:
            cost_points.append({"date": h["change_date"], "price": h["new_cost"]})
        if h["new_sell"] is not None:
            sell_points.append({"date": h["change_date"], "price": h["new_sell"]})

    return {
        "sku": sku,
        "has_history": True,
        "cost_points": cost_points,
        "sell_points": sell_points,
        "first_change": history[-1]["change_date"],
        "last_change": history[0]["change_date"],
        "total_changes": len(history),
    }


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM price_changes").fetchone()[0]
        this_month = c.execute("""
            SELECT COUNT(*) FROM price_changes
            WHERE strftime('%Y-%m', change_date) = strftime('%Y-%m', 'now')
        """).fetchone()[0]
        skus_changed = c.execute(
            "SELECT COUNT(DISTINCT sku) FROM price_changes"
        ).fetchone()[0]
    return {
        "total_changes": total,
        "this_month": this_month,
        "skus_with_history": skus_changed,
    }
