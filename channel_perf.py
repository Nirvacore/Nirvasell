"""Channel Performance — compare platforms side by side.

Shopee vs Lazada vs TikTok vs LINE vs Facebook.
Which channel makes real profit? Which is just vanity?"""
from __future__ import annotations

from datetime import datetime, timedelta

import db


def platform_comparison(days: int = 30) -> list[dict]:
    """Side-by-side platform comparison."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    with db.conn() as c:
        rows = c.execute("""
            SELECT
                o.platform,
                COUNT(DISTINCT o.order_id) AS orders,
                COUNT(DISTINCT COALESCE(o.buyer_phone, o.buyer_name)) AS customers,
                COALESCE(SUM(o.total_amount), 0) AS revenue,
                COALESCE(SUM(oi.qty), 0) AS items_sold,
                AVG(o.total_amount) AS aov
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.order_date >= ?
            GROUP BY o.platform
            ORDER BY revenue DESC
        """, (cutoff,)).fetchall()

    if not rows:
        return []

    total_revenue = sum(r["revenue"] or 0 for r in rows)
    items = []
    for r in rows:
        d = dict(r)
        d["revenue_pct"] = round((d["revenue"] or 0) / total_revenue * 100, 1) if total_revenue > 0 else 0
        d["aov"] = round(d["aov"] or 0, 0)

        # Get COGS for this platform
        with db.conn() as c2:
            cogs_row = c2.execute("""
                SELECT COALESCE(SUM(oi.qty * p.cost_price), 0) AS cogs
                FROM order_items oi
                JOIN orders o ON o.order_id = oi.order_id
                LEFT JOIN products p ON p.sku = oi.sku
                WHERE o.platform = ? AND o.order_date >= ?
            """, (d["platform"], cutoff)).fetchall()

        cogs = cogs_row[0]["cogs"] if cogs_row else 0
        d["cogs"] = cogs
        d["gross_profit"] = (d["revenue"] or 0) - cogs
        d["margin"] = round(d["gross_profit"] / d["revenue"] * 100, 1) if d["revenue"] else 0

        # Return count for this platform
        try:
            with db.conn() as c3:
                ret_row = c3.execute("""
                    SELECT COUNT(*) AS cnt FROM returns r
                    JOIN orders o ON o.order_id = r.order_id
                    WHERE o.platform = ? AND r.return_date >= ?
                """, (d["platform"], cutoff)).fetchone()
                d["returns"] = ret_row["cnt"] if ret_row else 0
        except Exception:
            d["returns"] = 0

        d["return_rate"] = round(d["returns"] / d["orders"] * 100, 1) if d["orders"] else 0

        items.append(d)

    return items


def growth_by_platform(months: int = 3) -> list[dict]:
    """Month-over-month growth per platform."""
    now = datetime.now()
    results = {}

    for m in range(months):
        month_end = now.replace(day=1) - timedelta(days=m * 28)
        month_start = month_end.replace(day=1)
        ms = month_start.strftime("%Y-%m-%d")
        me = month_end.strftime("%Y-%m-%d")
        label = month_start.strftime("%Y-%m")

        with db.conn() as c:
            rows = c.execute("""
                SELECT platform, COALESCE(SUM(total_amount), 0) AS revenue
                FROM orders WHERE order_date >= ? AND order_date < ?
                GROUP BY platform
            """, (ms, me)).fetchall()

        for r in rows:
            plat = r["platform"]
            if plat not in results:
                results[plat] = {}
            results[plat][label] = r["revenue"]

    items = []
    for plat, months_data in results.items():
        sorted_months = sorted(months_data.keys())
        item = {"platform": plat, "months": months_data}
        if len(sorted_months) >= 2:
            latest = months_data[sorted_months[-1]]
            prev = months_data[sorted_months[-2]]
            item["growth_pct"] = round((latest - prev) / prev * 100, 1) if prev > 0 else 0
        else:
            item["growth_pct"] = 0
        items.append(item)

    return sorted(items, key=lambda x: x["growth_pct"], reverse=True)


def summary(days: int = 30) -> dict:
    """Quick summary."""
    platforms = platform_comparison(days)
    if not platforms:
        return {
            "total_platforms": 0,
            "top_platform": "—",
            "top_revenue": 0,
            "total_revenue": 0,
        }

    return {
        "total_platforms": len(platforms),
        "top_platform": platforms[0]["platform"],
        "top_revenue": platforms[0]["revenue"],
        "total_revenue": sum(p["revenue"] for p in platforms),
        "best_margin": max(platforms, key=lambda x: x["margin"])["platform"],
        "best_margin_pct": max(p["margin"] for p in platforms),
    }
