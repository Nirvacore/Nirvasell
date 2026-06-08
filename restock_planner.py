"""Restock Planner — when to reorder, how much, lead time tracking.

Calculates optimal reorder quantities based on sales velocity,
current stock, and supplier lead times."""
from __future__ import annotations
from datetime import datetime, timedelta
import db


DEFAULT_LEAD_DAYS = 7
SAFETY_STOCK_DAYS = 3


def init():
    with db.conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS restock_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                lead_days INTEGER DEFAULT 7,
                safety_stock INTEGER DEFAULT 0,
                min_order_qty INTEGER DEFAULT 1,
                supplier_name TEXT,
                last_restock_date TEXT,
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS restock_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                qty INTEGER,
                supplier TEXT,
                ordered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                received_at TEXT,
                status TEXT DEFAULT 'ordered'
            );
            CREATE INDEX IF NOT EXISTS idx_restock_sku
                ON restock_history(sku);
        """)


def set_config(sku: str, lead_days: int = 7, safety_stock: int = 0,
               min_order_qty: int = 1, supplier_name: str = "",
               notes: str = "") -> None:
    with db.conn() as c:
        c.execute("""
            INSERT INTO restock_config (sku, lead_days, safety_stock,
                                        min_order_qty, supplier_name, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
                lead_days = excluded.lead_days,
                safety_stock = excluded.safety_stock,
                min_order_qty = excluded.min_order_qty,
                supplier_name = excluded.supplier_name,
                notes = excluded.notes
        """, (sku, lead_days, safety_stock, min_order_qty, supplier_name, notes))


def _sales_velocity(sku: str, days: int = 30) -> float:
    with db.conn() as c:
        row = c.execute("""
            SELECT COALESCE(SUM(qty), 0) AS total_qty
            FROM orders
            WHERE sku = ? AND order_date >= date('now', ? || ' days')
        """, (sku, str(-days))).fetchone()
    return row["total_qty"] / days if days > 0 else 0


def plan(days_horizon: int = 30) -> list:
    with db.conn() as c:
        products = c.execute("""
            SELECT p.sku, p.name, p.stock, p.cost_price,
                   COALESCE(rc.lead_days, ?) AS lead_days,
                   COALESCE(rc.safety_stock, 0) AS safety_stock,
                   COALESCE(rc.min_order_qty, 1) AS min_order_qty,
                   rc.supplier_name
            FROM products p
            LEFT JOIN restock_config rc ON p.sku = rc.sku
            WHERE p.stock IS NOT NULL
            ORDER BY p.sku
        """, (DEFAULT_LEAD_DAYS,)).fetchall()

    results = []
    for p in products:
        velocity = _sales_velocity(p["sku"])
        stock = p["stock"] or 0
        lead_days = p["lead_days"]
        safety = p["safety_stock"]

        if velocity <= 0:
            days_until_out = 999
            reorder_point = safety
            reorder_qty = 0
            urgency = "none"
        else:
            days_until_out = stock / velocity
            reorder_point = int(velocity * lead_days) + safety
            demand_during_horizon = int(velocity * days_horizon)
            reorder_qty = max(0, demand_during_horizon - stock + safety)
            reorder_qty = max(reorder_qty, p["min_order_qty"]) if reorder_qty > 0 else 0

            if stock <= 0:
                urgency = "critical"
            elif days_until_out <= lead_days:
                urgency = "urgent"
            elif stock <= reorder_point:
                urgency = "soon"
            else:
                urgency = "ok"

        results.append({
            "sku": p["sku"],
            "name": p["name"],
            "stock": stock,
            "velocity_day": round(velocity, 1),
            "velocity_week": round(velocity * 7, 0),
            "days_until_out": round(days_until_out, 0),
            "lead_days": lead_days,
            "reorder_point": reorder_point,
            "reorder_qty": int(reorder_qty),
            "reorder_cost": round(reorder_qty * (p["cost_price"] or 0), 0),
            "urgency": urgency,
            "supplier": p["supplier_name"] or "",
        })

    results.sort(key=lambda x: {"critical": 0, "urgent": 1, "soon": 2,
                                 "ok": 3, "none": 4}.get(x["urgency"], 5))
    return results


def record_order(sku: str, qty: int, supplier: str = "") -> int:
    with db.conn() as c:
        c.execute("""
            INSERT INTO restock_history (sku, qty, supplier)
            VALUES (?, ?, ?)
        """, (sku, qty, supplier))
        c.execute("""
            UPDATE restock_config SET last_restock_date = date('now')
            WHERE sku = ?
        """, (sku,))
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def receive_order(order_id: int, received_qty: int = None) -> None:
    with db.conn() as c:
        order = c.execute(
            "SELECT sku, qty FROM restock_history WHERE id = ?",
            (order_id,)
        ).fetchone()
        if not order:
            return

        actual_qty = received_qty if received_qty is not None else order["qty"]
        c.execute("""
            UPDATE restock_history
            SET status = 'received', received_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (order_id,))
        c.execute("""
            UPDATE products SET stock = stock + ? WHERE sku = ?
        """, (actual_qty, order["sku"]))


def pending_orders() -> list:
    with db.conn() as c:
        return [dict(r) for r in c.execute("""
            SELECT id, sku, qty, supplier, ordered_at
            FROM restock_history
            WHERE status = 'ordered'
            ORDER BY ordered_at DESC
        """).fetchall()]


def summary() -> dict:
    plan_data = plan()
    critical = sum(1 for p in plan_data if p["urgency"] == "critical")
    urgent = sum(1 for p in plan_data if p["urgency"] == "urgent")
    soon = sum(1 for p in plan_data if p["urgency"] == "soon")
    total_cost = sum(p["reorder_cost"] for p in plan_data if p["reorder_qty"] > 0)

    with db.conn() as c:
        pending = c.execute(
            "SELECT COUNT(*) FROM restock_history WHERE status = 'ordered'"
        ).fetchone()[0]

    return {
        "critical": critical,
        "urgent": urgent,
        "soon": soon,
        "ok": len(plan_data) - critical - urgent - soon,
        "total_reorder_cost": total_cost,
        "pending_orders": pending,
        "total_skus": len(plan_data),
    }
