"""Budget Tracker — set budgets per expense category, track overspend.

Thai sellers usually have no idea where money goes.
Set limits, see what's over, catch leaks before they drain profit."""
from __future__ import annotations

from datetime import datetime, date

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                monthly_limit REAL DEFAULT 0,
                alert_pct REAL DEFAULT 80,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


CATEGORIES = {
    "packaging":   {"label": "บรรจุภัณฑ์",     "icon": "📦"},
    "shipping":    {"label": "ค่าส่ง",          "icon": "🚚"},
    "ads":         {"label": "โฆษณา",          "icon": "📣"},
    "platform":    {"label": "ค่าแพลตฟอร์ม",    "icon": "🛒"},
    "salary":      {"label": "เงินเดือน/ค่าแรง", "icon": "👤"},
    "rent":        {"label": "ค่าเช่า",         "icon": "🏠"},
    "utilities":   {"label": "ค่าน้ำ/ไฟ/เน็ต",  "icon": "💡"},
    "supplies":    {"label": "วัสดุสิ้นเปลือง",   "icon": "🧴"},
    "tools":       {"label": "เครื่องมือ/ซอฟต์แวร์", "icon": "🔧"},
    "other":       {"label": "อื่นๆ",           "icon": "📋"},
}


def set_budget(category: str, monthly_limit: float, alert_pct: float = 80) -> int:
    with db.conn() as c:
        existing = c.execute(
            "SELECT id FROM budgets WHERE category=?", (category,)
        ).fetchone()
        if existing:
            c.execute(
                "UPDATE budgets SET monthly_limit=?, alert_pct=? WHERE id=?",
                (monthly_limit, alert_pct, existing["id"]),
            )
            return existing["id"]
        else:
            c.execute(
                "INSERT INTO budgets (category, monthly_limit, alert_pct) VALUES (?,?,?)",
                (category, monthly_limit, alert_pct),
            )
            return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def delete_budget(budget_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM budgets WHERE id=?", (budget_id,))


def all_budgets() -> list[dict]:
    with db.conn() as c:
        rows = c.execute("SELECT * FROM budgets ORDER BY category").fetchall()
    return [dict(r) for r in rows]


def budget_vs_actual(month: str = "") -> list[dict]:
    """Compare budgets against actual spending for a month (YYYY-MM)."""
    if not month:
        month = date.today().strftime("%Y-%m")

    budgets = all_budgets()
    budget_map = {b["category"]: b for b in budgets}

    # Get actual expenses for the month
    with db.conn() as c:
        rows = c.execute("""
            SELECT category, COALESCE(SUM(amount), 0) AS spent
            FROM expenses
            WHERE strftime('%%Y-%%m', expense_date) = ?
            GROUP BY category
        """, (month,)).fetchall()

    actual_map = {r["category"]: r["spent"] for r in rows}

    # Merge
    all_cats = set(list(budget_map.keys()) + list(actual_map.keys()))
    result = []
    for cat in sorted(all_cats):
        budget = budget_map.get(cat, {})
        limit_ = budget.get("monthly_limit", 0)
        spent = actual_map.get(cat, 0)
        alert_pct = budget.get("alert_pct", 80)
        used_pct = (spent / limit_ * 100) if limit_ > 0 else 0
        remaining = limit_ - spent if limit_ > 0 else 0

        # Status
        if limit_ <= 0:
            status = "no_budget"
        elif used_pct >= 100:
            status = "over"
        elif used_pct >= alert_pct:
            status = "warning"
        else:
            status = "ok"

        cat_info = CATEGORIES.get(cat, {"label": cat, "icon": "📋"})

        result.append({
            "category": cat,
            "label": cat_info["label"],
            "icon": cat_info["icon"],
            "budget": limit_,
            "spent": spent,
            "remaining": remaining,
            "used_pct": round(used_pct, 1),
            "status": status,
        })

    return sorted(result, key=lambda x: x["used_pct"], reverse=True)


def summary(month: str = "") -> dict:
    """Summary of budget health."""
    items = budget_vs_actual(month)
    total_budget = sum(i["budget"] for i in items)
    total_spent = sum(i["spent"] for i in items)
    over_count = sum(1 for i in items if i["status"] == "over")
    warn_count = sum(1 for i in items if i["status"] == "warning")
    ok_count = sum(1 for i in items if i["status"] == "ok")

    return {
        "total_budget": total_budget,
        "total_spent": total_spent,
        "total_remaining": total_budget - total_spent,
        "used_pct": round(total_spent / total_budget * 100, 1) if total_budget > 0 else 0,
        "over": over_count,
        "warning": warn_count,
        "ok": ok_count,
        "categories": len(items),
    }
