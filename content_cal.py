"""Seller content planning calendar (B0 page).

Separate from content_calendar.py (content_posts for G2/e pages).
Uses the content_calendar table — also referenced by alerts.py."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import db

CONTENT_TYPES = {
    "post": {"icon": "📝"},
    "live": {"icon": "🔴"},
    "promo": {"icon": "🏷️"},
    "reel": {"icon": "🎬"},
    "story": {"icon": "📱"},
    "flash_sale": {"icon": "⚡"},
}

PLATFORMS = [
    "facebook", "instagram", "tiktok", "line_oa",
    "shopee", "lazada", "youtube",
]

STATUSES = {
    "planned": {"icon": "📋"},
    "in_progress": {"icon": "🔄"},
    "done": {"icon": "✅"},
    "cancelled": {"icon": "❌"},
}


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS content_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content_type TEXT DEFAULT 'post',
                platform TEXT DEFAULT '',
                scheduled_date TEXT,
                scheduled_time TEXT DEFAULT '',
                description TEXT DEFAULT '',
                target_revenue REAL DEFAULT 0,
                actual_revenue REAL DEFAULT 0,
                status TEXT DEFAULT 'planned',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


def add(
    *,
    title: str,
    content_type: str = "post",
    platform: str = "",
    scheduled_date: str = "",
    scheduled_time: str = "",
    description: str = "",
    target_revenue: float = 0,
) -> int:
    with db.conn() as c:
        c.execute(
            "INSERT INTO content_calendar "
            "(title, content_type, platform, scheduled_date, scheduled_time, "
            "description, target_revenue) VALUES (?,?,?,?,?,?,?)",
            (
                title, content_type, platform, scheduled_date,
                scheduled_time, description, target_revenue,
            ),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_status(item_id: int, status: str):
    with db.conn() as c:
        c.execute(
            "UPDATE content_calendar SET status=? WHERE id=?",
            (status, item_id),
        )


def upcoming(days: int = 7) -> list[dict]:
    today = date.today().isoformat()
    end = (date.today() + timedelta(days=days)).isoformat()
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM content_calendar "
            "WHERE scheduled_date >= ? AND scheduled_date <= ? "
            "AND status IN ('planned','in_progress') "
            "ORDER BY scheduled_date, scheduled_time",
            (today, end),
        ).fetchall()
    return [dict(r) for r in rows]


def week_items(anchor_date: str) -> dict[str, list[dict]]:
    """Return {YYYY-MM-DD: [items]} for the Mon–Sun week containing anchor_date."""
    anchor = datetime.strptime(anchor_date, "%Y-%m-%d").date()
    start = anchor - timedelta(days=anchor.weekday())
    result: dict[str, list[dict]] = {}
    for i in range(7):
        d_str = (start + timedelta(days=i)).isoformat()
        with db.conn() as c:
            rows = c.execute(
                "SELECT * FROM content_calendar WHERE scheduled_date = ? "
                "ORDER BY scheduled_time",
                (d_str,),
            ).fetchall()
        result[d_str] = [dict(r) for r in rows]
    return result


def stats() -> dict:
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    with db.conn() as c:
        total = c.execute(
            "SELECT COUNT(*) FROM content_calendar"
        ).fetchone()[0]
        this_month = c.execute(
            "SELECT COUNT(*) FROM content_calendar "
            "WHERE scheduled_date >= ?",
            (month_start,),
        ).fetchone()[0]
        done = c.execute(
            "SELECT COUNT(*) FROM content_calendar WHERE status='done'"
        ).fetchone()[0]
        total_revenue = c.execute(
            "SELECT COALESCE(SUM(actual_revenue), 0) FROM content_calendar "
            "WHERE status='done'"
        ).fetchone()[0]
    return {
        "total": total,
        "this_month": this_month,
        "done": done,
        "total_revenue": float(total_revenue or 0),
    }
