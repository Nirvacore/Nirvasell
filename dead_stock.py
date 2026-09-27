"""Dead Stock Detector — find cash trapped on shelves.

Products with zero or very low sales in X days are dead stock.
Thai resellers can't afford to sit on dead inventory — the margins
are too thin. This module finds them and suggests actions."""
from __future__ import annotations

from datetime import datetime, timedelta

import db


def detect(days: int = 30) -> list[dict]:
    """Find products with no sales in the last N days."""
    return _analysis(days)["items"]


def _analysis(days: int = 30) -> dict:
    """Return dead-stock items only when order and product evidence is complete."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    with db.conn() as c:
        missing_order_evidence_rows = c.execute("""
            SELECT COUNT(*) AS count
            FROM orders o
            LEFT JOIN products p ON p.sku = o.sku
            WHERE LOWER(COALESCE(o.status, '')) NOT IN ('cancelled', 'returned')
              AND (
                  o.status IS NULL
                  OR TRIM(o.status) = ''
                  OR o.sku IS NULL
                  OR TRIM(o.sku) = ''
                  OR p.sku IS NULL
                  OR TRIM(p.sku) = ''
                  OR p.cost_price IS NULL
                  OR o.qty IS NULL
                  OR o.order_date IS NULL
                  OR date(o.order_date) IS NULL
                  OR o.total_price IS NULL
              )
        """).fetchone()["count"]
        missing_product_evidence_rows = c.execute("""
            SELECT COUNT(*) AS count
            FROM products
            WHERE stock > 0
              AND (sku IS NULL OR TRIM(sku) = '' OR cost_price IS NULL)
        """).fetchone()["count"]

        if missing_order_evidence_rows or missing_product_evidence_rows:
            return {
                "evidence_complete": False,
                "missing_order_evidence_rows": missing_order_evidence_rows,
                "missing_product_evidence_rows": missing_product_evidence_rows,
                "items": [],
            }

        # LEFT JOIN preserves products that genuinely have no sale rows.
        rows = c.execute("""
            SELECT p.sku, p.name, p.stock, p.cost_price, p.sell_price,
                   MAX(o.order_date) AS last_sale_date,
                   COALESCE(SUM(CASE WHEN o.order_date >= ? THEN o.qty ELSE 0 END), 0)
                       AS recent_qty,
                   COALESCE(SUM(o.qty), 0) AS total_qty
            FROM products p
            LEFT JOIN orders o
              ON o.sku = p.sku
             AND LOWER(o.status) NOT IN ('cancelled', 'returned')
            WHERE p.stock > 0
            GROUP BY p.id, p.sku, p.name, p.stock, p.cost_price, p.sell_price
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

    return {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "items": items,
    }


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
    analysis = _analysis(days)
    if not analysis["evidence_complete"]:
        return {
            "evidence_complete": False,
            "missing_order_evidence_rows": analysis["missing_order_evidence_rows"],
            "missing_product_evidence_rows": analysis["missing_product_evidence_rows"],
            "items": [],
            "total_items": None,
            "dead": None,
            "stale": None,
            "slow": None,
            "trapped_cash": None,
            "dead_trapped": None,
            "stale_trapped": None,
            "slow_trapped": None,
        }

    items = analysis["items"]
    total_trapped = sum(i["trapped_cash"] for i in items)
    dead = [i for i in items if i["severity"] == "dead"]
    stale = [i for i in items if i["severity"] == "stale"]
    slow = [i for i in items if i["severity"] == "slow"]

    return {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "items": items,
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
