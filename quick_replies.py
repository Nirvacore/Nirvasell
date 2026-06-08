"""Quick Replies — Thai home seller's daily FAQ template kit.

Every reseller answers the same 10 questions every day in LINE / FB chat:
"ค่าส่งเท่าไหร่", "ของพร้อมส่งไหม", "ลดได้ไหม", etc. This module ships a
sensible default set + lets users add their own + uses Claude to generate
new ones from a question the user pastes in.

Storage: per-user `quick_replies` table.
Variables: {shop_name}, {shipping_cost}, {prep_days}, {bank_name},
           {promptpay} are resolved from user_settings at copy time.
"""
from __future__ import annotations
import json
from typing import Iterable

import db


SCHEMA = """
CREATE TABLE IF NOT EXISTS quick_replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL DEFAULT 'general',
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    use_count   INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    last_used   TEXT
);
CREATE INDEX IF NOT EXISTS idx_qr_cat ON quick_replies(category);
"""


# Sensible Thai defaults seeded on first init — covers ~80% of daily LINE/FB
# questions Thai home sellers actually receive. Variables in {curly} get
# resolved from user_settings.
DEFAULTS = [
    ("shipping", "ค่าส่งเท่าไหร่",
     "ค่าส่ง {shipping_cost} บาทค่ะ ส่งด้วย Kerry/Flash นะคะ ส่งทุกวันจันทร์-ศุกร์"),
    ("shipping", "ส่งฟรีไหม",
     "ฟรีค่าส่งเมื่อซื้อครบ 500 บาทค่ะ ถ้าต่ำกว่า ค่าส่ง {shipping_cost} บาทค่ะ"),
    ("stock", "ของพร้อมส่งไหม",
     "พร้อมส่งค่ะ! โอนปุ๊บส่งออกใน 1 วันทำการเลยค่ะ 📦"),
    ("stock", "มีสต็อกไหม",
     "ตอนนี้ของพร้อมส่งค่ะ ตอบเร็วๆ นะคะ เดี๋ยวหมดอีก เพราะของขายดีค่ะ ✨"),
    ("price", "ลดได้ไหม",
     "ราคานี้ดีสุดแล้วค่ะ — แต่ถ้าซื้อ 2 ชิ้นขึ้นไป ลดให้ชิ้นละ 20 บาทนะคะ 🎁"),
    ("price", "ราคารวมค่าส่งไหม",
     "ราคารวมค่าส่งแล้วค่ะ ส่งฟรี! 🚚"),
    ("payment", "โอนยังไง",
     "โอนได้ที่ PromptPay: {promptpay}\nหรือธนาคาร: {bank_name}\nโอนแล้ว ส่งสลิปมาทาง chat นี้เลยค่ะ ✨"),
    ("payment", "สั่ง 1 ชิ้น โอนแล้ว",
     "ขอบคุณค่ะ! ✨ จะเช็คสลิปแล้วยืนยันใน 30 นาทีนะคะ พอยืนยันแล้วจะส่งของออกพรุ่งนี้เช้าค่ะ"),
    ("delivery", "เมื่อไหร่ส่ง",
     "พรุ่งนี้เช้าส่งออกค่ะ Kerry/Flash ปกติถึงใน 1-2 วันค่ะ (กรุงเทพ-ปริมณฑล) 2-3 วันต่างจังหวัด"),
    ("delivery", "ของยังไม่ถึง",
     "ขอโทษด้วยค่ะ ส่ง track number ให้ตรวจสอบนะคะ ปกติ Kerry/Flash 1-3 วัน — ถ้าเกินนั้นแจ้งกลับมาเลยค่ะ จะเช็คให้"),
    ("return", "เปลี่ยน/คืนได้ไหม",
     "ของผิดสเปคหรือบกพร่อง เปลี่ยนคืนได้ภายใน 7 วันค่ะ ส่งรูป/วิดีโอ + ใบเสร็จมา จะส่งของใหม่ให้ฟรีค่ะ 🔄"),
    ("greeting", "สวัสดี",
     "สวัสดีค่ะ ยินดีต้อนรับสู่ {shop_name} ค่ะ มีอะไรให้ช่วยไหมคะ? 🌸"),
]


def init():
    with db.conn() as c:
        c.executescript(SCHEMA)
        # Seed defaults on first init only
        n = c.execute("SELECT COUNT(*) FROM quick_replies").fetchone()[0]
        if n == 0:
            for cat, title, body in DEFAULTS:
                c.execute(
                    "INSERT INTO quick_replies (category, title, body) "
                    "VALUES (?, ?, ?)",
                    (cat, title, body),
                )


# ---- CRUD --------------------------------------------------------------

def all_replies(category: str | None = None) -> list[dict]:
    init()
    sql = "SELECT * FROM quick_replies"
    params: tuple = ()
    if category and category != "all":
        sql += " WHERE category = ?"
        params = (category,)
    sql += " ORDER BY use_count DESC, id ASC"
    with db.conn() as c:
        rows = c.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def categories() -> list[str]:
    init()
    with db.conn() as c:
        rows = c.execute(
            "SELECT DISTINCT category FROM quick_replies ORDER BY category"
        ).fetchall()
    return [r["category"] for r in rows]


