"""Sales Goals — set targets, track progress, celebrate wins.

Monthly revenue target, order count target, new customer target.
Visual progress bars. Alert when behind pace."""
from __future__ import annotations

from datetime import datetime, date

import db
from i18n_inline import goal_type_label, goal_type_unit


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS sales_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                metric TEXT NOT NULL,
                target REAL NOT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


METRICS = {
    "revenue":       {"icon": "💰"},
    "orders":        {"icon": "📦"},
    "profit":        {"icon": "💵"},
    "new_customers": {"icon": "👥"},
    "avg_order":     {"icon": "🎯"},
}


def set_goal(period: str, metric: str, target: float) -> int:
    """Set or update a goal. period = YYYY-MM."""
    with db.conn() as c:
        existing = c.execute(
            "SELECT id FROM sales_goals WHERE period=? AND metric=?",
            (period, metric),
        ).fetchone()
        if existing:
            c.execute("UPDATE sales_goals SET target=? WHERE id=?",
                      (target, existing["id"]))
            return existing["id"]
        else:
            c.execute(
                "INSERT INTO sales_goals (period, metric, target) VALUES (?,?,?)",
                (period, metric, target),
            )
            return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def delete_goal(goal_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM sales_goals WHERE id=?", (goal_id,))


def goals_for_period(period: str = "") -> list[dict]:
    """Get all goals for a period with actual progress."""
    if not period:
        period = date.today().strftime("%Y-%m")

    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM sales_goals WHERE period=? ORDER BY metric",
            (period,),
        ).fetchall()

    results = []
    for r in rows:
        d = dict(r)
        actual = _get_actual(d["metric"], period)
        target = d["target"]
        pct = round(actual / target * 100, 1) if target > 0 else 0

        # Days progress
        today = date.today()
        days_in_month = 30
        days_elapsed = today.day
        pace_pct = round(days_elapsed / days_in_month * 100, 1)

        # Status
        if pct >= 100:
            status = "achieved"
        elif pct >= pace_pct * 0.9:
            status = "on_track"
        elif pct >= pace_pct * 0.7:
            status = "behind"
        else:
            status = "at_risk"

        d["actual"] = actual
        d["pct"] = min(pct, 200)  # cap display at 200%
        d["pace_pct"] = pace_pct
        d["status"] = status
        d["days_elapsed"] = days_elapsed
        d["days_remaining"] = max(days_in_month - days_elapsed, 0)

        info = METRICS.get(d["metric"], {})
        d["label"] = goal_type_label(d["metric"])
        d["icon"] = info.get("icon", "🎯")
        d["unit"] = goal_type_unit(d["metric"])

        results.append(d)

    return results


def _get_actual(metric: str, period: str) -> float:
    """Get actual value for a metric in a period."""
    with db.conn() as c:
        if metric == "revenue":
            r = c.execute("""
                SELECT COALESCE(SUM(total_amount), 0) AS val FROM orders
                WHERE strftime('%%Y-%%m', order_date) = ?
            """, (period,)).fetchone()
            return r["val"]

        elif metric == "orders":
            r = c.execute("""
                SELECT COUNT(*) AS val FROM orders
                WHERE strftime('%%Y-%%m', order_date) = ?
            """, (period,)).fetchone()
            return r["val"]

        elif metric == "profit":
            r = c.execute("""
                SELECT COALESCE(SUM(oi.qty * (oi.unit_price - COALESCE(p.cost_price, 0))), 0) AS val
                FROM order_items oi
                JOIN orders o ON o.order_id = oi.order_id
                LEFT JOIN products p ON p.sku = oi.sku
                WHERE strftime('%%Y-%%m', o.order_date) = ?
            """, (period,)).fetchone()
            return r["val"]

        elif metric == "new_customers":
            r = c.execute("""
                SELECT COUNT(DISTINCT COALESCE(buyer_phone, buyer_name)) AS val
                FROM orders
                WHERE strftime('%%Y-%%m', order_date) = ?
            """, (period,)).fetchone()
            return r["val"]

        elif metric == "avg_order":
            r = c.execute("""
                SELECT AVG(total_amount) AS val FROM orders
                WHERE strftime('%%Y-%%m', order_date) = ?
            """, (period,)).fetchone()
            return r["val"] or 0

    return 0


def summary(period: str = "") -> dict:
    goals = goals_for_period(period)
    achieved = sum(1 for g in goals if g["status"] == "achieved")
    on_track = sum(1 for g in goals if g["status"] == "on_track")
    behind = sum(1 for g in goals if g["status"] == "behind")
    at_risk = sum(1 for g in goals if g["status"] == "at_risk")

    return {
        "total": len(goals),
        "achieved": achieved,
        "on_track": on_track,
        "behind": behind,
        "at_risk": at_risk,
    }
