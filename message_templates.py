"""Quick-reply message templates for FB / Line / IG / TikTok."""
from __future__ import annotations
import db

CATEGORIES = {
    "greet":        {"icon": "👋"},
    "order_confirm":{"icon": "✅"},
    "tracking":     {"icon": "📦"},
    "payment":      {"icon": "💳"},
    "promotion":    {"icon": "🎉"},
    "complaint":    {"icon": "🙏"},
    "review_req":   {"icon": "⭐"},
    "custom":       {"icon": "✏️"},
}

PLATFORMS = ["facebook", "line", "instagram", "tiktok", "shopee", "lazada", "all"]

DEFAULT_TEMPLATES = [
    ("greet", "ทักทายลูกค้าใหม่",
     "สวัสดีค่ะ ขอบคุณที่สนใจสินค้าของเรานะคะ 🙏 มีอะไรให้ช่วยได้เลยค่ะ",
     "all"),
    ("order_confirm", "ยืนยันออเดอร์",
     "ขอบคุณที่สั่งสินค้านะคะ 🎉 ออเดอร์ของคุณ #{order_id} ได้รับการยืนยันแล้วค่ะ "
     "จะจัดส่งภายใน 1-2 วันทำการค่ะ",
     "all"),
    ("tracking", "แจ้งเลข Tracking",
     "สินค้าของคุณจัดส่งแล้วนะคะ 📦 เลข Tracking: {tracking} "
     "ตรวจสอบสถานะได้ที่เว็บไซต์ขนส่งเลยค่ะ",
     "all"),
    ("review_req", "ขอรีวิว",
     "ขอบคุณที่เลือกซื้อสินค้าจากเรานะคะ 💕 รบกวนรีวิวให้เราหน่อยได้ไหมคะ "
     "จะเป็นกำลังใจมากๆ เลยค่ะ ⭐",
     "all"),
    ("complaint", "ขอโทษ + แก้ไข",
     "ขอโทษเป็นอย่างยิ่งนะคะ 🙏 เราจะรีบแก้ไขให้ค่ะ "
     "รบกวนส่งรูปปัญหาให้เราทางนี้ได้เลยค่ะ",
     "all"),
]


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS message_templates (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category    TEXT NOT NULL DEFAULT 'custom',
                title       TEXT NOT NULL,
                content     TEXT NOT NULL,
                platforms   TEXT DEFAULT 'all',
                notes       TEXT,
                use_count   INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        row = c.execute("SELECT COUNT(*) FROM message_templates").fetchone()
        if row[0] == 0:
            for cat, title, content, platforms in DEFAULT_TEMPLATES:
                c.execute(
                    "INSERT INTO message_templates (category,title,content,platforms) "
                    "VALUES (?,?,?,?)",
                    (cat, title, content, platforms),
                )


def add(category: str, title: str, content: str,
        platforms: str = "all", notes: str = "") -> int:
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO message_templates (category,title,content,platforms,notes) "
            "VALUES (?,?,?,?,?)",
            (category, title, content, platforms, notes),
        )
        return cur.lastrowid


def update(template_id: int, title: str = None, content: str = None,
           category: str = None, platforms: str = None) -> None:
    with db.conn() as c:
        if title is not None:
            c.execute("UPDATE message_templates SET title=? WHERE id=?",
                      (title, template_id))
        if content is not None:
            c.execute("UPDATE message_templates SET content=? WHERE id=?",
                      (content, template_id))
        if category is not None:
            c.execute("UPDATE message_templates SET category=? WHERE id=?",
                      (category, template_id))
        if platforms is not None:
            c.execute("UPDATE message_templates SET platforms=? WHERE id=?",
                      (platforms, template_id))


def delete(template_id: int) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM message_templates WHERE id=?", (template_id,))


def use(template_id: int) -> str:
    with db.conn() as c:
        c.execute("UPDATE message_templates SET use_count=use_count+1 WHERE id=?",
                  (template_id,))
        row = c.execute("SELECT content FROM message_templates WHERE id=?",
                        (template_id,)).fetchone()
        return row["content"] if row else ""


def all_templates(category: str = None, platform: str = None) -> list[dict]:
    with db.conn() as c:
        query = "SELECT * FROM message_templates"
        params = []
        conditions = []
        if category:
            conditions.append("category=?")
            params.append(category)
        if platform and platform != "all":
            conditions.append("(platforms='all' OR platforms LIKE ?)")
            params.append("%" + platform + "%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY use_count DESC, id DESC"
        rows = c.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["category_info"] = CATEGORIES.get(r["category"], CATEGORIES["custom"])
            result.append(d)
        return result


def get(template_id: int) -> dict | None:
    with db.conn() as c:
        row = c.execute("SELECT * FROM message_templates WHERE id=?",
                        (template_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["category_info"] = CATEGORIES.get(row["category"], CATEGORIES["custom"])
        return d


def popular(limit: int = 5) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM message_templates ORDER BY use_count DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM message_templates").fetchone()[0]
        total_uses = c.execute(
            "SELECT COALESCE(SUM(use_count),0) FROM message_templates"
        ).fetchone()[0]
        cats = c.execute(
            "SELECT category, COUNT(*) cnt FROM message_templates GROUP BY category"
        ).fetchall()
    return {
        "total": total,
        "total_uses": total_uses,
        "by_category": {r["category"]: r["cnt"] for r in cats},
    }
