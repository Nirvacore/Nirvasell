"""Dead Stock Detector — find cash trapped on shelves.

Products with zero or very low sales in X days are dead stock.
Thai resellers can't afford to sit on dead inventory — the margins
are too thin. This module finds them and suggests actions."""
from __future__ import annotations

from datetime import datetime, timedelta

import db


def detect(days: int = 30) -> list[dict]:
    """Find products with no sales in the last N days."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    with db.conn() as c:
        # Products with stock but no recent sales
        rows = c.execute("""
            SELECT p.sku, p.name, p.stock, p.cost_price, p.sell_price,
                   (SELECT MAX(o.order_date) FROM order_items oi
                    JOIN orders o ON o.order_id = oi.order_id
                    WHERE oi.sku = p.sku) AS last_sale_date,
                   (SELECT COALESCE(SUM(oi.qty), 0) FROM order_items oi
                    JOIN orders o ON o.order_id = oi.order_id
                    WHERE oi.sku = p.sku AND o.order_date >= ?) AS recent_qty,
                   (SELECT COALESCE(SUM(oi.qty), 0) FROM order_items oi
                    WHERE oi.sku = p.sku) AS total_qty
            FROM products p
            WHERE p.stock > 0
            ORDER BY recent_qty ASC, p.stock DESC
        """, (cutoff,)).fetchall()

    items = []
    for r in rows:
        d = dict(r)
        stock = d.get("stock") or 0
        cost = d.get("cost_price") or 0
        d["trapped_cash"] = stock * cost
        d["days_since_sale"] = _days_since(d.get("last_sale_date"))

        # Classify severity
        recent = d.get("recent_qty") or 0
        if recent == 0 and d["days_since_sale"] > 60:
            d["severity"] = "dead"
        elif recent == 0 and d["days_since_sale"] > 30:
            d["severity"] = "stale"
        elif recent <= 2:
            d["severity"] = "slow"
        else:
            d["severity"] = "ok"

        if d["severity"] != "ok":
            items.append(d)

    return items


def _days_since(date_str: str | None) -> int:
    if not date_str:
        return 999
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return (datetime.now() - dt).days
    except Exception:
        return 999


def summary(days: int = 30) -> dict:
    """Summary of dead stock situation."""
    items = detect(days)
    total_trapped = sum(i["trapped_cash"] for i in items)
    dead = [i for i in items if i["severity"] == "dead"]
    stale = [i for i in items if i["severity"] == "stale"]
    slow = [i for i in items if i["severity"] == "slow"]

    return {
        "total_items": len(items),
        "dead": len(dead),
        "stale": len(stale),
        "slow": len(slow),
        "trapped_cash": total_trapped,
        "dead_trapped": sum(i["trapped_cash"] for i in dead),
        "stale_trapped": sum(i["trapped_cash"] for i in stale),
        "slow_trapped": sum(i["trapped_cash"] for i in slow),
    }


def suggest_actions(items: list[dict] | None = None) -> list[dict]:
    """Generate action suggestions for dead stock."""
    if items is None:
        items = detect()

    suggestions = []
    for i in items:
        sev = i["severity"]
        if sev == "dead":
            suggestions.append({
                "sku": i["sku"], "name": i["name"],
                "severity": sev,
                "trapped": i["trapped_cash"],
                "action": "liquidate",
                "suggestion": "ขายขาดทุน / bundle กับสินค้าขายดี / ลดราคา 50%+",
            })
        elif sev == "stale":
            suggestions.append({
                "sku": i["sku"], "name": i["name"],
                "severity": sev,
                "trapped": i["trapped_cash"],
                "action": "discount",
                "suggestion": "ลดราคา 20-30% / โปรโมท live / ให้เป็นของแถม",
            })
        elif sev == "slow":
            suggestions.append({
                "sku": i["sku"], "name": i["name"],
                "severity": sev,
                "trapped": i["trapped_cash"],
                "action": "promote",
                "suggestion": "โปรโมทเพิ่ม / ลองช่องทางใหม่ / ปรับรูป/รายละเอียด",
            })

    return suggestions
