"""Purchase Orders — formal POs to suppliers, track status and receipt.

Create POs, track pending/received, auto-update stock on receipt."""
from __future__ import annotations
from datetime import datetime
import json
import db


STATUSES = {
    "draft":    {"icon": "📋", "color": "#9a9485"},
    "sent":     {"icon": "📤", "color": "#4a7ab5"},
    "partial":  {"icon": "📦", "color": "#c5963d"},
    "received": {"icon": "✅", "color": "#4d6c5c"},
    "cancelled":{"icon": "❌", "color": "#c54c4c"},
}


def init():
    with db.conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT NOT NULL UNIQUE,
                supplier TEXT NOT NULL,
                order_date TEXT DEFAULT CURRENT_DATE,
                expected_date TEXT,
                status TEXT DEFAULT 'draft',
                notes TEXT,
                total_amount REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS po_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id INTEGER REFERENCES purchase_orders(id) ON DELETE CASCADE,
                sku TEXT NOT NULL,
                product_name TEXT,
                qty_ordered INTEGER DEFAULT 0,
                qty_received INTEGER DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                line_total REAL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
            CREATE INDEX IF NOT EXISTS idx_poi_po ON po_items(po_id);
        """)


def _next_po_number() -> str:
    prefix = "PO-" + datetime.now().strftime("%Y%m")
    with db.conn() as c:
        last = c.execute("""
            SELECT po_number FROM purchase_orders
            WHERE po_number LIKE ?
            ORDER BY po_number DESC LIMIT 1
        """, (prefix + "%",)).fetchone()
    if last:
        seq = int(last["po_number"].split("-")[-1]) + 1
    else:
        seq = 1
    return prefix + "-{:04d}".format(seq)


def create(supplier: str, items: list, expected_date: str = "",
           notes: str = "") -> int:
    po_number = _next_po_number()
    total = sum(i.get("qty", 0) * i.get("unit_cost", 0) for i in items)

    with db.conn() as c:
        c.execute("""
            INSERT INTO purchase_orders
                (po_number, supplier, expected_date, notes, total_amount)
            VALUES (?, ?, ?, ?, ?)
        """, (po_number, supplier, expected_date, notes, total))
        po_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]

        for item in items:
            sku = item.get("sku", "")
            qty = item.get("qty", 0)
            unit_cost = item.get("unit_cost", 0)
            name = item.get("name", "")
            c.execute("""
                INSERT INTO po_items
                    (po_id, sku, product_name, qty_ordered, unit_cost, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (po_id, sku, name, qty, unit_cost, qty * unit_cost))
    return po_id


def send(po_id: int) -> None:
    with db.conn() as c:
        c.execute(
            "UPDATE purchase_orders SET status = 'sent' WHERE id = ?",
            (po_id,)
        )


def receive_item(po_id: int, sku: str, qty_received: int,
                 update_stock: bool = True) -> None:
    with db.conn() as c:
        item = c.execute("""
            SELECT id, qty_ordered, qty_received
            FROM po_items WHERE po_id = ? AND sku = ?
        """, (po_id, sku)).fetchone()

        if not item:
            return

        new_received = item["qty_received"] + qty_received
        c.execute(
            "UPDATE po_items SET qty_received = ? WHERE id = ?",
            (new_received, item["id"])
        )

        if update_stock:
            c.execute(
                "UPDATE products SET stock = stock + ? WHERE sku = ?",
                (qty_received, sku)
            )

        all_items = c.execute("""
            SELECT qty_ordered, qty_received FROM po_items WHERE po_id = ?
        """, (po_id,)).fetchall()

        fully_received = all(
            i["qty_received"] >= i["qty_ordered"] for i in all_items
        )
        any_received = any(i["qty_received"] > 0 for i in all_items)

        new_status = "received" if fully_received else ("partial" if any_received else "sent")
        c.execute(
            "UPDATE purchase_orders SET status = ? WHERE id = ?",
            (new_status, po_id)
        )


def get(po_id: int) -> dict:
    with db.conn() as c:
        po = c.execute(
            "SELECT * FROM purchase_orders WHERE id = ?", (po_id,)
        ).fetchone()
        if not po:
            return {}
        items = c.execute(
            "SELECT * FROM po_items WHERE po_id = ? ORDER BY sku",
            (po_id,)
        ).fetchall()

    item_list = [dict(i) for i in items]
    for item in item_list:
        item["pending_qty"] = item["qty_ordered"] - item["qty_received"]
        item["is_complete"] = item["qty_received"] >= item["qty_ordered"]

    return {
        **dict(po),
        "items": item_list,
        "status_info": STATUSES.get(po["status"], {}),
        "items_received": sum(1 for i in item_list if i["is_complete"]),
        "items_pending": sum(1 for i in item_list if not i["is_complete"]),
    }


def all_pos(status: str = None, limit: int = 50) -> list:
    with db.conn() as c:
        if status:
            rows = c.execute("""
                SELECT po.*, COUNT(poi.id) AS item_count
                FROM purchase_orders po
                LEFT JOIN po_items poi ON po.id = poi.po_id
                WHERE po.status = ?
                GROUP BY po.id ORDER BY po.order_date DESC LIMIT ?
            """, (status, limit)).fetchall()
        else:
            rows = c.execute("""
                SELECT po.*, COUNT(poi.id) AS item_count
                FROM purchase_orders po
                LEFT JOIN po_items poi ON po.id = poi.po_id
                GROUP BY po.id ORDER BY po.order_date DESC LIMIT ?
            """, (limit,)).fetchall()

    result = []
    for r in rows:
        item = dict(r)
        item["status_info"] = STATUSES.get(r["status"], {})
        result.append(item)
    return result


def cancel(po_id: int) -> None:
    with db.conn() as c:
        c.execute(
            "UPDATE purchase_orders SET status = 'cancelled' WHERE id = ?",
            (po_id,)
        )


def summary() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM purchase_orders").fetchone()[0]
        pending_val = c.execute("""
            SELECT COALESCE(SUM(total_amount), 0)
            FROM purchase_orders WHERE status IN ('draft', 'sent', 'partial')
        """).fetchone()[0]
        pending_count = c.execute("""
            SELECT COUNT(*) FROM purchase_orders
            WHERE status IN ('sent', 'partial')
        """).fetchone()[0]
        overdue = c.execute("""
            SELECT COUNT(*) FROM purchase_orders
            WHERE status IN ('sent', 'partial')
              AND expected_date != ''
              AND expected_date < date('now')
        """).fetchone()[0]
    return {
        "total": total,
        "pending_count": pending_count,
        "pending_value": pending_val,
        "overdue": overdue,
    }
