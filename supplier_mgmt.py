"""Supplier Management — track costs across distributors.

Thai resellers buy from multiple sources: Synnex, VSTECS, direct brands,
Alibaba, local wholesalers. This module tracks which supplier gives the
best price per SKU, lead times, and order history."""
from __future__ import annotations

from datetime import datetime

import db


SUPPLIER_ORDER_COLUMNS = {
    "id", "supplier_id", "order_date", "total_amount", "items_count",
    "status", "received_at", "note",
}


def _table_columns(connection, table: str) -> set[str]:
    return {
        row["name"] for row in connection.execute(f"PRAGMA table_info({table})")
    }


def _migrate_supplier_orders(connection) -> None:
    legacy_columns = _table_columns(connection, "purchase_orders")
    target_columns = _table_columns(connection, "supplier_orders")
    if target_columns and not SUPPLIER_ORDER_COLUMNS <= target_columns:
        raise RuntimeError("supplier_orders has an incompatible schema")
    if SUPPLIER_ORDER_COLUMNS <= legacy_columns:
        if target_columns:
            raise RuntimeError(
                "cannot migrate supplier orders while both legacy and target tables exist"
            )
        item_columns = _table_columns(connection, "po_items")
        if item_columns:
            item_count = connection.execute(
                "SELECT COUNT(*) FROM po_items"
            ).fetchone()[0]
            if item_count:
                raise RuntimeError(
                    "cannot migrate supplier orders because po_items contains data"
                )
            connection.execute("DROP TABLE po_items")
        connection.execute("DROP INDEX IF EXISTS idx_po_status")
        connection.execute("ALTER TABLE purchase_orders RENAME TO supplier_orders")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS supplier_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            order_date TEXT DEFAULT (date('now','localtime')),
            total_amount REAL DEFAULT 0,
            items_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ordered',
            received_at TEXT,
            note TEXT DEFAULT '',
            FOREIGN KEY (supplier_id) REFERENCES supplier_contacts(id)
        )
    """)


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS supplier_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                line_id TEXT DEFAULT '',
                website TEXT DEFAULT '',
                payment_terms TEXT DEFAULT '',
                lead_days INTEGER DEFAULT 3,
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS supplier_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                sku TEXT NOT NULL,
                product_name TEXT DEFAULT '',
                unit_cost REAL NOT NULL,
                min_qty INTEGER DEFAULT 1,
                last_updated TEXT DEFAULT (datetime('now','localtime')),
                note TEXT DEFAULT '',
                FOREIGN KEY (supplier_id) REFERENCES supplier_contacts(id)
            )
        """)
        _migrate_supplier_orders(c)


