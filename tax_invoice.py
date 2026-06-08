"""Thai Tax Invoice Generator — ใบกำกับภาษี.

Generates proper Thai tax invoices with:
- VAT 7% calculation
- Seller TIN (เลขประจำตัวผู้เสียภาษี)
- Running invoice number
- Buyer details
- Printable plain-text format (upgrade to PDF later)

Required by law for all VAT-registered sellers."""
from __future__ import annotations

from datetime import date, datetime

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS tax_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT NOT NULL UNIQUE,
                invoice_date TEXT DEFAULT (date('now','localtime')),
                seller_name TEXT DEFAULT '',
                seller_tin TEXT DEFAULT '',
                seller_address TEXT DEFAULT '',
                buyer_name TEXT DEFAULT '',
                buyer_tin TEXT DEFAULT '',
                buyer_address TEXT DEFAULT '',
                subtotal REAL DEFAULT 0,
                vat_rate REAL DEFAULT 7.0,
                vat_amount REAL DEFAULT 0,
                total REAL DEFAULT 0,
                items_json TEXT DEFAULT '[]',
                order_id TEXT DEFAULT '',
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


VAT_RATE = 7.0


def next_invoice_no() -> str:
    """Generate next invoice number: INV-YYYYMM-NNNN."""
    prefix = "INV-" + date.today().strftime("%Y%m") + "-"
    with db.conn() as c:
        r = c.execute(
            "SELECT invoice_no FROM tax_invoices "
            "WHERE invoice_no LIKE ? ORDER BY invoice_no DESC LIMIT 1",
            (prefix + "%",),
        ).fetchone()
    if r:
        try:
            last_num = int(r["invoice_no"].split("-")[-1])
            return prefix + str(last_num + 1).zfill(4)
        except Exception:
            pass
    return prefix + "0001"


def create_invoice(
    seller_name: str, seller_tin: str, seller_address: str,
    buyer_name: str, items: list[dict],
    buyer_tin: str = "", buyer_address: str = "",
    order_id: str = "", note: str = "",
) -> dict:
    """Create a tax invoice. Items: [{name, qty, unit_price}]."""
    import json

    inv_no = next_invoice_no()
    subtotal = sum(
        float(i.get("unit_price", 0)) * int(i.get("qty", 1))
        for i in items
    )
    vat = round(subtotal * VAT_RATE / 100, 2)
    total = round(subtotal + vat, 2)

    with db.conn() as c:
        c.execute(
            "INSERT INTO tax_invoices "
            "(invoice_no, seller_name, seller_tin, seller_address, "
            "buyer_name, buyer_tin, buyer_address, "
            "subtotal, vat_rate, vat_amount, total, "
            "items_json, order_id, note) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (inv_no, seller_name, seller_tin, seller_address,
             buyer_name, buyer_tin, buyer_address,
             subtotal, VAT_RATE, vat, total,
             json.dumps(items, ensure_ascii=False), order_id, note),
        )

    return {
        "invoice_no": inv_no,
        "subtotal": subtotal,
        "vat_amount": vat,
        "total": total,
    }


def get_invoice(inv_id: int) -> dict | None:
    import json
    with db.conn() as c:
        r = c.execute("SELECT * FROM tax_invoices WHERE id=?", (inv_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["items"] = json.loads(d.get("items_json") or "[]")
    return d


def all_invoices() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT id, invoice_no, invoice_date, buyer_name, total, order_id "
            "FROM tax_invoices ORDER BY invoice_no DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_invoice(inv_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM tax_invoices WHERE id=?", (inv_id,))


def to_text(inv_id: int) -> str:
    """Generate printable plain-text tax invoice."""
    inv = get_invoice(inv_id)
    if not inv:
        return "Invoice not found"

    lines = [
        "=" * 60,
        "               ใบกำกับภาษี / TAX INVOICE",
        "=" * 60,
        "",
        "เลขที่ / No:     " + inv["invoice_no"],
        "วันที่ / Date:   " + (inv.get("invoice_date") or ""),
        "",
        "--- ผู้ขาย / Seller ---",
        "ชื่อ:  " + (inv.get("seller_name") or ""),
        "TIN:   " + (inv.get("seller_tin") or ""),
        "ที่อยู่: " + (inv.get("seller_address") or ""),
        "",
        "--- ผู้ซื้อ / Buyer ---",
        "ชื่อ:  " + (inv.get("buyer_name") or ""),
        "TIN:   " + (inv.get("buyer_tin") or ""),
        "ที่อยู่: " + (inv.get("buyer_address") or ""),
        "",
        "-" * 60,
        "{:<30s} {:>5s} {:>10s} {:>10s}".format("รายการ", "จำนวน", "ราคา/หน่วย", "รวม"),
        "-" * 60,
    ]

    for item in inv.get("items", []):
        name = (item.get("name") or "")[:28]
        qty = str(item.get("qty", 1))
        unit = "{:,.0f}".format(float(item.get("unit_price", 0)))
        sub = "{:,.0f}".format(float(item.get("unit_price", 0)) * int(item.get("qty", 1)))
        lines.append("{:<30s} {:>5s} {:>10s} {:>10s}".format(name, qty, unit, sub))

    lines.extend([
        "-" * 60,
        "{:<47s} {:>10s}".format("ราคาสินค้า (Subtotal)", "฿" + "{:,.2f}".format(inv["subtotal"])),
        "{:<47s} {:>10s}".format(
            "VAT " + "{:.0f}%".format(inv.get("vat_rate", 7)),
            "฿" + "{:,.2f}".format(inv.get("vat_amount", 0)),
        ),
        "=" * 60,
        "{:<47s} {:>10s}".format("รวมทั้งสิ้น (Total)", "฿" + "{:,.2f}".format(inv["total"])),
        "=" * 60,
    ])

    if inv.get("note"):
        lines.extend(["", "หมายเหตุ: " + inv["note"]])

    lines.extend(["", "ลงชื่อ _________________ ผู้ออกใบกำกับภาษี"])

    return "\n".join(lines)
