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
                COALESCE(o.platform, 'direct') AS platform,
                COUNT(DISTINCT o.order_id) AS orders,
                COUNT(DISTINCT COALESCE(o.buyer_phone, o.buyer_name)) AS customers,
                SUM(o.total_price) AS revenue,
                SUM(o.qty) AS items_sold,
                SUM(CASE WHEN o.total_price IS NULL THEN 1 ELSE 0 END)
                    AS missing_total_price_rows,
                SUM(CASE WHEN o.qty IS NULL THEN 1 ELSE 0 END)
                    AS missing_qty_rows,
                SUM(CASE WHEN p.sku IS NULL THEN 1 ELSE 0 END)
                    AS missing_product_rows,
                SUM(CASE WHEN p.sku IS NOT NULL AND p.cost_price IS NULL
                         THEN 1 ELSE 0 END) AS missing_cost_rows,
                SUM(CASE WHEN p.cost_price IS NOT NULL AND o.qty IS NOT NULL
                         THEN o.qty * p.cost_price ELSE 0 END) AS available_cogs
            FROM orders o
            LEFT JOIN products p ON p.sku = o.sku
            WHERE o.order_date >= ?
              AND LOWER(o.status) NOT IN ('cancelled', 'returned')
            GROUP BY COALESCE(o.platform, 'direct')
        """, (cutoff,)).fetchall()

    if not rows:
        return []

    items = []
    for r in rows:
        d = dict(r)
        d["revenue_complete"] = d["missing_total_price_rows"] == 0
        d["quantity_complete"] = d["missing_qty_rows"] == 0
        d["cogs_complete"] = (
            d["missing_qty_rows"] == 0
            and d["missing_product_rows"] == 0
            and d["missing_cost_rows"] == 0
        )
        d["evidence_complete"] = (
            d["revenue_complete"]
            and d["quantity_complete"]
            and d["cogs_complete"]
        )

        d["revenue"] = round(d["revenue"], 2) if d["revenue_complete"] else None
        d["aov"] = (
            round(d["revenue"] / d["orders"], 2)
            if d["revenue_complete"] and d["orders"] > 0 else None
        )
        d["items_sold"] = d["items_sold"] if d["quantity_complete"] else None
        d["cogs"] = round(d.pop("available_cogs"), 2) if d["cogs_complete"] else None
        d["gross_profit"] = (
            round(d["revenue"] - d["cogs"], 2)
            if d["revenue_complete"] and d["cogs_complete"] else None
        )
        d["margin"] = (
            round(d["gross_profit"] / d["revenue"] * 100, 1)
            if d["gross_profit"] is not None and d["revenue"] > 0
            else (0 if d["gross_profit"] is not None else None)
        )

        # Return count for this platform
        try:
            with db.conn() as c3:
                ret_row = c3.execute("""
                    SELECT COUNT(*) AS cnt FROM returns r
                    JOIN orders o ON o.order_id = r.order_id
                    WHERE COALESCE(o.platform, 'direct') = ?
                      AND r.return_date >= ?
                """, (d["platform"], cutoff)).fetchone()
                d["returns"] = ret_row["cnt"] if ret_row else 0
        except Exception:
            d["returns"] = 0

        d["return_rate"] = round(d["returns"] / d["orders"] * 100, 1) if d["orders"] else 0

        items.append(d)

    revenue_complete = all(item["revenue_complete"] for item in items)
    total_revenue = (
        sum(item["revenue"] for item in items)
        if revenue_complete else None
    )
    for item in items:
        item["revenue_pct"] = (
            round(item["revenue"] / total_revenue * 100, 1)
            if total_revenue and item["revenue"] is not None
            else (0 if revenue_complete else None)
        )

    return sorted(
        items,
        key=lambda item: (
            item["revenue"] is not None,
            item["revenue"] if item["revenue"] is not None else 0,
        ),
        reverse=True,
    )


def growth_by_platform(months: int = 3) -> list[dict]:
    """Month-over-month growth per platform."""
    now = datetime.now()
    results = {}
    evidence = {}

    for m in range(months):
        month_index = now.year * 12 + now.month - 1 - m
        month_start = datetime(month_index // 12, month_index % 12 + 1, 1)
        next_month_index = month_index + 1
        month_end = datetime(
            next_month_index // 12,
            next_month_index % 12 + 1,
            1,
        )
        ms = month_start.strftime("%Y-%m-%d")
        me = month_end.strftime("%Y-%m-%d")
        label = month_start.strftime("%Y-%m")

        with db.conn() as c:
            rows = c.execute("""
                SELECT COALESCE(platform, 'direct') AS platform,
                       SUM(total_price) AS revenue,
                       SUM(CASE WHEN total_price IS NULL THEN 1 ELSE 0 END)
                           AS missing_total_price_rows
                FROM orders
                WHERE order_date >= ? AND order_date < ?
                  AND LOWER(status) NOT IN ('cancelled', 'returned')
                GROUP BY COALESCE(platform, 'direct')
            """, (ms, me)).fetchall()

        for r in rows:
            plat = r["platform"]
            if plat not in results:
                results[plat] = {}
                evidence[plat] = True
            complete = r["missing_total_price_rows"] == 0
            results[plat][label] = round(r["revenue"], 2) if complete else None
            evidence[plat] = evidence[plat] and complete

    items = []
    for plat, months_data in results.items():
        sorted_months = sorted(months_data.keys())
        item = {
            "platform": plat,
            "months": months_data,
            "evidence_complete": evidence[plat],
        }
        if not evidence[plat]:
            item["growth_pct"] = None
        elif len(sorted_months) >= 2:
            latest = months_data[sorted_months[-1]]
            prev = months_data[sorted_months[-2]]
            item["growth_pct"] = round((latest - prev) / prev * 100, 1) if prev > 0 else 0
        else:
            item["growth_pct"] = 0
        items.append(item)

    return sorted(
        items,
        key=lambda item: (
            item["growth_pct"] is not None,
            item["growth_pct"] if item["growth_pct"] is not None else 0,
        ),
        reverse=True,
    )


def summary(days: int = 30) -> dict:
    """Quick summary."""
    platforms = platform_comparison(days)
    if not platforms:
        return {
            "total_platforms": 0,
            "active_platforms": 0,
            "total_orders": 0,
            "top_platform": "—",
            "top_revenue": 0,
            "total_revenue": 0,
            "best_margin": "—",
            "best_margin_pct": 0,
            "evidence_complete": True,
        }

    evidence_complete = all(p["evidence_complete"] for p in platforms)
    if not evidence_complete:
        return {
            "total_platforms": len(platforms),
            "active_platforms": len(platforms),
            "total_orders": sum(p["orders"] for p in platforms),
            "top_platform": "—",
            "top_revenue": None,
            "total_revenue": None,
            "best_margin": "—",
            "best_margin_pct": None,
            "evidence_complete": False,
        }

    return {
        "total_platforms": len(platforms),
        "active_platforms": len(platforms),
        "total_orders": sum(p["orders"] for p in platforms),
        "top_platform": platforms[0]["platform"],
        "top_revenue": platforms[0]["revenue"],
        "total_revenue": sum(p["revenue"] for p in platforms),
        "best_margin": max(platforms, key=lambda x: x["margin"])["platform"],
        "best_margin_pct": max(p["margin"] for p in platforms),
        "evidence_complete": True,
    }
