"""Review Tracker — manually log product reviews from all platforms.

Track ratings, common complaints, and response times.
No API needed — enter manually from Shopee/Lazada/TikTok/Facebook."""
from __future__ import annotations
from datetime import datetime
import db


PLATFORMS = ["shopee", "lazada", "tiktok", "facebook", "google", "other"]
SENTIMENTS = {
    5: {"icon": "⭐⭐⭐⭐⭐", "label": "ดีมาก", "color": "#4d6c5c"},
    4: {"icon": "⭐⭐⭐⭐", "label": "ดี", "color": "#4a7ab5"},
    3: {"icon": "⭐⭐⭐", "label": "พอใช้", "color": "#c5963d"},
    2: {"icon": "⭐⭐", "label": "ไม่ดี", "color": "#c54c4c"},
    1: {"icon": "⭐", "label": "แย่มาก", "color": "#8b1a1a"},
}


def init():
    with db.conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT,
                platform TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                reviewer_name TEXT,
                review_text TEXT,
                review_date TEXT DEFAULT CURRENT_DATE,
                responded INTEGER DEFAULT 0,
                response_text TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_reviews_sku
                ON reviews(sku);
            CREATE INDEX IF NOT EXISTS idx_reviews_platform
                ON reviews(platform);
            CREATE INDEX IF NOT EXISTS idx_reviews_rating
                ON reviews(rating);
        """)


def add(platform: str, rating: int, sku: str = None,
        reviewer: str = "", text: str = "",
        review_date: str = None, tags: list = None) -> int:
    date = review_date or datetime.now().strftime("%Y-%m-%d")
    with db.conn() as c:
        c.execute("""
            INSERT INTO reviews
                (sku, platform, rating, reviewer_name, review_text,
                 review_date, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (sku, platform, rating, reviewer, text, date,
              ",".join(tags or [])))
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def add_response(review_id: int, response: str) -> None:
    with db.conn() as c:
        c.execute("""
            UPDATE reviews SET responded = 1, response_text = ?
            WHERE id = ?
        """, (response, review_id))


def delete(review_id: int) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM reviews WHERE id = ?", (review_id,))


def all_reviews(sku: str = None, platform: str = None,
                min_rating: int = 1, max_rating: int = 5,
                limit: int = 100) -> list:
    filters = ["rating BETWEEN ? AND ?"]
    params = [min_rating, max_rating]

    if sku:
        filters.append("sku = ?")
        params.append(sku)
    if platform and platform != "all":
        filters.append("platform = ?")
        params.append(platform)

    where = " AND ".join(filters)
    params.append(limit)

    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM reviews WHERE " + where +
            " ORDER BY review_date DESC LIMIT ?",
            params
        ).fetchall()

    result = []
    for r in rows:
        item = dict(r)
        item["sentiment"] = SENTIMENTS.get(r["rating"], SENTIMENTS[3])
        item["tags_list"] = [t.strip() for t in (r["tags"] or "").split(",") if t.strip()]
        result.append(item)
    return result


def unanswered(limit: int = 20) -> list:
    with db.conn() as c:
        rows = c.execute("""
            SELECT * FROM reviews
            WHERE responded = 0 AND rating <= 3
            ORDER BY rating ASC, review_date DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def sku_summary(sku: str) -> dict:
    with db.conn() as c:
        rows = c.execute("""
            SELECT rating, COUNT(*) AS cnt
            FROM reviews WHERE sku = ?
            GROUP BY rating
        """, (sku,)).fetchall()
        avg = c.execute(
            "SELECT AVG(rating) FROM reviews WHERE sku = ?", (sku,)
        ).fetchone()[0]

    dist = {r["rating"]: r["cnt"] for r in rows}
    total = sum(dist.values())
    return {
        "sku": sku,
        "total_reviews": total,
        "avg_rating": round(avg or 0, 2),
        "distribution": {i: dist.get(i, 0) for i in range(1, 6)},
    }


def platform_summary() -> list:
    with db.conn() as c:
        rows = c.execute("""
            SELECT platform,
                   COUNT(*) AS total,
                   AVG(rating) AS avg_rating,
                   SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) AS positive,
                   SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) AS negative,
                   SUM(CASE WHEN responded = 0 AND rating <= 3 THEN 1 ELSE 0 END) AS unanswered
            FROM reviews
            GROUP BY platform
            ORDER BY total DESC
        """).fetchall()
    return [dict(r) for r in rows]


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        avg = c.execute("SELECT AVG(rating) FROM reviews").fetchone()[0]
        five_star = c.execute(
            "SELECT COUNT(*) FROM reviews WHERE rating = 5"
        ).fetchone()[0]
        unanswered_neg = c.execute("""
            SELECT COUNT(*) FROM reviews WHERE responded = 0 AND rating <= 3
        """).fetchone()[0]
    return {
        "total": total,
        "avg_rating": round(avg or 0, 2),
        "five_star": five_star,
        "unanswered_negative": unanswered_neg,
        "five_star_pct": round(five_star / total * 100, 0) if total > 0 else 0,
    }
