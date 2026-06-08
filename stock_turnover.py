"""Stock Turnover Analysis — how fast does inventory move?

Key metrics:
  - Turnover Rate = COGS / Average Inventory (higher = better)
  - Days of Inventory (DOI) = 365 / Turnover Rate
  - Reorder Point = Daily Sales × Lead Days + Safety Stock

Thai resellers with thin margins can't afford slow-moving stock.
Fast turnover = more cash cycles per year = more profit."""
from __future__ import annotations

from datetime import datetime, timedelta

import db


def calculate() -> list[dict]:
    """Calculate stock turnover for each SKU."""
    with db.conn() as c:
        rows = c.execute("""
            SELECT p.sku, p.name, p.stock, p.cost_price, p.sell_price,
                   COALESCE(SUM(oi.qty), 0) AS total_sold,
                   COUNT(DISTINCT o.order_id) AS order_count,
                   MIN(o.order_date) AS first_sale,
                   MAX(o.order_date) AS last_sale
            FROM products p
            LEFT JOIN order_items oi ON oi.sku = p.sku
            LEFT JOIN orders o ON o.order_id = oi.order_id
            GROUP BY p.sku
            ORDER BY total_sold DESC
        """).fetchall()

    if not rows:
        return []

    items = []
    now = datetime.now()

    for r in rows:
        d = dict(r)
        stock = d.get("stock") or 0
        cost = d.get("cost_price") or 0
        sold = d.get("total_sold") or 0

        # Trading period
        first_sale = d.get("first_sale")
        if first_sale:
            try:
                first_dt = datetime.strptime(str(first_sale)[:10], "%Y-%m-%d")
                trading_days = max((now - first_dt).days, 1)
            except Exception:
                trading_days = 90  # default
        else:
            trading_days = 90

        # Daily sales velocity
        daily_sales = sold / trading_days if trading_days > 0 else 0

        # Stock value
        stock_value = stock * cost

        # COGS for period
        cogs_total = sold * cost

        # Average inventory (simple: current stock as proxy)
        avg_inventory_value = stock_value if stock_value > 0 else 1

        # Turnover rate (annualized)
        if trading_days > 0 and avg_inventory_value > 0:
            turnover_rate = (cogs_total / avg_inventory_value) * (365 / trading_days)
        else:
            turnover_rate = 0

        # Days of inventory
        doi = round(stock / daily_sales, 0) if daily_sales > 0 else 999

        # Reorder point (assume 7-day lead time + 3 days safety)
        lead_days = 7
        safety_days = 3
        reorder_point = round(daily_sales * (lead_days + safety_days), 0)

        # Health status
        if doi <= 14:
            health = "fast"
        elif doi <= 30:
            health = "good"
        elif doi <= 60:
            health = "slow"
        else:
            health = "stuck"

        d["daily_sales"] = round(daily_sales, 2)
        d["stock_value"] = round(stock_value, 0)
        d["turnover_rate"] = round(turnover_rate, 1)
        d["doi"] = int(min(doi, 999))
        d["reorder_point"] = int(reorder_point)
        d["needs_reorder"] = stock <= reorder_point and daily_sales > 0
        d["health"] = health
        d["trading_days"] = trading_days

        items.append(d)

    return items


def summary() -> dict:
    """Overall stock turnover summary."""
    items = calculate()
    if not items:
        return {
            "total_skus": 0,
            "avg_turnover": 0,
            "avg_doi": 0,
            "total_stock_value": 0,
            "need_reorder": 0,
            "health": {"fast": 0, "good": 0, "slow": 0, "stuck": 0},
        }

    health = {"fast": 0, "good": 0, "slow": 0, "stuck": 0}
    for i in items:
        health[i["health"]] = health.get(i["health"], 0) + 1

    selling = [i for i in items if i["daily_sales"] > 0]
    avg_turnover = (sum(i["turnover_rate"] for i in selling) / len(selling)) if selling else 0
    avg_doi = (sum(i["doi"] for i in selling) / len(selling)) if selling else 0

    return {
        "total_skus": len(items),
        "avg_turnover": round(avg_turnover, 1),
        "avg_doi": int(avg_doi),
        "total_stock_value": sum(i["stock_value"] for i in items),
        "need_reorder": sum(1 for i in items if i["needs_reorder"]),
        "health": health,
    }


def reorder_list() -> list[dict]:
    """Products that need reordering."""
    return [i for i in calculate() if i["needs_reorder"]]
