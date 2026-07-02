"""Message Templates — pre-built LINE/chat templates for Thai sellers.

Order confirmation, shipping notice, review request, VIP follow-up.
Thai sellers copy-paste these daily — save 30+ minutes per day."""
from __future__ import annotations

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS msg_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                platform TEXT DEFAULT 'all',
                body TEXT NOT NULL,
                variables TEXT DEFAULT '',
                use_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        # Seed default templates if empty
        count = c.execute("SELECT COUNT(*) FROM msg_templates").fetchone()[0]
        if count == 0:
            _seed_defaults(c)


CATEGORIES = {
    "order":     {"icon": "🛒"},
    "shipping":  {"icon": "🚚"},
    "review":    {"icon": "⭐"},
    "followup":  {"icon": "💬"},
    "promo":     {"icon": "🎪"},
    "vip":       {"icon": "💎"},
    "complaint": {"icon": "🙏"},
    "custom":    {"icon": "📝"},
}

PLATFORMS = ["all", "line", "facebook", "instagram", "shopee_chat", "lazada_chat", "tiktok"]


def _seed_defaults(c):
    """Seed built-in Thai seller templates."""
    defaults = [
        ("ยืนยันออเดอร์", "order", "all",
         "สวัสดีค่ะ {buyer_name} 🙏\n"
         "ได้รับออเดอร์เรียบร้อยค่ะ\n"
         "📦 สินค้า: {product}\n"
         "💰 ยอด: ฿{total}\n"
         "จะจัดส่งภายใน {days} วันทำการนะคะ\n"
         "ขอบคุณที่อุดหนุนค่ะ 💕",
         "buyer_name,product,total,days"),

        ("แจ้งเลขพัสดุ", "shipping", "all",
         "สวัสดีค่ะ {buyer_name} 📦\n"
         "จัดส่งสินค้าแล้วค่ะ!\n"
         "🚚 ขนส่ง: {carrier}\n"
         "📮 เลขพัสดุ: {tracking}\n"
         "ประมาณ {days} วันถึงค่ะ\n"
         "มีอะไรทักมาได้เลยนะคะ 💕",
         "buyer_name,carrier,tracking,days"),

        ("ขอรีวิว", "review", "all",
         "สวัสดีค่ะ {buyer_name} 🌟\n"
         "ได้รับสินค้าเรียบร้อยไหมคะ?\n"
         "ถ้าชอบรบกวนกด ⭐⭐⭐⭐⭐ ให้ร้านด้วยนะคะ\n"
         "รีวิวของลูกค้ามีค่ามากค่ะ 🙏\n"
         "ขอบคุณค่ะ 💕",
         "buyer_name"),

        ("ติดตามลูกค้าเก่า", "followup", "all",
         "สวัสดีค่ะ {buyer_name} 👋\n"
         "ไม่ได้ทักมานาน คิดถึงค่ะ 💕\n"
         "ตอนนี้มีสินค้าใหม่มาเยอะเลย\n"
         "แวะมาดูได้นะคะ 🛒\n"
         "มีส่วนลดพิเศษสำหรับลูกค้าเก่าด้วยค่ะ ✨",
         "buyer_name"),

        ("ขอบคุณ VIP", "vip", "all",
         "สวัสดีค่ะ คุณ{buyer_name} 💎\n"
         "ขอบคุณที่อุดหนุนร้านมาตลอดค่ะ\n"
         "ลูกค้า VIP ของร้านเลย 🏆\n"
         "มีสินค้าใหม่จะแจ้งก่อนใครนะคะ\n"
         "อยากได้อะไรทักมาได้เลยค่ะ 💕",
         "buyer_name"),

        ("ตอบร้องเรียน", "complaint", "all",
         "สวัสดีค่ะ {buyer_name} 🙏\n"
         "ต้องขออภัยจริงๆ ค่ะ\n"
         "ร้านรับทราบปัญหาแล้วค่ะ\n"
         "จะรีบดำเนินการแก้ไขภายใน {days} วันค่ะ\n"
         "{solution}\n"
         "ขอโทษอีกครั้งนะคะ 🙏",
         "buyer_name,days,solution"),

        ("โปรโมชั่น", "promo", "all",
         "🎉 โปรสุดพิเศษ! 🎉\n"
         "{promo_name}\n"
         "💰 ลด {discount}\n"
         "📅 ถึงวันที่ {end_date}\n"
         "🛒 สั่งเลย → {link}\n"
         "จำนวนจำกัดค่ะ! ⚡",
         "promo_name,discount,end_date,link"),

        ("COD แจ้งชำระ", "order", "all",
         "สวัสดีค่ะ {buyer_name} 💰\n"
         "สินค้าถึงแล้วค่ะ\n"
         "กรุณาชำระเงินกับพนักงานส่ง\n"
         "💵 ยอด: ฿{total}\n"
         "ขอบคุณค่ะ 🙏",
         "buyer_name,total"),
    ]

    for name, cat, plat, body, vars_ in defaults:
        c.execute(
            "INSERT INTO msg_templates (name, category, platform, body, variables) "
            "VALUES (?,?,?,?,?)",
            (name, cat, plat, body, vars_),
        )


def add(name: str, category: str, platform: str, body: str,
        variables: str = "") -> int:
    with db.conn() as c:
        c.execute(
            "INSERT INTO msg_templates (name, category, platform, body, variables) "
            "VALUES (?,?,?,?,?)",
            (name, category, platform, body, variables),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def update(tmpl_id: int, **kwargs):
    sets = []
    vals = []
    for k in ("name", "category", "platform", "body", "variables"):
        if k in kwargs:
            sets.append(k + "=?")
            vals.append(kwargs[k])
    if not sets:
        return
    vals.append(tmpl_id)
    with db.conn() as c:
        c.execute("UPDATE msg_templates SET " + ",".join(sets) + " WHERE id=?", vals)


def delete(tmpl_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM msg_templates WHERE id=?", (tmpl_id,))


def record_use(tmpl_id: int):
    with db.conn() as c:
        c.execute("UPDATE msg_templates SET use_count=use_count+1 WHERE id=?",
                  (tmpl_id,))


def all_templates() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM msg_templates ORDER BY use_count DESC, name"
        ).fetchall()
    return [dict(r) for r in rows]


def by_category(category: str) -> list[dict]:
    return [t for t in all_templates() if t["category"] == category]


def get_template(tmpl_id: int) -> dict | None:
    with db.conn() as c:
        r = c.execute("SELECT * FROM msg_templates WHERE id=?", (tmpl_id,)).fetchone()
    return dict(r) if r else None


def fill_template(tmpl_id: int, values: dict) -> str:
    """Fill a template with actual values."""
    tmpl = get_template(tmpl_id)
    if not tmpl:
        return ""
    body = tmpl["body"]
    for k, v in values.items():
        body = body.replace("{" + k + "}", str(v))
    record_use(tmpl_id)
    return body


def stats() -> dict:
    templates = all_templates()
    total_uses = sum(t.get("use_count", 0) for t in templates)
    cats = {}
    for t in templates:
        cat = t["category"]
        cats[cat] = cats.get(cat, 0) + 1
    return {
        "total": len(templates),
        "total_uses": total_uses,
        "categories": cats,
        "most_used": templates[0]["name"] if templates else "—",
    }