def add_supplier(name: str, **kwargs) -> int:
    cols = ["name"]
    vals = [name]
    for k in ("contact", "phone", "email", "line_id", "website",
              "payment_terms", "lead_days", "note"):
        if k in kwargs and kwargs[k]:
            cols.append(k)
            vals.append(kwargs[k])
    placeholders = ",".join("?" * len(vals))
    col_str = ",".join(cols)
    with db.conn() as c:
        c.execute(
            "INSERT INTO supplier_contacts (" + col_str + ") VALUES (" + placeholders + ")",
            vals,
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_supplier(sup_id: int, **kwargs):
    sets = []
    vals = []
    for k in ("name", "contact", "phone", "email", "line_id",
              "website", "payment_terms", "lead_days", "note"):
        if k in kwargs:
            sets.append(k + "=?")
            vals.append(kwargs[k])
    if not sets:
        return
    vals.append(sup_id)
    with db.conn() as c:
        c.execute(
            "UPDATE supplier_contacts SET " + ",".join(sets) + " WHERE id=?",
            vals,
        )


def delete_supplier(sup_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM supplier_prices WHERE supplier_id=?", (sup_id,))
        c.execute("DELETE FROM supplier_orders WHERE supplier_id=?", (sup_id,))
        c.execute("DELETE FROM supplier_contacts WHERE id=?", (sup_id,))


def all_suppliers() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT s.*, "
            "(SELECT COUNT(*) FROM supplier_prices WHERE supplier_id=s.id) as sku_count, "
            "(SELECT COUNT(*) FROM supplier_orders WHERE supplier_id=s.id) as order_count "
            "FROM supplier_contacts s ORDER BY s.name"
        ).fetchall()
    return [dict(r) for r in rows]


def get_supplier(sup_id: int) -> dict | None:
    with db.conn() as c:
        r = c.execute("SELECT * FROM supplier_contacts WHERE id=?", (sup_id,)).fetchone()
    return dict(r) if r else None


def set_price(supplier_id: int, sku: str, unit_cost: float,
              product_name: str = "", min_qty: int = 1, note: str = ""):
    with db.conn() as c:
        existing = c.execute(
            "SELECT id FROM supplier_prices WHERE supplier_id=? AND sku=?",
            (supplier_id, sku),
        ).fetchone()
        if existing:
            c.execute(
                "UPDATE supplier_prices SET unit_cost=?, min_qty=?, "
                "product_name=?, note=?, last_updated=datetime('now','localtime') "
                "WHERE id=?",
                (unit_cost, min_qty, product_name, note, existing["id"]),
            )
        else:
            c.execute(
                "INSERT INTO supplier_prices "
                "(supplier_id, sku, unit_cost, product_name, min_qty, note) "
                "VALUES (?,?,?,?,?,?)",
                (supplier_id, sku, unit_cost, product_name, min_qty, note),
            )


def delete_price(price_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM supplier_prices WHERE id=?", (price_id,))


def prices_for_sku(sku: str) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT sp.*, s.name as supplier_name, s.lead_days "
            "FROM supplier_prices sp JOIN supplier_contacts s ON s.id=sp.supplier_id "
            "WHERE sp.sku=? ORDER BY sp.unit_cost ASC",
            (sku,),
        ).fetchall()
    return [dict(r) for r in rows]


def prices_for_supplier(supplier_id: int) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM supplier_prices WHERE supplier_id=? ORDER BY sku",
            (supplier_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def best_price(sku: str) -> dict | None:
    prices = prices_for_sku(sku)
    return prices[0] if prices else None


def price_comparison() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT sku, COUNT(DISTINCT supplier_id) as suppliers, "
            "MIN(unit_cost) as min_cost, MAX(unit_cost) as max_cost, "
            "ROUND(AVG(unit_cost),2) as avg_cost "
            "FROM supplier_prices GROUP BY sku "
            "HAVING suppliers > 1 ORDER BY (max_cost-min_cost) DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def add_order(supplier_id: int, total_amount: float,
              items_count: int = 0, note: str = "") -> int:
    with db.conn() as c:
        c.execute(
            "INSERT INTO supplier_orders "
            "(supplier_id, total_amount, items_count, note) VALUES (?,?,?,?)",
            (supplier_id, total_amount, items_count, note),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def receive_order(order_id: int, received_at: str | None = None) -> None:
    """Mark one ordered supplier order received on a validated local date."""
    if isinstance(order_id, bool) or not isinstance(order_id, int) or order_id <= 0:
        raise ValueError("order_id must be a positive integer")

    today = datetime.now().date()
    if received_at is None:
        received_date = today
    elif not isinstance(received_at, str) or not received_at:
        raise ValueError("received_at must be a YYYY-MM-DD date")
    else:
        try:
            received_date = datetime.strptime(received_at, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("received_at must be a YYYY-MM-DD date") from exc
        if received_date.isoformat() != received_at:
            raise ValueError("received_at must be a YYYY-MM-DD date")
    if received_date > today:
        raise ValueError("received_at cannot be in the future")

    with db.conn() as c:
        order = c.execute(
            "SELECT order_date, status FROM supplier_orders WHERE id=?",
            (order_id,),
        ).fetchone()
        if not order:
            raise ValueError("supplier order not found")
        if order["status"] != "ordered":
            raise ValueError("supplier order is not awaiting receipt")
        try:
            order_date = datetime.strptime(
                str(order["order_date"])[:10], "%Y-%m-%d"
            ).date()
        except (TypeError, ValueError) as exc:
            raise ValueError("supplier order has an invalid order_date") from exc
        if received_date < order_date:
            raise ValueError("received_at cannot precede order_date")

        updated = c.execute(
            "UPDATE supplier_orders SET status='received', received_at=? "
            "WHERE id=? AND status='ordered'",
            (received_date.isoformat(), order_id),
        )
        if updated.rowcount != 1:
            raise RuntimeError("supplier order receipt was not recorded")


def supplier_order_history(supplier_id: int) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM supplier_orders WHERE supplier_id=? "
            "ORDER BY order_date DESC LIMIT 50",
            (supplier_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def total_spend() -> dict:
    with db.conn() as c:
        r = c.execute(
            "SELECT COALESCE(SUM(total_amount),0) as total, "
            "COUNT(*) as order_count FROM supplier_orders"
        ).fetchone()
    return {"total_spent": float(r["total"]), "total_orders": r["order_count"]}
