"""Profit Calendar — daily profit heatmap like GitHub contributions.

See at a glance which days made money, which days lost money.
Spot patterns: weekend vs weekday, campaign days, seasonal trends."""
from __future__ import annotations

from datetime import datetime, timedelta, date

import db


def daily_profits(days: int = 90) -> list[dict]:
    """Calculate net profit for each day in the last N days."""
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    with db.conn() as c:
        rows = c.execute("""
            SELECT
                o.order_date AS day,
                COALESCE(SUM(oi.qty * oi.unit_price), 0) AS revenue,
                COALESCE(SUM(oi.qty * p.cost_price), 0) AS cogs
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            LEFT JOIN products p ON p.sku = oi.sku
            WHERE o.order_date >= ?
            GROUP BY o.order_date
            ORDER BY o.order_date
        """, (start,)).fetchall()

    # Build day-by-day map
    day_map = {}
    for r in rows:
        d = r["day"]
        if d:
            day_map[d[:10]] = {
                "revenue": r["revenue"] or 0,
                "cogs": r["cogs"] or 0,
            }

    # Fill all days
    result = []
    current = datetime.now() - timedelta(days=days)
    for _ in range(days + 1):
        ds = current.strftime("%Y-%m-%d")
        data = day_map.get(ds, {"revenue": 0, "cogs": 0})
        profit = data["revenue"] - data["cogs"]

        result.append({
            "date": ds,
            "weekday": current.strftime("%a"),
            "weekday_num": current.weekday(),
            "revenue": data["revenue"],
            "cogs": data["cogs"],
            "profit": profit,
            "has_data": ds in day_map,
        })
        current += timedelta(days=1)

    return result


def weekly_summary(days: int = 90) -> list[dict]:
    """Aggregate daily profits into weeks."""
    daily = daily_profits(days)
    weeks = []
    current_week = []

    for d in daily:
        current_week.append(d)
        if d["weekday_num"] == 6 or d == daily[-1]:  # Sunday or last day
            revenue = sum(x["revenue"] for x in current_week)
            cogs = sum(x["cogs"] for x in current_week)
            profit = revenue - cogs
            weeks.append({
                "start": current_week[0]["date"],
                "end": current_week[-1]["date"],
                "revenue": revenue,
                "cogs": cogs,
                "profit": profit,
                "days_with_sales": sum(1 for x in current_week if x["has_data"]),
                "best_day": max(current_week, key=lambda x: x["profit"])["date"] if current_week else "",
            })
            current_week = []

    return weeks


def monthly_summary(months: int = 6) -> list[dict]:
    """Monthly profit summary."""
    daily = daily_profits(months * 31)
    monthly = {}

    for d in daily:
        month_key = d["date"][:7]  # YYYY-MM
        if month_key not in monthly:
            monthly[month_key] = {"revenue": 0, "cogs": 0, "days": 0}
        monthly[month_key]["revenue"] += d["revenue"]
        monthly[month_key]["cogs"] += d["cogs"]
        if d["has_data"]:
            monthly[month_key]["days"] += 1

    result = []
    for k in sorted(monthly.keys()):
        m = monthly[k]
        result.append({
            "month": k,
            "revenue": m["revenue"],
            "cogs": m["cogs"],
            "profit": m["revenue"] - m["cogs"],
            "days_with_sales": m["days"],
        })

    return result


def best_worst_days(days: int = 90, top: int = 5) -> dict:
    """Find the best and worst profit days."""
    daily = [d for d in daily_profits(days) if d["has_data"]]
    if not daily:
        return {"best": [], "worst": []}

    by_profit = sorted(daily, key=lambda x: x["profit"], reverse=True)
    return {
        "best": by_profit[:top],
        "worst": by_profit[-top:],
    }
