"""Label Generator — packing slip and shipping address label text."""
from __future__ import annotations

import db
from i18n import t
from i18n_inline import carrier_name

LABEL_STYLES = ("full", "compact", "cod")


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
        "name": t("lbl.shop_default"), "phone": "", "address": "",
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
    dash = "-" * 40
    eq = "=" * 40
    carrier_label = carrier_name(carrier)

    lines = []
    if style == "full":
        lines += [
            eq,
            t("lbl.body_title"),
            eq,
            t("lbl.body_order", id=order_id or "—"),
            t("lbl.body_recipient", name=buyer_name or "—"),
            t("lbl.body_phone", phone=buyer_phone or "—"),
            t("lbl.body_address", address=buyer_address or "—"),
            dash,
        ]
        unit = t("lbl.unit_pcs")
        for item in items:
            line = t("lbl.body_item",
                     sku=item.get("sku") or "",
                     qty=str(item.get("qty", 1)),
                     unit=unit)
            if item.get("price"):
                line += t("lbl.body_item_price",
                          amount="{:,.0f}".format(item.get("price", 0)))
            lines.append(line)
        lines += [
            dash,
            t("lbl.body_total", amount="{:,.0f}".format(total_price)),
        ]
        if cod_amount > 0:
            lines.append(t("lbl.body_cod", amount="{:,.0f}".format(cod_amount)))
        if tracking:
            lines.append(t("lbl.body_tracking",
                           number=tracking, carrier=carrier_label))
        if notes:
            lines.append(t("lbl.body_notes", notes=notes))
        lines += [
            dash,
            t("lbl.body_sender", name=shop.get("name", "")),
            t("lbl.body_phone", phone=shop.get("phone", "")),
            eq,
        ]
    elif style == "compact":
        lines += [
            buyer_name or "—",
            buyer_phone or "—",
            buyer_address or "—",
        ]
        if cod_amount > 0:
            lines.append(t("lbl.body_cod_compact",
                           amount="{:,.0f}".format(cod_amount)))
        if tracking:
            lines.append(tracking)
    elif style == "cod":
        lines += [
            "=" * 30,
            t("lbl.body_recipient", name=buyer_name or "—"),
            t("lbl.body_phone", phone=buyer_phone or "—"),
            t("lbl.body_address", address=buyer_address or "—"),
            t("lbl.body_cod_collect", amount="{:,.0f}".format(cod_amount)),
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
                return t("lbl.order_not_found", id=order_id_str)
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
            return t("lbl.error_prefix", msg=str(e))


def stats() -> dict:
    with db.conn() as c:
        try:
            today_orders = c.execute(
                "SELECT COUNT(*) FROM orders WHERE date(order_date)=date('now','localtime')"
            ).fetchone()[0]
        except Exception:
            today_orders = 0
    return {"today_orders": today_orders}
