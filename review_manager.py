"""Review Manager — track product reviews across platforms."""
from __future__ import annotations
import db

STATUSES = {
    "new":       {"label": "ใหม่", "icon": "🔵", "color": "#4a7ab5"},
    "replied":   {"label": "ตอบแล้ว", "icon": "✅", "color": "#4d6c5c"},
    "escalated": {"label": "รุนแรง", "icon": "🔴", "color": "#c54c4c"},
    "noted":     {"label": "จดไว้แล้ว", "icon": "📌", "color": "#9a9485"},
}

RATINGS = [1, 2, 3, 4, 5]


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                platform    TEXT DEFAULT '',
                sku         TEXT DEFAULT '',
                product_name TEXT DEFAULT '',
                rating      INTEGER DEFAULT 5,
                review_text TEXT DEFAULT '',
                reviewer    TEXT DEFAULT '',
                status      TEXT DEFAULT 'new',
                reply_text  TEXT DEFAULT '',
                review_date TEXT DEFAULT (date('now','localtime')),
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


def add(platform: str, sku: str, rating: int, review_text: str = "",
        reviewer: str = "", product_name: str = "",
        review_date: str = "") -> int:
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO reviews (platform,sku,product_name,rating,"
            "review_text,reviewer,review_date) VALUES (?,?,?,?,?,?,?)",
            (platform, sku, product_name, rating, review_text,
             reviewer, review_date or ""),
        )
        return cur.lastrowid


def reply(review_id: int, reply_text: str) -> None:
    with db.conn() as c:
        c.execute(
            "UPDATE reviews SET reply_text=?,status='replied' WHERE id=?",
            (reply_text, review_id),
        )


def set_status(review_id: int, status: str) -> None:
    with db.conn() as c:
        c.execute("UPDATE reviews SET status=? WHERE id=?", (status, review_id))


def delete(review_id: int) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM reviews WHERE id=?", (review_id,))


def all_reviews(platform: str = None, rating: int = None,
                status: str = None, limit: int = 100) -> list[dict]:
    with db.conn() as c:
        conditions = []
        params = []
        if platform:
            conditions.append("platform=?")
            params.append(platform)
        if rating:
            conditions.append("rating=?")
            params.append(rating)
        if status:
            conditions.append("status=?")
            params.append(status)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = c.execute(
            "SELECT * FROM reviews " + where +
            " ORDER BY created_at DESC LIMIT ?",
            params + [limit],
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["status_info"] = STATUSES.get(r["status"], STATUSES["new"])
            d["stars"] = "⭐" * r["rating"]
            result.append(d)
        return result


def by_sku(limit: int = 20) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT sku, product_name, COUNT(*) total, "
            "AVG(rating) avg_rating, "
            "SUM(CASE WHEN rating<=2 THEN 1 ELSE 0 END) negatives "
            "FROM reviews GROUP BY sku "
            "ORDER BY negatives DESC, total DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def by_platform() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT platform, COUNT(*) total, "
            "AVG(rating) avg_rating, "
            "SUM(CASE WHEN rating<=2 THEN 1 ELSE 0 END) negatives, "
            "SUM(CASE WHEN status='new' THEN 1 ELSE 0 END) unanswered "
            "FROM reviews GROUP BY platform ORDER BY total DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        unanswered = c.execute(
            "SELECT COUNT(*) FROM reviews WHERE status='new'"
        ).fetchone()[0]
        avg_row = c.execute(
            "SELECT AVG(rating) FROM reviews"
        ).fetchone()
        avg_rating = round(avg_row[0] or 0, 2)
        negative = c.execute(
            "SELECT COUNT(*) FROM reviews WHERE rating<=2"
        ).fetchone()[0]
    return {
        "total": total,
        "unanswered": unanswered,
        "avg_rating": avg_rating,
        "negative": negative,
    }
