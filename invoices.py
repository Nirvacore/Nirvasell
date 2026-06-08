"""Thai-style tax invoice / receipt generator."""
from __future__ import annotations
import db

VAT_RATE = 0.07
INVOICE_PREFIX = "INV"


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number  TEXT UNIQUE NOT NULL,
                order_id        TEXT,
                customer_name   TEXT,
                customer_address TEXT,
                customer_tax_id TEXT,
                subtotal        REAL DEFAULT 0,
                vat_amount      REAL DEFAULT 0,
                total           REAL DEFAULT 0,
                include_vat     INTEGER DEFAULT 0,
                notes           TEXT,
                status          TEXT DEFAULT 'issued',
                issued_at       TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id  INTEGER NOT NULL,
                sku         TEXT,
                description TEXT NOT NULL,
                qty         INTEGER DEFAULT 1,
                unit_price  REAL DEFAULT 0,
                line_total  REAL DEFAULT 0,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        """)


def _next_number() -> str:
    from datetime import datetime
    ym = datetime.now().strftime("%Y%m")
    with db.conn() as c:
        row = c.execute(
            "SELECT COUNT(*) cnt FROM invoices WHERE invoice_number LIKE ?",
            (INVOICE_PREFIX + "-" + ym + "-%",),
        ).fetchone()
        seq = (row["cnt"] if row else 0) + 1
        return INVOICE_PREFIX + "-" + ym + "-" + str(seq).zfill(4)


def create(order_id: str = "", customer_name: str = "",
           customer_address: str = "", customer_tax_id: str = "",
           items: list[dict] = None, include_vat: bool = False,
           notes: str = "") -> int:
    if items is None:
        items = []
    subtotal = sum(
        (i.get("qty", 1) * i.get("unit_price", 0)) for i in items
    )
    vat_amount = round(subtotal * VAT_RATE, 2) if include_vat else 0
    total = round(subtotal + vat_amount, 2)
    inv_number = _next_number()
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO invoices (invoice_number,order_id,customer_name,"
            "customer_address,customer_tax_id,subtotal,vat_amount,total,"
            "include_vat,notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (inv_number, order_id, customer_name, customer_address,
             customer_tax_id, subtotal, vat_amount, total,
             int(include_vat), notes),
        )
        inv_id = cur.lastrowid
        for item in items:
            qty = item.get("qty", 1)
            price = item.get("unit_price", 0)
            line_total = round(qty * price, 2)
            c.execute(
                "INSERT INTO invoice_items "
                "(invoice_id,sku,description,qty,unit_price,line_total) "
                "VALUES (?,?,?,?,?,?)",
                (inv_id, item.get("sku", ""), item.get("description", ""),
                 qty, price, line_total),
            )
        return inv_id


def get(invoice_id: int) -> dict | None:
    with db.conn() as c:
        row = c.execute("SELECT * FROM invoices WHERE id=?",
                        (invoice_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["items"] = [dict(r) for r in c.execute(
            "SELECT * FROM invoice_items WHERE invoice_id=?", (invoice_id,)
        ).fetchall()]
        return d


def all_invoices(limit: int = 50) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM invoices ORDER BY issued_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def render_text(invoice_id: int) -> str:
    inv = get(invoice_id)
    if not inv:
        return ""
    lines = [
        "=" * 50,
        "  ใบกำกับภาษี / TAX INVOICE",
        "=" * 50,
        "เลขที่: " + inv["invoice_number"],
        "วันที่: " + (inv["issued_at"] or "")[:10],
    ]
    if inv.get("order_id"):
        lines.append("ออเดอร์: " + inv["order_id"])
    lines.append("-" * 50)
    if inv.get("customer_name"):
        lines.append("ลูกค้า: " + inv["customer_name"])
    if inv.get("customer_address"):
        lines.append("ที่อยู่: " + inv["customer_address"])
    if inv.get("customer_tax_id"):
        lines.append("เลขผู้เสียภาษี: " + inv["customer_tax_id"])
    lines.append("-" * 50)
    lines.append("{:<25}{:>5}{:>10}{:>10}".format(
        "รายการ", "จำนวน", "ราคา/ชิ้น", "รวม"
    ))
    lines.append("-" * 50)
    for item in inv.get("items", []):
        desc = (item["description"] or "")[:24]
        lines.append("{:<25}{:>5}{:>10.2f}{:>10.2f}".format(
            desc, item["qty"], item["unit_price"], item["line_total"]
        ))
    lines.append("-" * 50)
    lines.append("{:<40}{:>10.2f}".format("ยอดก่อน VAT:", inv["subtotal"]))
    if inv["include_vat"]:
        lines.append("{:<40}{:>10.2f}".format(
            "VAT 7%:", inv["vat_amount"]
        ))
    lines.append("{:<40}{:>10.2f}".format("รวมทั้งสิ้น:", inv["total"]))
    lines.append("=" * 50)
    if inv.get("notes"):
        lines.append("หมายเหตุ: " + inv["notes"])
    return "\n".join(lines)


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
        total_revenue = c.execute(
            "SELECT COALESCE(SUM(total),0) FROM invoices"
        ).fetchone()[0]
        this_month = c.execute(
            "SELECT COALESCE(SUM(total),0) FROM invoices "
            "WHERE strftime('%Y-%m',issued_at)=strftime('%Y-%m','now','localtime')"
        ).fetchone()[0]
    return {
        "total": total,
        "total_revenue": total_revenue,
        "this_month": this_month,
    }
