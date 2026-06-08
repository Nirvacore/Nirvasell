"""SKU Performance Trends — week-over-week and month-over-month.

Not just "this SKU sold 50 units" but "this SKU is UP 30% vs last week".
Spot rising stars early, catch declining products before it's too late."""
from __future__ import annotations

from datetime import datetime, timedelta

import db


def weekly_trend(weeks: int = 4) -> list[dict]:
    """Per-SKU sales trend across weeks. Returns WoW change."""
    now = datetime.now()
    results = {}

    for w in range(weeks):
        end = now - timedelta(weeks=w)
        start = end - timedelta(days=7)
        s_str = start.strftime("%Y-%m-%d")
        e_str = end.strftime("%Y-%m-%d")
        label = "W-" + str(w) if w > 0 else "This Week"

        with db.conn() as c:
            rows = c.execute("""
                SELECT oi.sku,
                       COALESCE(SUM(oi.qty), 0) AS qty,
                       COALESCE(SUM(oi.qty * oi.unit_price), 0) AS revenue
                FROM order_items oi
                JOIN orders o ON o.order_id = oi.order_id
                WHERE o.order_date >= ? AND o.order_date < ?
                GROUP BY oi.sku
            """, (s_str, e_str)).fetchall()

        for r in rows:
            sku = r["sku"]
            if sku not in results:
                results[sku] = {"sku": sku, "weeks": {}}
            results[sku]["weeks"][label] = {
                "qty": r["qty"],
                "revenue": r["revenue"],
            }

    # Calculate WoW change
    items = []
    for sku, data in results.items():
        this_week = data["weeks"].get("This Week", {})
        last_week = data["weeks"].get("W-1", {})

        qty_now = this_week.get("qty", 0)
        qty_prev = last_week.get("qty", 0)
        rev_now = this_week.get("revenue", 0)
        rev_prev = last_week.get("revenue", 0)

        qty_change = ((qty_now - qty_prev) / qty_prev * 100) if qty_prev > 0 else (100 if qty_now > 0 else 0)
        rev_change = ((rev_now - rev_prev) / rev_prev * 100) if rev_prev > 0 else (100 if rev_now > 0 else 0)

        # Get product name
        with db.conn() as c:
            p = c.execute("SELECT name FROM products WHERE sku=?", (sku,)).fetchone()

        # Trend direction
        if qty_change > 20:
            trend = "rising"
        elif qty_change < -20:
            trend = "declining"
        else:
            trend = "stable"

        items.append({
            "sku": sku,
            "name": p["name"] if p else "",
            "qty_this_week": qty_now,
            "qty_last_week": qty_prev,
            "qty_change_pct": round(qty_change, 1),
            "rev_this_week": rev_now,
            "rev_last_week": rev_prev,
            "rev_change_pct": round(rev_change, 1),
            "trend": trend,
            "weeks": data["weeks"],
        })

    return sorted(items, key=lambda x: x["rev_change_pct"], reverse=True)


def rising_stars(min_change: float = 20) -> list[dict]:
    """Products with significant growth."""
    return [i for i in weekly_trend() if i["trend"] == "rising" and i["qty_this_week"] >= 3]


def declining(min_change: float = -20) -> list[dict]:
    """Products losing momentum."""
    return [i for i in weekly_trend() if i["trend"] == "declining"]


def new_products(days: int = 14) -> list[dict]:
    """Recently added products and their early performance."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    with db.conn() as c:
        rows = c.execute("""
            SELECT p.sku, p.name, p.stock, p.sell_price,
                   COALESCE(SUM(oi.qty), 0) AS total_sold,
                   COALESCE(SUM(oi.qty * oi.unit_price), 0) AS total_revenue
            FROM products p
            LEFT JOIN order_items oi ON oi.sku = p.sku
            LEFT JOIN orders o ON o.order_id = oi.order_id
            WHERE p.created_at >= ?
            GROUP BY p.sku
            ORDER BY total_sold DESC
        """, (cutoff,)).fetchall()

    return [dict(r) for r in rows]


def summary() -> dict:
    trends = weekly_trend()
    rising = [t for t in trends if t["trend"] == "rising"]
    declining_ = [t for t in trends if t["trend"] == "declining"]
    stable = [t for t in trends if t["trend"] == "stable"]

    return {
        "total_skus": len(trends),
        "rising": len(rising),
        "declining": len(declining_),
        "stable": len(stable),
        "top_gainer": rising[0]["sku"] if rising else "—",
        "top_gainer_pct": rising[0]["rev_change_pct"] if rising else 0,
        "top_loser": declining_[-1]["sku"] if declining_ else "—",
        "top_loser_pct": declining_[-1]["rev_change_pct"] if declining_ else 0,
    }
