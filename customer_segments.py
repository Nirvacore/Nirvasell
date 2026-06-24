"""Customer Segments — tag-based grouping + RFM-lite scoring."""
from __future__ import annotations
import db

DEFAULT_TAGS = [
    "VIP", "wholesale", "reseller", "returning", "new",
    "problematic", "local", "export", "dormant",
]

RFM_SEGMENTS = {
    "champion":  {"icon": "🏆", "color": "#4d6c5c"},
    "loyal":     {"icon": "💎", "color": "#4a7ab5"},
    "at_risk":   {"icon": "⚠️", "color": "#c5963d"},
    "new":       {"icon": "🌱", "color": "#7ac58a"},
    "promising": {"icon": "✨", "color": "#9a7dc5"},
    "dormant":   {"icon": "💤", "color": "#9a9485"},
}


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS customer_tags (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_key TEXT NOT NULL,
                tag         TEXT NOT NULL,
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(customer_key, tag)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS customer_notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_key TEXT NOT NULL,
                note        TEXT NOT NULL,
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


def _rfm_score(recency_days: int, frequency: int, monetary: float) -> str:
    """Classify customer into RFM segment."""
    r = 1 if recency_days <= 30 else (2 if recency_days <= 90 else 3)
    f = 3 if frequency >= 5 else (2 if frequency >= 2 else 1)
    m = 3 if monetary >= 2000 else (2 if monetary >= 500 else 1)
    score = r * 3 + f * 2 + m
    if r == 1 and f >= 2 and score >= 10:
        return "champion"
    if f >= 3:
        return "loyal"
    if r == 1 and f == 1:
        return "new"
    if r == 1:
        return "promising"
    if r == 2 and f >= 2:
        return "at_risk"
    return "dormant"


def all_customers_rfm(limit: int = 200) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT "
            "  buyer_name customer_key, "
            "  buyer_phone phone, "
            "  COUNT(*) frequency, "
            "  SUM(total_price) monetary, "
            "  CAST(julianday('now','localtime') - julianday(MAX(order_date)) AS INTEGER) recency_days "
            "FROM orders "
            "WHERE buyer_name IS NOT NULL AND buyer_name!='' "
            "  AND status NOT IN ('cancelled','returned') "
            "GROUP BY buyer_name "
            "ORDER BY monetary DESC LIMIT ?",
            (limit,),
        ).fetchall()
        result = []
        for r in rows:
            seg = _rfm_score(r["recency_days"] or 999,
                             r["frequency"], r["monetary"] or 0)
            seg_info = RFM_SEGMENTS.get(seg, RFM_SEGMENTS["dormant"])
            tags = [
                row["tag"] for row in c.execute(
                    "SELECT tag FROM customer_tags WHERE customer_key=?",
                    (r["customer_key"],),
                ).fetchall()
            ]
            d = dict(r)
            d["segment"] = seg
            d["segment_info"] = seg_info
            d["tags"] = tags
            result.append(d)
        return result


def add_tag(customer_key: str, tag: str) -> None:
    with db.conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO customer_tags (customer_key,tag) VALUES (?,?)",
            (customer_key, tag),
        )


def remove_tag(customer_key: str, tag: str) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM customer_tags WHERE customer_key=? AND tag=?",
                  (customer_key, tag))


def add_note(customer_key: str, note: str) -> None:
    with db.conn() as c:
        c.execute(
            "INSERT INTO customer_notes (customer_key,note) VALUES (?,?)",
            (customer_key, note),
        )


def get_notes(customer_key: str) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM customer_notes WHERE customer_key=? "
            "ORDER BY created_at DESC LIMIT 10",
            (customer_key,),
        ).fetchall()
        return [dict(r) for r in rows]


def by_segment(segment: str) -> list[dict]:
    return [c for c in all_customers_rfm(500) if c["segment"] == segment]


def by_tag(tag: str) -> list[dict]:
    with db.conn() as c:
        keys = [r["customer_key"] for r in c.execute(
            "SELECT customer_key FROM customer_tags WHERE tag=?", (tag,)
        ).fetchall()]
    return [c for c in all_customers_rfm(500) if c["customer_key"] in keys]


def stats() -> dict:
    customers = all_customers_rfm(500)
    seg_counts = {}
    for c in customers:
        seg_counts[c["segment"]] = seg_counts.get(c["segment"], 0) + 1
    return {
        "total": len(customers),
        "by_segment": seg_counts,
        "champions": seg_counts.get("champion", 0),
        "at_risk": seg_counts.get("at_risk", 0),
    }
