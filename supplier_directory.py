"""Supplier Directory — contacts, payment terms, performance history."""
from __future__ import annotations
import db

PAYMENT_TERMS = ["cod", "prepay", "net7", "net15", "net30", "credit"]

CATEGORIES = [
    "manufacturer", "distributor", "wholesaler",
    "importer", "local_brand", "other",
]


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL UNIQUE,
                contact_name    TEXT,
                phone           TEXT,
                email           TEXT,
                line_id         TEXT,
                category        TEXT DEFAULT 'other',
                payment_terms   TEXT DEFAULT 'prepay',
                credit_days     INTEGER DEFAULT 0,
                min_order_amount REAL DEFAULT 0,
                notes           TEXT,
                active          INTEGER DEFAULT 1,
                created_at      TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS supplier_skus (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                sku         TEXT NOT NULL,
                supplier_sku TEXT,
                cost_price  REAL DEFAULT 0,
                min_qty     INTEGER DEFAULT 1,
                lead_days   INTEGER DEFAULT 7,
                notes       TEXT,
                UNIQUE(supplier_id, sku)
            )
        """)


def add(name: str, contact_name: str = "", phone: str = "",
        email: str = "", line_id: str = "", category: str = "other",
        payment_terms: str = "prepay", credit_days: int = 0,
        min_order_amount: float = 0, notes: str = "") -> int:
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO suppliers (name,contact_name,phone,email,line_id,"
            "category,payment_terms,credit_days,min_order_amount,notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (name, contact_name, phone, email, line_id,
             category, payment_terms, credit_days, min_order_amount, notes),
        )
        return cur.lastrowid


def update(supplier_id: int, **kwargs) -> None:
    allowed = {"contact_name", "phone", "email", "line_id", "category",
               "payment_terms", "credit_days", "min_order_amount", "notes", "active"}
    with db.conn() as c:
        for key, val in kwargs.items():
            if key in allowed:
                c.execute(f"UPDATE suppliers SET {key}=? WHERE id=?",
                          (val, supplier_id))


def link_sku(supplier_id: int, sku: str, supplier_sku: str = "",
             cost_price: float = 0, min_qty: int = 1,
             lead_days: int = 7, notes: str = "") -> None:
    with db.conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO supplier_skus "
            "(supplier_id,sku,supplier_sku,cost_price,min_qty,lead_days,notes) "
            "VALUES (?,?,?,?,?,?,?)",
            (supplier_id, sku, supplier_sku, cost_price, min_qty, lead_days, notes),
        )


def get_skus(supplier_id: int) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT ss.*, p.name product_name "
            "FROM supplier_skus ss "
            "LEFT JOIN products p ON ss.sku=p.sku "
            "WHERE ss.supplier_id=?",
            (supplier_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def all_suppliers(active_only: bool = True) -> list[dict]:
    with db.conn() as c:
        if active_only:
            rows = c.execute(
                "SELECT s.*, "
                "  (SELECT COUNT(*) FROM supplier_skus WHERE supplier_id=s.id) sku_count, "
                "  (SELECT COUNT(*) FROM purchase_orders WHERE supplier=s.name) po_count "
                "FROM suppliers s WHERE s.active=1 ORDER BY s.name"
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT s.*, "
                "  (SELECT COUNT(*) FROM supplier_skus WHERE supplier_id=s.id) sku_count, "
                "  (SELECT COUNT(*) FROM purchase_orders WHERE supplier=s.name) po_count "
                "FROM suppliers s ORDER BY s.active DESC, s.name"
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            result.append(d)
        return result


def get(supplier_id: int) -> dict | None:
    with db.conn() as c:
        row = c.execute("SELECT * FROM suppliers WHERE id=?",
                        (supplier_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["skus"] = get_skus(supplier_id)
        try:
            po_rows = c.execute(
                "SELECT COUNT(*) cnt, COALESCE(SUM(total_amount),0) total "
                "FROM purchase_orders WHERE supplier=?",
                (row["name"],),
            ).fetchone()
            d["po_count"] = po_rows["cnt"]
            d["total_spent"] = po_rows["total"]
        except Exception:
            d["po_count"] = 0
            d["total_spent"] = 0
        return d


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
        active = c.execute(
            "SELECT COUNT(*) FROM suppliers WHERE active=1"
        ).fetchone()[0]
        linked_skus = c.execute(
            "SELECT COUNT(DISTINCT sku) FROM supplier_skus"
        ).fetchone()[0]
    return {"total": total, "active": active, "linked_skus": linked_skus}
