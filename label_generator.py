"""Label Generator — packing slip and shipping address label text."""
from __future__ import annotations
import db

LABEL_STYLES = {
    "full":    "ครบทุกข้อมูล",
    "compact": "กระชับ (เฉพาะที่จำเป็น)",
    "cod":     "COD (แสดงยอดเก็บปลายทาง)",
}


def init() -> None:
    """Load shop profile from settings for label generation."""
    pass


def _shop_info() -> dict:
    with db.conn() as c:
        try:
            row = c.execute(
                "SELECT * FROM settings WHERE key='shop_profile'"
            ).fetchone()
            if row:
                import json
                return json.loads(row["value"] or "{}")
        except Exception:
            pass
    return {
        "name": "ร้านค้า", "phone": "", "address": "",
        "line": "", "facebook": "",
    }


def generate_label(order_id: str = "", buyer_name: str = "",
                   buyer_phone: str = "", buyer_address: str = "",
                   items: list[dict] = None, total_price: float = 0,
                   cod_amount: float = 0, tracking: str = "",
                   carrier: str = "kerry", notes: str = "",
                   style: str = "full") -> str:
    if items is None:
        items = []

    shop = _shop_info()

    lines = []
    if style == "full":
        lines += [
            "=" * 40,
            "📦 ใบแพ็คสินค้า / PACKING SLIP",
            "=" * 40,
            "ออเดอร์: " + (order_id or "—"),
            "ผู้รับ: " + (buyer_name or "—"),
            "โทร: " + (buyer_phone or "—"),
            "ที่อยู่: " + (buyer_address or "—"),
            "-" * 40,
        ]
        for item in items:
            lines.append(
                "  " + (item.get("sku") or "") + " · " +
                str(item.get("qty", 1)) + " ชิ้น" +
                (" · ฿{:,.0f}".format(item.get("price", 0)) if item.get("price") else "")
            )
        lines += [
            "-" * 40,
            "ยอดรวม: ฿{:,.0f}".format(total_price),
        ]
        if cod_amount > 0:
            lines.append("💰 ยอดเก็บปลายทาง (COD): ฿{:,.0f}".format(cod_amount))
        if tracking:
            lines.append("Tracking: " + tracking + " (" + carrier + ")")
        if notes:
            lines.append("หมายเหตุ: " + notes)
        lines += [
            "-" * 40,
            "ผู้ส่ง: " + shop.get("name", ""),
            "โทร: " + shop.get("phone", ""),
            "=" * 40,
        ]
    elif style == "compact":
        lines += [
            buyer_name or "—",
            buyer_phone or "—",
            buyer_address or "—",
        ]
        if cod_amount > 0:
            lines.append("COD ฿{:,.0f}".format(cod_amount))
        if tracking:
            lines.append(tracking)
    elif style == "cod":
        lines += [
            "=" * 30,
            "ผู้รับ: " + (buyer_name or "—"),
            "โทร: " + (buyer_phone or "—"),
            "ที่อยู่: " + (buyer_address or "—"),
            "💰 เก็บเงินปลายทาง: ฿{:,.0f}".format(cod_amount),
            (tracking or ""),
            "=" * 30,
        ]
    return "\n".join(lines)


def from_order(order_id_str: str, style: str = "full") -> str:
    """Auto-generate label from a saved order."""
    with db.conn() as c:
        try:
            row = c.execute(
                "SELECT * FROM orders WHERE id=? OR order_id=? LIMIT 1",
                (order_id_str, order_id_str),
            ).fetchone()
            if not row:
                return "ไม่พบออเดอร์ " + order_id_str
            items_rows = c.execute(
                "SELECT sku, quantity qty, unit_price price "
                "FROM order_items WHERE order_id=?",
                (row["id"],),
            ).fetchall()
            items = [dict(r) for r in items_rows]
            cod = row["total_price"] if row.get("payment_method") == "cod" else 0
            return generate_label(
                order_id=str(row["id"]),
                buyer_name=row.get("buyer_name") or "",
                buyer_phone=row.get("buyer_phone") or "",
                buyer_address=row.get("buyer_address") or "",
                items=items,
                total_price=row.get("total_price") or 0,
                cod_amount=cod,
                tracking=row.get("tracking_number") or "",
                carrier=row.get("carrier") or "kerry",
                notes=row.get("notes") or "",
                style=style,
            )
        except Exception as e:
            return "Error: " + str(e)


def stats() -> dict:
    with db.conn() as c:
        try:
            today_orders = c.execute(
                "SELECT COUNT(*) FROM orders WHERE date(order_date)=date('now','localtime')"
            ).fetchone()[0]
        except Exception:
            today_orders = 0
    return {"today_orders": today_orders}