def add(*, title: str, body: str, category: str = "general") -> int:
    init()
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO quick_replies (category, title, body) VALUES (?, ?, ?)",
            (category.strip() or "general", title.strip(), body.strip()),
        )
        return cur.lastrowid


def update(reply_id: int, *, title: str | None = None,
           body: str | None = None, category: str | None = None) -> bool:
    init()
    fields, params = [], []
    if title is not None:    fields.append("title = ?");    params.append(title.strip())
    if body is not None:     fields.append("body = ?");     params.append(body.strip())
    if category is not None: fields.append("category = ?"); params.append(category.strip() or "general")
    if not fields:
        return False
    params.append(reply_id)
    with db.conn() as c:
        cur = c.execute(
            f"UPDATE quick_replies SET {', '.join(fields)} WHERE id = ?",
            params,
        )
    return cur.rowcount > 0


def delete(reply_id: int) -> bool:
    init()
    with db.conn() as c:
        cur = c.execute("DELETE FROM quick_replies WHERE id = ?", (reply_id,))
    return cur.rowcount > 0


def bump_use(reply_id: int) -> None:
    """Track which replies get copied most so we can sort by popularity."""
    init()
    with db.conn() as c:
        c.execute(
            "UPDATE quick_replies SET use_count = use_count + 1, "
            "last_used = CURRENT_TIMESTAMP WHERE id = ?", (reply_id,),
        )


# ---- Variable substitution --------------------------------------------

def _get_vars() -> dict:
    """Read substitution vars from user_settings. Cheap, called per-render."""
    try:
        import user_settings as us
        return {
            "shop_name":     us.get("shop.name", "ร้านของเรา") or "ร้านของเรา",
            "shipping_cost": us.get("shop.shipping_cost", "50") or "50",
            "prep_days":     us.get("shop.prep_days", "1") or "1",
            "bank_name":     us.get("shop.bank_name", "KBANK xxx-x-xxxxx-x") or "KBANK xxx-x-xxxxx-x",
            "promptpay":     us.get("payments.promptpay_id", "08x-xxx-xxxx") or "08x-xxx-xxxx",
        }
    except Exception:
        return {"shop_name": "ร้านของเรา", "shipping_cost": "50",
                "prep_days": "1", "bank_name": "KBANK xxx-x-xxxxx-x",
                "promptpay": "08x-xxx-xxxx"}


def render(body: str) -> str:
    """Resolve {variable} placeholders. Unknown placeholders left as-is."""
    vars_ = _get_vars()
    out = body
    for k, v in vars_.items():
        out = out.replace("{" + k + "}", str(v))
    return out


# ---- AI-generated replies ---------------------------------------------

_AI_PROMPT = """คุณคือ customer success rep ของร้านขายของออนไลน์ไทย

ข้อมูลร้าน:
- ชื่อร้าน: {shop_name}
- ค่าส่งปกติ: {shipping_cost} บาท
- เตรียมส่งใน: {prep_days} วัน

ลูกค้าถาม / สถานการณ์:
"{question}"

ภารกิจ: เขียน reply ภาษาไทยที่ดูจริงใจ ไม่ใช่ template
- ตรงประเด็น ไม่อ้อม
- ลงท้าย "ค่ะ" หรือ "ครับ" ตามเหมาะสม
- ถ้าต้องใส่ตัวเลข ให้ใช้ตัวเลขข้อมูลร้านที่ให้
- emoji ไม่เกิน 2 ตัว ใส่ตอนเหมาะสม

ส่ง JSON เท่านั้น:
{{
  "title": "ชื่อย่อสั้นๆ (ไม่เกิน 30 ตัวอักษร) สำหรับใช้เก็บใน template list",
  "category": "ประเภท: shipping | stock | price | payment | delivery | return | greeting | general",
  "body": "Reply ตัวเต็มที่จะ copy ไปวางใน LINE/FB chat"
}}

ห้ามใส่ ``` หรือคำอธิบาย"""


def ai_generate(question: str, api_key: str) -> dict | None:
    """Ask Claude to write a reply for a question the user pastes."""
    import os, json as _json, re
    if not api_key:
        return None
    try:
        from anthropic import Anthropic
        vars_ = _get_vars()
        prompt = _AI_PROMPT.format(
            shop_name=vars_["shop_name"],
            shipping_cost=vars_["shipping_cost"],
            prep_days=vars_["prep_days"],
            question=question.replace('"', "'")[:500],
        )
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        out = msg.content[0].text.strip()
        out = re.sub(r"^```(?:json)?\s*|\s*```$", "", out)
        data = _json.loads(out)
        return {
            "title": (data.get("title") or "")[:80],
            "category": (data.get("category") or "general"),
            "body": data.get("body") or "",
        }
    except Exception:
        return None
