"""Simple expense tracker — know your REAL profit.

Thai home sellers track revenue but rarely track expenses. The result:
"ขายเยอะแต่ไม่เหลือเงิน". This module gives a clear picture of where
money goes: shipping, packaging, ads, platform fees, supplies.

Pairs with Dashboard (revenue) to show TRUE net profit."""
from __future__ import annotations

from datetime import datetime, timedelta

import db


CATEGORIES = [
    "shipping",     # ค่าส่ง
    "packaging",    # ค่าแพ็ค กล่อง ซอง
    "advertising",  # ค่าโฆษณา Shopee Ads, FB Ads
    "platform_fee", # ค่าธรรมเนียมแพลตฟอร์ม
    "supplies",     # อุปกรณ์ ป้าย สติกเกอร์
    "cogs",         # ต้นทุนสินค้า (cost of goods sold)
    "refund",       # คืนเงินลูกค้า
    "other",        # อื่นๆ
]

CATEGORY_ICONS = {
    "shipping":     "🚚",
    "packaging":    "📦",
    "advertising":  "📢",
    "platform_fee": "🏪",
    "supplies":     "🏷",
    "cogs":         "💰",
    "refund":       "↩",
    "other":        "📝",
}


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                category    TEXT NOT NULL DEFAULT 'other',
                amount      REAL NOT NULL DEFAULT 0,
                note        TEXT DEFAULT '',
                platform    TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)


def add(*, date: str, category: str, amount: float,
        note: str = "", platform: str = "") -> int:
    cat = category if category in CATEGORIES else "other"
    with db.conn() as c:
        c.execute(
            "INSERT INTO expenses (date, category, amount, note, platform) VALUES (?,?,?,?,?)",
            (date, cat, abs(amount), note.strip(), platform.strip()),
        )
        return c.lastrowid


def update(expense_id: int, **fields):
    allowed = {"date", "category", "amount", "note", "platform"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return
    if "category" in sets and sets["category"] not in CATEGORIES:
        sets["category"] = "other"
    if "amount" in sets:
        sets["amount"] = abs(sets["amount"])
    clause = ", ".join(f"{k} = ?" for k in sets)
    with db.conn() as c:
        c.execute(f"UPDATE expenses SET {clause} WHERE id = ?",
                  (*sets.values(), expense_id))


def delete(expense_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def all_expenses(*, month: str = "", limit: int = 500) -> list[dict]:
    with db.conn() as c:
        if month:
            rows = c.execute(
                "SELECT * FROM expenses WHERE date LIKE ? ORDER BY date DESC LIMIT ?",
                (f"{month}%", limit),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM expenses ORDER BY date DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]


def monthly_summary(month: str) -> dict:
    with db.conn() as c:
        rows = c.execute(
            "SELECT category, SUM(amount) as total FROM expenses "
            "WHERE date LIKE ? GROUP BY category ORDER BY total DESC",
            (f"{month}%",),
        ).fetchall()
        grand = c.execute(
            "SELECT SUM(amount) FROM expenses WHERE date LIKE ?",
            (f"{month}%",),
        ).fetchone()[0] or 0
    breakdown = {r["category"]: r["total"] for r in rows}
    return {"total": grand, "breakdown": breakdown}


def monthly_totals(months: int = 6) -> list[dict]:
    out = []
    now = datetime.now()
    for i in range(months):
        d = now - timedelta(days=30 * i)
        m = d.strftime("%Y-%m")
        s = monthly_summary(m)
        out.append({"month": m, "total": s["total"], **s["breakdown"]})
    return list(reversed(out))


def stats() -> dict:
    now = datetime.now()
    this_month = now.strftime("%Y-%m")
    last_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    with db.conn() as c:
        this_total = c.execute(
            "SELECT SUM(amount) FROM expenses WHERE date LIKE ?",
            (f"{this_month}%",),
        ).fetchone()[0] or 0
        last_total = c.execute(
            "SELECT SUM(amount) FROM expenses WHERE date LIKE ?",
            (f"{last_month}%",),
        ).fetchone()[0] or 0
        all_total = c.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0
        count = c.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]

    return {
        "this_month": this_total,
        "last_month": last_total,
        "all_time": all_total,
        "count": count,
        "change_pct": round((this_total - last_total) / last_total * 100, 1) if last_total else 0,
    }
