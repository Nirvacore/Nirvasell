"""Goal Tracker — daily/monthly/quarterly sales and profit targets."""
from __future__ import annotations
import db

GOAL_TYPES = {
    "revenue":     {"label": "ยอดขาย", "icon": "💰", "unit": "฿"},
    "orders":      {"label": "จำนวนออเดอร์", "icon": "📦", "unit": "ออเดอร์"},
    "profit":      {"label": "กำไรสุทธิ", "icon": "📈", "unit": "฿"},
    "new_customers":{"label": "ลูกค้าใหม่", "icon": "👥", "unit": "คน"},
    "reviews":     {"label": "รีวิวใหม่", "icon": "⭐", "unit": "รีวิว"},
}

PERIODS = {
    "daily":     "รายวัน",
    "weekly":    "รายสัปดาห์",
    "monthly":   "รายเดือน",
    "quarterly": "รายไตรมาส",
}


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_type   TEXT NOT NULL,
                period      TEXT NOT NULL DEFAULT 'monthly',
                period_key  TEXT NOT NULL,
                target      REAL NOT NULL,
                notes       TEXT,
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


def set_goal(goal_type: str, period: str, target: float,
             period_key: str = "", notes: str = "") -> int:
    if not period_key:
        from datetime import datetime
        now = datetime.now()
        if period == "daily":
            period_key = now.strftime("%Y-%m-%d")
        elif period == "weekly":
            period_key = now.strftime("%Y-W%W")
        elif period == "monthly":
            period_key = now.strftime("%Y-%m")
        elif period == "quarterly":
            q = (now.month - 1) // 3 + 1
            period_key = str(now.year) + "-Q" + str(q)
        else:
            period_key = now.strftime("%Y-%m")
    with db.conn() as c:
        c.execute(
            "DELETE FROM goals WHERE goal_type=? AND period=? AND period_key=?",
            (goal_type, period, period_key),
        )
        cur = c.execute(
            "INSERT INTO goals (goal_type,period,period_key,target,notes) "
            "VALUES (?,?,?,?,?)",
            (goal_type, period, period_key, target, notes),
        )
        return cur.lastrowid


def _actual_revenue(period_key: str, period: str) -> float:
    with db.conn() as c:
        if period == "daily":
            row = c.execute(
                "SELECT COALESCE(SUM(total_price),0) v FROM orders "
                "WHERE date(order_date)=? AND status NOT IN ('cancelled','returned')",
                (period_key,),
            ).fetchone()
        elif period == "monthly":
            row = c.execute(
                "SELECT COALESCE(SUM(total_price),0) v FROM orders "
                "WHERE strftime('%Y-%m',order_date)=? "
                "  AND status NOT IN ('cancelled','returned')",
                (period_key,),
            ).fetchone()
        else:
            row = c.execute(
                "SELECT COALESCE(SUM(total_price),0) v FROM orders "
                "WHERE status NOT IN ('cancelled','returned')",
            ).fetchone()
        return row["v"] if row else 0


def _actual_orders(period_key: str, period: str) -> int:
    with db.conn() as c:
        if period == "daily":
            row = c.execute(
                "SELECT COUNT(*) v FROM orders "
                "WHERE date(order_date)=? AND status NOT IN ('cancelled','returned')",
                (period_key,),
            ).fetchone()
        elif period == "monthly":
            row = c.execute(
                "SELECT COUNT(*) v FROM orders "
                "WHERE strftime('%Y-%m',order_date)=? "
                "  AND status NOT IN ('cancelled','returned')",
                (period_key,),
            ).fetchone()
        else:
            row = c.execute("SELECT COUNT(*) v FROM orders "
                            "WHERE status NOT IN ('cancelled','returned')").fetchone()
        return row["v"] if row else 0


def current_goals() -> list[dict]:
    from datetime import datetime
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    this_month = now.strftime("%Y-%m")
    this_week = now.strftime("%Y-W%W")
    q = (now.month - 1) // 3 + 1
    this_quarter = str(now.year) + "-Q" + str(q)

    period_keys = {
        "daily": today,
        "weekly": this_week,
        "monthly": this_month,
        "quarterly": this_quarter,
    }

    with db.conn() as c:
        goals = []
        for period, key in period_keys.items():
            rows = c.execute(
                "SELECT * FROM goals WHERE period=? AND period_key=? "
                "ORDER BY created_at DESC",
                (period, key),
            ).fetchall()
            for r in rows:
                d = dict(r)
                goal_info = GOAL_TYPES.get(r["goal_type"],
                                           GOAL_TYPES["revenue"])
                d["goal_label"] = goal_info["label"]
                d["goal_icon"] = goal_info["icon"]
                d["unit"] = goal_info["unit"]
                d["period_label"] = PERIODS.get(period, period)
                # compute actual
                if r["goal_type"] == "revenue":
                    d["actual"] = _actual_revenue(key, period)
                elif r["goal_type"] == "orders":
                    d["actual"] = float(_actual_orders(key, period))
                else:
                    d["actual"] = 0.0
                d["pct"] = min(
                    round(d["actual"] / d["target"] * 100, 1)
                    if d["target"] > 0 else 0,
                    100,
                )
                d["on_track"] = d["pct"] >= 80
                goals.append(d)
    return goals


def history(limit: int = 20) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM goals ORDER BY period_key DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def stats() -> dict:
    goals = current_goals()
    on_track = sum(1 for g in goals if g["on_track"])
    return {
        "total_active": len(goals),
        "on_track": on_track,
        "off_track": len(goals) - on_track,
    }
