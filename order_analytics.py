"""Order analytics — discover when, where, and what sells best.

Peak hours, best days, platform trends, AOV tracking. Helps sellers
decide when to run ads and which products to push."""
from __future__ import annotations

from datetime import datetime, timedelta

import db


def hourly_distribution() -> list[dict]:
    """Orders by hour of day. Returns [{hour: 0..23, count: n, revenue: x}]."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT CAST(strftime('%H', order_date) AS INTEGER) as hour, "
            "COUNT(*) as count, SUM(total_price) as revenue "
            "FROM orders WHERE order_date IS NOT NULL "
            "GROUP BY hour ORDER BY hour"
        ).fetchall()
    return [dict(r) for r in rows]


def daily_distribution() -> list[dict]:
    """Orders by day of week. 0=Mon, 6=Sun."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT CAST(strftime('%w', order_date) AS INTEGER) as dow, "
            "COUNT(*) as count, SUM(total_price) as revenue "
            "FROM orders WHERE order_date IS NOT NULL "
            "GROUP BY dow ORDER BY dow"
        ).fetchall()
    return [dict(r) for r in rows]


def peak_hours(top_n: int = 3) -> list[dict]:
    """Top N best selling hours."""
    dist = hourly_distribution()
    return sorted(dist, key=lambda x: x.get("revenue", 0), reverse=True)[:top_n]


def best_day() -> dict | None:
    dist = daily_distribution()
    if not dist:
        return None
    return max(dist, key=lambda x: x.get("revenue", 0))


def platform_trend(months: int = 6) -> list[dict]:
    """Monthly revenue per platform."""
    now = datetime.now()
    cutoff = (now - timedelta(days=30 * months)).strftime("%Y-%m-%d")
    with db.conn() as c:
        rows = c.execute(
            "SELECT strftime('%Y-%m', order_date) as month, "
            "platform, COUNT(*) as orders, SUM(total_price) as revenue "
            "FROM orders WHERE order_date >= ? "
            "GROUP BY month, platform ORDER BY month",
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


def aov_trend(months: int = 6) -> list[dict]:
    """Average order value per month."""
    now = datetime.now()
    cutoff = (now - timedelta(days=30 * months)).strftime("%Y-%m-%d")
    with db.conn() as c:
        rows = c.execute(
            "SELECT strftime('%Y-%m', order_date) as month, "
            "AVG(total_price) as aov, COUNT(*) as orders "
            "FROM orders WHERE order_date >= ? "
            "GROUP BY month ORDER BY month",
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


def repeat_purchase_rate() -> dict:
    """How many customers ordered more than once."""
    with db.conn() as c:
        total = c.execute(
            "SELECT COUNT(DISTINCT buyer_name) FROM orders "
            "WHERE buyer_name IS NOT NULL AND buyer_name != ''"
        ).fetchone()[0]
        repeat = c.execute(
            "SELECT COUNT(*) FROM ("
            "SELECT buyer_name FROM orders "
            "WHERE buyer_name IS NOT NULL AND buyer_name != '' "
            "GROUP BY buyer_name HAVING COUNT(*) > 1)"
        ).fetchone()[0]
    return {
        "total_buyers": total,
        "repeat_buyers": repeat,
        "repeat_rate": round(repeat / total * 100, 1) if total else 0,
    }


def top_combos(limit: int = 5) -> list[dict]:
    """Products frequently bought together (same order)."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT a.sku as sku_a, b.sku as sku_b, COUNT(*) as freq "
            "FROM orders a JOIN orders b ON a.order_id = b.order_id "
            "AND a.sku < b.sku "
            "WHERE a.order_id IS NOT NULL AND a.order_id != '' "
            "GROUP BY a.sku, b.sku "
            "HAVING freq >= 2 "
            "ORDER BY freq DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
