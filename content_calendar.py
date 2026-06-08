"""Content Calendar — plan what to post, where, and when.

Consistent posting = more visibility = more sales. This module helps
sellers plan social media posts across Facebook, Instagram, TikTok,
LINE OA, and track which content type performs best."""
from __future__ import annotations

from datetime import datetime, date, timedelta

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS content_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                platform TEXT DEFAULT '',
                post_type TEXT DEFAULT 'product',
                scheduled_date TEXT,
                scheduled_time TEXT DEFAULT '10:00',
                status TEXT DEFAULT 'draft',
                product_sku TEXT DEFAULT '',
                caption TEXT DEFAULT '',
                hashtags TEXT DEFAULT '',
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


POST_PLATFORMS = ["facebook", "instagram", "tiktok", "line_oa", "twitter", "youtube", "other"]

PLATFORM_ICONS = {
    "facebook": "📘", "instagram": "📸", "tiktok": "🎵",
    "line_oa": "💚", "twitter": "🐦", "youtube": "📹", "other": "📣",
}

POST_TYPES = ["product", "promo", "review", "behind_scenes", "tips", "live", "repost", "story"]

TYPE_ICONS = {
    "product": "📦", "promo": "🏷️", "review": "⭐", "behind_scenes": "🎬",
    "tips": "💡", "live": "🔴", "repost": "🔄", "story": "📱",
}

STATUSES = ["draft", "scheduled", "posted", "cancelled"]


def add(title: str, platform: str, post_type: str = "product",
        scheduled_date: str = "", scheduled_time: str = "10:00",
        product_sku: str = "", caption: str = "", hashtags: str = "",
        note: str = "") -> int:
    with db.conn() as c:
        c.execute(
            "INSERT INTO content_posts "
            "(title, platform, post_type, scheduled_date, scheduled_time, "
            "product_sku, caption, hashtags, note) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (title, platform, post_type, scheduled_date, scheduled_time,
             product_sku, caption, hashtags, note),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def update(post_id: int, **kwargs):
    sets = []
    vals = []
    for k in ("title", "platform", "post_type", "scheduled_date",
              "scheduled_time", "status", "product_sku", "caption",
              "hashtags", "note"):
        if k in kwargs:
            sets.append(k + "=?")
            vals.append(kwargs[k])
    if not sets:
        return
    vals.append(post_id)
    with db.conn() as c:
        c.execute(
            "UPDATE content_posts SET " + ",".join(sets) + " WHERE id=?",
            vals,
        )


def delete(post_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM content_posts WHERE id=?", (post_id,))


def get(post_id: int) -> dict | None:
    with db.conn() as c:
        r = c.execute(
            "SELECT * FROM content_posts WHERE id=?", (post_id,)
        ).fetchone()
    return dict(r) if r else None


def all_posts(status: str | None = None) -> list[dict]:
    with db.conn() as c:
        if status:
            rows = c.execute(
                "SELECT * FROM content_posts WHERE status=? "
                "ORDER BY scheduled_date, scheduled_time",
                (status,),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM content_posts "
                "ORDER BY scheduled_date DESC, scheduled_time"
            ).fetchall()
    return [dict(r) for r in rows]


def upcoming(days: int = 7) -> list[dict]:
    """Posts scheduled in the next N days."""
    today = date.today().isoformat()
    end = (date.today() + timedelta(days=days)).isoformat()
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM content_posts "
            "WHERE scheduled_date >= ? AND scheduled_date <= ? "
            "AND status IN ('draft','scheduled') "
            "ORDER BY scheduled_date, scheduled_time",
            (today, end),
        ).fetchall()
    return [dict(r) for r in rows]


def today_posts() -> list[dict]:
    today = date.today().isoformat()
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM content_posts WHERE scheduled_date = ? "
            "ORDER BY scheduled_time",
            (today,),
        ).fetchall()
    return [dict(r) for r in rows]


def weekly_view(start_date: date | None = None) -> dict[str, list[dict]]:
    """Returns {date_str: [posts]} for a 7-day window."""
    if not start_date:
        # Start from Monday of current week
        today = date.today()
        start_date = today - timedelta(days=today.weekday())

    result = {}
    for i in range(7):
        d = start_date + timedelta(days=i)
        d_str = d.isoformat()
        with db.conn() as c:
            rows = c.execute(
                "SELECT * FROM content_posts WHERE scheduled_date = ? "
                "ORDER BY scheduled_time",
                (d_str,),
            ).fetchall()
        result[d_str] = [dict(r) for r in rows]
    return result


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM content_posts").fetchone()[0]
        draft = c.execute(
            "SELECT COUNT(*) FROM content_posts WHERE status='draft'"
        ).fetchone()[0]
        scheduled = c.execute(
            "SELECT COUNT(*) FROM content_posts WHERE status='scheduled'"
        ).fetchone()[0]
        posted = c.execute(
            "SELECT COUNT(*) FROM content_posts WHERE status='posted'"
        ).fetchone()[0]
    return {
        "total": total,
        "draft": draft,
        "scheduled": scheduled,
        "posted": posted,
    }


# ---- Best posting times from order data ------------------------------------

def suggest_post_times() -> list[dict]:
    """Suggest best times to post based on peak order hours."""
    try:
        import order_analytics as oa
        peaks = oa.peak_hours(5)
        suggestions = []
        for p in peaks:
            h = p["hour"]
            # Post 1-2 hours before peak buying time
            post_hour = max(0, h - 1)
            suggestions.append({
                "post_time": "{:02d}:00".format(post_hour),
                "peak_buy_time": "{:02d}:00".format(h),
                "revenue": p.get("revenue", 0),
            })
        return suggestions
    except Exception:
        return []
