"""Pick & Pack Lists — warehouse operations made simple.

Generates pick lists (which items to grab from shelves) and pack
slips (what goes in each box) from pending orders. Exportable as
printable format."""
from __future__ import annotations

from datetime import date

import db


def pending_orders() -> list[dict]:
    """Get all orders not yet fulfilled."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT o.*, p.name as product_name, p.brand, "
            "p.image_url, p.category "
            "FROM orders o LEFT JOIN products p ON p.id = o.product_id "
            "WHERE o.status IS NULL OR o.status IN ('new','pending','confirmed') "
            "ORDER BY o.order_date DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def generate_pick_list() -> list[dict]:
    """Aggregate pending orders into a pick list.
    Groups by SKU so warehouse picker grabs all of one item at once."""
    orders = pending_orders()
    sku_map: dict[str, dict] = {}

    for o in orders:
        sku = o.get("sku") or "UNKNOWN"
        if sku not in sku_map:
            sku_map[sku] = {
                "sku": sku,
                "name": o.get("product_name") or o.get("name") or "",
                "brand": o.get("brand") or "",
                "category": o.get("category") or "",
                "total_qty": 0,
                "order_count": 0,
                "order_ids": [],
            }
        sku_map[sku]["total_qty"] += int(o.get("qty") or 1)
        sku_map[sku]["order_count"] += 1
        oid = o.get("order_id") or ""
        if oid and oid not in sku_map[sku]["order_ids"]:
            sku_map[sku]["order_ids"].append(oid)

    return sorted(sku_map.values(), key=lambda x: x["total_qty"], reverse=True)


def generate_pack_slips() -> list[dict]:
    """Generate one pack slip per order."""
    orders = pending_orders()
    order_map: dict[str, dict] = {}

    for o in orders:
        oid = o.get("order_id") or str(o.get("id", ""))
        if oid not in order_map:
            order_map[oid] = {
                "order_id": oid,
                "order_date": o.get("order_date") or "",
                "platform": o.get("platform") or "",
                "buyer_name": o.get("buyer_name") or "",
                "buyer_phone": o.get("buyer_phone") or "",
                "items": [],
                "total": 0,
            }
        order_map[oid]["items"].append({
            "sku": o.get("sku") or "",
            "name": o.get("product_name") or "",
            "qty": int(o.get("qty") or 1),
            "price": float(o.get("unit_price") or 0),
            "subtotal": float(o.get("total_price") or 0),
        })
        order_map[oid]["total"] += float(o.get("total_price") or 0)

    return sorted(order_map.values(), key=lambda x: x["order_date"], reverse=True)


def pick_list_text() -> str:
    """Plain text pick list for printing."""
    items = generate_pick_list()
    if not items:
        return "ไม่มีรายการที่ต้อง pick"

    lines = [
        "=" * 50,
        "PICK LIST — " + date.today().isoformat(),
        "=" * 50,
        "",
    ]
    for i, item in enumerate(items, 1):
        lines.append(
            str(i) + ". [ ] " + item["sku"] +
            " — " + item["name"][:30] +
            " × " + str(item["total_qty"]) +
            " (" + str(item["order_count"]) + " orders)"
        )
    lines.extend([
        "",
        "-" * 50,
        "Total SKUs: " + str(len(items)),
        "Total items: " + str(sum(i["total_qty"] for i in items)),
        "=" * 50,
    ])
    return "\n".join(lines)


def pack_slip_text(order_id: str) -> str:
    """Plain text pack slip for one order."""
    slips = generate_pack_slips()
    slip = None
    for s in slips:
        if s["order_id"] == order_id:
            slip = s
            break

    if not slip:
        return "Order not found: " + order_id

    lines = [
        "=" * 50,
        "PACK SLIP",
        "=" * 50,
        "Order: " + slip["order_id"],
        "Date:  " + slip["order_date"][:10],
        "Platform: " + slip["platform"],
        "Buyer: " + slip["buyer_name"],
        "Phone: " + slip["buyer_phone"],
        "-" * 50,
    ]
    for item in slip["items"]:
        lines.append(
            "  [ ] " + item["sku"] + " — " + item["name"][:25] +
            " × " + str(item["qty"]) +
            "  ฿" + "{:,.0f}".format(item["subtotal"])
        )
    lines.extend([
        "-" * 50,
        "TOTAL: ฿" + "{:,.0f}".format(slip["total"]),
        "=" * 50,
    ])
    return "\n".join(lines)


def all_pack_slips_text() -> str:
    """All pack slips as one printable document."""
    slips = generate_pack_slips()
    if not slips:
        return "ไม่มีออเดอร์ที่ต้องแพ็ค"

    sections = []
    for s in slips:
        sections.append(pack_slip_text(s["order_id"]))
    return "\n\n".join(sections)
