"""ABC Analysis — the Pareto rule for inventory investment.

A items = top 80% of revenue (your cash cows — never let them stock out)
B items = next 15% (important but not critical)
C items = bottom 5% (consider trimming or reducing stock)

Every serious retailer uses ABC to decide WHERE to invest limited cash."""
from __future__ import annotations

import db


def classify() -> list[dict]:
    """Classify all products into A/B/C by revenue contribution."""
    with db.conn() as c:
        rows = c.execute("""
            SELECT p.sku, p.name, p.stock, p.cost_price, p.sell_price,
                   COALESCE(SUM(oi.qty), 0) AS total_qty,
                   COALESCE(SUM(oi.qty * oi.unit_price), 0) AS total_revenue
            FROM products p
            LEFT JOIN order_items oi ON oi.sku = p.sku
            LEFT JOIN orders o ON o.order_id = oi.order_id
            GROUP BY p.sku
            ORDER BY total_revenue DESC
        """).fetchall()

    if not rows:
        return []

    items = [dict(r) for r in rows]
    grand_total = sum(i["total_revenue"] for i in items)
    if grand_total <= 0:
        for i in items:
            i["class"] = "C"
            i["cumulative_pct"] = 0
            i["revenue_pct"] = 0
            i["stock_value"] = (i.get("cost_price") or 0) * (i.get("stock") or 0)
        return items

    cumulative = 0
    for i in items:
        i["revenue_pct"] = round(i["total_revenue"] / grand_total * 100, 1)
        cumulative += i["total_revenue"]
        i["cumulative_pct"] = round(cumulative / grand_total * 100, 1)
        i["stock_value"] = (i.get("cost_price") or 0) * (i.get("stock") or 0)

        if i["cumulative_pct"] <= 80:
            i["class"] = "A"
        elif i["cumulative_pct"] <= 95:
            i["class"] = "B"
        else:
            i["class"] = "C"

    return items


def summary() -> dict:
    """Summary counts and revenue per class."""
    items = classify()
    result = {"A": {"count": 0, "revenue": 0, "stock_value": 0},
              "B": {"count": 0, "revenue": 0, "stock_value": 0},
              "C": {"count": 0, "revenue": 0, "stock_value": 0}}
    for i in items:
        cls = i["class"]
        result[cls]["count"] += 1
        result[cls]["revenue"] += i["total_revenue"]
        result[cls]["stock_value"] += i["stock_value"]
    result["total_skus"] = len(items)
    return result


def class_items(cls: str) -> list[dict]:
    """Get items for a specific class (A/B/C)."""
    return [i for i in classify() if i["class"] == cls]


def investment_advice() -> list[dict]:
    """Generate inventory investment recommendations."""
    items = classify()
    advice = []

    for i in items:
        stock = i.get("stock") or 0
        qty_sold = i.get("total_qty") or 0
        cls = i["class"]

        if cls == "A" and stock < 5:
            advice.append({
                "sku": i["sku"], "name": i["name"],
                "class": cls, "stock": stock,
                "action": "restock_urgent",
                "priority": "high",
            })
        elif cls == "A" and stock < 10:
            advice.append({
                "sku": i["sku"], "name": i["name"],
                "class": cls, "stock": stock,
                "action": "restock_soon",
                "priority": "medium",
            })
        elif cls == "C" and stock > 20 and qty_sold < 3:
            advice.append({
                "sku": i["sku"], "name": i["name"],
                "class": cls, "stock": stock,
                "action": "reduce_stock",
                "priority": "low",
            })

    return sorted(advice, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]])
